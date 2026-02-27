class GamificationEngine:
    def __init__(self):
        self.user_level = 1
        self.points = 0
        self.achievements = []
        self.achievement_catalog = {
            "Disciplined Day": {"points": 50, "desc": "Stay under daily limit"},
            "Focus Master": {"points": 100, "desc": "Complete 5 focus sessions"},
            "First Week": {"points": 150, "desc": "Track for 7 consecutive days"},
            "Under Budget": {"points": 200, "desc": "Stay under limit 5 days in a row"},
            "Focus Warrior": {"points": 250, "desc": "Complete 20 focus sessions"},
            "Early Bird": {"points": 200, "desc": "No screen time before 8 AM for a week"},
            "Weekend Warrior": {"points": 200, "desc": "Reduce weekend usage by 30%"},
            "Digital Detox": {"points": 300, "desc": "One full day with no screen time"}
        }
        self.level_thresholds = [0, 200, 500, 900, 1400, 2000]

    def award_achievement(self, name):
        if name in self.achievement_catalog and name not in self.achievements:
            self.achievements.append(name)
            self.points += self.achievement_catalog[name]["points"]
            self._update_level()

    def check_achievements(self, usage_data):
        if usage_data.get("stayed_under_limit"):
            self.award_achievement("Disciplined Day")
        if usage_data.get("focus_sessions", 0) >= 5:
            self.award_achievement("Focus Master")
        if usage_data.get("consecutive_days", 0) >= 7:
            self.award_achievement("First Week")
        if usage_data.get("under_budget_streak", 0) >= 5:
            self.award_achievement("Under Budget")
        if usage_data.get("focus_sessions", 0) >= 20:
            self.award_achievement("Focus Warrior")
        if usage_data.get("early_bird_week"):
            self.award_achievement("Early Bird")
        if usage_data.get("weekend_reduction"):
            self.award_achievement("Weekend Warrior")
        if usage_data.get("digital_detox_day"):
            self.award_achievement("Digital Detox")

    def _update_level(self):
        for idx, threshold in enumerate(self.level_thresholds):
            if self.points >= threshold:
                self.user_level = idx + 1

    def get_progress_to_next_level(self):
        if self.user_level >= len(self.level_thresholds):
            return 1.0
        current = self.level_thresholds[self.user_level - 1]
        next_level = self.level_thresholds[self.user_level]
        if next_level == current:
            return 1.0
        return min(1.0, (self.points - current) / (next_level - current))
