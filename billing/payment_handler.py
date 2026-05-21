"""
Devil ERP — Payment Handler
Modes: Cash, UPI, Card, Bank Transfer, Credit
Developed by Devil One Pvt Ltd & Nexuzy Lab
Lead Developer: David K. Angel
"""
from database.db_manager import DBManager
from datetime import datetime

PAYMENT_MODES = ["cash", "upi", "card", "bank_transfer", "credit"]


class PaymentHandler:
    def __init__(self):
        self.db = DBManager()
        self._ensure_table()

    def _ensure_table(self):
        conn = self.db.get_connection()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                mode TEXT NOT NULL,
                reference TEXT DEFAULT '',
                notes TEXT DEFAULT '',
                created_at TEXT NOT NULL
            )
        """)
        conn.commit()
        conn.close()

    def record_payment(self, invoice_id: int, amount: float,
                       mode: str, reference: str = "", notes: str = "") -> dict:
        if mode not in PAYMENT_MODES:
            return {"success": False, "error": f"Invalid payment mode: {mode}"}
        if amount <= 0:
            return {"success": False, "error": "Amount must be positive"}

        conn = self.db.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                INSERT INTO payments (invoice_id, amount, mode, reference, notes, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (invoice_id, amount, mode, reference, notes, datetime.now().isoformat()))
            cur.execute("""
                UPDATE invoices SET
                    paid_amount = COALESCE(paid_amount, 0) + ?,
                    payment_status = CASE
                        WHEN COALESCE(paid_amount, 0) + ? >= total_amount THEN 'paid'
                        ELSE 'partial'
                    END
                WHERE id = ?
            """, (amount, amount, invoice_id))
            conn.commit()
            return {"success": True, "payment_id": cur.lastrowid}
        except Exception as e:
            conn.rollback()
            return {"success": False, "error": str(e)}
        finally:
            conn.close()

    def get_payment_history(self, invoice_id: int) -> list:
        conn = self.db.get_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM payments WHERE invoice_id=? ORDER BY created_at DESC",
            (invoice_id,)
        )
        rows = cur.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_daily_collection(self, date: str = None) -> dict:
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")
        conn = self.db.get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT mode, SUM(amount) as total
            FROM payments WHERE DATE(created_at) = ?
            GROUP BY mode
        """, (date,))
        rows = cur.fetchall()
        conn.close()
        return {r["mode"]: r["total"] for r in rows}

    def get_unpaid_invoices(self) -> list:
        conn = self.db.get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT i.*, c.name as customer_name
            FROM invoices i
            LEFT JOIN customers c ON i.customer_id = c.id
            WHERE i.payment_status IN ('unpaid','partial')
            ORDER BY i.created_at DESC
        """)
        rows = cur.fetchall()
        conn.close()
        return [dict(r) for r in rows]
