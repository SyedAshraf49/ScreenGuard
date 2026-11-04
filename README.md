# ScreenGuard

ScreenGuard is a screen-time management and digital well-being application with a PyQt6 desktop client and a FastAPI-powered web dashboard. It records app usage, supports daily and per-app limits, and provides usage reports and focus and well-being tools.

## About

ScreenGuard helps users understand and manage their screen habits. Usage data and settings are stored locally in SQLite, while the desktop and browser interfaces provide dashboards, reports, limit controls, and recovery prompts.

## Features

- Desktop dashboard and browser-based interface
- App usage logging, summaries, and reports
- Daily screen-time and per-app limits
- Windows app monitoring and automatic app-lock enforcement
- Usage recommendations, focus recovery prompts, and well-being insights
- Local achievement and social features
- Theme and notification settings
- Optional Google Calendar integration for schedule-aware limit suggestions

## Skills and Technologies

- **Python** — application logic and desktop/system integration
- **PyQt6** — desktop user interface
- **FastAPI and Uvicorn** — web API and local web server
- **HTML, CSS, and JavaScript** — browser interface
- **SQLite** — local data persistence
- **psutil and Windows APIs** — process information and active-window monitoring
- **REST API development, usage analytics, background monitoring, and notification workflows**
- **Google Calendar API** — optional calendar integration

## Requirements

- Python 3.10 or newer
- Windows, macOS, or Linux

The desktop and web interfaces can run on Windows, macOS, and Linux. Active-window detection and automatic app-lock enforcement use Windows APIs; on macOS and Linux, usage must be entered manually.

## Setup

The setup scripts create a virtual environment and install the dependencies from `requirements.txt`.

**Windows:**

```bat
setup.bat
```

**macOS or Linux:**

```bash
chmod +x setup.sh
./setup.sh
```

## Run the Desktop App

**Windows:**

```bat
.venv\Scripts\python main.py
```

**macOS or Linux:**

```bash
.venv/bin/python main.py
```

## Run the Web Dashboard

Start the local web server:

**Windows:**

```bat
.venv\Scripts\python -m uvicorn backend.app:app --reload
```

**macOS or Linux:**

```bash
.venv/bin/python -m uvicorn backend.app:app --reload
```

Then open [http://127.0.0.1:8000](http://127.0.0.1:8000) in a browser.

## Local Data

ScreenGuard stores its SQLite database at `backend/data/screenguard.db`. Google Calendar integration is optional and requires Google API credentials.
