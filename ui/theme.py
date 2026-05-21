"""
Devil ERP — Global Dark Theme
Inspired by: Tally Prime + VS Code + Modern POS
"""

DARK_THEME = """
QWidget {
    background-color: #1e1e2e;
    color: #cdd6f4;
    font-family: 'Segoe UI', 'Noto Sans', Arial, sans-serif;
    font-size: 13px;
}

QMainWindow {
    background-color: #181825;
}

QPushButton {
    background-color: #89b4fa;
    color: #1e1e2e;
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: bold;
}

QPushButton:hover {
    background-color: #74c7ec;
}

QPushButton:pressed {
    background-color: #cba6f7;
}

QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {
    background-color: #313244;
    border: 1px solid #45475a;
    border-radius: 4px;
    padding: 6px;
    color: #cdd6f4;
}

QTableWidget {
    background-color: #1e1e2e;
    alternate-background-color: #2a2a3e;
    border: 1px solid #45475a;
    gridline-color: #313244;
}

QTableWidget::item:selected {
    background-color: #89b4fa;
    color: #1e1e2e;
}

QHeaderView::section {
    background-color: #313244;
    color: #89b4fa;
    padding: 6px;
    border: none;
    font-weight: bold;
}

QMenuBar {
    background-color: #181825;
    color: #cdd6f4;
}

QMenuBar::item:selected {
    background-color: #313244;
}

QStatusBar {
    background-color: #181825;
    color: #a6adc8;
}

QScrollBar:vertical {
    background: #1e1e2e;
    width: 8px;
}

QScrollBar::handle:vertical {
    background: #45475a;
    border-radius: 4px;
}
"""

def apply_dark_theme(app):
    app.setStyleSheet(DARK_THEME)
