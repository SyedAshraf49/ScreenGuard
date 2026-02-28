from PyQt6.QtCore import QSize
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QStyle, QButtonGroup

class Sidebar(QWidget):
    def __init__(self, switch, extra_pages=None):
        super().__init__()
        self.setObjectName("sidebar")
        self.setFixedWidth(180)
        layout = QVBoxLayout()
        layout.setContentsMargins(12, 16, 12, 16)
        layout.setSpacing(10)

        self.button_group = QButtonGroup(self)
        self.button_group.setExclusive(True)
        self.buttons = {}

        page_names = ["Dashboard", "Reports"]
        if extra_pages:
            page_names += extra_pages
        page_names += ["Settings"]

        icon_map = {
            "dashboard": QStyle.StandardPixmap.SP_ComputerIcon,
            "reports": QStyle.StandardPixmap.SP_FileDialogDetailedView,
            "settings": QStyle.StandardPixmap.SP_FileDialogContentsView,
            "health": QStyle.StandardPixmap.SP_MediaPlay,
            "achievements": QStyle.StandardPixmap.SP_DialogApplyButton,
            "social": QStyle.StandardPixmap.SP_DirIcon,
            "well-being": QStyle.StandardPixmap.SP_MessageBoxInformation,
            "locker": QStyle.StandardPixmap.SP_MessageBoxWarning,
        }

        for name in page_names:
            btn = QPushButton(name)
            btn.setObjectName("sidebarButton")
            btn.setCheckable(True)
            key = name.lower()
            icon_id = icon_map.get(key)
            if icon_id is not None:
                btn.setIcon(self.style().standardIcon(icon_id))
                btn.setIconSize(QSize(16, 16))
            btn.clicked.connect(lambda _, n=name.lower(): switch(n))
            btn.setMinimumHeight(36)
            self.button_group.addButton(btn)
            self.buttons[key] = btn
            layout.addWidget(btn)

        layout.addStretch()
        self.setLayout(layout)

    def set_active(self, name):
        key = (name or "").lower()
        btn = self.buttons.get(key)
        if btn is not None:
            btn.setChecked(True)
