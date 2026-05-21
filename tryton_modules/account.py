"""
Devil ERP — Accounting Module (Tryton account)
Developed by Devil One Pvt Ltd & Nexuzy Lab
Lead Developer: David K. Angel

Wraps trytond account module with Devil ERP enhancements:
- GST support (CGST, SGST, IGST)
- Indian chart of accounts
- Rupee formatting
- Trial balance, P&L, Balance Sheet
"""
from database.db_manager import DBManager
from datetime import datetime, date
from decimal import Decimal


class ChartOfAccounts:
    """Indian Chart of Accounts with GST accounts built-in."""

    ACCOUNT_TYPES = [
        "asset", "liability", "equity", "income", "expense", "tax"
    ]

    def __init__(self):
        self.db = DBManager()
        self._ensure_tables()

    def _ensure_tables(self):
        conn = self.db.get_connection()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS chart_accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                account_type TEXT NOT NULL,
                parent_code TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TEXT
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS journal_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entry_date TEXT NOT NULL,
                reference TEXT,
                description TEXT,
                debit_account TEXT NOT NULL,
                credit_account TEXT NOT NULL,
                amount REAL NOT NULL,
                entry_type TEXT DEFAULT 'manual',
                created_at TEXT
            )
        """)
        conn.commit()
        self._seed_default_accounts(cur, conn)
        conn.close()

    def _seed_default_accounts(self, cur, conn):
        defaults = [
            # Assets
            ("1000", "Cash in Hand", "asset", None),
            ("1001", "Bank Account", "asset", None),
            ("1100", "Accounts Receivable", "asset", None),
            ("1200", "Inventory / Stock", "asset", None),
            ("1300", "Fixed Assets", "asset", None),
            # Liabilities
            ("2000", "Accounts Payable", "liability", None),
            ("2100", "GST Payable - CGST", "tax", None),
            ("2101", "GST Payable - SGST", "tax", None),
            ("2102", "GST Payable - IGST", "tax", None),
            ("2200", "TDS Payable", "liability", None),
            ("2300", "Salary Payable", "liability", None),
            # Equity
            ("3000", "Owner Capital", "equity", None),
            ("3100", "Retained Earnings", "equity", None),
            # Income
            ("4000", "Sales Revenue", "income", None),
            ("4100", "Service Revenue", "income", None),
            ("4200", "Other Income", "income", None),
            # Expenses
            ("5000", "Cost of Goods Sold", "expense", None),
            ("5100", "Salary Expense", "expense", None),
            ("5200", "Rent Expense", "expense", None),
            ("5300", "Electricity Expense", "expense", None),
            ("5400", "Marketing Expense", "expense", None),
            ("5500", "Miscellaneous Expense", "expense", None),
            # GST Input
            ("1400", "GST Input - CGST", "asset", None),
            ("1401", "GST Input - SGST", "asset", None),
            ("1402", "GST Input - IGST", "asset", None),
        ]
        for code, name, atype, parent in defaults:
            cur.execute(
                "INSERT OR IGNORE INTO chart_accounts (code, name, account_type, parent_code, created_at) VALUES (?,?,?,?,?)",
                (code, name, atype, parent, datetime.now().isoformat())
            )
        conn.commit()

    def get_all_accounts(self) -> list:
        conn = self.db.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM chart_accounts WHERE is_active=1 ORDER BY code")
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return rows

    def get_account_by_type(self, account_type: str) -> list:
        conn = self.db.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM chart_accounts WHERE account_type=? AND is_active=1 ORDER BY code", (account_type,))
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return rows

    def add_account(self, code: str, name: str, account_type: str, parent_code: str = None) -> dict:
        if account_type not in self.ACCOUNT_TYPES:
            return {"success": False, "error": f"Invalid type. Use: {self.ACCOUNT_TYPES}"}
        conn = self.db.get_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                "INSERT INTO chart_accounts (code, name, account_type, parent_code, created_at) VALUES (?,?,?,?,?)",
                (code, name, account_type, parent_code, datetime.now().isoformat())
            )
            conn.commit()
            return {"success": True, "id": cur.lastrowid}
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            conn.close()


class GeneralLedger:
    """General Ledger — Journal entry management."""

    def __init__(self):
        self.db = DBManager()
        self.coa = ChartOfAccounts()

    def post_entry(self, entry_date: str, description: str,
                   debit_account: str, credit_account: str,
                   amount: float, reference: str = "",
                   entry_type: str = "manual") -> dict:
        if amount <= 0:
            return {"success": False, "error": "Amount must be positive"}
        conn = self.db.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                INSERT INTO journal_entries
                (entry_date, reference, description, debit_account, credit_account, amount, entry_type, created_at)
                VALUES (?,?,?,?,?,?,?,?)
            """, (entry_date, reference, description, debit_account,
                  credit_account, amount, entry_type, datetime.now().isoformat()))
            conn.commit()
            return {"success": True, "entry_id": cur.lastrowid}
        except Exception as e:
            conn.rollback()
            return {"success": False, "error": str(e)}
        finally:
            conn.close()

    def get_ledger(self, account_code: str = None,
                   from_date: str = None, to_date: str = None) -> list:
        conn = self.db.get_connection()
        cur = conn.cursor()
        query = "SELECT * FROM journal_entries WHERE 1=1"
        params = []
        if account_code:
            query += " AND (debit_account=? OR credit_account=?)"
            params += [account_code, account_code]
        if from_date:
            query += " AND entry_date >= ?"
            params.append(from_date)
        if to_date:
            query += " AND entry_date <= ?"
            params.append(to_date)
        query += " ORDER BY entry_date DESC"
        cur.execute(query, params)
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return rows

    def trial_balance(self, from_date: str = None, to_date: str = None) -> dict:
        """Returns trial balance: {account_code: {debit, credit, balance}}."""
        entries = self.get_ledger(from_date=from_date, to_date=to_date)
        balances = {}
        for e in entries:
            for acc, side in [(e["debit_account"], "debit"), (e["credit_account"], "credit")]:
                if acc not in balances:
                    balances[acc] = {"debit": 0.0, "credit": 0.0}
                balances[acc][side] += e["amount"]
        for acc in balances:
            balances[acc]["balance"] = balances[acc]["debit"] - balances[acc]["credit"]
        return balances

    def profit_and_loss(self, from_date: str = None, to_date: str = None) -> dict:
        tb = self.trial_balance(from_date, to_date)
        coa = self.coa.get_all_accounts()
        coa_map = {a["code"]: a for a in coa}
        income_total = 0.0
        expense_total = 0.0
        income_details = {}
        expense_details = {}
        for code, data in tb.items():
            acc = coa_map.get(code)
            if not acc:
                continue
            if acc["account_type"] == "income":
                val = data["credit"] - data["debit"]
                income_total += val
                income_details[acc["name"]] = val
            elif acc["account_type"] == "expense":
                val = data["debit"] - data["credit"]
                expense_total += val
                expense_details[acc["name"]] = val
        return {
            "income": income_details,
            "expense": expense_details,
            "total_income": income_total,
            "total_expense": expense_total,
            "net_profit": income_total - expense_total,
        }
