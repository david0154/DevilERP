"""
Devil ERP — Invoice & POS Manager
Handles sale/purchase invoices, GST calculation, payments, returns
"""
import datetime
from database.db_manager import DBManager


class InvoiceManager:
    def __init__(self, db: DBManager):
        self.db = db

    def _next_invoice_no(self, inv_type="sale"):
        prefix = "INV" if inv_type == "sale" else "PUR"
        today = datetime.date.today().strftime("%Y%m%d")
        row = self.db.fetchone(
            "SELECT COUNT(*) as cnt FROM invoices WHERE invoice_type=? AND date(date)=date('now')",
            (inv_type,)
        )
        count = (row[0] if row else 0) + 1
        return f"{prefix}-{today}-{count:04d}"

    def create_invoice(self, party_id, lines, inv_type="sale",
                       payment_method="cash", notes="", created_by=None):
        """
        lines: list of dicts:
            {product_id, description, qty, unit_price, discount, tax_rate}
        Returns invoice_id
        """
        invoice_no = self._next_invoice_no(inv_type)
        date = datetime.datetime.now().isoformat()
        due_date = (datetime.date.today() + datetime.timedelta(days=30)).isoformat()

        subtotal = sum(l["qty"] * l["unit_price"] * (1 - l.get("discount", 0) / 100) for l in lines)
        tax_amount = sum(
            l["qty"] * l["unit_price"] * (1 - l.get("discount", 0) / 100) * (l.get("tax_rate", 0) / 100)
            for l in lines
        )
        discount_amount = sum(
            l["qty"] * l["unit_price"] * (l.get("discount", 0) / 100) for l in lines
        )
        total = subtotal + tax_amount

        self.db.execute("""
            INSERT INTO invoices
            (invoice_no, invoice_type, party_id, date, due_date,
             subtotal, tax_amount, discount_amount, total, payment_method,
             state, notes, created_by)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (invoice_no, inv_type, party_id, date, due_date,
               subtotal, tax_amount, discount_amount, total,
               payment_method, "confirmed", notes, created_by))

        inv = self.db.fetchone("SELECT id FROM invoices WHERE invoice_no=?", (invoice_no,))
        inv_id = inv[0]

        for l in lines:
            qty = l["qty"]
            unit_price = l["unit_price"]
            discount = l.get("discount", 0)
            tax_rate = l.get("tax_rate", 0)
            net = qty * unit_price * (1 - discount / 100)
            tax = net * (tax_rate / 100)
            amount = net + tax

            self.db.execute("""
                INSERT INTO invoice_lines
                (invoice_id, product_id, description, qty, unit_price,
                 discount, tax_rate, amount)
                VALUES (?,?,?,?,?,?,?,?)
            """, (inv_id, l.get("product_id"), l.get("description", ""),
                   qty, unit_price, discount, tax_rate, amount))

            # Update stock
            if l.get("product_id"):
                direction = -1 if inv_type == "sale" else 1
                self.db.execute(
                    "UPDATE products SET current_stock = current_stock + ? WHERE id=?",
                    (direction * qty, l["product_id"])
                )
                self.db.execute("""
                    INSERT INTO stock_movements (product_id, movement_type, qty, reference)
                    VALUES (?,?,?,?)
                """, (l["product_id"],
                       "sale_out" if inv_type == "sale" else "purchase_in",
                       qty, invoice_no))

        return inv_id, invoice_no, total

    def record_payment(self, invoice_id, amount, method="cash", reference=""):
        self.db.execute("""
            INSERT INTO payments (invoice_id, amount, method, reference)
            VALUES (?,?,?,?)
        """, (invoice_id, amount, method, reference))
        self.db.execute(
            "UPDATE invoices SET paid_amount = paid_amount + ? WHERE id=?",
            (amount, invoice_id)
        )
        inv = self.db.fetchone(
            "SELECT total, paid_amount FROM invoices WHERE id=?", (invoice_id,)
        )
        if inv and inv[1] >= inv[0]:
            self.db.execute(
                "UPDATE invoices SET state='paid' WHERE id=?", (invoice_id,)
            )

    def get_invoice(self, invoice_id):
        inv = self.db.fetchone("SELECT * FROM invoices WHERE id=?", (invoice_id,))
        lines = self.db.fetchall(
            "SELECT * FROM invoice_lines WHERE invoice_id=?", (invoice_id,)
        )
        return inv, lines

    def get_unpaid_invoices(self, inv_type="sale"):
        return self.db.fetchall("""
            SELECT i.*, p.name as party_name
            FROM invoices i
            LEFT JOIN parties p ON i.party_id = p.id
            WHERE i.invoice_type=? AND i.state != 'paid'
            ORDER BY i.date DESC
        """, (inv_type,))

    def get_all_invoices(self, inv_type="sale", limit=100):
        return self.db.fetchall("""
            SELECT i.*, p.name as party_name
            FROM invoices i
            LEFT JOIN parties p ON i.party_id = p.id
            WHERE i.invoice_type=?
            ORDER BY i.date DESC LIMIT ?
        """, (inv_type, limit))

    def process_return(self, original_invoice_id, lines, reason=""):
        """Create a credit note / return invoice."""
        orig = self.db.fetchone("SELECT * FROM invoices WHERE id=?", (original_invoice_id,))
        if not orig:
            raise ValueError("Original invoice not found")
        party_id = orig[3]
        return self.create_invoice(party_id, lines, inv_type="return",
                                   notes=f"Return of invoice #{orig[1]}. {reason}")
