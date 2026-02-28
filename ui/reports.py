from datetime import datetime, timedelta
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame, QScrollArea, QListWidget
from backend.db import get_usage_for_date, get_mood_entries_for_date
from ui.ui_helpers import apply_card_shadow
class ReportsPage(QWidget):
    def __init__(self):
        super().__init__()
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content = QWidget()
        l = QVBoxLayout(content)
        l.setContentsMargins(24, 20, 24, 24)
        l.setSpacing(16)
        t = QLabel("Reports")
        t.setObjectName("title")
        l.addWidget(t)
        usage_card = QFrame()
        usage_card.setObjectName("card")
        apply_card_shadow(usage_card)
        uv = QVBoxLayout()
        uv.setSpacing(10)
        header = QLabel("Weekly Usage Summary")
        header.setObjectName("cardTitle")
        uv.addWidget(header)
        self.usage_list = QListWidget()
        uv.addWidget(self.usage_list)
        usage_card.setLayout(uv)
        l.addWidget(usage_card)

        mood_card = QFrame()
        mood_card.setObjectName("card")
        apply_card_shadow(mood_card)
        mv = QVBoxLayout()
        mv.setSpacing(10)
        header = QLabel("Weekly Mood Summary")
        header.setObjectName("cardTitle")
        mv.addWidget(header)
        self.mood_list = QListWidget()
        mv.addWidget(self.mood_list)
        mood_card.setLayout(mv)
        l.addWidget(mood_card)
        l.addStretch()

        scroll.setWidget(content)
        outer.addWidget(scroll)

        self.refresh()

    def refresh(self):
        self.usage_list.clear()
        self.mood_list.clear()
        today = datetime.now().date()
        for offset in range(7):
            day = today - timedelta(days=offset)
            usage_entries = get_usage_for_date(str(day))
            total_minutes = sum(entry["duration"] for entry in usage_entries)
            if total_minutes:
                hours = total_minutes // 60
                minutes = total_minutes % 60
                usage_text = f"{day}: {hours}h {minutes}m"
            else:
                usage_text = f"{day}: no usage logged"
            self.usage_list.addItem(usage_text)

            mood_entries = get_mood_entries_for_date(str(day))
            if mood_entries:
                mood_avg = sum(entry["mood"] for entry in mood_entries) / len(mood_entries)
                mood_text = f"{day}: mood {mood_avg:.1f}/10"
            else:
                mood_text = f"{day}: no mood check-ins"
            self.mood_list.addItem(mood_text)
