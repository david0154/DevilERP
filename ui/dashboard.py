"""
Devil ERP — Main Dashboard
Developed by Devil One Pvt Ltd & Nexuzy Lab
Lead Developer: David K. Angel
Contact: nexuzylab@gmail.com | devilonepvtltd@gmail.com
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QGridLayout, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QPixmap
from pathlib import Path
from about import APP_NAME, APP_VERSION, LEAD_DEVELOPER

BASE_DIR = Path(__file__).resolve().parent.parent


class DashboardCard(QFrame):
    def __init__(self, title, value, subtitle, color="#4CAF50", parent=None):
        super().__init__(parent)
        self.setFixedSize(210, 115)
        self.setStyleSheet(f"""
            QFrame {{
                background: #1a1a2e;
                border: 1px solid {color};
                border-radius: 12px;
                padding: 10px;
            }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        t = QLabel(title)
        t.setStyleSheet(f"color: {color}; font-size: 11px; font-weight: bold;")
        v = QLabel(str(value))
        v.setStyleSheet("color: #ffffff; font-size: 24px; font-weight: bold;")
        s = QLabel(subtitle)
        s.setStyleSheet("color: #666; font-size: 10px;")
        layout.addWidget(t)
        layout.addWidget(v)
        layout.addWidget(s)


class Dashboard(QWidget):
    def __init__(self, user=None, parent=None):
        super().__init__(parent)
        self.user = user
        self._build_ui()
        self._refresh_timer = QTimer(self)
        self._refresh_timer.timeout.connect(self._load_stats)
        self._refresh_timer.start(30000)
        self._load_stats()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(18)

        # Header
        header = QHBoxLayout()
        logo_path = BASE_DIR / "assets" / "logo.jpg"
        if logo_path.exists():
            logo_lbl = QLabel()
            pix = QPixmap(str(logo_path)).scaled(40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_lbl.setPixmap(pix)
            header.addWidget(logo_lbl)
        title = QLabel(f"{APP_NAME}  —  Dashboard")
        title.setStyleSheet("color:#e0e0e0; font-size:18px; font-weight:bold; margin-left:8px;")
        version = QLabel(f"v{APP_VERSION}  |  {LEAD_DEVELOPER}")
        version.setStyleSheet("color:#555; font-size:11px;")
        header.addWidget(title)
        header.addStretch()
        header.addWidget(version)
        root.addLayout(header)

        # Stat cards
        self.cards_grid = QGridLayout()
        self.cards_grid.setSpacing(16)
        root.addLayout(self.cards_grid)

        # Quick actions
        action_label = QLabel("Quick Actions")
        action_label.setStyleSheet("color:#888; font-size:12px; font-weight:bold; margin-top:8px;")
        root.addWidget(action_label)

        actions = QHBoxLayout()
        actions.setSpacing(10)
        self._action_btns = {}
        for label, color in [
            ("🧾 New Bill", "#2196F3"),
            ("📦 Stock In", "#4CAF50"),
            ("👤 Customer", "#FF9800"),
            ("📊 Reports", "#9C27B0"),
            ("🔍 Scan Bill", "#F44336"),
            ("☁ Backup", "#00BCD4"),
        ]:
            btn = QPushButton(label)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {color}18;
                    color: {color};
                    border: 1px solid {color}55;
                    border-radius: 7px;
                    padding: 9px 14px;
                    font-size: 12px;
                }}
                QPushButton:hover {{ background: {color}35; }}
            """)
            actions.addWidget(btn)
            self._action_btns[label] = btn
        root.addLayout(actions)
        root.addStretch()

        # Footer
        footer = QLabel("Devil One Pvt Ltd  |  Nexuzy Lab  |  nexuzylab@gmail.com  |  devilonepvtltd@gmail.com")
        footer.setStyleSheet("color:#333; font-size:10px; margin-top:6px;")
        footer.setAlignment(Qt.AlignCenter)
        root.addWidget(footer)

    def _load_stats(self):
        try:
            from database.db_manager import DBManager
            db = DBManager()
            conn = db.get_connection()
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM invoices WHERE DATE(created_at)=DATE('now')")
            today_bills = cur.fetchone()[0]
            cur.execute("SELECT COALESCE(SUM(total_amount),0) FROM invoices WHERE DATE(created_at)=DATE('now')")
            today_sales = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM products WHERE stock_qty <= reorder_level")
            low_stock = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM invoices WHERE payment_status='unpaid'")
            unpaid = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM customers")
            total_customers = cur.fetchone()[0]
            cur.execute("SELECT COALESCE(SUM(total_amount),0) FROM invoices WHERE strftime('%Y-%m', created_at)=strftime('%Y-%m','now')")
            monthly_sales = cur.fetchone()[0]
            conn.close()
        except Exception:
            today_bills = today_sales = low_stock = unpaid = total_customers = monthly_sales = 0

        # Clear
        for i in reversed(range(self.cards_grid.count())):
            w = self.cards_grid.itemAt(i).widget()
            if w:
                w.deleteLater()

        cards = [
            ("Today's Bills", today_bills, "invoices raised", "#2196F3"),
            ("Today's Sales", f"\u20b9{today_sales:,.2f}", "revenue today", "#4CAF50"),
            ("Low Stock", low_stock, "need reorder", "#FF5722"),
            ("Unpaid Invoices", unpaid, "pending payment", "#FF9800"),
            ("Total Customers", total_customers, "registered", "#9C27B0"),
            ("Monthly Sales", f"\u20b9{monthly_sales:,.2f}", "this month", "#00BCD4"),
        ]
        for i, (t, v, s, c) in enumerate(cards):
            card = DashboardCard(t, v, s, c)
            row, col = divmod(i, 3)
            self.cards_grid.addWidget(card, row, col)
