from __future__ import annotations

from collections.abc import Iterable
from sqlite3 import Row

from aladdin_research_engine.db import connect, init_db


def print_rows(title: str, rows: Iterable[Row], columns: list[str]) -> None:
    print()
    print(title)
    print("=" * len(title))
    rows = list(rows)
    if not rows:
        print("No rows.")
        return
    widths = {
        column: max(len(column), *(len(str(row[column])) for row in rows))
        for column in columns
    }
    print(" | ".join(column.ljust(widths[column]) for column in columns))
    print("-+-".join("-" * widths[column] for column in columns))
    for row in rows:
        print(" | ".join(str(row[column]).ljust(widths[column]) for column in columns))


def main() -> None:
    with connect() as conn:
        init_db(conn)

        print_rows(
            "research_v2_historical passed vs rejected performance",
            conn.execute(
                """
                SELECT
                    CASE WHEN filter_passed = 1 THEN 'passed' ELSE 'rejected' END AS status,
                    COUNT(DISTINCT mint) AS tokens,
                    ROUND(AVG(max_multiple), 2) AS avg_multiple,
                    ROUND(AVG(CASE WHEN max_multiple >= 1.5 THEN 1.0 ELSE 0.0 END), 3) AS hit_1_5x,
                    ROUND(AVG(CASE WHEN max_multiple >= 2 THEN 1.0 ELSE 0.0 END), 3) AS hit_2x,
                    ROUND(AVG(CASE WHEN max_multiple >= 5 THEN 1.0 ELSE 0.0 END), 3) AS hit_5x,
                    ROUND(AVG(CASE WHEN max_multiple >= 10 THEN 1.0 ELSE 0.0 END), 3) AS hit_10x
                FROM strategy_research_view
                WHERE strategy_name = 'research_v2_historical'
                GROUP BY status
                ORDER BY status
                """
            ).fetchall(),
            ["status", "tokens", "avg_multiple", "hit_1_5x", "hit_2x", "hit_5x", "hit_10x"],
        )

        print_rows(
            "strategy row counts",
            conn.execute(
                """
                WITH expected_strategies(strategy_name) AS (
                    VALUES
                        ('research_v2_historical'),
                        ('research_v2_live'),
                        ('early_discovery'),
                        ('continuation_runner'),
                        ('premium_runner'),
                        ('confirmed_runner')
                )
                SELECT
                    expected_strategies.strategy_name,
                    COUNT(strategy_research_view.strategy_name) AS rows,
                    COUNT(DISTINCT strategy_research_view.mint) AS tokens,
                    COALESCE(
                        SUM(CASE WHEN strategy_research_view.filter_passed = 1 THEN 1 ELSE 0 END),
                        0
                    ) AS passed_rows
                FROM expected_strategies
                LEFT JOIN strategy_research_view
                    ON strategy_research_view.strategy_name = expected_strategies.strategy_name
                GROUP BY expected_strategies.strategy_name
                ORDER BY expected_strategies.strategy_name
                """
            ).fetchall(),
            ["strategy_name", "rows", "tokens", "passed_rows"],
        )

        print_rows(
            "top damaging rejection reasons",
            conn.execute(
                """
                SELECT
                    rejection_reason,
                    rejected_tokens,
                    hit_2x,
                    hit_5x,
                    hit_10x,
                    avg_multiple
                FROM rejection_damage_summary
                LIMIT 20
                """
            ).fetchall(),
            ["rejection_reason", "rejected_tokens", "hit_2x", "hit_5x", "hit_10x", "avg_multiple"],
        )

        print_rows(
            "top 20 missed winners",
            conn.execute(
                """
                SELECT
                    symbol,
                    mint,
                    rejection_reason,
                    ROUND(market_cap, 2) AS market_cap,
                    ROUND(liquidity, 2) AS liquidity,
                    ROUND(liq_to_mc, 4) AS liq_to_mc,
                    ROUND(volume_usd, 2) AS volume_usd,
                    buys,
                    holders,
                    ROUND(max_multiple, 2) AS max_multiple
                FROM missed_winner_examples
                LIMIT 20
                """
            ).fetchall(),
            [
                "symbol",
                "mint",
                "rejection_reason",
                "market_cap",
                "liquidity",
                "liq_to_mc",
                "volume_usd",
                "buys",
                "holders",
                "max_multiple",
            ],
        )

        print_rows(
            "outcome coverage",
            conn.execute(
                """
                SELECT
                    COUNT(DISTINCT a.mint) AS alert_mints,
                    COUNT(DISTINCT o.mint) AS outcome_mints,
                    COUNT(DISTINCT CASE WHEN o.mint IS NULL THEN a.mint END) AS missing_outcome_mints
                FROM alerts a
                LEFT JOIN outcomes o ON o.mint = a.mint
                """
            ).fetchall(),
            ["alert_mints", "outcome_mints", "missing_outcome_mints"],
        )

        print_rows(
            "strategy overlap summary",
            conn.execute(
                """
                SELECT
                    mint,
                    symbol,
                    passed_strategies,
                    strategy_count,
                    ROUND(max_multiple, 2) AS max_multiple
                FROM strategy_overlap_summary
                LIMIT 20
                """
            ).fetchall(),
            ["mint", "symbol", "passed_strategies", "strategy_count", "max_multiple"],
        )


if __name__ == "__main__":
    main()
