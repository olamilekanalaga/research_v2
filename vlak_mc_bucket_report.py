from __future__ import annotations

from pathlib import Path

import pandas as pd

from aladdin_research_engine.db import connect, init_db
from vlak_alert_survival_report import markdown_table


OUTPUT_DIR = Path('research_outputs') / 'vlak_alert_survival'


def mc_bucket(mc: float | None, notification_type: str | None = None, factory: str | None = None) -> tuple[str, int]:
    signal_type = '' if notification_type is None or pd.isna(notification_type) else str(notification_type).lower()
    factory_name = '' if factory is None or pd.isna(factory) else str(factory).lower()
    if signal_type == 'newsignalray' or factory_name == 'pumpamm':
        return 'ray_migrated', 5
    if mc is None or pd.isna(mc):
        return 'unknown', 99
    if mc < 10_000:
        return 'below_early_range', 0
    if mc < 30_000:
        return 'early_low_mc', 1
    if mc < 80_000:
        return 'early_mid_mc', 2
    if mc < 250_000:
        return 'runner_confirmation', 3
    return 'late_runner', 4


def load_alerts() -> pd.DataFrame:
    with connect() as conn:
        init_db(conn)
        df = pd.read_sql_query(
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
                o.ath_mc,
                o.max_multiple AS token_level_multiple
            FROM alerts a
            LEFT JOIN alert_filter_metrics fm ON fm.notification_id = a.notification_id
            LEFT JOIN outcomes o ON o.mint = a.mint
            WHERE a.mint IS NOT NULL
            ''',
            conn,
        )
    df['sent_at'] = pd.to_datetime(df['sent_at'], utc=True, errors='coerce')
    df['entry_mc'] = pd.to_numeric(
        df['market_cap'].fillna(df['first_call_market_cap']).fillna(df['call_mc']),
        errors='coerce',
    )
    df['ath_mc'] = pd.to_numeric(df['ath_mc'], errors='coerce')
    df['post_alert_multiple'] = df['ath_mc'] / df['entry_mc']
    buckets = df.apply(lambda row: mc_bucket(row['entry_mc'], row.get('notification_type'), row.get('factory')), axis=1)
    df['mc_bucket'] = buckets.map(lambda x: x[0])
    df['mc_bucket_order'] = buckets.map(lambda x: x[1])
    return df


def first_alert_per_mint(alerts: pd.DataFrame) -> pd.DataFrame:
    ordered = alerts.sort_values(['mint', 'sent_at', 'notification_id']).copy()
    ordered['rn'] = ordered.groupby('mint').cumcount() + 1
    return ordered[ordered['rn'] == 1].copy()


def summarize(df: pd.DataFrame, unit: str) -> pd.DataFrame:
    usable = df[df['post_alert_multiple'].notna()].copy()
    rows = []
    for (order, bucket), group in usable.groupby(['mc_bucket_order', 'mc_bucket'], dropna=False):
        rows.append(
            {
                'unit': unit,
                'mc_bucket': bucket,
                'rows_or_tokens': len(group),
                'unique_mints': group['mint'].nunique(),
                'avg_entry_mc': group['entry_mc'].mean(),
                'median_entry_mc': group['entry_mc'].median(),
                'avg_multiple_from_bucket_alert': group['post_alert_multiple'].mean(),
                'hit_2x_pct': (group['post_alert_multiple'] >= 2).mean() * 100,
                'hit_3x_pct': (group['post_alert_multiple'] >= 3).mean() * 100,
                'hit_5x_pct': (group['post_alert_multiple'] >= 5).mean() * 100,
                'hit_10x_pct': (group['post_alert_multiple'] >= 10).mean() * 100,
                'newSignal_pct': (group['notification_type'] == 'newSignal').mean() * 100,
                'newSignalRay_pct': (group['notification_type'] == 'newSignalRay').mean() * 100,
                'median_age_minutes': pd.to_numeric(group['age_minutes'], errors='coerce').median(),
                'median_holders': pd.to_numeric(group['holders'], errors='coerce').median(),
            }
        )
    out = pd.DataFrame(rows)
    if not out.empty:
        out = out.sort_values(['unit', 'mc_bucket'], key=lambda s: s)
        out['bucket_order'] = out['mc_bucket'].map({'below_early_range': 0, 'early_low_mc': 1, 'early_mid_mc': 2, 'runner_confirmation': 3, 'late_runner': 4, 'ray_migrated': 5, 'unknown': 99})
        out = out.sort_values(['unit', 'bucket_order']).drop(columns=['bucket_order'])
    return out


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    alerts = load_alerts()
    first = first_alert_per_mint(alerts)
    alert_summary = summarize(alerts, 'all_alert_snapshots')
    token_summary = summarize(first, 'first_alert_per_token')
    combined = pd.concat([token_summary, alert_summary], ignore_index=True)

    alerts.to_csv(OUTPUT_DIR / 'vlak_mc_bucket_alert_snapshots.csv', index=False)
    first.to_csv(OUTPUT_DIR / 'vlak_mc_bucket_first_alerts.csv', index=False)
    combined.to_csv(OUTPUT_DIR / 'vlak_mc_bucket_summary.csv', index=False)

    report = OUTPUT_DIR / 'vlak_mc_bucket_report.md'
    with report.open('w', encoding='utf-8') as f:
        f.write('# Vlak MC Bucket Report\n\n')
        f.write('Purpose: store all Vlak API signals, but classify research by market-cap bucket.\n\n')
        f.write('Buckets: `<5k`, `5k-15k`, `15k-30k`, `30k-50k`, `50k+`.\n\n')
        f.write('`first_alert_per_token` is for entry-quality research. `all_alert_snapshots` is for journey/progression research.\n\n')
        f.write('## First Alert Per Token\n\n')
        f.write(markdown_table(token_summary))
        f.write('\n\n## All Alert Snapshots\n\n')
        f.write(markdown_table(alert_summary))
        f.write('\n')

    print(f'Wrote {report}')
    print('\nFIRST ALERT PER TOKEN')
    print(token_summary.to_string(index=False))
    print('\nALL ALERT SNAPSHOTS')
    print(alert_summary.to_string(index=False))


if __name__ == '__main__':
    main()



