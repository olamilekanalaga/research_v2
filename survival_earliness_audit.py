from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from survival_phase_report import load_token_dataset
from survival_probability_curves import CURVES, label_range


OUTPUT_DIR = Path("research_outputs") / "survival_phase"


def build_earliness_table(df: pd.DataFrame, feature: str, bins: list[float]) -> pd.DataFrame:
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
        market_cap = pd.to_numeric(group["market_cap"], errors="coerce")
        age = pd.to_numeric(group["age_minutes"], errors="coerce")
        survival = group["survived"].mean() if len(group) else np.nan
        rows.append(
            {
                "feature": feature,
                "range": str(range_label),
                "tokens": len(group),
                "survived": int(group["survived"].sum()) if len(group) else 0,
                "survival_rate_pct": survival * 100 if pd.notna(survival) else np.nan,
                "lift_over_baseline": survival / baseline if baseline and pd.notna(survival) else np.nan,
                "market_cap_p25": market_cap.quantile(0.25),
                "market_cap_median": market_cap.median(),
                "market_cap_p75": market_cap.quantile(0.75),
                "age_minutes_p25": age.quantile(0.25),
                "age_minutes_median": age.median(),
                "age_minutes_p75": age.quantile(0.75),
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    df = load_token_dataset()
    df = df[df["has_outcome"] == 1].copy()
    tables = pd.concat(
        [build_earliness_table(df, feature, bins) for feature, bins in CURVES.items()],
        ignore_index=True,
    )
    out_csv = OUTPUT_DIR / "survival_earliness_audit.csv"
    tables.to_csv(out_csv, index=False)

    out_md = OUTPUT_DIR / "survival_earliness_audit.md"
    with out_md.open("w", encoding="utf-8") as f:
        f.write("# Survival Earliness Audit\n\n")
        f.write(
            "Outcome label: `SURVIVED = ath_mc / first_observed_market_cap >= 2`.\n\n"
        )
        f.write(
            "Purpose: separate early discovery signals from late confirmation signals by showing market cap and age at first observation for each bucket.\n\n"
        )
        for feature in CURVES:
            table = tables[tables["feature"] == feature]
            f.write(f"## {feature}\n\n")
            f.write("| Range | Tokens | Survival % | MC Median | MC P25 | MC P75 | Age Median | Age P25 | Age P75 |\n")
            f.write("| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |\n")
            for _, row in table.iterrows():
                f.write(
                    f"| {row['range']} | {int(row['tokens'])} | "
                    f"{row['survival_rate_pct']:.1f} | "
                    f"{row['market_cap_median']:.0f} | {row['market_cap_p25']:.0f} | {row['market_cap_p75']:.0f} | "
                    f"{row['age_minutes_median']:.2f} | {row['age_minutes_p25']:.2f} | {row['age_minutes_p75']:.2f} |\n"
                )
            f.write("\n")

    print(f"Wrote {out_csv}")
    print(f"Wrote {out_md}")
    print()
    for feature in CURVES:
        print(feature)
        print(
            tables[tables["feature"] == feature][
                [
                    "range",
                    "tokens",
                    "survival_rate_pct",
                    "market_cap_median",
                    "age_minutes_median",
                    "market_cap_p25",
                    "market_cap_p75",
                ]
            ].to_string(index=False)
        )
        print()


if __name__ == "__main__":
    main()
