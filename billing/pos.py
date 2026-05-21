"""
Devil ERP — POS & Billing Module
Features: Barcode scan, GST invoicing, thermal print, UPI/Cash/Card payment
"""

import sqlite3
from datetime import date
from core.config import BASE_DIR

DB_PATH = BASE_DIR / "database" / "devil_erp.sqlite"


class POSBilling:
    def __init__(self, company_id: int, user: dict):
        self.company_id = company_id
        self.user = user
        self.cart = []  # [{product_id, name, qty, rate, discount, gst_rate, amount}]

    def add_item(self, product_id: int, qty: float, discount: float = 0) -> dict:
        """Add product to cart by ID."""
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        product = conn.execute(
            "SELECT * FROM products WHERE id = ? AND company_id = ?",
            (product_id, self.company_id)
        ).fetchone()
        conn.close()

        if not product:
            return {"error": "Product not found"}

        rate = product['sale_rate']
        gst_rate = product['gst_rate']
        discounted_rate = rate * (1 - discount / 100)
        amount = discounted_rate * qty

        self.cart.append({
            "product_id": product_id,
            "name": product['name'],
            "qty": qty,
            "rate": rate,
            "discount": discount,
            "gst_rate": gst_rate,
            "amount": amount,
        })
        return {"success": True, "item_count": len(self.cart)}

    def calculate_totals(self) -> dict:
        """Calculate subtotal, GST, and grand total."""
        subtotal = sum(i['amount'] for i in self.cart)
        cgst = sum(i['amount'] * i['gst_rate'] / 200 for i in self.cart)
        sgst = cgst
        total = subtotal + cgst + sgst
        return {
            "subtotal": round(subtotal, 2),
            "cgst": round(cgst, 2),
            "sgst": round(sgst, 2),
            "igst": 0,
            "total": round(total, 2),
        }

    def create_invoice(self, party_id: int, payment_mode: str = 'cash') -> dict:
        """Finalize and save invoice to database."""
        if not self.cart:
            return {"error": "Cart is empty"}

        totals = self.calculate_totals()
        conn = sqlite3.connect(DB_PATH)

        # Generate invoice number
        count = conn.execute("SELECT COUNT(*) FROM invoices WHERE company_id = ?", (self.company_id,)).fetchone()[0]
        invoice_number = f"INV-{date.today().strftime('%Y%m')}-{count + 1:04d}"

        # Insert invoice
        cursor = conn.execute(
            """INSERT INTO invoices
               (invoice_number, invoice_type, party_id, invoice_date, subtotal, cgst, sgst, total, payment_mode, company_id)
               VALUES (?, 'sale', ?, ?, ?, ?, ?, ?, ?, ?)""",
            (invoice_number, party_id, str(date.today()),
             totals['subtotal'], totals['cgst'], totals['sgst'],
             totals['total'], payment_mode, self.company_id)
        )
        invoice_id = cursor.lastrowid

        # Insert items
        for item in self.cart:
            conn.execute(
                "INSERT INTO invoice_items (invoice_id, product_id, qty, rate, discount, gst_rate, amount) VALUES (?,?,?,?,?,?,?)",
                (invoice_id, item['product_id'], item['qty'], item['rate'],
                 item['discount'], item['gst_rate'], item['amount'])
            )
            # Deduct stock
            conn.execute(
                "UPDATE products SET stock_qty = stock_qty - ? WHERE id = ?",
                (item['qty'], item['product_id'])
            )

        conn.commit()
        conn.close()
        self.cart = []
        return {"success": True, "invoice_id": invoice_id, "invoice_number": invoice_number, **totals}
