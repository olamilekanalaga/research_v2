from __future__ import annotations

import asyncio
import logging
import os
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
SURVIVOR_THRESHOLDS = [1.5, 2, 3, 4, 5, 10]
MILESTONE_THRESHOLDS = [2, 3, 4, 5, 10]

logger = logging.getLogger(__name__)


def utc_now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


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


def bool_env(name: str, default: bool) -> bool:
    raw = env_value(name, "")
    if raw == "":
        return default
    return raw.strip().lower() in {"1", "true", "yes", "y", "on"}


def parse_time(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return parsed.astimezone(UTC) if parsed.tzinfo else parsed.replace(tzinfo=UTC)
    except ValueError:
        return None


def elapsed_text(start: Any, end: Any | None = None) -> str:
    start_dt = parse_time(start)
    end_dt = parse_time(end) if end else datetime.now(UTC)
    if not start_dt or not end_dt:
        return "n/a"
    seconds = max(0, int((end_dt - start_dt).total_seconds()))
    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes}m"
    hours = minutes // 60
    remain = minutes % 60
    if hours < 48:
        return f"{hours}h {remain}m"
    days = hours // 24
    return f"{days}d {hours % 24}h"


def fmt_money(value: Any) -> str:
    if value is None:
        return "n/a"
    try:
        value = float(value)
    except (TypeError, ValueError):
        return "n/a"
    if value >= 1_000_000:
        return f"${value / 1_000_000:.2f}M"
    if value >= 1_000:
        return f"${value / 1_000:.1f}K"
    return f"${value:.0f}"


def fmt_multiple(value: Any) -> str:
    if value is None:
        return "n/a"
    try:
        return f"{float(value):.2f}x"
    except (TypeError, ValueError):
        return "n/a"


def gmgn_link(mint: str) -> str:
    return f"https://gmgn.ai/sol/token/{mint}"


class SurvivorTelegramAlerts:
    def __init__(self, db_path: Path) -> None:
        load_dotenv(ROOT / ".env")
        self.db_path = db_path
        self.bot_token = env_value("TELEGRAM_BOT_TOKEN")
        self.chat_id = env_value("TELEGRAM_CHAT_ID")
        self.enabled = bool_env("TELEGRAM_SURVIVOR_ALERTS_ENABLED", False)
        self.dry_run = bool_env("TELEGRAM_SURVIVOR_DRY_RUN", True)
        self.client = httpx.AsyncClient(timeout=20)

    async def close(self) -> None:
        await self.client.aclose()

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def telegram_ready(self) -> bool:
        return bool(self.bot_token and self.chat_id)

    async def send_message(self, text: str, reply_to_message_id: int | None = None) -> int | None:
        if not self.enabled or self.dry_run:
            logger.info("Survivor Telegram dry/disabled: would send reply_to=%s text=%s", reply_to_message_id, text[:160])
            return None
        if not self.telegram_ready():
            logger.warning("Survivor Telegram enabled but TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID missing")
            return None
        payload: dict[str, Any] = {
            "chat_id": self.chat_id,
            "text": text,
            "disable_web_page_preview": True,
        }
        if reply_to_message_id is not None:
            payload["reply_to_message_id"] = int(reply_to_message_id)
            payload["allow_sending_without_reply"] = False
        response = await self.client.post(f"https://api.telegram.org/bot{self.bot_token}/sendMessage", json=payload)
        response.raise_for_status()
        message_id = response.json().get("result", {}).get("message_id")
        return int(message_id) if message_id is not None else None

    def load_token(self, conn: sqlite3.Connection, mint: str) -> sqlite3.Row | None:
        return conn.execute(
            """
            SELECT
                o.mint,
                e.symbol,
                e.name,
                e.alert_time,
                o.first_alert_time,
                COALESCE(o.first_call_market_cap, e.first_call_market_cap) AS first_call_market_cap,
                e.market_cap AS first_alert_market_cap,
                o.current_mc,
                o.ath_market_cap,
                o.max_multiple,
                o.latest_snapshot_time
            FROM vlak_token_outcomes o
            LEFT JOIN (
                SELECT * FROM vlak_alert_events WHERE is_first_alert_per_mint = 1
            ) e ON e.mint = o.mint
            WHERE o.mint = ?
            """,
            (mint,),
        ).fetchone()

    def format_root_message(self, row: sqlite3.Row) -> str:
        symbol = row["symbol"] or "UNKNOWN"
        name = row["name"] or symbol
        first_mc = row["first_call_market_cap"] or row["first_alert_market_cap"]
        return "\n".join(
            [
                "VLAK SURVIVOR ALERT - 1.5x",
                "",
                f"Token: {name} (${symbol})",
                f"CA: {row['mint']}",
                f"Current multiple: {fmt_multiple(row['max_multiple'])}",
                f"First call MC: {fmt_money(first_mc)}",
                f"Current MC: {fmt_money(row['current_mc'])}",
                f"ATH MC: {fmt_money(row['ath_market_cap'])}",
                f"Time since Vlak call: {elapsed_text(row['first_alert_time'] or row['alert_time'], row['latest_snapshot_time'])}",
                f"GMGN: {gmgn_link(row['mint'])}",
            ]
        )

    def format_milestone_message(self, row: sqlite3.Row, threshold: float, first_alerted_at: str | None) -> str:
        symbol = row["symbol"] or "UNKNOWN"
        return "\n".join(
            [
                f"Milestone update: {threshold:g}x hit",
                "",
                f"Token: ${symbol}",
                f"CA: {row['mint']}",
                f"Current multiple: {fmt_multiple(row['max_multiple'])}",
                f"ATH multiple: {fmt_multiple(row['max_multiple'])}",
                f"Time from 1.5x alert: {elapsed_text(first_alerted_at)}",
                f"GMGN: {gmgn_link(row['mint'])}",
            ]
        )

    async def process_mint(self, mint: str) -> None:
        if not self.enabled:
            return
        with self.connect() as conn:
            row = self.load_token(conn, mint)
            if row is None or row["max_multiple"] is None or float(row["max_multiple"]) < 1.5:
                return
            thread = conn.execute("SELECT * FROM telegram_survivor_threads WHERE mint = ?", (mint,)).fetchone()

        if thread is None:
            await self.send_root_alert(mint)

        with self.connect() as conn:
            row = self.load_token(conn, mint)
            thread = conn.execute("SELECT * FROM telegram_survivor_threads WHERE mint = ?", (mint,)).fetchone()
            if row is None or thread is None or thread["root_message_id"] is None:
                return
            max_multiple = float(row["max_multiple"] or 0)
            pending = [threshold for threshold in MILESTONE_THRESHOLDS if max_multiple >= threshold]

        for threshold in pending:
            await self.send_milestone_reply(mint, threshold)

    async def send_root_alert(self, mint: str) -> None:
        now = utc_now_iso()
        with self.connect() as conn:
            row = self.load_token(conn, mint)
            if row is None or row["max_multiple"] is None or float(row["max_multiple"]) < 1.5:
                return
            if self.dry_run:
                logger.info("DRY RUN survivor root eligible mint=%s multiple=%s", mint, row["max_multiple"])
                return
            cur = conn.execute(
                """
                INSERT OR IGNORE INTO telegram_survivor_threads
                (mint, chat_id, root_message_id, first_alert_threshold, first_alert_multiple, first_alerted_at, source)
                VALUES (?, ?, NULL, 1.5, ?, ?, 'vlak')
                """,
                (mint, self.chat_id, row["max_multiple"], now),
            )
            conn.commit()
            if not cur.rowcount:
                return
            text = self.format_root_message(row)
        try:
            message_id = await self.send_message(text)
        except Exception as exc:
            with self.connect() as conn:
                conn.execute("DELETE FROM telegram_survivor_threads WHERE mint = ? AND root_message_id IS NULL", (mint,))
                conn.commit()
            logger.error("Survivor root send failed mint=%s error=%s", mint, exc)
            return
        if message_id is None:
            with self.connect() as conn:
                conn.execute("DELETE FROM telegram_survivor_threads WHERE mint = ? AND root_message_id IS NULL", (mint,))
                conn.commit()
            return
        with self.connect() as conn:
            conn.execute("UPDATE telegram_survivor_threads SET root_message_id = ? WHERE mint = ?", (message_id, mint))
            conn.commit()

    async def send_milestone_reply(self, mint: str, threshold: float) -> None:
        now = utc_now_iso()
        with self.connect() as conn:
            row = self.load_token(conn, mint)
            thread = conn.execute("SELECT * FROM telegram_survivor_threads WHERE mint = ?", (mint,)).fetchone()
            if row is None or thread is None or thread["root_message_id"] is None:
                return
            if row["max_multiple"] is None or float(row["max_multiple"]) < threshold:
                return
            if conn.execute("SELECT 1 FROM telegram_survivor_milestones WHERE mint = ? AND threshold = ?", (mint, threshold)).fetchone():
                return
            if self.dry_run:
                logger.info("DRY RUN survivor milestone eligible mint=%s threshold=%s multiple=%s", mint, threshold, row["max_multiple"])
                return
            cur = conn.execute(
                """
                INSERT OR IGNORE INTO telegram_survivor_milestones
                (mint, threshold, multiple_at_send, telegram_message_id, sent_at, source)
                VALUES (?, ?, ?, NULL, ?, 'vlak')
                """,
                (mint, threshold, row["max_multiple"], now),
            )
            conn.commit()
            if not cur.rowcount:
                return
            text = self.format_milestone_message(row, threshold, thread["first_alerted_at"])
            root_message_id = int(thread["root_message_id"])
        try:
            message_id = await self.send_message(text, reply_to_message_id=root_message_id)
        except Exception as exc:
            with self.connect() as conn:
                conn.execute("DELETE FROM telegram_survivor_milestones WHERE mint = ? AND threshold = ? AND telegram_message_id IS NULL", (mint, threshold))
                conn.commit()
            logger.error("Survivor milestone send failed mint=%s threshold=%s error=%s", mint, threshold, exc)
            return
        if message_id is None:
            with self.connect() as conn:
                conn.execute("DELETE FROM telegram_survivor_milestones WHERE mint = ? AND threshold = ? AND telegram_message_id IS NULL", (mint, threshold))
                conn.commit()
            return
        with self.connect() as conn:
            conn.execute(
                "UPDATE telegram_survivor_milestones SET telegram_message_id = ? WHERE mint = ? AND threshold = ?",
                (message_id, mint, threshold),
            )
            conn.commit()
