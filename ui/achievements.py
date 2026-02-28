from datetime import datetime
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar, QFrame, QScrollArea
from core.gamification import GamificationEngine
from ui.ui_helpers import apply_card_shadow
from backend.db import get_usage_for_date

class AchievementsPage(QWidget):
    def __init__(self, engine=None):
        super().__init__()
        self.engine = engine or GamificationEngine()

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(24, 20, 24, 24)
        layout.setSpacing(16)

        title = QLabel("Achievements & Rewards")
        title.setObjectName("title")
        layout.addWidget(title)

        self.level_label = QLabel(f"Level {self.engine.user_level}")
        layout.addWidget(self.level_label)

        self.level_bar = QProgressBar()
        self.level_bar.setRange(0, 100)
        self.level_bar.setValue(int(self.engine.get_progress_to_next_level() * 100))
        self.level_bar.setFormat("Level Progress: %p%")
        layout.addWidget(self.level_bar)

        achieved = QFrame()
        achieved.setObjectName("card")
        apply_card_shadow(achieved)
        v = QVBoxLayout()
        v.setSpacing(10)
        header = QLabel("Unlocked Achievements")
        header.setObjectName("cardTitle")
        v.addWidget(header)
        unlocked = self.engine.achievements or ["No achievements yet"]
        v.addWidget(QLabel("\n".join(unlocked)))
        achieved.setLayout(v)
        layout.addWidget(achieved)

        pending = QFrame()
        pending.setObjectName("card")
        apply_card_shadow(pending)
        pv = QVBoxLayout()
        pv.setSpacing(10)
        header = QLabel("Pending Achievements")
        header.setObjectName("cardTitle")
        pv.addWidget(header)
        self.pending_label = QLabel("")
        pv.addWidget(self.pending_label)
        pending.setLayout(pv)
        layout.addWidget(pending)

        layout.addStretch()
        scroll.setWidget(content)
        outer.addWidget(scroll)

    def refresh(self):
        today = datetime.now().date()
        usage_entries = get_usage_for_date(str(today))
        total_minutes = sum(entry["duration"] for entry in usage_entries)
        usage_data = {
            "stayed_under_limit": total_minutes > 0 and total_minutes <= 360,
            "focus_sessions": 0,
            "consecutive_days": 0,
            "under_budget_streak": 0,
            "early_bird_week": False,
            "weekend_reduction": False,
            "digital_detox_day": total_minutes == 0
        }
        self.engine.check_achievements(usage_data)
        self.level_label.setText(f"Level {self.engine.user_level}")
        self.level_bar.setValue(int(self.engine.get_progress_to_next_level() * 100))
        pending_list = [
            f"{name} - {info['desc']}"
            for name, info in self.engine.achievement_catalog.items()
            if name not in self.engine.achievements
        ]
        self.pending_label.setText("\n".join(pending_list) if pending_list else "All achievements unlocked!")
