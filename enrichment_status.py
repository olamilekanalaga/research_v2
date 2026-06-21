from __future__ import annotations

from aladdin_research_engine.config import settings
from aladdin_research_engine.db import connect, init_db


def enabled_text(value: bool) -> str:
    return "enabled" if value else "disabled"


def present_text(value: str) -> str:
    return "present" if value else "missing"


def main() -> None:
    with connect() as conn:
        init_db(conn)
        trade_window_rows = conn.execute(
            "SELECT COUNT(1) AS count FROM alert_trade_windows"
        ).fetchone()["count"]
        basic_rows = conn.execute(
            "SELECT COUNT(1) AS count FROM solana_tracker_enrichment"
        ).fetchone()["count"]

    print(f"Solana Tracker basic enrichment: {enabled_text(settings.solana_tracker_enabled())}")
    print(
        "Solana Tracker trade windows: "
        f"{enabled_text(settings.solana_tracker_trade_windows_enabled())}"
    )
    print(
        "SOLANA_TRACKER_TRADE_WINDOWS_PATH_TEMPLATE: "
        f"{present_text(settings.solana_tracker_trade_windows_path_template)}"
    )
    print(f"solana_tracker_enrichment rows: {basic_rows}")
    print(f"alert_trade_windows rows count: {trade_window_rows}")
    if not settings.solana_tracker_trade_windows_path_template:
        print("Trade window enrichment skipped: endpoint template not configured.")


if __name__ == "__main__":
    main()
