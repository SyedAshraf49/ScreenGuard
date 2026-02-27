#!/bin/bash
echo "ScreenGuard Setup"
echo "================="

if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 not found. Please install Python 3.10+ from https://python.org"
    exit 1
fi

echo "Creating virtual environment..."
python3 -m venv .venv

echo "Installing dependencies..."
.venv/bin/pip install -r requirements.txt

echo ""
echo "Setup complete!"
echo ""
echo "To run the desktop app:"
echo "  .venv/bin/python main.py"
echo ""
echo "To run the web app:"
echo "  .venv/bin/python -m uvicorn backend.app:app --reload"
echo "  Then open http://127.0.0.1:8000"
