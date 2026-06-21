# Vlak Alert Failure Formation Study

Problem: given a Vlak alert, which feature combinations identify alerts likely to fail before another 2x?

No Aladdin strategy labels, pass/fail rules, or custom thresholds are used.

Outcome: failed if `ath_mc / first_vlak_market_cap < 2`.

Baseline failure: `75.14%` across `732` usable tokens.

Ranking score uses failure lift, sample size, and earliness. It is an avoid-list research ranking, not a live rule.

## Single Failure Conditions Used

| formation_type | conditions | features | tokens | failed | survived | failure_pct | survival_pct | baseline_failure_pct | failure_lift_over_baseline | ci95_low_pct | ci95_high_pct | median_first_vlak_mc | median_age_minutes | earliness_score | avoid_score | avg_post_vlak_multiple | median_post_vlak_multiple |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| single | age_minutes <= 0.2573 | age_minutes | 183 | 151 | 32 | 82.51 | 17.49 | 75.14 | 1.098 | 76.36 | 87.33 | 1.801e+04 | 0.191 | 1.523 | 8.724 | 2.128 | 1.068 |
| single | sniper_hold_percent >= 6.89 | sniper_hold_percent | 68 | 56 | 12 | 82.35 | 17.65 | 75.14 | 1.096 | 71.64 | 89.61 | 1.845e+04 | 0.3447 | 1.043 | 4.842 | 2.023 | 1.233 |
| single | top10_percent >= 27.13 | top10_percent | 183 | 148 | 35 | 80.87 | 19.13 | 75.14 | 1.076 | 74.56 | 85.91 | 1.739e+04 | 0.3423 | 1.075 | 6.037 | 2.557 | 1.145 |
| single | vol_to_mc >= 2.658 | vol_to_mc | 73 | 59 | 14 | 80.82 | 19.18 | 75.14 | 1.076 | 70.34 | 88.22 | 1.579e+04 | 0.6216 | 0.8614 | 3.988 | 1.611 | 1.101 |
| single | total_buy >= 119.5 | total_buy | 72 | 58 | 14 | 80.56 | 19.44 | 75.14 | 1.072 | 69.97 | 88.05 | 2.014e+04 | 0.296 | 1.1 | 5.062 | 1.59 | 1.105 |
| single | bundle_hold_percent >= 41.14 | bundle_hold_percent | 67 | 53 | 14 | 79.1 | 20.9 | 75.14 | 1.053 | 67.93 | 87.12 | 2.141e+04 | 0.2701 | 1.14 | 5.066 | 2.398 | 1.042 |
| single | first_call_market_cap <= 1.402e+04 | first_call_market_cap | 366 | 286 | 80 | 78.14 | 21.86 | 75.14 | 1.04 | 73.63 | 82.07 | 1.603e+04 | 0.4961 | 0.9353 | 5.744 | 2.1 | 1.129 |
| single | vol_1h >= 3.66e+04 | vol_1h | 183 | 143 | 40 | 78.14 | 21.86 | 75.14 | 1.04 | 71.61 | 83.52 | 1.847e+04 | 0.5216 | 0.8454 | 4.585 | 2.564 | 1.214 |
| single | chg_24h <= 5.732 | chg_24h | 183 | 143 | 40 | 78.14 | 21.86 | 75.14 | 1.04 | 71.61 | 83.52 | 1.567e+04 | 0.4392 | 0.9996 | 5.421 | 2.561 | 1.138 |
| single | liq_to_mc >= 0.7982 | liq_to_mc | 73 | 57 | 16 | 78.08 | 21.92 | 75.14 | 1.039 | 67.32 | 86.03 | 1.421e+04 | 0.5639 | 0.9546 | 4.27 | 1.776 | 1.119 |
| single | holders <= 118 | holders | 368 | 286 | 82 | 77.72 | 22.28 | 75.14 | 1.034 | 73.19 | 81.67 | 1.684e+04 | 0.3427 | 1.091 | 6.669 | 2.608 | 1.099 |
| single | chg_1h <= 5.576 | chg_1h | 183 | 142 | 41 | 77.6 | 22.4 | 75.14 | 1.033 | 71.02 | 83.03 | 1.588e+04 | 0.4418 | 0.9898 | 5.331 | 2.55 | 1.208 |
| single | avg_buy_size_sol >= 1.444 | avg_buy_size_sol | 367 | 283 | 84 | 77.11 | 22.89 | 75.14 | 1.026 | 72.55 | 81.12 | 1.852e+04 | 0.3648 | 1.009 | 6.12 | 2.545 | 1.168 |
| single | dev_hold_percent <= 0 | dev_hold_percent | 464 | 357 | 107 | 76.94 | 23.06 | 75.14 | 1.024 | 72.9 | 80.54 | 1.64e+04 | 0.4216 | 0.9946 | 6.255 | 2.098 | 1.136 |
| single | market_cap <= 2.178e+04 | market_cap | 547 | 417 | 130 | 76.23 | 23.77 | 75.14 | 1.015 | 72.49 | 79.61 | 1.615e+04 | 0.437 | 0.986 | 6.309 | 2.042 | 1.156 |
| single | count_buy <= 59 | count_buy | 559 | 423 | 136 | 75.67 | 24.33 | 75.14 | 1.007 | 71.95 | 79.04 | 1.682e+04 | 0.4175 | 0.9864 | 6.286 | 2.337 | 1.175 |
| single | vol_24h <= 2.739e+04 | vol_24h | 366 | 276 | 90 | 75.41 | 24.59 | 75.14 | 1.004 | 70.75 | 79.54 | 1.669e+04 | 0.3505 | 1.082 | 6.415 | 2.324 | 1.13 |
| single | liquidity >= 1.607e+04 | liquidity | 73 | 55 | 18 | 75.34 | 24.66 | 75.14 | 1.003 | 64.36 | 83.8 | 6.961e+04 | 0.4586 | 0.56 | 2.417 | 2.468 | 1.324 |

## Top Failure Formations By Avoid Score

| formation_type | conditions | features | tokens | failed | survived | failure_pct | survival_pct | baseline_failure_pct | failure_lift_over_baseline | ci95_low_pct | ci95_high_pct | median_first_vlak_mc | median_age_minutes | earliness_score | avoid_score | avg_post_vlak_multiple | median_post_vlak_multiple |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2-way | age_minutes <= 0.2573 AND dev_hold_percent <= 0 | age_minutes + dev_hold_percent | 122 | 106 | 16 | 86.89 | 13.11 | 75.14 | 1.156 | 79.75 | 91.76 | 1.703e+04 | 0.1831 | 1.595 | 8.878 | 1.933 | 1.031 |
| 2-way | age_minutes <= 0.2573 AND market_cap <= 2.178e+04 | age_minutes + market_cap | 132 | 110 | 22 | 83.33 | 16.67 | 75.14 | 1.109 | 76.05 | 88.73 | 1.663e+04 | 0.1858 | 1.592 | 8.635 | 2.146 | 1.073 |
| 3-way | age_minutes <= 0.2573 AND dev_hold_percent <= 0 AND market_cap <= 2.178e+04 | age_minutes + dev_hold_percent + market_cap | 99 | 84 | 15 | 84.85 | 15.15 | 75.14 | 1.129 | 76.5 | 90.6 | 1.653e+04 | 0.1827 | 1.613 | 8.39 | 2.068 | 1.068 |
| 3-way | age_minutes <= 0.2573 AND first_call_market_cap <= 1.402e+04 AND market_cap <= 2.178e+04 | age_minutes + first_call_market_cap + market_cap | 78 | 68 | 10 | 87.18 | 12.82 | 75.14 | 1.16 | 77.98 | 92.88 | 1.623e+04 | 0.1833 | 1.619 | 8.208 | 2.317 | 1.035 |
| 2-way | age_minutes <= 0.2573 AND holders <= 118 | age_minutes + holders | 112 | 95 | 17 | 84.82 | 15.18 | 75.14 | 1.129 | 77.03 | 90.3 | 1.723e+04 | 0.1923 | 1.537 | 8.204 | 1.802 | 1.067 |
| 2-way | age_minutes <= 0.2573 AND first_call_market_cap <= 1.402e+04 | age_minutes + first_call_market_cap | 89 | 76 | 13 | 85.39 | 14.61 | 75.14 | 1.137 | 76.6 | 91.26 | 1.654e+04 | 0.1888 | 1.577 | 8.067 | 2.293 | 1.042 |
| 3-way | age_minutes <= 0.2573 AND first_call_market_cap <= 1.402e+04 AND dev_hold_percent <= 0 | age_minutes + first_call_market_cap + dev_hold_percent | 65 | 58 | 7 | 89.23 | 10.77 | 75.14 | 1.188 | 79.4 | 94.68 | 1.639e+04 | 0.183 | 1.616 | 8.039 | 2.125 | 1.031 |
| 3-way | age_minutes <= 0.2573 AND dev_hold_percent <= 0 AND count_buy <= 59 | age_minutes + dev_hold_percent + count_buy | 76 | 65 | 11 | 85.53 | 14.47 | 75.14 | 1.138 | 75.91 | 91.72 | 1.668e+04 | 0.1808 | 1.62 | 8.012 | 1.575 | 1.072 |
| 3-way | age_minutes <= 0.2573 AND avg_buy_size_sol >= 1.444 AND dev_hold_percent <= 0 | age_minutes + avg_buy_size_sol + dev_hold_percent | 64 | 57 | 7 | 89.06 | 10.94 | 75.14 | 1.185 | 79.1 | 94.6 | 1.711e+04 | 0.181 | 1.606 | 7.949 | 1.585 | 1.037 |
| 2-way | age_minutes <= 0.2573 AND count_buy <= 59 | age_minutes + count_buy | 131 | 105 | 26 | 80.15 | 19.85 | 75.14 | 1.067 | 72.51 | 86.08 | 1.769e+04 | 0.1953 | 1.509 | 7.858 | 2.009 | 1.1 |
| 3-way | age_minutes <= 0.2573 AND holders <= 118 AND dev_hold_percent <= 0 | age_minutes + holders + dev_hold_percent | 73 | 64 | 9 | 87.67 | 12.33 | 75.14 | 1.167 | 78.2 | 93.38 | 1.667e+04 | 0.1924 | 1.554 | 7.803 | 1.638 | 1.008 |
| 3-way | age_minutes <= 0.2573 AND holders <= 118 AND market_cap <= 2.178e+04 | age_minutes + holders + market_cap | 88 | 74 | 14 | 84.09 | 15.91 | 75.14 | 1.119 | 75.05 | 90.28 | 1.65e+04 | 0.194 | 1.55 | 7.786 | 1.852 | 1.073 |
| 2-way | age_minutes <= 0.2573 AND vol_24h <= 2.739e+04 | age_minutes + vol_24h | 102 | 85 | 17 | 83.33 | 16.67 | 75.14 | 1.109 | 74.92 | 89.33 | 1.742e+04 | 0.1959 | 1.513 | 7.778 | 1.864 | 1.073 |
| 3-way | age_minutes <= 0.2573 AND holders <= 118 AND count_buy <= 59 | age_minutes + holders + count_buy | 87 | 72 | 15 | 82.76 | 17.24 | 75.14 | 1.101 | 73.48 | 89.26 | 1.713e+04 | 0.1924 | 1.54 | 7.595 | 1.889 | 1.075 |
| 3-way | age_minutes <= 0.2573 AND holders <= 118 AND vol_24h <= 2.739e+04 | age_minutes + holders + vol_24h | 81 | 69 | 12 | 85.19 | 14.81 | 75.14 | 1.134 | 75.87 | 91.32 | 1.716e+04 | 0.1961 | 1.52 | 7.592 | 1.924 | 1.075 |
| 3-way | age_minutes <= 0.2573 AND market_cap <= 2.178e+04 AND count_buy <= 59 | age_minutes + market_cap + count_buy | 95 | 77 | 18 | 81.05 | 18.95 | 75.14 | 1.079 | 72.03 | 87.67 | 1.642e+04 | 0.1961 | 1.542 | 7.591 | 1.925 | 1.1 |
| 2-way | age_minutes <= 0.2573 AND avg_buy_size_sol >= 1.444 | age_minutes + avg_buy_size_sol | 102 | 82 | 20 | 80.39 | 19.61 | 75.14 | 1.07 | 71.65 | 86.93 | 1.872e+04 | 0.1909 | 1.506 | 7.468 | 1.905 | 1.072 |
| 3-way | age_minutes <= 0.2573 AND market_cap <= 2.178e+04 AND vol_24h <= 2.739e+04 | age_minutes + market_cap + vol_24h | 79 | 66 | 13 | 83.54 | 16.46 | 75.14 | 1.112 | 73.85 | 90.12 | 1.675e+04 | 0.1969 | 1.527 | 7.44 | 1.906 | 1.075 |
| 3-way | age_minutes <= 0.2573 AND avg_buy_size_sol >= 1.444 AND market_cap <= 2.178e+04 | age_minutes + avg_buy_size_sol + market_cap | 63 | 52 | 11 | 82.54 | 17.46 | 75.14 | 1.099 | 71.38 | 89.96 | 1.654e+04 | 0.1815 | 1.62 | 7.4 | 1.747 | 1.107 |
| 3-way | age_minutes <= 0.2573 AND dev_hold_percent <= 0 AND vol_24h <= 2.739e+04 | age_minutes + dev_hold_percent + vol_24h | 66 | 57 | 9 | 86.36 | 13.64 | 75.14 | 1.149 | 76.07 | 92.66 | 1.695e+04 | 0.1964 | 1.524 | 7.364 | 1.721 | 1.059 |
| 3-way | age_minutes <= 0.2573 AND chg_1h <= 5.576 AND dev_hold_percent <= 0 | age_minutes + chg_1h + dev_hold_percent | 27 | 25 | 2 | 92.59 | 7.407 | 75.14 | 1.232 | 76.63 | 97.94 | 1.602e+04 | 0.1627 | 1.765 | 7.247 | 1.23 | 1.006 |
| 3-way | age_minutes <= 0.2573 AND first_call_market_cap <= 1.402e+04 AND vol_24h <= 2.739e+04 | age_minutes + first_call_market_cap + vol_24h | 49 | 43 | 6 | 87.76 | 12.24 | 75.14 | 1.168 | 75.76 | 94.27 | 1.654e+04 | 0.1887 | 1.578 | 7.209 | 1.864 | 1.008 |
| 3-way | age_minutes <= 0.2573 AND first_call_market_cap <= 1.402e+04 AND count_buy <= 59 | age_minutes + first_call_market_cap + count_buy | 60 | 51 | 9 | 85 | 15 | 75.14 | 1.131 | 73.89 | 91.9 | 1.628e+04 | 0.1963 | 1.545 | 7.185 | 1.831 | 1.068 |
| 3-way | age_minutes <= 0.2573 AND count_buy <= 59 AND vol_24h <= 2.739e+04 | age_minutes + count_buy + vol_24h | 72 | 59 | 13 | 81.94 | 18.06 | 75.14 | 1.091 | 71.52 | 89.13 | 1.735e+04 | 0.1982 | 1.503 | 7.032 | 1.965 | 1.113 |
| 3-way | age_minutes <= 0.2573 AND first_call_market_cap <= 1.402e+04 AND holders <= 118 | age_minutes + first_call_market_cap + holders | 48 | 41 | 7 | 85.42 | 14.58 | 75.14 | 1.137 | 72.83 | 92.75 | 1.608e+04 | 0.1905 | 1.583 | 7.002 | 1.97 | 1.041 |
| 3-way | age_minutes <= 0.2573 AND first_call_market_cap <= 1.402e+04 AND avg_buy_size_sol >= 1.444 | age_minutes + first_call_market_cap + avg_buy_size_sol | 46 | 41 | 5 | 89.13 | 10.87 | 75.14 | 1.186 | 76.96 | 95.27 | 1.682e+04 | 0.1961 | 1.529 | 6.985 | 1.285 | 1.037 |
| 2-way | age_minutes <= 0.2573 AND top10_percent >= 27.13 | age_minutes + top10_percent | 50 | 44 | 6 | 88 | 12 | 75.14 | 1.171 | 76.19 | 94.38 | 1.84e+04 | 0.1942 | 1.496 | 6.889 | 1.684 | 1.05 |
| 3-way | age_minutes <= 0.2573 AND chg_24h <= 5.732 AND dev_hold_percent <= 0 | age_minutes + chg_24h + dev_hold_percent | 28 | 25 | 3 | 89.29 | 10.71 | 75.14 | 1.188 | 72.8 | 96.29 | 1.57e+04 | 0.1722 | 1.708 | 6.833 | 1.277 | 1.094 |
| 3-way | age_minutes <= 0.2573 AND holders <= 118 AND avg_buy_size_sol >= 1.444 | age_minutes + holders + avg_buy_size_sol | 57 | 47 | 10 | 82.46 | 17.54 | 75.14 | 1.097 | 70.63 | 90.18 | 1.83e+04 | 0.1892 | 1.526 | 6.799 | 1.72 | 1.066 |
| 3-way | age_minutes <= 0.2573 AND avg_buy_size_sol >= 1.444 AND count_buy <= 59 | age_minutes + avg_buy_size_sol + count_buy | 81 | 63 | 18 | 77.78 | 22.22 | 75.14 | 1.035 | 67.58 | 85.46 | 1.842e+04 | 0.1957 | 1.487 | 6.784 | 2.021 | 1.089 |

## Top Failure Formations By Failure Lift

| formation_type | conditions | features | tokens | failed | survived | failure_pct | survival_pct | baseline_failure_pct | failure_lift_over_baseline | ci95_low_pct | ci95_high_pct | median_first_vlak_mc | median_age_minutes | earliness_score | avoid_score | avg_post_vlak_multiple | median_post_vlak_multiple |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 3-way | sniper_hold_percent >= 6.89 AND holders <= 118 AND market_cap <= 2.178e+04 | sniper_hold_percent + holders + market_cap | 27 | 26 | 1 | 96.3 | 3.704 | 75.14 | 1.282 | 81.72 | 99.34 | 1.6e+04 | 0.2815 | 1.244 | 5.314 | 1.639 | 1.126 |
| 3-way | age_minutes <= 0.2573 AND total_buy >= 119.5 AND dev_hold_percent <= 0 | age_minutes + total_buy + dev_hold_percent | 24 | 23 | 1 | 95.83 | 4.167 | 75.14 | 1.275 | 79.76 | 99.26 | 1.92e+04 | 0.1815 | 1.549 | 6.359 | 1.061 | 0.9223 |
| 3-way | age_minutes <= 0.2573 AND vol_1h >= 3.66e+04 AND dev_hold_percent <= 0 | age_minutes + vol_1h + dev_hold_percent | 20 | 19 | 1 | 95 | 5 | 75.14 | 1.264 | 76.39 | 99.11 | 1.931e+04 | 0.1932 | 1.479 | 5.695 | 1.121 | 0.992 |
| 3-way | vol_1h >= 3.66e+04 AND holders <= 118 AND avg_buy_size_sol >= 1.444 | vol_1h + holders + avg_buy_size_sol | 20 | 19 | 1 | 95 | 5 | 75.14 | 1.264 | 76.39 | 99.11 | 1.738e+04 | 0.3616 | 1.045 | 4.021 | 8.045 | 1.038 |
| 3-way | age_minutes <= 0.2573 AND chg_1h <= 5.576 AND dev_hold_percent <= 0 | age_minutes + chg_1h + dev_hold_percent | 27 | 25 | 2 | 92.59 | 7.407 | 75.14 | 1.232 | 76.63 | 97.94 | 1.602e+04 | 0.1627 | 1.765 | 7.247 | 1.23 | 1.006 |
| 2-way | age_minutes <= 0.2573 AND total_buy >= 119.5 | age_minutes + total_buy | 27 | 25 | 2 | 92.59 | 7.407 | 75.14 | 1.232 | 76.63 | 97.94 | 2.006e+04 | 0.1804 | 1.537 | 6.311 | 1.236 | 1 |
| 3-way | top10_percent >= 27.13 AND chg_24h <= 5.732 AND chg_1h <= 5.576 | top10_percent + chg_24h + chg_1h | 26 | 24 | 2 | 92.31 | 7.692 | 75.14 | 1.229 | 75.86 | 97.86 | 1.525e+04 | 0.3255 | 1.174 | 4.755 | 1.382 | 1.073 |
| 3-way | top10_percent >= 27.13 AND vol_1h >= 3.66e+04 AND count_buy <= 59 | top10_percent + vol_1h + count_buy | 26 | 24 | 2 | 92.31 | 7.692 | 75.14 | 1.229 | 75.86 | 97.86 | 2.056e+04 | 0.4084 | 0.9051 | 3.665 | 1.752 | 1.296 |
| 3-way | top10_percent >= 27.13 AND holders <= 118 AND chg_1h <= 5.576 | top10_percent + holders + chg_1h | 22 | 20 | 2 | 90.91 | 9.091 | 75.14 | 1.21 | 72.18 | 97.47 | 1.518e+04 | 0.2801 | 1.277 | 4.843 | 1.438 | 1.073 |
| 3-way | bundle_hold_percent >= 41.14 AND avg_buy_size_sol >= 1.444 AND dev_hold_percent <= 0 | bundle_hold_percent + avg_buy_size_sol + dev_hold_percent | 22 | 20 | 2 | 90.91 | 9.091 | 75.14 | 1.21 | 72.18 | 97.47 | 2.204e+04 | 0.2395 | 1.224 | 4.643 | 3.799 | 0.9661 |
| 3-way | sniper_hold_percent >= 6.89 AND top10_percent >= 27.13 AND market_cap <= 2.178e+04 | sniper_hold_percent + top10_percent + market_cap | 22 | 20 | 2 | 90.91 | 9.091 | 75.14 | 1.21 | 72.18 | 97.47 | 1.616e+04 | 0.29 | 1.218 | 4.622 | 1.872 | 1.107 |
| 3-way | sniper_hold_percent >= 6.89 AND holders <= 118 AND count_buy <= 59 | sniper_hold_percent + holders + count_buy | 32 | 29 | 3 | 90.62 | 9.375 | 75.14 | 1.206 | 75.78 | 96.76 | 1.64e+04 | 0.2936 | 1.202 | 5.07 | 1.726 | 1.117 |
| 3-way | age_minutes <= 0.2573 AND chg_1h <= 5.576 AND vol_24h <= 2.739e+04 | age_minutes + chg_1h + vol_24h | 21 | 19 | 2 | 90.48 | 9.524 | 75.14 | 1.204 | 71.09 | 97.35 | 1.564e+04 | 0.1783 | 1.67 | 6.215 | 1.304 | 1.089 |
| 3-way | top10_percent >= 27.13 AND chg_24h <= 5.732 AND dev_hold_percent <= 0 | top10_percent + chg_24h + dev_hold_percent | 20 | 18 | 2 | 90 | 10 | 75.14 | 1.198 | 69.9 | 97.21 | 1.518e+04 | 0.3352 | 1.159 | 4.227 | 1.654 | 1.031 |
| 3-way | top10_percent >= 27.13 AND chg_1h <= 5.576 AND dev_hold_percent <= 0 | top10_percent + chg_1h + dev_hold_percent | 20 | 18 | 2 | 90 | 10 | 75.14 | 1.198 | 69.9 | 97.21 | 1.525e+04 | 0.3616 | 1.113 | 4.057 | 1.466 | 1.031 |
| 3-way | age_minutes <= 0.2573 AND top10_percent >= 27.13 AND holders <= 118 | age_minutes + top10_percent + holders | 39 | 35 | 4 | 89.74 | 10.26 | 75.14 | 1.194 | 76.42 | 95.94 | 1.743e+04 | 0.1926 | 1.53 | 6.742 | 1.677 | 0.9725 |
| 2-way | top10_percent >= 27.13 AND chg_24h <= 5.732 | top10_percent + chg_24h | 29 | 26 | 3 | 89.66 | 10.34 | 75.14 | 1.193 | 73.61 | 96.42 | 1.52e+04 | 0.3397 | 1.15 | 4.668 | 1.595 | 1.089 |
| 3-way | first_call_market_cap <= 1.402e+04 AND avg_buy_size_sol >= 1.444 AND dev_hold_percent <= 0 | first_call_market_cap + avg_buy_size_sol + dev_hold_percent | 104 | 93 | 11 | 89.42 | 10.58 | 75.14 | 1.19 | 82.05 | 93.99 | 1.597e+04 | 0.419 | 1.012 | 5.604 | 1.366 | 1.072 |
| 3-way | vol_1h >= 3.66e+04 AND avg_buy_size_sol >= 1.444 AND market_cap <= 2.178e+04 | vol_1h + avg_buy_size_sol + market_cap | 47 | 42 | 5 | 89.36 | 10.64 | 75.14 | 1.189 | 77.41 | 95.37 | 1.598e+04 | 0.419 | 1.011 | 4.656 | 1.404 | 1.299 |
| 3-way | age_minutes <= 0.2573 AND chg_24h <= 5.732 AND dev_hold_percent <= 0 | age_minutes + chg_24h + dev_hold_percent | 28 | 25 | 3 | 89.29 | 10.71 | 75.14 | 1.188 | 72.8 | 96.29 | 1.57e+04 | 0.1722 | 1.708 | 6.833 | 1.277 | 1.094 |
| 3-way | vol_1h >= 3.66e+04 AND holders <= 118 AND count_buy <= 59 | vol_1h + holders + count_buy | 28 | 25 | 3 | 89.29 | 10.71 | 75.14 | 1.188 | 72.8 | 96.29 | 1.614e+04 | 0.3459 | 1.107 | 4.43 | 6.18 | 0.9925 |
| 3-way | age_minutes <= 0.2573 AND first_call_market_cap <= 1.402e+04 AND dev_hold_percent <= 0 | age_minutes + first_call_market_cap + dev_hold_percent | 65 | 58 | 7 | 89.23 | 10.77 | 75.14 | 1.188 | 79.4 | 94.68 | 1.639e+04 | 0.183 | 1.616 | 8.039 | 2.125 | 1.031 |
| 3-way | age_minutes <= 0.2573 AND top10_percent >= 27.13 AND count_buy <= 59 | age_minutes + top10_percent + count_buy | 37 | 33 | 4 | 89.19 | 10.81 | 75.14 | 1.187 | 75.29 | 95.71 | 1.743e+04 | 0.2025 | 1.479 | 6.387 | 1.745 | 1.071 |
| 3-way | first_call_market_cap <= 1.402e+04 AND vol_1h >= 3.66e+04 AND avg_buy_size_sol >= 1.444 | first_call_market_cap + vol_1h + avg_buy_size_sol | 37 | 33 | 4 | 89.19 | 10.81 | 75.14 | 1.187 | 75.29 | 95.71 | 1.627e+04 | 0.3434 | 1.107 | 4.782 | 1.512 | 1.335 |
| 3-way | age_minutes <= 0.2573 AND first_call_market_cap <= 1.402e+04 AND avg_buy_size_sol >= 1.444 | age_minutes + first_call_market_cap + avg_buy_size_sol | 46 | 41 | 5 | 89.13 | 10.87 | 75.14 | 1.186 | 76.96 | 95.27 | 1.682e+04 | 0.1961 | 1.529 | 6.985 | 1.285 | 1.037 |
| 3-way | age_minutes <= 0.2573 AND avg_buy_size_sol >= 1.444 AND dev_hold_percent <= 0 | age_minutes + avg_buy_size_sol + dev_hold_percent | 64 | 57 | 7 | 89.06 | 10.94 | 75.14 | 1.185 | 79.1 | 94.6 | 1.711e+04 | 0.181 | 1.606 | 7.949 | 1.585 | 1.037 |
| 3-way | liq_to_mc >= 0.7982 AND chg_1h <= 5.576 AND market_cap <= 2.178e+04 | liq_to_mc + chg_1h + market_cap | 45 | 40 | 5 | 88.89 | 11.11 | 75.14 | 1.183 | 76.5 | 95.16 | 1.456e+04 | 0.3817 | 1.11 | 5.027 | 1.328 | 1.098 |
| 3-way | sniper_hold_percent >= 6.89 AND market_cap <= 2.178e+04 AND count_buy <= 59 | sniper_hold_percent + market_cap + count_buy | 36 | 32 | 4 | 88.89 | 11.11 | 75.14 | 1.183 | 74.68 | 95.59 | 1.603e+04 | 0.4181 | 1.01 | 4.316 | 1.632 | 1.233 |
| 3-way | age_minutes <= 0.2573 AND top10_percent >= 27.13 AND dev_hold_percent <= 0 | age_minutes + top10_percent + dev_hold_percent | 27 | 24 | 3 | 88.89 | 11.11 | 75.14 | 1.183 | 71.94 | 96.15 | 1.743e+04 | 0.1827 | 1.587 | 6.255 | 1.854 | 0.9517 |
| 3-way | top10_percent >= 27.13 AND chg_24h <= 5.732 AND market_cap <= 2.178e+04 | top10_percent + chg_24h + market_cap | 27 | 24 | 3 | 88.89 | 11.11 | 75.14 | 1.183 | 71.94 | 96.15 | 1.519e+04 | 0.3397 | 1.151 | 4.536 | 1.633 | 1.089 |
