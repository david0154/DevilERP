"""
Devil ERP — Seed default chart of accounts & taxes (Indian GST)
"""
from database.db_manager import DBManager


DEFAULT_ACCOUNTS = [
    ("1000", "Cash", "asset"),
    ("1001", "Bank", "asset"),
    ("1100", "Accounts Receivable", "asset"),
    ("1200", "Inventory", "asset"),
    ("2000", "Accounts Payable", "liability"),
    ("2100", "GST Payable", "liability"),
    ("3000", "Owner Equity", "equity"),
    ("4000", "Sales Revenue", "income"),
    ("5000", "Cost of Goods Sold", "expense"),
    ("5100", "Rent Expense", "expense"),
    ("5200", "Salary Expense", "expense"),
    ("5300", "Miscellaneous Expense", "expense"),
]

DEFAULT_TAXES = [
    ("GST 5%", "gst", 5.0),
    ("GST 12%", "gst", 12.0),
    ("GST 18%", "gst", 18.0),
    ("GST 28%", "gst", 28.0),
    ("IGST 18%", "igst", 18.0),
    ("No Tax", "none", 0.0),
]


def seed(db: DBManager):
    for code, name, atype in DEFAULT_ACCOUNTS:
        existing = db.fetchone("SELECT id FROM chart_of_accounts WHERE code=?", (code,))
        if not existing:
            db.execute(
                "INSERT INTO chart_of_accounts (code, name, account_type) VALUES (?,?,?)",
                (code, name, atype)
            )
    for name, ttype, rate in DEFAULT_TAXES:
        existing = db.fetchone("SELECT id FROM taxes WHERE name=?", (name,))
        if not existing:
            db.execute(
                "INSERT INTO taxes (name, tax_type, rate) VALUES (?,?,?)",
                (name, ttype, rate)
            )
    print("[Seed] Default accounts and taxes seeded.")
