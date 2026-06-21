from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from .db import json_dumps
from .utils import number_or_none, pick


FILTER_NAME = "ERF-v1"

ERF_RULES = {
    "max_age_minutes": 5,
    "min_market_cap": 8_000,
    "max_market_cap": 30_000,
    "min_liquidity": 5_000,
    "min_liq_to_mc": 0.25,
    "min_volume_usd": 10_000,
    "min_vol_to_mc": 0.8,
    "min_buys": 40,
    "min_sol_volume": 40,
    "min_avg_buy_size_sol": 0.5,
    "min_holders": 50,
    "max_top10_holder_pct": 35,
    "max_bundle_pct": 35,
    "max_sniper_pct": 10,
    "min_buy_sell_volume_ratio": 3,
}


@dataclass(frozen=True)
class StrategyFilter:
    strategy_name: str
    filter_version: str
    telegram_label: str
    rules: dict[str, Any]


STRATEGY_FILTERS = [
    StrategyFilter(
        strategy_name="early_discovery",
        filter_version="early_v1",
        telegram_label="🚼 Early Discovery",
        rules={
            "max_age_minutes": 10,
            "min_market_cap": 8_000,
            "max_market_cap": 80_000,
            "min_liquidity": 10_000,
            "min_liq_to_mc": 0.20,
            "min_volume_usd": 8_000,
            "min_vol_to_mc": 0.50,
            "min_buys": 20,
            "min_sol_volume": 20,
            "min_holders": 40,
            "max_top10_holder_pct": 35,
            "max_bundle_pct": 35,
            "max_sniper_pct": 10,
            "min_buy_sell_volume_ratio": 3,
        },
    ),
    StrategyFilter(
        strategy_name="continuation_runner",
        filter_version="continuation_v1",
        telegram_label="🏃 Continuation Runner",
        rules={
            "max_age_minutes": 30,
            "min_market_cap": 80_000,
            "max_market_cap": 250_000,
            "min_liquidity": 20_000,
            "min_liq_to_mc": 0.10,
            "min_volume_usd": 70_000,
            "min_vol_to_mc": 0.30,
            "min_buys": 20,
            "max_buys": 120,
            "min_holders": 100,
            "max_top10_holder_pct": 35,
            "max_bundle_pct": 35,
            "max_sniper_pct": 10,
            "min_buy_sell_volume_ratio": 2,
        },
    ),
    StrategyFilter(
        strategy_name="premium_runner",
        filter_version="premium_v1",
        telegram_label="💎 Premium Runner",
        rules={
            "min_market_cap": 150_000,
            "max_market_cap": 500_000,
            "min_liquidity": 50_000,
            "min_volume_usd": 150_000,
            "min_liq_to_mc": 0.08,
            "min_holders": 150,
            "max_top10_holder_pct": 35,
            "max_bundle_pct": 35,
            "max_sniper_pct": 10,
            "optional_min_buys": 20,
            "min_buy_sell_volume_ratio": 2,
        },
    ),
    StrategyFilter(
        strategy_name="confirmed_runner",
        filter_version="confirmed_runner_v1",
        telegram_label="✅ Confirmed Runner",
        rules={
            "min_market_cap": 109_000,
            "min_liquidity": 20_000,
            "min_holders": 296,
            "optional_min_volume_usd": 96_000,
            "max_top10_holder_pct": 35,
            "max_bundle_pct": 35,
            "max_sniper_pct": 10,
        },
    ),
]


def _timestamp_ms(value: Any) -> int | None:
    if isinstance(value, str):
        try:
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
            return int(dt.timestamp() * 1000)
        except ValueError:
            pass
    number = number_or_none(value)
    if number is None:
        return None
    if number < 10_000_000_000:
        number *= 1000
    return int(number)


def _age_minutes(raw: dict[str, Any]) -> float | None:
    timestamp = _timestamp_ms(
        pick(raw, "sentAt", "firstCallTime", "createdAt", "timestamp", "callAt")
    )
    if timestamp is None:
        return None
    alert_time = datetime.fromtimestamp(timestamp / 1000, tz=timezone.utc)
    return (datetime.now(timezone.utc) - alert_time).total_seconds() / 60


def explosive_runner_metrics(raw: dict[str, Any]) -> dict[str, float | int | None]:
    trackers = pick(raw, "trackers", default={}) or {}
    trackers = trackers if isinstance(trackers, dict) else {}
    holders = pick(raw, "holders", default={}) or {}
    holders = holders if isinstance(holders, dict) else {}
    market_cap = number_or_none(pick(raw, "marketCap", "market_cap", "mc"))
    liquidity = number_or_none(pick(raw, "liquidity", "liq"))
    volume_usd = number_or_none(
        pick(raw, "buyVolumeUsd10m", "buy_volume_usd_10m", "vol1h", "volume1h")
    )
    sol_volume = number_or_none(
        pick(trackers, "totalBuy", "total_buy", "buyVolumeSol")
        or pick(raw, "totalBuy", "total_buy", "buyVolumeSol")
    )
    sell_volume_sol = number_or_none(
        pick(trackers, "totalSell", "total_sell", "sellVolumeSol")
        or pick(raw, "totalSell", "total_sell", "sellVolumeSol")
    )
    buys = int(
        number_or_none(
            pick(trackers, "countBuy10m", "buys10m", "buys_10m", "countBuy")
            or pick(raw, "countBuy10m", "buys10m", "buys_10m", "countBuy")
        )
        or 0
    )
    return {
        "market_cap": market_cap,
        "liquidity": liquidity,
        "age_minutes": _age_minutes(raw),
        "volume_usd": volume_usd,
        "sol_volume": sol_volume,
        "buy_volume_sol": sol_volume,
        "sell_volume_sol": sell_volume_sol,
        "buy_sell_volume_ratio": (
            sol_volume / sell_volume_sol
            if sol_volume is not None and sell_volume_sol
            else None
        ),
        "buys": buys,
        "holders": int(number_or_none(pick(holders, "total", "holderCount", "holders")) or 0),
        "top10_holder_pct": number_or_none(pick(holders, "top10Percent", "top10_percent")),
        "bundle_pct": number_or_none(pick(holders, "bundleHoldPercent", "bundle_pct")),
        "sniper_pct": number_or_none(pick(holders, "sniperHoldPercent", "sniper_pct")),
        "liq_to_mc": liquidity / market_cap if liquidity and market_cap else None,
        "vol_to_mc": volume_usd / market_cap if volume_usd and market_cap else None,
        "avg_buy_size_sol": sol_volume / buys if sol_volume is not None and buys else None,
        "unique_buyers": (
            number_or_none(
                pick(trackers, "uniqueBuyers", "unique_buyers", "uniqueBuyers10m", "unique_buyers_10m")
                or pick(raw, "uniqueBuyers", "unique_buyers", "uniqueBuyers10m", "unique_buyers_10m")
            )
        ),
        "top_buyer_share": number_or_none(
            pick(trackers, "topBuyerShare", "top_buyer_share", "topBuyerShare10m", "top_buyer_share_10m")
            or pick(raw, "topBuyerShare", "top_buyer_share", "topBuyerShare10m", "top_buyer_share_10m")
        ),
    }


def passes_quick_launch_filter(raw: dict[str, Any]) -> tuple[bool, dict[str, float | int | None]]:
    return passes_explosive_runner_filter(raw)


def passes_explosive_runner_filter(raw: dict[str, Any]) -> tuple[bool, dict[str, float | int | None]]:
    metrics = explosive_runner_metrics(raw)
    rules = ERF_RULES
    checks = [
        ("age_minutes", metrics["age_minutes"], lambda v: v <= rules["max_age_minutes"]),
        ("market_cap_min", metrics["market_cap"], lambda v: v >= rules["min_market_cap"]),
        ("market_cap_max", metrics["market_cap"], lambda v: v <= rules["max_market_cap"]),
        ("liquidity", metrics["liquidity"], lambda v: v >= rules["min_liquidity"]),
        ("liq_to_mc", metrics["liq_to_mc"], lambda v: v >= rules["min_liq_to_mc"]),
        ("volume_usd", metrics["volume_usd"], lambda v: v >= rules["min_volume_usd"]),
        ("vol_to_mc", metrics["vol_to_mc"], lambda v: v >= rules["min_vol_to_mc"]),
        ("buys", metrics["buys"], lambda v: v >= rules["min_buys"]),
        ("sol_volume", metrics["sol_volume"], lambda v: v >= rules["min_sol_volume"]),
        ("avg_buy_size_sol", metrics["avg_buy_size_sol"], lambda v: v >= rules["min_avg_buy_size_sol"]),
        ("holders", metrics["holders"], lambda v: v >= rules["min_holders"]),
        ("top10_holder_pct", metrics["top10_holder_pct"], lambda v: v <= rules["max_top10_holder_pct"]),
        ("bundle_pct", metrics["bundle_pct"], lambda v: v <= rules["max_bundle_pct"]),
        ("sniper_pct", metrics["sniper_pct"], lambda v: v <= rules["max_sniper_pct"]),
    ]
    if metrics["sell_volume_sol"] is not None and metrics["sell_volume_sol"] > 0:
        checks.append(
            (
                "buy_sell_volume_ratio",
                metrics["buy_sell_volume_ratio"],
                lambda v: v >= rules["min_buy_sell_volume_ratio"],
            )
        )
    rejection_reasons = []
    for name, value, predicate in checks:
        if value is None:
            rejection_reasons.append(f"missing_{name}")
        elif not predicate(value):
            rejection_reasons.append(f"failed_{name}")
    metrics["rejection_reason"] = ";".join(rejection_reasons) if rejection_reasons else None
    return not rejection_reasons, metrics


def _evaluate_checks(checks: list[tuple[str, Any, Any]]) -> str | None:
    rejection_reasons = []
    for name, value, predicate in checks:
        if value is None:
            rejection_reasons.append(f"missing_{name}")
        elif not predicate(value):
            rejection_reasons.append(f"failed_{name}")
    return ";".join(rejection_reasons) if rejection_reasons else None


def evaluate_strategy_filter(raw: dict[str, Any], strategy_filter: StrategyFilter) -> dict[str, Any]:
    metrics = explosive_runner_metrics(raw)
    rules = strategy_filter.rules
    checks: list[tuple[str, Any, Any]] = []

    if "max_age_minutes" in rules:
        checks.append(("age_minutes", metrics["age_minutes"], lambda v: v <= rules["max_age_minutes"]))
    checks.extend(
        [
            ("market_cap_min", metrics["market_cap"], lambda v: v >= rules["min_market_cap"]),
            ("liquidity", metrics["liquidity"], lambda v: v >= rules["min_liquidity"]),
            ("holders", metrics["holders"], lambda v: v >= rules["min_holders"]),
            (
                "top10_holder_pct",
                metrics["top10_holder_pct"],
                lambda v: v <= rules["max_top10_holder_pct"],
            ),
            ("bundle_pct", metrics["bundle_pct"], lambda v: v <= rules["max_bundle_pct"]),
            ("sniper_pct", metrics["sniper_pct"], lambda v: v <= rules["max_sniper_pct"]),
        ]
    )
    if "max_market_cap" in rules:
        checks.append(("market_cap_max", metrics["market_cap"], lambda v: v <= rules["max_market_cap"]))
    if "min_volume_usd" in rules:
        checks.append(("volume_usd", metrics["volume_usd"], lambda v: v >= rules["min_volume_usd"]))
    elif metrics["volume_usd"] is not None and "optional_min_volume_usd" in rules:
        checks.append(
            (
                "volume_usd",
                metrics["volume_usd"],
                lambda v: v >= rules["optional_min_volume_usd"],
            )
        )
    if "min_liq_to_mc" in rules:
        checks.append(("liq_to_mc", metrics["liq_to_mc"], lambda v: v >= rules["min_liq_to_mc"]))
    if "min_vol_to_mc" in rules:
        checks.append(("vol_to_mc", metrics["vol_to_mc"], lambda v: v >= rules["min_vol_to_mc"]))
    if "min_buys" in rules:
        checks.append(("buys", metrics["buys"], lambda v: v >= rules["min_buys"]))
    elif metrics["buys"] is not None and "optional_min_buys" in rules:
        checks.append(("buys", metrics["buys"], lambda v: v >= rules["optional_min_buys"]))
    if "max_buys" in rules:
        checks.append(("buys_max", metrics["buys"], lambda v: v <= rules["max_buys"]))
    if "min_sol_volume" in rules:
        checks.append(("sol_volume", metrics["sol_volume"], lambda v: v >= rules["min_sol_volume"]))
    if "min_buy_sell_volume_ratio" in rules and metrics["buy_sell_volume_ratio"] is not None:
        checks.append(
            (
                "buy_sell_volume_ratio",
                metrics["buy_sell_volume_ratio"],
                lambda v: v >= rules["min_buy_sell_volume_ratio"],
            )
        )

    rejection_reason = _evaluate_checks(checks)
    return {
        **metrics,
        "strategy_name": strategy_filter.strategy_name,
        "filter_version": strategy_filter.filter_version,
        "telegram_label": strategy_filter.telegram_label,
        "filter_passed": int(rejection_reason is None),
        "rejection_reason": rejection_reason,
        "raw_metrics_json": json_dumps(metrics),
    }


def evaluate_all_strategy_filters(raw: dict[str, Any]) -> list[dict[str, Any]]:
    return [evaluate_strategy_filter(raw, strategy_filter) for strategy_filter in STRATEGY_FILTERS]
