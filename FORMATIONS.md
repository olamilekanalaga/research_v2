# Formation Notes (Persisted for Recovery)

This repo's research is **separate from runtime secrets**; no `.env` is required to read this doc.

## Current Working Formation (lightweight merged-token layer)

Derived from `v1_total_performance.sqlite` in `work/merged_vlak_datasets/`:

- **Per-token baseline features**
  - `market_cap_at_signal`
  - `liquidity_at_signal`
  - `volume_10m_usd`
  - `buys_10m`
  - `holders_start`, `holders_5m`, `holders_10m`, `holders_30m`, `holders_1h`
  - `top10_holder_pct`, `bundle_pct`, `sniper_pct`
  - outcome counters/timers: `survived_2x`, `survived_3x`, `survived_5x`, `survived_10x`, `time_to_2x_minutes`, `time_to_5x_minutes`, `time_to_10x_minutes`

- **Derived features used in the study**
  - `holder_growth_5m = holders_5m - holders_start`
  - `holder_growth_10m = holders_10m - holders_start`
  - `holder_growth_30m = holders_30m - holders_start`
  - `holder_growth_1h = holders_1h - holders_start`
  - `holder_growth_*_pct = holder_growth / holders_start`
  - `volume_per_10m_buy = volume_10m_usd / buys_10m`
  - `volume_per_10m_holder = volume_10m_usd / holders_10m`
  - `liquidity_to_mcap = liquidity_at_signal / market_cap_at_signal`

## Outcome groups used
- `reached_2x = survived_2x == 1`
- `reached_3x = survived_3x == 1`
- `reached_5x = survived_5x == 1`
- `reached_10x = survived_10x == 1`

Hit-rate is computed two ways in the studies:
1) **all rows**
2) **rows with** `outcome_bucket` **not null**

## Candidate filters that ranked best (n >= 30)

### 5x candidates (all rows)
1. `market_cap_at_signal in [100k,250k]` 
   - n = 35
   - 5x = 54.29%, 10x = 25.71%
   - *high lift, very small sample (n=35)*
2. `liquidity_at_signal >= 20,000`
   - n = 2,531
   - 5x = 36.31%
   - 10x = 21.69%
3. `liquidity_at_signal >= 30,000`
   - n = 1,604
   - 5x = 33.85%
   - 10x = 24.19%
4. `market_cap_at_signal in [25k,50k)`
   - n = 1,008
   - 5x = 29.86%

### 10x candidates (all rows)
1. `market_cap_at_signal in [100k,250k]` (n=35, 10x = 25.71%)
2. `liquidity_at_signal >= 30,000` (n=1,604, 10x = 24.19%)
3. `market_cap_at_signal in [25k,50k)` (n=1,008, 10x = 22.62%)
4. `liquidity_at_signal >= 20,000` (n=2,531, 10x = 21.69%)

## Limitations for this DB layer
This is a **summary DB**, not a raw journey DB.
It does **not** contain per-window FDV/volume/drawdown series (`1m/5m/10m/15m/30m/60m`) required for exact Early-Life Window trajectories.

So this layer is excellent for **formation ranking**, but not for raw window reconstruction.

## How to preserve this safely
- Keep this file in version control.
- Never commit `.env`.
- On any environment, only load this repo + DB files and run scripts with local env locally.
