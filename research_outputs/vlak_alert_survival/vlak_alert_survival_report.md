# Vlak Alert Survival Report

Problem: among tokens Vlak alerted, identify what separates 2x survivors from non-survivors.

No Aladdin strategy labels, pass/fail rules, or custom thresholds are used.

Outcome: `post_vlak_multiple = ath_mc / first_vlak_market_cap`; survived if `>= 2`.

## Summary

| observed_vlak_tokens | usable_outcome_tokens | missing_outcome_or_mc | survived_2x_after_vlak | failed_after_vlak | baseline_survival_pct | avg_post_vlak_multiple | best_post_vlak_multiple |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 729 | 728 | 1 | 181 | 547 | 24.86 | 2.355 | 140.1 |

## Feature Separation

| feature | survived_mean | failed_mean | mean_diff | abs_standardized_diff |
| --- | --- | --- | --- | --- |
| age_minutes | 32.86 | 14.32 | 18.54 | 0.1576 |
| liq_to_mc | 0.6386 | 0.6611 | -0.02245 | 0.09663 |
| sniper_hold_percent | 1.63 | 2.063 | -0.4328 | 0.09154 |
| sniper_pct | 1.63 | 2.063 | -0.4328 | 0.09154 |
| total_buy | 71.52 | 67.54 | 3.974 | 0.07485 |
| market_cap | 5.736e+04 | 9.153e+04 | -3.417e+04 | 0.066 |
| chg_24h | 9.589 | 10.96 | -1.37 | 0.06269 |
| dev_hold_percent | 1.841 | 1.476 | 0.3651 | 0.05945 |
| buy_volume_sol | 70.47 | 67.45 | 3.016 | 0.05724 |
| volume_usd | 4.112e+04 | 3.796e+04 | 3156 | 0.0485 |
| liquidity | 1.34e+04 | 1.369e+04 | -294.5 | 0.04721 |
| vol_1h | 4.104e+04 | 3.796e+04 | 3074 | 0.04711 |
| buys | 45.09 | 43.98 | 1.116 | 0.03847 |
| bundle_hold_percent | 21.71 | 22.21 | -0.4949 | 0.03475 |
| bundle_pct | 21.71 | 22.21 | -0.4949 | 0.03475 |
| count_buy | 44.33 | 43.5 | 0.8214 | 0.0278 |
| vol_to_mc | 1.525 | 1.549 | -0.02387 | 0.02588 |
| holders | 145.4 | 141.1 | 4.264 | 0.02497 |
| first_call_market_cap | 6.931e+04 | 7.967e+04 | -1.035e+04 | 0.02078 |
| avg_buy_size_sol | 1.61 | 1.602 | 0.008292 | 0.01462 |
| top10_percent | 24.17 | 24.1 | 0.06733 | 0.006391 |
| top10_holder_pct | 24.17 | 24.1 | 0.06733 | 0.006391 |
| vol_24h | 4.973e+04 | 5.066e+04 | -931.2 | 0.004968 |
| chg_1h | 8.918 | 8.935 | -0.01683 | 0.001107 |

## Threshold Candidates

| condition | feature | threshold | direction | tokens | survived | survival_pct | lift_over_baseline | median_first_vlak_mc | median_age_minutes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| first_call_market_cap >= 6.837e+04 | first_call_market_cap | 6.837e+04 | >= | 73 | 25 | 34.25 | 1.377 | 3.017e+05 | 0.3904 |
| avg_buy_size_sol >= 2.27 | avg_buy_size_sol | 2.27 | >= | 73 | 25 | 34.25 | 1.377 | 1.911e+05 | 0.3978 |
| chg_24h >= 11.54 | chg_24h | 11.54 | >= | 73 | 24 | 32.88 | 1.322 | 8.396e+04 | 0.4586 |
| holders >= 151.2 | holders | 151.2 | >= | 182 | 59 | 32.42 | 1.304 | 1.823e+04 | 0.5824 |
| chg_1h >= 10.36 | chg_1h | 10.36 | >= | 73 | 23 | 31.51 | 1.267 | 5.09e+04 | 0.3912 |
| first_call_market_cap >= 1.644e+04 | first_call_market_cap | 1.644e+04 | >= | 182 | 57 | 31.32 | 1.26 | 4.196e+04 | 0.3476 |
| dev_hold_percent >= 3.461 | dev_hold_percent | 3.461 | >= | 68 | 21 | 30.88 | 1.242 | 1.833e+04 | 0.3704 |
| chg_24h >= 8.11 | chg_24h | 8.11 | >= | 182 | 55 | 30.22 | 1.215 | 2.605e+04 | 0.3457 |
| liq_to_mc <= 0.6448 | liq_to_mc | 0.6448 | <= | 182 | 55 | 30.22 | 1.215 | 4.441e+04 | 0.3457 |
| chg_1h >= 7.684 | chg_1h | 7.684 | >= | 182 | 52 | 28.57 | 1.149 | 2.332e+04 | 0.3169 |
| age_minutes >= 0.9479 | age_minutes | 0.9479 | >= | 182 | 52 | 28.57 | 1.149 | 1.601e+04 | 2.224 |
| dev_hold_percent >= 0.06888 | dev_hold_percent | 0.06888 | >= | 165 | 47 | 28.48 | 1.146 | 1.765e+04 | 0.4004 |
| holders >= 188 | holders | 188 | >= | 74 | 21 | 28.38 | 1.141 | 2.582e+04 | 0.6093 |
| market_cap >= 2.179e+04 | market_cap | 2.179e+04 | >= | 182 | 51 | 28.02 | 1.127 | 4.441e+04 | 0.3289 |
| holders >= 118 | holders | 118 | >= | 372 | 104 | 27.96 | 1.124 | 1.715e+04 | 0.5257 |
| avg_buy_size_sol <= 1.296 | avg_buy_size_sol | 1.296 | <= | 183 | 51 | 27.87 | 1.121 | 1.62e+04 | 0.5103 |
| first_call_market_cap >= 1.402e+04 | first_call_market_cap | 1.402e+04 | >= | 364 | 101 | 27.75 | 1.116 | 1.932e+04 | 0.3498 |
| sniper_hold_percent >= 1.729e-07 | sniper_hold_percent | 1.729e-07 | >= | 338 | 93 | 27.51 | 1.107 | 1.871e+04 | 0.3928 |
| sniper_pct >= 1.729e-07 | sniper_pct | 1.729e-07 | >= | 338 | 93 | 27.51 | 1.107 | 1.871e+04 | 0.3928 |
| age_minutes >= 0.2573 | age_minutes | 0.2573 | >= | 546 | 150 | 27.47 | 1.105 | 1.675e+04 | 0.5716 |
| market_cap >= 8.739e+04 | market_cap | 8.739e+04 | >= | 73 | 20 | 27.4 | 1.102 | 3.029e+05 | 0.4011 |
| avg_buy_size_sol >= 1.692 | avg_buy_size_sol | 1.692 | >= | 183 | 50 | 27.32 | 1.099 | 3.716e+04 | 0.3643 |
| avg_buy_size_sol <= 1.444 | avg_buy_size_sol | 1.444 | <= | 368 | 100 | 27.17 | 1.093 | 1.629e+04 | 0.4658 |
| top10_percent <= 27.12 | top10_percent | 27.12 | <= | 545 | 146 | 26.79 | 1.077 | 1.688e+04 | 0.437 |
| top10_holder_pct <= 27.12 | top10_holder_pct | 27.12 | <= | 545 | 146 | 26.79 | 1.077 | 1.688e+04 | 0.437 |
| bundle_hold_percent <= 11.34 | bundle_hold_percent | 11.34 | <= | 165 | 44 | 26.67 | 1.073 | 1.668e+04 | 0.5433 |
| bundle_pct <= 11.34 | bundle_pct | 11.34 | <= | 165 | 44 | 26.67 | 1.073 | 1.668e+04 | 0.5433 |
| chg_24h >= 6.605 | chg_24h | 6.605 | >= | 364 | 97 | 26.65 | 1.072 | 1.928e+04 | 0.3525 |
| top10_percent <= 24.02 | top10_percent | 24.02 | <= | 364 | 97 | 26.65 | 1.072 | 1.7e+04 | 0.4492 |
| top10_holder_pct <= 24.02 | top10_holder_pct | 24.02 | <= | 364 | 97 | 26.65 | 1.072 | 1.7e+04 | 0.4492 |
