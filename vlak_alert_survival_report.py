from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from aladdin_research_engine.db import connect, init_db


OUTPUT_DIR = Path("research_outputs") / "vlak_alert_survival"
MIN_SAMPLE = 20

FEATURES = [
    "market_cap",
    "first_call_market_cap",
    "liquidity",
    "total_buy",
    "count_buy",
    "vol_1h",
    "vol_24h",
    "chg_1h",
    "chg_24h",
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
    "liq_to_mc",
    "vol_to_mc",
    "avg_buy_size_sol",
    "top10_holder_pct",
    "bundle_pct",
    "sniper_pct",
]


def load_dataset() -> pd.DataFrame:
    with connect() as conn:
        init_db(conn)
        df = pd.read_sql_query(
            """
            WITH first_alert AS (
                SELECT *
                FROM (
                    SELECT
                        a.*,
                        ROW_NUMBER() OVER (
                            PARTITION BY a.mint
                            ORDER BY datetime(a.created_on), a.notification_id
                        ) AS rn
                    FROM alerts a
                    WHERE a.mint IS NOT NULL
                )
                WHERE rn = 1
            ),
            first_metric AS (
                SELECT *
                FROM (
                    SELECT
                        afm.*,
                        ROW_NUMBER() OVER (
                            PARTITION BY afm.mint
                            ORDER BY datetime(afm.created_at), afm.notification_id
                        ) AS rn
                    FROM alert_filter_metrics afm
                    WHERE afm.mint IS NOT NULL
                )
                WHERE rn = 1
            )
            SELECT
                fa.notification_id,
                fa.mint,
                fa.symbol,
                fa.name,
                fa.created_on AS first_vlak_alert_time,
                fa.market_cap,
                fa.first_call_market_cap,
                fa.liquidity,
                fa.total_buy,
                fa.count_buy,
                fa.vol_1h,
                fa.vol_24h,
                fa.chg_1h,
                fa.chg_24h,
                fm.age_minutes,
                fm.volume_usd,
                fm.buy_volume_sol,
                fm.sell_volume_sol,
                fm.buy_sell_volume_ratio,
                fm.buys,
                fm.holders,
                fm.unique_buyers,
                fm.top_buyer_share,
                fm.bundle_hold_percent,
                fm.sniper_hold_percent,
                fm.dev_hold_percent,
                fm.top10_percent,
                fm.liq_to_mc,
                fm.vol_to_mc,
                fm.avg_buy_size_sol,
                fm.top10_holder_pct,
                fm.bundle_pct,
                fm.sniper_pct,
                o.ath_mc,
                o.max_multiple AS token_level_max_multiple,
                o.outcome_bucket AS token_level_outcome_bucket
            FROM first_alert fa
            LEFT JOIN first_metric fm ON fm.mint = fa.mint
            LEFT JOIN outcomes o ON o.mint = fa.mint
            """,
            conn,
        )
    df["first_vlak_market_cap"] = pd.to_numeric(
        df["market_cap"].fillna(df["first_call_market_cap"]), errors="coerce"
    )
    df["ath_mc"] = pd.to_numeric(df["ath_mc"], errors="coerce")
    df["post_vlak_multiple"] = np.where(
        (df["first_vlak_market_cap"] > 0) & df["ath_mc"].notna(),
        df["ath_mc"] / df["first_vlak_market_cap"],
        np.nan,
    )
    df["survived_2x_after_vlak"] = np.where(
        df["post_vlak_multiple"].notna(),
        df["post_vlak_multiple"] >= 2,
        np.nan,
    )
    return df


def summarize_dataset(df: pd.DataFrame) -> pd.DataFrame:
    usable = df[df["survived_2x_after_vlak"].notna()]
    return pd.DataFrame(
        [
            {
                "observed_vlak_tokens": len(df),
                "usable_outcome_tokens": len(usable),
                "missing_outcome_or_mc": len(df) - len(usable),
                "survived_2x_after_vlak": int(usable["survived_2x_after_vlak"].sum()),
                "failed_after_vlak": int((usable["survived_2x_after_vlak"] == 0).sum()),
                "baseline_survival_pct": usable["survived_2x_after_vlak"].mean() * 100,
                "avg_post_vlak_multiple": usable["post_vlak_multiple"].mean(),
                "best_post_vlak_multiple": usable["post_vlak_multiple"].max(),
            }
        ]
    )


def feature_comparison(df: pd.DataFrame) -> pd.DataFrame:
    usable = df[df["survived_2x_after_vlak"].notna()].copy()
    rows = []
    for feature in FEATURES:
        if feature not in usable.columns:
            continue
        values = pd.to_numeric(usable[feature], errors="coerce")
        if values.notna().sum() < MIN_SAMPLE:
            continue
        for status, mask in [
            ("survived", usable["survived_2x_after_vlak"] == 1),
            ("failed", usable["survived_2x_after_vlak"] == 0),
        ]:
            group = values[mask].dropna()
            rows.append(
                {
                    "feature": feature,
                    "group": status,
                    "tokens": len(group),
                    "mean": group.mean(),
                    "median": group.median(),
                    "std": group.std(),
                    "p25": group.quantile(0.25),
                    "p75": group.quantile(0.75),
                }
            )
    stats = pd.DataFrame(rows)
    sep = []
    for feature in stats["feature"].unique():
        rows_for_feature = stats[stats["feature"] == feature].set_index("group")
        if not {"survived", "failed"}.issubset(rows_for_feature.index):
            continue
        survived_mean = rows_for_feature.loc["survived", "mean"]
        failed_mean = rows_for_feature.loc["failed", "mean"]
        pooled = pd.to_numeric(usable[feature], errors="coerce").std()
        sep.append(
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
    return pd.DataFrame(sep).sort_values("abs_standardized_diff", ascending=False)


def threshold_candidates(df: pd.DataFrame) -> pd.DataFrame:
    usable = df[df["survived_2x_after_vlak"].notna()].copy()
    baseline = usable["survived_2x_after_vlak"].mean()
    rows = []
    for feature in FEATURES:
        values = pd.to_numeric(usable[feature], errors="coerce")
        valid = usable[values.notna()].copy()
        valid[feature] = values[values.notna()]
        if len(valid) < MIN_SAMPLE * 2 or valid[feature].nunique() < 5:
            continue
        for threshold in valid[feature].quantile([0.25, 0.5, 0.75, 0.9]).dropna().unique():
            for direction in (">=", "<="):
                subset = valid[valid[feature] >= threshold] if direction == ">=" else valid[valid[feature] <= threshold]
                if len(subset) < MIN_SAMPLE:
                    continue
                rate = subset["survived_2x_after_vlak"].mean()
                rows.append(
                    {
                        "condition": f"{feature} {direction} {threshold:.4g}",
                        "feature": feature,
                        "threshold": threshold,
                        "direction": direction,
                        "tokens": len(subset),
                        "survived": int(subset["survived_2x_after_vlak"].sum()),
                        "survival_pct": rate * 100,
                        "lift_over_baseline": rate / baseline if baseline else np.nan,
                        "median_first_vlak_mc": subset["first_vlak_market_cap"].median(),
                        "median_age_minutes": pd.to_numeric(subset["age_minutes"], errors="coerce").median(),
                    }
                )
    return pd.DataFrame(rows).sort_values(
        ["lift_over_baseline", "tokens"], ascending=[False, False]
    )


def markdown_table(df: pd.DataFrame, max_rows: int | None = None) -> str:
    if df.empty:
        return "No rows."
    table = df.head(max_rows) if max_rows else df
    table = table.copy()
    for col in table.columns:
        if pd.api.types.is_float_dtype(table[col]):
            table[col] = table[col].map(lambda x: "" if pd.isna(x) else f"{x:.4g}")
        else:
            table[col] = table[col].map(lambda x: "" if pd.isna(x) else str(x))
    lines = [
        "| " + " | ".join(table.columns) + " |",
        "| " + " | ".join("---" for _ in table.columns) + " |",
    ]
    for _, row in table.iterrows():
        lines.append("| " + " | ".join(str(row[col]) for col in table.columns) + " |")
    return "\n".join(lines)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    df = load_dataset()
    summary = summarize_dataset(df)
    comparison = feature_comparison(df)
    thresholds = threshold_candidates(df)

    df.to_csv(OUTPUT_DIR / "vlak_alert_token_dataset.csv", index=False)
    summary.to_csv(OUTPUT_DIR / "vlak_alert_survival_summary.csv", index=False)
    comparison.to_csv(OUTPUT_DIR / "vlak_alert_feature_separation.csv", index=False)
    thresholds.to_csv(OUTPUT_DIR / "vlak_alert_threshold_candidates.csv", index=False)

    report = OUTPUT_DIR / "vlak_alert_survival_report.md"
    with report.open("w", encoding="utf-8") as f:
        f.write("# Vlak Alert Survival Report\n\n")
        f.write("Problem: among tokens Vlak alerted, identify what separates 2x survivors from non-survivors.\n\n")
        f.write("No Aladdin strategy labels, pass/fail rules, or custom thresholds are used.\n\n")
        f.write("Outcome: `post_vlak_multiple = ath_mc / first_vlak_market_cap`; survived if `>= 2`.\n\n")
        f.write("## Summary\n\n")
        f.write(markdown_table(summary))
        f.write("\n\n## Feature Separation\n\n")
        f.write(markdown_table(comparison, 25))
        f.write("\n\n## Threshold Candidates\n\n")
        f.write(markdown_table(thresholds, 30))
        f.write("\n")

    print(f"Wrote {report}")
    print()
    print("SUMMARY")
    print(summary.to_string(index=False))
    print()
    print("TOP FEATURE SEPARATION")
    print(comparison.head(15).to_string(index=False))
    print()
    print("TOP THRESHOLD CANDIDATES")
    print(thresholds.head(15).to_string(index=False))


if __name__ == "__main__":
    main()
