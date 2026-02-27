# ScreenGuard – Smart Screen Time Controller

## Requirements
- Python 3.10 or higher — download from https://python.org
- Windows, macOS, or Linux

> **Note:** Active window tracking (auto-detecting which app you're using) only works on **Windows**. On macOS/Linux the web dashboard and all other features still work fully.

---

## Quick Setup (Recommended)

**Windows:**
```bat
setup.bat
```

**macOS / Linux:**
```bash
chmod +x setup.sh
./setup.sh
```

These scripts automatically create a virtual environment and install all dependencies.

---

## Manual Setup

```bash
python -m venv .venv

# Windows
.venv\Scripts\pip install -r requirements.txt

# macOS / Linux
.venv/bin/pip install -r requirements.txt
```

---

## Running the App

### Desktop App (PyQt6 GUI)
```bash
# Windows
.venv\Scripts\python main.py

# macOS / Linux
.venv/bin/python main.py
```

### Web App (Browser UI)
```bash
# Windows
.venv\Scripts\python -m uvicorn backend.app:app --reload

# macOS / Linux
.venv/bin/python -m uvicorn backend.app:app --reload
```
Then open **http://127.0.0.1:8000** in your browser.

---

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
