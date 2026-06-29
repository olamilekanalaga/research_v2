from __future__ import annotations

import asyncio
import contextlib
import hashlib
import json
import logging
import os
import random
import signal
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import httpx
from dotenv import load_dotenv

try:
    import websockets
except ImportError as exc:  # pragma: no cover
    raise SystemExit(
        "Missing dependency: websockets. Run: .venv\\Scripts\\python.exe -m pip install -r requirements.txt"
    ) from exc

from aladdin_research_engine.normalizers import extract_signal_list, normalize_signal
from aladdin_research_engine.utils import number_or_none, pick
from migrate_vlak_long_run_schema import migrate
from vlak_survivor_telegram import SurvivorTelegramAlerts

ROOT = Path(__file__).resolve().parent
DEFAULT_DB_PATH = ROOT / "vlak_aladdin_research.sqlite"
DEFAULT_BASE_URL = "https://api.somehowissomewhere.uk"
DEFAULT_WS_URL = "wss://api.somehowissomewhere.uk/ws"
TRACKING_CHECKPOINTS = [1, 3, 5, 10, 15, 30, 60, 120, 1440]
LOG_DIR = ROOT / "logs"
REPORT_DIR = ROOT / "research_outputs" / "vlak_long_run_collector"


def utc_now() -> datetime:
    return datetime.now(UTC)


def utc_now_iso() -> str:
    return utc_now().isoformat(timespec="seconds")


def json_dumps(payload: Any) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True, default=str)


def payload_hash(payload: Any) -> str:
    return hashlib.sha256(json_dumps(payload).encode("utf-8")).hexdigest()


def redact(value: str | None) -> str:
    if not value:
        return ""
    if len(value) <= 8:
        return "[REDACTED]"
    return f"{value[:4]}...[REDACTED]...{value[-4:]}"


def env_value(name: str, default: str = "") -> str:
    value = os.getenv(name)
    if value:
        return value
    env_path = ROOT / ".env"
    if not env_path.exists():
        return default
    for line in env_path.read_text(encoding="utf-8-sig").splitlines():
        if not line or line.lstrip().startswith("#") or "=" not in line:
            continue
        key, raw_value = line.split("=", 1)
        if key.strip() == name:
            return raw_value.strip().strip('"').strip("'")
    return default


def parse_time(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    number = number_or_none(value)
    if number is not None:
        if number > 10_000_000_000:
            number /= 1000
        try:
            return datetime.fromtimestamp(number, UTC)
        except (OverflowError, OSError, ValueError):
            return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return parsed.astimezone(UTC) if parsed.tzinfo else parsed.replace(tzinfo=UTC)
    except ValueError:
        return None


def to_iso(value: Any) -> str | None:
    parsed = parse_time(value)
    return parsed.isoformat(timespec="seconds") if parsed else (str(value) if value else None)


def missing_fields(row: dict[str, Any], fields: list[str]) -> str:
    return ";".join(field for field in fields if row.get(field) in (None, ""))


def extract_holders(raw: dict[str, Any]) -> dict[str, Any]:
    holders = pick(raw, "holders", "holderStats", default={}) or {}
    return holders if isinstance(holders, dict) else {}


def extract_trackers(raw: dict[str, Any]) -> dict[str, Any]:
    trackers = pick(raw, "trackers", default={}) or {}
    return trackers if isinstance(trackers, dict) else {}


def normalized_alert_metrics(raw: dict[str, Any]) -> dict[str, Any]:
    alert = normalize_signal(raw)
    holders = extract_holders(raw)
    trackers = extract_trackers(raw)
    alert_time = to_iso(alert.get("first_call_time") or alert.get("sent_at") or alert.get("created_at"))
    alert_dt = parse_time(alert_time)
    capture_lag = (utc_now() - alert_dt).total_seconds() if alert_dt else None
    market_cap = number_or_none(alert.get("market_cap"))
    first_call_mc = number_or_none(alert.get("first_call_market_cap"))
    liquidity = number_or_none(alert.get("liquidity"))
    volume = number_or_none(alert.get("vol_1h"))
    buys = int(number_or_none(alert.get("count_buy")) or 0)
    buy_volume_sol = number_or_none(pick(trackers, "totalBuy", "total_buy", "buyVolumeSol") or alert.get("total_buy"))
    sell_volume_sol = number_or_none(pick(trackers, "totalSell", "total_sell", "sellVolumeSol"))
    return {
        "notification_id": alert.get("notification_id"),
        "mint": alert.get("mint"),
        "symbol": alert.get("symbol"),
        "name": alert.get("name"),
        "alert_time": alert_time,
        "first_call_market_cap": first_call_mc,
        "market_cap": market_cap,
        "liquidity": liquidity,
        "price": number_or_none(alert.get("price_usd")),
        "volume": volume,
        "buy_volume_sol": buy_volume_sol,
        "sell_volume_sol": sell_volume_sol,
        "buys": buys,
        "holders": int(number_or_none(pick(holders, "total", "holderCount", "holders")) or 0) or None,
        "bundle_percent": number_or_none(pick(holders, "bundleHoldPercent", "bundle_pct")),
        "sniper_percent": number_or_none(pick(holders, "sniperHoldPercent", "sniper_pct")),
        "top10_percent": number_or_none(pick(holders, "top10Percent", "top10_percent")),
        "liq_to_mc": liquidity / market_cap if liquidity and market_cap else None,
        "vol_to_mc": volume / market_cap if volume and market_cap else None,
        "avg_buy_size_sol": buy_volume_sol / buys if buy_volume_sol is not None and buys else None,
        "capture_lag_seconds": capture_lag,
        "raw_json": json_dumps(raw),
        "raw_payload_hash": payload_hash(raw),
    }


def nested_number(payload: dict[str, Any], *paths: tuple[str, ...]) -> float | None:
    for path in paths:
        current: Any = payload
        for part in path:
            if not isinstance(current, dict):
                current = None
                break
            current = current.get(part)
        value = number_or_none(current)
        if value is not None:
            return value
    return None


def outcome_max_market_cap(payload: dict[str, Any]) -> float | None:
    candidates: list[float] = []
    for value in [
        nested_number(payload, ("currentMc",), ("current_mc",)),
        nested_number(payload, ("marketCap",), ("market_cap",), ("pool", "marketCap")),
        nested_number(payload, ("athMarketCap",), ("ath_mc",), ("athMc",)),
    ]:
        if value is not None:
            candidates.append(value)
    outcome = payload.get("outcome") if isinstance(payload.get("outcome"), dict) else {}
    for key in ("max_mc_10m", "max_mc_30m", "max_mc_1h", "max_mc_24h"):
        value = number_or_none(outcome.get(key))
        if value is not None:
            candidates.append(value)
    milestones = payload.get("milestones") if isinstance(payload.get("milestones"), dict) else {}
    nested = milestones.get("milestones") if isinstance(milestones.get("milestones"), dict) else {}
    for item in list(nested.values()) + list(milestones.get("timeline", []) if isinstance(milestones.get("timeline"), list) else []):
        if isinstance(item, dict):
            value = number_or_none(item.get("mc"))
            if value is not None:
                candidates.append(value)
    return max(candidates) if candidates else None


def normalized_outcome_metrics(mint: str, payload: dict[str, Any]) -> dict[str, Any]:
    pool = payload.get("pool") if isinstance(payload.get("pool"), dict) else {}
    current_mc = nested_number(payload, ("currentMc",), ("current_mc",), ("pool", "marketCap"))
    call_mc = nested_number(payload, ("firstCallMarketCap",), ("first_call_market_cap",), ("callMc",))
    ath_mc = outcome_max_market_cap(payload)
    explicit_multiple = nested_number(payload, ("maxMultiple",), ("max_multiple",))
    computed_multiple = (ath_mc / call_mc) if ath_mc is not None and call_mc else None
    return {
        "mint": mint,
        "snapshot_time": utc_now_iso(),
        "current_mc": current_mc,
        "first_call_market_cap": call_mc,
        "ath_market_cap": ath_mc,
        "max_multiple": explicit_multiple if explicit_multiple is not None else computed_multiple,
        "liquidity": nested_number(payload, ("liquidity",), ("pool", "liquidUsd")),
        "price": nested_number(payload, ("price",), ("priceUsd",), ("pool", "priceUsd")),
        "market_cap": nested_number(payload, ("marketCap",), ("market_cap",), ("pool", "marketCap")),
        "updated_at": str(payload.get("updatedAt") or payload.get("updated_at") or pool.get("updatedAt") or "") or None,
        "raw_json": json_dumps(payload),
        "raw_payload_hash": payload_hash(payload),
    }

@dataclass(frozen=True)
class CollectorConfig:
    api_key: str
    db_path: Path
    base_url: str = DEFAULT_BASE_URL
    websocket_url: str = DEFAULT_WS_URL
    rest_min_interval_seconds: float = 1.5
    websocket_reconnect_min_seconds: float = 2.0
    websocket_reconnect_max_seconds: float = 60.0
    outcome_retry_limit: int = 3

    @classmethod
    def from_env(cls) -> "CollectorConfig":
        load_dotenv(ROOT / ".env")
        api_key = env_value("VLAK_API_KEY").strip()
        if not api_key:
            raise RuntimeError("Missing VLAK_API_KEY in environment or .env")
        return cls(
            api_key=api_key,
            db_path=Path(env_value("DATABASE_PATH", str(DEFAULT_DB_PATH))),
            base_url=env_value("VLAK_BASE_URL", DEFAULT_BASE_URL).rstrip("/"),
            websocket_url=env_value("VLAK_WS_URL", DEFAULT_WS_URL).rstrip("?"),
        )


class VlakLongRunCollector:
    def __init__(self, config: CollectorConfig) -> None:
        self.config = config
        self.stop_event = asyncio.Event()
        self.last_websocket_message_at: str | None = None
        self.last_outcome_refresh_at: str | None = None
        self.http = httpx.AsyncClient(timeout=30)
        self.survivor_alerts = SurvivorTelegramAlerts(self.config.db_path)
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        REPORT_DIR.mkdir(parents=True, exist_ok=True)
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s %(levelname)s %(name)s %(message)s",
            handlers=[
                logging.FileHandler(LOG_DIR / "vlak_long_run_collector.log", encoding="utf-8"),
                logging.StreamHandler(),
            ],
        )
        self.logger = logging.getLogger("vlak_long_run_collector")
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("httpcore").setLevel(logging.WARNING)

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.config.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def ws_url_with_key(self) -> str:
        sep = "&" if "?" in self.config.websocket_url else "?"
        return f"{self.config.websocket_url}{sep}apikey={self.config.api_key}"

    def audit_payload(
        self,
        conn: sqlite3.Connection,
        source: str,
        endpoint: str,
        method: str,
        payload: Any,
        *,
        mint: str | None = None,
        notification_id: str | None = None,
        status_code: int | None = None,
        success: bool = True,
        api_error: str | None = None,
    ) -> None:
        keys = sorted(str(key) for key in payload.keys()) if isinstance(payload, dict) else []
        raw = json_dumps(payload)
        conn.execute(
            """
            INSERT INTO vlak_api_payload_audit
            (received_at, source, endpoint, method, mint, notification_id, status_code, success, api_error, raw_payload_hash, payload_bytes, top_level_keys)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (utc_now_iso(), source, endpoint, method, mint, notification_id, status_code, int(success), api_error, payload_hash(payload), len(raw.encode("utf-8")), ";".join(keys)),
        )

    def log_error(
        self,
        conn: sqlite3.Connection,
        source: str,
        message: str,
        *,
        endpoint: str | None = None,
        mint: str | None = None,
        notification_id: str | None = None,
        error_type: str = "error",
        retry_count: int = 0,
        payload: Any | None = None,
    ) -> None:
        conn.execute(
            """
            INSERT INTO vlak_ingestion_errors
            (occurred_at, source, endpoint, mint, notification_id, error_type, error_message, retry_count, raw_payload_hash, raw_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (utc_now_iso(), source, endpoint, mint, notification_id, error_type, message[:1000], retry_count, payload_hash(payload) if payload is not None else None, json_dumps(payload) if payload is not None else None),
        )

    def save_metric_snapshot(self, conn: sqlite3.Connection, metrics: dict[str, Any], snapshot_kind: str, source: str, is_clean: int, missing: str | None) -> None:
        conn.execute(
            """
            INSERT INTO vlak_metric_snapshots
            (notification_id, mint, snapshot_time, snapshot_kind, first_call_market_cap, market_cap, liquidity, price, volume, buy_volume_sol, sell_volume_sol, buys, sells, holders, bundle_percent, sniper_percent, top10_percent, liq_to_mc, vol_to_mc, avg_buy_size_sol, max_multiple, source, capture_lag_seconds, is_clean_snapshot, missing_fields, api_error, raw_payload_hash, raw_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, ?, ?, ?, ?, ?, ?, ?, NULL, ?, ?, ?, ?, NULL, ?, ?)
            """,
            (metrics.get("notification_id"), metrics.get("mint"), utc_now_iso(), snapshot_kind, metrics.get("first_call_market_cap"), metrics.get("market_cap"), metrics.get("liquidity"), metrics.get("price"), metrics.get("volume"), metrics.get("buy_volume_sol"), metrics.get("sell_volume_sol"), metrics.get("buys"), metrics.get("holders"), metrics.get("bundle_percent"), metrics.get("sniper_percent"), metrics.get("top10_percent"), metrics.get("liq_to_mc"), metrics.get("vol_to_mc"), metrics.get("avg_buy_size_sol"), source, metrics.get("capture_lag_seconds"), is_clean, missing, metrics.get("raw_payload_hash"), metrics.get("raw_json")),
        )

    def create_tracking_schedule(self, conn: sqlite3.Connection, mint: str, alert_time: str) -> None:
        alert_dt = parse_time(alert_time) or utc_now()
        now = utc_now_iso()
        for minutes in TRACKING_CHECKPOINTS:
            due_at = (alert_dt + timedelta(minutes=minutes)).isoformat(timespec="seconds")
            label = f"{int(minutes)}m" if minutes < 1440 else "24h"
            conn.execute(
                """
                INSERT OR IGNORE INTO vlak_tracking_schedule
                (mint, first_alert_time, checkpoint_label, checkpoint_minutes, due_at, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (mint, alert_dt.isoformat(timespec="seconds"), label, minutes, due_at, now),
            )

    def save_alert(self, raw: dict[str, Any]) -> str | None:
        metrics = normalized_alert_metrics(raw)
        mint = metrics.get("mint")
        if not mint:
            with self.connect() as conn:
                self.log_error(conn, "vlak_websocket", "Missing mint in websocket signal", payload=raw)
                self.audit_payload(conn, "vlak_websocket", "websocket", "MESSAGE", raw, success=False, api_error="missing_mint")
                conn.commit()
            return None
        with self.connect() as conn:
            existing_for_mint = conn.execute("SELECT COUNT(1) FROM vlak_alert_events WHERE mint = ?", (mint,)).fetchone()[0]
            duplicate_count = conn.execute("SELECT COUNT(1) FROM vlak_alert_events WHERE notification_id = ?", (metrics.get("notification_id"),)).fetchone()[0] if metrics.get("notification_id") else 0
            is_first = existing_for_mint == 0
            capture_lag = metrics.get("capture_lag_seconds")
            is_clean = bool(is_first and capture_lag is not None and capture_lag <= 300)
            missing = missing_fields(metrics, ["mint", "alert_time", "first_call_market_cap", "market_cap", "liquidity", "volume", "buys"])
            conn.execute(
                """
                INSERT OR IGNORE INTO vlak_alert_events
                (notification_id, mint, symbol, name, alert_time, first_call_market_cap, market_cap, liquidity, volume, buys, holders, bundle_percent, sniper_percent, top10_percent, source, inserted_at, capture_lag_seconds, is_first_alert_per_mint, is_clean_first_snapshot, missing_fields, api_error, duplicate_alert_count, raw_payload_hash, raw_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'vlak_websocket', ?, ?, ?, ?, ?, NULL, ?, ?, ?)
                """,
                (metrics.get("notification_id"), mint, metrics.get("symbol"), metrics.get("name"), metrics.get("alert_time"), metrics.get("first_call_market_cap"), metrics.get("market_cap"), metrics.get("liquidity"), metrics.get("volume"), metrics.get("buys"), metrics.get("holders"), metrics.get("bundle_percent"), metrics.get("sniper_percent"), metrics.get("top10_percent"), utc_now_iso(), capture_lag, int(is_first), int(is_clean), missing, duplicate_count, metrics.get("raw_payload_hash"), metrics.get("raw_json")),
            )
            inserted = conn.execute("SELECT changes()").fetchone()[0]
            self.save_metric_snapshot(conn, metrics, "alert", "vlak_websocket", int(is_clean), missing)
            self.audit_payload(conn, "vlak_websocket", "websocket", "MESSAGE", raw, mint=mint, notification_id=metrics.get("notification_id"))
            if inserted:
                self.create_tracking_schedule(conn, mint, metrics.get("alert_time") or utc_now_iso())
            conn.commit()
        return mint

    async def websocket_loop(self) -> None:
        delay = self.config.websocket_reconnect_min_seconds
        safe_url = self.ws_url_with_key().replace(self.config.api_key, "[REDACTED]")
        while not self.stop_event.is_set():
            try:
                self.logger.info("Connecting Vlak websocket %s", safe_url)
                async with websockets.connect(self.ws_url_with_key(), ping_interval=20, ping_timeout=20, close_timeout=10) as ws:
                    delay = self.config.websocket_reconnect_min_seconds
                    async for message in ws:
                        self.last_websocket_message_at = utc_now_iso()
                        try:
                            payload = json.loads(message) if isinstance(message, str) else json.loads(message.decode("utf-8"))
                        except Exception as exc:
                            with self.connect() as conn:
                                self.log_error(conn, "vlak_websocket", f"Invalid JSON websocket payload: {exc}", payload={"message": str(message)[:1000]})
                                conn.commit()
                            continue
                        for raw in extract_signal_list(payload):
                            mint = self.save_alert(raw)
                            if mint:
                                self.logger.info("Captured Vlak websocket signal mint=%s", mint)
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                self.logger.warning("Websocket disconnected/error: %s", exc)
                with self.connect() as conn:
                    self.log_error(conn, "vlak_websocket", str(exc), endpoint="websocket", error_type=type(exc).__name__)
                    conn.commit()
                await asyncio.sleep(delay + random.random())
                delay = min(delay * 2, self.config.websocket_reconnect_max_seconds)

    async def fetch_outcome(self, mint: str) -> tuple[dict[str, Any] | None, str | None, int | None]:
        url = f"{self.config.base_url}/api/signal/{mint}/outcome"
        for attempt in range(1, self.config.outcome_retry_limit + 1):
            try:
                response = await self.http.get(url, params={"apikey": self.config.api_key})
                if response.status_code == 429:
                    await asyncio.sleep(min(30, 2 * attempt))
                    continue
                response.raise_for_status()
                payload = response.json()
                return (payload if isinstance(payload, dict) else {"data": payload}, None, response.status_code)
            except Exception as exc:
                if attempt >= self.config.outcome_retry_limit:
                    return None, str(exc), getattr(getattr(exc, "response", None), "status_code", None)
                await asyncio.sleep(min(30, 2**attempt))
        return None, "retry_exhausted", None

    def save_outcome(self, mint: str, payload: dict[str, Any], status_code: int | None = None) -> None:
        metrics = normalized_outcome_metrics(mint, payload)
        missing = missing_fields(metrics, ["current_mc", "first_call_market_cap", "ath_market_cap", "max_multiple"])
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO vlak_outcome_snapshots
                (mint, snapshot_time, current_mc, first_call_market_cap, ath_market_cap, max_multiple, liquidity, price, market_cap, updated_at, source, api_error, missing_fields, raw_payload_hash, raw_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'vlak_outcome_endpoint', NULL, ?, ?, ?)
                """,
                (mint, metrics.get("snapshot_time"), metrics.get("current_mc"), metrics.get("first_call_market_cap"), metrics.get("ath_market_cap"), metrics.get("max_multiple"), metrics.get("liquidity"), metrics.get("price"), metrics.get("market_cap"), metrics.get("updated_at"), missing, metrics.get("raw_payload_hash"), metrics.get("raw_json")),
            )
            self.audit_payload(conn, "vlak_outcome_endpoint", f"/api/signal/{mint}/outcome", "GET", payload, mint=mint, status_code=status_code)
            self.upsert_latest_outcome(conn, metrics)
            conn.commit()
        self.last_outcome_refresh_at = utc_now_iso()

    def upsert_latest_outcome(self, conn: sqlite3.Connection, metrics: dict[str, Any]) -> None:
        mint = metrics["mint"]
        first = conn.execute("SELECT alert_time, first_call_market_cap FROM vlak_alert_events WHERE mint = ? ORDER BY alert_time ASC, id ASC LIMIT 1", (mint,)).fetchone()
        first_alert_time = first["alert_time"] if first else None
        first_call_mc = metrics.get("first_call_market_cap") or (first["first_call_market_cap"] if first else None)
        max_multiple = metrics.get("max_multiple")
        completed_24h = 0
        if first_alert_time:
            first_dt = parse_time(first_alert_time)
            completed_24h = int(bool(first_dt and utc_now() >= first_dt + timedelta(hours=24)))
        conn.execute(
            """
            INSERT INTO vlak_token_outcomes
            (mint, first_alert_time, first_call_market_cap, latest_snapshot_time, current_mc, ath_market_cap, max_multiple, hit_2x, hit_5x, hit_10x, rugged, completed_24h, updated_at, raw_payload_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, ?, ?, ?)
            ON CONFLICT(mint) DO UPDATE SET
                first_alert_time=excluded.first_alert_time,
                first_call_market_cap=excluded.first_call_market_cap,
                latest_snapshot_time=excluded.latest_snapshot_time,
                current_mc=excluded.current_mc,
                ath_market_cap=excluded.ath_market_cap,
                max_multiple=excluded.max_multiple,
                hit_2x=excluded.hit_2x,
                hit_5x=excluded.hit_5x,
                hit_10x=excluded.hit_10x,
                completed_24h=excluded.completed_24h,
                updated_at=excluded.updated_at,
                raw_payload_hash=excluded.raw_payload_hash
            """,
            (mint, first_alert_time, first_call_mc, metrics.get("snapshot_time"), metrics.get("current_mc"), metrics.get("ath_market_cap"), max_multiple, int(bool(max_multiple is not None and max_multiple >= 2)), int(bool(max_multiple is not None and max_multiple >= 5)), int(bool(max_multiple is not None and max_multiple >= 10)), completed_24h, utc_now_iso(), metrics.get("raw_payload_hash")),
        )

    async def outcome_loop(self) -> None:
        while not self.stop_event.is_set():
            with self.connect() as conn:
                due = conn.execute(
                    """
                    SELECT id, mint, attempts
                    FROM vlak_tracking_schedule
                    WHERE completed_at IS NULL AND datetime(due_at) <= datetime('now')
                    ORDER BY datetime(due_at) ASC
                    LIMIT 25
                    """
                ).fetchall()
            if not due:
                await asyncio.sleep(10)
                continue
            for row in due:
                if self.stop_event.is_set():
                    break
                mint = row["mint"]
                payload, error, status_code = await self.fetch_outcome(mint)
                with self.connect() as conn:
                    conn.execute("UPDATE vlak_tracking_schedule SET attempts = attempts + 1 WHERE id = ?", (row["id"],))
                    if payload is None:
                        conn.execute("UPDATE vlak_tracking_schedule SET last_error = ? WHERE id = ?", (error, row["id"]))
                        self.log_error(conn, "vlak_outcome_endpoint", error or "unknown outcome error", endpoint=f"/api/signal/{mint}/outcome", mint=mint, retry_count=int(row["attempts"] or 0) + 1)
                        self.audit_payload(conn, "vlak_outcome_endpoint", f"/api/signal/{mint}/outcome", "GET", {"error": error}, mint=mint, status_code=status_code, success=False, api_error=error)
                    else:
                        conn.execute("UPDATE vlak_tracking_schedule SET completed_at = ?, last_error = NULL WHERE id = ?", (utc_now_iso(), row["id"]))
                    conn.commit()
                if payload is not None:
                    self.save_outcome(mint, payload, status_code=status_code)
                    await self.survivor_alerts.process_mint(mint)
                await asyncio.sleep(self.config.rest_min_interval_seconds)

    async def heartbeat_loop(self) -> None:
        while not self.stop_event.is_set():
            self.logger.info(
                "heartbeat db=%s last_ws=%s last_outcome=%s api_key=%s",
                self.config.db_path,
                self.last_websocket_message_at,
                self.last_outcome_refresh_at,
                redact(self.config.api_key),
            )
            await self.write_daily_report()
            await asyncio.sleep(3600)

    async def write_daily_report(self) -> None:
        today = utc_now().date().isoformat()
        day_start = f"{today}T00:00:00+00:00"
        with self.connect() as conn:
            values = self.daily_summary_values(conn, day_start)
            report = self.render_daily_report(today, values)
            conn.execute(
                """
                INSERT INTO vlak_daily_summaries
                (report_date, generated_at, new_alerts_collected, unique_mints_collected, outcome_snapshots_collected, completed_24h_outcomes, rate_2x, rate_5x, rate_10x, missing_field_rates_json, ingestion_errors, db_size_bytes, last_websocket_message_at, last_outcome_refresh_at, report_markdown)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(report_date) DO UPDATE SET
                    generated_at=excluded.generated_at,
                    new_alerts_collected=excluded.new_alerts_collected,
                    unique_mints_collected=excluded.unique_mints_collected,
                    outcome_snapshots_collected=excluded.outcome_snapshots_collected,
                    completed_24h_outcomes=excluded.completed_24h_outcomes,
                    rate_2x=excluded.rate_2x,
                    rate_5x=excluded.rate_5x,
                    rate_10x=excluded.rate_10x,
                    missing_field_rates_json=excluded.missing_field_rates_json,
                    ingestion_errors=excluded.ingestion_errors,
                    db_size_bytes=excluded.db_size_bytes,
                    last_websocket_message_at=excluded.last_websocket_message_at,
                    last_outcome_refresh_at=excluded.last_outcome_refresh_at,
                    report_markdown=excluded.report_markdown
                """,
                (today, utc_now_iso(), values["new_alerts"], values["unique_mints"], values["outcome_snapshots"], values["completed_24h"], values["rate_2x"], values["rate_5x"], values["rate_10x"], json_dumps(values["missing_rates"]), values["errors"], values["db_size"], self.last_websocket_message_at, self.last_outcome_refresh_at, report),
            )
            conn.commit()
        (REPORT_DIR / f"vlak_daily_summary_{today}.md").write_text(report, encoding="utf-8")

    def daily_summary_values(self, conn: sqlite3.Connection, day_start: str) -> dict[str, Any]:
        new_alerts = conn.execute("SELECT COUNT(1) FROM vlak_alert_events WHERE inserted_at >= ?", (day_start,)).fetchone()[0]
        unique_mints = conn.execute("SELECT COUNT(DISTINCT mint) FROM vlak_alert_events WHERE inserted_at >= ?", (day_start,)).fetchone()[0]
        outcome_snapshots = conn.execute("SELECT COUNT(1) FROM vlak_outcome_snapshots WHERE snapshot_time >= ?", (day_start,)).fetchone()[0]
        completed_24h = conn.execute("SELECT COUNT(1) FROM vlak_token_outcomes WHERE completed_24h = 1").fetchone()[0]
        row = conn.execute("SELECT AVG(hit_2x), AVG(hit_5x), AVG(hit_10x) FROM vlak_token_outcomes WHERE max_multiple IS NOT NULL").fetchone()
        errors = conn.execute("SELECT COUNT(1) FROM vlak_ingestion_errors WHERE occurred_at >= ?", (day_start,)).fetchone()[0]
        missing_rates: dict[str, float] = {}
        if new_alerts:
            for field in ["first_call_market_cap", "market_cap", "liquidity", "volume", "buys", "holders", "bundle_percent", "sniper_percent", "top10_percent"]:
                count = conn.execute(f"SELECT COUNT(1) FROM vlak_alert_events WHERE inserted_at >= ? AND {field} IS NULL", (day_start,)).fetchone()[0]
                missing_rates[field] = count / new_alerts
        return {
            "new_alerts": new_alerts,
            "unique_mints": unique_mints,
            "outcome_snapshots": outcome_snapshots,
            "completed_24h": completed_24h,
            "rate_2x": row[0] if row else None,
            "rate_5x": row[1] if row else None,
            "rate_10x": row[2] if row else None,
            "missing_rates": missing_rates,
            "errors": errors,
            "db_size": self.config.db_path.stat().st_size if self.config.db_path.exists() else 0,
        }

    def render_daily_report(self, today: str, values: dict[str, Any]) -> str:
        def pct(value: Any) -> str:
            return "n/a" if value is None else f"{float(value) * 100:.2f}%"

        missing_lines = "\n".join(f"- {key}: {pct(value)}" for key, value in sorted(values["missing_rates"].items())) or "- n/a"
        return f"""# Vlak Long-Run Daily Summary - {today}

- New alerts collected: {values['new_alerts']}
- Unique mints collected: {values['unique_mints']}
- Outcome snapshots collected: {values['outcome_snapshots']}
- Completed 24h outcomes: {values['completed_24h']}
- 2x rate: {pct(values['rate_2x'])}
- 5x rate: {pct(values['rate_5x'])}
- 10x rate: {pct(values['rate_10x'])}
- Ingestion errors today: {values['errors']}
- DB size bytes: {values['db_size']}
- Last successful WebSocket message time: {self.last_websocket_message_at or 'n/a'}
- Last successful outcome refresh time: {self.last_outcome_refresh_at or 'n/a'}

## Missing Field Rates Today

{missing_lines}
"""

    async def run(self) -> None:
        migrate(self.config.db_path)
        self.logger.info(
            "Starting Vlak long-run collector db=%s base_url=%s ws=%s api_key=%s",
            self.config.db_path,
            self.config.base_url,
            self.config.websocket_url,
            redact(self.config.api_key),
        )
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            with contextlib.suppress(NotImplementedError):
                loop.add_signal_handler(sig, self.stop_event.set)
        tasks = [
            asyncio.create_task(self.websocket_loop()),
            asyncio.create_task(self.outcome_loop()),
            asyncio.create_task(self.heartbeat_loop()),
        ]
        await self.stop_event.wait()
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        await self.http.aclose()
        await self.survivor_alerts.close()
        await self.write_daily_report()
        self.logger.info("Stopped Vlak long-run collector")


async def main() -> None:
    collector = VlakLongRunCollector(CollectorConfig.from_env())
    await collector.run()


if __name__ == "__main__":
    asyncio.run(main())




