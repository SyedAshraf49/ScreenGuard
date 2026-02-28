import sys
from PyQt6.QtWidgets import QApplication, QWidget, QHBoxLayout, QStackedWidget
from ui.sidebar import Sidebar
from ui.dashboard import DashboardPage
from ui.reports import ReportsPage
from ui.settings import SettingsPage
from ui.health import HealthPage
from ui.achievements import AchievementsPage
from ui.social import SocialPage
from ui.well_being import WellBeingPage
from ui.locker import LockerPage
from core.smart_notifier import SmartNotifier
from core.app_locker import make_locker
from backend.db import init_db

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ScreenGuard")
        self.resize(900, 550)

        layout = QHBoxLayout(self)

        init_db()
        self.notifier = SmartNotifier()

        self.stack = QStackedWidget()
        self.pages = {
            "dashboard": DashboardPage(),
            "reports": ReportsPage(),
            "settings": SettingsPage(self.notifier, theme_callback=self.apply_theme),
            "health": HealthPage(),
            "achievements": AchievementsPage(),
            "social": SocialPage(),
            "well-being": WellBeingPage(),
            "locker": LockerPage(),
        }

        for p in self.pages.values():
            self.stack.addWidget(p)

        self.sidebar = Sidebar(
            self.switch_page,
            extra_pages=["Health", "Achievements", "Social", "Well-Being", "Locker"]
        )
        layout.addWidget(self.sidebar)
        layout.addWidget(self.stack)

        # Start background app-locker enforcement
        self._app_locker = make_locker(
            on_locked_fn=lambda app: self.notifier.notify(
                f"{app} is locked — time limit reached.", urgency="high"
            )
            if hasattr(self.notifier, "notify")
            else None
        )
        self._app_locker.start()

        self.apply_theme("night")
        self.sidebar.set_active("dashboard")

    def switch_page(self, name):
        self.stack.setCurrentWidget(self.pages[name])
        self.sidebar.set_active(name)
        page = self.pages.get(name)
        if page and hasattr(page, "refresh"):
            page.refresh()

    def closeEvent(self, event):  # noqa: N802
        self._app_locker.stop()
        super().closeEvent(event)

    def apply_theme(self, theme_name):
        theme = (theme_name or "night").strip().lower()
        if theme not in ["day", "night", "aurora", "sunset", "mono"]:
            theme = "night"
        qss_path = f"ui/themes/{theme}.qss"
        try:
            with open(qss_path, "r") as f:
                QApplication.instance().setStyleSheet(f.read())
        except Exception:
            pass

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
