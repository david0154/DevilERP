"""
Devil ERP — Database Manager
Supports SQLite (small business) and PostgreSQL (large business)
"""
import os
from pathlib import Path

try:
    import psycopg2
    HAS_PG = True
except ImportError:
    HAS_PG = False

import sqlite3

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "database" / "devil_erp.db"


class DBManager:
    def __init__(self, use_postgres=False, pg_dsn=None):
        self.use_postgres = use_postgres and HAS_PG
        self.pg_dsn = pg_dsn
        self.conn = None
        self.connect()
        self.create_all_tables()

    def connect(self):
        if self.use_postgres:
            self.conn = psycopg2.connect(self.pg_dsn)
        else:
            DB_PATH.parent.mkdir(parents=True, exist_ok=True)
            self.conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
            self.conn.row_factory = sqlite3.Row

    def execute(self, sql, params=()):
        cur = self.conn.cursor()
        cur.execute(sql, params)
        self.conn.commit()
        return cur

    def fetchall(self, sql, params=()):
        cur = self.conn.cursor()
        cur.execute(sql, params)
        return cur.fetchall()

    def fetchone(self, sql, params=()):
        cur = self.conn.cursor()
        cur.execute(sql, params)
        return cur.fetchone()

    def create_all_tables(self):
        self._create_users_table()
        self._create_accounting_tables()
        self._create_inventory_tables()
        self._create_billing_tables()
        self._create_party_tables()
        self._create_hr_tables()

    # ── Users ──────────────────────────────────────────────
    def _create_users_table(self):
        self.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uid TEXT UNIQUE NOT NULL,
            email TEXT NOT NULL,
            name TEXT,
            role TEXT DEFAULT 'employee',
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT (datetime('now'))
        )
        """)

    # ── Accounting ─────────────────────────────────────────
    def _create_accounting_tables(self):
        self.execute("""
        CREATE TABLE IF NOT EXISTS chart_of_accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            account_type TEXT NOT NULL,
            parent_id INTEGER,
            is_active INTEGER DEFAULT 1
        )""")
        self.execute("""
        CREATE TABLE IF NOT EXISTS journal_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            reference TEXT,
            description TEXT,
            created_by INTEGER,
            created_at TEXT DEFAULT (datetime('now')),
            state TEXT DEFAULT 'draft'
        )""")
        self.execute("""
        CREATE TABLE IF NOT EXISTS journal_lines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            journal_id INTEGER NOT NULL,
            account_id INTEGER NOT NULL,
            debit REAL DEFAULT 0,
            credit REAL DEFAULT 0,
            description TEXT,
            FOREIGN KEY(journal_id) REFERENCES journal_entries(id)
        )""")
        self.execute("""
        CREATE TABLE IF NOT EXISTS taxes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            tax_type TEXT NOT NULL,
            rate REAL NOT NULL,
            is_active INTEGER DEFAULT 1
        )""")

    # ── Inventory ──────────────────────────────────────────
    def _create_inventory_tables(self):
        self.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sku TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            category TEXT,
            unit TEXT DEFAULT 'pcs',
            purchase_price REAL DEFAULT 0,
            sale_price REAL DEFAULT 0,
            tax_id INTEGER,
            hsn_code TEXT,
            barcode TEXT,
            current_stock REAL DEFAULT 0,
            reorder_level REAL DEFAULT 10,
            is_active INTEGER DEFAULT 1
        )""")
        self.execute("""
        CREATE TABLE IF NOT EXISTS stock_movements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            movement_type TEXT NOT NULL,
            qty REAL NOT NULL,
            reference TEXT,
            date TEXT DEFAULT (datetime('now')),
            FOREIGN KEY(product_id) REFERENCES products(id)
        )""")
        self.execute("""
        CREATE TABLE IF NOT EXISTS warehouses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            location TEXT,
            is_active INTEGER DEFAULT 1
        )""")

    # ── Billing ────────────────────────────────────────────
    def _create_billing_tables(self):
        self.execute("""
        CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_no TEXT UNIQUE NOT NULL,
            invoice_type TEXT DEFAULT 'sale',
            party_id INTEGER,
            date TEXT NOT NULL,
            due_date TEXT,
            subtotal REAL DEFAULT 0,
            tax_amount REAL DEFAULT 0,
            discount_amount REAL DEFAULT 0,
            total REAL DEFAULT 0,
            paid_amount REAL DEFAULT 0,
            payment_method TEXT,
            state TEXT DEFAULT 'draft',
            notes TEXT,
            created_by INTEGER,
            created_at TEXT DEFAULT (datetime('now'))
        )""")
        self.execute("""
        CREATE TABLE IF NOT EXISTS invoice_lines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_id INTEGER NOT NULL,
            product_id INTEGER,
            description TEXT,
            qty REAL DEFAULT 1,
            unit_price REAL DEFAULT 0,
            discount REAL DEFAULT 0,
            tax_rate REAL DEFAULT 0,
            amount REAL DEFAULT 0,
            FOREIGN KEY(invoice_id) REFERENCES invoices(id)
        )""")
        self.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_id INTEGER,
            amount REAL NOT NULL,
            method TEXT,
            date TEXT DEFAULT (datetime('now')),
            reference TEXT,
            FOREIGN KEY(invoice_id) REFERENCES invoices(id)
        )""")

    # ── Party (Customer/Vendor) ────────────────────────────
    def _create_party_tables(self):
        self.execute("""
        CREATE TABLE IF NOT EXISTS parties (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            party_type TEXT NOT NULL,
            gstin TEXT,
            phone TEXT,
            email TEXT,
            address TEXT,
            city TEXT,
            state TEXT,
            pincode TEXT,
            opening_balance REAL DEFAULT 0,
            credit_limit REAL DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT (datetime('now'))
        )""")

    # ── HR ─────────────────────────────────────────────────
    def _create_hr_tables(self):
        self.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            emp_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            department TEXT,
            designation TEXT,
            phone TEXT,
            email TEXT,
            join_date TEXT,
            basic_salary REAL DEFAULT 0,
            is_active INTEGER DEFAULT 1
        )""")
        self.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            status TEXT DEFAULT 'present',
            in_time TEXT,
            out_time TEXT,
            FOREIGN KEY(employee_id) REFERENCES employees(id)
        )""")
