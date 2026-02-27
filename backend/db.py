from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "screenguard.db"

DEFAULT_SETTINGS = {
    "notifications.channels": json.dumps(["desktop"]),
    "notifications.min_urgency": "low",
    "notifications.quiet_start": "22",
    "notifications.quiet_end": "7",
    "notifications.dnd": "0",
    "limits.daily_hours": "6",
    "theme.name": "night",
    "social.share_achievements": "1",
    "social.share_stats": "1",
    "social.anonymous_leaderboards": "0",
    "social.local_username": "you",
    "achievements.points": "0",
    "achievements.level": "1",
}


@contextmanager
def get_conn() -> Iterable[sqlite3.Connection]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with get_conn() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS usage_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                app TEXT NOT NULL,
                duration INTEGER NOT NULL,
                date TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS mood_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mood INTEGER NOT NULL,
                time TEXT NOT NULL,
                date TEXT NOT NULL,
                note TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                message TEXT NOT NULL,
                urgency TEXT NOT NULL,
                channels TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS achievements (
                name TEXT PRIMARY KEY,
                unlocked_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS social_friends (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                display_name TEXT,
                blocked INTEGER NOT NULL,
                added_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS social_groups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                is_private INTEGER NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS social_group_members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id INTEGER NOT NULL,
                username TEXT NOT NULL,
                role TEXT NOT NULL,
                joined_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS social_group_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id INTEGER NOT NULL,
                sender TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS social_challenges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                challenge_type TEXT NOT NULL,
                group_id INTEGER,
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL,
                status TEXT NOT NULL,
                is_anonymous INTEGER NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS social_challenge_participants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                challenge_id INTEGER NOT NULL,
                username TEXT NOT NULL,
                score INTEGER NOT NULL,
                completed INTEGER NOT NULL,
                last_updated TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS social_shares (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                achievement_id TEXT NOT NULL,
                message TEXT NOT NULL,
                audience TEXT NOT NULL,
                targets TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            """
        )

    ensure_default_settings()


def ensure_default_settings() -> None:
    with get_conn() as conn:
        for key, value in DEFAULT_SETTINGS.items():
            conn.execute(
                "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
                (key, value),
            )


def get_setting(key: str, default: Optional[str] = None) -> Optional[str]:
    with get_conn() as conn:
        row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        if row is None:
            return default
        return row["value"]


def set_setting(key: str, value: str) -> None:
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO settings (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, value),
        )


# Usage

def add_usage(app: str, duration: int, date_str: str) -> None:
    now = datetime.now().isoformat(timespec="seconds")
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO usage_entries (app, duration, date, created_at) VALUES (?, ?, ?, ?)",
            (app, int(duration), date_str, now),
        )


def get_usage_for_date(date_str: str) -> List[Dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT app, duration, date FROM usage_entries WHERE date = ?",
            (date_str,),
        ).fetchall()
    return [dict(row) for row in rows]


def get_usage_in_range(start_date: str, end_date: str) -> List[Dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT app, duration, date FROM usage_entries WHERE date BETWEEN ? AND ?",
            (start_date, end_date),
        ).fetchall()
    return [dict(row) for row in rows]


# Mood

def add_mood_entry(mood: int, timestamp: datetime, note: str) -> None:
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO mood_entries (mood, time, date, note) VALUES (?, ?, ?, ?)",
            (
                int(mood),
                timestamp.isoformat(timespec="seconds"),
                str(timestamp.date()),
                note or "",
            ),
        )


def get_mood_entries_for_date(date_str: str) -> List[Dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT mood, time, date, note FROM mood_entries WHERE date = ?",
            (date_str,),
        ).fetchall()
    return [dict(row) for row in rows]


def get_recent_mood_entries(limit: int) -> List[Dict[str, Any]]:
    if limit <= 0:
        return []
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT mood, time, date, note FROM mood_entries ORDER BY id DESC LIMIT ?",
            (int(limit),),
        ).fetchall()
    return [dict(row) for row in rows]


def get_all_mood_entries() -> List[Dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT mood, time, date, note FROM mood_entries ORDER BY id ASC"
        ).fetchall()
    return [dict(row) for row in rows]


# Notifications

def log_notification(event_type: str, message: str, urgency: str, channels: str) -> None:
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO notifications (event_type, message, urgency, channels, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (event_type, message, urgency, channels, datetime.now().isoformat(timespec="seconds")),
        )


def list_notifications(limit: int = 50) -> List[Dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT event_type, message, urgency, channels, created_at "
            "FROM notifications ORDER BY id DESC LIMIT ?",
            (int(limit),),
        ).fetchall()
    return [dict(row) for row in rows]


# Achievements

def list_unlocked_achievements() -> List[str]:
    with get_conn() as conn:
        rows = conn.execute("SELECT name FROM achievements ORDER BY unlocked_at ASC").fetchall()
    return [row["name"] for row in rows]


def unlock_achievement(name: str) -> bool:
    with get_conn() as conn:
        row = conn.execute("SELECT name FROM achievements WHERE name = ?", (name,)).fetchone()
        if row is not None:
            return False
        conn.execute(
            "INSERT INTO achievements (name, unlocked_at) VALUES (?, ?)",
            (name, datetime.now().isoformat(timespec="seconds")),
        )
    return True


# Social

def list_friends(include_blocked: bool) -> List[Dict[str, Any]]:
    with get_conn() as conn:
        if include_blocked:
            rows = conn.execute(
                "SELECT username, display_name, blocked, added_at FROM social_friends ORDER BY username"
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT username, display_name, blocked, added_at FROM social_friends "
                "WHERE blocked = 0 ORDER BY username"
            ).fetchall()
    return [dict(row) for row in rows]


def upsert_friend(username: str, display_name: Optional[str]) -> None:
    with get_conn() as conn:
        existing = conn.execute(
            "SELECT username FROM social_friends WHERE username = ?",
            (username,),
        ).fetchone()
        if existing is None:
            conn.execute(
                "INSERT INTO social_friends (username, display_name, blocked, added_at) "
                "VALUES (?, ?, ?, ?)",
                (username, display_name, 0, datetime.now().isoformat(timespec="seconds")),
            )
        else:
            conn.execute(
                "UPDATE social_friends SET display_name = ? WHERE username = ?",
                (display_name, username),
            )


def set_friend_blocked(username: str, blocked: bool) -> bool:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT username FROM social_friends WHERE username = ?",
            (username,),
        ).fetchone()
        if row is None:
            return False
        conn.execute(
            "UPDATE social_friends SET blocked = ? WHERE username = ?",
            (1 if blocked else 0, username),
        )
    return True


def create_group(name: str, is_private: bool, owner: str) -> int:
    now = datetime.now().isoformat(timespec="seconds")
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO social_groups (name, is_private, created_at) VALUES (?, ?, ?)",
            (name, 1 if is_private else 0, now),
        )
        group_id = int(cur.lastrowid)
        conn.execute(
            "INSERT INTO social_group_members (group_id, username, role, joined_at) "
            "VALUES (?, ?, ?, ?)",
            (group_id, owner, "owner", now),
        )
    return group_id


def list_groups() -> List[Dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, name, is_private, created_at FROM social_groups ORDER BY created_at DESC"
        ).fetchall()
    return [dict(row) for row in rows]


def add_group_member(group_id: int, username: str, role: str) -> bool:
    with get_conn() as conn:
        exists = conn.execute(
            "SELECT id FROM social_group_members WHERE group_id = ? AND username = ?",
            (group_id, username),
        ).fetchone()
        if exists is not None:
            return True
        conn.execute(
            "INSERT INTO social_group_members (group_id, username, role, joined_at) "
            "VALUES (?, ?, ?, ?)",
            (group_id, username, role, datetime.now().isoformat(timespec="seconds")),
        )
    return True


def add_group_message(group_id: int, sender: str, content: str) -> None:
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO social_group_messages (group_id, sender, content, created_at) "
            "VALUES (?, ?, ?, ?)",
            (group_id, sender, content, datetime.now().isoformat(timespec="seconds")),
        )


def list_group_messages(group_id: int, limit: int) -> List[Dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT sender, content, created_at FROM social_group_messages "
            "WHERE group_id = ? ORDER BY id DESC LIMIT ?",
            (group_id, int(limit)),
        ).fetchall()
    messages = [dict(row) for row in rows]
    return list(reversed(messages))


def create_challenge(
    title: str,
    challenge_type: str,
    participants: List[str],
    duration_days: int,
    group_id: Optional[int],
    anonymous: bool,
) -> int:
    start_date = datetime.now().date()
    end_date = start_date.fromordinal(start_date.toordinal() + int(duration_days))
    now = datetime.now().isoformat(timespec="seconds")
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO social_challenges "
            "(title, challenge_type, group_id, start_date, end_date, status, is_anonymous, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                title,
                challenge_type,
                group_id,
                str(start_date),
                str(end_date),
                "active",
                1 if anonymous else 0,
                now,
            ),
        )
        challenge_id = int(cur.lastrowid)
        for username in participants:
            conn.execute(
                "INSERT INTO social_challenge_participants "
                "(challenge_id, username, score, completed, last_updated) "
                "VALUES (?, ?, ?, ?, ?)",
                (challenge_id, username, 0, 0, now),
            )
    return challenge_id


def list_challenges() -> List[Dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, title, challenge_type, group_id, start_date, end_date, status, is_anonymous, created_at "
            "FROM social_challenges ORDER BY created_at DESC"
        ).fetchall()
    return [dict(row) for row in rows]


def update_challenge_score(challenge_id: int, username: str, score: int) -> bool:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT id FROM social_challenge_participants WHERE challenge_id = ? AND username = ?",
            (challenge_id, username),
        ).fetchone()
        if row is None:
            return False
        conn.execute(
            "UPDATE social_challenge_participants SET score = ?, last_updated = ? "
            "WHERE challenge_id = ? AND username = ?",
            (score, datetime.now().isoformat(timespec="seconds"), challenge_id, username),
        )
    return True


def close_challenge(challenge_id: int) -> bool:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT id FROM social_challenges WHERE id = ?",
            (challenge_id,),
        ).fetchone()
        if row is None:
            return False
        conn.execute(
            "UPDATE social_challenges SET status = ? WHERE id = ?",
            ("closed", challenge_id),
        )
    return True


def get_leaderboard(challenge_id: int, top_n: int) -> List[Tuple[str, int]]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT username, score FROM social_challenge_participants "
            "WHERE challenge_id = ? ORDER BY score DESC, username ASC LIMIT ?",
            (challenge_id, int(top_n)),
        ).fetchall()
    return [(row["username"], row["score"]) for row in rows]


def create_share(achievement_id: str, message: str, audience: str, targets: List[str]) -> int:
    now = datetime.now().isoformat(timespec="seconds")
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO social_shares (achievement_id, message, audience, targets, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (achievement_id, message, audience, json.dumps(targets), now),
        )
    return int(cur.lastrowid)


# Admin

def reset_all() -> None:
    with get_conn() as conn:
        conn.executescript(
            """
            DELETE FROM usage_entries;
            DELETE FROM mood_entries;
            DELETE FROM notifications;
            DELETE FROM achievements;
            DELETE FROM social_friends;
            DELETE FROM social_groups;
            DELETE FROM social_group_members;
            DELETE FROM social_group_messages;
            DELETE FROM social_challenges;
            DELETE FROM social_challenge_participants;
            DELETE FROM social_shares;
            """
        )
    ensure_default_settings()
