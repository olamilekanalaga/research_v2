from __future__ import annotations

import logging
from typing import Any

import httpx

from .config import Settings
from .db import json_dumps
from .utils import number_or_none, pick, utc_now_iso

logger = logging.getLogger(__name__)

TRADE_WINDOW_LABELS = (
    "pre_30m",
    "pre_10m",
    "pre_5m",
    "pre_1m",
    "post_1m",
    "post_5m",
    "post_10m",
    "post_30m",
)


class SolanaTrackerClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.client = httpx.AsyncClient(timeout=25)

    async def close(self) -> None:
        await self.client.aclose()

    async def enrich(self, notification_id: str, mint: str) -> dict[str, Any] | None:
        if not self.settings.solana_tracker_enabled():
            logger.info("Solana Tracker disabled; skipping enrichment for %s", mint)
            return None
        payload = await self._fetch_token(mint)
        if payload is None:
            return None
        return normalize_solana_tracker(notification_id, mint, payload)

    async def _fetch_token(self, mint: str) -> dict[str, Any] | None:
        headers = {"x-api-key": self.settings.solana_tracker_api_key}
        candidate_paths = [f"/tokens/{mint}", f"/token/{mint}"]
        for path in candidate_paths:
            try:
                response = await self.client.get(
                    f"{self.settings.solana_tracker_base_url}{path}", headers=headers
                )
                if response.status_code == 404:
                    continue
                response.raise_for_status()
                payload = response.json()
                return payload if isinstance(payload, dict) else {"data": payload}
            except Exception:
                logger.exception("Failed to fetch Solana Tracker data from %s", path)
                return None
        logger.warning("Solana Tracker token endpoint not found for %s", mint)
        return None

    async def enrich_trade_windows(
        self,
        notification_id: str,
        mint: str,
        strategy_names: list[str],
        alert_time: str | None,
    ) -> list[dict[str, Any]]:
        if not self.settings.solana_tracker_trade_windows_enabled():
            logger.info("Trade window enrichment skipped: endpoint template not configured.")
            return []
        payload = await self._fetch_trade_windows(mint, alert_time)
        if payload is None:
            return []
        return normalize_alert_trade_windows(
            notification_id=notification_id,
            mint=mint,
            strategy_names=strategy_names,
            alert_time=alert_time,
            payload=payload,
        )

    async def _fetch_trade_windows(
        self, mint: str, alert_time: str | None
    ) -> dict[str, Any] | None:
        headers = {"x-api-key": self.settings.solana_tracker_api_key}
        path = self.settings.solana_tracker_trade_windows_path_template.format(
            mint=mint,
            alert_time=alert_time or "",
        )
        try:
            response = await self.client.get(
                f"{self.settings.solana_tracker_base_url}{path}", headers=headers
            )
            if response.status_code == 404:
                logger.warning("Solana Tracker trade windows endpoint not found for %s", mint)
                return None
            response.raise_for_status()
            payload = response.json()
            return payload if isinstance(payload, dict) else {"data": payload}
        except Exception:
            logger.exception("Failed to fetch Solana Tracker trade windows for %s", mint)
            return None


def _window(payload: dict[str, Any], name: str) -> dict[str, Any]:
    txns = pick(payload, "txns", "transactions", default={}) or {}
    volume = pick(payload, "volume", "volumes", default={}) or {}
    buyers = pick(payload, "buyers", "uniqueBuyers", default={}) or {}
    window_data = pick(payload, name, f"{name}m", default={}) or {}
    txns = txns if isinstance(txns, dict) else {}
    volume = volume if isinstance(volume, dict) else {}
    buyers = buyers if isinstance(buyers, dict) else {}
    window_data = window_data if isinstance(window_data, dict) else {}
    return {
        "txns": pick(txns, name, f"{name}m", default={}) or {},
        "volume": pick(volume, name, f"{name}m", default={}) or {},
        "buyers": pick(buyers, name, f"{name}m", default=None),
        "direct": window_data,
    }


def normalize_solana_tracker(
    notification_id: str, mint: str, payload: dict[str, Any]
) -> dict[str, Any]:
    windows = {"1m": _window(payload, "1m"), "5m": _window(payload, "5m"), "10m": _window(payload, "10m")}
    row: dict[str, Any] = {
        "notification_id": notification_id,
        "mint": mint,
        "enriched_at": utc_now_iso(),
        "raw_json": json_dumps(payload),
    }
    for suffix, data in windows.items():
        txns = data["txns"]
        volume = data["volume"]
        direct = data["direct"]
        row[f"buy_count_{suffix}"] = int(
            number_or_none(pick(txns, "buys", "buy", "buyCount") or pick(direct, "buys", "buyCount"))
            or 0
        )
        row[f"sell_count_{suffix}"] = int(
            number_or_none(pick(txns, "sells", "sell", "sellCount") or pick(direct, "sells", "sellCount"))
            or 0
        )
        row[f"buy_volume_{suffix}_usd"] = number_or_none(
            pick(volume, "buyUsd", "buysUsd", "buy_volume_usd")
            or pick(direct, "buyUsd", "buy_volume_usd")
        )
        row[f"buy_volume_{suffix}_sol"] = number_or_none(
            pick(volume, "buySol", "buysSol", "buy_volume_sol")
            or pick(direct, "buySol", "buy_volume_sol")
        )
        sells_usd = number_or_none(
            pick(volume, "sellUsd", "sellsUsd", "sell_volume_usd")
            or pick(direct, "sellUsd", "sell_volume_usd")
        )
        row[f"net_buy_volume_{suffix}"] = (
            row[f"buy_volume_{suffix}_usd"] - sells_usd
            if row[f"buy_volume_{suffix}_usd"] is not None and sells_usd is not None
            else None
        )
        row[f"unique_buyers_{suffix}"] = int(
            number_or_none(data["buyers"] or pick(direct, "uniqueBuyers", "buyers")) or 0
        )
    row["top_buyer_share_10m"] = number_or_none(
        pick(payload, "topBuyerShare10m", "top_buyer_share_10m")
    )
    return row


def _trade_window_data(payload: dict[str, Any], label: str) -> dict[str, Any]:
    windows = pick(payload, "windows", "tradeWindows", "trade_windows", default={}) or {}
    windows = windows if isinstance(windows, dict) else {}
    direct = pick(payload, label, default={}) or {}
    direct = direct if isinstance(direct, dict) else {}
    window = pick(windows, label, default={}) or direct
    return window if isinstance(window, dict) else {}


def _normalize_trade_window_row(
    notification_id: str,
    mint: str,
    strategy_name: str,
    alert_time: str | None,
    window_label: str,
    data: dict[str, Any],
) -> dict[str, Any]:
    buy_volume_usd = number_or_none(
        pick(data, "buy_volume_usd", "buyVolumeUsd", "buyUsd", "buysUsd")
    )
    sell_volume_usd = number_or_none(
        pick(data, "sell_volume_usd", "sellVolumeUsd", "sellUsd", "sellsUsd")
    )
    buy_count = int(number_or_none(pick(data, "buy_count", "buyCount", "buys")) or 0)
    sell_count = int(number_or_none(pick(data, "sell_count", "sellCount", "sells")) or 0)
    return {
        "notification_id": notification_id,
        "mint": mint,
        "strategy_name": strategy_name,
        "alert_time": alert_time,
        "window_label": window_label,
        "buy_volume_usd": buy_volume_usd,
        "sell_volume_usd": sell_volume_usd,
        "net_volume_usd": (
            buy_volume_usd - sell_volume_usd
            if buy_volume_usd is not None and sell_volume_usd is not None
            else number_or_none(pick(data, "net_volume_usd", "netVolumeUsd", "netBuyVolumeUsd"))
        ),
        "buy_count": buy_count,
        "sell_count": sell_count,
        "unique_buyers": int(
            number_or_none(pick(data, "unique_buyers", "uniqueBuyers", "buyers")) or 0
        ),
        "unique_sellers": int(
            number_or_none(pick(data, "unique_sellers", "uniqueSellers", "sellers")) or 0
        ),
        "avg_buy_size_usd": (
            buy_volume_usd / buy_count
            if buy_volume_usd is not None and buy_count
            else number_or_none(pick(data, "avg_buy_size_usd", "avgBuySizeUsd"))
        ),
        "top_buyer_share": number_or_none(
            pick(data, "top_buyer_share", "topBuyerShare", "topBuyerSharePct")
        ),
        "created_at": utc_now_iso(),
        "raw_json": json_dumps(data),
    }


def normalize_alert_trade_windows(
    notification_id: str,
    mint: str,
    strategy_names: list[str],
    alert_time: str | None,
    payload: dict[str, Any],
) -> list[dict[str, Any]]:
    rows = []
    for strategy_name in strategy_names:
        for window_label in TRADE_WINDOW_LABELS:
            rows.append(
                _normalize_trade_window_row(
                    notification_id=notification_id,
                    mint=mint,
                    strategy_name=strategy_name,
                    alert_time=alert_time,
                    window_label=window_label,
                    data=_trade_window_data(payload, window_label),
                )
            )
    return rows
