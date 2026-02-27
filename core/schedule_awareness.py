from datetime import datetime, timedelta

class ScheduleAwarenessEngine:
    def __init__(self, calendar_client, base_daily_limit_hours, exam_mode=False):
        self.calendar_client = calendar_client
        self.base_daily_limit_hours = base_daily_limit_hours
        self.exam_mode = exam_mode

    def _parse_event_time(self, value):
        if "T" in value:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        return datetime.fromisoformat(value + "T00:00:00")

    def get_busy_hours(self, events):
        total = 0.0
        for event in events:
            start = event.get("start", {})
            end = event.get("end", {})
            start_value = start.get("dateTime") or start.get("date")
            end_value = end.get("dateTime") or end.get("date")
            if not start_value or not end_value:
                continue
            start_dt = self._parse_event_time(start_value)
            end_dt = self._parse_event_time(end_value)
            delta = (end_dt - start_dt).total_seconds() / 3600.0
            total += max(0.0, delta)
        return min(24.0, total)

    def suggest_limit(self, date):
        events = self.calendar_client.get_events_for_day(date)
        busy_hours = self.get_busy_hours(events)

        if busy_hours >= 6:
            limit = self.base_daily_limit_hours * 0.7
        elif busy_hours >= 3:
            limit = self.base_daily_limit_hours * 0.85
        else:
            limit = self.base_daily_limit_hours

        if self.exam_mode:
            limit *= 0.6

        return max(1.0, round(limit, 1)), busy_hours, len(events)

    def detect_free_time(self, date):
        events = self.calendar_client.get_events_for_day(date)
        intervals = []
        for event in events:
            start = event.get("start", {})
            end = event.get("end", {})
            start_value = start.get("dateTime") or start.get("date")
            end_value = end.get("dateTime") or end.get("date")
            if not start_value or not end_value:
                continue
            start_dt = self._parse_event_time(start_value)
            end_dt = self._parse_event_time(end_value)
            intervals.append((start_dt, end_dt))

        if not intervals:
            return [("00:00", "24:00")]

        intervals.sort(key=lambda x: x[0])
        free_blocks = []
        day_start = datetime(date.year, date.month, date.day)
        day_end = day_start + timedelta(days=1)

        current = day_start
        for start_dt, end_dt in intervals:
            if start_dt > current:
                free_blocks.append((current, start_dt))
            current = max(current, end_dt)
        if current < day_end:
            free_blocks.append((current, day_end))

        return [(b[0].strftime("%H:%M"), b[1].strftime("%H:%M")) for b in free_blocks]
