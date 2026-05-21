"""
Devil ERP — Thermal Printer Support
Prints GST-compliant receipts via ESC/POS or fallback plain text
"""
from billing.gst_calculator import format_inr
import datetime


COMPANY = "Devil One Pvt Ltd"
SUPPORT = "nexuzylab@gmail.com"


def build_receipt_text(invoice_no, party_name, lines, subtotal,
                       tax_amount, total, payment_method, gst_no=""):
    lines_text = ""
    for l in lines:
        lines_text += f"  {l.get('description','Item')[:20]:<20} {l.get('qty',1):>4} x {format_inr(l.get('unit_price',0)):>10} = {format_inr(l.get('amount',0)):>12}\n"

    receipt = f"""
================================================
           {COMPANY}
           Devil ERP | {SUPPORT}
================================================
Invoice No : {invoice_no}
Date       : {datetime.date.today().isoformat()}
Customer   : {party_name}
{f'GSTIN      : {gst_no}' if gst_no else ''}
------------------------------------------------
{lines_text}------------------------------------------------
Subtotal   : {format_inr(subtotal):>30}
GST        : {format_inr(tax_amount):>30}
TOTAL      : {format_inr(total):>30}
------------------------------------------------
Payment    : {payment_method.upper()}
================================================
       Thank you for your business!
================================================
"""
    return receipt


def print_receipt(invoice_no, party_name, lines, subtotal, tax_amount,
                  total, payment_method, gst_no="", printer_name=None):
    receipt = build_receipt_text(invoice_no, party_name, lines, subtotal,
                                  tax_amount, total, payment_method, gst_no)
    try:
        from escpos.printer import Network, Usb
        # ESC/POS network printer
        if printer_name and ":" in printer_name:
            host, port = printer_name.split(":")
            p = Network(host, int(port))
            p.text(receipt)
            p.cut()
            return True
    except ImportError:
        pass
    # Fallback: write to temp file and print via OS
    import tempfile, subprocess, os
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt",
                                    delete=False, encoding="utf-8") as f:
        f.write(receipt)
        tmp = f.name
    try:
        if os.name == "nt":
            subprocess.run(["notepad", "/p", tmp], check=True)
        else:
            subprocess.run(["lp", tmp], check=True)
    except Exception:
        pass
    return receipt
