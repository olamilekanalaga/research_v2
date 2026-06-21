from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from sqlite3 import Row
from typing import Any

from aladdin_research_engine.db import connect, init_db


METRICS = [
    "market_cap",
    "liquidity",
    "liq_to_mc",
    "volume_usd",
    "vol_to_mc",
    "buys",
    "holders",
    "top10_holder_pct",
    "bundle_pct",
    "sniper_pct",
]


@dataclass(frozen=True)
class BucketResult:
    metric: str
    bucket_rank: int
    bucket_label: str
    min_value: float
    max_value: float
    tokens: int
    avg_multiple: float | None
    hit_2x: float
    hit_5x: float
    hit_10x: float


def fmt_number(value: float | int | None) -> str:
    if value is None:
        return "n/a"
    if abs(value) >= 1:
        text = f"{value:,.2f}"
    else:
        text = f"{value:.4f}"
    return text.rstrip("0").rstrip(".")


def bucket_label(low: float, high: float, is_last: bool) -> str:
    if is_last:
        return f"{fmt_number(low)}+"
    return f"{fmt_number(low)}-{fmt_number(high)}"


def fetch_metric_rows(metric: str) -> list[Row]:
    with connect() as conn:
        init_db(conn)
        return conn.execute(
            f"""
            WITH ranked AS (
                SELECT
                    mint,
                    symbol,
                    {metric} AS metric_value,
                    max_multiple,
                    ROW_NUMBER() OVER (
                        PARTITION BY mint, ROUND({metric}, 8)
                        ORDER BY evaluated_at ASC
                    ) AS rn
                FROM strategy_research_view
                WHERE strategy_name = 'research_v2_historical'
                  AND {metric} IS NOT NULL
                  AND max_multiple IS NOT NULL
                  AND mint IS NOT NULL
            )
            SELECT mint, symbol, metric_value, max_multiple
            FROM ranked
            WHERE rn = 1
            ORDER BY metric_value ASC
            """
        ).fetchall()


def decile_results(metric: str, rows: list[Row]) -> list[BucketResult]:
    if not rows:
        return []
    bucket_count = min(10, len(rows))
    results = []
    for idx in range(bucket_count):
        start = idx * len(rows) // bucket_count
        end = (idx + 1) * len(rows) // bucket_count
        bucket_rows = rows[start:end]
        values = [float(row["metric_value"]) for row in bucket_rows]
        multiples = [float(row["max_multiple"]) for row in bucket_rows]
        low = min(values)
        high = max(values)
        results.append(
            BucketResult(
                metric=metric,
                bucket_rank=idx + 1,
                bucket_label=bucket_label(low, high, idx == bucket_count - 1),
                min_value=low,
                max_value=high,
                tokens=len({row["mint"] for row in bucket_rows}),
                avg_multiple=sum(multiples) / len(multiples) if multiples else None,
                hit_2x=sum(1 for value in multiples if value >= 2) / len(multiples),
                hit_5x=sum(1 for value in multiples if value >= 5) / len(multiples),
                hit_10x=sum(1 for value in multiples if value >= 10) / len(multiples),
            )
        )
    return results


def write_csv(results: list[BucketResult], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "metric",
                "bucket_rank",
                "bucket_label",
                "min_value",
                "max_value",
                "tokens",
                "avg_multiple",
                "hit_2x",
                "hit_5x",
                "hit_10x",
            ],
        )
        writer.writeheader()
        for row in results:
            writer.writerow(
                {
                    "metric": row.metric,
                    "bucket_rank": row.bucket_rank,
                    "bucket_label": row.bucket_label,
                    "min_value": row.min_value,
                    "max_value": row.max_value,
                    "tokens": row.tokens,
                    "avg_multiple": round(row.avg_multiple, 4) if row.avg_multiple is not None else "",
                    "hit_2x": round(row.hit_2x, 4),
                    "hit_5x": round(row.hit_5x, 4),
                    "hit_10x": round(row.hit_10x, 4),
                }
            )


def best_by(results: list[BucketResult], field: str) -> BucketResult | None:
    if not results:
        return None
    return max(results, key=lambda row: getattr(row, field) or 0)


def print_best_table(title: str, rows: list[tuple[str, BucketResult | None, str]]) -> None:
    print()
    print(title)
    print("=" * len(title))
    print("metric | bucket | tokens | avg_multiple | hit_2x | hit_5x | hit_10x | ranked_by")
    print("-------+--------+--------+--------------+--------+--------+---------+----------")
    for metric, row, ranked_by in rows:
        if row is None:
            continue
        print(
            " | ".join(
                [
                    metric,
                    row.bucket_label,
                    str(row.tokens),
                    fmt_number(row.avg_multiple),
                    f"{row.hit_2x:.3f}",
                    f"{row.hit_5x:.3f}",
                    f"{row.hit_10x:.3f}",
                    ranked_by,
                ]
            )
        )


def print_metric_tables(results_by_metric: dict[str, list[BucketResult]]) -> None:
    for metric, results in results_by_metric.items():
        print()
        print(metric)
        print("-" * len(metric))
        print("bucket | tokens | avg_multiple | hit_2x | hit_5x | hit_10x")
        print("-------+--------+--------------+--------+--------+---------")
        for row in results:
            print(
                " | ".join(
                    [
                        row.bucket_label,
                        str(row.tokens),
                        fmt_number(row.avg_multiple),
                        f"{row.hit_2x:.3f}",
                        f"{row.hit_5x:.3f}",
                        f"{row.hit_10x:.3f}",
                    ]
                )
            )


def main() -> None:
    results_by_metric: dict[str, list[BucketResult]] = {}
    all_results: list[BucketResult] = []
    for metric in METRICS:
        rows = fetch_metric_rows(metric)
        results = decile_results(metric, rows)
        results_by_metric[metric] = results
        all_results.extend(results)

    output_path = Path("research_outputs") / "threshold_discovery.csv"
    write_csv(all_results, output_path)

    print(f"Wrote {output_path}")
    print_metric_tables(results_by_metric)

    print_best_table(
        "best bucket by average multiple",
        [(metric, best_by(results, "avg_multiple"), "avg_multiple") for metric, results in results_by_metric.items()],
    )
    print_best_table(
        "best bucket by hit_5x",
        [(metric, best_by(results, "hit_5x"), "hit_5x") for metric, results in results_by_metric.items()],
    )
    print_best_table(
        "best bucket by hit_10x",
        [(metric, best_by(results, "hit_10x"), "hit_10x") for metric, results in results_by_metric.items()],
    )


if __name__ == "__main__":
    main()
