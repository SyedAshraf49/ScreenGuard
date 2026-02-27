from datetime import datetime, timedelta
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QFrame,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QCheckBox,
    QComboBox,
    QScrollArea
)
from PyQt6.QtCore import QTimer
from PyQt6.QtCore import QSettings
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from core.recommender import get_recommendations
from core.memory_store import add_usage, get_usage_for_date, reset_all
from core.active_window import get_active_app_name
from ui.ui_helpers import apply_card_shadow

class DashboardPage(QWidget):
    def __init__(self):
        super().__init__()
        self.settings = QSettings("ScreenGuard", "ScreenGuard")
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(24, 20, 24, 24)
        layout.setSpacing(16)

        title = QLabel("Dashboard")
        title.setObjectName("title")

        card = QFrame()
        card.setObjectName("card")
        apply_card_shadow(card)
        v = QVBoxLayout()
        v.setSpacing(10)
        header = QLabel("Smart Recommendations")
        header.setObjectName("cardTitle")
        v.addWidget(header)
        self.recommendations_label = QLabel()
        v.addWidget(self.recommendations_label)
        card.setLayout(v)

        summary_card = QFrame()
        summary_card.setObjectName("card")
        apply_card_shadow(summary_card)
        sv = QVBoxLayout()
        sv.setSpacing(10)
        header = QLabel("Usage Summary")
        header.setObjectName("cardTitle")
        sv.addWidget(header)
        self.total_usage_label = QLabel("")
        self.top_apps_label = QLabel("")
        self.trend_label = QLabel("")
        self.top_five_cb = QCheckBox("Top 5 apps")
        self.top_five_cb.setChecked(self._load_top_five_setting())
        self.top_five_cb.toggled.connect(self.refresh_summary)
        self.chart_mode = self._load_chart_mode_setting()
        self.chart_mode_box = QComboBox()
        self.chart_mode_box.addItem("Stacked Bars", "stacked")
        self.chart_mode_box.addItem("Smooth Area", "area")
        if self.chart_mode == "area":
            self.chart_mode_box.setCurrentIndex(1)
        self.chart_mode_box.currentIndexChanged.connect(self._on_chart_mode_changed)
        sv.addWidget(self.total_usage_label)
        sv.addWidget(self.top_apps_label)
        sv.addWidget(self.trend_label)
        sv.addWidget(self.top_five_cb)
        chart_mode_row = QHBoxLayout()
        chart_mode_row.addWidget(QLabel("Chart style"))
        chart_mode_row.addStretch()
        chart_mode_row.addWidget(self.chart_mode_box)
        sv.addLayout(chart_mode_row)
        self.usage_chart_figure = Figure(figsize=(5, 2.2))
        self.usage_chart_canvas = FigureCanvas(self.usage_chart_figure)
        self.usage_chart_canvas.setMinimumHeight(180)
        sv.addWidget(self.usage_chart_canvas)
        summary_card.setLayout(sv)

        usage_card = QFrame()
        usage_card.setObjectName("card")
        apply_card_shadow(usage_card)
        uv = QVBoxLayout()
        uv.setSpacing(10)
        header = QLabel("Automatic Usage Tracking")
        header.setObjectName("cardTitle")
        uv.addWidget(header)

        row = QHBoxLayout()
        self.app_input = QLineEdit()
        self.app_input.setPlaceholderText("Current active app")
        self.app_input.setReadOnly(True)
        self.auto_logging_enabled = self._load_auto_logging_setting()
        self.auto_log_toggle_btn = QPushButton("Pause Auto Logging")
        self.auto_log_toggle_btn.clicked.connect(self.on_toggle_auto_logging)
        row.addWidget(self.app_input, 1)
        row.addWidget(self.auto_log_toggle_btn)
        uv.addLayout(row)

        reset_btn = QPushButton("Reset In-Memory Data")
        reset_btn.clicked.connect(self.on_reset)
        uv.addWidget(reset_btn)

        self.usage_status = QLabel("")
        uv.addWidget(self.usage_status)
        self.auto_log_status = QLabel("Auto logging: ON")
        uv.addWidget(self.auto_log_status)
        self._apply_auto_logging_ui_state()
        usage_card.setLayout(uv)

        layout.addWidget(title)
        layout.addWidget(card)
        layout.addWidget(summary_card)
        layout.addWidget(usage_card)
        layout.addStretch()
        scroll.setWidget(content)
        outer.addWidget(scroll)

        self.refresh_recommendations()
        self.refresh_summary()
        self._start_auto_app_detection()
        self._start_auto_usage_logging()

    def refresh_recommendations(self):
        self.recommendations_label.setText("\n".join(get_recommendations()))

    def refresh(self):
        self.refresh_recommendations()
        self.refresh_summary()

    def _format_minutes(self, minutes):
        hours = minutes // 60
        remainder = minutes % 60
        if hours > 0:
            return f"{hours}h {remainder}m"
        return f"{remainder}m"

    def refresh_summary(self):
        today = datetime.now().date()
        yesterday = today - timedelta(days=1)
        self.settings.setValue("dashboard.top_five", "1" if self.top_five_cb.isChecked() else "0")
        usage_entries = get_usage_for_date(str(today))
        totals = {}
        total_minutes = 0
        for entry in usage_entries:
            totals[entry["app"]] = totals.get(entry["app"], 0) + entry["duration"]
            total_minutes += entry["duration"]

        top_n = 5 if self.top_five_cb.isChecked() else 3
        top_apps = sorted(totals.items(), key=lambda item: (-item[1], item[0]))[:top_n]
        if top_apps:
            top_text = ", ".join(
                [f"{name} ({self._format_minutes(minutes)})" for name, minutes in top_apps]
            )
        else:
            top_text = "No usage logged yet."

        if total_minutes == 0:
            self.total_usage_label.setText("Today total: no usage yet today")
        else:
            self.total_usage_label.setText(f"Today total: {self._format_minutes(total_minutes)}")
        self.top_apps_label.setText(f"Top apps: {top_text}")

        yesterday_entries = get_usage_for_date(str(yesterday))
        yesterday_total = sum(entry["duration"] for entry in yesterday_entries)
        if yesterday_total == 0:
            self.trend_label.setText("Trend: no data for yesterday")
        else:
            diff = total_minutes - yesterday_total
            if diff == 0:
                self.trend_label.setText("Trend: same as yesterday")
            else:
                arrow = "^" if diff > 0 else "v"
                sign = "+" if diff > 0 else "-"
                self.trend_label.setText(
                    f"Trend: {arrow} {sign}{self._format_minutes(abs(diff))} vs yesterday"
                )

        self._render_usage_chart(today)

    def _render_usage_chart(self, today):
        self.usage_chart_figure.clear()
        chart_axis = self.usage_chart_figure.add_subplot(111)
        self.usage_chart_figure.patch.set_alpha(0.0)
        chart_axis.set_facecolor("none")

        week_days = [today - timedelta(days=offset) for offset in range(6, -1, -1)]
        day_labels = [day.strftime("%a") for day in week_days]

        week_entries = [get_usage_for_date(str(day)) for day in week_days]
        weekly_app_totals = {}
        for entries in week_entries:
            for entry in entries:
                weekly_app_totals[entry["app"]] = weekly_app_totals.get(entry["app"], 0) + entry["duration"]

        top_app_names = [
            name for name, _ in sorted(weekly_app_totals.items(), key=lambda item: (-item[1], item[0]))[:5]
        ]

        if not top_app_names:
            chart_axis.text(0.5, 0.5, "No weekly usage data yet", ha="center", va="center")
            chart_axis.set_xticks([])
            chart_axis.set_yticks([])
            chart_axis.set_frame_on(False)
            self.usage_chart_canvas.draw_idle()
            return

        app_series = {name: [0] * len(week_days) for name in top_app_names}
        other_series = [0] * len(week_days)

        for day_index, entries in enumerate(week_entries):
            per_day = {}
            for entry in entries:
                per_day[entry["app"]] = per_day.get(entry["app"], 0) + entry["duration"]

            for app_name in top_app_names:
                app_series[app_name][day_index] = per_day.get(app_name, 0)

            other_series[day_index] = sum(
                minutes for app_name, minutes in per_day.items() if app_name not in top_app_names
            )

        series_order = list(top_app_names)
        if any(other_series):
            app_series["Other"] = other_series
            series_order.append("Other")

        color_palette = ["#38bdf8", "#22c55e", "#f59e0b", "#a78bfa", "#fb7185", "#94a3b8"]
        x_values = list(range(len(week_days)))
        if self.chart_mode == "area":
            series_values = [app_series[app_name] for app_name in series_order]
            chart_axis.stackplot(
                x_values,
                series_values,
                labels=series_order,
                colors=color_palette[:len(series_order)],
                alpha=0.85,
            )
            chart_axis.set_xticks(x_values)
            chart_axis.set_xticklabels(day_labels)
        else:
            stacked_bottom = [0] * len(week_days)
            for series_index, app_name in enumerate(series_order):
                values = app_series[app_name]
                chart_axis.bar(
                    day_labels,
                    values,
                    bottom=stacked_bottom,
                    label=app_name,
                    color=color_palette[series_index % len(color_palette)],
                )
                stacked_bottom = [stacked_bottom[i] + values[i] for i in range(len(values))]

        chart_axis.set_title("Weekly Review: Daily Usage by App")
        chart_axis.set_ylabel("Minutes")
        chart_axis.tick_params(axis="x", labelrotation=0)
        chart_axis.grid(axis="y", linestyle="--", alpha=0.25)
        chart_axis.legend(loc="upper left", fontsize=8, ncol=2, frameon=False)

        self.usage_chart_figure.tight_layout()
        self.usage_chart_canvas.draw_idle()

    def _on_chart_mode_changed(self):
        selected = self.chart_mode_box.currentData()
        self.chart_mode = selected if selected in ["stacked", "area"] else "stacked"
        self.settings.setValue("dashboard.chart_mode", self.chart_mode)
        self.refresh_summary()

    def _load_chart_mode_setting(self):
        value = (self.settings.value("dashboard.chart_mode", "stacked") or "stacked").strip().lower()
        return value if value in ["stacked", "area"] else "stacked"

    def _load_top_five_setting(self):
        value = (self.settings.value("dashboard.top_five", "0") or "0").strip().lower()
        return value in ["1", "true", "yes", "on"]

    def _load_auto_logging_setting(self):
        value = (self.settings.value("dashboard.auto_logging_enabled", "1") or "1").strip().lower()
        return value in ["1", "true", "yes", "on"]

    def _apply_auto_logging_ui_state(self):
        if self.auto_logging_enabled:
            self.auto_log_toggle_btn.setText("Pause Auto Logging")
            self.auto_log_status.setText("Auto logging: ON")
        else:
            self.auto_log_toggle_btn.setText("Resume Auto Logging")
            self.auto_log_status.setText("Auto logging: PAUSED")

    def _start_auto_app_detection(self):
        self.auto_app_timer = QTimer(self)
        self.auto_app_timer.setInterval(2000)
        self.auto_app_timer.timeout.connect(self._refresh_active_app)
        self.auto_app_timer.start()
        self._refresh_active_app()

    def _refresh_active_app(self):
        detected_app = get_active_app_name()
        if detected_app:
            self.app_input.setText(detected_app)

    def _start_auto_usage_logging(self):
        self.auto_log_timer = QTimer(self)
        self.auto_log_timer.setInterval(60000)
        self.auto_log_timer.timeout.connect(self._auto_log_active_app_minute)
        self.auto_log_timer.start()

    def _auto_log_active_app_minute(self):
        if not self.auto_logging_enabled:
            self.auto_log_status.setText("Auto logging: PAUSED")
            return
        detected_app = get_active_app_name()
        if not detected_app:
            self.auto_log_status.setText("Auto logging: ON (waiting for active app)")
            return
        add_usage(detected_app, 1)
        self.auto_log_status.setText(f"Auto logging: ON ({detected_app})")
        self.refresh_recommendations()
        self.refresh_summary()

    def on_toggle_auto_logging(self):
        self.auto_logging_enabled = not self.auto_logging_enabled
        self.settings.setValue("dashboard.auto_logging_enabled", "1" if self.auto_logging_enabled else "0")
        self._apply_auto_logging_ui_state()

    def on_reset(self):
        reset_all()
        self.usage_status.setText("All in-memory data cleared.")
        self.refresh_recommendations()
        self.refresh_summary()
