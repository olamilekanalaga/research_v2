from __future__ import annotations

from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd

from aladdin_research_engine.db import connect, init_db


OUTPUT_DIR = Path("research_outputs") / "survival_phase"
MIN_BUCKET_SIZE = 15


FEATURE_COLUMNS = [
    "market_cap",
    "liquidity",
    "age_minutes",
    "volume_usd",
    "buy_volume_sol",
    "sell_volume_sol",
    "buy_sell_volume_ratio",
    "buys",
    "holders",
    "unique_buyers",
    "top_buyer_share",
    "bundle_hold_percent",
    "sniper_hold_percent",
    "dev_hold_percent",
    "top10_percent",
    "phishing_hold_percent",
    "dex_paid",
    "lp_burned_percent",
    "liq_to_mc",
    "vol_to_mc",
    "avg_buy_size_sol",
    "top10_holder_pct",
    "bundle_pct",
    "sniper_pct",
]


def load_token_dataset() -> pd.DataFrame:
    with connect() as conn:
        init_db(conn)
        rows = pd.read_sql_query(
            """
            WITH first_metric AS (
                SELECT *
                FROM (
                    SELECT
                        afm.*,
                        ROW_NUMBER() OVER (
                            PARTITION BY afm.mint
                            ORDER BY datetime(afm.created_at) ASC, afm.notification_id ASC
                        ) AS rn
                    FROM alert_filter_metrics afm
                    WHERE afm.mint IS NOT NULL
                )
                WHERE rn = 1
            ),
            first_alert AS (
                SELECT
                    mint,
                    MIN(datetime(created_on)) AS first_seen_at,
                    COUNT(*) AS alert_rows_for_token
                FROM alerts
                WHERE mint IS NOT NULL
                GROUP BY mint
            )
            SELECT
                fm.*,
                fa.first_seen_at,
                fa.alert_rows_for_token,
                o.call_mc,
                o.current_mc,
                o.ath_mc,
                o.max_multiple,
                o.outcome_bucket,
                o.rugged
            FROM first_metric fm
            LEFT JOIN first_alert fa ON fa.mint = fm.mint
            LEFT JOIN outcomes o ON o.mint = fm.mint
            """,
            conn,
        )
    rows["observation_market_cap"] = pd.to_numeric(rows["market_cap"], errors="coerce")
    rows["ath_mc"] = pd.to_numeric(rows["ath_mc"], errors="coerce")
    rows["observation_max_multiple"] = np.where(
        (rows["observation_market_cap"].notna())
        & (rows["observation_market_cap"] > 0)
        & rows["ath_mc"].notna(),
        rows["ath_mc"] / rows["observation_market_cap"],
        np.nan,
    )
    rows["has_outcome"] = rows["observation_max_multiple"].notna().astype(int)
    rows["survived"] = np.where(
        rows["observation_max_multiple"].notna(),
        rows["observation_max_multiple"] >= 2,
        np.nan,
    )
    return rows


def dataset_integrity() -> dict[str, object]:
    with connect() as conn:
        init_db(conn)
        q = lambda sql: conn.execute(sql).fetchone()[0]
        return {
            "alerts_total_rows": q("SELECT COUNT(1) FROM alerts"),
            "alerts_unique_tokens": q("SELECT COUNT(DISTINCT mint) FROM alerts"),
            "alert_filter_metric_rows": q("SELECT COUNT(1) FROM alert_filter_metrics"),
            "alert_filter_metric_unique_tokens": q(
                "SELECT COUNT(DISTINCT mint) FROM alert_filter_metrics"
            ),
            "outcome_rows": q("SELECT COUNT(1) FROM outcomes"),
            "outcome_unique_tokens": q("SELECT COUNT(DISTINCT mint) FROM outcomes"),
            "milestone_rows": q("SELECT COUNT(1) FROM milestone_events"),
            "milestone_unique_tokens": q("SELECT COUNT(DISTINCT mint) FROM milestone_events"),
            "tokens_with_multiple_alert_rows": q(
                """
                SELECT COUNT(1)
                FROM (
                    SELECT mint
                    FROM alerts
                    WHERE mint IS NOT NULL
                    GROUP BY mint
                    HAVING COUNT(1) > 1
                )
                """
            ),
            "max_alert_rows_for_one_token": q(
                """
                SELECT MAX(row_count)
                FROM (
                    SELECT COUNT(1) AS row_count
                    FROM alerts
                    WHERE mint IS NOT NULL
                    GROUP BY mint
                )
                """
            ),
            "unit_of_analysis": (
                "token: one first-observed alert_filter_metrics row per mint, joined to one outcomes row; outcome is 2x after first observation"
            ),
        }


def survival_rate(df: pd.DataFrame) -> pd.DataFrame:
    eligible = df[df["has_outcome"] == 1]
    total = len(eligible)
    survived = int(eligible["survived"].sum())
    failed = total - survived
    return pd.DataFrame(
        [
            {
                "observed_tokens": len(df),
                "tokens_with_outcomes": total,
                "tokens_missing_outcomes": len(df) - total,
                "total_tokens": total,
                "survived_2x_plus": survived,
                "failed_before_2x": failed,
                "survival_probability": survived / total if total else np.nan,
                "survival_probability_pct": (survived / total * 100) if total else np.nan,
            }
        ]
    )


def feature_stats(df: pd.DataFrame) -> pd.DataFrame:
    records = []
    for feature in FEATURE_COLUMNS:
        if feature not in df.columns:
            continue
        series = pd.to_numeric(df[feature], errors="coerce")
        if series.notna().sum() < MIN_BUCKET_SIZE:
            continue
        for label, mask in [("survived", df["survived"] == 1), ("failed", df["survived"] == 0)]:
            values = series[mask].dropna()
            records.append(
                {
                    "feature": feature,
                    "group": label,
                    "tokens": len(values),
                    "mean": values.mean(),
                    "median": values.median(),
                    "std": values.std(),
                    "p25": values.quantile(0.25),
                    "p75": values.quantile(0.75),
                }
            )
    stats = pd.DataFrame(records)
    sep_records = []
    for feature in stats["feature"].unique():
        rows = stats[stats["feature"] == feature].set_index("group")
        if {"survived", "failed"} - set(rows.index):
            continue
        survived_mean = rows.loc["survived", "mean"]
        failed_mean = rows.loc["failed", "mean"]
        pooled = pd.to_numeric(df[feature], errors="coerce").std()
        sep_records.append(
            {
                "feature": feature,
                "survived_mean": survived_mean,
                "failed_mean": failed_mean,
                "mean_diff": survived_mean - failed_mean,
                "abs_standardized_diff": abs(survived_mean - failed_mean) / pooled
                if pooled and not np.isnan(pooled)
                else np.nan,
            }
        )
    sep = pd.DataFrame(sep_records).sort_values("abs_standardized_diff", ascending=False)
    return stats.merge(sep, on="feature", how="left")


def threshold_discovery(df: pd.DataFrame) -> pd.DataFrame:
    baseline = df["survived"].mean()
    records = []
    for feature in FEATURE_COLUMNS:
        values = pd.to_numeric(df[feature], errors="coerce")
        valid = df[values.notna()].copy()
        if len(valid) < MIN_BUCKET_SIZE * 2 or values.nunique(dropna=True) < 5:
            continue
        thresholds = sorted(valid[feature].quantile([0.25, 0.5, 0.75, 0.9]).dropna().unique())
        for threshold in thresholds:
            for direction, mask in [
                (">=", valid[feature] >= threshold),
                ("<=", valid[feature] <= threshold),
            ]:
                subset = valid[mask]
                if len(subset) < MIN_BUCKET_SIZE:
                    continue
                survival = subset["survived"].mean()
                records.append(
                    {
                        "feature": feature,
                        "threshold": threshold,
                        "condition": f"{feature} {direction} {threshold:.4g}",
                        "tokens": len(subset),
                        "survived": int(subset["survived"].sum()),
                        "survival_rate": survival,
                        "survival_rate_pct": survival * 100,
                        "lift_over_baseline": survival / baseline if baseline else np.nan,
                        "pct_point_gain": (survival - baseline) * 100,
                    }
                )
    return pd.DataFrame(records).sort_values(
        ["lift_over_baseline", "tokens"], ascending=[False, False]
    )


def probability_tables(df: pd.DataFrame) -> pd.DataFrame:
    records = []
    for feature in FEATURE_COLUMNS:
        values = pd.to_numeric(df[feature], errors="coerce")
        valid = df[values.notna()].copy()
        if len(valid) < MIN_BUCKET_SIZE * 2 or values.nunique(dropna=True) < 5:
            continue
        try:
            valid["bucket"] = pd.qcut(valid[feature], q=4, duplicates="drop")
        except ValueError:
            continue
        grouped = valid.groupby("bucket", observed=True)
        for bucket, group in grouped:
            records.append(
                {
                    "feature": feature,
                    "bucket": str(bucket),
                    "tokens": len(group),
                    "survived": int(group["survived"].sum()),
                    "survival_rate": group["survived"].mean(),
                    "survival_rate_pct": group["survived"].mean() * 100,
                }
            )
    return pd.DataFrame(records)


def interactions(df: pd.DataFrame, thresholds: pd.DataFrame) -> pd.DataFrame:
    top = thresholds[thresholds["tokens"] >= MIN_BUCKET_SIZE].head(12)
    records = []
    conditions = []
    for _, row in top.iterrows():
        feature = row["feature"]
        threshold = row["threshold"]
        direction = ">=" if ">=" in row["condition"] else "<="
        conditions.append((feature, direction, threshold, row["condition"]))
    for left, right in combinations(conditions, 2):
        f1, d1, t1, c1 = left
        f2, d2, t2, c2 = right
        s1 = pd.to_numeric(df[f1], errors="coerce")
        s2 = pd.to_numeric(df[f2], errors="coerce")
        m1 = s1 >= t1 if d1 == ">=" else s1 <= t1
        m2 = s2 >= t2 if d2 == ">=" else s2 <= t2
        subset = df[m1 & m2]
        if len(subset) < MIN_BUCKET_SIZE:
            continue
        survival = subset["survived"].mean()
        records.append(
            {
                "condition_1": c1,
                "condition_2": c2,
                "tokens": len(subset),
                "survived": int(subset["survived"].sum()),
                "survival_rate": survival,
                "survival_rate_pct": survival * 100,
            }
        )
    return pd.DataFrame(records).sort_values(["survival_rate", "tokens"], ascending=[False, False])


def failure_patterns(df: pd.DataFrame, thresholds: pd.DataFrame) -> pd.DataFrame:
    failed = df[df["survived"] == 0]
    records = []
    for _, row in thresholds.tail(40).iterrows():
        feature = row["feature"]
        threshold = row["threshold"]
        direction = ">=" if ">=" in row["condition"] else "<="
        values = pd.to_numeric(failed[feature], errors="coerce")
        mask = values >= threshold if direction == ">=" else values <= threshold
        if mask.sum() < MIN_BUCKET_SIZE:
            continue
        records.append(
            {
                "failure_pattern": row["condition"],
                "failed_tokens_matching": int(mask.sum()),
                "share_of_failures_pct": mask.mean() * 100,
            }
        )
    return pd.DataFrame(records).sort_values(
        ["share_of_failures_pct", "failed_tokens_matching"], ascending=[False, False]
    )


def survivor_archetypes(df: pd.DataFrame) -> pd.DataFrame:
    survived = df[df["survived"] == 1].copy()
    if survived.empty:
        return pd.DataFrame()
    q = lambda col, p: pd.to_numeric(df[col], errors="coerce").quantile(p)
    archetypes = {
        "liquidity_supported": pd.to_numeric(survived["liquidity"], errors="coerce") >= q("liquidity", 0.75),
        "volume_driven": pd.to_numeric(survived["volume_usd"], errors="coerce") >= q("volume_usd", 0.75),
        "holder_supported": pd.to_numeric(survived["holders"], errors="coerce") >= q("holders", 0.75),
        "low_bundle_low_sniper": (
            (pd.to_numeric(survived["bundle_pct"], errors="coerce") <= q("bundle_pct", 0.5))
            & (pd.to_numeric(survived["sniper_pct"], errors="coerce") <= q("sniper_pct", 0.5))
        ),
        "early_low_mc": pd.to_numeric(survived["market_cap"], errors="coerce") <= q("market_cap", 0.25),
    }
    return pd.DataFrame(
        [
            {
                "archetype": name,
                "surviving_tokens": int(mask.sum()),
                "share_of_survivors_pct": mask.mean() * 100,
            }
            for name, mask in archetypes.items()
        ]
    ).sort_values("surviving_tokens", ascending=False)


def markdown_table(df: pd.DataFrame, max_rows: int | None = None) -> str:
    if df.empty:
        return "No rows."
    table = df.head(max_rows) if max_rows else df
    table = table.copy()
    for column in table.columns:
        if pd.api.types.is_float_dtype(table[column]):
            table[column] = table[column].map(
                lambda value: "" if pd.isna(value) else f"{value:.4g}"
            )
        else:
            table[column] = table[column].map(lambda value: "" if pd.isna(value) else str(value))
    headers = list(table.columns)
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for _, row in table.iterrows():
        lines.append("| " + " | ".join(str(row[column]) for column in headers) + " |")
    return "\n".join(lines)


def write_report() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    full_df = load_token_dataset()
    df = full_df[full_df["has_outcome"] == 1].copy()
    integrity = pd.DataFrame([dataset_integrity()])
    survival = survival_rate(full_df)
    stats = feature_stats(df)
    stats_ranked = (
        stats[["feature", "survived_mean", "failed_mean", "mean_diff", "abs_standardized_diff"]]
        .drop_duplicates()
        .sort_values("abs_standardized_diff", ascending=False)
    )
    thresholds = threshold_discovery(df)
    probs = probability_tables(df)
    inter = interactions(df, thresholds)
    failures = failure_patterns(df, thresholds)
    archetypes = survivor_archetypes(df)
    candidates = thresholds[["condition", "tokens", "survival_rate_pct", "lift_over_baseline"]].head(30)

    outputs = {
        "dataset_integrity.csv": integrity,
        "survival_rate.csv": survival,
        "feature_stats.csv": stats,
        "feature_separation_ranked.csv": stats_ranked,
        "threshold_discovery.csv": thresholds,
        "probability_tables.csv": probs,
        "feature_interactions.csv": inter,
        "failure_patterns.csv": failures,
        "survivor_archetypes.csv": archetypes,
        "predictive_signal_candidates.csv": candidates,
    }
    for filename, table in outputs.items():
        table.to_csv(OUTPUT_DIR / filename, index=False)

    report_path = OUTPUT_DIR / "survival_phase_report.md"
    with report_path.open("w", encoding="utf-8") as f:
        f.write("# Survival Phase Report\n\n")
        f.write("## Dataset Integrity\n\n")
        f.write(markdown_table(integrity))
        f.write("\n\nCorrect unit of analysis: token. Each token uses its first observed `alert_filter_metrics` row as features, joined to one `outcomes` row. Survival is calculated as `ath_mc / first_observed_market_cap >= 2`, so this answers what predicts 2x after your threshold.\n\n")
        f.write("## Survival Rate\n\n")
        f.write(markdown_table(survival))
        f.write("\n\n## Strongest Feature Separation\n\n")
        f.write(markdown_table(stats_ranked, max_rows=15))
        f.write("\n\n## Best Threshold Candidates\n\n")
        f.write(markdown_table(thresholds, max_rows=20))
        f.write("\n\n## Best Feature Interactions\n\n")
        f.write(markdown_table(inter, max_rows=20) if not inter.empty else "No interaction met minimum sample size.")
        f.write("\n\n## Common Failure Patterns\n\n")
        f.write(markdown_table(failures, max_rows=20) if not failures.empty else "No failure pattern met minimum sample size.")
        f.write("\n\n## Survivor Archetypes\n\n")
        f.write(markdown_table(archetypes) if not archetypes.empty else "No survivor archetypes available.")
        f.write("\n")

    print(f"Wrote {report_path}")
    print()
    print("DATASET INTEGRITY")
    print(integrity.to_string(index=False))
    print()
    print("SURVIVAL RATE")
    print(survival.to_string(index=False))
    print()
    print("TOP FEATURE SEPARATION")
    print(stats_ranked.head(10).to_string(index=False))
    print()
    print("TOP THRESHOLDS")
    print(thresholds.head(10).to_string(index=False))
    print()
    print("TOP INTERACTIONS")
    print(inter.head(10).to_string(index=False) if not inter.empty else "No rows.")


if __name__ == "__main__":
    write_report()
