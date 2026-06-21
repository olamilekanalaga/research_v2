from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from survival_phase_report import load_token_dataset


OUTPUT_DIR = Path("research_outputs") / "survival_phase"


CURVES = {
    "holders": [0, 50, 100, 150, 200, 250, np.inf],
    "volume_usd": [0, 10_000, 25_000, 50_000, 75_000, 100_000, np.inf],
    "liquidity": [0, 5_000, 10_000, 12_500, 15_000, 20_000, np.inf],
    "liq_to_mc": [0, 0.25, 0.40, 0.55, 0.70, 1.00, np.inf],
    "age_minutes": [0, 0.25, 0.50, 1.00, 3.00, 10.00, np.inf],
}


def label_range(left: float, right: float) -> str:
    if right == np.inf:
        return f"{left:g}+"
    return f"{left:g}-{right:g}"


def build_curve(df: pd.DataFrame, feature: str, bins: list[float]) -> pd.DataFrame:
    values = pd.to_numeric(df[feature], errors="coerce")
    valid = df[values.notna()].copy()
    valid[feature] = values[values.notna()]
    valid["range"] = pd.cut(
        valid[feature],
        bins=bins,
        right=False,
        labels=[label_range(bins[i], bins[i + 1]) for i in range(len(bins) - 1)],
        include_lowest=True,
    )
    grouped = valid.groupby("range", observed=False)
    rows = []
    baseline = df["survived"].mean()
    for range_label, group in grouped:
        tokens = len(group)
        survived = int(group["survived"].sum()) if tokens else 0
        survival_rate = group["survived"].mean() if tokens else np.nan
        rows.append(
            {
                "feature": feature,
                "range": str(range_label),
                "tokens": tokens,
                "survived": survived,
                "failed": tokens - survived,
                "survival_rate": survival_rate,
                "survival_rate_pct": survival_rate * 100 if pd.notna(survival_rate) else np.nan,
                "lift_over_baseline": survival_rate / baseline
                if baseline and pd.notna(survival_rate)
                else np.nan,
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    df = load_token_dataset()
    df = df[df["has_outcome"] == 1].copy()
    curves = pd.concat(
        [build_curve(df, feature, bins) for feature, bins in CURVES.items()],
        ignore_index=True,
    )
    out_csv = OUTPUT_DIR / "survival_probability_curves.csv"
    curves.to_csv(out_csv, index=False)

    out_md = OUTPUT_DIR / "survival_probability_curves.md"
    with out_md.open("w", encoding="utf-8") as f:
        f.write("# Survival Probability Curves\n\n")
        f.write(
            "Outcome label: `SURVIVED = ath_mc / first_observed_market_cap >= 2`.\n\n"
        )
        f.write(f"Baseline survival probability: {df['survived'].mean() * 100:.1f}%\n\n")
        for feature in CURVES:
            table = curves[curves["feature"] == feature].copy()
            f.write(f"## {feature}\n\n")
            f.write("| Range | Tokens | Survived | Failed | Survival % | Lift |\n")
            f.write("| --- | ---: | ---: | ---: | ---: | ---: |\n")
            for _, row in table.iterrows():
                survival = ""
                lift = ""
                if pd.notna(row["survival_rate_pct"]):
                    survival = f"{row['survival_rate_pct']:.1f}"
                if pd.notna(row["lift_over_baseline"]):
                    lift = f"{row['lift_over_baseline']:.2f}"
                f.write(
                    f"| {row['range']} | {int(row['tokens'])} | {int(row['survived'])} | "
                    f"{int(row['failed'])} | {survival} | {lift} |\n"
                )
            f.write("\n")

    print(f"Wrote {out_csv}")
    print(f"Wrote {out_md}")
    print()
    for feature in CURVES:
        print(feature)
        print(
            curves[curves["feature"] == feature][
                ["range", "tokens", "survived", "failed", "survival_rate_pct", "lift_over_baseline"]
            ].to_string(index=False)
        )
        print()


if __name__ == "__main__":
    main()
