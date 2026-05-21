"""
Devil ERP — Payroll Module (Tryton payroll)
Developed by Devil One Pvt Ltd & Nexuzy Lab
Lead Developer: David K. Angel

Features: Salary structure, Payroll generation,
Payslips, TDS, PF, ESI, Indian payroll compliance
"""
from database.db_manager import DBManager
from datetime import datetime


class PayrollModule:
    """Indian payroll management."""

    # Standard Indian deductions
    PF_RATE = 0.12       # 12% of Basic
    ESI_RATE = 0.0075    # 0.75% employee
    TDS_THRESHOLD = 250000  # Annual TDS threshold

    def __init__(self):
        self.db = DBManager()
        self._ensure_tables()

    def _ensure_tables(self):
        conn = self.db.get_connection()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS salary_structures (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id INTEGER UNIQUE,
                basic REAL DEFAULT 0,
                hra REAL DEFAULT 0,
                da REAL DEFAULT 0,
                conveyance REAL DEFAULT 0,
                medical REAL DEFAULT 0,
                other_allowances REAL DEFAULT 0,
                pf_applicable INTEGER DEFAULT 1,
                esi_applicable INTEGER DEFAULT 1,
                tds_applicable INTEGER DEFAULT 0,
                created_at TEXT
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS payslips (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id INTEGER,
                month TEXT NOT NULL,
                year INTEGER NOT NULL,
                working_days INTEGER DEFAULT 26,
                present_days INTEGER DEFAULT 26,
                basic REAL DEFAULT 0,
                hra REAL DEFAULT 0,
                da REAL DEFAULT 0,
                conveyance REAL DEFAULT 0,
                medical REAL DEFAULT 0,
                other_allowances REAL DEFAULT 0,
                gross_salary REAL DEFAULT 0,
                pf_deduction REAL DEFAULT 0,
                esi_deduction REAL DEFAULT 0,
                tds_deduction REAL DEFAULT 0,
                other_deductions REAL DEFAULT 0,
                total_deductions REAL DEFAULT 0,
                net_salary REAL DEFAULT 0,
                status TEXT DEFAULT 'generated',
                payment_date TEXT,
                created_at TEXT
            )
        """)
        conn.commit()
        conn.close()

    def set_salary_structure(self, employee_id: int, basic: float,
                              hra: float = 0, da: float = 0,
                              conveyance: float = 0, medical: float = 0,
                              other_allowances: float = 0) -> dict:
        conn = self.db.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                INSERT OR REPLACE INTO salary_structures
                (employee_id, basic, hra, da, conveyance, medical, other_allowances, created_at)
                VALUES (?,?,?,?,?,?,?,?)
            """, (employee_id, basic, hra, da, conveyance, medical, other_allowances,
                  datetime.now().isoformat()))
            conn.commit()
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            conn.close()

    def generate_payslip(self, employee_id: int, month: str, year: int,
                         present_days: int = 26, working_days: int = 26,
                         other_deductions: float = 0) -> dict:
        conn = self.db.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM salary_structures WHERE employee_id=?", (employee_id,))
        ss = cur.fetchone()
        if not ss:
            conn.close()
            return {"success": False, "error": "No salary structure found for employee"}
        ss = dict(ss)
        # Pro-rate
        factor = present_days / max(working_days, 1)
        basic = round(ss["basic"] * factor, 2)
        hra = round(ss["hra"] * factor, 2)
        da = round(ss["da"] * factor, 2)
        conveyance = round(ss["conveyance"] * factor, 2)
        medical = round(ss["medical"] * factor, 2)
        other = round(ss["other_allowances"] * factor, 2)
        gross = basic + hra + da + conveyance + medical + other
        pf = round(basic * self.PF_RATE, 2) if ss["pf_applicable"] else 0
        esi = round(gross * self.ESI_RATE, 2) if ss["esi_applicable"] and gross <= 21000 else 0
        tds = round(gross * 0.05, 2) if ss["tds_applicable"] and (gross * 12) > self.TDS_THRESHOLD else 0
        total_ded = pf + esi + tds + other_deductions
        net = round(gross - total_ded, 2)
        try:
            cur.execute("""
                INSERT INTO payslips
                (employee_id, month, year, working_days, present_days,
                 basic, hra, da, conveyance, medical, other_allowances,
                 gross_salary, pf_deduction, esi_deduction, tds_deduction,
                 other_deductions, total_deductions, net_salary, created_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (employee_id, month, year, working_days, present_days,
                  basic, hra, da, conveyance, medical, other,
                  round(gross, 2), pf, esi, tds, other_deductions,
                  round(total_ded, 2), net, datetime.now().isoformat()))
            conn.commit()
            return {
                "success": True,
                "payslip_id": cur.lastrowid,
                "gross": round(gross, 2),
                "deductions": round(total_ded, 2),
                "net": net,
            }
        except Exception as e:
            conn.rollback()
            return {"success": False, "error": str(e)}
        finally:
            conn.close()
