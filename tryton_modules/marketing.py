"""
Devil ERP — Marketing Module (Tryton marketing)
Developed by Devil One Pvt Ltd & Nexuzy Lab
Lead Developer: David K. Angel

Features: Campaigns, Promotions, Customer segments,
Discount codes, Marketing analytics
"""
from database.db_manager import DBManager
from datetime import datetime


class MarketingModule:
    """Marketing campaigns and promotions."""

    def __init__(self):
        self.db = DBManager()
        self._ensure_tables()

    def _ensure_tables(self):
        conn = self.db.get_connection()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS campaigns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                campaign_type TEXT DEFAULT 'promotion',
                start_date TEXT,
                end_date TEXT,
                budget REAL DEFAULT 0,
                spent REAL DEFAULT 0,
                status TEXT DEFAULT 'active',
                notes TEXT DEFAULT '',
                created_at TEXT
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS discount_codes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                discount_type TEXT DEFAULT 'percent',
                discount_value REAL NOT NULL,
                min_order_value REAL DEFAULT 0,
                max_uses INTEGER DEFAULT 0,
                used_count INTEGER DEFAULT 0,
                valid_from TEXT,
                valid_to TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TEXT
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS customer_segments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                criteria TEXT DEFAULT '{}',
                customer_count INTEGER DEFAULT 0,
                created_at TEXT
            )
        """)
        conn.commit()
        conn.close()

    def create_campaign(self, name: str, campaign_type: str = "promotion",
                        start_date: str = None, end_date: str = None,
                        budget: float = 0, notes: str = "") -> dict:
        conn = self.db.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                INSERT INTO campaigns (name, campaign_type, start_date, end_date, budget, notes, created_at)
                VALUES (?,?,?,?,?,?,?)
            """, (name, campaign_type, start_date, end_date, budget, notes,
                  datetime.now().isoformat()))
            conn.commit()
            return {"success": True, "campaign_id": cur.lastrowid}
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            conn.close()

    def create_discount_code(self, code: str, discount_type: str = "percent",
                             discount_value: float = 10,
                             min_order_value: float = 0,
                             valid_from: str = None, valid_to: str = None,
                             max_uses: int = 100) -> dict:
        conn = self.db.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                INSERT INTO discount_codes
                (code, discount_type, discount_value, min_order_value,
                 max_uses, valid_from, valid_to, created_at)
                VALUES (?,?,?,?,?,?,?,?)
            """, (code.upper(), discount_type, discount_value, min_order_value,
                  max_uses, valid_from, valid_to, datetime.now().isoformat()))
            conn.commit()
            return {"success": True, "code": code.upper()}
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            conn.close()

    def validate_discount_code(self, code: str, order_value: float = 0) -> dict:
        conn = self.db.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM discount_codes WHERE code=? AND is_active=1", (code.upper(),))
        dc = cur.fetchone()
        conn.close()
        if not dc:
            return {"valid": False, "error": "Invalid or inactive code"}
        dc = dict(dc)
        if dc["max_uses"] > 0 and dc["used_count"] >= dc["max_uses"]:
            return {"valid": False, "error": "Code usage limit reached"}
        if order_value < dc["min_order_value"]:
            return {"valid": False, "error": f"Minimum order value \u20b9{dc['min_order_value']} required"}
        discount = dc["discount_value"] if dc["discount_type"] == "flat" else round(order_value * dc["discount_value"] / 100, 2)
        return {"valid": True, "discount_amount": discount, "code": dc}
