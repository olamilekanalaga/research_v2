from __future__ import annotations

import sqlite3
from pathlib import Path

DB_PATH = Path(r"C:\Users\alaga\Desktop\My Script Library\Web 3\UNKOWN\v3\vlak_aladdin_research.sqlite")

SCHEMA_SQL = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS vlak_alert_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    notification_id TEXT,
    mint TEXT NOT NULL,
    symbol TEXT,
    name TEXT,
    alert_time TEXT,
    first_call_market_cap REAL,
    market_cap REAL,
    liquidity REAL,
    volume REAL,
    buys INTEGER,
    holders INTEGER,
    bundle_percent REAL,
    sniper_percent REAL,
    top10_percent REAL,
    source TEXT NOT NULL DEFAULT 'vlak_websocket',
    inserted_at TEXT NOT NULL,
    capture_lag_seconds REAL,
    is_first_alert_per_mint INTEGER NOT NULL DEFAULT 0,
    is_clean_first_snapshot INTEGER NOT NULL DEFAULT 0,
    missing_fields TEXT,
    api_error TEXT,
    duplicate_alert_count INTEGER NOT NULL DEFAULT 0,
    raw_payload_hash TEXT NOT NULL,
    raw_json TEXT NOT NULL,
    UNIQUE(raw_payload_hash)
);

CREATE INDEX IF NOT EXISTS idx_vlak_alert_events_mint_time ON vlak_alert_events(mint, alert_time);
CREATE INDEX IF NOT EXISTS idx_vlak_alert_events_first_clean ON vlak_alert_events(is_first_alert_per_mint, is_clean_first_snapshot);
CREATE INDEX IF NOT EXISTS idx_vlak_alert_events_notification ON vlak_alert_events(notification_id);

CREATE TABLE IF NOT EXISTS vlak_metric_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    notification_id TEXT,
    mint TEXT NOT NULL,
    snapshot_time TEXT NOT NULL,
    snapshot_kind TEXT NOT NULL,
    first_call_market_cap REAL,
    market_cap REAL,
    liquidity REAL,
    price REAL,
    volume REAL,
    buy_volume_sol REAL,
    sell_volume_sol REAL,
    buys INTEGER,
    sells INTEGER,
    holders INTEGER,
    bundle_percent REAL,
    sniper_percent REAL,
    top10_percent REAL,
    liq_to_mc REAL,
    vol_to_mc REAL,
    avg_buy_size_sol REAL,
    max_multiple REAL,
    source TEXT NOT NULL,
    capture_lag_seconds REAL,
    is_clean_snapshot INTEGER NOT NULL DEFAULT 0,
    missing_fields TEXT,
    api_error TEXT,
    raw_payload_hash TEXT NOT NULL,
    raw_json TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_vlak_metric_snapshots_mint_time ON vlak_metric_snapshots(mint, snapshot_time);
CREATE INDEX IF NOT EXISTS idx_vlak_metric_snapshots_kind ON vlak_metric_snapshots(snapshot_kind);

CREATE TABLE IF NOT EXISTS vlak_outcome_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mint TEXT NOT NULL,
    snapshot_time TEXT NOT NULL,
    current_mc REAL,
    first_call_market_cap REAL,
    ath_market_cap REAL,
    max_multiple REAL,
    liquidity REAL,
    price REAL,
    market_cap REAL,
    updated_at TEXT,
    source TEXT NOT NULL DEFAULT 'vlak_outcome_endpoint',
    api_error TEXT,
    missing_fields TEXT,
    raw_payload_hash TEXT NOT NULL,
    raw_json TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_vlak_outcome_snapshots_mint_time ON vlak_outcome_snapshots(mint, snapshot_time);
CREATE INDEX IF NOT EXISTS idx_vlak_outcome_snapshots_multiple ON vlak_outcome_snapshots(max_multiple);

CREATE TABLE IF NOT EXISTS vlak_token_outcomes (
    mint TEXT PRIMARY KEY,
    first_alert_time TEXT,
    first_call_market_cap REAL,
    latest_snapshot_time TEXT,
    current_mc REAL,
    ath_market_cap REAL,
    max_multiple REAL,
    hit_2x INTEGER NOT NULL DEFAULT 0,
    hit_5x INTEGER NOT NULL DEFAULT 0,
    hit_10x INTEGER NOT NULL DEFAULT 0,
    rugged INTEGER,
    completed_24h INTEGER NOT NULL DEFAULT 0,
    updated_at TEXT NOT NULL,
    raw_payload_hash TEXT
);

CREATE TABLE IF NOT EXISTS vlak_ingestion_errors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    occurred_at TEXT NOT NULL,
    source TEXT NOT NULL,
    endpoint TEXT,
    mint TEXT,
    notification_id TEXT,
    error_type TEXT,
    error_message TEXT,
    retry_count INTEGER NOT NULL DEFAULT 0,
    raw_payload_hash TEXT,
    raw_json TEXT
);

CREATE INDEX IF NOT EXISTS idx_vlak_ingestion_errors_time ON vlak_ingestion_errors(occurred_at);
CREATE INDEX IF NOT EXISTS idx_vlak_ingestion_errors_mint ON vlak_ingestion_errors(mint);

CREATE TABLE IF NOT EXISTS vlak_api_payload_audit (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    received_at TEXT NOT NULL,
    source TEXT NOT NULL,
    endpoint TEXT,
    method TEXT,
    mint TEXT,
    notification_id TEXT,
    status_code INTEGER,
    success INTEGER NOT NULL DEFAULT 1,
    api_error TEXT,
    raw_payload_hash TEXT NOT NULL,
    payload_bytes INTEGER,
    top_level_keys TEXT
);

CREATE INDEX IF NOT EXISTS idx_vlak_api_payload_audit_time ON vlak_api_payload_audit(received_at);
CREATE INDEX IF NOT EXISTS idx_vlak_api_payload_audit_hash ON vlak_api_payload_audit(raw_payload_hash);

CREATE TABLE IF NOT EXISTS vlak_tracking_schedule (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mint TEXT NOT NULL,
    first_alert_time TEXT NOT NULL,
    checkpoint_label TEXT NOT NULL,
    checkpoint_minutes REAL NOT NULL,
    due_at TEXT NOT NULL,
    completed_at TEXT,
    attempts INTEGER NOT NULL DEFAULT 0,
    last_error TEXT,
    created_at TEXT NOT NULL,
    UNIQUE(mint, checkpoint_label)
);

CREATE INDEX IF NOT EXISTS idx_vlak_tracking_schedule_due ON vlak_tracking_schedule(completed_at, due_at);
CREATE INDEX IF NOT EXISTS idx_vlak_tracking_schedule_mint ON vlak_tracking_schedule(mint);


CREATE TABLE IF NOT EXISTS telegram_survivor_threads (
    mint TEXT PRIMARY KEY,
    chat_id TEXT,
    root_message_id INTEGER,
    first_alert_threshold REAL NOT NULL DEFAULT 1.5,
    first_alert_multiple REAL,
    first_alerted_at TEXT NOT NULL,
    source TEXT NOT NULL DEFAULT 'vlak'
);

CREATE TABLE IF NOT EXISTS telegram_survivor_milestones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mint TEXT NOT NULL,
    threshold REAL NOT NULL,
    multiple_at_send REAL,
    telegram_message_id INTEGER,
    sent_at TEXT NOT NULL,
    source TEXT NOT NULL DEFAULT 'vlak',
    UNIQUE(mint, threshold)
);

CREATE INDEX IF NOT EXISTS idx_telegram_survivor_milestones_mint ON telegram_survivor_milestones(mint);
CREATE TABLE IF NOT EXISTS vlak_daily_summaries (
    report_date TEXT PRIMARY KEY,
    generated_at TEXT NOT NULL,
    new_alerts_collected INTEGER NOT NULL DEFAULT 0,
    unique_mints_collected INTEGER NOT NULL DEFAULT 0,
    outcome_snapshots_collected INTEGER NOT NULL DEFAULT 0,
    completed_24h_outcomes INTEGER NOT NULL DEFAULT 0,
    rate_2x REAL,
    rate_5x REAL,
    rate_10x REAL,
    missing_field_rates_json TEXT,
    ingestion_errors INTEGER NOT NULL DEFAULT 0,
    db_size_bytes INTEGER NOT NULL DEFAULT 0,
    last_websocket_message_at TEXT,
    last_outcome_refresh_at TEXT,
    report_markdown TEXT
);
"""


def migrate(db_path: Path = DB_PATH) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        conn.executescript(SCHEMA_SQL)
        conn.commit()


if __name__ == "__main__":
    migrate()
    print(f"Vlak long-run schema ready: {DB_PATH}")

