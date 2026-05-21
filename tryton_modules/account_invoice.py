"""
Devil ERP — Account Invoice Module (Tryton account_invoice)
Developed by Devil One Pvt Ltd & Nexuzy Lab
Lead Developer: David K. Angel

Supports: Retail invoice, Tax invoice, GST invoice
With automatic CGST/SGST/IGST calculation
"""
from database.db_manager import DBManager
from billing.gst_calculator import GSTCalculator
from datetime import datetime


INVOICE_TYPES = ["retail", "tax", "gst", "proforma", "credit_note", "debit_note"]
INVOICE_STATUS = ["draft", "confirmed", "paid", "partial", "cancelled"]


class InvoiceModule:
    """Complete invoice management with GST & ledger posting."""

    def __init__(self):
        self.db = DBManager()
        self.gst = GSTCalculator()
        self._ensure_tables()

    def _ensure_tables(self):
        conn = self.db.get_connection()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS invoice_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_id INTEGER NOT NULL,
                product_id INTEGER,
                product_name TEXT NOT NULL,
                hsn_code TEXT DEFAULT '',
                quantity REAL NOT NULL,
                unit TEXT DEFAULT 'pcs',
                rate REAL NOT NULL,
                discount_pct REAL DEFAULT 0,
                taxable_amount REAL NOT NULL,
                gst_rate REAL DEFAULT 0,
                cgst_amount REAL DEFAULT 0,
                sgst_amount REAL DEFAULT 0,
                igst_amount REAL DEFAULT 0,
                total_amount REAL NOT NULL,
                FOREIGN KEY(invoice_id) REFERENCES invoices(id)
            )
        """)
        conn.commit()
        conn.close()

    def create_invoice(self, customer_id: int, invoice_type: str,
                       items: list, is_interstate: bool = False,
                       notes: str = "", reference: str = "") -> dict:
        """
        items = [
            {product_id, product_name, hsn_code, quantity, unit, rate,
             discount_pct, gst_rate}
        ]
        """
        if invoice_type not in INVOICE_TYPES:
            return {"success": False, "error": f"Invalid type. Use: {INVOICE_TYPES}"}
        if not items:
            return {"success": False, "error": "No items provided"}

        conn = self.db.get_connection()
        cur = conn.cursor()
        try:
            subtotal = 0.0
            total_cgst = total_sgst = total_igst = 0.0
            processed_items = []

            for item in items:
                qty = float(item["quantity"])
                rate = float(item["rate"])
                disc_pct = float(item.get("discount_pct", 0))
                gst_rate = float(item.get("gst_rate", 0))

                taxable = qty * rate * (1 - disc_pct / 100)
                gst_calc = self.gst.calculate(
                    taxable, gst_rate, is_interstate=is_interstate
                )
                item_total = taxable + gst_calc["total_gst"]
                subtotal += taxable
                total_cgst += gst_calc.get("cgst", 0)
                total_sgst += gst_calc.get("sgst", 0)
                total_igst += gst_calc.get("igst", 0)
                processed_items.append({
                    **item,
                    "taxable_amount": round(taxable, 2),
                    "cgst_amount": round(gst_calc.get("cgst", 0), 2),
                    "sgst_amount": round(gst_calc.get("sgst", 0), 2),
                    "igst_amount": round(gst_calc.get("igst", 0), 2),
                    "total_amount": round(item_total, 2),
                })

            total_gst = total_cgst + total_sgst + total_igst
            grand_total = subtotal + total_gst

            # Get invoice number
            cur.execute("SELECT COUNT(*) FROM invoices")
            count = cur.fetchone()[0]
            inv_no = f"INV-{datetime.now().year}-{count+1:05d}"

            cur.execute("""
                INSERT INTO invoices
                (invoice_number, customer_id, invoice_type, invoice_date,
                 subtotal, cgst_amount, sgst_amount, igst_amount, total_gst,
                 total_amount, paid_amount, payment_status, notes, reference,
                 is_interstate, status, created_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,0,'unpaid',?,?,?,?,?)
            """, (
                inv_no, customer_id, invoice_type,
                datetime.now().strftime("%Y-%m-%d"),
                round(subtotal, 2), round(total_cgst, 2),
                round(total_sgst, 2), round(total_igst, 2),
                round(total_gst, 2), round(grand_total, 2),
                notes, reference, 1 if is_interstate else 0,
                "confirmed", datetime.now().isoformat()
            ))
            invoice_id = cur.lastrowid

            for item in processed_items:
                cur.execute("""
                    INSERT INTO invoice_items
                    (invoice_id, product_id, product_name, hsn_code, quantity,
                     unit, rate, discount_pct, taxable_amount, gst_rate,
                     cgst_amount, sgst_amount, igst_amount, total_amount)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """, (
                    invoice_id,
                    item.get("product_id"),
                    item["product_name"],
                    item.get("hsn_code", ""),
                    item["quantity"],
                    item.get("unit", "pcs"),
                    item["rate"],
                    item["discount_pct"],
                    item["taxable_amount"],
                    item["gst_rate"],
                    item["cgst_amount"],
                    item["sgst_amount"],
                    item["igst_amount"],
                    item["total_amount"],
                ))

            conn.commit()
            return {
                "success": True,
                "invoice_id": invoice_id,
                "invoice_number": inv_no,
                "subtotal": round(subtotal, 2),
                "total_gst": round(total_gst, 2),
                "grand_total": round(grand_total, 2),
            }
        except Exception as e:
            conn.rollback()
            return {"success": False, "error": str(e)}
        finally:
            conn.close()

    def get_invoice(self, invoice_id: int) -> dict:
        conn = self.db.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM invoices WHERE id=?", (invoice_id,))
        inv = dict(cur.fetchone() or {})
        if inv:
            cur.execute("SELECT * FROM invoice_items WHERE invoice_id=?", (invoice_id,))
            inv["items"] = [dict(r) for r in cur.fetchall()]
        conn.close()
        return inv

    def get_invoices(self, status: str = None, from_date: str = None,
                     to_date: str = None, customer_id: int = None) -> list:
        conn = self.db.get_connection()
        cur = conn.cursor()
        q = "SELECT * FROM invoices WHERE 1=1"
        p = []
        if status:
            q += " AND payment_status=?"; p.append(status)
        if from_date:
            q += " AND invoice_date>=?"; p.append(from_date)
        if to_date:
            q += " AND invoice_date<=?"; p.append(to_date)
        if customer_id:
            q += " AND customer_id=?"; p.append(customer_id)
        q += " ORDER BY created_at DESC"
        cur.execute(q, p)
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return rows

    def cancel_invoice(self, invoice_id: int, reason: str = "") -> dict:
        conn = self.db.get_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                "UPDATE invoices SET status='cancelled', notes=COALESCE(notes,'')||? WHERE id=?",
                (f" | CANCELLED: {reason}", invoice_id)
            )
            conn.commit()
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            conn.close()

    def gst_summary_report(self, from_date: str, to_date: str) -> dict:
        """GST report for filing — CGST, SGST, IGST breakup."""
        conn = self.db.get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT
                SUM(subtotal) as taxable_value,
                SUM(cgst_amount) as total_cgst,
                SUM(sgst_amount) as total_sgst,
                SUM(igst_amount) as total_igst,
                SUM(total_gst) as total_tax,
                SUM(total_amount) as gross_total,
                COUNT(*) as invoice_count
            FROM invoices
            WHERE invoice_date BETWEEN ? AND ?
            AND status != 'cancelled'
        """, (from_date, to_date))
        row = dict(cur.fetchone())
        conn.close()
        return row
