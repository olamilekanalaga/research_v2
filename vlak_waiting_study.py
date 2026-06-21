from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from aladdin_research_engine.db import connect, init_db
from vlak_alert_survival_report import markdown_table


OUTPUT_DIR = Path("research_outputs") / "vlak_alert_survival"
EARLY_AGE_THRESHOLD_MIN = 0.2573
WAIT_WINDOWS_MIN = [0, 1, 2, 3, 5, 10]


def load_snapshots() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    with connect() as conn:
        init_db(conn)
        snapshots = pd.read_sql_query(
            """
            SELECT
                a.notification_id,
                a.mint,
                a.symbol,
                a.name,
                a.sent_at,
                a.market_cap AS alert_market_cap,
                a.first_call_market_cap,
                a.liquidity AS alert_liquidity,
                a.vol_1h,
                a.vol_24h,
                a.total_buy,
                a.count_buy,
                fm.market_cap AS metric_market_cap,
                fm.liquidity AS metric_liquidity,
                fm.age_minutes,
                fm.volume_usd,
                fm.buy_volume_sol,
                fm.sell_volume_sol,
                fm.buy_sell_volume_ratio,
                fm.buys,
                fm.holders,
                fm.unique_buyers,
                fm.top_buyer_share,
                fm.bundle_pct,
                fm.sniper_pct,
                fm.top10_holder_pct,
                fm.bundle_hold_percent,
                fm.sniper_hold_percent,
                fm.top10_percent,
                fm.liq_to_mc,
                fm.vol_to_mc,
                fm.avg_buy_size_sol
            FROM alerts a
            LEFT JOIN alert_filter_metrics fm
              ON fm.notification_id = a.notification_id
            WHERE a.mint IS NOT NULL
              AND a.sent_at IS NOT NULL
            """,
            conn,
        )
        outcomes = pd.read_sql_query(
            """
            SELECT
                mint,
                current_mc,
                ath_mc,
                ath_at,
                max_multiple,
                outcome_bucket
            FROM outcomes
            """,
            conn,
        )
        milestones = pd.read_sql_query(
            """
            SELECT mint, milestone, mc, hit_at
            FROM milestone_events
            WHERE hit_at IS NOT NULL
            """,
            conn,
        )

    snapshots["sent_at"] = pd.to_datetime(snapshots["sent_at"], utc=True, errors="coerce")
    snapshots["entry_market_cap"] = (
        snapshots["alert_market_cap"]
        .fillna(snapshots["metric_market_cap"])
        .fillna(snapshots["first_call_market_cap"])
    )
    snapshots["entry_liquidity"] = snapshots["alert_liquidity"].fillna(snapshots["metric_liquidity"])
    for col in [
        "entry_market_cap",
        "entry_liquidity",
        "age_minutes",
        "volume_usd",
        "buy_volume_sol",
        "vol_1h",
        "vol_24h",
        "total_buy",
        "count_buy",
        "buys",
        "holders",
        "unique_buyers",
        "bundle_pct",
        "sniper_pct",
        "top10_holder_pct",
        "bundle_hold_percent",
        "sniper_hold_percent",
        "top10_percent",
        "liq_to_mc",
        "vol_to_mc",
        "avg_buy_size_sol",
    ]:
        snapshots[col] = pd.to_numeric(snapshots[col], errors="coerce")

    outcomes["ath_at"] = pd.to_datetime(outcomes["ath_at"], utc=True, errors="coerce")
    for col in ["current_mc", "ath_mc", "max_multiple"]:
        outcomes[col] = pd.to_numeric(outcomes[col], errors="coerce")

    milestones["hit_at"] = pd.to_datetime(milestones["hit_at"], utc=True, errors="coerce")
    milestones["mc"] = pd.to_numeric(milestones["mc"], errors="coerce")
    return snapshots, outcomes, milestones


def first_snapshots(snapshots: pd.DataFrame) -> pd.DataFrame:
    ranked = snapshots.sort_values(["mint", "sent_at", "notification_id"]).copy()
    ranked["rn"] = ranked.groupby("mint").cumcount() + 1
    first = ranked[ranked["rn"] == 1].copy()
    return first[
        first["age_minutes"].notna()
        & (first["age_minutes"] <= EARLY_AGE_THRESHOLD_MIN)
        & first["entry_market_cap"].notna()
        & (first["entry_market_cap"] > 0)
    ].copy()


def post_entry_multiple(entry: pd.DataFrame) -> pd.Series:
    ath_at = pd.to_datetime(entry["ath_at"], utc=True, errors="coerce")
    entry_time = pd.to_datetime(entry["entry_time"], utc=True, errors="coerce")
    ath_after_entry = ath_at.isna() | (ath_at >= entry_time)
    return np.where(
        ath_after_entry & entry["ath_mc"].notna() & (entry["entry_market_cap"] > 0),
        entry["ath_mc"] / entry["entry_market_cap"],
        1.0,
    )


def hit_before_wait(
    milestones: pd.DataFrame,
    mint: str,
    first_entry_mc: float,
    first_sent_at: pd.Timestamp,
    wait_until: pd.Timestamp,
    multiple: float,
) -> bool:
    rows = milestones[
        (milestones["mint"] == mint)
        & (milestones["hit_at"] >= first_sent_at)
        & (milestones["hit_at"] < wait_until)
        & (milestones["mc"] >= first_entry_mc * multiple)
    ]
    return not rows.empty


def pick_wait_entries(
    snapshots: pd.DataFrame,
    outcomes: pd.DataFrame,
    milestones: pd.DataFrame,
    early_first: pd.DataFrame,
    wait_minutes: int,
) -> tuple[pd.DataFrame, dict[str, float | int]]:
    outcome_by_mint = outcomes.set_index("mint")
    rows = []
    diagnostics = {
        "wait_minutes": wait_minutes,
        "early_vlak_tokens": len(early_first),
        "trackable_at_wait": 0,
        "not_trackable_at_wait": 0,
        "missed_2x_before_wait": 0,
        "missed_3x_before_wait": 0,
        "missed_5x_before_wait": 0,
        "avoided_immediate_failures_no_snapshot": 0,
    }

    snapshots_by_mint = {
        mint: group.sort_values(["sent_at", "notification_id"]).copy()
        for mint, group in snapshots.groupby("mint")
    }

    for first in early_first.to_dict("records"):
        mint = first["mint"]
        first_sent_at = first["sent_at"]
        first_entry_mc = first["entry_market_cap"]
        wait_until = first_sent_at + pd.Timedelta(minutes=wait_minutes)
        token_snapshots = snapshots_by_mint.get(mint)
        if token_snapshots is None:
            continue

        candidates = token_snapshots[token_snapshots["sent_at"] >= wait_until]
        if wait_minutes == 0:
            candidates = token_snapshots[token_snapshots["sent_at"] == first_sent_at]
        if candidates.empty:
            diagnostics["not_trackable_at_wait"] += 1
            if mint in outcome_by_mint.index:
                outcome = outcome_by_mint.loc[mint]
                immediate_multiple = (
                    outcome["ath_mc"] / first_entry_mc
                    if pd.notna(outcome["ath_mc"]) and first_entry_mc and first_entry_mc > 0
                    else np.nan
                )
                if pd.notna(immediate_multiple) and immediate_multiple < 2:
                    diagnostics["avoided_immediate_failures_no_snapshot"] += 1
            continue

        picked = candidates.iloc[0].to_dict()
        picked["first_vlak_sent_at"] = first_sent_at
        picked["first_vlak_market_cap"] = first_entry_mc
        picked["target_wait_time"] = wait_until
        picked["wait_minutes"] = wait_minutes
        picked["snapshot_lag_minutes"] = (picked["sent_at"] - wait_until).total_seconds() / 60
        picked["entry_time"] = picked["sent_at"]

        if mint in outcome_by_mint.index:
            outcome = outcome_by_mint.loc[mint]
            picked["ath_mc"] = outcome["ath_mc"]
            picked["ath_at"] = outcome["ath_at"]
            picked["current_mc"] = outcome["current_mc"]
            picked["token_level_max_multiple"] = outcome["max_multiple"]
        else:
            picked["ath_mc"] = np.nan
            picked["ath_at"] = pd.NaT
            picked["current_mc"] = np.nan
            picked["token_level_max_multiple"] = np.nan

        for multiple in (2, 3, 5):
            key = f"missed_{multiple}x_before_wait"
            if wait_minutes > 0 and hit_before_wait(
                milestones,
                mint,
                first_entry_mc,
                first_sent_at,
                wait_until,
                float(multiple),
            ):
                diagnostics[key] += 1

        rows.append(picked)

    entries = pd.DataFrame(rows)
    diagnostics["trackable_at_wait"] = len(entries)
    return entries, diagnostics


def summarize_wait(entries: pd.DataFrame, diagnostics: dict[str, float | int], baseline_2x: float) -> dict[str, float | int]:
    row = dict(diagnostics)
    if entries.empty:
        return row
    entries = entries.copy()
    entries["post_wait_multiple"] = post_entry_multiple(entries)
    row.update(
        {
            "trackable_pct": len(entries) / diagnostics["early_vlak_tokens"] * 100
            if diagnostics["early_vlak_tokens"]
            else np.nan,
            "median_snapshot_lag_minutes": entries["snapshot_lag_minutes"].median(),
            "median_entry_market_cap": entries["entry_market_cap"].median(),
            "median_entry_mc_increase_pct": (
                (entries["entry_market_cap"] / entries["first_vlak_market_cap"] - 1).median() * 100
            ),
            "median_holders": entries["holders"].median(),
            "median_buys": entries["buys"].fillna(entries["count_buy"]).median(),
            "median_volume_usd": entries["volume_usd"].fillna(entries["vol_1h"]).median(),
            "median_liquidity": entries["entry_liquidity"].median(),
            "median_bundle_pct": entries["bundle_pct"].fillna(entries["bundle_hold_percent"]).median(),
            "median_sniper_pct": entries["sniper_pct"].fillna(entries["sniper_hold_percent"]).median(),
            "median_top10_pct": entries["top10_holder_pct"].fillna(entries["top10_percent"]).median(),
            "avg_post_wait_multiple": entries["post_wait_multiple"].mean(),
            "median_post_wait_multiple": entries["post_wait_multiple"].median(),
            "hit_2x_pct": (entries["post_wait_multiple"] >= 2).mean() * 100,
            "hit_3x_pct": (entries["post_wait_multiple"] >= 3).mean() * 100,
            "hit_5x_pct": (entries["post_wait_multiple"] >= 5).mean() * 100,
            "survival_lift_vs_immediate": ((entries["post_wait_multiple"] >= 2).mean() / baseline_2x)
            if baseline_2x
            else np.nan,
            "false_positive_reduction_count": row["avoided_immediate_failures_no_snapshot"],
            "missed_winners_total": row["missed_2x_before_wait"],
        }
    )
    return row


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    snapshots, outcomes, milestones = load_snapshots()
    early = first_snapshots(snapshots)
    all_entries = []
    summary_rows = []

    immediate_entries, _ = pick_wait_entries(snapshots, outcomes, milestones, early, 0)
    immediate_entries["post_wait_multiple"] = post_entry_multiple(immediate_entries)
    baseline_2x = (immediate_entries["post_wait_multiple"] >= 2).mean()

    for wait_minutes in WAIT_WINDOWS_MIN:
        entries, diagnostics = pick_wait_entries(snapshots, outcomes, milestones, early, wait_minutes)
        if not entries.empty:
            entries["post_wait_multiple"] = post_entry_multiple(entries)
            all_entries.append(entries)
        summary_rows.append(summarize_wait(entries, diagnostics, baseline_2x))

    summary = pd.DataFrame(summary_rows)
    detail = pd.concat(all_entries, ignore_index=True) if all_entries else pd.DataFrame()

    summary.to_csv(OUTPUT_DIR / "vlak_waiting_study_summary.csv", index=False)
    detail.to_csv(OUTPUT_DIR / "vlak_waiting_study_entries.csv", index=False)

    report = OUTPUT_DIR / "vlak_waiting_study.md"
    with report.open("w", encoding="utf-8") as f:
        f.write("# Vlak Waiting Study\n\n")
        f.write("Problem: for ultra-early Vlak alerts, compare buying immediately vs waiting for later Vlak snapshots.\n\n")
        f.write("No Aladdin strategy labels, pass/fail rules, or old thresholds are used.\n\n")
        f.write(f"Ultra-early cohort: first Vlak `age_minutes <= {EARLY_AGE_THRESHOLD_MIN}`.\n\n")
        f.write("Important limitation: wait entries use the first Vlak snapshot at or after the wait target. This is not tick-level chain data.\n\n")
        f.write("`missed_*_before_wait` uses milestone events before the wait target when available.\n\n")
        f.write("## Wait Summary\n\n")
        f.write(markdown_table(summary))
        f.write("\n\n## Research Director Read\n\n")
        f.write("- If waiting raises hit rates but sharply reduces trackable tokens, it supports a confirmation-wait bucket.\n")
        f.write("- If missed winners rise faster than hit-rate lift, immediate buying may still be better for some token types.\n")
        f.write("- If snapshot lag is high, the result is directional only and needs better time-series enrichment.\n")

    print(f"Wrote {report}")
    print()
    print(f"Ultra-early tokens: {len(early)}")
    print(f"Immediate 2x baseline: {baseline_2x * 100:.2f}%")
    print()
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
