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
from core.smart_notifier import SmartNotifier

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ScreenGuard")
        self.resize(900, 550)

        layout = QHBoxLayout(self)

        self.notifier = SmartNotifier()

        self.stack = QStackedWidget()
        self.pages = {
            "dashboard": DashboardPage(),
            "reports": ReportsPage(),
            "settings": SettingsPage(self.notifier, theme_callback=self.apply_theme),
            "health": HealthPage(),
            "achievements": AchievementsPage(),
            "social": SocialPage(),
            "well-being": WellBeingPage()
        }

        for p in self.pages.values():
            self.stack.addWidget(p)

        self.sidebar = Sidebar(
            self.switch_page,
            extra_pages=["Health", "Achievements", "Social", "Well-Being"]
        )
        layout.addWidget(self.sidebar)
        layout.addWidget(self.stack)

        self.apply_theme("night")
        self.sidebar.set_active("dashboard")

    def switch_page(self, name):
        self.stack.setCurrentWidget(self.pages[name])
        self.sidebar.set_active(name)
        page = self.pages.get(name)
        if page and hasattr(page, "refresh"):
            page.refresh()

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
