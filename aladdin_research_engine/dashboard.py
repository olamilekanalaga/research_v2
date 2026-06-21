from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from aladdin_research_engine.config import settings
from aladdin_research_engine.db import connect, init_db


st.set_page_config(page_title="Aladdin Research Engine", layout="wide")
st.title("Aladdin Research Engine")


@st.cache_data(ttl=10)
def read_sql(sql: str, params: tuple = ()) -> pd.DataFrame:
    try:
        with connect() as conn:
            init_db(conn)
            return pd.read_sql_query(sql, conn, params=params)
    except sqlite3.Error as exc:
        st.error(f"Database error: {exc}")
        return pd.DataFrame()


alerts = read_sql(
    """
    SELECT a.*, o.max_multiple, o.outcome_bucket
    FROM alerts a
    LEFT JOIN outcomes o ON o.mint = a.mint
    ORDER BY datetime(a.created_on) DESC
    LIMIT 100
    """
)
milestones = read_sql(
    """
    SELECT *
    FROM milestone_events
    ORDER BY datetime(hit_at) DESC
    LIMIT 100
    """
)
top = read_sql(
    """
    SELECT o.mint, a.symbol, a.name, o.call_mc, o.ath_mc, o.max_multiple, o.outcome_bucket, o.updated_at
    FROM outcomes o
    LEFT JOIN alerts a ON a.mint = o.mint
    GROUP BY o.mint
    ORDER BY o.max_multiple DESC
    LIMIT 50
    """
)
buckets = read_sql(
    """
    SELECT COALESCE(outcome_bucket, 'unknown') AS outcome_bucket, COUNT(*) AS count
    FROM alerts a
    LEFT JOIN outcomes o ON o.mint = a.mint
    GROUP BY COALESCE(outcome_bucket, 'unknown')
    ORDER BY count DESC
    """
)
milestone_counts = read_sql(
    """
    SELECT milestone, COUNT(*) AS hits
    FROM milestone_events
    GROUP BY milestone
    ORDER BY milestone
    """
)
repeated = read_sql(
    """
    SELECT mint, symbol, name, COUNT(*) AS alert_count, MIN(created_on) AS first_seen, MAX(created_on) AS last_seen
    FROM alerts
    WHERE mint IS NOT NULL
    GROUP BY mint
    HAVING COUNT(*) > 1
    ORDER BY alert_count DESC, datetime(last_seen) DESC
    """
)
quality_by_bucket = read_sql(
    """
    SELECT
        COALESCE(o.outcome_bucket, 'unknown') AS outcome_bucket,
        AVG(q.bundle_hold_percent) AS avg_bundle,
        AVG(q.sniper_hold_percent) AS avg_sniper,
        AVG(q.dev_hold_percent) AS avg_dev,
        AVG(q.top10_percent) AS avg_top10,
        AVG(q.holder_count) AS avg_holders
    FROM outcomes o
    LEFT JOIN token_quality_metrics q ON q.mint = o.mint
    GROUP BY COALESCE(o.outcome_bucket, 'unknown')
    """
)
volume_by_bucket = read_sql(
    """
    SELECT
        COALESCE(o.outcome_bucket, 'unknown') AS outcome_bucket,
        AVG(e.buy_volume_1m_usd) AS avg_buy_volume_1m_usd,
        AVG(e.buy_volume_5m_usd) AS avg_buy_volume_5m_usd,
        AVG(e.buy_volume_10m_usd) AS avg_buy_volume_10m_usd,
        AVG(e.buy_count_1m) AS avg_buy_count_1m,
        AVG(e.buy_count_5m) AS avg_buy_count_5m,
        AVG(e.buy_count_10m) AS avg_buy_count_10m
    FROM outcomes o
    LEFT JOIN alerts a ON a.mint = o.mint
    LEFT JOIN solana_tracker_enrichment e ON e.notification_id = a.notification_id
    GROUP BY COALESCE(o.outcome_bucket, 'unknown')
    """
)
research = read_sql(
    """
    SELECT
        a.notification_id,
        a.mint,
        a.symbol,
        a.name,
        a.market_cap,
        a.liquidity,
        q.holder_count,
        q.bundle_hold_percent,
        q.sniper_hold_percent,
        q.top10_percent,
        q.dex_paid,
        e.buy_volume_1m_usd,
        e.buy_volume_5m_usd,
        e.buy_volume_10m_usd,
        e.buy_count_1m,
        e.buy_count_5m,
        e.buy_count_10m,
        o.max_multiple,
        o.outcome_bucket
    FROM alerts a
    LEFT JOIN token_quality_metrics q ON q.mint = a.mint
    LEFT JOIN solana_tracker_enrichment e ON e.notification_id = a.notification_id
    LEFT JOIN outcomes o ON o.mint = a.mint
    ORDER BY datetime(a.created_on) DESC
    """
)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Alerts", len(alerts))
col2.metric("Milestones", len(milestones))
col3.metric("Tracked Mints", len(top))
col4.metric("Repeated Mints", len(repeated))

tab_alerts, tab_milestones, tab_research, tab_stats = st.tabs(
    ["Latest Alerts", "Milestones", "Filter Research", "Stats"]
)

with tab_alerts:
    st.subheader("Latest alerts")
    st.dataframe(alerts, use_container_width=True, hide_index=True)
    st.subheader("Highest max multiple")
    st.dataframe(top, use_container_width=True, hide_index=True)
    st.subheader("Repeated mints")
    st.dataframe(repeated, use_container_width=True, hide_index=True)

with tab_milestones:
    st.subheader("Latest milestones")
    st.dataframe(milestones, use_container_width=True, hide_index=True)
    st.subheader("Hit counts")
    st.dataframe(milestone_counts, use_container_width=True, hide_index=True)

with tab_research:
    st.subheader("Compare future filters against outcomes")
    bucket_options = ["all"] + sorted(
        [str(value) for value in research.get("outcome_bucket", pd.Series(dtype=str)).dropna().unique()]
    )
    bucket = st.selectbox("Outcome bucket", bucket_options)
    filtered = research if bucket == "all" else research[research["outcome_bucket"] == bucket]
    st.dataframe(filtered, use_container_width=True, hide_index=True)

with tab_stats:
    left, right = st.columns(2)
    with left:
        st.subheader("Alerts by outcome bucket")
        st.dataframe(buckets, use_container_width=True, hide_index=True)
        if not buckets.empty:
            st.bar_chart(buckets.set_index("outcome_bucket"))
    with right:
        st.subheader("Milestone hits")
        st.dataframe(milestone_counts, use_container_width=True, hide_index=True)
        if not milestone_counts.empty:
            st.bar_chart(milestone_counts.set_index("milestone"))
    st.subheader("Average quality by outcome bucket")
    st.dataframe(quality_by_bucket, use_container_width=True, hide_index=True)
    st.subheader("Average volume by outcome bucket")
    st.dataframe(volume_by_bucket, use_container_width=True, hide_index=True)

st.caption(f"Reading SQLite database: {settings.database_path}")
