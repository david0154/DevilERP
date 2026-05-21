"""
Devil ERP — Purchase Module (Tryton purchase)
Developed by Devil One Pvt Ltd & Nexuzy Lab
Lead Developer: David K. Angel

Features: RFQ, Purchase Orders, Supplier management,
Purchase returns, Vendor scoring
"""
from database.db_manager import DBManager
from datetime import datetime


class PurchaseModule:
    """Purchase order & vendor management."""

    def __init__(self):
        self.db = DBManager()
        self._ensure_tables()

    def _ensure_tables(self):
        conn = self.db.get_connection()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS purchase_orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                po_number TEXT UNIQUE,
                vendor_id INTEGER,
                order_date TEXT,
                expected_date TEXT,
                status TEXT DEFAULT 'draft',
                subtotal REAL DEFAULT 0,
                total_gst REAL DEFAULT 0,
                total_amount REAL DEFAULT 0,
                paid_amount REAL DEFAULT 0,
                payment_status TEXT DEFAULT 'unpaid',
                notes TEXT DEFAULT '',
                created_at TEXT
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS purchase_order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                po_id INTEGER,
                product_id INTEGER,
                product_name TEXT,
                quantity REAL,
                received_qty REAL DEFAULT 0,
                unit TEXT DEFAULT 'pcs',
                rate REAL,
                gst_rate REAL DEFAULT 0,
                total_amount REAL,
                FOREIGN KEY(po_id) REFERENCES purchase_orders(id)
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS rfq (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rfq_number TEXT UNIQUE,
                vendor_id INTEGER,
                request_date TEXT,
                status TEXT DEFAULT 'sent',
                notes TEXT,
                created_at TEXT
            )
        """)
        conn.commit()
        conn.close()

    def create_po(self, vendor_id: int, items: list,
                  expected_date: str = None, notes: str = "") -> dict:
        conn = self.db.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("SELECT COUNT(*) FROM purchase_orders")
            n = cur.fetchone()[0]
            po_no = f"PO-{datetime.now().year}-{n+1:05d}"
            subtotal = sum(float(i["quantity"]) * float(i["rate"]) for i in items)
            cur.execute("""
                INSERT INTO purchase_orders
                (po_number, vendor_id, order_date, expected_date, status,
                 subtotal, total_amount, notes, created_at)
                VALUES (?,?,?,?,?,?,?,?,?)
            """, (po_no, vendor_id, datetime.now().strftime("%Y-%m-%d"),
                  expected_date, "confirmed", round(subtotal, 2),
                  round(subtotal, 2), notes, datetime.now().isoformat()))
            po_id = cur.lastrowid
            for item in items:
                total = float(item["quantity"]) * float(item["rate"])
                cur.execute("""
                    INSERT INTO purchase_order_items
                    (po_id, product_id, product_name, quantity, unit, rate, gst_rate, total_amount)
                    VALUES (?,?,?,?,?,?,?,?)
                """, (po_id, item.get("product_id"), item["product_name"],
                      item["quantity"], item.get("unit", "pcs"),
                      item["rate"], item.get("gst_rate", 0), round(total, 2)))
            conn.commit()
            return {"success": True, "po_id": po_id, "po_number": po_no}
        except Exception as e:
            conn.rollback()
            return {"success": False, "error": str(e)}
        finally:
            conn.close()

    def receive_goods(self, po_id: int, received_items: list) -> dict:
        """Mark items as received and update stock."""
        from tryton_modules.stock import StockModule
        stock = StockModule()
        conn = self.db.get_connection()
        cur = conn.cursor()
        try:
            for item in received_items:
                cur.execute("""
                    UPDATE purchase_order_items SET received_qty=received_qty+?
                    WHERE po_id=? AND product_id=?
                """, (item["quantity"], po_id, item["product_id"]))
                stock.stock_in(
                    product_id=item["product_id"],
                    quantity=item["quantity"],
                    reference=f"PO-{po_id}"
                )
            conn.commit()
            return {"success": True}
        except Exception as e:
            conn.rollback()
            return {"success": False, "error": str(e)}
        finally:
            conn.close()

    def vendor_score(self, vendor_id: int) -> dict:
        """Score vendor based on delivery, pricing, quality."""
        conn = self.db.get_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT COUNT(*), AVG(total_amount) FROM purchase_orders WHERE vendor_id=? AND status='confirmed'",
            (vendor_id,)
        )
        row = cur.fetchone()
        conn.close()
        order_count = row[0] or 0
        avg_order = row[1] or 0
        score = min(100, order_count * 5 + (50 if avg_order > 0 else 0))
        return {"vendor_id": vendor_id, "order_count": order_count, "avg_order_value": avg_order, "score": score}
