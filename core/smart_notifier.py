from datetime import datetime
from core.memory_store import log_notification

class SmartNotifier:
    def __init__(self):
        self.notification_preferences = {
            "channels": ["desktop"],
            "min_urgency": "low",
            "quiet_hours": {"start": 22, "end": 7},
            "do_not_disturb": False
        }
        self.quiet_hours = []

    def set_preferences(self, channels=None, min_urgency=None, quiet_start=None, quiet_end=None, dnd=None):
        if channels is not None:
            self.notification_preferences["channels"] = channels
        if min_urgency is not None:
            self.notification_preferences["min_urgency"] = min_urgency
        if quiet_start is not None:
            self.notification_preferences["quiet_hours"]["start"] = int(quiet_start)
        if quiet_end is not None:
            self.notification_preferences["quiet_hours"]["end"] = int(quiet_end)
        if dnd is not None:
            self.notification_preferences["do_not_disturb"] = bool(dnd)

    def is_quiet_hours(self):
        if self.notification_preferences.get("do_not_disturb"):
            return True
        now = datetime.now().hour
        start = self.notification_preferences["quiet_hours"]["start"]
        end = self.notification_preferences["quiet_hours"]["end"]
        if start == end:
            return False
        if start < end:
            return start <= now < end
        return now >= start or now < end

    def send_notification(self, message, urgency, channels=None, event_type=None):
        if self.is_quiet_hours():
            return False

        min_urgency = self.notification_preferences.get("min_urgency", "low")
        urgency_rank = {"low": 0, "medium": 1, "high": 2, "critical": 3}
        if urgency_rank.get(urgency, 0) < urgency_rank.get(min_urgency, 0):
            return False

        active_channels = channels or self.notification_preferences.get("channels", [])
        if "desktop" in active_channels:
            self.show_desktop_notification(message)
        if "email" in active_channels and urgency in ["high", "critical"]:
            self.send_email(message)
        if "sms" in active_channels and urgency == "critical":
            self.send_sms(message)
        if "voice" in active_channels:
            self.send_voice_alert(message)
        if "wallpaper" in active_channels and urgency in ["high", "critical"]:
            self.change_wallpaper(message)

        log_notification(event_type or "custom", message, urgency, ",".join(active_channels))
        return True

    def show_desktop_notification(self, message):
        print(f"[Desktop Notification] {message}")

    def send_email(self, message):
        print(f"[Email] {message}")

    def send_sms(self, message):
        print(f"[SMS] {message}")

    def send_voice_alert(self, message):
        print(f"[Voice Alert] {message}")

    def change_wallpaper(self, message):
        print(f"[Wallpaper Change] {message}")
