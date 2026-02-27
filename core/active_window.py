from __future__ import annotations

import ctypes
import sys
from ctypes import wintypes
from pathlib import Path

import psutil


def get_active_app_name() -> str:
    if sys.platform != "win32":
        return ""

    user32 = ctypes.windll.user32
    hwnd = user32.GetForegroundWindow()
    if not hwnd:
        return ""

    pid = wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    if not pid.value:
        return ""

    try:
        process = psutil.Process(pid.value)
        name = process.name() or ""
    except (psutil.Error, OSError):
        return ""

    app_name = Path(name).stem.strip()
    return app_name