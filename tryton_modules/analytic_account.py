"""
Devil ERP — Analytic / Reporting Module (Tryton analytic_account)
Developed by Devil One Pvt Ltd & Nexuzy Lab
Lead Developer: David K. Angel

Features: Business analytics, Sales prediction, Profit analysis,
Seasonal trends, Dead stock detection, Vendor scoring,
Customer behavior analysis, Expense analysis
"""
from database.db_manager import DBManager
from datetime import datetime, timedelta


class AnalyticModule:
    """Business analytics and reporting engine."""

    def __init__(self):
        self.db = DBManager()

    def sales_trend(self, days: int = 30) -> list:
        """Daily sales for last N days."""
        conn = self.db.get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT DATE(created_at) as day,
                   COUNT(*) as invoice_count,
                   COALESCE(SUM(total_amount), 0) as total_sales
            FROM invoices
            WHERE DATE(created_at) >= DATE('now', '-' || ? || ' days')
            AND status != 'cancelled'
            GROUP BY day ORDER BY day ASC
        """, (days,))
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return rows

    def top_customers(self, limit: int = 10) -> list:
        conn = self.db.get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT c.id, c.name, c.phone,
                   COUNT(i.id) as order_count,
                   COALESCE(SUM(i.total_amount), 0) as total_spent
            FROM customers c
            LEFT JOIN invoices i ON c.id=i.customer_id AND i.status!='cancelled'
            GROUP BY c.id ORDER BY total_spent DESC LIMIT ?
        """, (limit,))
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return rows

    def dead_stock(self, days_no_movement: int = 60) -> list:
        """Products with no sales in N days."""
        conn = self.db.get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT p.id, p.name, p.stock_qty, p.reorder_level,
                   MAX(sm.created_at) as last_movement
            FROM products p
            LEFT JOIN stock_movements sm ON p.id=sm.product_id AND sm.movement_type='out'
            WHERE p.stock_qty > 0
            GROUP BY p.id
            HAVING last_movement IS NULL OR DATE(last_movement) < DATE('now', '-' || ? || ' days')
            ORDER BY p.stock_qty DESC
        """, (days_no_movement,))
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return rows

    def monthly_expense_summary(self, year: int = None) -> list:
        year = year or datetime.now().year
        conn = self.db.get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT strftime('%m', entry_date) as month,
                   SUM(amount) as total_expense
            FROM journal_entries
            WHERE strftime('%Y', entry_date) = ?
            AND debit_account LIKE '5%'
            GROUP BY month ORDER BY month
        """, (str(year),))
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return rows

    def profit_summary(self, from_date: str = None, to_date: str = None) -> dict:
        from tryton_modules.account import GeneralLedger
        gl = GeneralLedger()
        return gl.profit_and_loss(from_date, to_date)

    def sales_prediction_simple(self) -> dict:
        """Simple moving average prediction for next month sales."""
        trend = self.sales_trend(days=90)
        if len(trend) < 7:
            return {"predicted_daily": 0, "predicted_monthly": 0, "basis": "insufficient data"}
        total = sum(t["total_sales"] for t in trend)
        avg_daily = total / len(trend)
        return {
            "predicted_daily": round(avg_daily, 2),
            "predicted_monthly": round(avg_daily * 30, 2),
            "basis": f"{len(trend)} days average",
        }

    def product_performance(self, limit: int = 10) -> list:
        conn = self.db.get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT ii.product_name,
                   SUM(ii.quantity) as total_qty_sold,
                   SUM(ii.total_amount) as total_revenue,
                   COUNT(DISTINCT ii.invoice_id) as order_count
            FROM invoice_items ii
            JOIN invoices inv ON ii.invoice_id=inv.id
            WHERE inv.status != 'cancelled'
            GROUP BY ii.product_name
            ORDER BY total_revenue DESC LIMIT ?
        """, (limit,))
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return rows

    def full_dashboard_data(self) -> dict:
        """Single call to get all dashboard metrics."""
        return {
            "sales_trend_30d": self.sales_trend(30),
            "top_customers": self.top_customers(5),
            "dead_stock": self.dead_stock(60),
            "product_performance": self.product_performance(10),
            "sales_prediction": self.sales_prediction_simple(),
            "profit_summary": self.profit_summary(),
        }
