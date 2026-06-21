from __future__ import annotations

from itertools import combinations
from math import sqrt
from pathlib import Path
from typing import NamedTuple

import numpy as np
import pandas as pd

from aladdin_research_engine.db import connect, init_db
from vlak_alert_survival_report import FEATURES, load_dataset, markdown_table
from vlak_alert_formation_study import FEATURE_ALIASES


OUTPUT_DIR = Path("research_outputs") / "vlak_alert_survival"
MIN_TRAIN_SAMPLE = 25
MIN_TEST_SAMPLE = 15
TOP_CONDITIONS = 14
QUANTILES = [0.2, 0.35, 0.5, 0.65, 0.8]


class Condition(NamedTuple):
    feature: str
    direction: str
    threshold: float
    label: str


def canonical_feature(feature: str) -> str:
    return FEATURE_ALIASES.get(feature, feature)


def wilson_ci(successes: int, total: int, z: float = 1.96) -> tuple[float, float]:
    if total == 0:
        return np.nan, np.nan
    p = successes / total
    denom = 1 + z**2 / total
    centre = p + z**2 / (2 * total)
    spread = z * sqrt((p * (1 - p) + z**2 / (4 * total)) / total)
    return (centre - spread) / denom, (centre + spread) / denom


def apply_condition(df: pd.DataFrame, condition: Condition) -> pd.Series:
    values = pd.to_numeric(df[condition.feature], errors="coerce")
    if condition.direction == ">=":
        return values >= condition.threshold
    return values <= condition.threshold


def apply_formation(df: pd.DataFrame, conditions: tuple[Condition, ...]) -> pd.Series:
    mask = pd.Series(True, index=df.index)
    for condition in conditions:
        mask &= apply_condition(df, condition)
    return mask


def add_first_sent_at(df: pd.DataFrame) -> pd.DataFrame:
    with connect() as conn:
        init_db(conn)
        sent = pd.read_sql_query(
            """
            SELECT mint, MIN(datetime(sent_at)) AS first_sent_at
            FROM alerts
            WHERE mint IS NOT NULL
              AND sent_at IS NOT NULL
            GROUP BY mint
            """,
            conn,
        )
    merged = df.merge(sent, on="mint", how="left")
    merged["first_sent_at"] = pd.to_datetime(merged["first_sent_at"], utc=True, errors="coerce")
    return merged


def split_dataset(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    usable = df[df["survived_2x_after_vlak"].notna()].copy()
    usable = add_first_sent_at(usable)
    usable = usable[usable["first_sent_at"].notna()].copy()
    usable = usable.sort_values(["first_sent_at", "mint"]).reset_index(drop=True)
    n = len(usable)
    train_end = int(n * 0.6)
    validate_end = int(n * 0.8)
    return (
        usable.iloc[:train_end].copy(),
        usable.iloc[train_end:validate_end].copy(),
        usable.iloc[validate_end:].copy(),
    )


def summarize_subset(
    subset: pd.DataFrame,
    baseline_rate: float,
    baseline_avg: float,
    split_name: str,
) -> dict[str, float | int | str]:
    tokens = len(subset)
    hits_2x = int((subset["post_vlak_multiple"] >= 2).sum())
    hits_3x = int((subset["post_vlak_multiple"] >= 3).sum())
    hits_5x = int((subset["post_vlak_multiple"] >= 5).sum())
    ci_low, ci_high = wilson_ci(hits_2x, tokens)
    hit_2x = hits_2x / tokens if tokens else np.nan
    avg_multiple = subset["post_vlak_multiple"].mean() if tokens else np.nan
    return {
        f"{split_name}_tokens": tokens,
        f"{split_name}_hit_2x_pct": hit_2x * 100,
        f"{split_name}_hit_3x_pct": hits_3x / tokens * 100 if tokens else np.nan,
        f"{split_name}_hit_5x_pct": hits_5x / tokens * 100 if tokens else np.nan,
        f"{split_name}_ci95_low_pct": ci_low * 100,
        f"{split_name}_ci95_high_pct": ci_high * 100,
        f"{split_name}_avg_multiple": avg_multiple,
        f"{split_name}_median_multiple": subset["post_vlak_multiple"].median() if tokens else np.nan,
        f"{split_name}_lift_vs_baseline": hit_2x / baseline_rate if baseline_rate else np.nan,
        f"{split_name}_avg_lift_vs_baseline": avg_multiple / baseline_avg if baseline_avg else np.nan,
        f"{split_name}_median_entry_mc": subset["first_vlak_market_cap"].median() if tokens else np.nan,
        f"{split_name}_median_age": pd.to_numeric(subset["age_minutes"], errors="coerce").median()
        if tokens
        else np.nan,
    }


def build_single_conditions(train: pd.DataFrame) -> list[Condition]:
    baseline = train["survived_2x_after_vlak"].mean()
    rows = []
    for feature in FEATURES:
        if feature not in train.columns:
            continue
        values = pd.to_numeric(train[feature], errors="coerce")
        valid = train[values.notna()].copy()
        valid[feature] = values[values.notna()]
        if len(valid) < MIN_TRAIN_SAMPLE * 2 or valid[feature].nunique() < 5:
            continue
        for threshold in valid[feature].quantile(QUANTILES).dropna().unique():
            for direction in (">=", "<="):
                subset = valid[valid[feature] >= threshold] if direction == ">=" else valid[valid[feature] <= threshold]
                if len(subset) < MIN_TRAIN_SAMPLE:
                    continue
                hit_rate = subset["survived_2x_after_vlak"].mean()
                if hit_rate <= baseline:
                    continue
                rows.append(
                    {
                        "feature": feature,
                        "direction": direction,
                        "threshold": float(threshold),
                        "tokens": len(subset),
                        "hit_rate": hit_rate,
                        "lift": hit_rate / baseline if baseline else np.nan,
                        "avg_multiple": subset["post_vlak_multiple"].mean(),
                    }
                )

    candidates = pd.DataFrame(rows)
    if candidates.empty:
        return []
    candidates = candidates.sort_values(
        ["lift", "avg_multiple", "tokens"], ascending=[False, False, False]
    )
    selected: list[Condition] = []
    used: set[str] = set()
    for row in candidates.to_dict("records"):
        feature = str(row["feature"])
        canonical = canonical_feature(feature)
        if canonical in used:
            continue
        threshold = float(row["threshold"])
        direction = str(row["direction"])
        selected.append(
            Condition(
                feature=feature,
                direction=direction,
                threshold=threshold,
                label=f"{feature} {direction} {threshold:.4g}",
            )
        )
        used.add(canonical)
        if len(selected) >= TOP_CONDITIONS:
            break
    return selected


def candidate_formations(conditions: list[Condition]) -> list[tuple[Condition, ...]]:
    formations: list[tuple[Condition, ...]] = [(condition,) for condition in conditions]
    for size in (2, 3):
        for combo in combinations(conditions, size):
            canonical = [canonical_feature(condition.feature) for condition in combo]
            if len(set(canonical)) != len(canonical):
                continue
            formations.append(combo)
    return formations


def evaluate_formations(
    formations: list[tuple[Condition, ...]],
    train: pd.DataFrame,
    validate: pd.DataFrame,
    test: pd.DataFrame,
) -> pd.DataFrame:
    baselines = {
        "train": (train["survived_2x_after_vlak"].mean(), train["post_vlak_multiple"].mean()),
        "validate": (validate["survived_2x_after_vlak"].mean(), validate["post_vlak_multiple"].mean()),
        "test": (test["survived_2x_after_vlak"].mean(), test["post_vlak_multiple"].mean()),
    }
    rows = []
    for formation in formations:
        train_subset = train[apply_formation(train, formation)]
        if len(train_subset) < MIN_TRAIN_SAMPLE:
            continue
        validate_subset = validate[apply_formation(validate, formation)]
        test_subset = test[apply_formation(test, formation)]
        if len(validate_subset) < MIN_TEST_SAMPLE or len(test_subset) < MIN_TEST_SAMPLE:
            continue
        row: dict[str, float | int | str] = {
            "conditions": " AND ".join(condition.label for condition in formation),
            "features": " + ".join(condition.feature for condition in formation),
            "formation_size": len(formation),
        }
        row.update(summarize_subset(train_subset, *baselines["train"], "train"))
        row.update(summarize_subset(validate_subset, *baselines["validate"], "validate"))
        row.update(summarize_subset(test_subset, *baselines["test"], "test"))
        row["stability_score"] = min(
            float(row["train_lift_vs_baseline"]),
            float(row["validate_lift_vs_baseline"]),
            float(row["test_lift_vs_baseline"]),
        )
        row["trade_score"] = (
            float(row["test_lift_vs_baseline"])
            * np.log1p(float(row["test_tokens"]))
            * min(float(row["test_avg_lift_vs_baseline"]), 3.0)
        )
        rows.append(row)
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows).sort_values(
        ["stability_score", "test_lift_vs_baseline", "test_tokens"],
        ascending=[False, False, False],
    )


def avoid_formations(results: pd.DataFrame, train: pd.DataFrame, validate: pd.DataFrame, test: pd.DataFrame) -> pd.DataFrame:
    # Reuse the opposite of weak buy formations by evaluating low-performing train conditions separately.
    baseline = train["survived_2x_after_vlak"].mean()
    rows = []
    for feature in FEATURES:
        if feature not in train.columns:
            continue
        values = pd.to_numeric(train[feature], errors="coerce")
        valid = train[values.notna()].copy()
        valid[feature] = values[values.notna()]
        if len(valid) < MIN_TRAIN_SAMPLE * 2 or valid[feature].nunique() < 5:
            continue
        for threshold in valid[feature].quantile(QUANTILES).dropna().unique():
            for direction in (">=", "<="):
                condition = Condition(
                    feature=feature,
                    direction=direction,
                    threshold=float(threshold),
                    label=f"{feature} {direction} {float(threshold):.4g}",
                )
                subset = valid[apply_condition(valid, condition)]
                if len(subset) < MIN_TRAIN_SAMPLE:
                    continue
                if subset["survived_2x_after_vlak"].mean() >= baseline:
                    continue
                validate_subset = validate[apply_condition(validate, condition)]
                test_subset = test[apply_condition(test, condition)]
                if len(validate_subset) < MIN_TEST_SAMPLE or len(test_subset) < MIN_TEST_SAMPLE:
                    continue
                train_fail = 1 - subset["survived_2x_after_vlak"].mean()
                validate_fail = 1 - validate_subset["survived_2x_after_vlak"].mean()
                test_fail = 1 - test_subset["survived_2x_after_vlak"].mean()
                rows.append(
                    {
                        "condition": condition.label,
                        "train_tokens": len(subset),
                        "validate_tokens": len(validate_subset),
                        "test_tokens": len(test_subset),
                        "train_failure_pct": train_fail * 100,
                        "validate_failure_pct": validate_fail * 100,
                        "test_failure_pct": test_fail * 100,
                        "test_survival_pct": (1 - test_fail) * 100,
                        "test_avg_multiple": test_subset["post_vlak_multiple"].mean(),
                        "test_median_entry_mc": test_subset["first_vlak_market_cap"].median(),
                        "test_median_age": pd.to_numeric(test_subset["age_minutes"], errors="coerce").median(),
                        "avoid_stability_score": min(train_fail, validate_fail, test_fail),
                    }
                )
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows).sort_values(
        ["avoid_stability_score", "test_failure_pct", "test_tokens"],
        ascending=[False, False, False],
    )


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    df = load_dataset()
    train, validate, test = split_dataset(df)
    conditions = build_single_conditions(train)
    formations = candidate_formations(conditions)
    results = evaluate_formations(formations, train, validate, test)
    avoids = avoid_formations(results, train, validate, test)

    summary = pd.DataFrame(
        [
            {
                "split": "train",
                "tokens": len(train),
                "hit_2x_pct": train["survived_2x_after_vlak"].mean() * 100,
                "avg_multiple": train["post_vlak_multiple"].mean(),
                "start_time": train["first_sent_at"].min(),
                "end_time": train["first_sent_at"].max(),
            },
            {
                "split": "validate",
                "tokens": len(validate),
                "hit_2x_pct": validate["survived_2x_after_vlak"].mean() * 100,
                "avg_multiple": validate["post_vlak_multiple"].mean(),
                "start_time": validate["first_sent_at"].min(),
                "end_time": validate["first_sent_at"].max(),
            },
            {
                "split": "test",
                "tokens": len(test),
                "hit_2x_pct": test["survived_2x_after_vlak"].mean() * 100,
                "avg_multiple": test["post_vlak_multiple"].mean(),
                "start_time": test["first_sent_at"].min(),
                "end_time": test["first_sent_at"].max(),
            },
        ]
    )

    summary.to_csv(OUTPUT_DIR / "vlak_trading_edge_split_summary.csv", index=False)
    results.to_csv(OUTPUT_DIR / "vlak_trading_edge_validated_buy_candidates.csv", index=False)
    avoids.to_csv(OUTPUT_DIR / "vlak_trading_edge_validated_avoid_candidates.csv", index=False)

    report = OUTPUT_DIR / "vlak_trading_edge_validation.md"
    with report.open("w", encoding="utf-8") as f:
        f.write("# Vlak Trading Edge Validation\n\n")
        f.write("Research question: which Vlak-only conditions survive out-of-sample well enough to change buy, avoid, or size decisions?\n\n")
        f.write("No Aladdin strategy labels, pass/fail rules, or old custom thresholds are used.\n\n")
        f.write("Method: chronological train/validate/test split. Conditions are discovered on train, then checked on later data.\n\n")
        f.write("Outcome: `post_vlak_multiple = ATH / first Vlak market cap`; 2x survival is the primary benchmark.\n\n")
        f.write("## Split Baselines\n\n")
        f.write(markdown_table(summary))
        f.write("\n\n## Validated Buy Candidates\n\n")
        f.write(markdown_table(results, 30))
        f.write("\n\n## Validated Avoid Candidates\n\n")
        f.write(markdown_table(avoids, 30))
        f.write("\n\n## Research Director Notes\n\n")
        f.write("- A candidate matters only if it improves later validation/test data, not just the discovery period.\n")
        f.write("- Use this to change buy/avoid/risk-size decisions, not to explain old charts.\n")
        f.write("- Avg multiple is optimistic because it assumes ATH capture; hit-rate stability is the cleaner decision metric.\n")

    print(f"Wrote {report}")
    print()
    print("SPLIT BASELINES")
    print(summary.to_string(index=False))
    print()
    print("TOP BUY CANDIDATES")
    print(results.head(12).to_string(index=False))
    print()
    print("TOP AVOID CANDIDATES")
    print(avoids.head(12).to_string(index=False))


if __name__ == "__main__":
    main()

