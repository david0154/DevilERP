"""
Devil ERP — CRM Module (Tryton crm)
Developed by Devil One Pvt Ltd & Nexuzy Lab
Lead Developer: David K. Angel

Features: Leads, Opportunities, Follow-ups,
Customer communication, Pipeline tracking
"""
from database.db_manager import DBManager
from datetime import datetime


LEAD_STATUS = ["new", "contacted", "qualified", "proposal", "negotiation", "won", "lost"]


class CRMModule:
    """CRM — Lead and opportunity management."""

    def __init__(self):
        self.db = DBManager()
        self._ensure_tables()

    def _ensure_tables(self):
        conn = self.db.get_connection()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                company TEXT DEFAULT '',
                phone TEXT DEFAULT '',
                email TEXT DEFAULT '',
                source TEXT DEFAULT '',
                status TEXT DEFAULT 'new',
                expected_value REAL DEFAULT 0,
                assigned_to TEXT DEFAULT '',
                next_followup TEXT DEFAULT '',
                notes TEXT DEFAULT '',
                created_at TEXT
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS followups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lead_id INTEGER NOT NULL,
                followup_date TEXT NOT NULL,
                contact_mode TEXT DEFAULT 'call',
                summary TEXT DEFAULT '',
                next_action TEXT DEFAULT '',
                done INTEGER DEFAULT 0,
                created_at TEXT,
                FOREIGN KEY(lead_id) REFERENCES leads(id)
            )
        """)
        conn.commit()
        conn.close()

    def add_lead(self, name: str, phone: str = "", email: str = "",
                 company: str = "", source: str = "",
                 expected_value: float = 0) -> dict:
        conn = self.db.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                INSERT INTO leads (name, company, phone, email, source, expected_value, created_at)
                VALUES (?,?,?,?,?,?,?)
            """, (name, company, phone, email, source, expected_value,
                  datetime.now().isoformat()))
            conn.commit()
            return {"success": True, "lead_id": cur.lastrowid}
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            conn.close()

    def update_lead_status(self, lead_id: int, status: str) -> dict:
        if status not in LEAD_STATUS:
            return {"success": False, "error": f"Invalid status. Use: {LEAD_STATUS}"}
        conn = self.db.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("UPDATE leads SET status=? WHERE id=?", (status, lead_id))
            conn.commit()
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            conn.close()

    def add_followup(self, lead_id: int, followup_date: str,
                     contact_mode: str = "call", summary: str = "",
                     next_action: str = "") -> dict:
        conn = self.db.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                INSERT INTO followups (lead_id, followup_date, contact_mode, summary, next_action, created_at)
                VALUES (?,?,?,?,?,?)
            """, (lead_id, followup_date, contact_mode, summary, next_action,
                  datetime.now().isoformat()))
            cur.execute("UPDATE leads SET next_followup=? WHERE id=?", (followup_date, lead_id))
            conn.commit()
            return {"success": True, "followup_id": cur.lastrowid}
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            conn.close()

    def get_pipeline(self) -> dict:
        """Return leads grouped by status."""
        conn = self.db.get_connection()
        cur = conn.cursor()
        pipeline = {}
        for status in LEAD_STATUS:
            cur.execute(
                "SELECT COUNT(*), COALESCE(SUM(expected_value),0) FROM leads WHERE status=?",
                (status,)
            )
            row = cur.fetchone()
            pipeline[status] = {"count": row[0], "total_value": row[1]}
        conn.close()
        return pipeline

    def today_followups(self) -> list:
        conn = self.db.get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT f.*, l.name as lead_name, l.phone FROM followups f
            JOIN leads l ON f.lead_id=l.id
            WHERE DATE(f.followup_date)=DATE('now') AND f.done=0
            ORDER BY f.followup_date ASC
        """)
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return rows
