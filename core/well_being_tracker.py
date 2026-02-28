from datetime import datetime, timedelta
from backend.db import (
    add_mood_entry,
    get_all_mood_entries,
    get_mood_entries_for_date,
    get_recent_mood_entries,
    get_usage_for_date
)


class WellBeingTracker:
    def __init__(self):
        self.mood_data = get_all_mood_entries()

    def log_mood(self, mood_score, timestamp=None, note=""):
        if timestamp is None:
            timestamp = datetime.now()
        try:
            add_mood_entry(mood_score, timestamp=timestamp, note=note)
            self.mood_data = get_all_mood_entries()
            return True
        except Exception:
            return False

    def _estimate_auto_mood(self, timestamp=None):
        if timestamp is None:
            timestamp = datetime.now()
        screen_minutes = self.get_screen_time_minutes(timestamp.date())
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
        if timestamp.hour >= 23:
            mood -= 1
        return max(1, min(10, mood))

    def auto_log_mood_checkin(self, timestamp=None):
        if timestamp is None:
            timestamp = datetime.now()

        recent = get_recent_mood_entries(limit=1)
        if recent:
            latest = recent[-1]
            latest_time = datetime.fromisoformat(latest["time"])
            latest_note = (latest.get("note") or "").lower()
            if "auto check-in" in latest_note and (timestamp - latest_time).total_seconds() < 50 * 60:
                return False

        mood_score = self._estimate_auto_mood(timestamp)
        return self.log_mood(
            mood_score,
            timestamp=timestamp,
            note="Auto check-in based on screen-time pattern"
        )

    def get_daily_mood_average(self, date_value):
        entries = get_mood_entries_for_date(str(date_value))
        if not entries:
            return None
        return sum(entry["mood"] for entry in entries) / len(entries)

    def get_screen_time_minutes(self, date_value):
        usage_entries = get_usage_for_date(str(date_value))
        return sum(entry["duration"] for entry in usage_entries)

    def _get_daily_pairs(self, lookback_days=14):
        today = datetime.now().date()
        pairs = []
        for offset in range(lookback_days):
            day = today - timedelta(days=offset)
            mood_avg = self.get_daily_mood_average(day)
            if mood_avg is None:
                continue
            screen_minutes = self.get_screen_time_minutes(day)
            pairs.append((screen_minutes, mood_avg, day))
        return pairs

    def _pearson_correlation(self, xs, ys):
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
        return num / (den_x ** 0.5 * den_y ** 0.5)

    def analyze_correlations(self, lookback_days=14, high_screen_threshold_minutes=480):
        pairs = self._get_daily_pairs(lookback_days=lookback_days)
        if len(pairs) < 2:
            return {
                "pair_count": len(pairs),
                "correlation": None,
                "high_avg": None,
                "low_avg": None
            }

        high_moods = [mood for minutes, mood, _ in pairs if minutes >= high_screen_threshold_minutes]
        low_moods = [mood for minutes, mood, _ in pairs if minutes < high_screen_threshold_minutes]
        high_avg = sum(high_moods) / len(high_moods) if high_moods else None
        low_avg = sum(low_moods) / len(low_moods) if low_moods else None

        xs = [minutes for minutes, _, _ in pairs]
        ys = [mood for _, mood, _ in pairs]
        corr = self._pearson_correlation(xs, ys)

        return {
            "pair_count": len(pairs),
            "correlation": corr,
            "high_avg": high_avg,
            "low_avg": low_avg
        }

    def detect_patterns(self, lookback_days=14):
        patterns = []
        pairs = self._get_daily_pairs(lookback_days=lookback_days)
        if not pairs:
            return patterns

        low_mood_days = [day for minutes, mood, day in pairs if mood <= 3]
        if len(low_mood_days) >= 3:
            patterns.append("Low mood reported on 3+ days in the last two weeks.")

        high_screen_low_mood = [day for minutes, mood, day in pairs if minutes >= 480 and mood <= 4]
        if high_screen_low_mood:
            patterns.append("High screen time (8h+) often aligns with lower mood.")

        recent = self.get_trend_summary()
        if recent.get("trend") == "down":
            patterns.append("Mood trend is down compared to the previous week.")

        return patterns

    def get_trend_summary(self, lookback_days=7):
        today = datetime.now().date()
        recent_days = [today - timedelta(days=i) for i in range(lookback_days)]
        prev_days = [today - timedelta(days=lookback_days + i) for i in range(lookback_days)]

        recent_values = [self.get_daily_mood_average(day) for day in recent_days]
        prev_values = [self.get_daily_mood_average(day) for day in prev_days]

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

    def get_well_being_recommendations(self):
        recommendations = []
        today = datetime.now().date()
        today_avg = self.get_daily_mood_average(today)

        if today_avg is not None and today_avg <= 4:
            recommendations.append("Consider a short break or a quick walk to reset.")
            recommendations.append("Try a 2-minute breathing exercise or mindfulness check-in.")

        correlation = self.analyze_correlations()
        if correlation.get("high_avg") is not None and correlation.get("low_avg") is not None:
            if correlation["high_avg"] + 0.4 < correlation["low_avg"]:
                recommendations.append("On high screen-time days, your mood trends lower. Plan earlier breaks.")

        patterns = self.detect_patterns()
        if patterns:
            recommendations.append("Consider scheduling a lower-screen evening if this pattern continues.")

        if not recommendations:
            recommendations.append("Keep up the steady routine and check in daily.")

        return recommendations
