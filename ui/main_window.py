"""
Devil ERP — Main Application Window
Tally-style navigation with module panels.
"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QPushButton, QFrame, QStackedWidget, QStatusBar
)
from PySide6.QtGui import QIcon, QFont, QPixmap
from PySide6.QtCore import Qt
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

MODULES = [
    ("🏠", "Dashboard"),
    ("💰", "Accounting"),
    ("📦", "Inventory"),
    ("🛒", "Sales"),
    ("🏭", "Purchase"),
    ("🧾", "Billing / POS"),
    ("🤖", "AI Scanner"),
    ("📈", "AI Analytics"),
    ("👥", "HR"),
    ("📋", "Reports"),
    ("☁️", "Backup"),
    ("⚙️", "Settings"),
]

class MainWindow(QMainWindow):
    def __init__(self, user: dict):
        super().__init__()
        self.user = user
        self.setWindowTitle(f"Devil ERP  —  {user.get('email', '')}  [{user.get('role', 'user').upper()}]")
        self.setWindowIcon(QIcon(str(BASE_DIR / "assets" / "icon.ico")))
        self.resize(1280, 800)
        self._build_ui()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Sidebar ───────────────────────────────────────
        sidebar = QFrame()
        sidebar.setFixedWidth(200)
        sidebar.setStyleSheet("background-color: #181825; border-right: 1px solid #313244;")
        side_layout = QVBoxLayout(sidebar)
        side_layout.setContentsMargins(0, 0, 0, 0)
        side_layout.setSpacing(0)

        # Logo in sidebar
        logo_label = QLabel()
        logo_path = BASE_DIR / "assets" / "logo.png"
        if logo_path.exists():
            pix = QPixmap(str(logo_path)).scaled(160, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_label.setPixmap(pix)
        else:
            logo_label.setText("🐉 Devil ERP")
            logo_label.setStyleSheet("color: #89b4fa; font-size: 14px; font-weight: bold; padding: 16px;")
        logo_label.setAlignment(Qt.AlignCenter)
        logo_label.setFixedHeight(80)
        side_layout.addWidget(logo_label)

        self.stack = QStackedWidget()

        for icon, name in MODULES:
            btn = QPushButton(f"  {icon}  {name}")
            btn.setFixedHeight(44)
            btn.setStyleSheet("""
                QPushButton {
                    text-align: left;
                    padding-left: 16px;
                    border: none;
                    background: transparent;
                    color: #a6adc8;
                    font-size: 13px;
                }
                QPushButton:hover {
                    background-color: #313244;
                    color: #cdd6f4;
                }
            """)
            page = QLabel(f"{icon}  {name}\n\nModule Coming Soon")
            page.setAlignment(Qt.AlignCenter)
            page.setStyleSheet("color: #6c7086; font-size: 16px;")
            self.stack.addWidget(page)
            idx = self.stack.count() - 1
            btn.clicked.connect(lambda checked, i=idx: self.stack.setCurrentIndex(i))
            side_layout.addWidget(btn)

        side_layout.addStretch()

        user_info = QLabel(f"👤 {self.user.get('role', 'user').capitalize()}")
        user_info.setAlignment(Qt.AlignCenter)
        user_info.setStyleSheet("color: #6c7086; font-size: 11px; padding: 12px;")
        side_layout.addWidget(user_info)

        root.addWidget(sidebar)
        root.addWidget(self.stack)

        # Status bar
        status = QStatusBar()
        status.showMessage("Devil ERP  |  Devil One Pvt Ltd & Nexuzy Lab  |  Lead Dev: David K. Angel  |  nexuzylab@gmail.com")
        self.setStatusBar(status)
