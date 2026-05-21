"""
Devil ERP — Login Screen
Firebase email/password login with role display.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QMessageBox, QFrame
)
from PySide6.QtGui import QPixmap, QFont, QIcon
from PySide6.QtCore import Qt
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

class LoginScreen(QWidget):
    def __init__(self, auth):
        super().__init__()
        self.auth = auth
        self.setWindowTitle("Devil ERP — Login")
        self.setWindowIcon(QIcon(str(BASE_DIR / "assets" / "icon.ico")))
        self.setFixedSize(420, 500)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(16)

        # Logo
        logo_label = QLabel()
        logo_path = BASE_DIR / "assets" / "logo.png"
        if logo_path.exists():
            pixmap = QPixmap(str(logo_path)).scaled(120, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_label.setPixmap(pixmap)
        else:
            logo_label.setText("🐉")
            logo_label.setFont(QFont("Arial", 36))
        logo_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(logo_label)

        title = QLabel("Devil ERP")
        title.setFont(QFont("Segoe UI", 22, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #89b4fa;")
        layout.addWidget(title)

        subtitle = QLabel("Devil One Pvt Ltd · Nexuzy Lab")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: #6c7086; font-size: 11px;")
        layout.addWidget(subtitle)

        layout.addSpacing(10)

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Email address")
        layout.addWidget(self.email_input)

        self.pass_input = QLineEdit()
        self.pass_input.setPlaceholderText("Password")
        self.pass_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.pass_input)

        login_btn = QPushButton("Login")
        login_btn.setFixedHeight(42)
        login_btn.clicked.connect(self._do_login)
        layout.addWidget(login_btn)

        forgot_btn = QPushButton("Forgot Password?")
        forgot_btn.setFlat(True)
        forgot_btn.setStyleSheet("color: #89b4fa; text-decoration: underline; background: transparent;")
        forgot_btn.clicked.connect(self._forgot_password)
        layout.addWidget(forgot_btn, alignment=Qt.AlignCenter)

        footer = QLabel("Lead Developer: David K. Angel  |  nexuzylab@gmail.com")
        footer.setAlignment(Qt.AlignCenter)
        footer.setStyleSheet("color: #45475a; font-size: 10px;")
        layout.addWidget(footer)

    def _do_login(self):
        email = self.email_input.text().strip()
        password = self.pass_input.text()
        if not email or not password:
            QMessageBox.warning(self, "Login", "Please enter email and password.")
            return
        result = self.auth.login(email, password)
        if result.get("success"):
            from ui.main_window import MainWindow
            self._main = MainWindow(result["user"])
            self._main.show()
            self.close()
        else:
            QMessageBox.critical(self, "Login Failed", result.get("error", "Invalid credentials."))

    def _forgot_password(self):
        email = self.email_input.text().strip()
        if not email:
            QMessageBox.warning(self, "Reset Password", "Enter your email first.")
            return
        result = self.auth.reset_password(email)
        if result.get("success"):
            QMessageBox.information(self, "Reset Password", f"Password reset email sent to {email}")
        else:
            QMessageBox.critical(self, "Error", result.get("error", "Failed to send reset email."))
