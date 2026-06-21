# Vlak Waiting Study

Problem: for ultra-early Vlak alerts, compare buying immediately vs waiting for later Vlak snapshots.

No Aladdin strategy labels, pass/fail rules, or old thresholds are used.

Ultra-early cohort: first Vlak `age_minutes <= 0.2573`.

Important limitation: wait entries use the first Vlak snapshot at or after the wait target. This is not tick-level chain data.

`missed_*_before_wait` uses milestone events before the wait target when available.

## Wait Summary

| wait_minutes | early_vlak_tokens | trackable_at_wait | not_trackable_at_wait | missed_2x_before_wait | missed_3x_before_wait | missed_5x_before_wait | avoided_immediate_failures_no_snapshot | trackable_pct | median_snapshot_lag_minutes | median_entry_market_cap | median_entry_mc_increase_pct | median_holders | median_buys | median_volume_usd | median_liquidity | median_bundle_pct | median_sniper_pct | median_top10_pct | avg_post_wait_multiple | median_post_wait_multiple | hit_2x_pct | hit_3x_pct | hit_5x_pct | survival_lift_vs_immediate | false_positive_reduction_count | missed_winners_total |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | 186 | 186 | 0 | 0 | 0 | 0 | 0 | 100 | 0 | 1.795e+04 | 0 | 111 | 42.5 | 2.584e+04 | 1.254e+04 | 23.88 | 0 | 24.51 | 2.11 | 1.067 | 17.2 | 10.22 | 4.301 | 1 | 0 | 0 |
| 1 | 186 | 81 | 105 | 0 | 0 | 0 | 97 | 43.55 | 1.664 | 2.241e+04 | 27.93 | 173 | 47 | 4.403e+04 | 1.373e+04 | 18.06 | 0 | 23.11 | 2.363 | 1.023 | 18.52 | 13.58 | 7.407 | 1.076 | 97 | 0 |
| 2 | 186 | 67 | 119 | 0 | 0 | 0 | 107 | 36.02 | 1.686 | 2.144e+04 | 31.67 | 184 | 34 | 4.907e+04 | 1.363e+04 | 16.18 | 0 | 23.14 | 2.187 | 1.039 | 16.42 | 10.45 | 5.97 | 0.9543 | 107 | 0 |
| 3 | 186 | 55 | 131 | 0 | 0 | 0 | 117 | 29.57 | 3.27 | 2.481e+04 | 46.38 | 202 | 24 | 5.523e+04 | 1.422e+04 | 12.96 | 1.575e-06 | 23.57 | 2.309 | 1.024 | 18.18 | 10.91 | 7.273 | 1.057 | 117 | 0 |
| 5 | 186 | 44 | 142 | 1 | 0 | 0 | 126 | 23.66 | 6.129 | 2.644e+04 | 58.66 | 222 | 23 | 7.514e+04 | 1.519e+04 | 12.09 | 0.03433 | 23.54 | 2.374 | 1.047 | 15.91 | 6.818 | 4.545 | 0.9247 | 126 | 1 |
| 10 | 186 | 32 | 154 | 7 | 2 | 0 | 137 | 17.2 | 8.961 | 2.796e+04 | 68.03 | 229.5 | 22 | 8.57e+04 | 1.564e+04 | 11.01 | 0.1107 | 23.37 | 2.779 | 1.089 | 18.75 | 6.25 | 6.25 | 1.09 | 137 | 7 |

## Research Director Read

- If waiting raises hit rates but sharply reduces trackable tokens, it supports a confirmation-wait bucket.
- If missed winners rise faster than hit-rate lift, immediate buying may still be better for some token types.
- If snapshot lag is high, the result is directional only and needs better time-series enrichment.
