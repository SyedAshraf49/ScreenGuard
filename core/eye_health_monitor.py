class EyeHealthMonitor:
    def __init__(self):
        self.continuous_time = 0
        self.blue_light_exposure = 0
        self.focus_window = 50 * 60
        self.recovery_duration = 90
        self.in_recovery = False
        self.recovery_remaining = 0

    def update_time(self, seconds):
        if self.in_recovery:
            self.recovery_remaining = max(0, self.recovery_remaining - seconds)
            if self.recovery_remaining == 0:
                self.end_recovery()
            return

        if seconds > 0:
            self.continuous_time += seconds
            self.blue_light_exposure += seconds

    def get_load_percent(self):
        if self.focus_window <= 0:
            return 0
        return min(100, int((self.continuous_time / self.focus_window) * 100))

    def get_focus_score(self):
        load = self.get_load_percent()
        return max(0, 100 - load)

    def get_recovery_suggestion(self):
        load = self.get_load_percent()
        if load >= 100:
            return "High eye load detected. Start a 90s recovery session now."
        if load >= 80:
            return "Eye load rising. Consider a short recovery in a few minutes."
        if load >= 50:
            return "Focus is steady. Keep blinking and adjust posture."
        return "Focus health looks good."

    def get_next_recovery_hint(self):
        remaining = max(0, self.focus_window - self.continuous_time)
        return remaining

    def start_recovery(self):
        self.in_recovery = True
        self.recovery_remaining = self.recovery_duration

    def end_recovery(self):
        self.in_recovery = False
        self.recovery_remaining = 0
        self.continuous_time = max(0, self.continuous_time - (15 * 60))

    def get_blue_light_exposure(self):
        return self.blue_light_exposure
