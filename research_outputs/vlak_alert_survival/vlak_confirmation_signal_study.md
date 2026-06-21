# Vlak Confirmation Signal Study

Problem: after an ultra-early Vlak alert, what proof signal appears before buying?

No Aladdin strategy labels, pass/fail rules, or old thresholds are used.

Ultra-early cohort: first Vlak `age_minutes <= 0.2573`.

Confirmation entry: latest Vlak snapshot within the window. Outcome is measured from that confirmation market cap.

## Window Summary

| window_minutes | ultra_early_tokens | tokens_with_confirmation_snapshot | confirmation_trackable_pct | median_confirmation_delay_minutes | median_entry_market_cap | median_mc_delta_pct | median_holders_delta | median_buys_delta | median_volume_delta_pct | hit_2x_from_confirmation_pct | hit_3x_from_confirmation_pct | hit_5x_from_confirmation_pct | avg_post_confirmation_multiple | median_post_confirmation_multiple |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 186 | 71 | 38.17 | 0.3574 | 2.03e+04 | 10.8 | 30 | 18 | 33.35 | 11.27 | 2.817 | 2.817 | 1.619 | 1.027 |
| 3 | 186 | 96 | 51.61 | 0.888 | 2.124e+04 | 21.2 | 37.5 | 17.5 | 47.96 | 10.42 | 7.292 | 5.208 | 1.921 | 1.002 |
| 5 | 186 | 107 | 57.53 | 1.348 | 2.158e+04 | 24.88 | 44 | 18 | 53.85 | 11.21 | 8.411 | 4.673 | 1.804 | 0.9916 |
| 10 | 186 | 113 | 60.75 | 1.659 | 2.241e+04 | 28.47 | 49 | 16 | 62.8 | 8.85 | 5.31 | 3.54 | 1.637 | 0.9465 |

## Top Confirmation Threshold Candidates

| window_minutes | condition | feature | threshold | direction | tokens | hit_2x_pct | hit_3x_pct | hit_5x_pct | baseline_2x_pct | lift_over_window_baseline | median_confirmation_delay_minutes | median_entry_market_cap | median_mc_delta_pct |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | mc_delta_pct <= -0.8475 | mc_delta_pct | -0.8475 | <= | 18 | 33.33 | 11.11 | 11.11 | 11.27 | 2.958 | 0.1887 | 1.838e+04 | -11.07 |
| 1 | liq_to_mc_delta >= -0.004763 | liq_to_mc_delta | -0.004763 | >= | 18 | 33.33 | 11.11 | 11.11 | 11.27 | 2.958 | 0.1923 | 1.755e+04 | -7.917 |
| 1 | liquidity_delta_pct <= -1.574 | liquidity_delta_pct | -1.574 | <= | 18 | 27.78 | 11.11 | 11.11 | 11.27 | 2.465 | 0.1923 | 1.849e+04 | -11.07 |
| 1 | bundle_delta <= -3.839 | bundle_delta | -3.839 | <= | 18 | 27.78 | 5.556 | 5.556 | 11.27 | 2.465 | 0.3298 | 1.943e+04 | 8.858 |
| 3 | buys <= 43.75 | buys | 43.75 | <= | 24 | 25 | 16.67 | 8.333 | 10.42 | 2.4 | 1.558 | 2.053e+04 | 18.23 |
| 3 | count_buy <= 43.75 | count_buy | 43.75 | <= | 24 | 25 | 16.67 | 8.333 | 10.42 | 2.4 | 1.558 | 2.053e+04 | 18.23 |
| 5 | sniper_pct >= 1.224 | sniper_pct | 1.224 | >= | 25 | 24 | 20 | 12 | 11.21 | 2.14 | 1.084 | 2.317e+04 | 33.01 |
| 10 | bundle_delta <= -7.199 | bundle_delta | -7.199 | <= | 27 | 18.52 | 11.11 | 7.407 | 8.85 | 2.093 | 3.154 | 2.33e+04 | 39.87 |
| 10 | vol_to_mc_delta >= 0.7101 | vol_to_mc_delta | 0.7101 | >= | 28 | 17.86 | 7.143 | 3.571 | 8.85 | 2.018 | 3.66 | 2.222e+04 | 33.18 |
| 3 | top10_delta >= 0.1168 | top10_delta | 0.1168 | >= | 24 | 20.83 | 16.67 | 16.67 | 10.42 | 2 | 1.334 | 2.277e+04 | 26.41 |
| 3 | avg_buy_size_delta_pct >= 12.58 | avg_buy_size_delta_pct | 12.58 | >= | 24 | 20.83 | 16.67 | 8.333 | 10.42 | 2 | 1.735 | 2.288e+04 | 28.38 |
| 5 | vol_to_mc_delta >= 0.6347 | vol_to_mc_delta | 0.6347 | >= | 27 | 22.22 | 18.52 | 7.407 | 11.21 | 1.981 | 2.237 | 1.914e+04 | 21.05 |
| 1 | buys <= 45.5 | buys | 45.5 | <= | 18 | 22.22 | 5.556 | 5.556 | 11.27 | 1.972 | 0.3355 | 1.949e+04 | 11.58 |
| 1 | count_buy <= 45.5 | count_buy | 45.5 | <= | 18 | 22.22 | 5.556 | 5.556 | 11.27 | 1.972 | 0.3355 | 1.949e+04 | 11.58 |
| 1 | vol_to_mc >= 1.862 | vol_to_mc | 1.862 | >= | 18 | 22.22 | 0 | 0 | 11.27 | 1.972 | 0.2821 | 1.856e+04 | 3.42 |
| 1 | holders_delta <= 15 | holders_delta | 15 | <= | 18 | 22.22 | 11.11 | 11.11 | 11.27 | 1.972 | 0.2862 | 1.937e+04 | 0.349 |
| 1 | holders_delta_pct <= 16.31 | holders_delta_pct | 16.31 | <= | 18 | 22.22 | 11.11 | 11.11 | 11.27 | 1.972 | 0.3047 | 1.936e+04 | 0.349 |
| 10 | top10_delta >= 0.1442 | top10_delta | 0.1442 | >= | 29 | 17.24 | 13.79 | 10.34 | 8.85 | 1.948 | 2.184 | 2.294e+04 | 35.61 |
| 1 | mc_delta_pct <= 10.8 | mc_delta_pct | 10.8 | <= | 36 | 19.44 | 5.556 | 5.556 | 11.27 | 1.726 | 0.2401 | 1.842e+04 | -0.8475 |
| 1 | holders_delta_pct <= 29.33 | holders_delta_pct | 29.33 | <= | 36 | 19.44 | 5.556 | 5.556 | 11.27 | 1.726 | 0.2821 | 1.945e+04 | 3.632 |
| 1 | liquidity_delta_pct <= 4.28 | liquidity_delta_pct | 4.28 | <= | 36 | 19.44 | 5.556 | 5.556 | 11.27 | 1.726 | 0.2275 | 1.882e+04 | -0.8475 |
| 1 | liq_to_mc_delta >= -0.04438 | liq_to_mc_delta | -0.04438 | >= | 36 | 19.44 | 5.556 | 5.556 | 11.27 | 1.726 | 0.2464 | 1.842e+04 | 1.411 |
| 1 | vol_to_mc_delta >= 0.1338 | vol_to_mc_delta | 0.1338 | >= | 36 | 19.44 | 5.556 | 5.556 | 11.27 | 1.726 | 0.3298 | 1.849e+04 | 2.767 |
| 3 | bundle_pct <= 14.38 | bundle_pct | 14.38 | <= | 23 | 17.39 | 8.696 | 8.696 | 10.42 | 1.67 | 1.113 | 1.937e+04 | 18.33 |
| 3 | sniper_pct >= 1.066 | sniper_pct | 1.066 | >= | 23 | 17.39 | 13.04 | 8.696 | 10.42 | 1.67 | 0.841 | 2.3e+04 | 31.67 |
| 5 | avg_buy_size_delta_pct >= 5.473 | avg_buy_size_delta_pct | 5.473 | >= | 54 | 18.52 | 14.81 | 7.407 | 11.21 | 1.651 | 2.183 | 2.24e+04 | 32.34 |
| 5 | holders >= 209.5 | holders | 209.5 | >= | 27 | 18.52 | 18.52 | 11.11 | 11.21 | 1.651 | 2.205 | 2.465e+04 | 40.54 |
| 5 | volume_usd >= 4.816e+04 | volume_usd | 4.816e+04 | >= | 27 | 18.52 | 14.81 | 7.407 | 11.21 | 1.651 | 2.559 | 2.483e+04 | 42.38 |
| 5 | vol_1h >= 4.816e+04 | vol_1h | 4.816e+04 | >= | 27 | 18.52 | 14.81 | 7.407 | 11.21 | 1.651 | 2.559 | 2.483e+04 | 42.38 |
| 5 | liq_to_mc <= 0.5817 | liq_to_mc | 0.5817 | <= | 27 | 18.52 | 18.52 | 11.11 | 11.21 | 1.651 | 1.458 | 2.998e+04 | 52.13 |
| 5 | holders_delta >= 71 | holders_delta | 71 | >= | 27 | 18.52 | 18.52 | 11.11 | 11.21 | 1.651 | 2.194 | 2.492e+04 | 46.32 |
| 5 | top10_delta >= 0.1343 | top10_delta | 0.1343 | >= | 27 | 18.52 | 14.81 | 11.11 | 11.21 | 1.651 | 2.181 | 2.213e+04 | 27.93 |
| 5 | liq_to_mc_delta <= -0.1366 | liq_to_mc_delta | -0.1366 | <= | 27 | 18.52 | 18.52 | 11.11 | 11.21 | 1.651 | 1.308 | 2.837e+04 | 60.76 |
| 5 | avg_buy_size_delta_pct >= 14.75 | avg_buy_size_delta_pct | 14.75 | >= | 27 | 18.52 | 14.81 | 7.407 | 11.21 | 1.651 | 2.329 | 2.241e+04 | 31.67 |
| 10 | liq_to_mc <= 0.5776 | liq_to_mc | 0.5776 | <= | 28 | 14.29 | 7.143 | 7.143 | 8.85 | 1.614 | 2.469 | 4.693e+04 | 85.25 |
| 3 | avg_buy_size_sol >= 1.698 | avg_buy_size_sol | 1.698 | >= | 24 | 16.67 | 8.333 | 4.167 | 10.42 | 1.6 | 0.8201 | 2.405e+04 | 20.97 |
| 3 | buys_delta_pct >= 78.03 | buys_delta_pct | 78.03 | >= | 24 | 16.67 | 8.333 | 8.333 | 10.42 | 1.6 | 1.23 | 2.526e+04 | 27.68 |
| 3 | liquidity_delta_pct <= 0.317 | liquidity_delta_pct | 0.317 | <= | 24 | 16.67 | 12.5 | 8.333 | 10.42 | 1.6 | 0.3944 | 2.017e+04 | -4.671 |
| 3 | liq_to_mc_delta <= -0.1384 | liq_to_mc_delta | -0.1384 | <= | 24 | 16.67 | 16.67 | 12.5 | 10.42 | 1.6 | 1.107 | 2.65e+04 | 59.94 |
| 10 | avg_buy_size_delta_pct >= 5.603 | avg_buy_size_delta_pct | 5.603 | >= | 57 | 14.04 | 8.772 | 5.263 | 8.85 | 1.586 | 2.492 | 2.378e+04 | 36.52 |

## Survivor vs Failure Feature Comparison

| window_minutes | feature | group | tokens | mean | median | p25 | p75 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | entry_market_cap | survived | 8 | 1.943e+04 | 1.911e+04 | 1.679e+04 | 2.135e+04 |
| 1 | entry_market_cap | failed | 63 | 5.178e+04 | 2.038e+04 | 1.808e+04 | 2.539e+04 |
| 1 | holders | survived | 8 | 145.4 | 129 | 118.2 | 174 |
| 1 | holders | failed | 63 | 141.4 | 143 | 108.5 | 166 |
| 1 | buys | survived | 8 | 72.62 | 66.5 | 37.25 | 111 |
| 1 | buys | failed | 63 | 72.41 | 66 | 47.5 | 93 |
| 1 | count_buy | survived | 8 | 72.62 | 66.5 | 37.25 | 111 |
| 1 | count_buy | failed | 63 | 72.41 | 66 | 47.5 | 93 |
| 1 | volume_usd | survived | 8 | 3.643e+04 | 3.404e+04 | 2.379e+04 | 4.453e+04 |
| 1 | volume_usd | failed | 63 | 3.181e+04 | 3.019e+04 | 2.396e+04 | 3.949e+04 |
| 1 | vol_1h | survived | 8 | 3.643e+04 | 3.404e+04 | 2.379e+04 | 4.453e+04 |
| 1 | vol_1h | failed | 63 | 3.181e+04 | 3.019e+04 | 2.396e+04 | 3.949e+04 |
| 1 | entry_liquidity | survived | 8 | 1.323e+04 | 1.306e+04 | 1.228e+04 | 1.419e+04 |
| 1 | entry_liquidity | failed | 63 | 1.378e+04 | 1.338e+04 | 1.258e+04 | 1.457e+04 |
| 1 | bundle_pct | survived | 8 | 26.71 | 26.94 | 21.42 | 31.48 |
| 1 | bundle_pct | failed | 61 | 25.98 | 25.43 | 17.8 | 36.58 |
| 1 | sniper_pct | survived | 8 | 1.627 | 1.187 | 0.1487 | 2.65 |
| 1 | sniper_pct | failed | 60 | 2.232 | 0 | 0 | 1.257 |
| 1 | top10_holder_pct | survived | 8 | 21.64 | 22.19 | 19.98 | 24.03 |
| 1 | top10_holder_pct | failed | 63 | 23.4 | 23.72 | 21.58 | 26.52 |
| 1 | liq_to_mc | survived | 8 | 0.687 | 0.6839 | 0.6652 | 0.7313 |
| 1 | liq_to_mc | failed | 63 | 0.6404 | 0.6749 | 0.6061 | 0.72 |
| 1 | vol_to_mc | survived | 8 | 1.906 | 1.611 | 1.248 | 2.071 |
| 1 | vol_to_mc | failed | 63 | 1.451 | 1.455 | 1.098 | 1.821 |
| 1 | avg_buy_size_sol | survived | 8 | 1.597 | 1.618 | 1.425 | 1.777 |
| 1 | avg_buy_size_sol | failed | 63 | 1.534 | 1.5 | 1.386 | 1.643 |
| 1 | mc_delta_pct | survived | 8 | -3.462 | -10.95 | -15 | 0.3841 |
| 1 | mc_delta_pct | failed | 63 | 21.9 | 13.28 | 2.067 | 34.31 |
| 1 | holders_delta | survived | 8 | 25.88 | 13.5 | 6.75 | 28 |
| 1 | holders_delta | failed | 63 | 38.62 | 33 | 18 | 57 |
| 1 | holders_delta_pct | survived | 8 | 24.19 | 13.29 | 6.889 | 18.25 |
| 1 | holders_delta_pct | failed | 63 | 39.97 | 36 | 19.01 | 49 |
| 1 | buys_delta | survived | 8 | 23.25 | 14.5 | 10.5 | 33.5 |
| 1 | buys_delta | failed | 63 | 22.14 | 18 | 9 | 30 |
| 1 | buys_delta_pct | survived | 8 | 48.05 | 38.68 | 28.17 | 63.29 |
| 1 | buys_delta_pct | failed | 63 | 53.07 | 37.5 | 23.61 | 66.73 |
| 1 | volume_delta_pct | survived | 8 | 48.15 | 27.9 | 15.05 | 49.03 |
| 1 | volume_delta_pct | failed | 63 | 45.9 | 33.56 | 17.52 | 59.5 |
| 1 | liquidity_delta_pct | survived | 8 | -2.187 | -5.63 | -7.775 | 0.1702 |
| 1 | liquidity_delta_pct | failed | 63 | 6.111 | 5.023 | 0.1731 | 13.78 |
| 1 | bundle_delta | survived | 8 | -8.334 | -4.947 | -9.342 | -1.226 |
| 1 | bundle_delta | failed | 61 | -0.8318 | -0.2984 | -3.245 | 1.134 |
| 1 | sniper_delta | survived | 8 | -1.032 | -0.0707 | -1.211 | 0 |
| 1 | sniper_delta | failed | 60 | -0.5809 | 0 | -0.1448 | 0 |
| 1 | top10_delta | survived | 8 | -6.57 | -0.7259 | -4.688 | 0.8666 |
| 1 | top10_delta | failed | 63 | -2.07 | -0.5033 | -2.566 | 0 |
| 1 | liq_to_mc_delta | survived | 8 | 0.01784 | 0.04152 | -0.0003821 | 0.05314 |
| 1 | liq_to_mc_delta | failed | 63 | -0.07526 | -0.0491 | -0.108 | -0.009957 |
| 1 | vol_to_mc_delta | survived | 8 | 0.6245 | 0.3423 | 0.2898 | 0.4866 |
| 1 | vol_to_mc_delta | failed | 63 | 0.1825 | 0.1276 | 0.00606 | 0.3359 |
| 1 | avg_buy_size_delta_pct | survived | 8 | 2.994 | 3.457 | -5.088 | 12.39 |
| 1 | avg_buy_size_delta_pct | failed | 63 | 4.264 | 4.328 | 0.7478 | 7.498 |
| 3 | entry_market_cap | survived | 10 | 2.327e+04 | 2.253e+04 | 2.102e+04 | 2.571e+04 |
| 3 | entry_market_cap | failed | 86 | 4.993e+04 | 2.081e+04 | 1.861e+04 | 2.535e+04 |
| 3 | holders | survived | 10 | 167.5 | 155 | 112 | 207 |
| 3 | holders | failed | 86 | 159.4 | 154 | 118 | 183.8 |
| 3 | buys | survived | 10 | 44.2 | 37.5 | 23.75 | 53.5 |
| 3 | buys | failed | 86 | 76.36 | 64.5 | 46.5 | 93 |
| 3 | count_buy | survived | 10 | 44.2 | 37.5 | 23.75 | 53.5 |
| 3 | count_buy | failed | 86 | 76.36 | 64.5 | 46.5 | 93 |
| 3 | volume_usd | survived | 10 | 3.462e+04 | 3.61e+04 | 2.533e+04 | 4.304e+04 |
| 3 | volume_usd | failed | 86 | 3.847e+04 | 3.636e+04 | 2.666e+04 | 4.448e+04 |
| 3 | vol_1h | survived | 10 | 3.462e+04 | 3.61e+04 | 2.533e+04 | 4.304e+04 |
| 3 | vol_1h | failed | 86 | 3.847e+04 | 3.636e+04 | 2.666e+04 | 4.448e+04 |
| 3 | entry_liquidity | survived | 10 | 1.333e+04 | 1.356e+04 | 1.239e+04 | 1.426e+04 |
| 3 | entry_liquidity | failed | 86 | 1.372e+04 | 1.351e+04 | 1.256e+04 | 1.497e+04 |
| 3 | bundle_pct | survived | 10 | 18.85 | 18.16 | 11.22 | 23.55 |
| 3 | bundle_pct | failed | 82 | 23.9 | 23.79 | 15.01 | 34.14 |
| 3 | sniper_pct | survived | 8 | 1.512 | 0.692 | 0 | 2.856 |
| 3 | sniper_pct | failed | 83 | 1.513 | 0 | 0 | 0.5969 |
| 3 | top10_holder_pct | survived | 10 | 23.8 | 23.49 | 22.06 | 25.7 |
| 3 | top10_holder_pct | failed | 86 | 22.39 | 23 | 20.14 | 25.36 |
| 3 | liq_to_mc | survived | 10 | 0.5907 | 0.642 | 0.4927 | 0.6713 |
| 3 | liq_to_mc | failed | 85 | 0.622 | 0.6614 | 0.6031 | 0.6998 |
| 3 | vol_to_mc | survived | 10 | 1.506 | 1.539 | 1.115 | 1.877 |
| 3 | vol_to_mc | failed | 85 | 1.652 | 1.666 | 1.129 | 2.124 |
| 3 | avg_buy_size_sol | survived | 10 | 1.606 | 1.62 | 1.464 | 1.726 |
| 3 | avg_buy_size_sol | failed | 86 | 1.554 | 1.5 | 1.38 | 1.663 |
| 3 | mc_delta_pct | survived | 10 | 24.2 | 21.6 | 7.902 | 38.57 |
| 3 | mc_delta_pct | failed | 86 | 25.8 | 21.2 | 3.934 | 41.04 |
