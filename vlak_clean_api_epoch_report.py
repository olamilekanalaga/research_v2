from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from aladdin_research_engine.db import connect, init_db
from vlak_alert_survival_report import markdown_table

OUTPUT_DIR = Path('research_outputs') / 'vlak_clean_api_epoch'


def bucket(mc: float | None, notification_type: str | None, factory: str | None) -> str:
    nt = '' if notification_type is None or pd.isna(notification_type) else str(notification_type).lower()
    fac = '' if factory is None or pd.isna(factory) else str(factory).lower()
    if nt == 'newsignalray' or fac == 'pumpamm':
        return 'ray_migrated'
    if mc is None or pd.isna(mc):
        return 'unknown'
    if mc < 10_000:
        return 'below_early_range'
    if mc < 30_000:
        return 'early_low_mc'
    if mc < 80_000:
        return 'early_mid_mc'
    if mc < 250_000:
        return 'runner_confirmation'
    return 'late_runner'


def load_epoch() -> tuple[str, pd.DataFrame]:
    with connect() as conn:
        init_db(conn)
        row = conn.execute(
            "SELECT value FROM research_meta WHERE key='clean_vlak_api_epoch_started_at'"
        ).fetchone()
        if not row:
            raise RuntimeError('Missing clean_vlak_api_epoch_started_at marker')
        started_at = row['value']
        alerts = pd.read_sql_query(
            '''
            SELECT
                a.notification_id,
                a.mint,
                a.symbol,
                a.name,
                a.notification_type,
                a.sent_at,
                a.market_cap,
                a.first_call_market_cap,
                a.liquidity,
                a.vol_1h,
                a.chg_1h,
                a.total_buy,
                a.count_buy,
                a.label,
                a.factory,
                a.pre_factory,
                fm.age_minutes,
                fm.volume_usd,
                fm.buys,
                fm.holders,
                fm.top10_holder_pct,
                fm.bundle_pct,
                fm.sniper_pct,
                o.call_mc,
                o.call_at,
                o.current_mc,
                o.ath_mc,
                o.max_multiple AS outcome_call_multiple,
                o.outcome_bucket,
                o.updated_at AS outcome_updated_at
            FROM alerts a
            LEFT JOIN alert_filter_metrics fm ON fm.notification_id = a.notification_id
            LEFT JOIN outcomes o ON o.mint = a.mint
            WHERE a.mint IS NOT NULL
            ''',
            conn,
        )
    alerts['sent_at_dt'] = pd.to_datetime(alerts['sent_at'], utc=True, errors='coerce')
    started = pd.to_datetime(started_at, utc=True, errors='coerce')
    alerts = alerts[alerts['sent_at_dt'] >= started].copy()
    alerts['entry_mc'] = pd.to_numeric(
        alerts['market_cap'].fillna(alerts['first_call_market_cap']).fillna(alerts['call_mc']),
        errors='coerce',
    )
    alerts['ath_mc'] = pd.to_numeric(alerts['ath_mc'], errors='coerce')
    alerts['multiple_from_first_captured_alert'] = np.where(
        (alerts['entry_mc'] > 0) & alerts['ath_mc'].notna(),
        alerts['ath_mc'] / alerts['entry_mc'],
        np.nan,
    )
    alerts['bucket'] = alerts.apply(
        lambda row: bucket(row['entry_mc'], row['notification_type'], row['factory']), axis=1
    )
    return started_at, alerts


def first_per_mint(alerts: pd.DataFrame) -> pd.DataFrame:
    if alerts.empty:
        return alerts.copy()
    ordered = alerts.sort_values(['mint', 'sent_at_dt', 'notification_id']).copy()
    ordered['rn'] = ordered.groupby('mint').cumcount() + 1
    return ordered[ordered['rn'] == 1].copy()


def summarize(df: pd.DataFrame, label: str) -> pd.DataFrame:
    usable = df[df['multiple_from_first_captured_alert'].notna()].copy()
    if usable.empty:
        return pd.DataFrame([
            {'unit': label, 'tokens_or_rows': len(df), 'usable_outcomes': 0}
        ])
    m = usable['multiple_from_first_captured_alert']
    return pd.DataFrame([
        {
            'unit': label,
            'tokens_or_rows': len(df),
            'usable_outcomes': len(usable),
            'unique_mints': usable['mint'].nunique(),
            'avg_multiple': m.mean(),
            'best_multiple': m.max(),
            'hit_1_5x_pct': (m >= 1.5).mean() * 100,
            'hit_2x_pct': (m >= 2).mean() * 100,
            'hit_3x_pct': (m >= 3).mean() * 100,
            'hit_5x_pct': (m >= 5).mean() * 100,
            'hit_10x_pct': (m >= 10).mean() * 100,
            'median_entry_mc': usable['entry_mc'].median(),
        }
    ])


def summarize_buckets(df: pd.DataFrame, label: str) -> pd.DataFrame:
    usable = df[df['multiple_from_first_captured_alert'].notna()].copy()
    rows = []
    order = {
        'below_early_range': 0,
        'early_low_mc': 1,
        'early_mid_mc': 2,
        'runner_confirmation': 3,
        'late_runner': 4,
        'ray_migrated': 5,
        'unknown': 99,
    }
    for b, g in usable.groupby('bucket'):
        m = g['multiple_from_first_captured_alert']
        rows.append({
            'unit': label,
            'bucket': b,
            'order': order.get(b, 99),
            'rows_or_tokens': len(g),
            'unique_mints': g['mint'].nunique(),
            'avg_multiple': m.mean(),
            'hit_2x_pct': (m >= 2).mean() * 100,
            'hit_5x_pct': (m >= 5).mean() * 100,
            'hit_10x_pct': (m >= 10).mean() * 100,
            'median_entry_mc': g['entry_mc'].median(),
            'median_holders': pd.to_numeric(g['holders'], errors='coerce').median(),
            'newSignal_pct': (g['notification_type'] == 'newSignal').mean() * 100,
            'newSignalRay_pct': (g['notification_type'] == 'newSignalRay').mean() * 100,
        })
    out = pd.DataFrame(rows)
    return out.sort_values(['unit', 'order']).drop(columns=['order']) if not out.empty else out


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    started_at, alerts = load_epoch()
    first = first_per_mint(alerts)
    overall = pd.concat([
        summarize(first, 'first_captured_alert_per_token'),
        summarize(alerts, 'all_captured_alert_snapshots'),
    ], ignore_index=True)
    buckets = pd.concat([
        summarize_buckets(first, 'first_captured_alert_per_token'),
        summarize_buckets(alerts, 'all_captured_alert_snapshots'),
    ], ignore_index=True)

    alerts.to_csv(OUTPUT_DIR / 'clean_epoch_alert_snapshots.csv', index=False)
    first.to_csv(OUTPUT_DIR / 'clean_epoch_first_alerts.csv', index=False)
    overall.to_csv(OUTPUT_DIR / 'clean_epoch_overall.csv', index=False)
    buckets.to_csv(OUTPUT_DIR / 'clean_epoch_buckets.csv', index=False)

    report = OUTPUT_DIR / 'clean_vlak_api_epoch_report.md'
    with report.open('w', encoding='utf-8') as f:
        f.write('# Clean Vlak API Epoch Report\n\n')
        f.write(f'Epoch started at: `{started_at}`\n\n')
        f.write('Uses only Vlak API alerts captured after the epoch marker. No Aladdin pass/reject or strategy filters.\n\n')
        f.write('Primary metric: `ATH / first captured Vlak alert MC` for each mint.\n\n')
        f.write('## Overall\n\n')
        f.write(markdown_table(overall))
        f.write('\n\n## Buckets\n\n')
        f.write(markdown_table(buckets))
        f.write('\n')

    print(f'Wrote {report}')
    print(f'Epoch started at: {started_at}')
    print('\nOVERALL')
    print(overall.to_string(index=False))
    print('\nBUCKETS')
    print(buckets.to_string(index=False))


if __name__ == '__main__':
    main()
