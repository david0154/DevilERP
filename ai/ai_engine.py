"""
Devil ERP — AI Analytics Engine
Offline AI: Sales prediction, profit trends, vendor scoring,
customer behavior, seasonal analysis — CPU-friendly, no server needed.
Uses llama-cpp-python for local GGUF inference.
"""
import datetime
from pathlib import Path
from database.db_manager import DBManager

BASE_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = BASE_DIR / "models"


class AIEngine:
    """
    Single AI engine that handles:
    - Natural language ERP queries
    - Business analytics
    - Predictions
    """
    def __init__(self, db: DBManager, model_path: str = None):
        self.db = db
        self.model_path = model_path or str(MODELS_DIR / "gemma-2b-it.gguf")
        self._llm = None

    def _load_model(self):
        if self._llm is not None:
            return True
        try:
            from llama_cpp import Llama
            self._llm = Llama(
                model_path=self.model_path,
                n_ctx=1024,
                n_threads=4,
                verbose=False
            )
            return True
        except Exception as e:
            print(f"[AI] Model not available: {e}")
            return False

    def _ask_model(self, prompt: str, max_tokens: int = 512) -> str:
        if not self._load_model():
            return "[AI not available — model not loaded]"
        try:
            result = self._llm(prompt, max_tokens=max_tokens, temperature=0.3)
            return result["choices"][0]["text"].strip()
        except Exception as e:
            return f"[AI Error] {e}"

    # ── Sales Analytics ─────────────────────────────────────
    def get_monthly_sales(self, months: int = 6):
        """Returns monthly sales totals for last N months."""
        results = []
        for i in range(months - 1, -1, -1):
            row = self.db.fetchone("""
                SELECT strftime('%Y-%m', date) as month,
                       SUM(total) as revenue,
                       COUNT(*) as count
                FROM invoices
                WHERE invoice_type='sale' AND state='paid'
                AND date(date) >= date('now', ?)
                AND date(date) < date('now', ?)
            """, (f"-{i+1} months", f"-{i} months"))
            if row:
                results.append({
                    "month": row[0] or f"-{i}m",
                    "revenue": row[1] or 0,
                    "count": row[2] or 0
                })
        return results

    def predict_next_month_sales(self) -> dict:
        """Simple linear trend prediction for next month sales."""
        data = self.get_monthly_sales(6)
        if not data:
            return {"predicted": 0, "confidence": "low", "trend": "no data"}
        revenues = [d["revenue"] for d in data if d["revenue"]]
        if len(revenues) < 2:
            return {"predicted": revenues[0] if revenues else 0,
                    "confidence": "low", "trend": "insufficient data"}
        # Simple linear regression slope
        n = len(revenues)
        avg = sum(revenues) / n
        slope = (revenues[-1] - revenues[0]) / max(n - 1, 1)
        predicted = revenues[-1] + slope
        trend = "up" if slope > 0 else "down" if slope < 0 else "flat"
        confidence = "high" if abs(slope / avg) < 0.3 else "medium"
        return {
            "predicted": round(max(predicted, 0), 2),
            "confidence": confidence,
            "trend": trend,
            "avg_monthly": round(avg, 2)
        }

    # ── Profit Analysis ────────────────────────────────────
    def get_profit_summary(self, period_days: int = 30):
        sales = self.db.fetchone("""
            SELECT SUM(total) FROM invoices
            WHERE invoice_type='sale' AND state='paid'
            AND date(date) >= date('now', ?)
        """, (f"-{period_days} days",))
        purchases = self.db.fetchone("""
            SELECT SUM(total) FROM invoices
            WHERE invoice_type='purchase'
            AND date(date) >= date('now', ?)
        """, (f"-{period_days} days",))
        revenue = sales[0] or 0
        cost = purchases[0] or 0
        profit = revenue - cost
        margin = (profit / revenue * 100) if revenue > 0 else 0
        return {
            "revenue": round(revenue, 2),
            "cost": round(cost, 2),
            "profit": round(profit, 2),
            "margin_pct": round(margin, 2),
            "period_days": period_days
        }

    # ── Vendor Scoring ────────────────────────────────────
    def score_vendors(self):
        """Ranks vendors by total purchases, avg invoice value."""
        rows = self.db.fetchall("""
            SELECT p.name, p.gstin,
                   COUNT(i.id) as invoice_count,
                   SUM(i.total) as total_spent,
                   AVG(i.total) as avg_value
            FROM parties p
            JOIN invoices i ON i.party_id = p.id
            WHERE p.party_type='vendor' AND i.invoice_type='purchase'
            GROUP BY p.id
            ORDER BY total_spent DESC
        """)
        vendors = []
        for r in rows:
            vendors.append({
                "name": r[0], "gstin": r[1],
                "invoice_count": r[2],
                "total_spent": round(r[3] or 0, 2),
                "avg_value": round(r[4] or 0, 2)
            })
        return vendors

    # ── Customer Behavior ────────────────────────────────
    def top_customers(self, limit: int = 10):
        rows = self.db.fetchall("""
            SELECT p.name, COUNT(i.id) as orders,
                   SUM(i.total) as lifetime_value
            FROM parties p
            JOIN invoices i ON i.party_id = p.id
            WHERE p.party_type='customer' AND i.invoice_type='sale'
            GROUP BY p.id
            ORDER BY lifetime_value DESC LIMIT ?
        """, (limit,))
        return [{
            "name": r[0], "orders": r[1],
            "lifetime_value": round(r[2] or 0, 2)
        } for r in rows]

    # ── Natural Language Query ────────────────────────────
    def query(self, user_question: str) -> str:
        """
        Handles predefined ERP queries without LLM (fast, CPU-friendly).
        Falls back to LLM for open-ended questions.
        """
        q = user_question.lower().strip()

        if "unpaid invoice" in q:
            rows = self.db.fetchall("""
                SELECT invoice_no, total, paid_amount, date
                FROM invoices WHERE state != 'paid' AND invoice_type='sale'
                ORDER BY date DESC LIMIT 10
            """)
            if not rows:
                return "No unpaid invoices found."
            out = "Unpaid Invoices:\n"
            for r in rows:
                out += f"  {r[0]} | Total: ₹{r[1]:.2f} | Paid: ₹{r[2]:.2f} | Date: {r[3][:10]}\n"
            return out

        elif "fast" in q and ("sell" in q or "product" in q or "moving" in q):
            rows = self.db.fetchall("""
                SELECT p.name, SUM(sm.qty) as sold
                FROM stock_movements sm JOIN products p ON sm.product_id=p.id
                WHERE sm.movement_type='sale_out'
                GROUP BY sm.product_id ORDER BY sold DESC LIMIT 5
            """)
            if not rows:
                return "No sales data found."
            return "Top Selling Products:\n" + "\n".join([f"  {r[0]}: {r[1]} units" for r in rows])

        elif "predict" in q and "sales" in q or "next month" in q:
            pred = self.predict_next_month_sales()
            return (f"Predicted next month sales: ₹{pred['predicted']:,.2f}\n"
                    f"Trend: {pred['trend']} | Confidence: {pred['confidence']}")

        elif "profit" in q:
            p = self.get_profit_summary(30)
            return (f"Last 30 days:\n"
                    f"  Revenue: ₹{p['revenue']:,.2f}\n"
                    f"  Cost: ₹{p['cost']:,.2f}\n"
                    f"  Profit: ₹{p['profit']:,.2f} ({p['margin_pct']}%)")

        elif "vendor" in q and ("best" in q or "profit" in q or "score" in q):
            vendors = self.score_vendors()
            if not vendors:
                return "No vendor data."
            top = vendors[0]
            return f"Top vendor by purchases: {top['name']} | Total: ₹{top['total_spent']:,.2f}"

        elif "low stock" in q or "reorder" in q:
            rows = self.db.fetchall(
                "SELECT name, current_stock, reorder_level FROM products WHERE current_stock <= reorder_level AND is_active=1"
            )
            if not rows:
                return "All products are adequately stocked."
            return "Low Stock Alert:\n" + "\n".join([f"  {r[0]}: {r[1]} (min: {r[2]})" for r in rows])

        else:
            # Use LLM for open-ended queries
            context = f"""
You are a helpful ERP assistant for Devil ERP, an Indian business software.
Answer the following business question concisely.
Question: {user_question}
Answer:"""
            return self._ask_model(context, max_tokens=256)
