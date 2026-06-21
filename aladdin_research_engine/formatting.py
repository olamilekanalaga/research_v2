from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .utils import human_money, human_multiple
from .utils import number_or_none, pick


FULL_WIDTH_BAR = "｜"


def _fmt_number(value: Any, decimals: int = 1) -> str:
    number = number_or_none(value)
    if number is None:
        return "n/a"
    if number.is_integer():
        return str(int(number))
    return f"{number:.{decimals}f}".rstrip("0").rstrip(".")


def _pct(value: Any, decimals: int = 2) -> str:
    number = number_or_none(value)
    if number is None:
        return "n/a"
    return f"{number:.{decimals}f}%"


def _short_money(value: Any) -> str:
    return human_money(value)


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


def _age_text(raw: dict[str, Any], fallback_minutes: Any = None) -> str:
    minutes = number_or_none(fallback_minutes)
    if minutes is None:
        timestamp = _timestamp_ms(
            pick(raw, "sentAt", "firstCallTime", "createdAt", "timestamp", "callAt")
        )
        if timestamp is not None:
            dt = datetime.fromtimestamp(timestamp / 1000, tz=timezone.utc)
            minutes = (datetime.now(timezone.utc) - dt).total_seconds() / 60
    if minutes is None:
        return "n/a"
    minutes = max(0, minutes)
    if minutes < 60:
        return f"{int(minutes)}m"
    return f"{minutes / 60:.1f}h"


def _social_text(raw: dict[str, Any]) -> str:
    social = pick(raw, "social", default={}) or {}
    social = social if isinstance(social, dict) else {}
    bits: list[str] = []
    if pick(social, "twitter", "x"):
        bits.append("𝕏")
    if pick(social, "telegram"):
        bits.append("Telegram")
    if pick(social, "website", "web"):
        bits.append("Website")
    return f" {FULL_WIDTH_BAR} ".join(bits) if bits else "n/a"


def _top_holder_row(raw: dict[str, Any]) -> str:
    holders = pick(raw, "holders", default={}) or {}
    holders = holders if isinstance(holders, dict) else {}
    candidates = pick(
        holders,
        "topHoldersPercent",
        "top_holders_percent",
        "topHolders",
        "top_holders",
        "top10",
        "top10Holders",
        "top10_holders",
        default=[],
    )
    if isinstance(candidates, dict):
        candidates = list(candidates.values())
    if not isinstance(candidates, list):
        return "n/a"

    values: list[str] = []
    for item in candidates[:10]:
        if isinstance(item, dict):
            value = number_or_none(
                pick(item, "percent", "percentage", "pct", "holdPercent", "hold_percent")
            )
        else:
            value = number_or_none(item)
        if value is not None:
            values.append(_fmt_number(value, 1))
    return f" {FULL_WIDTH_BAR} ".join(values) if values else "n/a"


def _dex_paid_text(raw: dict[str, Any]) -> str:
    audit = pick(raw, "audit", default={}) or {}
    audit = audit if isinstance(audit, dict) else {}
    return "✅" if pick(audit, "dexPaid", "dex_paid") else "❌"


def _dev_text(raw: dict[str, Any]) -> str:
    holders = pick(raw, "holders", default={}) or {}
    holders = holders if isinstance(holders, dict) else {}
    dev_hold = number_or_none(pick(holders, "devHoldPercent", "dev_hold_percent"))
    if dev_hold == 0:
        return "✅ Sold All"
    return _pct(dev_hold)


def alert_buy_button(mint: str | None) -> dict | None:
    if not mint:
        return None
    return {
        "inline_keyboard": [
            [
                {
                    "text": "Buy Token",
                    "url": f"https://t.me/hector_trojanbot?start=r-ola_crrypt-{mint}",
                }
            ]
        ]
    }


def format_alert(
    alert: dict[str, Any],
    enrichment: dict[str, Any] | None = None,
    raw: dict[str, Any] | None = None,
    filter_metrics: dict[str, Any] | None = None,
    passed_strategies: list[str] | None = None,
) -> str:
    raw = raw or {}
    filter_metrics = filter_metrics or {}
    holders = pick(raw, "holders", default={}) or {}
    holders = holders if isinstance(holders, dict) else {}

    symbol = alert.get("symbol") or pick(raw, "symbol") or "UNKNOWN"
    name = alert.get("name") or pick(raw, "name") or "Unknown token"
    mint = alert.get("mint") or pick(raw, "mint", "address") or "n/a"
    label = alert.get("label") or pick(raw, "label", "category") or "n/a"

    buy_volume_sol = (
        filter_metrics.get("sol_volume")
        or filter_metrics.get("buy_volume_sol")
        or alert.get("total_buy")
        or pick(raw, "totalBuy")
    )
    buys = filter_metrics.get("buys") or alert.get("count_buy") or pick(raw, "countBuy")
    total_fee = pick(raw, "totalFee", "total_fee") or alert.get("total_fee")
    total_fee_text = _fmt_number(total_fee, 2) if total_fee is not None else "n/a"

    volume_usd = filter_metrics.get("volume_usd") or alert.get("vol_1h") or pick(raw, "vol1h")
    strategy_block = []
    if passed_strategies:
        strategy_block = ["✅ Passed Strategies", "", *passed_strategies, ""]

    lines = [
        f"🚨 NEW ALERT: {_fmt_number(buy_volume_sol)} SOL in {_fmt_number(buys, 0)} buys ⚠️",
        "",
        *strategy_block,
        f"🌖 CA: {mint}",
        "",
        f"┌ {name} | #{symbol}",
        f"├ Label: {label}",
        f"├ MC: {_short_money(alert.get('market_cap') or pick(raw, 'marketCap'))}",
        f"├ Liq: {_short_money(alert.get('liquidity') or pick(raw, 'liquidity'))}",
        f"├ Vol: {_short_money(volume_usd)}  {FULL_WIDTH_BAR} Total Fees: {total_fee_text} SOL",
        f"├ Age: {_age_text(raw, filter_metrics.get('age_minutes'))}",
        f"└ Social: {_social_text(raw)}",
        "",
        f"┌ Holder: {pick(holders, 'total', 'holderCount', 'holders') or 'n/a'} | Top 10: {_pct(pick(holders, 'top10Percent', 'top10_percent'), 1)}",
        f"├ DEX Paid:  {_dex_paid_text(raw)}",
        f"├ Bundle:  {_pct(pick(holders, 'bundleHoldPercent', 'bundle_pct'), 2)}",
        f"├ Snipers:  {_pct(pick(holders, 'sniperHoldPercent', 'sniper_pct'), 2)}",
        f"├ Dev: {_dev_text(raw)}",
        f"└ {_top_holder_row(raw)}",
    ]
    return "\n".join(lines)


def format_milestone(
    symbol: str | None,
    milestone: float,
    call_mc: float | None,
    ath_mc: float | None,
    max_multiple: float | None,
    call_at: str | None,
) -> str:
    elapsed = "n/a"
    if call_at:
        try:
            call_dt = datetime.fromisoformat(call_at.replace("Z", "+00:00"))
            minutes = max(0, int((datetime.now(timezone.utc) - call_dt).total_seconds() / 60))
            elapsed = f"{minutes}m" if minutes < 60 else f"{minutes // 60}h {minutes % 60}m"
        except ValueError:
            elapsed = "n/a"
    return "\n".join(
        [
            f"🔥🔥🔥 {human_multiple(max_multiple or milestone)}",
            "",
            f"#{symbol or 'UNKNOWN'}  {human_money(call_mc)} ↗️ {human_money(ath_mc)} within {elapsed}",
            "",
            "credit: ⭕️La_Crrypt💰₿",
        ]
    )
