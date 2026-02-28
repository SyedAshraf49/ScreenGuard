from __future__ import annotations

import json
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from core.calendar_integration import GoogleCalendarClient
from core.schedule_awareness import ScheduleAwarenessEngine
from core.active_window import get_active_app_name
from core.app_locker import make_locker

from backend.db import (
    add_group_member,
    add_group_message,
    add_mood_entry,
    add_usage,
    create_challenge,
    create_group,
    create_share,
    get_all_mood_entries,
    get_mood_entries_for_date,
    get_recent_mood_entries,
    get_setting,
    get_usage_for_date,
    get_usage_in_range,
    init_db,
    list_challenges,
    list_friends,
    list_group_messages,
    list_groups,
    list_notifications,
    list_unlocked_achievements,
    log_notification,
    reset_all,
    set_friend_blocked,
    set_setting,
    unlock_achievement,
    update_challenge_score,
    close_challenge,
    get_leaderboard,
    upsert_friend,
    # Locker
    set_app_limit,
    get_app_limit,
    list_app_limits,
    list_available_apps,
    remove_app_limit,
    lock_app,
    unlock_app,
    list_locked_apps,
    is_app_locked,
)

APP_DIR = Path(__file__).resolve().parent
WEB_DIR = APP_DIR.parent / "web"

STUDY_APPS = ["Code", "VSCode", "PyCharm", "Word", "Excel", "PowerPoint"]
DISTRACTION_APPS = ["Chrome", "YouTube", "Netflix", "Instagram"]

ACHIEVEMENT_CATALOG = {
    "Disciplined Day": {"points": 50, "desc": "Stay under daily limit"},
    "Focus Master": {"points": 100, "desc": "Complete 5 focus sessions"},
    "First Week": {"points": 150, "desc": "Track for 7 consecutive days"},
    "Under Budget": {"points": 200, "desc": "Stay under limit 5 days in a row"},
    "Focus Warrior": {"points": 250, "desc": "Complete 20 focus sessions"},
    "Early Bird": {"points": 200, "desc": "No screen time before 8 AM for a week"},
    "Weekend Warrior": {"points": 200, "desc": "Reduce weekend usage by 30%"},
    "Digital Detox": {"points": 300, "desc": "One full day with no screen time"},
}
LEVEL_THRESHOLDS = [0, 200, 500, 900, 1400, 2000]

URGENCY_RANK = {"low": 0, "medium": 1, "high": 2, "critical": 3}


app = FastAPI(title="ScreenGuard Web")
locker_engine = None

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"] ,
    allow_headers=["*"],
)


class UsageEntryIn(BaseModel):
    app: str
    duration: int = Field(ge=1, le=1440)
    date: Optional[str] = None


class MoodEntryIn(BaseModel):
    mood: int = Field(ge=1, le=10)
    note: Optional[str] = ""
    timestamp: Optional[str] = None


class AutoMoodIn(BaseModel):
    note: Optional[str] = ""


class NotificationPrefsIn(BaseModel):
    channels: List[str]
    min_urgency: str
    quiet_start: int = Field(ge=0, le=23)
    quiet_end: int = Field(ge=0, le=23)
    dnd: bool


class LimitSettingsIn(BaseModel):
    daily_hours: int = Field(ge=1, le=24)


class ThemeIn(BaseModel):
    theme: str


class CalendarSyncIn(BaseModel):
    credentials_path: str
    calendar_id: str = "primary"
    base_daily_limit_hours: int = Field(ge=1, le=24)
    exam_mode: bool = False


class FriendIn(BaseModel):
    username: str
    display_name: Optional[str] = None


class FriendBlockIn(BaseModel):
    username: str
    blocked: bool


class GroupIn(BaseModel):
    name: str
    is_private: bool = True


class GroupMemberIn(BaseModel):
    group_id: int
    username: str
    role: str = "member"


class GroupMessageIn(BaseModel):
    group_id: int
    sender: Optional[str] = None
    content: str


class ChallengeIn(BaseModel):
    title: str
    challenge_type: str
    participants: List[str]
    duration_days: int = Field(ge=1, le=60)
    group_id: Optional[int] = None
    anonymous: bool = False


class ChallengeScoreIn(BaseModel):
    challenge_id: int
    username: str
    score: int


class ChallengeCloseIn(BaseModel):
    challenge_id: int


class ShareIn(BaseModel):
    achievement_id: str
    message: Optional[str] = ""
    audience: str = "friends"
    targets: List[str] = []


class PrivacyIn(BaseModel):
    share_achievements: bool
    share_stats: bool
    anonymous_leaderboards: bool
    local_username: str


class SummaryIn(BaseModel):
    limit: int


class AppLimitIn(BaseModel):
    app: str
    daily_minutes: int = Field(ge=1, le=1440)


class AppUnlockIn(BaseModel):
    app: str


class AppRemoveIn(BaseModel):
    app: str


@app.on_event("startup")
def on_startup() -> None:
    init_db()
    global locker_engine
    locker_engine = make_locker(on_locked_fn=lambda app_name: _send_notification(
        f"{app_name} is locked — time limit reached.",
        "high",
    ))
    locker_engine.start()


@app.on_event("shutdown")
def on_shutdown() -> None:
    global locker_engine
    if locker_engine is not None:
        locker_engine.stop()
        locker_engine = None


def _get_notification_prefs() -> Dict[str, object]:
    channels_json = get_setting("notifications.channels", "[]") or "[]"
    try:
        channels = json.loads(channels_json)
    except json.JSONDecodeError:
        channels = []
    return {
        "channels": channels,
        "min_urgency": get_setting("notifications.min_urgency", "low"),
        "quiet_start": int(get_setting("notifications.quiet_start", "22") or 22),
        "quiet_end": int(get_setting("notifications.quiet_end", "7") or 7),
        "dnd": (get_setting("notifications.dnd", "0") == "1"),
    }


def _is_quiet_hours(prefs: Dict[str, object]) -> bool:
    if prefs.get("dnd"):
        return True
    now_hour = datetime.now().hour
    start = int(prefs.get("quiet_start", 22))
    end = int(prefs.get("quiet_end", 7))
    if start == end:
        return False
    if start < end:
        return start <= now_hour < end
    return now_hour >= start or now_hour < end


def _send_notification(message: str, urgency: str, channels: Optional[List[str]] = None) -> bool:
    prefs = _get_notification_prefs()
    if _is_quiet_hours(prefs):
        return False
    min_urgency = prefs.get("min_urgency", "low")
    if URGENCY_RANK.get(urgency, 0) < URGENCY_RANK.get(min_urgency, 0):
        return False
    active = channels or prefs.get("channels", [])
    log_notification("custom", message, urgency, ",".join(active))
    return True


def _get_daily_limit_minutes() -> int:
    daily_hours = int(get_setting("limits.daily_hours", "6") or 6)
    return daily_hours * 60


def _get_recommendations(day: date) -> List[str]:
    usage_entries = get_usage_for_date(str(day))
    aggregates: Dict[str, int] = {}
    for entry in usage_entries:
        aggregates[entry["app"]] = aggregates.get(entry["app"], 0) + int(entry["duration"])
    data = list(aggregates.items())

    total = sum(minutes for _, minutes in data)
    rec: List[str] = []

    yesterday = day - timedelta(days=1)
    yesterday_entries = get_usage_for_date(str(yesterday))
    yesterday_total = sum(entry["duration"] for entry in yesterday_entries)

    if total >= 480:
        rec.append("Very high screen usage today. Plan a low-screen evening to recover.")
    elif total > 360:
        rec.append("High screen usage detected. Consider staying under 6 hours.")
    elif total < 60:
        rec.append("Light screen usage so far. Maintain this balance through the day.")

    if datetime.now().hour >= 23:
        rec.append("Late usage detected. Avoid screens after 11 PM for better sleep.")

    distraction = sum(
        minutes for app, minutes in data if any(name in app for name in DISTRACTION_APPS)
    )
    study = sum(
        minutes for app, minutes in data if any(name in app for name in STUDY_APPS)
    )

    if distraction > study:
        rec.append("Distraction apps dominate usage. Plan focused sessions.")
    elif study >= 120:
        rec.append("Productive app usage is strong today. Keep consistent focus blocks.")

    if total > 120:
        rec.append("Take a short break every hour to reduce eye strain.")

    if data:
        top_app, top_minutes = max(data, key=lambda item: item[1])
        if top_minutes >= max(90, int(total * 0.5)):
            rec.append(f"{top_app} dominates today's usage. Consider an app-specific limit.")

    if len(usage_entries) >= 25:
        rec.append("Usage is fragmented across many sessions. Try 25-minute focus blocks.")

    if yesterday_total > 0:
        diff = total - yesterday_total
        if diff >= 120:
            rec.append("You are up more than 2 hours vs yesterday. Add a cooldown break.")
        elif diff <= -120:
            rec.append("Great improvement versus yesterday. Keep the same routine.")

    if not rec:
        rec.append("Healthy digital habits detected.")

    return rec[:8]


def _get_daily_pairs(lookback_days: int) -> List[tuple]:
    today = datetime.now().date()
    pairs = []
    for offset in range(lookback_days):
        day = today - timedelta(days=offset)
        mood_entries = get_mood_entries_for_date(str(day))
        if not mood_entries:
            continue
        mood_avg = sum(entry["mood"] for entry in mood_entries) / len(mood_entries)
        usage_entries = get_usage_for_date(str(day))
        screen_minutes = sum(entry["duration"] for entry in usage_entries)
        pairs.append((screen_minutes, mood_avg, day))
    return pairs


def _pearson_correlation(xs: List[float], ys: List[float]) -> Optional[float]:
    n = len(xs)
    if n < 2:
        return None
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    num = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    den_x = sum((x - mean_x) ** 2 for x in xs)
    den_y = sum((y - mean_y) ** 2 for y in ys)
    if den_x == 0 or den_y == 0:
        return None
    return num / ((den_x ** 0.5) * (den_y ** 0.5))


def _get_trend_summary(lookback_days: int = 7) -> Dict[str, Optional[float]]:
    today = datetime.now().date()
    recent_days = [today - timedelta(days=i) for i in range(lookback_days)]
    prev_days = [today - timedelta(days=lookback_days + i) for i in range(lookback_days)]

    def day_avg(day: date) -> Optional[float]:
        entries = get_mood_entries_for_date(str(day))
        if not entries:
            return None
        return sum(entry["mood"] for entry in entries) / len(entries)

    recent_values = [day_avg(day) for day in recent_days]
    prev_values = [day_avg(day) for day in prev_days]

    recent_values = [val for val in recent_values if val is not None]
    prev_values = [val for val in prev_values if val is not None]

    if not recent_values:
        return {"average": None, "trend": None}

    recent_avg = sum(recent_values) / len(recent_values)
    prev_avg = sum(prev_values) / len(prev_values) if prev_values else None

    trend = None
    if prev_avg is not None:
        if recent_avg > prev_avg + 0.2:
            trend = "up"
        elif recent_avg < prev_avg - 0.2:
            trend = "down"
        else:
            trend = "flat"

    return {"average": recent_avg, "trend": trend}


def _analyze_correlations(lookback_days: int = 14, high_screen_threshold_minutes: int = 480) -> Dict[str, Optional[float]]:
    pairs = _get_daily_pairs(lookback_days)
    if len(pairs) < 2:
        return {"pair_count": len(pairs), "correlation": None, "high_avg": None, "low_avg": None}

    high_moods = [mood for minutes, mood, _ in pairs if minutes >= high_screen_threshold_minutes]
    low_moods = [mood for minutes, mood, _ in pairs if minutes < high_screen_threshold_minutes]
    high_avg = sum(high_moods) / len(high_moods) if high_moods else None
    low_avg = sum(low_moods) / len(low_moods) if low_moods else None

    xs = [minutes for minutes, _, _ in pairs]
    ys = [mood for _, mood, _ in pairs]
    corr = _pearson_correlation(xs, ys)

    return {"pair_count": len(pairs), "correlation": corr, "high_avg": high_avg, "low_avg": low_avg}


def _detect_patterns(lookback_days: int = 14) -> List[str]:
    patterns: List[str] = []
    pairs = _get_daily_pairs(lookback_days)
    if not pairs:
        return patterns

    low_mood_days = [day for minutes, mood, day in pairs if mood <= 3]
    if len(low_mood_days) >= 3:
        patterns.append("Low mood reported on 3+ days in the last two weeks.")

    high_screen_low_mood = [day for minutes, mood, day in pairs if minutes >= 480 and mood <= 4]
    if high_screen_low_mood:
        patterns.append("High screen time often aligns with lower mood.")

    recent = _get_trend_summary()
    if recent.get("trend") == "down":
        patterns.append("Mood trend is down compared to the previous week.")

    return patterns


def _get_wellbeing_recommendations() -> List[str]:
    recommendations: List[str] = []
    today = datetime.now().date()
    today_entries = get_mood_entries_for_date(str(today))
    if today_entries:
        today_avg = sum(entry["mood"] for entry in today_entries) / len(today_entries)
    else:
        today_avg = None

    if today_avg is not None and today_avg <= 4:
        recommendations.append("Consider a short break or a quick walk to reset.")
        recommendations.append("Try a 2-minute breathing exercise or mindfulness check-in.")

    correlation = _analyze_correlations()
    if correlation.get("high_avg") is not None and correlation.get("low_avg") is not None:
        if correlation["high_avg"] + 0.4 < correlation["low_avg"]:
            recommendations.append("On high screen-time days, your mood trends lower. Plan earlier breaks.")

    patterns = _detect_patterns()
    if patterns:
        recommendations.append("Consider scheduling a lower-screen evening if this pattern continues.")

    if not recommendations:
        recommendations.append("Keep up the steady routine and check in daily.")

    return recommendations


def _get_points_level() -> Dict[str, int]:
    points = int(get_setting("achievements.points", "0") or 0)
    level = int(get_setting("achievements.level", "1") or 1)
    return {"points": points, "level": level}


def _set_points_level(points: int, level: int) -> None:
    set_setting("achievements.points", str(points))
    set_setting("achievements.level", str(level))


def _update_level(points: int) -> int:
    level = 1
    for idx, threshold in enumerate(LEVEL_THRESHOLDS):
        if points >= threshold:
            level = idx + 1
    return level


def _get_progress_to_next_level(points: int, level: int) -> float:
    if level >= len(LEVEL_THRESHOLDS):
        return 1.0
    current = LEVEL_THRESHOLDS[level - 1]
    next_level = LEVEL_THRESHOLDS[level]
    if next_level == current:
        return 1.0
    return min(1.0, (points - current) / (next_level - current))


def _check_achievements() -> None:
    today = datetime.now().date()
    usage_entries = get_usage_for_date(str(today))
    total_minutes = sum(entry["duration"] for entry in usage_entries)
    usage_data = {
        "stayed_under_limit": total_minutes > 0 and total_minutes <= _get_daily_limit_minutes(),
        "focus_sessions": 0,
        "consecutive_days": 0,
        "under_budget_streak": 0,
        "early_bird_week": False,
        "weekend_reduction": False,
        "digital_detox_day": total_minutes == 0,
    }

    points_state = _get_points_level()
    points = points_state["points"]

    def award(name: str) -> None:
        nonlocal points
        if unlock_achievement(name):
            points += ACHIEVEMENT_CATALOG[name]["points"]

    if usage_data.get("stayed_under_limit"):
        award("Disciplined Day")
    if usage_data.get("focus_sessions", 0) >= 5:
        award("Focus Master")
    if usage_data.get("consecutive_days", 0) >= 7:
        award("First Week")
    if usage_data.get("under_budget_streak", 0) >= 5:
        award("Under Budget")
    if usage_data.get("focus_sessions", 0) >= 20:
        award("Focus Warrior")
    if usage_data.get("early_bird_week"):
        award("Early Bird")
    if usage_data.get("weekend_reduction"):
        award("Weekend Warrior")
    if usage_data.get("digital_detox_day"):
        award("Digital Detox")

    level = _update_level(points)
    _set_points_level(points, level)


@app.get("/api/recommendations")
def api_recommendations() -> Dict[str, List[str]]:
    return {"items": _get_recommendations(datetime.now().date())}


@app.post("/api/usage")
def api_add_usage(entry: UsageEntryIn) -> Dict[str, object]:
    app_name = entry.app.strip() or get_active_app_name().strip()
    if not app_name:
        raise HTTPException(status_code=400, detail="Could not detect active app.")
    entry_date = entry.date or str(datetime.now().date())
    add_usage(app_name, entry.duration, entry_date)

    total_minutes = sum(e["duration"] for e in get_usage_for_date(entry_date))
    if total_minutes > _get_daily_limit_minutes():
        _send_notification("Daily limit exceeded.", "high")

    # Auto-lock check: if the app has an individual limit, enforce it
    app_limit = get_app_limit(app_name)
    if app_limit is not None:
        app_total = sum(
            e["duration"] for e in get_usage_for_date(entry_date) if e["app"] == app_name
        )
        if app_total >= app_limit and not is_app_locked(app_name):
            lock_app(app_name, "limit_exceeded")
            _send_notification(
                f"{app_name} locked: daily limit of {app_limit} min reached.",
                "high",
            )

    return {"ok": True}


@app.get("/api/usage/current-app")
def api_get_current_app() -> Dict[str, str]:
    return {"app": get_active_app_name()}


@app.get("/api/usage")
def api_get_usage(date_str: str) -> Dict[str, List[Dict[str, object]]]:
    return {"items": get_usage_for_date(date_str)}


@app.get("/api/reports/weekly")
def api_weekly_reports() -> Dict[str, List[Dict[str, object]]]:
    today = datetime.now().date()
    rows: List[Dict[str, object]] = []
    for offset in range(7):
        day = today - timedelta(days=offset)
        usage_entries = get_usage_for_date(str(day))
        total_minutes = sum(entry["duration"] for entry in usage_entries)
        mood_entries = get_mood_entries_for_date(str(day))
        mood_avg = None
        if mood_entries:
            mood_avg = sum(entry["mood"] for entry in mood_entries) / len(mood_entries)
        rows.append({"date": str(day), "total_minutes": total_minutes, "mood_avg": mood_avg})
    return {"items": rows}


@app.post("/api/mood")
def api_add_mood(entry: MoodEntryIn) -> Dict[str, object]:
    try:
        timestamp = (
            datetime.fromisoformat(entry.timestamp)
            if entry.timestamp
            else datetime.now()
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid timestamp.") from exc

    add_mood_entry(entry.mood, timestamp, entry.note or "")
    return {"ok": True}


def _estimate_auto_mood(day: date) -> int:
    usage_entries = get_usage_for_date(str(day))
    screen_minutes = sum(entry["duration"] for entry in usage_entries)
    if screen_minutes <= 120:
        mood = 8
    elif screen_minutes <= 240:
        mood = 7
    elif screen_minutes <= 360:
        mood = 6
    elif screen_minutes <= 480:
        mood = 5
    else:
        mood = 4
    if datetime.now().hour >= 23:
        mood -= 1
    return max(1, min(10, mood))


@app.post("/api/mood/auto")
def api_auto_mood(entry: AutoMoodIn) -> Dict[str, object]:
    now = datetime.now()
    recent = get_recent_mood_entries(1)
    if recent:
        latest = recent[0]
        latest_note = (latest.get("note") or "").lower()
        latest_time_raw = latest.get("time")
        if latest_time_raw:
            latest_time = datetime.fromisoformat(latest_time_raw)
            if "auto check-in" in latest_note and (now - latest_time).total_seconds() < 50 * 60:
                return {"ok": True, "created": False}

    mood_score = _estimate_auto_mood(now.date())
    note = (entry.note or "").strip() or "Auto check-in based on screen-time pattern"
    add_mood_entry(mood_score, now, note)
    return {"ok": True, "created": True, "mood": mood_score}


@app.get("/api/mood/recent")
def api_recent_mood(limit: int = 8) -> Dict[str, List[Dict[str, object]]]:
    return {"items": get_recent_mood_entries(limit)}


@app.get("/api/wellbeing/insights")
def api_wellbeing_insights() -> Dict[str, object]:
    trend = _get_trend_summary()
    correlation = _analyze_correlations()
    patterns = _detect_patterns()
    recommendations = _get_wellbeing_recommendations()
    return {
        "trend": trend,
        "correlation": correlation,
        "patterns": patterns,
        "recommendations": recommendations,
    }


@app.get("/api/wellbeing/summary")
def api_wellbeing_summary() -> Dict[str, List[str]]:
    trend = _get_trend_summary()
    correlation = _analyze_correlations()
    lines: List[str] = []
    if trend.get("average") is not None:
        lines.append(f"7-day average mood: {trend['average']:.1f}")
    if correlation.get("correlation") is not None:
        lines.append(f"Mood vs screen time correlation: {correlation['correlation']:.2f}")
    if not lines:
        lines.append("Not enough data for summary yet.")
    return {"lines": lines}


@app.get("/api/achievements/status")
def api_achievements_status() -> Dict[str, object]:
    _check_achievements()
    unlocked = list_unlocked_achievements()
    pending = [
        f"{name} - {info['desc']}"
        for name, info in ACHIEVEMENT_CATALOG.items()
        if name not in unlocked
    ]
    points_state = _get_points_level()
    points = points_state["points"]
    level = points_state["level"]
    return {
        "level": level,
        "points": points,
        "progress": _get_progress_to_next_level(points, level),
        "unlocked": unlocked,
        "pending": pending,
    }


@app.get("/api/settings/notifications")
def api_get_notification_settings() -> Dict[str, object]:
    return _get_notification_prefs()


@app.post("/api/settings/notifications")
def api_set_notification_settings(prefs: NotificationPrefsIn) -> Dict[str, object]:
    set_setting("notifications.channels", json.dumps(prefs.channels))
    set_setting("notifications.min_urgency", prefs.min_urgency)
    set_setting("notifications.quiet_start", str(prefs.quiet_start))
    set_setting("notifications.quiet_end", str(prefs.quiet_end))
    set_setting("notifications.dnd", "1" if prefs.dnd else "0")
    return {"ok": True}


@app.get("/api/settings/limits")
def api_get_limits() -> Dict[str, object]:
    return {"daily_hours": int(get_setting("limits.daily_hours", "6") or 6)}


@app.post("/api/settings/limits")
def api_set_limits(settings_in: LimitSettingsIn) -> Dict[str, object]:
    set_setting("limits.daily_hours", str(settings_in.daily_hours))
    return {"ok": True}


@app.get("/api/settings/theme")
def api_get_theme() -> Dict[str, str]:
    return {"theme": get_setting("theme.name", "night") or "night"}


@app.post("/api/settings/theme")
def api_set_theme(theme_in: ThemeIn) -> Dict[str, object]:
    theme = (theme_in.theme or "night").strip().lower()
    if theme not in ["day", "night", "aurora", "sunset", "mono"]:
        theme = "night"
    set_setting("theme.name", theme)
    return {"ok": True, "theme": theme}


@app.post("/api/calendar/sync")
def api_calendar_sync(payload: CalendarSyncIn) -> Dict[str, object]:
    try:
        client = GoogleCalendarClient(payload.credentials_path, calendar_id=payload.calendar_id)
        engine = ScheduleAwarenessEngine(
            client,
            base_daily_limit_hours=payload.base_daily_limit_hours,
            exam_mode=payload.exam_mode,
        )
        suggested_limit, busy_hours, event_count = engine.suggest_limit(date.today())
        return {
            "event_count": event_count,
            "busy_hours": busy_hours,
            "suggested_limit": suggested_limit,
        }
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Sync failed: {exc}") from exc


@app.get("/api/social/friends")
def api_list_friends(include_blocked: bool = True) -> Dict[str, List[Dict[str, object]]]:
    return {"items": list_friends(include_blocked)}


@app.post("/api/social/friends")
def api_add_friend(friend: FriendIn) -> Dict[str, object]:
    if not friend.username.strip():
        raise HTTPException(status_code=400, detail="Username required.")
    upsert_friend(friend.username.strip(), friend.display_name)
    return {"ok": True}


@app.post("/api/social/friends/block")
def api_block_friend(payload: FriendBlockIn) -> Dict[str, object]:
    if not payload.username.strip():
        raise HTTPException(status_code=400, detail="Username required.")
    ok = set_friend_blocked(payload.username.strip(), payload.blocked)
    if not ok:
        raise HTTPException(status_code=404, detail="User not found.")
    return {"ok": True}


@app.get("/api/social/groups")
def api_list_groups() -> Dict[str, List[Dict[str, object]]]:
    return {"items": list_groups()}


@app.post("/api/social/groups")
def api_create_group(group: GroupIn) -> Dict[str, object]:
    if not group.name.strip():
        raise HTTPException(status_code=400, detail="Group name required.")
    owner = get_setting("social.local_username", "you") or "you"
    group_id = create_group(group.name.strip(), group.is_private, owner)
    return {"ok": True, "id": group_id}


@app.post("/api/social/groups/members")
def api_add_group_member(payload: GroupMemberIn) -> Dict[str, object]:
    ok = add_group_member(payload.group_id, payload.username.strip(), payload.role)
    if not ok:
        raise HTTPException(status_code=400, detail="Unable to add member.")
    return {"ok": True}


@app.get("/api/social/groups/messages")
def api_list_group_messages(group_id: int, limit: int = 20) -> Dict[str, List[Dict[str, object]]]:
    return {"items": list_group_messages(group_id, limit)}


@app.post("/api/social/groups/messages")
def api_add_group_message(payload: GroupMessageIn) -> Dict[str, object]:
    sender = payload.sender or (get_setting("social.local_username", "you") or "you")
    if not payload.content.strip():
        raise HTTPException(status_code=400, detail="Message required.")
    add_group_message(payload.group_id, sender, payload.content.strip())
    return {"ok": True}


@app.get("/api/social/challenges")
def api_list_challenges() -> Dict[str, List[Dict[str, object]]]:
    return {"items": list_challenges()}


@app.post("/api/social/challenges")
def api_create_challenge(payload: ChallengeIn) -> Dict[str, object]:
    if not payload.title.strip():
        raise HTTPException(status_code=400, detail="Title required.")
    participants = [p.strip() for p in payload.participants if p.strip()]
    local = get_setting("social.local_username", "you") or "you"
    if local not in participants:
        participants.append(local)
    challenge_id = create_challenge(
        payload.title.strip(),
        payload.challenge_type,
        participants,
        payload.duration_days,
        payload.group_id,
        payload.anonymous,
    )
    return {"ok": True, "id": challenge_id}


@app.post("/api/social/challenges/score")
def api_update_challenge_score(payload: ChallengeScoreIn) -> Dict[str, object]:
    ok = update_challenge_score(payload.challenge_id, payload.username.strip(), payload.score)
    if not ok:
        raise HTTPException(status_code=404, detail="Participant not found.")
    return {"ok": True}


@app.post("/api/social/challenges/close")
def api_close_challenge(payload: ChallengeCloseIn) -> Dict[str, object]:
    ok = close_challenge(payload.challenge_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Challenge not found.")
    return {"ok": True}


@app.get("/api/social/challenges/leaderboard")
def api_leaderboard(challenge_id: int, top_n: int = 10) -> Dict[str, List[Dict[str, object]]]:
    rows = get_leaderboard(challenge_id, top_n)
    return {"items": [{"username": name, "score": score} for name, score in rows]}


@app.post("/api/social/shares")
def api_share_achievement(payload: ShareIn) -> Dict[str, object]:
    if not payload.achievement_id.strip():
        raise HTTPException(status_code=400, detail="Achievement required.")
    share_id = create_share(
        payload.achievement_id.strip(),
        payload.message or "",
        payload.audience,
        payload.targets,
    )
    return {"ok": True, "id": share_id}


@app.get("/api/social/privacy")
def api_get_privacy() -> Dict[str, object]:
    return {
        "share_achievements": (get_setting("social.share_achievements", "1") == "1"),
        "share_stats": (get_setting("social.share_stats", "1") == "1"),
        "anonymous_leaderboards": (get_setting("social.anonymous_leaderboards", "0") == "1"),
        "local_username": get_setting("social.local_username", "you") or "you",
    }


@app.post("/api/social/privacy")
def api_set_privacy(payload: PrivacyIn) -> Dict[str, object]:
    set_setting("social.share_achievements", "1" if payload.share_achievements else "0")
    set_setting("social.share_stats", "1" if payload.share_stats else "0")
    set_setting("social.anonymous_leaderboards", "1" if payload.anonymous_leaderboards else "0")
    set_setting("social.local_username", payload.local_username.strip() or "you")
    return {"ok": True}


@app.get("/api/notifications")
def api_list_notifications(limit: int = 50) -> Dict[str, List[Dict[str, object]]]:
    return {"items": list_notifications(limit)}


@app.post("/api/admin/reset")
def api_reset() -> Dict[str, object]:
    reset_all()
    return {"ok": True}


# ── App Locker ────────────────────────────────────────────────────────────────

@app.get("/api/locker/limits")
def api_list_locker_limits() -> Dict[str, List[Dict[str, object]]]:
    return {"items": list_app_limits()}


@app.get("/api/locker/apps")
def api_list_locker_apps() -> Dict[str, List[str]]:
    return {"items": list_available_apps()}


@app.post("/api/locker/limits")
def api_set_locker_limit(payload: AppLimitIn) -> Dict[str, object]:
    app_name = payload.app.strip()
    if not app_name:
        raise HTTPException(status_code=400, detail="App name required.")
    set_app_limit(app_name, payload.daily_minutes)
    return {"ok": True}


@app.delete("/api/locker/limits/{app_name}")
def api_remove_locker_limit(app_name: str) -> Dict[str, object]:
    removed = remove_app_limit(app_name)
    if not removed:
        raise HTTPException(status_code=404, detail="Limit not found.")
    return {"ok": True}


@app.post("/api/locker/limits/remove")
def api_remove_locker_limit_post(payload: AppRemoveIn) -> Dict[str, object]:
    app_name = payload.app.strip()
    if not app_name:
        raise HTTPException(status_code=400, detail="App name required.")
    removed = remove_app_limit(app_name)
    if not removed:
        raise HTTPException(status_code=404, detail="Limit not found.")
    return {"ok": True}


@app.get("/api/locker/status")
def api_locker_status() -> Dict[str, object]:
    today = str(datetime.now().date())
    usage_entries = get_usage_for_date(today)
    usage_by_app: Dict[str, int] = {}
    for e in usage_entries:
        usage_by_app[e["app"]] = usage_by_app.get(e["app"], 0) + int(e["duration"])

    locked = {row["app"]: row for row in list_locked_apps()}
    limits = list_app_limits()

    items = []
    for lim in limits:
        app_name = lim["app"]
        used = usage_by_app.get(app_name, 0)
        items.append(
            {
                "app": app_name,
                "daily_minutes": lim["daily_minutes"],
                "used_minutes": used,
                "locked": app_name in locked,
                "locked_at": locked[app_name]["locked_at"] if app_name in locked else None,
                "locked_reason": locked[app_name]["locked_reason"] if app_name in locked else None,
            }
        )

    # Also include apps that are locked but no longer have a limit configured
    for app_name, info in locked.items():
        if not any(i["app"] == app_name for i in items):
            items.append(
                {
                    "app": app_name,
                    "daily_minutes": None,
                    "used_minutes": usage_by_app.get(app_name, 0),
                    "locked": True,
                    "locked_at": info["locked_at"],
                    "locked_reason": info["locked_reason"],
                }
            )

    return {"items": items}


@app.post("/api/locker/unlock")
def api_unlock_app(payload: AppUnlockIn) -> Dict[str, object]:
    app_name = payload.app.strip()
    if not app_name:
        raise HTTPException(status_code=400, detail="App name required.")
    ok = unlock_app(app_name)
    if not ok:
        raise HTTPException(status_code=404, detail="App is not locked.")
    return {"ok": True}


if WEB_DIR.exists():
    app.mount("/", StaticFiles(directory=WEB_DIR, html=True), name="static")
