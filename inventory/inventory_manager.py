"""
Devil ERP — Inventory Manager
Product CRUD, stock tracking, warehouse transfers, reorder alerts
"""
from database.db_manager import DBManager


class InventoryManager:
    def __init__(self, db: DBManager):
        self.db = db

    # ── Product CRUD ───────────────────────────────────────
    def add_product(self, sku, name, category, unit, purchase_price,
                    sale_price, tax_id=None, hsn_code="",
                    barcode="", reorder_level=10):
        self.db.execute("""
            INSERT INTO products
            (sku, name, category, unit, purchase_price, sale_price,
             tax_id, hsn_code, barcode, reorder_level)
            VALUES (?,?,?,?,?,?,?,?,?,?)
        """, (sku, name, category, unit, purchase_price, sale_price,
               tax_id, hsn_code, barcode, reorder_level))

    def update_product(self, product_id, **kwargs):
        fields = ", ".join([f"{k}=?" for k in kwargs])
        values = list(kwargs.values()) + [product_id]
        self.db.execute(f"UPDATE products SET {fields} WHERE id=?", values)

    def get_product(self, product_id=None, sku=None, barcode=None):
        if product_id:
            return self.db.fetchone("SELECT * FROM products WHERE id=?", (product_id,))
        if sku:
            return self.db.fetchone("SELECT * FROM products WHERE sku=?", (sku,))
        if barcode:
            return self.db.fetchone("SELECT * FROM products WHERE barcode=?", (barcode,))

    def search_products(self, query):
        q = f"%{query}%"
        return self.db.fetchall("""
            SELECT * FROM products
            WHERE is_active=1 AND (name LIKE ? OR sku LIKE ? OR barcode LIKE ?)
            ORDER BY name
        """, (q, q, q))

    def get_all_products(self):
        return self.db.fetchall(
            "SELECT * FROM products WHERE is_active=1 ORDER BY name"
        )

    def delete_product(self, product_id):
        self.db.execute(
            "UPDATE products SET is_active=0 WHERE id=?", (product_id,)
        )

    # ── Stock Operations ───────────────────────────────────
    def adjust_stock(self, product_id, qty, movement_type="adjustment",
                     reference=""):
        self.db.execute(
            "UPDATE products SET current_stock = current_stock + ? WHERE id=?",
            (qty, product_id)
        )
        self.db.execute("""
            INSERT INTO stock_movements (product_id, movement_type, qty, reference)
            VALUES (?,?,?,?)
        """, (product_id, movement_type, qty, reference))

    def get_stock_history(self, product_id, limit=50):
        return self.db.fetchall("""
            SELECT sm.*, p.name as product_name
            FROM stock_movements sm
            JOIN products p ON sm.product_id = p.id
            WHERE sm.product_id=?
            ORDER BY sm.date DESC LIMIT ?
        """, (product_id, limit))

    # ── Alerts ─────────────────────────────────────────────
    def get_low_stock_products(self):
        return self.db.fetchall("""
            SELECT * FROM products
            WHERE is_active=1 AND current_stock <= reorder_level
            ORDER BY current_stock ASC
        """)

    def get_dead_stock(self, days=90):
        """Products with no movement in last N days."""
        return self.db.fetchall("""
            SELECT p.* FROM products p
            WHERE p.is_active=1
            AND p.id NOT IN (
                SELECT DISTINCT product_id FROM stock_movements
                WHERE date >= datetime('now', ?)
            ) AND p.current_stock > 0
            ORDER BY p.current_stock DESC
        """, (f"-{days} days",))

    # ── Analytics ──────────────────────────────────────────
    def get_fast_moving(self, days=30, limit=10):
        """Top selling products by quantity in last N days."""
        return self.db.fetchall("""
            SELECT p.name, p.sku, SUM(sm.qty) as total_sold
            FROM stock_movements sm
            JOIN products p ON sm.product_id = p.id
            WHERE sm.movement_type='sale_out'
            AND sm.date >= datetime('now', ?)
            GROUP BY sm.product_id
            ORDER BY total_sold DESC LIMIT ?
        """, (f"-{days} days", limit))

    def get_stock_valuation(self):
        """Total inventory value at purchase price."""
        row = self.db.fetchone(
            "SELECT SUM(current_stock * purchase_price) FROM products WHERE is_active=1"
        )
        return row[0] or 0.0
