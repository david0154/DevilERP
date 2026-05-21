"""
Devil ERP Database Schema Manager
Supports SQLite (small business) and PostgreSQL (large business)
"""

import sqlite3
from pathlib import Path
from core.config import DB_TYPE, BASE_DIR

DB_PATH = BASE_DIR / "database" / "devil_erp.sqlite"

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS companies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    gstin TEXT,
    address TEXT,
    phone TEXT,
    email TEXT,
    logo_path TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    firebase_uid TEXT UNIQUE,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    role TEXT NOT NULL DEFAULT 'employee',  -- owner / manager / employee
    company_id INTEGER REFERENCES companies(id),
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    sku TEXT UNIQUE,
    barcode TEXT,
    category TEXT,
    unit TEXT DEFAULT 'pcs',
    purchase_rate REAL DEFAULT 0,
    sale_rate REAL DEFAULT 0,
    gst_rate REAL DEFAULT 18.0,
    hsn_code TEXT,
    stock_qty REAL DEFAULT 0,
    reorder_level REAL DEFAULT 10,
    company_id INTEGER REFERENCES companies(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS parties (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    type TEXT NOT NULL,  -- customer / vendor
    gstin TEXT,
    phone TEXT,
    email TEXT,
    address TEXT,
    balance REAL DEFAULT 0,
    company_id INTEGER REFERENCES companies(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS invoices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_number TEXT NOT NULL,
    invoice_type TEXT NOT NULL,  -- sale / purchase / credit_note / debit_note
    party_id INTEGER REFERENCES parties(id),
    invoice_date TEXT NOT NULL,
    due_date TEXT,
    subtotal REAL DEFAULT 0,
    cgst REAL DEFAULT 0,
    sgst REAL DEFAULT 0,
    igst REAL DEFAULT 0,
    total REAL DEFAULT 0,
    payment_mode TEXT DEFAULT 'cash',  -- cash / upi / card / bank
    status TEXT DEFAULT 'unpaid',  -- unpaid / paid / partial
    notes TEXT,
    company_id INTEGER REFERENCES companies(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS invoice_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_id INTEGER REFERENCES invoices(id),
    product_id INTEGER REFERENCES products(id),
    qty REAL NOT NULL,
    rate REAL NOT NULL,
    discount REAL DEFAULT 0,
    gst_rate REAL DEFAULT 0,
    amount REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS ledger_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account TEXT NOT NULL,
    party_id INTEGER REFERENCES parties(id),
    debit REAL DEFAULT 0,
    credit REAL DEFAULT 0,
    narration TEXT,
    reference TEXT,
    entry_date TEXT NOT NULL,
    company_id INTEGER REFERENCES companies(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ai_scanned_bills (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path TEXT,
    raw_ocr_text TEXT,
    ai_json TEXT,
    invoice_id INTEGER REFERENCES invoices(id),
    status TEXT DEFAULT 'pending',  -- pending / processed / failed
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS backup_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    backup_type TEXT,  -- manual / auto
    gdrive_file_id TEXT,
    status TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

def init_database():
    """Initialize the SQLite database with Devil ERP schema."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA_SQL)
    conn.commit()
    conn.close()
    print(f"[DevilERP] Database initialized at {DB_PATH}")

if __name__ == "__main__":
    init_database()
