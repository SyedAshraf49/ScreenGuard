@echo off
echo ScreenGuard Setup
echo =================

where python >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.10+ from https://python.org
    pause
    exit /b 1
)

echo Creating virtual environment...
python -m venv .venv

echo Installing dependencies...
.venv\Scripts\pip install -r requirements.txt

echo.
echo Setup complete!
echo.
echo To run the desktop app:
echo   .venv\Scripts\python main.py
echo.
echo To run the web app:
echo   .venv\Scripts\python -m uvicorn backend.app:app --reload
echo   Then open http://127.0.0.1:8000
pause
