from __future__ import annotations

import asyncio
import logging

from .config import settings
from .db import (
    claim_milestone_send,
    connect,
    due_mints_for_outcome_tracking,
    init_db,
    insert_milestone_event,
    log_telegram_message,
    mark_milestone_sent,
    reset_stale_milestone_claims,
    upsert_outcome,
)
from .formatting import format_milestone
from .logging_config import configure_logging
from .normalizers import hit_milestones, next_milestone, normalize_outcome, outcome_bucket
from .telegram import TelegramClient
from .utils import utc_now_iso
from .vlak_client import VlakClient

logger = logging.getLogger(__name__)


MIN_MILESTONE_LIQUIDITY_USD = 5_000


def _number_or_none(value) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(str(value).replace(",", "").replace("$", ""))
    except (TypeError, ValueError):
        return None


def _outcome_liquidity_usd(raw: dict) -> float | None:
    pool = raw.get("pool") if isinstance(raw.get("pool"), dict) else {}
    return _number_or_none(
        pool.get("liquidUsd")
        or pool.get("liquidity")
        or pool.get("liquidityUsd")
        or raw.get("liquidity")
        or raw.get("liquidityUsd")
    )


def _milestone_sendable(raw: dict, outcome: dict) -> tuple[bool, str | None]:
    if outcome.get("rugged"):
        return False, "rugged"
    liquidity_usd = _outcome_liquidity_usd(raw)
    if liquidity_usd is not None and liquidity_usd < MIN_MILESTONE_LIQUIDITY_USD:
        return False, f"low_liquidity_{liquidity_usd:.0f}"
    return True, None


def _ath_milestone_value(max_multiple: float | None) -> float | None:
    if max_multiple is None:
        return None
    return round(max_multiple, 1)


async def process_mint(mint: str, client: VlakClient) -> None:
    raw = await client.fetch_outcome(mint)
    if raw is None:
        with connect() as conn:
            init_db(conn)
            existing = conn.execute(
                """
                SELECT call_mc, call_at, current_mc, ath_mc, ath_at, max_multiple,
                       outcome_bucket, rugged, next_milestone, updated_at, raw_json
                FROM outcomes
                WHERE mint = ?
                """,
                (mint,),
            ).fetchone()
        if not existing:
            return
        raw = {}
        outcome = {"mint": mint, **dict(existing)}
    else:
        outcome = normalize_outcome(mint, raw)
    with connect() as conn:
        init_db(conn)
        reset_stale_milestone_claims(conn)
        if raw:
            previous_outcome = conn.execute(
                """
                SELECT ath_mc, ath_at, max_multiple
                FROM outcomes
                WHERE mint = ?
                """,
                (mint,),
            ).fetchone()
            if previous_outcome:
                previous_ath = previous_outcome["ath_mc"]
                previous_multiple = previous_outcome["max_multiple"]
                if previous_ath is not None and (
                    outcome.get("ath_mc") is None or previous_ath > outcome["ath_mc"]
                ):
                    outcome["ath_mc"] = previous_ath
                    outcome["ath_at"] = previous_outcome["ath_at"]
                if previous_multiple is not None and (
                    outcome.get("max_multiple") is None
                    or previous_multiple > outcome["max_multiple"]
                ):
                    outcome["max_multiple"] = previous_multiple
                    outcome["outcome_bucket"] = outcome_bucket(previous_multiple)
                    outcome["next_milestone"] = next_milestone(previous_multiple)
            upsert_outcome(conn, outcome)
        symbol_row = conn.execute(
            "SELECT symbol FROM alerts WHERE mint = ? ORDER BY created_on ASC LIMIT 1", (mint,)
        ).fetchone()
        symbol = symbol_row["symbol"] if symbol_row else None
        alert_message_row = conn.execute(
            """
            SELECT telegram_message_id
            FROM telegram_sent_messages
            WHERE message_type = 'alert'
              AND mint = ?
              AND telegram_message_id IS NOT NULL
            ORDER BY id ASC
            LIMIT 1
            """,
            (mint,),
        ).fetchone()
        reply_to_message_id = (
            alert_message_row["telegram_message_id"] if alert_message_row else None
        )

    hit = hit_milestones(outcome.get("max_multiple"))
    if not hit:
        return

    highest_hit = max(hit)
    with connect() as conn:
        sent_row = conn.execute(
            """
            SELECT MAX(milestone) AS highest_sent
            FROM milestone_events
            WHERE mint = ?
              AND telegram_sent = 1
              AND telegram_message_id IS NOT NULL
            """,
            (mint,),
        ).fetchone()
        highest_sent = sent_row["highest_sent"] if sent_row else None

    max_multiple = outcome.get("max_multiple")
    ath_milestone = _ath_milestone_value(max_multiple)
    milestone_to_send = max(
        value for value in (highest_hit, ath_milestone) if value is not None
    )
    if highest_sent is not None:
        if highest_hit <= highest_sent:
            if ath_milestone is None or ath_milestone <= highest_sent:
                return
            milestone_to_send = ath_milestone
        elif ath_milestone is not None and ath_milestone > highest_sent:
            milestone_to_send = ath_milestone

    for milestone in [value for value in hit if value < milestone_to_send]:
        row = {
            "mint": mint,
            "milestone": milestone,
            "multiple": outcome.get("max_multiple"),
            "mc": outcome.get("ath_mc") or outcome.get("current_mc"),
            "hit_at": outcome.get("ath_at") or utc_now_iso(),
            "telegram_sent": False,
            "telegram_message_id": None,
        }
        with connect() as conn:
            insert_milestone_event(conn, row)

    for milestone in [milestone_to_send]:
        row = {
            "mint": mint,
            "milestone": milestone,
            "multiple": outcome.get("max_multiple"),
            "mc": outcome.get("ath_mc") or outcome.get("current_mc"),
            "hit_at": outcome.get("ath_at") or utc_now_iso(),
            "telegram_sent": False,
            "telegram_message_id": None,
        }
        with connect() as conn:
            insert_milestone_event(conn, row)
            claimed = claim_milestone_send(conn, mint, milestone)
            already_sent = conn.execute(
                """
                SELECT 1
                FROM milestone_events
                WHERE mint = ?
                  AND milestone = ?
                  AND telegram_sent = 1
                  AND telegram_message_id IS NOT NULL
                LIMIT 1
                """,
                (mint, milestone),
            ).fetchone()
        if already_sent or not claimed:
            continue
        if not reply_to_message_id:
            logger.info(
                "Milestone %.1fx for %s has no sent alert message to reply to; skipping Telegram",
                milestone,
                mint,
            )
            continue
        if settings.dry_run:
            logger.info(
                "DRY_RUN=true: would send milestone %.1fx for %s as reply to %s",
                milestone,
                mint,
                reply_to_message_id,
            )
            with connect() as conn:
                mark_milestone_sent(conn, mint, milestone, None)
            continue

        telegram = TelegramClient(settings)
        try:
            milestone_text = format_milestone(
                symbol=symbol,
                milestone=milestone,
                call_mc=outcome.get("call_mc"),
                ath_mc=outcome.get("ath_mc"),
                max_multiple=outcome.get("max_multiple"),
                call_at=outcome.get("call_at"),
            )
            message_id = await telegram.send_message(
                milestone_text,
                reply_to_message_id=reply_to_message_id,
            )
            if not message_id and reply_to_message_id:
                logger.info(
                    "Milestone %.1fx for %s reply failed; sending standalone fallback",
                    milestone,
                    mint,
                )
                message_id = await telegram.send_message(milestone_text)
        finally:
            await telegram.close()
        with connect() as conn:
            mark_milestone_sent(conn, mint, milestone, message_id)
            log_telegram_message(
                conn,
                message_type="milestone",
                telegram_message_id=message_id,
                mint=mint,
                milestone=milestone,
            )


async def run_outcome_tracker() -> None:
    configure_logging()
    client = VlakClient(settings)
    try:
        while True:
            with connect() as conn:
                init_db(conn)
                reset_stale_milestone_claims(conn)
                mints = due_mints_for_outcome_tracking(conn, settings.outcome_track_hours)
            if mints:
                logger.info("Tracking outcomes for %s mint(s)", len(mints))
            results = await asyncio.gather(
                *(process_mint(mint, client) for mint in mints), return_exceptions=True
            )
            for result in results:
                if isinstance(result, Exception):
                    logger.exception("Outcome task failed", exc_info=result)
            await asyncio.sleep(settings.outcome_poll_seconds)
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(run_outcome_tracker())
