# Research v3 - Vlak API Mirror + Raw Capture Engine

Python research engine for storing every Vlak API alert in SQLite, capturing raw alert metrics, tracking outcomes and private milestones, and viewing results in a local Streamlit dashboard.

Every new Vlak alert is stored. Telegram sending and Aladdin pass/reject routing are paused in v3 so the database can capture the full Vlak API stream for research. Historical Aladdin filter logic remains in the codebase for reference, but it is not the active routing path.

Solana Tracker data is stored for research only.

## Current v3 mode

This local folder is the active v3 research workspace. The collector stores raw Vlak API alerts and raw capture metrics for all incoming signals. Aladdin pass/reject routing, strategy Telegram sends, and filtered alert delivery are paused in the collector so the dataset can capture the full Vlak API stream for research.

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



