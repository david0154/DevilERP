"""
Devil ERP — Sales Module (Tryton sale)
Developed by Devil One Pvt Ltd & Nexuzy Lab
Lead Developer: David K. Angel

Features: Quotations, Sales Orders, Customer management,
Price lists, Discount rules, Sales analytics
"""
from database.db_manager import DBManager
from datetime import datetime


class SaleModule:
    """Sales order management."""

    def __init__(self):
        self.db = DBManager()
        self._ensure_tables()

    def _ensure_tables(self):
        conn = self.db.get_connection()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS sales_orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_number TEXT UNIQUE,
                customer_id INTEGER,
                order_date TEXT,
                delivery_date TEXT,
                status TEXT DEFAULT 'draft',
                subtotal REAL DEFAULT 0,
                total_gst REAL DEFAULT 0,
                total_amount REAL DEFAULT 0,
                discount_amount REAL DEFAULT 0,
                notes TEXT DEFAULT '',
                salesperson TEXT DEFAULT '',
                created_at TEXT
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS sales_order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER,
                product_id INTEGER,
                product_name TEXT,
                quantity REAL,
                unit TEXT DEFAULT 'pcs',
                rate REAL,
                discount_pct REAL DEFAULT 0,
                total_amount REAL,
                FOREIGN KEY(order_id) REFERENCES sales_orders(id)
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS price_lists (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                product_id INTEGER,
                customer_category TEXT DEFAULT 'all',
                price REAL NOT NULL,
                valid_from TEXT,
                valid_to TEXT
            )
        """)
        conn.commit()
        conn.close()

    def create_order(self, customer_id: int, items: list,
                     delivery_date: str = None, notes: str = "",
                     salesperson: str = "") -> dict:
        conn = self.db.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("SELECT COUNT(*) FROM sales_orders")
            n = cur.fetchone()[0]
            order_no = f"SO-{datetime.now().year}-{n+1:05d}"
            subtotal = sum(float(i["quantity"]) * float(i["rate"]) for i in items)
            cur.execute("""
                INSERT INTO sales_orders
                (order_number, customer_id, order_date, delivery_date, status,
                 subtotal, total_amount, notes, salesperson, created_at)
                VALUES (?,?,?,?,?,?,?,?,?,?)
            """, (order_no, customer_id, datetime.now().strftime("%Y-%m-%d"),
                  delivery_date, "confirmed", round(subtotal, 2),
                  round(subtotal, 2), notes, salesperson,
                  datetime.now().isoformat()))
            order_id = cur.lastrowid
            for item in items:
                total = float(item["quantity"]) * float(item["rate"]) * (1 - float(item.get("discount_pct", 0)) / 100)
                cur.execute("""
                    INSERT INTO sales_order_items
                    (order_id, product_id, product_name, quantity, unit, rate, discount_pct, total_amount)
                    VALUES (?,?,?,?,?,?,?,?)
                """, (order_id, item.get("product_id"), item["product_name"],
                      item["quantity"], item.get("unit", "pcs"),
                      item["rate"], item.get("discount_pct", 0), round(total, 2)))
            conn.commit()
            return {"success": True, "order_id": order_id, "order_number": order_no}
        except Exception as e:
            conn.rollback()
            return {"success": False, "error": str(e)}
        finally:
            conn.close()

    def get_sales_analytics(self, from_date: str = None, to_date: str = None) -> dict:
        conn = self.db.get_connection()
        cur = conn.cursor()
        q_base = "FROM invoices WHERE status != 'cancelled'"
        p = []
        if from_date:
            q_base += " AND invoice_date>=?"; p.append(from_date)
        if to_date:
            q_base += " AND invoice_date<=?"; p.append(to_date)
        cur.execute(f"SELECT COUNT(*), COALESCE(SUM(total_amount),0) {q_base}", p)
        row = cur.fetchone()
        cur.execute(f"""
            SELECT ii.product_name, SUM(ii.quantity) as qty, SUM(ii.total_amount) as revenue
            FROM invoice_items ii
            JOIN invoices inv ON ii.invoice_id=inv.id
            WHERE inv.status != 'cancelled'
            GROUP BY ii.product_name ORDER BY revenue DESC LIMIT 10
        """)
        top_products = [dict(r) for r in cur.fetchall()]
        conn.close()
        return {
            "total_invoices": row[0],
            "total_revenue": row[1],
            "top_products": top_products,
        }
