from __future__ import annotations

from itertools import combinations
from math import log1p, sqrt
from pathlib import Path
from typing import NamedTuple

import numpy as np
import pandas as pd

from vlak_alert_survival_report import FEATURES, load_dataset, markdown_table


OUTPUT_DIR = Path("research_outputs") / "vlak_alert_survival"
MIN_SAMPLE = 20
MAX_SINGLE_CONDITIONS = 15
QUANTILES = [0.25, 0.5, 0.75, 0.9]
FEATURE_ALIASES = {
    "top10_percent": "top10_holder_pct",
    "top10_holder_pct": "top10_holder_pct",
    "bundle_hold_percent": "bundle_pct",
    "bundle_pct": "bundle_pct",
    "sniper_hold_percent": "sniper_pct",
    "sniper_pct": "sniper_pct",
    "total_buy": "buy_volume_sol",
    "buy_volume_sol": "buy_volume_sol",
    "count_buy": "buys",
    "buys": "buys",
    "vol_1h": "volume_usd",
    "volume_usd": "volume_usd",
}


class Condition(NamedTuple):
    feature: str
    threshold: float
    direction: str
    label: str


def canonical_feature(feature: str) -> str:
    return FEATURE_ALIASES.get(feature, feature)


def wilson_ci(successes: int, tokens: int, z: float = 1.96) -> tuple[float, float]:
    if tokens == 0:
        return np.nan, np.nan
    p = successes / tokens
    denom = 1 + z**2 / tokens
    centre = p + z**2 / (2 * tokens)
    spread = z * sqrt((p * (1 - p) + z**2 / (4 * tokens)) / tokens)
    return (centre - spread) / denom, (centre + spread) / denom


def apply_condition(df: pd.DataFrame, condition: Condition) -> pd.Series:
    values = pd.to_numeric(df[condition.feature], errors="coerce")
    if condition.direction == ">=":
        return values >= condition.threshold
    return values <= condition.threshold


def summarize_subset(
    subset: pd.DataFrame,
    baseline_rate: float,
    baseline_median_mc: float,
    baseline_median_age: float,
    formation_type: str,
    conditions: tuple[Condition, ...],
) -> dict[str, float | int | str]:
    tokens = len(subset)
    survived = int(subset["survived_2x_after_vlak"].sum())
    rate = survived / tokens if tokens else np.nan
    ci_low, ci_high = wilson_ci(survived, tokens)
    median_mc = subset["first_vlak_market_cap"].median()
    median_age = pd.to_numeric(subset["age_minutes"], errors="coerce").median()

    mc_earliness = baseline_median_mc / median_mc if median_mc and median_mc > 0 else 1
    age_earliness = baseline_median_age / median_age if median_age and median_age > 0 else 1
    earliness_score = float(np.clip((mc_earliness + age_earliness) / 2, 0.25, 3.0))
    lift = rate / baseline_rate if baseline_rate else np.nan
    rank_score = lift * log1p(tokens) * earliness_score if pd.notna(lift) else np.nan

    return {
        "formation_type": formation_type,
        "conditions": " AND ".join(condition.label for condition in conditions),
        "features": " + ".join(condition.feature for condition in conditions),
        "tokens": tokens,
        "survived": survived,
        "survival_pct": rate * 100,
        "baseline_survival_pct": baseline_rate * 100,
        "lift_over_baseline": lift,
        "ci95_low_pct": ci_low * 100,
        "ci95_high_pct": ci_high * 100,
        "median_first_vlak_mc": median_mc,
        "median_age_minutes": median_age,
        "earliness_score": earliness_score,
        "rank_score": rank_score,
        "avg_post_vlak_multiple": subset["post_vlak_multiple"].mean(),
        "median_post_vlak_multiple": subset["post_vlak_multiple"].median(),
    }


def build_single_conditions(usable: pd.DataFrame, baseline_rate: float) -> list[Condition]:
    rows = []
    for feature in FEATURES:
        if feature not in usable.columns:
            continue
        values = pd.to_numeric(usable[feature], errors="coerce")
        valid = usable[values.notna()].copy()
        valid[feature] = values[values.notna()]
        if len(valid) < MIN_SAMPLE * 2 or valid[feature].nunique() < 5:
            continue

        for threshold in valid[feature].quantile(QUANTILES).dropna().unique():
            for direction in (">=", "<="):
                mask = valid[feature] >= threshold if direction == ">=" else valid[feature] <= threshold
                subset = valid[mask]
                if len(subset) < MIN_SAMPLE:
                    continue
                rate = subset["survived_2x_after_vlak"].mean()
                if rate <= baseline_rate:
                    continue
                rows.append(
                    {
                        "feature": feature,
                        "threshold": float(threshold),
                        "direction": direction,
                        "tokens": len(subset),
                        "survival_rate": rate,
                        "lift": rate / baseline_rate,
                    }
                )

    candidates = pd.DataFrame(rows)
    if candidates.empty:
        return []
    candidates = candidates.sort_values(["lift", "tokens"], ascending=[False, False])

    selected: list[Condition] = []
    used_features: set[str] = set()
    for row in candidates.to_dict("records"):
        feature = str(row["feature"])
        canonical = canonical_feature(feature)
        if canonical in used_features:
            continue
        threshold = float(row["threshold"])
        direction = str(row["direction"])
        selected.append(
            Condition(
                feature=feature,
                threshold=threshold,
                direction=direction,
                label=f"{feature} {direction} {threshold:.4g}",
            )
        )
        used_features.add(canonical)
        if len(selected) >= MAX_SINGLE_CONDITIONS:
            break
    return selected


def formation_rows(usable: pd.DataFrame, conditions: list[Condition]) -> pd.DataFrame:
    baseline_rate = usable["survived_2x_after_vlak"].mean()
    baseline_median_mc = usable["first_vlak_market_cap"].median()
    baseline_median_age = pd.to_numeric(usable["age_minutes"], errors="coerce").median()
    rows = []

    for size in (2, 3):
        for combo in combinations(conditions, size):
            features = [condition.feature for condition in combo]
            canonical_features = [canonical_feature(feature) for feature in features]
            if len(set(canonical_features)) != len(canonical_features):
                continue
            mask = pd.Series(True, index=usable.index)
            for condition in combo:
                mask &= apply_condition(usable, condition)
            subset = usable[mask]
            if len(subset) < MIN_SAMPLE:
                continue
            rows.append(
                summarize_subset(
                    subset=subset,
                    baseline_rate=baseline_rate,
                    baseline_median_mc=baseline_median_mc,
                    baseline_median_age=baseline_median_age,
                    formation_type=f"{size}-way",
                    conditions=combo,
                )
            )

    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows).sort_values(
        ["rank_score", "lift_over_baseline", "tokens"],
        ascending=[False, False, False],
    )


def condition_rows(usable: pd.DataFrame, conditions: list[Condition]) -> pd.DataFrame:
    baseline_rate = usable["survived_2x_after_vlak"].mean()
    baseline_median_mc = usable["first_vlak_market_cap"].median()
    baseline_median_age = pd.to_numeric(usable["age_minutes"], errors="coerce").median()
    rows = []
    for condition in conditions:
        subset = usable[apply_condition(usable, condition)]
        if len(subset) < MIN_SAMPLE:
            continue
        rows.append(
            summarize_subset(
                subset=subset,
                baseline_rate=baseline_rate,
                baseline_median_mc=baseline_median_mc,
                baseline_median_age=baseline_median_age,
                formation_type="single",
                conditions=(condition,),
            )
        )
    return pd.DataFrame(rows).sort_values(
        ["lift_over_baseline", "tokens"], ascending=[False, False]
    )


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    df = load_dataset()
    usable = df[df["survived_2x_after_vlak"].notna()].copy()
    baseline_rate = usable["survived_2x_after_vlak"].mean()

    conditions = build_single_conditions(usable, baseline_rate)
    singles = condition_rows(usable, conditions)
    formations = formation_rows(usable, conditions)

    singles.to_csv(OUTPUT_DIR / "vlak_alert_formation_single_conditions.csv", index=False)
    formations.to_csv(OUTPUT_DIR / "vlak_alert_formations.csv", index=False)

    report = OUTPUT_DIR / "vlak_alert_formation_study.md"
    with report.open("w", encoding="utf-8") as f:
        f.write("# Vlak Alert Formation Study\n\n")
        f.write("Problem: given a Vlak alert, which feature combinations improve the chance of another 2x?\n\n")
        f.write("No Aladdin strategy labels, pass/fail rules, or custom thresholds are used.\n\n")
        f.write("Outcome: `post_vlak_multiple = ath_mc / first_vlak_market_cap`; survived if `>= 2`.\n\n")
        f.write(f"Baseline survival: `{baseline_rate * 100:.2f}%` across `{len(usable)}` usable tokens.\n\n")
        f.write("Ranking score uses lift, sample size, and earliness. It is a research ranking, not a buy rule.\n\n")
        f.write("## Single Conditions Used\n\n")
        f.write(markdown_table(singles, 20))
        f.write("\n\n## Top Formations By Rank Score\n\n")
        f.write(markdown_table(formations, 30))
        f.write("\n\n## Top Formations By Survival Lift\n\n")
        top_lift = formations.sort_values(
            ["lift_over_baseline", "tokens"], ascending=[False, False]
        )
        f.write(markdown_table(top_lift, 30))
        f.write("\n")

    print(f"Wrote {report}")
    print()
    print(f"Baseline survival: {baseline_rate * 100:.2f}%")
    print(f"Usable tokens: {len(usable)}")
    print(f"Single conditions selected: {len(conditions)}")
    print(f"Formation rows: {len(formations)}")
    print()
    print("TOP FORMATIONS BY RANK SCORE")
    print(formations.head(15).to_string(index=False))


if __name__ == "__main__":
    main()
