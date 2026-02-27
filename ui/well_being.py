from datetime import datetime
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QFrame,
    QPushButton,
    QListWidget,
    QScrollArea
)
from core.well_being_tracker import WellBeingTracker
from core.memory_store import get_recent_mood_entries
from ui.ui_helpers import apply_card_shadow


class WellBeingPage(QWidget):
    def __init__(self):
        super().__init__()
        self.tracker = WellBeingTracker()

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(24, 20, 24, 24)
        layout.setSpacing(16)

        title = QLabel("Mood & Well-Being")
        title.setObjectName("title")
        layout.addWidget(title)

        layout.addWidget(self._build_checkin_card())
        layout.addWidget(self._build_trends_card())
        layout.addWidget(self._build_recommendations_card())
        layout.addWidget(self._build_integrations_card())

        layout.addStretch()
        scroll.setWidget(content)
        outer.addWidget(scroll)

        self.refresh_insights()
        self.refresh_recent_entries()
        self._start_auto_mood_logging()

    def _build_checkin_card(self):
        card = QFrame()
        card.setObjectName("card")
        apply_card_shadow(card)
        v = QVBoxLayout()
        v.setSpacing(10)
        header = QLabel("Automatic Mood Tracking")
        header.setObjectName("cardTitle")
        v.addWidget(header)

        v.addWidget(QLabel("Mood check-ins are captured automatically every hour."))

        self.checkin_status = QLabel("")
        v.addWidget(self.checkin_status)

        self.recent_entries = QListWidget()
        self.recent_entries.setMinimumHeight(100)
        v.addWidget(self.recent_entries)

        card.setLayout(v)
        return card

    def _build_trends_card(self):
        card = QFrame()
        card.setObjectName("card")
        apply_card_shadow(card)
        v = QVBoxLayout()
        v.setSpacing(10)
        header = QLabel("Trends & Correlations")
        header.setObjectName("cardTitle")
        v.addWidget(header)

        self.mood_trend_label = QLabel("")
        self.correlation_label = QLabel("")
        self.patterns_label = QLabel("")
        self.patterns_label.setWordWrap(True)

        v.addWidget(self.mood_trend_label)
        v.addWidget(self.correlation_label)
        v.addWidget(self.patterns_label)

        card.setLayout(v)
        return card

    def _build_recommendations_card(self):
        card = QFrame()
        card.setObjectName("card")
        apply_card_shadow(card)
        v = QVBoxLayout()
        v.setSpacing(10)
        header = QLabel("Well-Being Recommendations")
        header.setObjectName("cardTitle")
        v.addWidget(header)

        self.recommendations_label = QLabel("")
        self.recommendations_label.setWordWrap(True)
        v.addWidget(self.recommendations_label)

        card.setLayout(v)
        return card

    def _build_integrations_card(self):
        card = QFrame()
        card.setObjectName("card")
        apply_card_shadow(card)
        v = QVBoxLayout()
        v.setSpacing(10)
        header = QLabel("Mental Health App Integrations")
        header.setObjectName("cardTitle")
        v.addWidget(header)
        v.addWidget(QLabel("Planned: Daylio, Moodpath, Apple Health, Google Fit"))
        self.integration_status = QLabel("Status: not connected")
        v.addWidget(self.integration_status)

        export_btn = QPushButton("Generate Summary")
        export_btn.clicked.connect(self.on_generate_summary)
        v.addWidget(export_btn)

        card.setLayout(v)
        return card

    def _start_auto_mood_logging(self):
        self.auto_mood_timer = QTimer(self)
        self.auto_mood_timer.setInterval(60 * 60 * 1000)
        self.auto_mood_timer.timeout.connect(self._auto_log_mood)
        self.auto_mood_timer.start()
        self._auto_log_mood()

    def _auto_log_mood(self):
        if self.tracker.auto_log_mood_checkin(timestamp=datetime.now()):
            self.checkin_status.setText("Auto mood check-in logged.")
            self.refresh_insights()
            self.refresh_recent_entries()

    def on_generate_summary(self):
        trend = self.tracker.get_trend_summary()
        correlation = self.tracker.analyze_correlations()
        lines = []
        if trend.get("average") is not None:
            lines.append(f"7-day average mood: {trend['average']:.1f}")
        if correlation.get("correlation") is not None:
            lines.append(f"Mood vs screen time correlation: {correlation['correlation']:.2f}")
        if not lines:
            lines.append("Not enough data for summary yet.")
        self.integration_status.setText("Summary: " + " | ".join(lines))

    def refresh_recent_entries(self):
        self.recent_entries.clear()
        entries = get_recent_mood_entries(limit=8)
        if not entries:
            self.recent_entries.addItem("No mood check-ins yet.")
            return
        for entry in reversed(entries):
            note = f" - {entry['note']}" if entry.get("note") else ""
            self.recent_entries.addItem(f"{entry['date']} {entry['time'][11:16]}: {entry['mood']}/10{note}")

    def refresh_insights(self):
        trend = self.tracker.get_trend_summary()
        if trend.get("average") is None:
            self.mood_trend_label.setText("Mood trend: log a few days to see trends.")
        else:
            direction = trend.get("trend")
            if direction == "up":
                trend_text = "up vs previous week"
            elif direction == "down":
                trend_text = "down vs previous week"
            elif direction == "flat":
                trend_text = "steady vs previous week"
            else:
                trend_text = "no prior week data"
            self.mood_trend_label.setText(f"Mood trend: {trend['average']:.1f} avg ({trend_text})")

        correlation = self.tracker.analyze_correlations()
        if correlation.get("pair_count", 0) < 2:
            self.correlation_label.setText("Screen time correlation: log more data to compare days.")
        else:
            corr = correlation.get("correlation")
            if corr is None:
                corr_text = "not enough variance yet"
            else:
                corr_text = f"corr {corr:.2f}"
            high_avg = correlation.get("high_avg")
            low_avg = correlation.get("low_avg")
            if high_avg is not None and low_avg is not None:
                self.correlation_label.setText(
                    f"Screen time correlation: {corr_text}, 8h+ mood {high_avg:.1f} vs <8h mood {low_avg:.1f}"
                )
            else:
                self.correlation_label.setText(f"Screen time correlation: {corr_text}")

        patterns = self.tracker.detect_patterns()
        if not patterns:
            self.patterns_label.setText("Patterns: nothing notable yet.")
        else:
            self.patterns_label.setText("Patterns: " + " | ".join(patterns))

        tips = self.tracker.get_well_being_recommendations()
        self.recommendations_label.setText("\n".join(tips))

    def refresh(self):
        self.refresh_insights()
        self.refresh_recent_entries()
