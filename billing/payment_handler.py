"""
Devil ERP — Payment Handler (Cash, UPI, Card, Bank Transfer, Credit)
Developed by Devil One Pvt Ltd & Nexuzy Lab
Lead Developer: David K. Angel
Contact: nexuzylab@gmail.com | devilonepvtltd@gmail.com
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
                created_at TEXT NOT NULL,
                FOREIGN KEY(invoice_id) REFERENCES invoices(id)
            )
        """)
        conn.commit()
        conn.close()

    def record_payment(self, invoice_id: int, amount: float, mode: str,
                       reference: str = "", notes: str = "") -> dict:
        if mode not in PAYMENT_MODES:
            return {"success": False, "error": f"Invalid mode: {mode}. Valid: {PAYMENT_MODES}"}
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
                UPDATE invoices
                SET paid_amount = COALESCE(paid_amount, 0) + ?,
                    payment_status = CASE
                        WHEN COALESCE(paid_amount, 0) + ? >= total_amount THEN 'paid'
                        ELSE 'partial'
                    END,
                    payment_mode = ?
                WHERE id = ?
            """, (amount, amount, mode, invoice_id))

            conn.commit()
            return {"success": True, "payment_id": cur.lastrowid, "mode": mode, "amount": amount}
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
            SELECT mode, SUM(amount) as total, COUNT(*) as count
            FROM payments WHERE DATE(created_at) = ?
            GROUP BY mode
        """, (date,))
        rows = cur.fetchall()
        conn.close()
        return {r["mode"]: {"total": r["total"], "count": r["count"]} for r in rows}

    def get_monthly_summary(self, year: int = None, month: int = None) -> dict:
        now = datetime.now()
        year = year or now.year
        month = month or now.month
        period = f"{year}-{month:02d}"
        conn = self.db.get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT mode, SUM(amount) as total FROM payments
            WHERE strftime('%Y-%m', created_at) = ?
            GROUP BY mode
        """, (period,))
        rows = cur.fetchall()
        conn.close()
        return {r["mode"]: r["total"] for r in rows}

    def refund_payment(self, invoice_id: int, refund_amount: float, reason: str = "") -> dict:
        return self.record_payment(
            invoice_id, -abs(refund_amount), "refund", notes=f"REFUND: {reason}"
        )
