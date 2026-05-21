"""
Devil ERP — Manufacturing / Production Module (Tryton production)
Developed by Devil One Pvt Ltd & Nexuzy Lab
Lead Developer: David K. Angel

Features: BOM, Production Orders, Work Centers,
Material consumption, Production costing
"""
from database.db_manager import DBManager
from datetime import datetime


class ProductionModule:
    """Manufacturing and production management."""

    def __init__(self):
        self.db = DBManager()
        self._ensure_tables()

    def _ensure_tables(self):
        conn = self.db.get_connection()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS bom (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                bom_name TEXT NOT NULL,
                output_quantity REAL DEFAULT 1,
                is_active INTEGER DEFAULT 1,
                created_at TEXT
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS bom_components (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bom_id INTEGER NOT NULL,
                component_id INTEGER NOT NULL,
                component_name TEXT,
                quantity REAL NOT NULL,
                unit TEXT DEFAULT 'pcs',
                FOREIGN KEY(bom_id) REFERENCES bom(id)
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS production_orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_number TEXT UNIQUE,
                product_id INTEGER,
                bom_id INTEGER,
                planned_quantity REAL,
                produced_quantity REAL DEFAULT 0,
                status TEXT DEFAULT 'planned',
                start_date TEXT,
                end_date TEXT,
                total_cost REAL DEFAULT 0,
                notes TEXT DEFAULT '',
                created_at TEXT
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS work_centers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                capacity REAL DEFAULT 1,
                cost_per_hour REAL DEFAULT 0,
                is_active INTEGER DEFAULT 1
            )
        """)
        conn.commit()
        conn.close()

    def create_bom(self, product_id: int, bom_name: str,
                   components: list, output_quantity: float = 1) -> dict:
        """
        components = [{component_id, component_name, quantity, unit}]
        """
        conn = self.db.get_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                "INSERT INTO bom (product_id, bom_name, output_quantity, created_at) VALUES (?,?,?,?)",
                (product_id, bom_name, output_quantity, datetime.now().isoformat())
            )
            bom_id = cur.lastrowid
            for comp in components:
                cur.execute(
                    "INSERT INTO bom_components (bom_id, component_id, component_name, quantity, unit) VALUES (?,?,?,?,?)",
                    (bom_id, comp["component_id"], comp.get("component_name", ""),
                     comp["quantity"], comp.get("unit", "pcs"))
                )
            conn.commit()
            return {"success": True, "bom_id": bom_id}
        except Exception as e:
            conn.rollback()
            return {"success": False, "error": str(e)}
        finally:
            conn.close()

    def create_production_order(self, product_id: int, bom_id: int,
                                planned_quantity: float, start_date: str = None) -> dict:
        conn = self.db.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("SELECT COUNT(*) FROM production_orders")
            n = cur.fetchone()[0]
            order_no = f"MFG-{datetime.now().year}-{n+1:05d}"
            cur.execute("""
                INSERT INTO production_orders
                (order_number, product_id, bom_id, planned_quantity, status, start_date, created_at)
                VALUES (?,?,?,?,?,?,?)
            """, (order_no, product_id, bom_id, planned_quantity, "in_progress",
                  start_date or datetime.now().strftime("%Y-%m-%d"),
                  datetime.now().isoformat()))
            order_id = cur.lastrowid
            conn.commit()
            return {"success": True, "order_id": order_id, "order_number": order_no}
        except Exception as e:
            conn.rollback()
            return {"success": False, "error": str(e)}
        finally:
            conn.close()

    def complete_production(self, order_id: int, produced_qty: float,
                            actual_cost: float = 0) -> dict:
        conn = self.db.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                UPDATE production_orders
                SET produced_quantity=?, status='completed', total_cost=?, end_date=?
                WHERE id=?
            """, (produced_qty, actual_cost,
                  datetime.now().strftime("%Y-%m-%d"), order_id))
            conn.commit()
            return {"success": True}
        except Exception as e:
            conn.rollback()
            return {"success": False, "error": str(e)}
        finally:
            conn.close()
