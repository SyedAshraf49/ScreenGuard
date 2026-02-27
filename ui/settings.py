from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QSpinBox, QPushButton, QCheckBox, QComboBox, QFrame, QLineEdit, QScrollArea, QHBoxLayout
from datetime import date
from core.smart_notifier import SmartNotifier
from core.calendar_integration import GoogleCalendarClient
from core.schedule_awareness import ScheduleAwarenessEngine
from ui.ui_helpers import apply_card_shadow

class SettingsPage(QWidget):
    def __init__(self, notifier=None, theme_callback=None):
        super().__init__()
        self.notifier = notifier or SmartNotifier()
        self.theme_callback = theme_callback

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content = QWidget()
        l = QVBoxLayout(content)
        l.setContentsMargins(24, 20, 24, 24)
        l.setSpacing(16)

        t = QLabel("Settings")
        t.setObjectName("title")
        l.addWidget(t)

        limit_card = QFrame()
        limit_card.setObjectName("card")
        apply_card_shadow(limit_card)
        lv = QVBoxLayout()
        lv.setSpacing(10)
        header = QLabel("Usage Limits")
        header.setObjectName("cardTitle")
        lv.addWidget(header)

        limit_row = QHBoxLayout()
        limit_row.addWidget(QLabel("Daily Screen Time Limit (hours)"))
        self.daily_limit_box = QSpinBox()
        self.daily_limit_box.setRange(1, 24)
        self.daily_limit_box.setValue(6)
        self.daily_limit_box.setFixedWidth(90)
        limit_row.addStretch()
        limit_row.addWidget(self.daily_limit_box)
        lv.addLayout(limit_row)

        limit_card.setLayout(lv)
        l.addWidget(limit_card)

        notif_card = QFrame()
        notif_card.setObjectName("card")
        apply_card_shadow(notif_card)
        nv = QVBoxLayout()
        nv.setSpacing(10)
        header = QLabel("Notification Preferences")
        header.setObjectName("cardTitle")
        nv.addWidget(header)

        self.desktop_cb = QCheckBox("Desktop notifications")
        self.email_cb = QCheckBox("Email notifications (high urgency)")
        self.sms_cb = QCheckBox("SMS notifications (critical)")
        self.voice_cb = QCheckBox("Voice alerts")
        self.wallpaper_cb = QCheckBox("Change wallpaper on limit exceeded")

        self.desktop_cb.setChecked(True)

        self.urgency_box = QComboBox()
        self.urgency_box.addItems(["low", "medium", "high", "critical"])

        self.quiet_start = QSpinBox()
        self.quiet_start.setRange(0, 23)
        self.quiet_start.setValue(22)
        self.quiet_end = QSpinBox()
        self.quiet_end.setRange(0, 23)
        self.quiet_end.setValue(7)

        self.dnd_cb = QCheckBox("Do Not Disturb")

        nv.addWidget(self.desktop_cb)
        nv.addWidget(self.email_cb)
        nv.addWidget(self.sms_cb)
        nv.addWidget(self.voice_cb)
        nv.addWidget(self.wallpaper_cb)
        nv.addWidget(QLabel("Minimum urgency to notify"))
        nv.addWidget(self.urgency_box)
        nv.addWidget(QLabel("Quiet hours start (0-23)"))
        nv.addWidget(self.quiet_start)
        nv.addWidget(QLabel("Quiet hours end (0-23)"))
        nv.addWidget(self.quiet_end)
        nv.addWidget(self.dnd_cb)

        notif_card.setLayout(nv)
        l.addWidget(notif_card)

        appearance_card = QFrame()
        appearance_card.setObjectName("card")
        apply_card_shadow(appearance_card)
        av = QVBoxLayout()
        av.setSpacing(10)
        header = QLabel("Appearance")
        header.setObjectName("cardTitle")
        av.addWidget(header)
        self.theme_box = QComboBox()
        self.theme_box.addItems(["Night", "Day", "Aurora", "Sunset", "Mono"])
        self.theme_box.currentTextChanged.connect(self.on_theme_changed)
        av.addWidget(QLabel("Theme"))
        av.addWidget(self.theme_box)
        appearance_card.setLayout(av)
        l.addWidget(appearance_card)

        calendar_card = QFrame()
        calendar_card.setObjectName("card")
        apply_card_shadow(calendar_card)
        cv = QVBoxLayout()
        cv.setSpacing(10)
        header = QLabel("Calendar Integration (Google)")
        header.setObjectName("cardTitle")
        cv.addWidget(header)
        self.calendar_enabled_cb = QCheckBox("Enable calendar sync")
        self.exam_mode_cb = QCheckBox("Exam mode (stricter limits)")
        cv.addWidget(self.calendar_enabled_cb)
        cv.addWidget(self.exam_mode_cb)

        cv.addWidget(QLabel("Credentials JSON path"))
        self.credentials_input = QLineEdit()
        self.credentials_input.setPlaceholderText("path/to/credentials.json")
        cv.addWidget(self.credentials_input)

        cv.addWidget(QLabel("Calendar ID (default: primary)"))
        self.calendar_id_input = QLineEdit()
        self.calendar_id_input.setPlaceholderText("primary")
        cv.addWidget(self.calendar_id_input)

        self.calendar_status = QLabel("Status: not synced")
        cv.addWidget(self.calendar_status)

        sync_btn = QPushButton("Sync Calendar Now")
        sync_btn.clicked.connect(self.sync_calendar)
        cv.addWidget(sync_btn)

        calendar_card.setLayout(cv)
        l.addWidget(calendar_card)

        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save_settings)
        l.addWidget(save_btn)
        l.addStretch()
        scroll.setWidget(content)
        outer.addWidget(scroll)

    def on_theme_changed(self, value):
        if not self.theme_callback:
            return
        selected = (value or "Night").strip().lower()
        self.theme_callback(selected)

    def save_settings(self):
        channels = []
        if self.desktop_cb.isChecked():
            channels.append("desktop")
        if self.email_cb.isChecked():
            channels.append("email")
        if self.sms_cb.isChecked():
            channels.append("sms")
        if self.voice_cb.isChecked():
            channels.append("voice")
        if self.wallpaper_cb.isChecked():
            channels.append("wallpaper")

        self.notifier.set_preferences(
            channels=channels,
            min_urgency=self.urgency_box.currentText(),
            quiet_start=self.quiet_start.value(),
            quiet_end=self.quiet_end.value(),
            dnd=self.dnd_cb.isChecked()
        )

    def sync_calendar(self):
        if not self.calendar_enabled_cb.isChecked():
            self.calendar_status.setText("Status: calendar sync is disabled")
            return

        credentials_path = self.credentials_input.text().strip()
        calendar_id = self.calendar_id_input.text().strip() or "primary"
        if not credentials_path:
            self.calendar_status.setText("Status: missing credentials path")
            return

        try:
            client = GoogleCalendarClient(credentials_path, calendar_id=calendar_id)
            engine = ScheduleAwarenessEngine(
                client,
                base_daily_limit_hours=self.daily_limit_box.value(),
                exam_mode=self.exam_mode_cb.isChecked()
            )
            suggested_limit, busy_hours, event_count = engine.suggest_limit(date.today())
            self.calendar_status.setText(
                f"Status: {event_count} events, {busy_hours:.1f} busy hours, "
                f"suggested limit {suggested_limit}h"
            )
        except Exception as exc:
            self.calendar_status.setText(f"Status: sync failed - {exc}")
