"""
Devil ERP — Splash Screen
Shown during application startup with branding.
"""

from PySide6.QtWidgets import QSplashScreen, QLabel, QVBoxLayout, QWidget
from PySide6.QtGui import QPixmap, QColor, QFont
from PySide6.QtCore import Qt
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

class SplashScreen(QSplashScreen):
    def __init__(self):
        logo_path = BASE_DIR / "assets" / "logo.png"
        if logo_path.exists():
            pixmap = QPixmap(str(logo_path)).scaled(400, 250, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        else:
            pixmap = QPixmap(400, 250)
            pixmap.fill(QColor("#1e1e2e"))
        super().__init__(pixmap)
        self.setWindowFlag(Qt.WindowStaysOnTopHint)
        self.showMessage(
            "🐉 Devil ERP  |  Loading...",
            Qt.AlignBottom | Qt.AlignCenter,
            QColor("#89b4fa")
        )
