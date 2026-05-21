"""
Devil ERP — AI Reorder Predictor
Predicts reorder timing based on sales velocity (no external AI needed)
"""
import datetime
from database.db_manager import DBManager


class AIReorderPredictor:
    def __init__(self, db: DBManager):
        self.db = db

    def _get_daily_sales_rate(self, product_id: int, days: int = 30) -> float:
        row = self.db.fetchone("""
            SELECT SUM(qty) as total
            FROM stock_movements
            WHERE product_id=? AND movement_type='sale_out'
            AND date >= datetime('now', ?)
        """, (product_id, f"-{days} days"))
        total = row[0] if row and row[0] else 0
        return total / days if days > 0 else 0

    def predict_reorder(self, product_id: int, lead_time_days: int = 7):
        """
        Returns:
            days_until_stockout: estimated days
            reorder_now: bool
            suggested_qty: recommended order quantity
        """
        product = self.db.fetchone(
            "SELECT current_stock, reorder_level FROM products WHERE id=?",
            (product_id,)
        )
        if not product:
            return None

        current_stock = product[0]
        reorder_level = product[1]
        daily_rate = self._get_daily_sales_rate(product_id)

        if daily_rate <= 0:
            return {
                "days_until_stockout": 999,
                "reorder_now": current_stock <= reorder_level,
                "suggested_qty": reorder_level * 2,
                "daily_rate": 0
            }

        days_until_stockout = int(current_stock / daily_rate)
        reorder_now = days_until_stockout <= lead_time_days
        # Order enough for 30 days
        suggested_qty = int(daily_rate * 30)

        return {
            "days_until_stockout": days_until_stockout,
            "reorder_now": reorder_now,
            "suggested_qty": max(suggested_qty, reorder_level),
            "daily_rate": round(daily_rate, 2)
        }

    def get_all_reorder_alerts(self):
        """Returns list of products that need reordering."""
        products = self.db.fetchall(
            "SELECT id, name, sku, current_stock, reorder_level FROM products WHERE is_active=1"
        )
        alerts = []
        for p in products:
            pred = self.predict_reorder(p[0])
            if pred and pred["reorder_now"]:
                alerts.append({
                    "product_id": p[0],
                    "name": p[1],
                    "sku": p[2],
                    "current_stock": p[3],
                    "reorder_level": p[4],
                    **pred
                })
        return alerts
