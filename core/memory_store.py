from datetime import datetime

USAGE_ENTRIES = []
NOTIFICATIONS = []
MOOD_ENTRIES = []

DEFAULT_PRIVACY = {
    "share_achievements": "1",
    "share_stats": "1",
    "anonymous_leaderboards": "0",
    "local_username": "you"
}

SOCIAL = {
    "friends": {},
    "groups": {},
    "group_members": [],
    "group_messages": [],
    "challenges": {},
    "challenge_participants": [],
    "shares": [],
    "privacy": dict(DEFAULT_PRIVACY),
    "counters": {
        "group_id": 1,
        "message_id": 1,
        "challenge_id": 1,
        "participant_id": 1,
        "share_id": 1
    }
}


def add_usage(app, duration, date_str=None):
    if not app or duration is None:
        return False
    if date_str is None:
        date_str = str(datetime.now().date())
    USAGE_ENTRIES.append({
        "app": app,
        "duration": int(duration),
        "date": date_str
    })
    return True


def get_usage_for_date(date_str):
    return [entry for entry in USAGE_ENTRIES if entry["date"] == date_str]


def log_notification(event_type, message, urgency, channels):
    NOTIFICATIONS.append({
        "event_type": event_type,
        "message": message,
        "urgency": urgency,
        "channels": channels,
        "created_at": datetime.now().isoformat(timespec="seconds")
    })
    return True


def add_mood_entry(mood_score, timestamp=None, note=""):
    if mood_score is None:
        return False
    if timestamp is None:
        timestamp = datetime.now()
    try:
        mood_value = int(mood_score)
    except (TypeError, ValueError):
        return False
    mood_value = max(1, min(10, mood_value))
    MOOD_ENTRIES.append({
        "mood": mood_value,
        "time": timestamp.isoformat(timespec="seconds"),
        "date": str(timestamp.date()),
        "note": note or ""
    })
    return True


def get_mood_entries():
    return list(MOOD_ENTRIES)


def get_mood_entries_for_date(date_str):
    return [entry for entry in MOOD_ENTRIES if entry["date"] == date_str]


def get_recent_mood_entries(limit=10):
    if limit <= 0:
        return []
    return MOOD_ENTRIES[-limit:]


def reset_all():
    USAGE_ENTRIES.clear()
    NOTIFICATIONS.clear()
    MOOD_ENTRIES.clear()

    SOCIAL["friends"].clear()
    SOCIAL["groups"].clear()
    SOCIAL["group_members"].clear()
    SOCIAL["group_messages"].clear()
    SOCIAL["challenges"].clear()
    SOCIAL["challenge_participants"].clear()
    SOCIAL["shares"].clear()

    SOCIAL["privacy"].clear()
    SOCIAL["privacy"].update(DEFAULT_PRIVACY)

    SOCIAL["counters"]["group_id"] = 1
    SOCIAL["counters"]["message_id"] = 1
    SOCIAL["counters"]["challenge_id"] = 1
    SOCIAL["counters"]["participant_id"] = 1
    SOCIAL["counters"]["share_id"] = 1
    return True
