"""
AppLocker – background enforcement engine.

Runs on a periodic timer (every CHECK_INTERVAL seconds) and minimises any
foreground window whose process name appears in the locked_apps table.
An app stays locked until explicitly unlocked via the web UI (POST /api/locker/unlock).
"""
from __future__ import annotations

import ctypes
import sys
import threading
from ctypes import wintypes
from pathlib import Path
from typing import Callable, Optional

import psutil

CHECK_INTERVAL = 5  # seconds between enforcement checks

# Win32 constants
SW_MINIMIZE = 6
WM_SYSCOMMAND = 0x0112
SC_MINIMIZE = 0xF020


def _get_foreground_pid() -> Optional[int]:
    if sys.platform != "win32":
        return None
    user32 = ctypes.windll.user32
    hwnd = user32.GetForegroundWindow()
    if not hwnd:
        return None
    pid = wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    return int(pid.value) if pid.value else None


def _get_foreground_hwnd() -> Optional[int]:
    if sys.platform != "win32":
        return None
    user32 = ctypes.windll.user32
    hwnd = user32.GetForegroundWindow()
    return int(hwnd) if hwnd else None


def _minimize_hwnd(hwnd: int) -> None:
    """Minimise a window by its handle."""
    user32 = ctypes.windll.user32
    user32.ShowWindow(hwnd, SW_MINIMIZE)


def _app_name_from_pid(pid: int) -> str:
    try:
        process = psutil.Process(pid)
        return Path(process.name() or "").stem.strip()
    except (psutil.Error, OSError):
        return ""


class AppLocker:
    """
    Monitors the active window and enforces locks defined in the DB.

    Usage
    -----
    locker = AppLocker(lock_check_fn, on_locked_fn)
    locker.start()   # starts the background thread
    locker.stop()    # stops it gracefully
    """

    def __init__(
        self,
        lock_check_fn: Callable[[str], bool],
        on_locked_fn: Optional[Callable[[str], None]] = None,
        interval: int = CHECK_INTERVAL,
    ) -> None:
        """
        Parameters
        ----------
        lock_check_fn:
            Called with the current foreground app name.
            Should return True if the app is locked.
        on_locked_fn:
            Optional callback fired when an app is blocked (receives app name).
        interval:
            Seconds between checks.
        """
        self._lock_check = lock_check_fn
        self._on_locked = on_locked_fn
        self._interval = interval
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

    # ── Public ────────────────────────────────────────────────────────────────

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True, name="AppLockerThread")
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=self._interval + 2)

    # ── Internal ──────────────────────────────────────────────────────────────

    def _run(self) -> None:
        while not self._stop_event.wait(self._interval):
            try:
                self._check()
            except Exception:  # noqa: BLE001 – never crash the thread
                pass

    def _check(self) -> None:
        if sys.platform != "win32":
            return

        pid = _get_foreground_pid()
        if not pid:
            return

        app_name = _app_name_from_pid(pid)
        if not app_name:
            return

        if self._lock_check(app_name):
            hwnd = _get_foreground_hwnd()
            if hwnd:
                _minimize_hwnd(hwnd)
            if self._on_locked:
                self._on_locked(app_name)


# ── Convenience factory used by main.py ───────────────────────────────────────

def make_locker(on_locked_fn: Optional[Callable[[str], None]] = None) -> AppLocker:
    """
    Build an AppLocker wired to the live SQLite database.
    Import only after the DB has been initialised.
    """
    from backend.db import is_app_locked  # deferred to avoid circular import

    return AppLocker(
        lock_check_fn=is_app_locked,
        on_locked_fn=on_locked_fn,
    )
