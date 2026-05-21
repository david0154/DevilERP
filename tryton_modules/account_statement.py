"""
Devil ERP — Bank Statement / Account Statement Module (Tryton account_statement)
Developed by Devil One Pvt Ltd & Nexuzy Lab
Lead Developer: David K. Angel

Features: Bank accounts, Statement import,
Reconciliation, Cheque tracking, Transaction matching
"""
from database.db_manager import DBManager
from datetime import datetime


class AccountStatementModule:
    """Banking and statement reconciliation."""

    def __init__(self):
        self.db = DBManager()
        self._ensure_tables()

    def _ensure_tables(self):
        conn = self.db.get_connection()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS bank_accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bank_name TEXT NOT NULL,
                account_number TEXT UNIQUE NOT NULL,
                ifsc_code TEXT DEFAULT '',
                account_type TEXT DEFAULT 'current',
                opening_balance REAL DEFAULT 0,
                current_balance REAL DEFAULT 0,
                is_active INTEGER DEFAULT 1,
                created_at TEXT
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS bank_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bank_account_id INTEGER,
                transaction_date TEXT,
                description TEXT DEFAULT '',
                debit_amount REAL DEFAULT 0,
                credit_amount REAL DEFAULT 0,
                balance REAL DEFAULT 0,
                reference TEXT DEFAULT '',
                cheque_number TEXT DEFAULT '',
                reconciled INTEGER DEFAULT 0,
                journal_entry_id INTEGER,
                created_at TEXT,
                FOREIGN KEY(bank_account_id) REFERENCES bank_accounts(id)
            )
        """)
        conn.commit()
        conn.close()

    def add_bank_account(self, bank_name: str, account_number: str,
                         ifsc_code: str = "", account_type: str = "current",
                         opening_balance: float = 0) -> dict:
        conn = self.db.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                INSERT INTO bank_accounts
                (bank_name, account_number, ifsc_code, account_type, opening_balance, current_balance, created_at)
                VALUES (?,?,?,?,?,?,?)
            """, (bank_name, account_number, ifsc_code, account_type,
                  opening_balance, opening_balance, datetime.now().isoformat()))
            conn.commit()
            return {"success": True, "bank_account_id": cur.lastrowid}
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            conn.close()

    def add_transaction(self, bank_account_id: int, transaction_date: str,
                        description: str, debit: float = 0, credit: float = 0,
                        reference: str = "", cheque_number: str = "") -> dict:
        conn = self.db.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("SELECT current_balance FROM bank_accounts WHERE id=?", (bank_account_id,))
            row = cur.fetchone()
            balance = (row[0] if row else 0) + credit - debit
            cur.execute("""
                INSERT INTO bank_transactions
                (bank_account_id, transaction_date, description, debit_amount, credit_amount,
                 balance, reference, cheque_number, created_at)
                VALUES (?,?,?,?,?,?,?,?,?)
            """, (bank_account_id, transaction_date, description, debit, credit,
                  round(balance, 2), reference, cheque_number, datetime.now().isoformat()))
            cur.execute(
                "UPDATE bank_accounts SET current_balance=? WHERE id=?",
                (round(balance, 2), bank_account_id)
            )
            conn.commit()
            return {"success": True, "new_balance": round(balance, 2)}
        except Exception as e:
            conn.rollback()
            return {"success": False, "error": str(e)}
        finally:
            conn.close()

    def reconcile(self, transaction_id: int) -> dict:
        conn = self.db.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("UPDATE bank_transactions SET reconciled=1 WHERE id=?", (transaction_id,))
            conn.commit()
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            conn.close()

    def unreconciled_transactions(self, bank_account_id: int) -> list:
        conn = self.db.get_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM bank_transactions WHERE bank_account_id=? AND reconciled=0 ORDER BY transaction_date DESC",
            (bank_account_id,)
        )
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return rows
