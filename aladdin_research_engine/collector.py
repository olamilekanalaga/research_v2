from __future__ import annotations

import asyncio
import logging
import socket

from .config import settings
from .db import (
    connect,
    init_db,
    insert_alert,
    log_telegram_message,
    replace_top_holders,
    upsert_token_quality,
    upsert_alert_filter_metrics,
    upsert_explosive_runner_candidate,
    upsert_alert_trade_window,
    upsert_strategy_evaluation,
)
from .formatting import alert_buy_button, format_alert
from .filters import FILTER_NAME, evaluate_all_strategy_filters, passes_explosive_runner_filter
from .logging_config import configure_logging
from .normalizers import (
    extract_signal_list,
    extract_top_holders,
    normalize_signal,
    normalize_token_quality,
)
from .solana_tracker import SolanaTrackerClient
from .telegram import TelegramClient
from .vlak_client import VlakClient

logger = logging.getLogger(__name__)


async def process_signal(raw: dict, vlak_alert_count: int, allow_telegram: bool = True) -> None:
    alert = normalize_signal(raw)
    notification_id = alert.get("notification_id")
    mint = alert.get("mint")
    with connect() as conn:
        init_db(conn)
        inserted = insert_alert(conn, alert)
        already_sent = conn.execute(
            """
            SELECT 1
            FROM telegram_sent_messages
            WHERE message_type = 'alert' AND notification_id = ?
            LIMIT 1
            """,
            (notification_id,),
        ).fetchone()
        quality = normalize_token_quality(mint, raw)
        if quality:
            upsert_token_quality(conn, quality)
        holders = extract_top_holders(raw)
        if mint and holders:
            replace_top_holders(conn, mint, holders, alert.get("created_on"))
    if already_sent:
        return

    if inserted:
        logger.info("Stored new Vlak alert %s (%s/%s)", notification_id, mint, vlak_alert_count)
    else:
        logger.info("Sending previously stored unsent alert %s (%s/%s)", notification_id, mint, vlak_alert_count)

    # research_v2_historical is the frozen old baseline.
    # research_v2_live is the current live version of that old filter.
    # New named strategy filters are experimental filters.
    research_v2_live_passed, metrics = passes_explosive_runner_filter(raw)
    holders_data = raw.get("holders") if isinstance(raw.get("holders"), dict) else {}
    audit_data = raw.get("audit") if isinstance(raw.get("audit"), dict) else {}
    with connect() as conn:
        upsert_alert_filter_metrics(
            conn,
            {
                "notification_id": notification_id,
                "mint": mint,
                "symbol": alert.get("symbol"),
                "filter_name": "vlak_raw_capture",
                "filter_passed": None,
                "market_cap": metrics.get("market_cap"),
                "liquidity": metrics.get("liquidity"),
                "age_minutes": metrics.get("age_minutes"),
                "volume_usd": metrics.get("volume_usd"),
                "buy_volume_sol": metrics.get("buy_volume_sol"),
                "sell_volume_sol": metrics.get("sell_volume_sol"),
                "buy_sell_volume_ratio": metrics.get("buy_sell_volume_ratio"),
                "buys": metrics.get("buys"),
                "holders": metrics.get("holders"),
                "unique_buyers": metrics.get("unique_buyers"),
                "top_buyer_share": metrics.get("top_buyer_share"),
                "bundle_hold_percent": holders_data.get("bundleHoldPercent"),
                "sniper_hold_percent": holders_data.get("sniperHoldPercent"),
                "dev_hold_percent": holders_data.get("devHoldPercent"),
                "top10_percent": holders_data.get("top10Percent"),
                "phishing_hold_percent": holders_data.get("phishingHoldPercent"),
                "dex_paid": int(bool(audit_data.get("dexPaid"))),
                "lp_burned_percent": audit_data.get("lpBurnedPercent"),
                "liq_to_mc": metrics.get("liq_to_mc"),
                "vol_to_mc": metrics.get("vol_to_mc"),
                "avg_buy_size_sol": metrics.get("avg_buy_size_sol"),
                "top10_holder_pct": metrics.get("top10_holder_pct"),
                "bundle_pct": metrics.get("bundle_pct"),
                "sniper_pct": metrics.get("sniper_pct"),
                "rejection_reason": metrics.get("rejection_reason"),
                "created_at": alert.get("created_on"),
            },
        )
        logger.info(
            "Aladdin pass/reject paused: stored raw Vlak capture metrics for %s; skipping strategy evaluations and Telegram routing",
            notification_id,
        )
        return

    strategy_evaluations = evaluate_all_strategy_filters(raw)
    passed_strategies = [
        evaluation for evaluation in strategy_evaluations if evaluation.get("filter_passed")
    ]
    failed_strategies = [
        evaluation for evaluation in strategy_evaluations if not evaluation.get("filter_passed")
    ]
    with connect() as conn:
        for evaluation in strategy_evaluations:
            upsert_strategy_evaluation(
                conn,
                {
                    "evaluation_id": f"{evaluation['strategy_name']}:{notification_id}",
                    "notification_id": notification_id,
                    "mint": mint,
                    "symbol": alert.get("symbol"),
                    "strategy_name": evaluation.get("strategy_name"),
                    "filter_version": evaluation.get("filter_version"),
                    "filter_passed": evaluation.get("filter_passed"),
                    "rejection_reason": evaluation.get("rejection_reason"),
                    "market_cap": evaluation.get("market_cap"),
                    "liquidity": evaluation.get("liquidity"),
                    "age_minutes": evaluation.get("age_minutes"),
                    "volume_usd": evaluation.get("volume_usd"),
                    "sol_volume": evaluation.get("sol_volume"),
                    "liq_to_mc": evaluation.get("liq_to_mc"),
                    "vol_to_mc": evaluation.get("vol_to_mc"),
                    "buys": evaluation.get("buys"),
                    "holders": evaluation.get("holders"),
                    "top10_holder_pct": evaluation.get("top10_holder_pct"),
                    "bundle_pct": evaluation.get("bundle_pct"),
                    "sniper_pct": evaluation.get("sniper_pct"),
                    "buy_sell_volume_ratio": evaluation.get("buy_sell_volume_ratio"),
                    "evaluated_at": alert.get("created_on"),
                    "raw_metrics_json": evaluation.get("raw_metrics_json"),
                },
            )

    evaluated_strategy_names = ["research_v2_live"] + [
        evaluation["strategy_name"] for evaluation in strategy_evaluations
    ]
    solana_tracker = SolanaTrackerClient(settings)
    try:
        trade_window_rows = await solana_tracker.enrich_trade_windows(
            notification_id=notification_id,
            mint=mint,
            strategy_names=evaluated_strategy_names,
            alert_time=alert.get("created_on") or alert.get("sent_at"),
        )
    finally:
        await solana_tracker.close()
    if trade_window_rows:
        with connect() as conn:
            for row in trade_window_rows:
                upsert_alert_trade_window(conn, row)
        logger.info(
            "Stored %s Solana Tracker trade-window row(s) for %s",
            len(trade_window_rows),
            notification_id,
        )

    logger.info(
        "Strategy evaluation for %s %s: passed=%s failed=%s",
        alert.get("symbol"),
        mint,
        [evaluation["strategy_name"] for evaluation in passed_strategies],
        {
            evaluation["strategy_name"]: evaluation.get("rejection_reason")
            for evaluation in failed_strategies
        },
    )
    confirmed_runner = next(
        (
            evaluation
            for evaluation in strategy_evaluations
            if evaluation["strategy_name"] == "confirmed_runner"
        ),
        None,
    )
    if confirmed_runner:
        if confirmed_runner.get("filter_passed"):
            logger.info("confirmed_runner passed for %s %s", alert.get("symbol"), mint)
        else:
            logger.info(
                "confirmed_runner failed for %s %s: %s",
                alert.get("symbol"),
                mint,
                confirmed_runner.get("rejection_reason"),
            )
    if not passed_strategies:
        logger.info("Alert %s skipped: no new strategies passed", notification_id)
        return

    primary_metrics = passed_strategies[0]
    with connect() as conn:
        upsert_explosive_runner_candidate(
            conn,
            {
                "notification_id": notification_id,
                "mint": mint,
                "symbol": alert.get("symbol"),
                "market_cap": primary_metrics.get("market_cap"),
                "liquidity": primary_metrics.get("liquidity"),
                "age_minutes": primary_metrics.get("age_minutes"),
                "volume_usd": primary_metrics.get("volume_usd"),
                "sol_volume": primary_metrics.get("sol_volume"),
                "buys": primary_metrics.get("buys"),
                "holders": primary_metrics.get("holders"),
                "liq_to_mc": primary_metrics.get("liq_to_mc"),
                "vol_to_mc": primary_metrics.get("vol_to_mc"),
                "avg_buy_size_sol": primary_metrics.get("avg_buy_size_sol"),
                "top10_holder_pct": primary_metrics.get("top10_holder_pct"),
                "bundle_pct": primary_metrics.get("bundle_pct"),
                "sniper_pct": primary_metrics.get("sniper_pct"),
                "created_at": alert.get("created_on"),
            },
        )

    if not allow_telegram:
        logger.info(
            "Alert %s captured for DB/outcome tracking with Telegram disabled for this capture",
            notification_id,
        )
        return

    telegram_strategies = [
        evaluation
        for evaluation in passed_strategies
        if settings.telegram_enabled_for_strategy(evaluation["strategy_name"])
    ]
    if not telegram_strategies:
        logger.info(
            "Alert %s skipped for Telegram: passed strategies are research-only (%s)",
            notification_id,
            [evaluation["strategy_name"] for evaluation in passed_strategies],
        )
        return

    telegram_primary_metrics = telegram_strategies[0]
    passed_labels = [evaluation["telegram_label"] for evaluation in telegram_strategies]
    if settings.dry_run:
        logger.info(
            "DRY_RUN=true: would send alert %s for %s with Telegram-enabled strategies=%s",
            notification_id,
            mint,
            [evaluation["strategy_name"] for evaluation in telegram_strategies],
        )
        return

    telegram = TelegramClient(settings)
    try:
        message_id = await telegram.send_message(
            format_alert(
                alert,
                raw=raw,
                filter_metrics=telegram_primary_metrics,
                passed_strategies=passed_labels,
            ),
            reply_markup=alert_buy_button(mint),
        )
    finally:
        await telegram.close()
    if not message_id:
        logger.error("Telegram send failed for alert %s; leaving it pending for retry", notification_id)
        return
    with connect() as conn:
        log_telegram_message(
            conn,
            message_type="alert",
            telegram_message_id=message_id,
            notification_id=notification_id,
            mint=mint,
        )


async def run_collector() -> None:
    configure_logging()
    lock_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        lock_socket.bind(("127.0.0.1", 49321))
        lock_socket.listen(1)
    except OSError:
        logger.error("Collector is already running; exiting duplicate process")
        lock_socket.close()
        return

    client = VlakClient(settings)
    try:
        initial_payload = await client.fetch_signals()
        initial_signals = extract_signal_list(initial_payload)
        seen_notification_ids = {
            normalize_signal(signal).get("notification_id") for signal in initial_signals
        }
        logger.info(
            "Collector baseline captured %s current Vlak signal(s); storing them for DB/outcome tracking without Telegram",
            len(seen_notification_ids),
        )
        baseline_tasks = [
            process_signal(signal, len(initial_signals), allow_telegram=False)
            for signal in initial_signals
        ]
        if baseline_tasks:
            results = await asyncio.gather(*baseline_tasks, return_exceptions=True)
            for result in results:
                if isinstance(result, Exception):
                    logger.exception("Baseline signal task failed", exc_info=result)
        while True:
            payload = await client.fetch_signals()
            signals = extract_signal_list(payload)
            if signals:
                logger.info("Fetched %s Vlak signal(s)", len(signals))
            new_signals = []
            for signal in signals:
                notification_id = normalize_signal(signal).get("notification_id")
                if notification_id in seen_notification_ids:
                    continue
                seen_notification_ids.add(notification_id)
                new_signals.append(signal)
            if new_signals:
                logger.info("Found %s new Vlak signal(s) after baseline", len(new_signals))
            tasks = [process_signal(signal, len(new_signals)) for signal in new_signals]
            if tasks:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                for result in results:
                    if isinstance(result, Exception):
                        logger.exception("Signal task failed", exc_info=result)
            await asyncio.sleep(settings.signal_poll_seconds)
    finally:
        await client.close()
        lock_socket.close()


if __name__ == "__main__":
    asyncio.run(run_collector())


