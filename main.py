"""
Devil ERP — Main Entry Point
Developed by Devil One Pvt Ltd & Nexuzy Lab
Lead Developer: David K. Angel
Contact: devilonepvtltd@gmail.com | nexuzylab@gmail.com
"""

import sys
import os
from pathlib import Path

# ── Ensure project root is on path ──────────────────────────
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

def check_first_run():
    """Check if AI models need to be downloaded on first run."""
    models_dir = BASE_DIR / "models"
    models_dir.mkdir(exist_ok=True)
    marker = models_dir / ".initialized"
    return not marker.exists()

def launch_app():
    from PySide6.QtWidgets import QApplication
    from PySide6.QtGui import QIcon
    from ui.splash import SplashScreen
    from ui.main_window import MainWindow
    from auth.firebase_auth import FirebaseAuth

    app = QApplication(sys.argv)
    app.setApplicationName("Devil ERP")
    app.setOrganizationName("Devil One Pvt Ltd")
    app.setWindowIcon(QIcon(str(BASE_DIR / "assets" / "icon.ico")))

    # Apply global dark theme
    from ui.theme import apply_dark_theme
    apply_dark_theme(app)

    # Show splash screen
    splash = SplashScreen()
    splash.show()
    app.processEvents()

    # First-run AI model setup
    if check_first_run():
        from installer.model_installer import ModelInstaller
        installer = ModelInstaller()
        installer.run()

    # Firebase login
    auth = FirebaseAuth()
    if not auth.is_logged_in():
        from ui.login_screen import LoginScreen
        splash.close()
        login = LoginScreen(auth)
        login.show()
        sys.exit(app.exec())

    splash.close()
    window = MainWindow(auth.current_user())
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    launch_app()
