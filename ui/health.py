from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QProgressBar, QFrame, QScrollArea
from core.eye_health_monitor import EyeHealthMonitor
from ui.ui_helpers import apply_card_shadow

class HealthPage(QWidget):
    def __init__(self, monitor=None):
        super().__init__()
        self.monitor = monitor or EyeHealthMonitor()
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(24, 20, 24, 24)
        layout.setSpacing(16)

        title = QLabel("Focus Recovery Coach")
        title.setObjectName("title")
        layout.addWidget(title)

        # Eye load indicator
        self.strain_bar = QProgressBar()
        self.strain_bar.setRange(0, 100)
        self.strain_bar.setValue(self.monitor.get_load_percent())
        self.strain_bar.setFormat("Eye Load: %p%")
        layout.addWidget(self.strain_bar)

        self.focus_score_label = QLabel(f"Focus Score: {self.monitor.get_focus_score()}/100")
        layout.addWidget(self.focus_score_label)

        self.recovery_label = QLabel("Next recovery in: {} sec".format(
            self.monitor.get_next_recovery_hint()))
        layout.addWidget(self.recovery_label)

        self.suggestion_label = QLabel(self.monitor.get_recovery_suggestion())
        layout.addWidget(self.suggestion_label)

        # Eye exercise tutorial (placeholder)
        exercise_card = QFrame()
        exercise_card.setObjectName("card")
        apply_card_shadow(exercise_card)
        v = QVBoxLayout()
        v.setSpacing(10)
        header = QLabel("Eye Exercise Guide")
        header.setObjectName("cardTitle")
        v.addWidget(header)
        v.addWidget(QLabel("Try blinking slowly, rolling eyes, and focusing on distant objects."))
        exercise_card.setLayout(v)
        layout.addWidget(exercise_card)

        # Blue light exposure
        self.blue_label = QLabel(f"Blue Light Exposure: {self.monitor.get_blue_light_exposure()} sec")
        layout.addWidget(self.blue_label)

        self.recovery_btn = QPushButton("Start Recovery Session")
        self.recovery_btn.clicked.connect(self.start_recovery)
        layout.addWidget(self.recovery_btn)

        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self._tick)
        self.timer.start()

        layout.addStretch()
        scroll.setWidget(content)
        outer.addWidget(scroll)

    def update_ui(self):
        self.strain_bar.setValue(self.monitor.get_load_percent())
        self.focus_score_label.setText(f"Focus Score: {self.monitor.get_focus_score()}/100")
        if self.monitor.in_recovery:
            self.recovery_label.setText(
                f"Recovery in progress: {self.monitor.recovery_remaining} sec left"
            )
        else:
            self.recovery_label.setText(
                "Next recovery in: {} sec".format(self.monitor.get_next_recovery_hint())
            )
        self.suggestion_label.setText(self.monitor.get_recovery_suggestion())
        self.blue_label.setText(f"Blue Light Exposure: {self.monitor.get_blue_light_exposure()} sec")

    def refresh(self):
        self.update_ui()

    def _tick(self):
        self.monitor.update_time(1)
        self.update_ui()

    def start_recovery(self):
        self.monitor.start_recovery()
        self.update_ui()
