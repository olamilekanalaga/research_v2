# Vlak Alert Formation Study

Problem: given a Vlak alert, which feature combinations improve the chance of another 2x?

No Aladdin strategy labels, pass/fail rules, or custom thresholds are used.

Outcome: `post_vlak_multiple = ath_mc / first_vlak_market_cap`; survived if `>= 2`.

Baseline survival: `24.79%` across `730` usable tokens.

Ranking score uses lift, sample size, and earliness. It is a research ranking, not a buy rule.

## Single Conditions Used

| formation_type | conditions | features | tokens | survived | survival_pct | baseline_survival_pct | lift_over_baseline | ci95_low_pct | ci95_high_pct | median_first_vlak_mc | median_age_minutes | earliness_score | rank_score | avg_post_vlak_multiple | median_post_vlak_multiple |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| single | first_call_market_cap >= 6.821e+04 | first_call_market_cap | 73 | 25 | 34.25 | 24.79 | 1.381 | 24.39 | 45.67 | 3.017e+05 | 0.3904 | 0.5424 | 3.225 | 4.26 | 1.411 |
| single | avg_buy_size_sol >= 2.27 | avg_buy_size_sol | 73 | 25 | 34.25 | 24.79 | 1.381 | 24.39 | 45.67 | 1.911e+05 | 0.3978 | 0.5491 | 3.265 | 4.719 | 1.418 |
| single | chg_24h >= 11.52 | chg_24h | 73 | 24 | 32.88 | 24.79 | 1.326 | 23.19 | 44.27 | 8.396e+04 | 0.4586 | 0.5391 | 3.077 | 2.52 | 1.325 |
| single | holders >= 151.8 | holders | 183 | 59 | 32.24 | 24.79 | 1.3 | 25.89 | 39.32 | 1.818e+04 | 0.5823 | 0.8125 | 5.509 | 2.203 | 1.322 |
| single | chg_1h >= 10.35 | chg_1h | 73 | 23 | 31.51 | 24.79 | 1.271 | 22 | 42.86 | 5.09e+04 | 0.3912 | 0.6802 | 3.72 | 2.505 | 1.322 |
| single | dev_hold_percent >= 3.461 | dev_hold_percent | 68 | 21 | 30.88 | 24.79 | 1.246 | 21.17 | 42.64 | 1.833e+04 | 0.3704 | 1.006 | 5.305 | 3.108 | 1.177 |
| single | liq_to_mc <= 0.6451 | liq_to_mc | 182 | 55 | 30.22 | 24.79 | 1.219 | 24.01 | 37.24 | 4.441e+04 | 0.3457 | 0.7721 | 4.902 | 3.345 | 1.306 |
| single | age_minutes >= 0.9439 | age_minutes | 183 | 52 | 28.42 | 24.79 | 1.146 | 22.38 | 35.34 | 1.599e+04 | 2.213 | 0.6225 | 3.72 | 2.882 | 1.32 |
| single | market_cap >= 2.179e+04 | market_cap | 182 | 51 | 28.02 | 24.79 | 1.13 | 22 | 34.95 | 4.441e+04 | 0.3289 | 0.8018 | 4.721 | 3.295 | 1.211 |
| single | sniper_hold_percent >= 1.729e-07 | sniper_hold_percent | 339 | 93 | 27.43 | 24.79 | 1.106 | 22.96 | 32.42 | 1.87e+04 | 0.3945 | 0.9636 | 6.215 | 2.527 | 1.251 |
| single | top10_percent <= 27.13 | top10_percent | 547 | 147 | 26.87 | 24.79 | 1.084 | 23.33 | 30.74 | 1.685e+04 | 0.4362 | 0.9648 | 6.594 | 2.286 | 1.168 |
| single | bundle_hold_percent <= 11.38 | bundle_hold_percent | 166 | 44 | 26.51 | 24.79 | 1.069 | 20.38 | 33.7 | 1.668e+04 | 0.5388 | 0.8825 | 4.828 | 2.037 | 1.323 |
| single | count_buy <= 22 | count_buy | 189 | 50 | 26.46 | 24.79 | 1.067 | 20.68 | 33.17 | 1.729e+04 | 0.3912 | 1.005 | 5.626 | 2.179 | 1.299 |
| single | vol_to_mc <= 0.9806 | vol_to_mc | 182 | 48 | 26.37 | 24.79 | 1.064 | 20.51 | 33.22 | 2.201e+04 | 0.3146 | 1.025 | 5.677 | 3.029 | 1.212 |
| single | vol_24h >= 5.705e+04 | vol_24h | 73 | 19 | 26.03 | 24.79 | 1.05 | 17.34 | 37.11 | 5.541e+04 | 0.5216 | 0.5383 | 2.432 | 4.055 | 1.367 |

## Top Formations By Rank Score

| formation_type | conditions | features | tokens | survived | survival_pct | baseline_survival_pct | lift_over_baseline | ci95_low_pct | ci95_high_pct | median_first_vlak_mc | median_age_minutes | earliness_score | rank_score | avg_post_vlak_multiple | median_post_vlak_multiple |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2-way | sniper_hold_percent >= 1.729e-07 AND top10_percent <= 27.13 | sniper_hold_percent + top10_percent | 253 | 76 | 30.04 | 24.79 | 1.212 | 24.72 | 35.95 | 1.809e+04 | 0.416 | 0.9526 | 6.39 | 2.481 | 1.253 |
| 3-way | liq_to_mc <= 0.6451 AND bundle_hold_percent <= 11.38 AND count_buy <= 22 | liq_to_mc + bundle_hold_percent + count_buy | 26 | 13 | 50 | 24.79 | 2.017 | 32.06 | 67.94 | 2.892e+04 | 0.3136 | 0.9341 | 6.209 | 3.676 | 1.967 |
| 2-way | top10_percent <= 27.13 AND count_buy <= 22 | top10_percent + count_buy | 136 | 40 | 29.41 | 24.79 | 1.186 | 22.4 | 37.55 | 1.699e+04 | 0.4052 | 0.9961 | 5.813 | 2.203 | 1.288 |
| 3-way | top10_percent <= 27.13 AND bundle_hold_percent <= 11.38 AND count_buy <= 22 | top10_percent + bundle_hold_percent + count_buy | 63 | 24 | 38.1 | 24.79 | 1.536 | 27.12 | 50.44 | 1.678e+04 | 0.5433 | 0.8762 | 5.599 | 2.648 | 1.558 |
| 2-way | bundle_hold_percent <= 11.38 AND count_buy <= 22 | bundle_hold_percent + count_buy | 83 | 28 | 33.73 | 24.79 | 1.361 | 24.48 | 44.42 | 1.719e+04 | 0.4813 | 0.9118 | 5.497 | 2.492 | 1.469 |
| 2-way | holders >= 151.8 AND top10_percent <= 27.13 | holders + top10_percent | 158 | 51 | 32.28 | 24.79 | 1.302 | 25.48 | 39.91 | 1.762e+04 | 0.5815 | 0.8278 | 5.463 | 2.132 | 1.281 |
| 3-way | sniper_hold_percent >= 1.729e-07 AND top10_percent <= 27.13 AND bundle_hold_percent <= 11.38 | sniper_hold_percent + top10_percent + bundle_hold_percent | 51 | 20 | 39.22 | 24.79 | 1.582 | 27.03 | 52.92 | 1.77e+04 | 0.5824 | 0.8252 | 5.157 | 2.361 | 1.427 |
| 3-way | sniper_hold_percent >= 1.729e-07 AND top10_percent <= 27.13 AND count_buy <= 22 | sniper_hold_percent + top10_percent + count_buy | 63 | 20 | 31.75 | 24.79 | 1.28 | 21.59 | 44 | 1.877e+04 | 0.4018 | 0.9527 | 5.073 | 2.287 | 1.208 |
| 3-way | sniper_hold_percent >= 1.729e-07 AND bundle_hold_percent <= 11.38 AND count_buy <= 22 | sniper_hold_percent + bundle_hold_percent + count_buy | 34 | 13 | 38.24 | 24.79 | 1.542 | 23.9 | 54.96 | 1.853e+04 | 0.4388 | 0.9164 | 5.024 | 2.51 | 1.386 |
| 2-way | top10_percent <= 27.13 AND bundle_hold_percent <= 11.38 | top10_percent + bundle_hold_percent | 138 | 39 | 28.26 | 24.79 | 1.14 | 21.42 | 36.28 | 1.642e+04 | 0.5388 | 0.8905 | 5.009 | 2.08 | 1.294 |
| 2-way | top10_percent <= 27.13 AND vol_to_mc <= 0.9806 | top10_percent + vol_to_mc | 120 | 34 | 28.33 | 24.79 | 1.143 | 21.04 | 36.97 | 2.628e+04 | 0.3459 | 0.904 | 4.954 | 3.389 | 1.237 |
| 2-way | sniper_hold_percent >= 1.729e-07 AND count_buy <= 22 | sniper_hold_percent + count_buy | 90 | 25 | 27.78 | 24.79 | 1.12 | 19.58 | 37.8 | 1.905e+04 | 0.379 | 0.9762 | 4.933 | 2.124 | 1.211 |
| 3-way | holders >= 151.8 AND sniper_hold_percent >= 1.729e-07 AND top10_percent <= 27.13 | holders + sniper_hold_percent + top10_percent | 83 | 29 | 34.94 | 24.79 | 1.409 | 25.56 | 45.66 | 1.953e+04 | 0.58 | 0.7816 | 4.88 | 1.831 | 1.322 |
| 2-way | sniper_hold_percent >= 1.729e-07 AND bundle_hold_percent <= 11.38 | sniper_hold_percent + bundle_hold_percent | 66 | 23 | 34.85 | 24.79 | 1.405 | 24.48 | 46.89 | 1.863e+04 | 0.5513 | 0.8205 | 4.849 | 2.232 | 1.386 |
| 2-way | dev_hold_percent >= 3.461 AND liq_to_mc <= 0.6451 | dev_hold_percent + liq_to_mc | 26 | 11 | 42.31 | 24.79 | 1.706 | 25.54 | 61.05 | 2.88e+04 | 0.3574 | 0.8569 | 4.819 | 3.659 | 1.545 |
| 3-way | liq_to_mc <= 0.6451 AND market_cap >= 2.179e+04 AND bundle_hold_percent <= 11.38 | liq_to_mc + market_cap + bundle_hold_percent | 36 | 16 | 44.44 | 24.79 | 1.793 | 29.54 | 60.42 | 6.08e+04 | 0.3345 | 0.7401 | 4.79 | 3.011 | 1.422 |
| 3-way | dev_hold_percent >= 3.461 AND liq_to_mc <= 0.6451 AND sniper_hold_percent >= 1.729e-07 | dev_hold_percent + liq_to_mc + sniper_hold_percent | 23 | 10 | 43.48 | 24.79 | 1.754 | 25.63 | 63.19 | 2.728e+04 | 0.3701 | 0.8541 | 4.76 | 3.922 | 1.555 |
| 2-way | liq_to_mc <= 0.6451 AND count_buy <= 22 | liq_to_mc + count_buy | 58 | 22 | 37.93 | 24.79 | 1.53 | 26.56 | 50.8 | 3.725e+04 | 0.379 | 0.758 | 4.728 | 2.713 | 1.446 |
| 3-way | market_cap >= 2.179e+04 AND bundle_hold_percent <= 11.38 AND count_buy <= 22 | market_cap + bundle_hold_percent + count_buy | 23 | 9 | 39.13 | 24.79 | 1.578 | 22.16 | 59.21 | 3.011e+04 | 0.3045 | 0.9417 | 4.723 | 3.425 | 1.403 |
| 2-way | liq_to_mc <= 0.6451 AND bundle_hold_percent <= 11.38 | liq_to_mc + bundle_hold_percent | 41 | 20 | 48.78 | 24.79 | 1.967 | 34.25 | 63.52 | 4.305e+04 | 0.4586 | 0.6353 | 4.672 | 3.104 | 1.815 |
| 2-way | holders >= 151.8 AND sniper_hold_percent >= 1.729e-07 | holders + sniper_hold_percent | 99 | 35 | 35.35 | 24.79 | 1.426 | 26.64 | 45.16 | 2.381e+04 | 0.5824 | 0.7018 | 4.608 | 2.034 | 1.368 |
| 2-way | market_cap >= 2.179e+04 AND bundle_hold_percent <= 11.38 | market_cap + bundle_hold_percent | 39 | 16 | 41.03 | 24.79 | 1.655 | 27.08 | 56.58 | 5.09e+04 | 0.3447 | 0.7495 | 4.575 | 2.869 | 1.417 |
| 3-way | liq_to_mc <= 0.6451 AND top10_percent <= 27.13 AND bundle_hold_percent <= 11.38 | liq_to_mc + top10_percent + bundle_hold_percent | 31 | 17 | 54.84 | 24.79 | 2.212 | 37.77 | 70.84 | 5.471e+04 | 0.4646 | 0.5875 | 4.504 | 3.46 | 2.12 |
| 2-way | dev_hold_percent >= 3.461 AND sniper_hold_percent >= 1.729e-07 | dev_hold_percent + sniper_hold_percent | 54 | 16 | 29.63 | 24.79 | 1.195 | 19.14 | 42.83 | 1.891e+04 | 0.4144 | 0.9342 | 4.474 | 3.045 | 1.117 |
| 2-way | holders >= 151.8 AND count_buy <= 22 | holders + count_buy | 54 | 18 | 33.33 | 24.79 | 1.344 | 22.24 | 46.64 | 1.909e+04 | 0.528 | 0.8256 | 4.448 | 2.456 | 1.548 |
| 2-way | count_buy <= 22 AND vol_to_mc <= 0.9806 | count_buy + vol_to_mc | 43 | 13 | 30.23 | 24.79 | 1.219 | 18.6 | 45.11 | 2.441e+04 | 0.3287 | 0.9591 | 4.425 | 2.557 | 1.464 |
| 2-way | liq_to_mc <= 0.6451 AND market_cap >= 2.179e+04 | liq_to_mc + market_cap | 169 | 48 | 28.4 | 24.79 | 1.146 | 22.14 | 35.62 | 5.541e+04 | 0.3447 | 0.7359 | 4.329 | 3.415 | 1.214 |
| 3-way | holders >= 151.8 AND bundle_hold_percent <= 11.38 AND count_buy <= 22 | holders + bundle_hold_percent + count_buy | 30 | 13 | 43.33 | 24.79 | 1.748 | 27.38 | 60.8 | 2.007e+04 | 0.6768 | 0.7204 | 4.324 | 3.032 | 1.669 |
| 3-way | market_cap >= 2.179e+04 AND top10_percent <= 27.13 AND bundle_hold_percent <= 11.38 | market_cap + top10_percent + bundle_hold_percent | 28 | 14 | 50 | 24.79 | 2.017 | 32.63 | 67.37 | 6.824e+04 | 0.4016 | 0.6244 | 4.24 | 3.357 | 1.728 |
| 2-way | holders >= 151.8 AND liq_to_mc <= 0.6451 | holders + liq_to_mc | 75 | 30 | 40 | 24.79 | 1.613 | 29.66 | 51.31 | 4.701e+04 | 0.4741 | 0.6043 | 4.222 | 2.454 | 1.538 |

## Top Formations By Survival Lift

| formation_type | conditions | features | tokens | survived | survival_pct | baseline_survival_pct | lift_over_baseline | ci95_low_pct | ci95_high_pct | median_first_vlak_mc | median_age_minutes | earliness_score | rank_score | avg_post_vlak_multiple | median_post_vlak_multiple |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2-way | first_call_market_cap >= 6.821e+04 AND holders >= 151.8 | first_call_market_cap + holders | 25 | 14 | 56 | 24.79 | 2.259 | 37.07 | 73.33 | 1.398e+05 | 0.4586 | 0.4986 | 3.669 | 3.723 | 2.03 |
| 3-way | first_call_market_cap >= 6.821e+04 AND holders >= 151.8 AND liq_to_mc <= 0.6451 | first_call_market_cap + holders + liq_to_mc | 25 | 14 | 56 | 24.79 | 2.259 | 37.07 | 73.33 | 1.398e+05 | 0.4586 | 0.4986 | 3.669 | 3.723 | 2.03 |
| 3-way | liq_to_mc <= 0.6451 AND top10_percent <= 27.13 AND bundle_hold_percent <= 11.38 | liq_to_mc + top10_percent + bundle_hold_percent | 31 | 17 | 54.84 | 24.79 | 2.212 | 37.77 | 70.84 | 5.471e+04 | 0.4646 | 0.5875 | 4.504 | 3.46 | 2.12 |
| 3-way | holders >= 151.8 AND liq_to_mc <= 0.6451 AND bundle_hold_percent <= 11.38 | holders + liq_to_mc + bundle_hold_percent | 31 | 17 | 54.84 | 24.79 | 2.212 | 37.77 | 70.84 | 6.978e+04 | 0.7681 | 0.3832 | 2.938 | 3.157 | 2.12 |
| 3-way | first_call_market_cap >= 6.821e+04 AND holders >= 151.8 AND market_cap >= 2.179e+04 | first_call_market_cap + holders + market_cap | 24 | 13 | 54.17 | 24.79 | 2.185 | 35.07 | 72.11 | 1.654e+05 | 0.4282 | 0.5202 | 3.658 | 3.687 | 2.021 |
| 3-way | first_call_market_cap >= 6.821e+04 AND holders >= 151.8 AND vol_24h >= 5.705e+04 | first_call_market_cap + holders + vol_24h | 23 | 12 | 52.17 | 24.79 | 2.104 | 32.96 | 70.76 | 1.398e+05 | 0.4869 | 0.4732 | 3.164 | 3.865 | 2.03 |
| 3-way | chg_24h >= 11.52 AND holders >= 151.8 AND bundle_hold_percent <= 11.38 | chg_24h + holders + bundle_hold_percent | 25 | 13 | 52 | 24.79 | 2.097 | 33.5 | 69.97 | 9.909e+04 | 0.7682 | 0.3471 | 2.372 | 2.419 | 2.03 |
| 3-way | liq_to_mc <= 0.6451 AND bundle_hold_percent <= 11.38 AND vol_24h >= 5.705e+04 | liq_to_mc + bundle_hold_percent + vol_24h | 25 | 13 | 52 | 24.79 | 2.097 | 33.5 | 69.97 | 9.909e+04 | 4.933 | 0.25 | 1.708 | 3.337 | 2.03 |
| 3-way | market_cap >= 2.179e+04 AND top10_percent <= 27.13 AND bundle_hold_percent <= 11.38 | market_cap + top10_percent + bundle_hold_percent | 28 | 14 | 50 | 24.79 | 2.017 | 32.63 | 67.37 | 6.824e+04 | 0.4016 | 0.6244 | 4.24 | 3.357 | 1.728 |
| 3-way | holders >= 151.8 AND market_cap >= 2.179e+04 AND bundle_hold_percent <= 11.38 | holders + market_cap + bundle_hold_percent | 28 | 14 | 50 | 24.79 | 2.017 | 32.63 | 67.37 | 7.124e+04 | 0.7483 | 0.3876 | 2.632 | 3.152 | 1.729 |
| 3-way | liq_to_mc <= 0.6451 AND bundle_hold_percent <= 11.38 AND count_buy <= 22 | liq_to_mc + bundle_hold_percent + count_buy | 26 | 13 | 50 | 24.79 | 2.017 | 32.06 | 67.94 | 2.892e+04 | 0.3136 | 0.9341 | 6.209 | 3.676 | 1.967 |
| 2-way | first_call_market_cap >= 6.821e+04 AND vol_24h >= 5.705e+04 | first_call_market_cap + vol_24h | 26 | 13 | 50 | 24.79 | 2.017 | 32.06 | 67.94 | 1.654e+05 | 0.4727 | 0.4761 | 3.164 | 8.887 | 1.898 |
| 3-way | first_call_market_cap >= 6.821e+04 AND liq_to_mc <= 0.6451 AND vol_24h >= 5.705e+04 | first_call_market_cap + liq_to_mc + vol_24h | 26 | 13 | 50 | 24.79 | 2.017 | 32.06 | 67.94 | 1.654e+05 | 0.4727 | 0.4761 | 3.164 | 8.887 | 1.898 |
| 3-way | first_call_market_cap >= 6.821e+04 AND chg_24h >= 11.52 AND holders >= 151.8 | first_call_market_cap + chg_24h + holders | 22 | 11 | 50 | 24.79 | 2.017 | 30.72 | 69.28 | 1.654e+05 | 0.4727 | 0.4761 | 3.01 | 2.637 | 1.898 |
| 3-way | chg_24h >= 11.52 AND bundle_hold_percent <= 11.38 AND vol_24h >= 5.705e+04 | chg_24h + bundle_hold_percent + vol_24h | 22 | 11 | 50 | 24.79 | 2.017 | 30.72 | 69.28 | 1.128e+05 | 2.851 | 0.25 | 1.581 | 2.207 | 1.728 |
| 2-way | chg_1h >= 10.35 AND bundle_hold_percent <= 11.38 | chg_1h + bundle_hold_percent | 20 | 10 | 50 | 24.79 | 2.017 | 29.93 | 70.07 | 6.321e+04 | 0.4694 | 0.5622 | 3.452 | 2.237 | 1.753 |
| 3-way | first_call_market_cap >= 6.821e+04 AND avg_buy_size_sol >= 2.27 AND holders >= 151.8 | first_call_market_cap + avg_buy_size_sol + holders | 20 | 10 | 50 | 24.79 | 2.017 | 29.93 | 70.07 | 2.189e+05 | 0.5405 | 0.4102 | 2.519 | 3.86 | 1.888 |
| 3-way | avg_buy_size_sol >= 2.27 AND holders >= 151.8 AND bundle_hold_percent <= 11.38 | avg_buy_size_sol + holders + bundle_hold_percent | 20 | 10 | 50 | 24.79 | 2.017 | 29.93 | 70.07 | 6.969e+04 | 0.7681 | 0.3834 | 2.354 | 3.622 | 1.728 |
| 3-way | chg_24h >= 11.52 AND top10_percent <= 27.13 AND bundle_hold_percent <= 11.38 | chg_24h + top10_percent + bundle_hold_percent | 20 | 10 | 50 | 24.79 | 2.017 | 29.93 | 70.07 | 8.54e+04 | 2.851 | 0.25 | 1.535 | 2.223 | 1.728 |
| 2-way | liq_to_mc <= 0.6451 AND bundle_hold_percent <= 11.38 | liq_to_mc + bundle_hold_percent | 41 | 20 | 48.78 | 24.79 | 1.967 | 34.25 | 63.52 | 4.305e+04 | 0.4586 | 0.6353 | 4.672 | 3.104 | 1.815 |
| 3-way | holders >= 151.8 AND liq_to_mc <= 0.6451 AND count_buy <= 22 | holders + liq_to_mc + count_buy | 27 | 13 | 48.15 | 24.79 | 1.942 | 30.74 | 66.01 | 4.305e+04 | 1.039 | 0.3908 | 2.529 | 3.063 | 1.815 |
| 2-way | chg_24h >= 11.52 AND bundle_hold_percent <= 11.38 | chg_24h + bundle_hold_percent | 27 | 13 | 48.15 | 24.79 | 1.942 | 30.74 | 66.01 | 7.17e+04 | 0.7681 | 0.38 | 2.459 | 2.347 | 1.476 |
| 3-way | first_call_market_cap >= 6.821e+04 AND market_cap >= 2.179e+04 AND vol_24h >= 5.705e+04 | first_call_market_cap + market_cap + vol_24h | 25 | 12 | 48 | 24.79 | 1.936 | 30.03 | 66.5 | 1.911e+05 | 0.4586 | 0.4823 | 3.042 | 9.059 | 1.766 |
| 3-way | market_cap >= 2.179e+04 AND bundle_hold_percent <= 11.38 AND vol_24h >= 5.705e+04 | market_cap + bundle_hold_percent + vol_24h | 25 | 12 | 48 | 24.79 | 1.936 | 30.03 | 66.5 | 9.909e+04 | 0.7681 | 0.3472 | 2.19 | 3.18 | 1.428 |
| 3-way | chg_24h >= 11.52 AND liq_to_mc <= 0.6451 AND bundle_hold_percent <= 11.38 | chg_24h + liq_to_mc + bundle_hold_percent | 26 | 12 | 46.15 | 24.79 | 1.861 | 28.76 | 64.54 | 8.54e+04 | 0.7566 | 0.3649 | 2.239 | 2.203 | 1.451 |
| 3-way | chg_24h >= 11.52 AND market_cap >= 2.179e+04 AND bundle_hold_percent <= 11.38 | chg_24h + market_cap + bundle_hold_percent | 26 | 12 | 46.15 | 24.79 | 1.861 | 28.76 | 64.54 | 8.54e+04 | 0.7566 | 0.3649 | 2.239 | 2.203 | 1.451 |
| 3-way | first_call_market_cap >= 6.821e+04 AND chg_24h >= 11.52 AND top10_percent <= 27.13 | first_call_market_cap + chg_24h + top10_percent | 24 | 11 | 45.83 | 24.79 | 1.849 | 27.89 | 64.93 | 3.117e+05 | 0.4181 | 0.5074 | 3.019 | 2.353 | 1.596 |
| 3-way | first_call_market_cap >= 6.821e+04 AND chg_24h >= 11.52 AND vol_24h >= 5.705e+04 | first_call_market_cap + chg_24h + vol_24h | 22 | 10 | 45.45 | 24.79 | 1.833 | 26.92 | 65.34 | 2.026e+05 | 0.4727 | 0.4666 | 2.682 | 2.581 | 1.652 |
| 3-way | chg_24h >= 11.52 AND sniper_hold_percent >= 1.729e-07 AND bundle_hold_percent <= 11.38 | chg_24h + sniper_hold_percent + bundle_hold_percent | 22 | 10 | 45.45 | 24.79 | 1.833 | 26.92 | 65.34 | 1.128e+05 | 0.5264 | 0.4568 | 2.626 | 2.31 | 1.451 |
| 3-way | holders >= 151.8 AND age_minutes >= 0.9439 AND count_buy <= 22 | holders + age_minutes + count_buy | 22 | 10 | 45.45 | 24.79 | 1.833 | 26.92 | 65.34 | 2.013e+04 | 386.2 | 0.4231 | 2.432 | 2.143 | 1.79 |
