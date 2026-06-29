from __future__ import annotations

import csv
import sqlite3
from pathlib import Path

from migrate_vlak_long_run_schema import migrate
from vlak_survivor_telegram import SURVIVOR_THRESHOLDS

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "vlak_aladdin_research.sqlite"
OUT_DIR = ROOT / "research_outputs" / "telegram_survivor_alerts"
OUT_DIR.mkdir(parents=True, exist_ok=True)

MILESTONE_THRESHOLDS = [2, 3, 4, 5, 10]


def pct(value: float | None) -> str:
    return "n/a" if value is None else f"{value * 100:.2f}%"


def main() -> None:
    migrate(DB_PATH)
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row

    tokens_tracked = con.execute("SELECT COUNT(*) FROM vlak_token_outcomes WHERE max_multiple IS NOT NULL").fetchone()[0]
    thread_count = con.execute("SELECT COUNT(*) FROM telegram_survivor_threads").fetchone()[0]
    milestone_count = con.execute("SELECT COUNT(*) FROM telegram_survivor_milestones").fetchone()[0]
    duplicate_threads = con.execute("SELECT COUNT(*) FROM (SELECT mint FROM telegram_survivor_threads GROUP BY mint HAVING COUNT(*) > 1)").fetchone()[0]
    duplicate_milestones = con.execute("SELECT COUNT(*) FROM (SELECT mint, threshold FROM telegram_survivor_milestones GROUP BY mint, threshold HAVING COUNT(*) > 1)").fetchone()[0]

    threshold_counts = {}
    for threshold in SURVIVOR_THRESHOLDS:
        threshold_counts[threshold] = con.execute(
            "SELECT COUNT(*) FROM vlak_token_outcomes WHERE max_multiple >= ?",
            (threshold,),
        ).fetchone()[0]

    eligible_first = con.execute(
        """
        SELECT
            o.mint,
            e.symbol,
            e.name,
            o.first_alert_time,
            COALESCE(o.first_call_market_cap, e.first_call_market_cap) AS first_call_market_cap,
            o.current_mc,
            o.ath_market_cap,
            o.max_multiple,
            'root_1.5x' AS alert_action,
            1.5 AS threshold
        FROM vlak_token_outcomes o
        LEFT JOIN (SELECT * FROM vlak_alert_events WHERE is_first_alert_per_mint = 1) e ON e.mint = o.mint
        LEFT JOIN telegram_survivor_threads t ON t.mint = o.mint
        WHERE o.max_multiple >= 1.5
          AND t.mint IS NULL
        ORDER BY o.max_multiple DESC
        """
    ).fetchall()

    eligible_milestones = []
    for threshold in MILESTONE_THRESHOLDS:
        eligible_milestones.extend(
            con.execute(
                """
                SELECT
                    o.mint,
                    e.symbol,
                    e.name,
                    o.first_alert_time,
                    COALESCE(o.first_call_market_cap, e.first_call_market_cap) AS first_call_market_cap,
                    o.current_mc,
                    o.ath_market_cap,
                    o.max_multiple,
                    'reply_milestone' AS alert_action,
                    ? AS threshold
                FROM vlak_token_outcomes o
                JOIN telegram_survivor_threads t ON t.mint = o.mint
                LEFT JOIN telegram_survivor_milestones m ON m.mint = o.mint AND m.threshold = ?
                LEFT JOIN (SELECT * FROM vlak_alert_events WHERE is_first_alert_per_mint = 1) e ON e.mint = o.mint
                WHERE o.max_multiple >= ?
                  AND m.id IS NULL
                  AND t.root_message_id IS NOT NULL
                ORDER BY o.max_multiple DESC
                """,
                (threshold, threshold, threshold),
            ).fetchall()
        )

    dry_run_rows = [dict(row) for row in eligible_first] + [dict(row) for row in eligible_milestones]
    dry_run_csv = OUT_DIR / "vlak_survivor_alerts_dry_run.csv"
    with dry_run_csv.open("w", newline="", encoding="utf-8") as fp:
        fieldnames = [
            "alert_action",
            "threshold",
            "mint",
            "symbol",
            "name",
            "first_alert_time",
            "first_call_market_cap",
            "current_mc",
            "ath_market_cap",
            "max_multiple",
        ]
        writer = csv.DictWriter(fp, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(dry_run_rows)

    summary_rows = [
        {"metric": "tokens_tracked", "value": tokens_tracked},
        {"metric": "tokens_ge_1_5x", "value": threshold_counts[1.5]},
        {"metric": "tokens_ge_2x", "value": threshold_counts[2]},
        {"metric": "tokens_ge_3x", "value": threshold_counts[3]},
        {"metric": "tokens_ge_4x", "value": threshold_counts[4]},
        {"metric": "tokens_ge_5x", "value": threshold_counts[5]},
        {"metric": "tokens_ge_10x", "value": threshold_counts[10]},
        {"metric": "eligible_first_1_5x_alerts", "value": len(eligible_first)},
        {"metric": "eligible_milestone_replies", "value": len(eligible_milestones)},
        {"metric": "already_sent_threads", "value": thread_count},
        {"metric": "already_sent_milestones", "value": milestone_count},
        {"metric": "duplicate_thread_rows", "value": duplicate_threads},
        {"metric": "duplicate_milestone_rows", "value": duplicate_milestones},
    ]
    summary_csv = OUT_DIR / "vlak_survivor_alerts_summary.csv"
    with summary_csv.open("w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=["metric", "value"])
        writer.writeheader()
        writer.writerows(summary_rows)

    md = []
    md.append("# Vlak Survivor Telegram Alerts Implementation Report")
    md.append("")
    md.append("## Status")
    md.append("- Raw Vlak ingestion remains silent.")
    md.append("- Survivor Telegram logic is integrated after `vlak_token_outcomes` is updated by outcome refresh.")
    md.append("- `TELEGRAM_SURVIVOR_ALERTS_ENABLED` defaults to `false`.")
    md.append("- `TELEGRAM_SURVIVOR_DRY_RUN` defaults to `true`.")
    md.append("- No live survivor Telegram messages are sent unless enabled and dry-run is disabled.")
    md.append("")
    md.append("## Dry-Run Summary")
    md.append(f"- Total tokens tracked: {tokens_tracked}")
    for threshold in SURVIVOR_THRESHOLDS:
        rate = threshold_counts[threshold] / tokens_tracked if tokens_tracked else None
        md.append(f"- Tokens >= {threshold:g}x: {threshold_counts[threshold]} ({pct(rate)})")
    md.append(f"- Tokens eligible for first 1.5x alert: {len(eligible_first)}")
    md.append(f"- Tokens eligible for milestone replies: {len(eligible_milestones)}")
    md.append(f"- Already sent survivor root alerts: {thread_count}")
    md.append(f"- Already sent survivor milestone replies: {milestone_count}")
    md.append("")
    md.append("## Duplicate Prevention")
    md.append("- `telegram_survivor_threads.mint` is the primary key.")
    md.append("- `telegram_survivor_milestones` has `UNIQUE(mint, threshold)`.")
    md.append(f"- Duplicate root rows found: {duplicate_threads}")
    md.append(f"- Duplicate milestone rows found: {duplicate_milestones}")
    md.append("")
    md.append("## Validation")
    md.append("- Raw Vlak signal code path was not changed to send Telegram.")
    md.append("- Survivor root alert requires `max_multiple >= 1.5`.")
    md.append("- Milestone replies require an existing root survivor thread.")
    md.append("- Dry-run CSV lists eligible actions without sending Telegram.")
    (OUT_DIR / "vlak_survivor_alerts_implementation_report.md").write_text("\n".join(md), encoding="utf-8")

    print(OUT_DIR / "vlak_survivor_alerts_implementation_report.md")
    print(dry_run_csv)
    print(summary_csv)
    for row in summary_rows:
        print(f"{row['metric']}={row['value']}")


if __name__ == "__main__":
    main()
