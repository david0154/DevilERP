"""
Devil ERP — Stock / Inventory Module (Tryton stock)
Developed by Devil One Pvt Ltd & Nexuzy Lab
Lead Developer: David K. Angel

Features: Multi-warehouse, stock transfers, batch/serial tracking,
expiry management, stock valuation (FIFO/weighted avg)
"""
from database.db_manager import DBManager
from datetime import datetime


MOVEMENT_TYPES = ["in", "out", "transfer", "adjustment", "return"]


class StockModule:
    """Complete stock management with movement tracking."""

    def __init__(self):
        self.db = DBManager()
        self._ensure_tables()

    def _ensure_tables(self):
        conn = self.db.get_connection()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS warehouses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                location TEXT DEFAULT '',
                is_active INTEGER DEFAULT 1
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS stock_movements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                movement_type TEXT NOT NULL,
                quantity REAL NOT NULL,
                from_warehouse INTEGER,
                to_warehouse INTEGER,
                batch_number TEXT DEFAULT '',
                serial_number TEXT DEFAULT '',
                expiry_date TEXT DEFAULT '',
                unit_cost REAL DEFAULT 0,
                reference TEXT DEFAULT '',
                notes TEXT DEFAULT '',
                created_at TEXT NOT NULL,
                FOREIGN KEY(product_id) REFERENCES products(id)
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS stock_locations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                warehouse_id INTEGER,
                name TEXT NOT NULL,
                code TEXT,
                FOREIGN KEY(warehouse_id) REFERENCES warehouses(id)
            )
        """)
        conn.commit()
        # Seed default warehouse
        cur.execute("INSERT OR IGNORE INTO warehouses (name, location) VALUES ('Main Warehouse', 'HQ')")
        conn.commit()
        conn.close()

    def stock_in(self, product_id: int, quantity: float, warehouse_id: int = 1,
                 unit_cost: float = 0, batch_number: str = "",
                 serial_number: str = "", expiry_date: str = "",
                 reference: str = "") -> dict:
        if quantity <= 0:
            return {"success": False, "error": "Quantity must be positive"}
        conn = self.db.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                INSERT INTO stock_movements
                (product_id, movement_type, quantity, to_warehouse, unit_cost,
                 batch_number, serial_number, expiry_date, reference, created_at)
                VALUES (?,?,?,?,?,?,?,?,?,?)
            """, (product_id, "in", quantity, warehouse_id, unit_cost,
                  batch_number, serial_number, expiry_date, reference,
                  datetime.now().isoformat()))
            cur.execute(
                "UPDATE products SET stock_qty = COALESCE(stock_qty,0) + ? WHERE id=?",
                (quantity, product_id)
            )
            conn.commit()
            return {"success": True}
        except Exception as e:
            conn.rollback()
            return {"success": False, "error": str(e)}
        finally:
            conn.close()

    def stock_out(self, product_id: int, quantity: float, warehouse_id: int = 1,
                  reference: str = "") -> dict:
        conn = self.db.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("SELECT stock_qty FROM products WHERE id=?", (product_id,))
            row = cur.fetchone()
            if not row or row[0] < quantity:
                return {"success": False, "error": "Insufficient stock"}
            cur.execute("""
                INSERT INTO stock_movements
                (product_id, movement_type, quantity, from_warehouse, reference, created_at)
                VALUES (?,?,?,?,?,?)
            """, (product_id, "out", quantity, warehouse_id, reference,
                  datetime.now().isoformat()))
            cur.execute(
                "UPDATE products SET stock_qty = stock_qty - ? WHERE id=?",
                (quantity, product_id)
            )
            conn.commit()
            return {"success": True}
        except Exception as e:
            conn.rollback()
            return {"success": False, "error": str(e)}
        finally:
            conn.close()

    def transfer_stock(self, product_id: int, quantity: float,
                       from_warehouse: int, to_warehouse: int,
                       notes: str = "") -> dict:
        conn = self.db.get_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                "INSERT INTO stock_movements (product_id, movement_type, quantity, from_warehouse, to_warehouse, notes, created_at) VALUES (?,?,?,?,?,?,?)",
                (product_id, "transfer", quantity, from_warehouse, to_warehouse, notes, datetime.now().isoformat())
            )
            conn.commit()
            return {"success": True}
        except Exception as e:
            conn.rollback()
            return {"success": False, "error": str(e)}
        finally:
            conn.close()

    def adjust_stock(self, product_id: int, new_quantity: float, reason: str = "") -> dict:
        conn = self.db.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("SELECT stock_qty FROM products WHERE id=?", (product_id,))
            row = cur.fetchone()
            current = row[0] if row else 0
            diff = new_quantity - current
            move_type = "adjustment"
            cur.execute(
                "INSERT INTO stock_movements (product_id, movement_type, quantity, notes, created_at) VALUES (?,?,?,?,?)",
                (product_id, move_type, diff, f"Adjustment: {reason}", datetime.now().isoformat())
            )
            cur.execute("UPDATE products SET stock_qty=? WHERE id=?", (new_quantity, product_id))
            conn.commit()
            return {"success": True, "previous": current, "new": new_quantity, "diff": diff}
        except Exception as e:
            conn.rollback()
            return {"success": False, "error": str(e)}
        finally:
            conn.close()

    def get_stock_levels(self, low_stock_only: bool = False) -> list:
        conn = self.db.get_connection()
        cur = conn.cursor()
        if low_stock_only:
            cur.execute("SELECT * FROM products WHERE stock_qty <= reorder_level ORDER BY stock_qty ASC")
        else:
            cur.execute("SELECT * FROM products ORDER BY name ASC")
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return rows

    def get_movement_history(self, product_id: int = None,
                             from_date: str = None, to_date: str = None) -> list:
        conn = self.db.get_connection()
        cur = conn.cursor()
        q = "SELECT sm.*, p.name as product_name FROM stock_movements sm JOIN products p ON sm.product_id=p.id WHERE 1=1"
        p = []
        if product_id:
            q += " AND sm.product_id=?"; p.append(product_id)
        if from_date:
            q += " AND DATE(sm.created_at)>=?"; p.append(from_date)
        if to_date:
            q += " AND DATE(sm.created_at)<=?"; p.append(to_date)
        q += " ORDER BY sm.created_at DESC"
        cur.execute(q, p)
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return rows

    def expiry_alert(self, days_ahead: int = 30) -> list:
        """Return batch items expiring within days_ahead days."""
        conn = self.db.get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT sm.*, p.name as product_name FROM stock_movements sm
            JOIN products p ON sm.product_id=p.id
            WHERE sm.expiry_date != ''
            AND DATE(sm.expiry_date) <= DATE('now', '+' || ? || ' days')
            AND DATE(sm.expiry_date) >= DATE('now')
            ORDER BY sm.expiry_date ASC
        """, (days_ahead,))
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return rows
