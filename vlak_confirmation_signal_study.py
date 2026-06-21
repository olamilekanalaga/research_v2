from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from vlak_alert_survival_report import markdown_table
from vlak_waiting_study import EARLY_AGE_THRESHOLD_MIN, load_snapshots, post_entry_multiple


OUTPUT_DIR = Path("research_outputs") / "vlak_alert_survival"
WINDOWS_MIN = [1, 3, 5, 10]
MIN_SAMPLE = 15

LEVEL_FEATURES = [
    "entry_market_cap",
    "holders",
    "buys",
    "count_buy",
    "volume_usd",
    "vol_1h",
    "entry_liquidity",
    "bundle_pct",
    "sniper_pct",
    "top10_holder_pct",
    "liq_to_mc",
    "vol_to_mc",
    "avg_buy_size_sol",
]

DELTA_FEATURES = [
    "mc_delta_pct",
    "holders_delta",
    "holders_delta_pct",
    "buys_delta",
    "buys_delta_pct",
    "volume_delta_pct",
    "liquidity_delta_pct",
    "bundle_delta",
    "sniper_delta",
    "top10_delta",
    "liq_to_mc_delta",
    "vol_to_mc_delta",
    "avg_buy_size_delta_pct",
]


def first_ultra_early(snapshots: pd.DataFrame) -> pd.DataFrame:
    ranked = snapshots.sort_values(["mint", "sent_at", "notification_id"]).copy()
    ranked["rn"] = ranked.groupby("mint").cumcount() + 1
    first = ranked[ranked["rn"] == 1].copy()
    return first[
        first["age_minutes"].notna()
        & (first["age_minutes"] <= EARLY_AGE_THRESHOLD_MIN)
        & first["entry_market_cap"].notna()
        & (first["entry_market_cap"] > 0)
    ].copy()


def pct_delta(new: pd.Series, old: pd.Series) -> pd.Series:
    return np.where(old.notna() & (old != 0), (new - old) / old * 100, np.nan)


def build_window_rows(snapshots: pd.DataFrame, outcomes: pd.DataFrame, window_min: int) -> pd.DataFrame:
    early = first_ultra_early(snapshots)
    outcome_by_mint = outcomes.set_index("mint")
    rows = []

    for _, first in early.iterrows():
        token_snaps = snapshots[
            (snapshots["mint"] == first["mint"])
            & (snapshots["sent_at"] > first["sent_at"])
            & (snapshots["sent_at"] <= first["sent_at"] + pd.Timedelta(minutes=window_min))
        ].sort_values(["sent_at", "notification_id"])
        if token_snaps.empty:
            continue

        confirm = token_snaps.iloc[-1].copy()
        row = confirm.to_dict()
        row["window_minutes"] = window_min
        row["first_vlak_sent_at"] = first["sent_at"]
        row["confirmation_time"] = confirm["sent_at"]
        row["confirmation_delay_minutes"] = (confirm["sent_at"] - first["sent_at"]).total_seconds() / 60
        row["first_vlak_market_cap"] = first["entry_market_cap"]
        row["entry_time"] = confirm["sent_at"]

        if first["mint"] in outcome_by_mint.index:
            outcome = outcome_by_mint.loc[first["mint"]]
            row["ath_mc"] = outcome["ath_mc"]
            row["ath_at"] = outcome["ath_at"]
            row["current_mc"] = outcome["current_mc"]
            row["token_level_max_multiple"] = outcome["max_multiple"]
        else:
            row["ath_mc"] = np.nan
            row["ath_at"] = pd.NaT
            row["current_mc"] = np.nan
            row["token_level_max_multiple"] = np.nan

        row["mc_delta_pct"] = (
            (confirm["entry_market_cap"] - first["entry_market_cap"]) / first["entry_market_cap"] * 100
            if pd.notna(confirm["entry_market_cap"]) and pd.notna(first["entry_market_cap"]) and first["entry_market_cap"]
            else np.nan
        )
        row["holders_delta"] = confirm["holders"] - first["holders"]
        row["holders_delta_pct"] = (
            (confirm["holders"] - first["holders"]) / first["holders"] * 100
            if pd.notna(confirm["holders"]) and pd.notna(first["holders"]) and first["holders"]
            else np.nan
        )
        row["buys_delta"] = confirm["buys"] - first["buys"]
        row["buys_delta_pct"] = (
            (confirm["buys"] - first["buys"]) / first["buys"] * 100
            if pd.notna(confirm["buys"]) and pd.notna(first["buys"]) and first["buys"]
            else np.nan
        )
        row["volume_delta_pct"] = (
            (confirm["volume_usd"] - first["volume_usd"]) / first["volume_usd"] * 100
            if pd.notna(confirm["volume_usd"]) and pd.notna(first["volume_usd"]) and first["volume_usd"]
            else np.nan
        )
        row["liquidity_delta_pct"] = (
            (confirm["entry_liquidity"] - first["entry_liquidity"]) / first["entry_liquidity"] * 100
            if pd.notna(confirm["entry_liquidity"]) and pd.notna(first["entry_liquidity"]) and first["entry_liquidity"]
            else np.nan
        )
        row["bundle_delta"] = confirm["bundle_pct"] - first["bundle_pct"]
        row["sniper_delta"] = confirm["sniper_pct"] - first["sniper_pct"]
        row["top10_delta"] = confirm["top10_holder_pct"] - first["top10_holder_pct"]
        row["liq_to_mc_delta"] = confirm["liq_to_mc"] - first["liq_to_mc"]
        row["vol_to_mc_delta"] = confirm["vol_to_mc"] - first["vol_to_mc"]
        row["avg_buy_size_delta_pct"] = (
            (confirm["avg_buy_size_sol"] - first["avg_buy_size_sol"]) / first["avg_buy_size_sol"] * 100
            if pd.notna(confirm["avg_buy_size_sol"]) and pd.notna(first["avg_buy_size_sol"]) and first["avg_buy_size_sol"]
            else np.nan
        )
        rows.append(row)

    df = pd.DataFrame(rows)
    if df.empty:
        return df
    df["post_confirmation_multiple"] = post_entry_multiple(df)
    df["survived_2x_after_confirmation"] = df["post_confirmation_multiple"] >= 2
    df["survived_3x_after_confirmation"] = df["post_confirmation_multiple"] >= 3
    df["survived_5x_after_confirmation"] = df["post_confirmation_multiple"] >= 5
    return df


def group_comparison(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    features = [*LEVEL_FEATURES, *DELTA_FEATURES]
    for window, group in df.groupby("window_minutes"):
        for feature in features:
            if feature not in group:
                continue
            values = pd.to_numeric(group[feature], errors="coerce")
            if values.notna().sum() < MIN_SAMPLE:
                continue
            for status, mask in [
                ("survived", group["survived_2x_after_confirmation"] == 1),
                ("failed", group["survived_2x_after_confirmation"] == 0),
            ]:
                part = values[mask].dropna()
                if len(part) < 3:
                    continue
                rows.append(
                    {
                        "window_minutes": window,
                        "feature": feature,
                        "group": status,
                        "tokens": len(part),
                        "mean": part.mean(),
                        "median": part.median(),
                        "p25": part.quantile(0.25),
                        "p75": part.quantile(0.75),
                    }
                )
    return pd.DataFrame(rows)


def threshold_candidates(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    features = [*LEVEL_FEATURES, *DELTA_FEATURES]
    for window, group in df.groupby("window_minutes"):
        baseline = group["survived_2x_after_confirmation"].mean()
        for feature in features:
            if feature not in group:
                continue
            values = pd.to_numeric(group[feature], errors="coerce")
            valid = group[values.notna()].copy()
            valid[feature] = values[values.notna()]
            if len(valid) < MIN_SAMPLE * 2 or valid[feature].nunique() < 5:
                continue
            for threshold in valid[feature].quantile([0.25, 0.5, 0.75]).dropna().unique():
                for direction in (">=", "<="):
                    subset = valid[valid[feature] >= threshold] if direction == ">=" else valid[valid[feature] <= threshold]
                    if len(subset) < MIN_SAMPLE:
                        continue
                    rate = subset["survived_2x_after_confirmation"].mean()
                    if rate <= baseline:
                        continue
                    rows.append(
                        {
                            "window_minutes": window,
                            "condition": f"{feature} {direction} {threshold:.4g}",
                            "feature": feature,
                            "threshold": threshold,
                            "direction": direction,
                            "tokens": len(subset),
                            "hit_2x_pct": rate * 100,
                            "hit_3x_pct": subset["survived_3x_after_confirmation"].mean() * 100,
                            "hit_5x_pct": subset["survived_5x_after_confirmation"].mean() * 100,
                            "baseline_2x_pct": baseline * 100,
                            "lift_over_window_baseline": rate / baseline if baseline else np.nan,
                            "median_confirmation_delay_minutes": subset["confirmation_delay_minutes"].median(),
                            "median_entry_market_cap": subset["entry_market_cap"].median(),
                            "median_mc_delta_pct": subset["mc_delta_pct"].median(),
                        }
                    )
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows).sort_values(
        ["lift_over_window_baseline", "tokens"], ascending=[False, False]
    )


def window_summary(df: pd.DataFrame, early_count: int) -> pd.DataFrame:
    rows = []
    for window, group in df.groupby("window_minutes"):
        rows.append(
            {
                "window_minutes": window,
                "ultra_early_tokens": early_count,
                "tokens_with_confirmation_snapshot": len(group),
                "confirmation_trackable_pct": len(group) / early_count * 100 if early_count else np.nan,
                "median_confirmation_delay_minutes": group["confirmation_delay_minutes"].median(),
                "median_entry_market_cap": group["entry_market_cap"].median(),
                "median_mc_delta_pct": group["mc_delta_pct"].median(),
                "median_holders_delta": group["holders_delta"].median(),
                "median_buys_delta": group["buys_delta"].median(),
                "median_volume_delta_pct": group["volume_delta_pct"].median(),
                "hit_2x_from_confirmation_pct": group["survived_2x_after_confirmation"].mean() * 100,
                "hit_3x_from_confirmation_pct": group["survived_3x_after_confirmation"].mean() * 100,
                "hit_5x_from_confirmation_pct": group["survived_5x_after_confirmation"].mean() * 100,
                "avg_post_confirmation_multiple": group["post_confirmation_multiple"].mean(),
                "median_post_confirmation_multiple": group["post_confirmation_multiple"].median(),
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    snapshots, outcomes, _ = load_snapshots()
    early = first_ultra_early(snapshots)
    windows = [build_window_rows(snapshots, outcomes, window) for window in WINDOWS_MIN]
    confirmations = pd.concat([df for df in windows if not df.empty], ignore_index=True)
    summary = window_summary(confirmations, len(early))
    comparisons = group_comparison(confirmations)
    thresholds = threshold_candidates(confirmations)

    confirmations.to_csv(OUTPUT_DIR / "vlak_confirmation_signal_entries.csv", index=False)
    summary.to_csv(OUTPUT_DIR / "vlak_confirmation_signal_summary.csv", index=False)
    comparisons.to_csv(OUTPUT_DIR / "vlak_confirmation_signal_comparison.csv", index=False)
    thresholds.to_csv(OUTPUT_DIR / "vlak_confirmation_signal_thresholds.csv", index=False)

    report = OUTPUT_DIR / "vlak_confirmation_signal_study.md"
    with report.open("w", encoding="utf-8") as f:
        f.write("# Vlak Confirmation Signal Study\n\n")
        f.write("Problem: after an ultra-early Vlak alert, what proof signal appears before buying?\n\n")
        f.write("No Aladdin strategy labels, pass/fail rules, or old thresholds are used.\n\n")
        f.write(f"Ultra-early cohort: first Vlak `age_minutes <= {EARLY_AGE_THRESHOLD_MIN}`.\n\n")
        f.write("Confirmation entry: latest Vlak snapshot within the window. Outcome is measured from that confirmation market cap.\n\n")
        f.write("## Window Summary\n\n")
        f.write(markdown_table(summary))
        f.write("\n\n## Top Confirmation Threshold Candidates\n\n")
        f.write(markdown_table(thresholds, 40))
        f.write("\n\n## Survivor vs Failure Feature Comparison\n\n")
        f.write(markdown_table(comparisons, 80))
        f.write("\n")

    print(f"Wrote {report}")
    print()
    print("WINDOW SUMMARY")
    print(summary.to_string(index=False))
    print()
    print("TOP THRESHOLD CANDIDATES")
    print(thresholds.head(20).to_string(index=False))


if __name__ == "__main__":
    main()
