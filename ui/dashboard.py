"""
Devil ERP — Main Dashboard
Developed by Devil One Pvt Ltd & Nexuzy Lab
Lead Developer: David K. Angel
Contact: nexuzylab@gmail.com | devilonepvtltd@gmail.com
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QGridLayout, QFrame, QScrollArea, QSizePolicy
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QPixmap
from pathlib import Path
from about import APP_NAME, APP_VERSION, LEAD_DEVELOPER, LAB

ASSETS = Path(__file__).resolve().parent.parent / "assets"


class DashboardCard(QFrame):
    def __init__(self, title: str, value: str, subtitle: str,
                 color: str = "#4CAF50", icon: str = "", parent=None):
        super().__init__(parent)
        self.setFixedSize(210, 115)
        self.setStyleSheet(f"""
            QFrame {{
                background: #1a1a2e;
                border: 1px solid {color}55;
                border-left: 4px solid {color};
                border-radius: 10px;
            }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(2)

        top = QHBoxLayout()
        t = QLabel(f"{icon}  {title}" if icon else title)
        t.setStyleSheet(f"color: {color}; font-size: 11px; font-weight: bold; background:transparent;")
        top.addWidget(t)
        top.addStretch()
        layout.addLayout(top)

        v = QLabel(str(value))
        v.setStyleSheet("color: #ffffff; font-size: 24px; font-weight: bold; background:transparent;")
        layout.addWidget(v)

        s = QLabel(subtitle)
        s.setStyleSheet("color: #888; font-size: 10px; background:transparent;")
        layout.addWidget(s)


class Dashboard(QWidget):
    def __init__(self, user: dict = None, parent=None):
        super().__init__(parent)
        self.user = user or {}
        self._build_ui()
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._load_stats)
        self._timer.start(30_000)
        self._load_stats()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(16)

        # ── Header ───────────────────────────────────────────
        header = QHBoxLayout()
        logo_label = QLabel()
        logo_path = ASSETS / "logo.png"
        if logo_path.exists():
            pix = QPixmap(str(logo_path)).scaledToHeight(42, Qt.SmoothTransformation)
            logo_label.setPixmap(pix)
        header.addWidget(logo_label)

        title_block = QVBoxLayout()
        t1 = QLabel(APP_NAME)
        t1.setStyleSheet("color:#e0e0e0; font-size:20px; font-weight:bold;")
        t2 = QLabel(f"{LAB}  ·  v{APP_VERSION}  ·  {LEAD_DEVELOPER}")
        t2.setStyleSheet("color:#666; font-size:10px;")
        title_block.addWidget(t1)
        title_block.addWidget(t2)
        header.addLayout(title_block)
        header.addStretch()

        role = self.user.get("role", "employee").capitalize()
        user_info = QLabel(f"👤  {self.user.get('name', 'User')}  |  {role}")
        user_info.setStyleSheet("color:#aaa; font-size:11px;")
        header.addWidget(user_info)
        root.addLayout(header)

        # ── Stats Cards ─────────────────────────────────────
        self.cards_layout = QGridLayout()
        self.cards_layout.setSpacing(14)
        root.addLayout(self.cards_layout)

        # ── Quick Actions ────────────────────────────────────
        ql = QLabel("  Quick Actions")
        ql.setStyleSheet("color:#aaa; font-size:12px; margin-top:8px;")
        root.addWidget(ql)

        actions = QHBoxLayout()
        quick_btns = [
            ("🧾  New Bill",   "#2196F3", "billing"),
            ("📦  Add Stock",  "#4CAF50", "inventory"),
            ("👤  Customer",   "#FF9800", "crm"),
            ("📊  Reports",    "#9C27B0", "reports"),
            ("☁️  Backup",     "#00BCD4", "backup"),
            ("🤖  AI Scan",    "#E91E63", "ocr"),
        ]
        for label, color, _ in quick_btns:
            btn = QPushButton(label)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {color}18;
                    color: {color};
                    border: 1px solid {color}66;
                    border-radius: 7px;
                    padding: 8px 14px;
                    font-size: 12px;
                }}
                QPushButton:hover {{ background: {color}33; }}
            """)
            actions.addWidget(btn)
        root.addLayout(actions)
        root.addStretch()

    def _load_stats(self):
        try:
            from database.db_manager import DBManager
            db = DBManager()
            conn = db.get_connection()
            cur = conn.cursor()

            def q(sql, params=()):
                try:
                    cur.execute(sql, params)
                    r = cur.fetchone()
                    return r[0] if r else 0
                except Exception:
                    return 0

            today_bills  = q("SELECT COUNT(*) FROM invoices WHERE DATE(created_at)=DATE('now')")
            today_sales  = q("SELECT COALESCE(SUM(total_amount),0) FROM invoices WHERE DATE(created_at)=DATE('now')")
            low_stock    = q("SELECT COUNT(*) FROM products WHERE stock_qty <= reorder_level")
            unpaid       = q("SELECT COUNT(*) FROM invoices WHERE payment_status='unpaid'")
            total_cust   = q("SELECT COUNT(*) FROM customers")
            month_sales  = q("SELECT COALESCE(SUM(total_amount),0) FROM invoices WHERE strftime('%Y-%m',created_at)=strftime('%Y-%m','now')")
            conn.close()
        except Exception:
            today_bills = today_sales = low_stock = unpaid = total_cust = month_sales = 0

        stats = [
            ("Today's Bills",   str(today_bills),             "invoices raised today", "#2196F3", "🧾"),
            ("Today's Sales",   f"₹{today_sales:,.2f}",       "total revenue today",   "#4CAF50", "💰"),
            ("Month Sales",     f"₹{month_sales:,.2f}",       "this month's revenue",  "#00BCD4", "📅"),
            ("Low Stock",       str(low_stock),               "items need reorder",    "#FF5722", "📦"),
            ("Unpaid Invoices", str(unpaid),                  "pending payment",       "#FF9800", "⏳"),
            ("Customers",       str(total_cust),              "total customers",       "#9C27B0", "👥"),
        ]

        # Clear old cards
        for i in reversed(range(self.cards_layout.count())):
            w = self.cards_layout.itemAt(i).widget()
            if w:
                w.deleteLater()

        cols = 3
        for idx, (title, value, sub, color, icon) in enumerate(stats):
            card = DashboardCard(title, value, sub, color, icon)
            self.cards_layout.addWidget(card, idx // cols, idx % cols)
