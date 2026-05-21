"""
Devil ERP — HR Manager
Employee management, attendance, payroll
"""
import datetime
from database.db_manager import DBManager


class HRManager:
    def __init__(self, db: DBManager):
        self.db = db

    def add_employee(self, emp_id, name, department, designation,
                     phone="", email="", join_date=None, basic_salary=0):
        join_date = join_date or datetime.date.today().isoformat()
        self.db.execute("""
            INSERT INTO employees
            (emp_id, name, department, designation, phone, email,
             join_date, basic_salary)
            VALUES (?,?,?,?,?,?,?,?)
        """, (emp_id, name, department, designation,
               phone, email, join_date, basic_salary))

    def get_employees(self, active_only=True):
        if active_only:
            return self.db.fetchall(
                "SELECT * FROM employees WHERE is_active=1 ORDER BY name"
            )
        return self.db.fetchall("SELECT * FROM employees ORDER BY name")

    def mark_attendance(self, employee_id, status="present",
                        in_time=None, out_time=None):
        date = datetime.date.today().isoformat()
        existing = self.db.fetchone(
            "SELECT id FROM attendance WHERE employee_id=? AND date=?",
            (employee_id, date)
        )
        if existing:
            self.db.execute(
                "UPDATE attendance SET status=?, in_time=?, out_time=? WHERE id=?",
                (status, in_time, out_time, existing[0])
            )
        else:
            self.db.execute("""
                INSERT INTO attendance (employee_id, date, status, in_time, out_time)
                VALUES (?,?,?,?,?)
            """, (employee_id, date, status, in_time, out_time))

    def get_attendance(self, employee_id=None, month=None):
        if employee_id and month:
            return self.db.fetchall("""
                SELECT a.*, e.name
                FROM attendance a JOIN employees e ON a.employee_id=e.id
                WHERE a.employee_id=? AND strftime('%Y-%m', a.date)=?
                ORDER BY a.date
            """, (employee_id, month))
        return self.db.fetchall(
            "SELECT a.*, e.name FROM attendance a JOIN employees e ON a.employee_id=e.id ORDER BY a.date DESC LIMIT 100"
        )

    def generate_payslip(self, employee_id, month):
        emp = self.db.fetchone(
            "SELECT * FROM employees WHERE id=?", (employee_id,)
        )
        if not emp:
            return None

        present_days = self.db.fetchone("""
            SELECT COUNT(*) FROM attendance
            WHERE employee_id=? AND status='present'
            AND strftime('%Y-%m', date)=?
        """, (employee_id, month))

        basic = emp[8]
        days_present = present_days[0] if present_days else 0
        # Assume 26 working days per month
        earned = round(basic * days_present / 26, 2)
        pf = round(earned * 0.12, 2)
        net = round(earned - pf, 2)

        return {
            "employee": emp[2],
            "emp_id": emp[1],
            "department": emp[3],
            "month": month,
            "basic": basic,
            "days_present": days_present,
            "earned": earned,
            "pf_deduction": pf,
            "net_salary": net
        }
