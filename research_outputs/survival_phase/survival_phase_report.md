# Survival Phase Report

## Dataset Integrity

| alerts_total_rows | alerts_unique_tokens | alert_filter_metric_rows | alert_filter_metric_unique_tokens | outcome_rows | outcome_unique_tokens | milestone_rows | milestone_unique_tokens | tokens_with_multiple_alert_rows | max_alert_rows_for_one_token | unit_of_analysis |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1511 | 659 | 1511 | 659 | 659 | 659 | 1475 | 320 | 436 | 11 | token: one first-observed alert_filter_metrics row per mint, joined to one outcomes row; outcome is 2x after first observation |

Correct unit of analysis: token. Each token uses its first observed `alert_filter_metrics` row as features, joined to one `outcomes` row. Survival is calculated as `ath_mc / first_observed_market_cap >= 2`, so this answers what predicts 2x after your threshold.

## Survival Rate

| observed_tokens | tokens_with_outcomes | tokens_missing_outcomes | total_tokens | survived_2x_plus | failed_before_2x | survival_probability | survival_probability_pct |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 659 | 657 | 2 | 657 | 164 | 493 | 0.2496 | 24.96 |

## Strongest Feature Separation

| feature | survived_mean | failed_mean | mean_diff | abs_standardized_diff |
| --- | --- | --- | --- | --- |
| age_minutes | 36.19 | 15.76 | 20.43 | 0.1652 |
| lp_burned_percent | 96.34 | 93.31 | 3.035 | 0.1283 |
| liq_to_mc | 0.6318 | 0.6572 | -0.02543 | 0.1061 |
| sniper_hold_percent | 1.685 | 2.123 | -0.4379 | 0.09064 |
| sniper_pct | 1.685 | 2.123 | -0.4379 | 0.09064 |
| buy_volume_sol | 71.39 | 67.27 | 4.125 | 0.07745 |
| market_cap | 6.08e+04 | 9.866e+04 | -3.787e+04 | 0.06964 |
| volume_usd | 4.285e+04 | 3.865e+04 | 4202 | 0.06165 |
| buys | 45.24 | 43.66 | 1.575 | 0.05498 |
| dex_paid | 0.122 | 0.1055 | 0.01647 | 0.0527 |
| dev_hold_percent | 1.829 | 1.505 | 0.3233 | 0.05128 |
| top10_holder_pct | 24.27 | 23.78 | 0.4854 | 0.04545 |
| top10_percent | 24.27 | 23.78 | 0.4854 | 0.04545 |
| liquidity | 1.351e+04 | 1.376e+04 | -247.8 | 0.03836 |
| avg_buy_size_sol | 1.63 | 1.61 | 0.01986 | 0.0339 |

## Best Threshold Candidates

| feature | threshold | condition | tokens | survived | survival_rate | survival_rate_pct | lift_over_baseline | pct_point_gain |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| avg_buy_size_sol | 2.313 | avg_buy_size_sol >= 2.313 | 66 | 23 | 0.3485 | 34.85 | 1.396 | 9.887 |
| phishing_hold_percent | 0 | phishing_hold_percent <= 0 | 110 | 38 | 0.3455 | 34.55 | 1.384 | 9.584 |
| dev_hold_percent | 3.461 | dev_hold_percent >= 3.461 | 60 | 20 | 0.3333 | 33.33 | 1.335 | 8.371 |
| phishing_hold_percent | 1.257 | phishing_hold_percent <= 1.257 | 219 | 69 | 0.3151 | 31.51 | 1.262 | 6.545 |
| holders | 151 | holders >= 151 | 168 | 52 | 0.3095 | 30.95 | 1.24 | 5.99 |
| dev_hold_percent | 0.07003 | dev_hold_percent >= 0.07003 | 148 | 44 | 0.2973 | 29.73 | 1.191 | 4.768 |
| holders | 188 | holders >= 188 | 68 | 20 | 0.2941 | 29.41 | 1.178 | 4.45 |
| age_minutes | 0.9869 | age_minutes >= 0.9869 | 165 | 48 | 0.2909 | 29.09 | 1.165 | 4.129 |
| avg_buy_size_sol | 1.692 | avg_buy_size_sol >= 1.692 | 168 | 48 | 0.2857 | 28.57 | 1.145 | 3.609 |
| liq_to_mc | 0.6409 | liq_to_mc <= 0.6409 | 165 | 47 | 0.2848 | 28.48 | 1.141 | 3.523 |
| avg_buy_size_sol | 1.294 | avg_buy_size_sol <= 1.294 | 166 | 47 | 0.2831 | 28.31 | 1.134 | 3.351 |
| market_cap | 2.198e+04 | market_cap >= 2.198e+04 | 165 | 46 | 0.2788 | 27.88 | 1.117 | 2.917 |
| age_minutes | 0.2609 | age_minutes >= 0.2609 | 493 | 137 | 0.2779 | 27.79 | 1.113 | 2.827 |
| sniper_hold_percent | 2.953e-06 | sniper_hold_percent >= 2.953e-06 | 306 | 84 | 0.2745 | 27.45 | 1.1 | 2.489 |
| sniper_pct | 2.953e-06 | sniper_pct >= 2.953e-06 | 306 | 84 | 0.2745 | 27.45 | 1.1 | 2.489 |
| phishing_hold_percent | 3.881 | phishing_hold_percent <= 3.881 | 328 | 90 | 0.2744 | 27.44 | 1.099 | 2.477 |
| holders | 118 | holders >= 118 | 336 | 92 | 0.2738 | 27.38 | 1.097 | 2.419 |
| buys | 59 | buys >= 59 | 165 | 45 | 0.2727 | 27.27 | 1.093 | 2.311 |
| age_minutes | 2.867 | age_minutes >= 2.867 | 66 | 18 | 0.2727 | 27.27 | 1.093 | 2.311 |
| volume_usd | 5.144e+04 | volume_usd >= 5.144e+04 | 66 | 18 | 0.2727 | 27.27 | 1.093 | 2.311 |

## Best Feature Interactions

| condition_1 | condition_2 | tokens | survived | survival_rate | survival_rate_pct |
| --- | --- | --- | --- | --- | --- |
| phishing_hold_percent <= 0 | liq_to_mc <= 0.6409 | 17 | 10 | 0.5882 | 58.82 |
| phishing_hold_percent <= 0 | market_cap >= 2.198e+04 | 17 | 9 | 0.5294 | 52.94 |
| phishing_hold_percent <= 0 | avg_buy_size_sol >= 1.692 | 19 | 9 | 0.4737 | 47.37 |
| phishing_hold_percent <= 0 | holders >= 151 | 34 | 16 | 0.4706 | 47.06 |
| dev_hold_percent >= 3.461 | avg_buy_size_sol >= 1.692 | 15 | 7 | 0.4667 | 46.67 |
| dev_hold_percent >= 3.461 | liq_to_mc <= 0.6409 | 22 | 10 | 0.4545 | 45.45 |
| dev_hold_percent >= 3.461 | market_cap >= 2.198e+04 | 20 | 9 | 0.45 | 45 |
| phishing_hold_percent <= 0 | holders >= 188 | 18 | 8 | 0.4444 | 44.44 |
| phishing_hold_percent <= 1.257 | holders >= 151 | 61 | 27 | 0.4426 | 44.26 |
| avg_buy_size_sol >= 2.313 | holders >= 188 | 25 | 11 | 0.44 | 44 |
| phishing_hold_percent <= 1.257 | dev_hold_percent >= 0.07003 | 39 | 17 | 0.4359 | 43.59 |
| phishing_hold_percent <= 1.257 | age_minutes >= 0.9869 | 51 | 22 | 0.4314 | 43.14 |
| holders >= 151 | avg_buy_size_sol <= 1.294 | 35 | 15 | 0.4286 | 42.86 |
| phishing_hold_percent <= 0 | age_minutes >= 0.9869 | 28 | 12 | 0.4286 | 42.86 |
| avg_buy_size_sol >= 2.313 | holders >= 151 | 33 | 14 | 0.4242 | 42.42 |
| avg_buy_size_sol >= 2.313 | phishing_hold_percent <= 1.257 | 43 | 18 | 0.4186 | 41.86 |
| holders >= 151 | avg_buy_size_sol >= 1.692 | 53 | 22 | 0.4151 | 41.51 |
| holders >= 151 | dev_hold_percent >= 0.07003 | 41 | 17 | 0.4146 | 41.46 |
| phishing_hold_percent <= 1.257 | holders >= 188 | 34 | 14 | 0.4118 | 41.18 |
| avg_buy_size_sol >= 2.313 | age_minutes >= 0.9869 | 17 | 7 | 0.4118 | 41.18 |

## Common Failure Patterns

| failure_pattern | failed_tokens_matching | share_of_failures_pct |
| --- | --- | --- |
| avg_buy_size_sol <= 2.313 | 450 | 91.28 |
| holders <= 151 | 383 | 77.69 |
| avg_buy_size_sol <= 1.692 | 378 | 76.67 |
| age_minutes <= 0.9869 | 377 | 76.47 |
| avg_buy_size_sol >= 1.294 | 376 | 76.27 |
| liq_to_mc >= 0.6409 | 375 | 76.06 |
| dev_hold_percent <= 0.07003 | 338 | 68.56 |
| dev_hold_percent <= 0 | 318 | 64.5 |
| holders <= 118 | 256 | 51.93 |
| avg_buy_size_sol >= 1.444 | 254 | 51.52 |
| buy_volume_sol <= 59 | 252 | 51.12 |
| liquidity <= 1.238e+04 | 251 | 50.91 |
| top10_percent >= 24.02 | 250 | 50.71 |
| top10_holder_pct >= 24.02 | 250 | 50.71 |
| sniper_hold_percent <= 2.953e-06 | 236 | 47.87 |
| sniper_pct <= 2.953e-06 | 236 | 47.87 |
| bundle_hold_percent <= 20.81 | 226 | 45.84 |
| bundle_pct <= 20.81 | 226 | 45.84 |
| sniper_hold_percent <= 0 | 221 | 44.83 |
| sniper_pct <= 0 | 221 | 44.83 |

## Survivor Archetypes

| archetype | surviving_tokens | share_of_survivors_pct |
| --- | --- | --- |
| holder_supported | 52 | 31.71 |
| liquidity_supported | 43 | 26.22 |
| early_low_mc | 40 | 24.39 |
| volume_driven | 38 | 23.17 |
| low_bundle_low_sniper | 32 | 19.51 |
