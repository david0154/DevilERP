"""
Devil ERP — Company & Employee Module (Tryton company_employee)
Developed by Devil One Pvt Ltd & Nexuzy Lab
Lead Developer: David K. Angel

Features: Company management, Employee database,
Departments, Attendance, Roles, Leave management
"""
from database.db_manager import DBManager
from datetime import datetime


class CompanyEmployeeModule:
    """Company structure and employee management."""

    def __init__(self):
        self.db = DBManager()
        self._ensure_tables()

    def _ensure_tables(self):
        conn = self.db.get_connection()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS departments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                head_employee_id INTEGER,
                created_at TEXT
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id INTEGER NOT NULL,
                attendance_date TEXT NOT NULL,
                check_in TEXT,
                check_out TEXT,
                status TEXT DEFAULT 'present',
                work_hours REAL DEFAULT 0,
                notes TEXT DEFAULT '',
                created_at TEXT
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS leaves (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id INTEGER NOT NULL,
                leave_type TEXT DEFAULT 'casual',
                from_date TEXT NOT NULL,
                to_date TEXT NOT NULL,
                days INTEGER DEFAULT 1,
                reason TEXT DEFAULT '',
                status TEXT DEFAULT 'pending',
                approved_by TEXT DEFAULT '',
                created_at TEXT
            )
        """)
        conn.commit()
        conn.close()

    def add_department(self, name: str) -> dict:
        conn = self.db.get_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                "INSERT INTO departments (name, created_at) VALUES (?,?)",
                (name, datetime.now().isoformat())
            )
            conn.commit()
            return {"success": True, "department_id": cur.lastrowid}
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            conn.close()

    def mark_attendance(self, employee_id: int, status: str = "present",
                        check_in: str = None, check_out: str = None,
                        attendance_date: str = None) -> dict:
        conn = self.db.get_connection()
        cur = conn.cursor()
        date = attendance_date or datetime.now().strftime("%Y-%m-%d")
        work_hours = 0
        if check_in and check_out:
            try:
                from datetime import datetime as dt
                ci = dt.strptime(check_in, "%H:%M")
                co = dt.strptime(check_out, "%H:%M")
                work_hours = max((co - ci).seconds / 3600, 0)
            except Exception:
                pass
        try:
            cur.execute("""
                INSERT OR REPLACE INTO attendance
                (employee_id, attendance_date, check_in, check_out, status, work_hours, created_at)
                VALUES (?,?,?,?,?,?,?)
            """, (employee_id, date, check_in, check_out, status,
                  round(work_hours, 2), datetime.now().isoformat()))
            conn.commit()
            return {"success": True, "work_hours": round(work_hours, 2)}
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            conn.close()

    def apply_leave(self, employee_id: int, leave_type: str,
                    from_date: str, to_date: str, reason: str = "") -> dict:
        from datetime import date
        try:
            d1 = datetime.strptime(from_date, "%Y-%m-%d").date()
            d2 = datetime.strptime(to_date, "%Y-%m-%d").date()
            days = (d2 - d1).days + 1
        except Exception:
            days = 1
        conn = self.db.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                INSERT INTO leaves (employee_id, leave_type, from_date, to_date, days, reason, created_at)
                VALUES (?,?,?,?,?,?,?)
            """, (employee_id, leave_type, from_date, to_date, days, reason,
                  datetime.now().isoformat()))
            conn.commit()
            return {"success": True, "days": days, "leave_id": cur.lastrowid}
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            conn.close()

    def monthly_attendance_report(self, employee_id: int, year: int, month: int) -> dict:
        conn = self.db.get_connection()
        cur = conn.cursor()
        period = f"{year}-{month:02d}"
        cur.execute("""
            SELECT status, COUNT(*) as count FROM attendance
            WHERE employee_id=? AND strftime('%Y-%m', attendance_date)=?
            GROUP BY status
        """, (employee_id, period))
        summary = {r["status"]: r["count"] for r in cur.fetchall()}
        conn.close()
        return summary
