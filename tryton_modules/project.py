"""
Devil ERP — Project Management Module (Tryton project)
Developed by Devil One Pvt Ltd & Nexuzy Lab
Lead Developer: David K. Angel

Features: Projects, Tasks, Teams, Time tracking,
Resource management, Progress tracking
"""
from database.db_manager import DBManager
from datetime import datetime


TASK_STATUS = ["todo", "in_progress", "review", "done", "cancelled"]
PRIORITY = ["low", "medium", "high", "urgent"]


class ProjectModule:
    """Project and task management."""

    def __init__(self):
        self.db = DBManager()
        self._ensure_tables()

    def _ensure_tables(self):
        conn = self.db.get_connection()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT DEFAULT '',
                start_date TEXT,
                end_date TEXT,
                status TEXT DEFAULT 'active',
                customer_id INTEGER,
                budget REAL DEFAULT 0,
                created_at TEXT
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                assigned_to TEXT DEFAULT '',
                status TEXT DEFAULT 'todo',
                priority TEXT DEFAULT 'medium',
                due_date TEXT,
                estimated_hours REAL DEFAULT 0,
                actual_hours REAL DEFAULT 0,
                created_at TEXT,
                FOREIGN KEY(project_id) REFERENCES projects(id)
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS timesheets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER,
                employee_id INTEGER,
                work_date TEXT,
                hours REAL,
                description TEXT,
                created_at TEXT,
                FOREIGN KEY(task_id) REFERENCES tasks(id)
            )
        """)
        conn.commit()
        conn.close()

    def create_project(self, name: str, description: str = "",
                       start_date: str = None, end_date: str = None,
                       customer_id: int = None, budget: float = 0) -> dict:
        conn = self.db.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                INSERT INTO projects (name, description, start_date, end_date, customer_id, budget, created_at)
                VALUES (?,?,?,?,?,?,?)
            """, (name, description, start_date or datetime.now().strftime("%Y-%m-%d"),
                  end_date, customer_id, budget, datetime.now().isoformat()))
            conn.commit()
            return {"success": True, "project_id": cur.lastrowid}
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            conn.close()

    def add_task(self, project_id: int, title: str, assigned_to: str = "",
                 priority: str = "medium", due_date: str = None,
                 estimated_hours: float = 0) -> dict:
        conn = self.db.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                INSERT INTO tasks
                (project_id, title, assigned_to, priority, due_date, estimated_hours, created_at)
                VALUES (?,?,?,?,?,?,?)
            """, (project_id, title, assigned_to, priority, due_date,
                  estimated_hours, datetime.now().isoformat()))
            conn.commit()
            return {"success": True, "task_id": cur.lastrowid}
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            conn.close()

    def log_time(self, task_id: int, employee_id: int, hours: float,
                 description: str = "", work_date: str = None) -> dict:
        conn = self.db.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                INSERT INTO timesheets (task_id, employee_id, work_date, hours, description, created_at)
                VALUES (?,?,?,?,?,?)
            """, (task_id, employee_id, work_date or datetime.now().strftime("%Y-%m-%d"),
                  hours, description, datetime.now().isoformat()))
            cur.execute(
                "UPDATE tasks SET actual_hours = actual_hours + ? WHERE id=?",
                (hours, task_id)
            )
            conn.commit()
            return {"success": True}
        except Exception as e:
            conn.rollback()
            return {"success": False, "error": str(e)}
        finally:
            conn.close()
