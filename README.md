# ScreenGuard – Smart Screen Time Controller

## How to Run
1. Install Python 3.10+
2. pip install -r requirements.txt
3. python main.py

## Web Version
1. Install Python 3.10+
2. pip install -r requirements.txt
3. python -m uvicorn backend.app:app --reload
4. Open http://127.0.0.1:8000

Notes:
- The web UI is served from the backend and uses the FastAPI JSON API.
- Google Calendar sync requires the Google API packages already listed in requirements.txt.

## Features
- App-wise usage tracking
- Automatic active-app logging (1-minute intervals)
- Adaptive focus recovery coach (focus score + guided recovery sessions)
- Automatic mood check-ins for trend/correlation insights
- No manual logging required (fully automatic tracking)
- Multiple switchable themes with theme-specific fonts (Night, Day, Aurora, Sunset, Mono)
- Dashboard weekly day-by-day usage chart with color-coded apps and persistent style switch (stacked/area)
- Dashboard Top 5 apps preference is saved across restarts
- Auto-logging pause/resume state is saved across restarts
- Expanded smart recommendations with usage intensity, trend, focus, and app-dominance insights
- First-time web username onboarding with persistent personalized greeting
- Display name can be updated directly from web Settings (and reflected in greeting)
- Popup notifications for daily limit exceedance and newly unlocked achievements
- First-time name capture uses an in-page website modal (not browser localhost prompt)
- Sidebar-based modern UI
- Smart recommendation engine
- Reports and limits
