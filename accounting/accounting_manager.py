"""
Devil ERP — Accounting Manager
General Ledger, Journal Entries, Trial Balance, P&L, Balance Sheet
"""
import datetime
from database.db_manager import DBManager


class AccountingManager:
    def __init__(self, db: DBManager):
        self.db = db

    def create_journal_entry(self, date, description, lines, reference="", created_by=None):
        """
        lines: list of {account_id, debit, credit, description}
        """
        total_debit = sum(l.get("debit", 0) for l in lines)
        total_credit = sum(l.get("credit", 0) for l in lines)
        if abs(total_debit - total_credit) > 0.01:
            raise ValueError(f"Journal not balanced: Debit={total_debit} Credit={total_credit}")

        self.db.execute("""
            INSERT INTO journal_entries (date, reference, description, created_by, state)
            VALUES (?,?,?,?,?)
        """, (date, reference, description, created_by, "posted"))

        je = self.db.fetchone(
            "SELECT id FROM journal_entries ORDER BY id DESC LIMIT 1"
        )
        je_id = je[0]

        for l in lines:
            self.db.execute("""
                INSERT INTO journal_lines (journal_id, account_id, debit, credit, description)
                VALUES (?,?,?,?,?)
            """, (je_id, l["account_id"], l.get("debit", 0),
                   l.get("credit", 0), l.get("description", "")))
        return je_id

    def get_trial_balance(self):
        """Returns list of (account_code, account_name, total_debit, total_credit)"""
        return self.db.fetchall("""
            SELECT coa.code, coa.name, coa.account_type,
                   COALESCE(SUM(jl.debit), 0) as total_debit,
                   COALESCE(SUM(jl.credit), 0) as total_credit
            FROM chart_of_accounts coa
            LEFT JOIN journal_lines jl ON jl.account_id = coa.id
            GROUP BY coa.id
            ORDER BY coa.code
        """)

    def get_profit_loss(self, from_date=None, to_date=None):
        from_date = from_date or "2000-01-01"
        to_date = to_date or datetime.date.today().isoformat()

        income = self.db.fetchone("""
            SELECT COALESCE(SUM(jl.credit - jl.debit), 0)
            FROM journal_lines jl
            JOIN journal_entries je ON jl.journal_id=je.id
            JOIN chart_of_accounts coa ON jl.account_id=coa.id
            WHERE coa.account_type='income'
            AND date(je.date) BETWEEN ? AND ?
        """, (from_date, to_date))

        expense = self.db.fetchone("""
            SELECT COALESCE(SUM(jl.debit - jl.credit), 0)
            FROM journal_lines jl
            JOIN journal_entries je ON jl.journal_id=je.id
            JOIN chart_of_accounts coa ON jl.account_id=coa.id
            WHERE coa.account_type='expense'
            AND date(je.date) BETWEEN ? AND ?
        """, (from_date, to_date))

        total_income = income[0] or 0
        total_expense = expense[0] or 0
        return {
            "income": round(total_income, 2),
            "expense": round(total_expense, 2),
            "net_profit": round(total_income - total_expense, 2),
            "from_date": from_date,
            "to_date": to_date
        }

    def get_accounts(self, account_type=None):
        if account_type:
            return self.db.fetchall(
                "SELECT * FROM chart_of_accounts WHERE account_type=? AND is_active=1 ORDER BY code",
                (account_type,)
            )
        return self.db.fetchall(
            "SELECT * FROM chart_of_accounts WHERE is_active=1 ORDER BY code"
        )
