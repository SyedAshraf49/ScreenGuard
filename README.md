# ScreenGuard – Smart Screen Time Controller

<p align="center">
  <img src="web/logo.svg" alt="ScreenGuard Logo" width="120" />
</p>

<p align="center">
  <strong>A comprehensive screen monitoring and digital wellness utility for Windows, macOS, and Linux.</strong><br/>
  Track app usage, enforce healthy limits, protect your focus, and monitor your well-being — all in one tool.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue?logo=python" alt="Python 3.10+" />
  <img src="https://img.shields.io/badge/FastAPI-0.133-green?logo=fastapi" alt="FastAPI" />
  <img src="https://img.shields.io/badge/PyQt6-6.10-informational?logo=qt" alt="PyQt6" />
  <img src="https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey" alt="Platform" />
  <img src="https://img.shields.io/badge/License-MIT-yellow" alt="MIT License" />
</p>

---

## Table of Contents

- [Project Overview](#project-overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [Usage Guide](#usage-guide)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

---

## Project Overview

**ScreenGuard** is a full-featured screen monitoring and digital wellness tool designed to help you understand your digital habits, enforce healthy screen time limits, and protect your mental and physical well-being. It offers two interfaces:

- **Desktop App** — A native PyQt6 GUI with rich visualizations, theme support, and real-time tracking.
- **Web App** — A browser-based dashboard served by a FastAPI backend, accessible from any device on your local network.

ScreenGuard automatically detects which application is in the foreground (Windows), logs usage to a local SQLite database, generates smart recommendations, and can even lock distracting apps when you exceed your self-imposed limits.

> **Note:** Active window tracking and app locking require **Windows**. The web dashboard and all other features work fully on **macOS/Linux**.

---

## Features

### 📊 Usage Monitoring
- Automatic foreground app detection and logging (1-minute intervals, no manual input)
- Per-app daily usage totals and weekly breakdowns
- Top 5 most-used apps with colour-coded bar charts
- Weekly day-by-day usage chart with persistent stacked/area style toggle
- Usage trend detection (increasing/decreasing vs. yesterday)

### 🔒 Screen Protection & App Locking
- Set per-app daily time limits
- Background enforcement engine that minimises locked apps automatically (Windows)
- Emergency unlock button for critical situations
- Daily limit exceedance popup notifications

### 🧠 Smart Recommendations
- AI-style recommendation engine that analyses usage patterns
- Detects app dominance, intensity spikes, focus degradation
- Distinguishes productivity apps (VSCode, Word) from distractions (YouTube, Instagram)
- Emoji-prefixed, actionable suggestions (🚨 urgent → 🌱 light nudge)

### 👁️ Eye Health & Focus Coaching
- Continuous screen-time tracking with eye strain load percentage
- 20-20-20 rule inspired recovery reminders (50-minute focus windows)
- Guided 90-second recovery sessions with contextual suggestions
- Focus score display

### 😌 Well-Being & Mood Tracking
- Daily mood entries on a 1–10 scale with optional notes
- Auto mood estimation based on screen time patterns
- Mood history and correlation analysis (mood vs. usage trends)

### 🏆 Gamification & Achievements
- Points-based progression system with 6 levels
- 8 achievement types: Disciplined Day, Focus Master, First Week, Under Budget, Focus Warrior, Early Bird, Weekend Warrior, Digital Detox
- XP progress bars and level-up notifications

### 👥 Social Features
- Friends list with add/block management
- Group creation and in-app messaging
- Challenges with real-time leaderboards
- Privacy-controlled achievement sharing

### 📅 Schedule-Aware Limits
- Google Calendar integration for context-aware screen time limits
- Exam mode: automatically reduces daily limit to 60% of baseline
- Busy-day detection: proportionally tightens limits based on calendar load

### 🎨 Themes & UI
- 5 switchable themes: Night, Day, Aurora, Sunset, Monochrome
- Theme-specific fonts for a cohesive look
- Sidebar-based navigation with modern card layouts
- First-time web onboarding modal with persistent personalised greeting

### 🔔 Notifications
- Multi-channel delivery: desktop, email, SMS, voice, wallpaper
- Quiet hours and Do-Not-Disturb mode
- Configurable urgency filtering (low → critical)
- Popup alerts for limit exceedance and newly unlocked achievements

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Desktop UI** | Python 3.10+, PyQt6 6.10, Matplotlib |
| **Web UI** | HTML5, CSS3, Vanilla JavaScript |
| **Backend API** | FastAPI 0.133, Uvicorn, Starlette |
| **Database** | SQLite (via Python `sqlite3`) |
| **Core / ML** | psutil, plyer, google-api-python-client |
| **Notifications** | plyer (desktop), smtplib (email) |
| **Charting** | Matplotlib (desktop), Chart.js-compatible API (web) |
| **Auth / OAuth** | google-auth, google-auth-oauthlib |
| **Data Validation** | Pydantic v2 |
| **Packaging** | pip, venv, setup scripts |

---

## Installation

### Prerequisites

- **Python 3.10 or higher** — [Download](https://python.org)
- **Windows, macOS, or Linux**
- Git (to clone the repository)

### Clone the Repository

```bash
git clone https://github.com/SyedAshraf49/ScreenGuard.git
cd ScreenGuard
```

### Automated Setup (Recommended)

**Windows:**
```bat
setup.bat
```

**macOS / Linux:**
```bash
chmod +x setup.sh
./setup.sh
```

The setup scripts automatically:
1. Create a Python virtual environment (`.venv/`)
2. Upgrade `pip` to the latest version
3. Install all dependencies from `requirements.txt`
4. Initialise the SQLite database

### Manual Setup

```bash
# Create virtual environment
python -m venv .venv

# Install dependencies
# Windows:
.venv\Scripts\pip install -r requirements.txt

# macOS / Linux:
.venv/bin/pip install -r requirements.txt
```

---

## Quick Start

### Option 1 — Desktop App (PyQt6 GUI)

```bash
# Windows
.venv\Scripts\python main.py

# macOS / Linux
.venv/bin/python main.py
```

The desktop window (900 × 550 px) opens with the Dashboard as the default view. Navigation is via the left sidebar.

### Option 2 — Web App (Browser Dashboard)

```bash
# Windows
.venv\Scripts\python -m uvicorn backend.app:app --reload

# macOS / Linux
.venv/bin/python -m uvicorn backend.app:app --reload
```

Then open **http://127.0.0.1:8000** in your browser. On first launch you will be prompted to enter your display name via an in-page modal.

> **Tip:** Both interfaces share the same SQLite database, so data is always in sync.

---

## Project Structure

```
ScreenGuard/
├── main.py                     # Desktop app entry point (PyQt6)
├── requirements.txt            # Python dependencies
├── setup.bat                   # Windows one-click setup
├── setup.sh                    # macOS/Linux one-click setup
│
├── backend/                    # FastAPI REST API layer
│   ├── app.py                  # API endpoints (usage, locker, social, onboarding…)
│   ├── db.py                   # SQLite schema, queries, connection management
│   └── data/                   # Database directory (screenguard.db created here)
│
├── core/                       # Business logic engines
│   ├── active_window.py        # Foreground app detection (Win32 API)
│   ├── app_locker.py           # Background enforcement daemon (Windows)
│   ├── smart_notifier.py       # Multi-channel notification system
│   ├── gamification.py         # Points, levels, and achievements engine
│   ├── well_being_tracker.py   # Mood logging and correlation analysis
│   ├── eye_health_monitor.py   # Eye strain tracking and recovery coaching
│   ├── recommender.py          # Smart recommendation engine
│   ├── social_features.py      # Friends, groups, challenges, and sharing
│   ├── calendar_integration.py # Google Calendar OAuth2 client
│   ├── schedule_awareness.py   # Adaptive limits based on calendar events
│   └── memory_store.py         # In-memory fallback data structures
│
├── ui/                         # PyQt6 desktop views
│   ├── sidebar.py              # Navigation sidebar
│   ├── dashboard.py            # Dashboard (charts, recommendations, summary)
│   ├── reports.py              # Usage analytics and exports
│   ├── health.py               # Eye health and focus coach view
│   ├── achievements.py         # Gamification and XP view
│   ├── social.py               # Friends, groups, and challenges view
│   ├── well_being.py           # Mood tracking and wellness view
│   ├── locker.py               # App locking and limit management
│   ├── settings.py             # App settings (limits, themes, notifications)
│   ├── ui_helpers.py           # Shared UI utilities (card shadows, etc.)
│   ├── styles.qss              # Default (Night) theme stylesheet
│   └── themes/                 # Additional QSS theme files
│       ├── night.qss
│       ├── day.qss
│       ├── aurora.qss
│       ├── sunset.qss
│       └── mono.qss
│
└── web/                        # Browser-based dashboard
    ├── index.html              # Single-page app shell
    ├── app.js                  # View routing, API calls, charting logic
    ├── styles.css              # Modern card-based responsive styles
    └── logo.svg                # ScreenGuard brand logo
```

---

## Usage Guide

### Tracking Your Screen Time

ScreenGuard starts logging automatically as soon as the app launches. No configuration is needed. Navigate to the **Dashboard** to see:

- **Today's total screen time** with a live active-app counter
- **Top 5 apps** for the current day
- **Weekly bar chart** (stacked or area — toggle persists across restarts)
- **Smart recommendations** based on your latest usage patterns

### Setting Daily Limits

1. Open **Settings** (desktop) or the **Settings** page (web).
2. Use the **Daily Limit** slider to set your overall limit (1–24 hours).
3. For per-app limits, open the **Locker** page, select an app from the dropdown, enter a limit in minutes, and click **Set Limit**.

### Locking Distracting Apps

1. Navigate to **Locker**.
2. Select the app you want to restrict.
3. Click **Lock App** — ScreenGuard will minimise it automatically whenever the daily limit is reached.
4. Use **Emergency Unlock** to temporarily override a lock.

> App locking is supported on **Windows only**.

### Eye Health & Focus

The **Health** page tracks how long you have been looking at the screen without a break. When eye load exceeds 80 % (approximately 50 minutes of continuous use), ScreenGuard suggests a recovery session. Click **Start Recovery Session** to begin a guided 90-second break with contextual suggestions.

### Tracking Your Mood

Open **Well-Being** and use the slider to log your current mood (1 = very low, 10 = excellent). Add an optional note for context. ScreenGuard correlates mood entries with your usage data over time to reveal patterns.

### Achievements

ScreenGuard awards XP for healthy digital habits. Visit the **Achievements** page to see your unlocked badges, current level, and XP needed for the next level.

### Social Challenges

1. Open **Social** and add friends by username.
2. Create a challenge, invite friends, and set a goal (e.g., "Under 4 hours screen time this week").
3. Track the leaderboard in real time.

---

## Configuration

All persistent settings are stored in `backend/data/screenguard.db` (SQLite). Most options are accessible through the UI without touching the database directly.

### Settings Page Options

| Setting | Default | Description |
|---|---|---|
| Daily Screen Time Limit | 8 hours | Overall daily usage cap; triggers notification when exceeded |
| Notification Channels | Desktop | Enable/disable desktop, email, SMS, voice, or wallpaper alerts |
| Minimum Urgency | Low | Only deliver notifications at or above this urgency level |
| Quiet Hours | 22:00 – 07:00 | No notifications are sent during this window |
| Do-Not-Disturb | Off | Temporarily suppresses all notifications |
| Theme | Night | Visual theme for the desktop app (Night / Day / Aurora / Sunset / Mono) |
| Google Calendar Credentials | _(empty)_ | Path to `credentials.json` for schedule-aware limits |
| Display Name | _(prompted)_ | Personalised greeting shown in the web dashboard |

### Google Calendar Integration

1. Create a Google Cloud project and enable the **Google Calendar API**.
2. Download `credentials.json` (OAuth2 Desktop App credentials).
3. In **Settings**, set the path to your `credentials.json` file.
4. ScreenGuard will open a browser window for one-time authorisation.
5. After authorisation, limits are adjusted automatically based on your calendar events.

### Environment Variables

ScreenGuard supports optional `.env` configuration in the project root:

```dotenv
# Override the default database path
DB_PATH=backend/data/screenguard.db

# Email notification settings (optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your@email.com
SMTP_PASS=your_app_password
```

---

## Troubleshooting

### App does not start after setup

- Confirm Python 3.10+ is installed: `python --version`
- Re-run the setup script to reinstall dependencies: `setup.bat` (Windows) or `./setup.sh` (macOS/Linux)
- Activate the virtual environment manually and check for import errors:
  ```bash
  # Windows
  .venv\Scripts\activate
  python main.py

  # macOS / Linux
  source .venv/bin/activate
  python main.py
  ```

### Active window tracking not working

Active window detection uses the Win32 API and is **Windows-only**. On macOS/Linux, usage must be logged manually or via the web interface. All other features remain fully functional.

### Web dashboard shows no data

- Ensure the backend server is running: `uvicorn backend.app:app --reload`
- Check that you are accessing `http://127.0.0.1:8000` (not HTTPS).
- Open the browser console (F12) and look for API errors.
- Verify `backend/data/screenguard.db` exists; if not, re-run setup.

### App locking is not enforced

- App locking is **Windows-only**.
- Run ScreenGuard with administrator privileges if window minimisation is blocked.
- Check that the app name in the **Locker** list exactly matches the process name shown in Task Manager (without `.exe`).

### Google Calendar integration fails

- Confirm `credentials.json` exists at the path specified in **Settings**.
- Delete `token.json` (if it exists) and re-authorise by re-entering the credentials path.
- Ensure the Google Calendar API is enabled in your Google Cloud project.

### High CPU usage

- The background logging interval is 60 seconds by default; this is lightweight.
- If CPU usage is high, check whether the `AppLocker` daemon is looping rapidly — this can occur if a locked app constantly reopens.

### PyQt6 display issues on Linux

```bash
# Install Qt platform plugin dependencies
sudo apt-get install libxcb-xinerama0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 libxcb-randr0 libxcb-render-util0 libxcb-xkb1 libxkbcommon-x11-0
```

---

## Contributing

Contributions are welcome! Here is how to get involved:

1. **Fork** the repository and create your feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```
2. **Install** dependencies as described in [Installation](#installation).
3. **Make your changes**, keeping code style consistent with the existing codebase.
4. **Test** your changes thoroughly:
   - Start the desktop app: `python main.py`
   - Start the web server and verify in the browser: `uvicorn backend.app:app --reload`
5. **Commit** with a descriptive message:
   ```bash
   git commit -m "feat: add your feature description"
   ```
6. **Open a Pull Request** against the `main` branch and describe what you changed and why.

### Code Style Guidelines

- Follow [PEP 8](https://peps.python.org/pep-0008/) for Python code.
- Keep functions focused and single-purpose.
- Add docstrings to new public functions and classes.
- Avoid introducing new third-party libraries unless necessary.

### Reporting Issues

If you find a bug or have a feature request, please [open an issue](https://github.com/SyedAshraf49/ScreenGuard/issues) and include:
- Your operating system and Python version
- Steps to reproduce the issue
- Expected vs. actual behaviour
- Any relevant error messages or screenshots

---

## License

This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for details.

---

<p align="center">Built with ❤️ by <a href="https://github.com/SyedAshraf49">Syed Ashraf</a></p>
