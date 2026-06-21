# Vlak API Mirror + Aladdin Research Engine

Python V1 for mirroring every Vlak alert to Telegram, storing alert metrics in SQLite, enriching alerts with Solana Tracker research metrics, tracking outcomes and private milestones, and viewing results in a local Streamlit dashboard.

Every new Vlak alert is stored. Telegram sending is currently set to the Aladdin 10-minute filter:

- 12 <= buys_10m <= 90
- sells_10m <= buys_10m
- net_buy_volume_10m > 0
- buy_volume_sol_10m >= 10 SOL
- buy_volume_sol_10m > buys_10m
- buy_volume_usd_10m >= $10,000
- market_cap between $8,000 and $60,000
- liquidity >= $5,000
- age <= 30 minutes
- unique_buyers_10m >= 10
- top_buyer_share_10m <= 35%

Solana Tracker data is stored for research only.

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Fill `.env` with your credentials.

The default database for this project is `vlak_aladdin_research.sqlite` to keep it separate from any unrelated projects that also use `research.sqlite`.

## Run

Initialize the database:

```powershell
.\.venv\Scripts\python.exe -m aladdin_research_engine.db
```

Run the signal collector:

```powershell
.\.venv\Scripts\python.exe -m aladdin_research_engine.collector
```

Run the outcome tracker:

```powershell
.\.venv\Scripts\python.exe -m aladdin_research_engine.outcome_tracker
```

Run the dashboard:

```powershell
.\.venv\Scripts\streamlit.exe run .\aladdin_research_engine\dashboard.py
```

## Environment

Required:

- `VLAK_API_KEY`
- `VLAK_BASE_URL`
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`
- `SOLANA_TRACKER_API_KEY`

Optional:

- `SOLANA_TRACKER_BASE_URL`
- `DATABASE_PATH`
- `SIGNAL_POLL_SECONDS`
- `OUTCOME_POLL_SECONDS`
- `OUTCOME_TRACK_HOURS`

## Notes

- Alerts are deduplicated by `notificationId`, not mint.
- One mint can appear in many alerts.
- Outcome and milestone state is keyed by mint.
- Milestone Telegram messages are sent once per mint per milestone.
- Dashboard reads from SQLite only; it does not call external APIs.



## Formation Notes
Persistent formation logic is documented in [FORMATIONS.md](./FORMATIONS.md).

