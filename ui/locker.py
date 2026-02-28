from __future__ import annotations

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from ui.ui_helpers import apply_card_shadow


class LockerPage(QWidget):
    """Per-app time-limit & lock management page."""

    DEFAULT_APP_SUGGESTIONS = [
        "chrome",
        "msedge",
        "firefox",
        "brave",
        "code",
        "pycharm64",
        "discord",
        "spotify",
        "steam",
        "telegram",
        "whatsapp",
        "notion",
        "teams",
        "zoom",
        "obs64",
    ]

    def __init__(self) -> None:
        super().__init__()
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(24, 20, 24, 24)
        layout.setSpacing(16)

        title = QLabel("App Locker")
        title.setObjectName("title")
        layout.addWidget(title)

        subtitle = QLabel(
            "Set daily time limits for specific apps. Once a limit is reached the app "
            "is minimised automatically. Unlock anytime from the ScreenGuard website."
        )
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        # ── Add limit card ────────────────────────────────────────────────────
        add_card = QFrame()
        add_card.setObjectName("card")
        apply_card_shadow(add_card)
        add_layout = QVBoxLayout(add_card)
        add_layout.setSpacing(10)

        add_title = QLabel("Set App Limit")
        add_title.setObjectName("cardTitle")
        add_layout.addWidget(add_title)

        row = QHBoxLayout()
        self.app_input = QComboBox()
        self.app_input.setEditable(True)
        self.app_input.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        if self.app_input.lineEdit() is not None:
            self.app_input.lineEdit().setPlaceholderText("Choose app or type app name")
        row.addWidget(self.app_input, stretch=1)

        refresh_apps_btn = QPushButton("Refresh Apps")
        refresh_apps_btn.clicked.connect(self._refresh_app_choices)
        row.addWidget(refresh_apps_btn)

        self.minutes_spin = QSpinBox()
        self.minutes_spin.setRange(1, 1440)
        self.minutes_spin.setValue(60)
        self.minutes_spin.setSuffix(" min / day")
        row.addWidget(self.minutes_spin)

        save_btn = QPushButton("Set Limit")
        save_btn.clicked.connect(self._save_limit)
        row.addWidget(save_btn)

        add_layout.addLayout(row)
        self.add_status = QLabel("")
        add_layout.addWidget(self.add_status)
        layout.addWidget(add_card)

        # ── Current limits card ───────────────────────────────────────────────
        limits_card = QFrame()
        limits_card.setObjectName("card")
        apply_card_shadow(limits_card)
        limits_layout = QVBoxLayout(limits_card)
        limits_layout.setSpacing(10)

        limits_title = QLabel("Active Limits (today's usage)")
        limits_title.setObjectName("cardTitle")
        limits_layout.addWidget(limits_title)

        self.limits_container = QVBoxLayout()
        limits_layout.addLayout(self.limits_container)
        self.no_limits_label = QLabel("No app limits configured yet.")
        self.limits_container.addWidget(self.no_limits_label)
        layout.addWidget(limits_card)

        # ── Locked apps card ──────────────────────────────────────────────────
        locked_card = QFrame()
        locked_card.setObjectName("card")
        apply_card_shadow(locked_card)
        locked_layout = QVBoxLayout(locked_card)
        locked_layout.setSpacing(10)

        locked_title = QLabel("Currently Locked Apps")
        locked_title.setObjectName("cardTitle")
        locked_layout.addWidget(locked_title)

        self.locked_container = QVBoxLayout()
        locked_layout.addLayout(self.locked_container)
        self.no_locked_label = QLabel("No apps are locked right now.")
        self.locked_container.addWidget(self.no_locked_label)
        layout.addWidget(locked_card)

        layout.addStretch()
        scroll.setWidget(content)
        outer.addWidget(scroll)

        # Auto-refresh every 10 seconds
        self._timer = QTimer(self)
        self._timer.setInterval(10_000)
        self._timer.timeout.connect(self.refresh)
        self._timer.start()

        self._refresh_app_choices()
        self.refresh()

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _save_limit(self) -> None:
        app_name = self.app_input.currentText().strip()
        minutes = self.minutes_spin.value()
        if not app_name:
            self.add_status.setText("Please enter an app name.")
            return
        try:
            from backend.db import set_app_limit
            set_app_limit(app_name, minutes)
            self.add_status.setText(f"Limit set: {app_name} → {minutes} min / day")
            if self.app_input.lineEdit() is not None:
                self.app_input.lineEdit().clear()
            self._refresh_app_choices()
            self.refresh()
        except Exception as exc:
            self.add_status.setText(f"Error: {exc}")

    def _refresh_app_choices(self) -> None:
        from backend.db import list_available_apps

        current_text = self.app_input.currentText().strip()
        suggestions = set(self.DEFAULT_APP_SUGGESTIONS)
        suggestions.update(list_available_apps())

        sorted_items = sorted(suggestions)
        self.app_input.blockSignals(True)
        self.app_input.clear()
        self.app_input.addItems(sorted_items)
        if current_text:
            self.app_input.setCurrentText(current_text)
        self.app_input.blockSignals(False)

    def _remove_limit(self, app_name: str) -> None:
        from backend.db import remove_app_limit
        remove_app_limit(app_name)
        self.refresh()

    def _unlock_app(self, app_name: str) -> None:
        from backend.db import unlock_app
        unlock_app(app_name)
        self.refresh()

    # ── Refresh ───────────────────────────────────────────────────────────────

    def refresh(self) -> None:
        self._refresh_app_choices()
        self._refresh_limits()
        self._refresh_locked()

    def _clear_layout(self, layout: QVBoxLayout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _refresh_limits(self) -> None:
        from datetime import datetime
        from backend.db import list_app_limits, get_usage_for_date, is_app_locked

        self._clear_layout(self.limits_container)
        limits = list_app_limits()
        if not limits:
            self.limits_container.addWidget(QLabel("No app limits configured yet."))
            return

        today = str(datetime.now().date())
        usage_entries = get_usage_for_date(today)
        usage_by_app: dict[str, int] = {}
        for e in usage_entries:
            usage_by_app[e["app"]] = usage_by_app.get(e["app"], 0) + int(e["duration"])

        for lim in limits:
            app = lim["app"]
            daily = lim["daily_minutes"]
            used = usage_by_app.get(app, 0)
            locked = is_app_locked(app)

            row_widget = QFrame()
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(0, 0, 0, 0)

            lock_icon = "🔒 " if locked else ""
            info = QLabel(f"{lock_icon}{app}  —  {used}/{daily} min")
            if locked:
                info.setStyleSheet("color: #e55;")
            row_layout.addWidget(info, stretch=1)

            del_btn = QPushButton("Remove")
            del_btn.setFixedWidth(80)
            del_btn.clicked.connect(lambda _checked, a=app: self._remove_limit(a))
            row_layout.addWidget(del_btn)

            self.limits_container.addWidget(row_widget)

    def _refresh_locked(self) -> None:
        from backend.db import list_locked_apps

        self._clear_layout(self.locked_container)
        locked = list_locked_apps()
        if not locked:
            self.locked_container.addWidget(QLabel("No apps are locked right now."))
            return

        for entry in locked:
            app = entry["app"]
            reason = entry["locked_reason"]
            locked_at = entry["locked_at"]

            row_widget = QFrame()
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(0, 0, 0, 0)

            info = QLabel(f"🔒  {app}  ({reason})  since {locked_at[:16]}")
            info.setStyleSheet("color: #e55;")
            row_layout.addWidget(info, stretch=1)

            unlock_btn = QPushButton("Unlock")
            unlock_btn.setFixedWidth(80)
            unlock_btn.clicked.connect(lambda _checked, a=app: self._unlock_app(a))
            row_layout.addWidget(unlock_btn)

            self.locked_container.addWidget(row_widget)
