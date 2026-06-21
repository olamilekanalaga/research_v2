from __future__ import annotations

import csv
from collections import defaultdict
from itertools import combinations
from pathlib import Path
from sqlite3 import Row

from aladdin_research_engine.db import connect, init_db


BASE_METRICS = ["market_cap", "liquidity", "volume_usd", "holders"]
PAIR_INTERACTIONS = list(combinations(BASE_METRICS, 2))
THREE_WAY_INTERACTIONS = [
    ("market_cap", "liquidity", "holders"),
    ("market_cap", "volume_usd", "holders"),
    ("liquidity", "volume_usd", "holders"),
    ("market_cap", "liquidity", "volume_usd"),
]
MIN_TOKENS_FOR_TOP_TABLE = 20


def fmt_number(value: float | int | None) -> str:
    if value is None:
        return "n/a"
    if abs(value) >= 1:
        text = f"{value:,.2f}"
    else:
        text = f"{value:.4f}"
    return text.rstrip("0").rstrip(".")


def load_bucket_edges() -> dict[str, list[dict[str, str | float | int]]]:
    path = Path("research_outputs") / "threshold_discovery.csv"
    if not path.exists():
        raise FileNotFoundError(
            "Missing research_outputs/threshold_discovery.csv. Run threshold_discovery.py first."
        )
    buckets: dict[str, list[dict[str, str | float | int]]] = defaultdict(list)
    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            metric = row["metric"]
            if metric not in BASE_METRICS:
                continue
            buckets[metric].append(
                {
                    "bucket_rank": int(row["bucket_rank"]),
                    "bucket_label": row["bucket_label"],
                    "min_value": float(row["min_value"]),
                    "max_value": float(row["max_value"]),
                }
            )
    return dict(buckets)


def bucket_for(value: float, buckets: list[dict[str, str | float | int]]) -> dict[str, str | float | int]:
    for bucket in buckets:
        if value <= float(bucket["max_value"]):
            return bucket
    return buckets[-1]


def fetch_rows() -> list[Row]:
    with connect() as conn:
        init_db(conn)
        return conn.execute(
            """
            WITH ranked AS (
                SELECT
                    mint,
                    symbol,
                    market_cap,
                    liquidity,
                    volume_usd,
                    holders,
                    max_multiple,
                    ROW_NUMBER() OVER (
                        PARTITION BY mint, ROUND(market_cap, 8), ROUND(liquidity, 8),
                                     ROUND(volume_usd, 8), holders
                        ORDER BY evaluated_at ASC
                    ) AS rn
                FROM strategy_research_view
                WHERE strategy_name = 'research_v2_historical'
                  AND mint IS NOT NULL
                  AND market_cap IS NOT NULL
                  AND liquidity IS NOT NULL
                  AND volume_usd IS NOT NULL
                  AND holders IS NOT NULL
                  AND max_multiple IS NOT NULL
            )
            SELECT
                mint,
                symbol,
                market_cap,
                liquidity,
                volume_usd,
                holders,
                max_multiple
            FROM ranked
            WHERE rn = 1
            """
        ).fetchall()


def summarize(values: list[float]) -> dict[str, float | int]:
    return {
        "tokens": len(values),
        "avg_multiple": sum(values) / len(values) if values else 0,
        "hit_2x": sum(1 for value in values if value >= 2) / len(values) if values else 0,
        "hit_5x": sum(1 for value in values if value >= 5) / len(values) if values else 0,
        "hit_10x": sum(1 for value in values if value >= 10) / len(values) if values else 0,
    }


def interaction_rows(
    source_rows: list[Row],
    bucket_edges: dict[str, list[dict[str, str | float | int]]],
    interaction: tuple[str, ...],
) -> list[dict[str, str | float | int]]:
    grouped: dict[tuple[str, ...], list[float]] = defaultdict(list)
    bucket_meta: dict[tuple[str, ...], dict[str, str | int]] = {}
    for row in source_rows:
        labels = []
        ranks = []
        for metric in interaction:
            bucket = bucket_for(float(row[metric]), bucket_edges[metric])
            labels.append(str(bucket["bucket_label"]))
            ranks.append(str(bucket["bucket_rank"]))
        key = tuple(labels)
        grouped[key].append(float(row["max_multiple"]))
        bucket_meta[key] = {
            "bucket_ranks": " + ".join(ranks),
            "bucket_labels": " + ".join(labels),
        }

    results = []
    interaction_name = " + ".join(interaction)
    for key, multiples in grouped.items():
        stats = summarize(multiples)
        results.append(
            {
                "interaction": interaction_name,
                "metrics": ",".join(interaction),
                "bucket_ranks": bucket_meta[key]["bucket_ranks"],
                "bucket_labels": bucket_meta[key]["bucket_labels"],
                "tokens": stats["tokens"],
                "avg_multiple": stats["avg_multiple"],
                "hit_2x": stats["hit_2x"],
                "hit_5x": stats["hit_5x"],
                "hit_10x": stats["hit_10x"],
            }
        )
    return results


def write_csv(rows: list[dict[str, str | float | int]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "interaction",
                "metrics",
                "bucket_ranks",
                "bucket_labels",
                "tokens",
                "avg_multiple",
                "hit_2x",
                "hit_5x",
                "hit_10x",
            ],
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    **row,
                    "avg_multiple": round(float(row["avg_multiple"]), 4),
                    "hit_2x": round(float(row["hit_2x"]), 4),
                    "hit_5x": round(float(row["hit_5x"]), 4),
                    "hit_10x": round(float(row["hit_10x"]), 4),
                }
            )


def print_top(title: str, rows: list[dict[str, str | float | int]], sort_key: str) -> None:
    ranked = sorted(
        (row for row in rows if int(row["tokens"]) >= MIN_TOKENS_FOR_TOP_TABLE),
        key=lambda row: (
            float(row[sort_key]),
            float(row["hit_5x"]),
            float(row["avg_multiple"]),
            int(row["tokens"]),
        ),
        reverse=True,
    )[:20]
    print()
    print(title)
    print("=" * len(title))
    print("interaction | bucket_labels | tokens | avg_multiple | hit_2x | hit_5x | hit_10x")
    print("------------+---------------+--------+--------------+--------+--------+---------")
    for row in ranked:
        print(
            " | ".join(
                [
                    str(row["interaction"]),
                    str(row["bucket_labels"]),
                    str(row["tokens"]),
                    fmt_number(float(row["avg_multiple"])),
                    f"{float(row['hit_2x']):.3f}",
                    f"{float(row['hit_5x']):.3f}",
                    f"{float(row['hit_10x']):.3f}",
                ]
            )
        )


def main() -> None:
    bucket_edges = load_bucket_edges()
    source_rows = fetch_rows()
    all_results: list[dict[str, str | float | int]] = []
    for interaction in [*PAIR_INTERACTIONS, *THREE_WAY_INTERACTIONS]:
        all_results.extend(interaction_rows(source_rows, bucket_edges, interaction))

    output_path = Path("research_outputs") / "feature_interactions.csv"
    write_csv(all_results, output_path)

    print(f"Wrote {output_path}")
    print(f"Source rows: {len(source_rows)}")
    print(f"Interaction rows: {len(all_results)}")
    print(f"Top tables require at least {MIN_TOKENS_FOR_TOP_TABLE} tokens per formation.")

    print_top("top formations by hit_10x", all_results, "hit_10x")
    print_top("top formations by hit_5x", all_results, "hit_5x")
    print_top("top formations by avg_multiple", all_results, "avg_multiple")


if __name__ == "__main__":
    main()
