"""
Devil ERP — POS Module (Tryton sale_point)
Developed by Devil One Pvt Ltd & Nexuzy Lab
Lead Developer: David K. Angel

Features: POS session, Quick billing, Barcode scan,
Thermal print, Cash drawer, Shift management
"""
from database.db_manager import DBManager
from billing.invoice_manager import InvoiceManager
from billing.payment_handler import PaymentHandler
from datetime import datetime


class POSModule:
    """Point of Sale session management."""

    def __init__(self):
        self.db = DBManager()
        self.invoice_mgr = InvoiceManager()
        self.payment = PaymentHandler()
        self._ensure_tables()
        self.current_session = None

    def _ensure_tables(self):
        conn = self.db.get_connection()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS pos_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cashier TEXT NOT NULL,
                open_time TEXT NOT NULL,
                close_time TEXT,
                opening_cash REAL DEFAULT 0,
                closing_cash REAL DEFAULT 0,
                total_sales REAL DEFAULT 0,
                total_transactions INTEGER DEFAULT 0,
                status TEXT DEFAULT 'open'
            )
        """)
        conn.commit()
        conn.close()

    def open_session(self, cashier: str, opening_cash: float = 0) -> dict:
        conn = self.db.get_connection()
        cur = conn.cursor()
        # Check if already open
        cur.execute("SELECT id FROM pos_sessions WHERE cashier=? AND status='open'", (cashier,))
        existing = cur.fetchone()
        if existing:
            conn.close()
            return {"success": True, "session_id": existing[0], "message": "Session already open"}
        try:
            cur.execute("""
                INSERT INTO pos_sessions (cashier, open_time, opening_cash, status)
                VALUES (?,?,?,?)
            """, (cashier, datetime.now().isoformat(), opening_cash, "open"))
            conn.commit()
            session_id = cur.lastrowid
            self.current_session = session_id
            return {"success": True, "session_id": session_id}
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            conn.close()

    def close_session(self, session_id: int, closing_cash: float = 0) -> dict:
        conn = self.db.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                UPDATE pos_sessions
                SET close_time=?, closing_cash=?, status='closed'
                WHERE id=?
            """, (datetime.now().isoformat(), closing_cash, session_id))
            conn.commit()
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            conn.close()

    def quick_bill(self, customer_id: int, items: list,
                   payment_mode: str = "cash", cashier: str = "") -> dict:
        """One-step POS billing: create invoice + record payment."""
        from tryton_modules.account_invoice import InvoiceModule
        inv_mod = InvoiceModule()
        result = inv_mod.create_invoice(
            customer_id=customer_id,
            invoice_type="retail",
            items=items
        )
        if not result["success"]:
            return result
        pay_result = self.payment.record_payment(
            invoice_id=result["invoice_id"],
            amount=result["grand_total"],
            mode=payment_mode
        )
        # Update session totals
        if self.current_session:
            conn = self.db.get_connection()
            cur = conn.cursor()
            cur.execute("""
                UPDATE pos_sessions
                SET total_sales=total_sales+?, total_transactions=total_transactions+1
                WHERE id=?
            """, (result["grand_total"], self.current_session))
            conn.commit()
            conn.close()
        return {**result, "payment": pay_result}
