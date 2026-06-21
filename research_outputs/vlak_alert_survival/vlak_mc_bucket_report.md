# Vlak MC Bucket Report

Purpose: store all Vlak API signals, but classify research by market-cap bucket.

Buckets: `<5k`, `5k-15k`, `15k-30k`, `30k-50k`, `50k+`.

`first_alert_per_token` is for entry-quality research. `all_alert_snapshots` is for journey/progression research.

## First Alert Per Token

| unit | mc_bucket | rows_or_tokens | unique_mints | avg_entry_mc | median_entry_mc | avg_multiple_from_bucket_alert | hit_2x_pct | hit_3x_pct | hit_5x_pct | hit_10x_pct | newSignal_pct | newSignalRay_pct | median_age_minutes | median_holders |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| first_alert_per_token | early_low_mc | 641 | 641 | 1.718e+04 | 1.627e+04 | 2.157 | 23.4 | 13.57 | 6.552 | 1.716 | 100 | 0 | 0.4149 | 118 |
| first_alert_per_token | early_mid_mc | 4 | 4 | 3.899e+04 | 3.932e+04 | 1.119 | 0 | 0 | 0 | 0 | 100 | 0 | 0.6621 | 124.5 |
| first_alert_per_token | ray_migrated | 137 | 137 | 3.693e+05 | 1.189e+05 | 3.531 | 30.66 | 17.52 | 8.759 | 5.109 | 29.93 | 70.07 | 0.3904 | 133 |

## All Alert Snapshots

| unit | mc_bucket | rows_or_tokens | unique_mints | avg_entry_mc | median_entry_mc | avg_multiple_from_bucket_alert | hit_2x_pct | hit_3x_pct | hit_5x_pct | hit_10x_pct | newSignal_pct | newSignalRay_pct | median_age_minutes | median_holders |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| all_alert_snapshots | below_early_range | 1 | 1 | 4696 | 4696 | 3.521 | 100 | 100 | 0 | 0 | 100 | 0 | 0.1788 | 73 |
| all_alert_snapshots | early_low_mc | 1362 | 641 | 1.922e+04 | 1.828e+04 | 2.091 | 22.1 | 12.92 | 5.653 | 1.762 | 100 | 0 | 0.3297 | 138 |
| all_alert_snapshots | early_mid_mc | 24 | 12 | 4.208e+04 | 4.256e+04 | 1.139 | 12.5 | 8.333 | 0 | 0 | 100 | 0 | 0.3152 | 132 |
| all_alert_snapshots | ray_migrated | 407 | 263 | 3.007e+05 | 7.533e+04 | 2.626 | 28.99 | 15.72 | 8.108 | 3.931 | 29.73 | 70.27 | 0.3264 | 250 |
