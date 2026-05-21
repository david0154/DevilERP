"""
Devil ERP — Report Engine
Generates financial, inventory, sales, GST reports.
Exports to PDF (reportlab) and Excel (openpyxl).
"""
import datetime
from pathlib import Path
from database.db_manager import DBManager
from billing.gst_calculator import format_inr

BASE_DIR = Path(__file__).resolve().parent.parent
REPORTS_DIR = BASE_DIR / "exports"


class ReportEngine:
    def __init__(self, db: DBManager):
        self.db = db
        REPORTS_DIR.mkdir(exist_ok=True)

    def _filename(self, name):
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        return REPORTS_DIR / f"{name}_{ts}"

    # ── Data Fetch ────────────────────────────────────────────
    def get_sales_report(self, from_date, to_date):
        return self.db.fetchall("""
            SELECT i.invoice_no, p.name as customer, i.date,
                   i.subtotal, i.tax_amount, i.total, i.state, i.payment_method
            FROM invoices i
            LEFT JOIN parties p ON i.party_id=p.id
            WHERE i.invoice_type='sale'
            AND date(i.date) BETWEEN ? AND ?
            ORDER BY i.date DESC
        """, (from_date, to_date))

    def get_purchase_report(self, from_date, to_date):
        return self.db.fetchall("""
            SELECT i.invoice_no, p.name as vendor, i.date,
                   i.subtotal, i.tax_amount, i.total, i.state
            FROM invoices i
            LEFT JOIN parties p ON i.party_id=p.id
            WHERE i.invoice_type='purchase'
            AND date(i.date) BETWEEN ? AND ?
            ORDER BY i.date DESC
        """, (from_date, to_date))

    def get_gst_report(self, from_date, to_date):
        return self.db.fetchall("""
            SELECT i.invoice_no, p.name, p.gstin,
                   i.subtotal, i.tax_amount, i.total, i.date,
                   i.invoice_type
            FROM invoices i
            LEFT JOIN parties p ON i.party_id=p.id
            WHERE date(i.date) BETWEEN ? AND ?
            ORDER BY i.date
        """, (from_date, to_date))

    def get_ledger(self, account_id, from_date, to_date):
        return self.db.fetchall("""
            SELECT je.date, je.reference, je.description,
                   jl.debit, jl.credit
            FROM journal_lines jl
            JOIN journal_entries je ON jl.journal_id=je.id
            WHERE jl.account_id=?
            AND date(je.date) BETWEEN ? AND ?
            ORDER BY je.date
        """, (account_id, from_date, to_date))

    # ── Excel Export ───────────────────────────────────────
    def export_sales_excel(self, from_date, to_date):
        try:
            import openpyxl
            rows = self.get_sales_report(from_date, to_date)
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Sales Report"
            headers = ["Invoice No", "Customer", "Date",
                       "Subtotal", "GST", "Total", "Status", "Payment"]
            ws.append(headers)
            for r in rows:
                ws.append(list(r))
            path = str(self._filename("sales_report")) + ".xlsx"
            wb.save(path)
            return path
        except ImportError:
            return None

    # ── PDF Export ──────────────────────────────────────────
    def export_invoice_pdf(self, invoice_id, billing_manager):
        try:
            from reportlab.platypus import SimpleDocTemplate, Table, Spacer, Paragraph
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.lib.pagesizes import A4
            from reportlab.lib import colors

            inv, lines = billing_manager.get_invoice(invoice_id)
            if not inv:
                return None

            path = str(self._filename(f"invoice_{inv[1]}")) + ".pdf"
            doc = SimpleDocTemplate(path, pagesize=A4)
            styles = getSampleStyleSheet()
            story = []

            story.append(Paragraph("<b>Devil One Pvt Ltd | Devil ERP</b>", styles["Title"]))
            story.append(Paragraph(f"Invoice No: {inv[1]} | Date: {inv[4][:10]}", styles["Normal"]))
            story.append(Spacer(1, 12))

            table_data = [["#", "Description", "Qty", "Rate", "GST%", "Amount"]]
            for i, l in enumerate(lines, 1):
                table_data.append([
                    i, l[3] or "", l[4], format_inr(l[5]),
                    f"{l[7]}%", format_inr(l[8])
                ])

            table_data.append(["", "", "", "", "Subtotal", format_inr(inv[6])])
            table_data.append(["", "", "", "", "GST", format_inr(inv[7])])
            table_data.append(["", "", "", "", "TOTAL", format_inr(inv[9])])

            t = Table(table_data, colWidths=[30, 200, 50, 80, 60, 80])
            t.setStyle([("BACKGROUND", (0, 0), (-1, 0), colors.darkblue),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey)])
            story.append(t)
            doc.build(story)
            return path
        except ImportError:
            return None
