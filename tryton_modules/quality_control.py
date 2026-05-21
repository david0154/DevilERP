"""
Devil ERP — Quality Control Module (Tryton quality_control)
Developed by Devil One Pvt Ltd & Nexuzy Lab
Lead Developer: David K. Angel

Features: QC checks, Inspection templates, Pass/Fail tracking,
Defect logging, Quality reports
"""
from database.db_manager import DBManager
from datetime import datetime


QC_RESULT = ["pass", "fail", "conditional"]


class QualityControlModule:
    """Quality inspection and control."""

    def __init__(self):
        self.db = DBManager()
        self._ensure_tables()

    def _ensure_tables(self):
        conn = self.db.get_connection()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS qc_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                product_id INTEGER,
                checkpoints TEXT NOT NULL,
                is_active INTEGER DEFAULT 1,
                created_at TEXT
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS qc_inspections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                template_id INTEGER,
                reference_type TEXT DEFAULT '',
                reference_id INTEGER,
                inspector TEXT DEFAULT '',
                inspection_date TEXT,
                result TEXT DEFAULT 'pending',
                remarks TEXT DEFAULT '',
                checkpoint_results TEXT DEFAULT '{}',
                created_at TEXT,
                FOREIGN KEY(template_id) REFERENCES qc_templates(id)
            )
        """)
        conn.commit()
        conn.close()

    def create_template(self, name: str, checkpoints: list,
                        product_id: int = None) -> dict:
        import json
        conn = self.db.get_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                "INSERT INTO qc_templates (name, product_id, checkpoints, created_at) VALUES (?,?,?,?)",
                (name, product_id, json.dumps(checkpoints), datetime.now().isoformat())
            )
            conn.commit()
            return {"success": True, "template_id": cur.lastrowid}
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            conn.close()

    def record_inspection(self, template_id: int, inspector: str,
                          checkpoint_results: dict, reference_type: str = "",
                          reference_id: int = None, remarks: str = "") -> dict:
        import json
        passed = sum(1 for v in checkpoint_results.values() if v)
        total = len(checkpoint_results)
        result = "pass" if passed == total else ("conditional" if passed / max(total, 1) >= 0.7 else "fail")
        conn = self.db.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                INSERT INTO qc_inspections
                (template_id, reference_type, reference_id, inspector,
                 inspection_date, result, remarks, checkpoint_results, created_at)
                VALUES (?,?,?,?,?,?,?,?,?)
            """, (template_id, reference_type, reference_id, inspector,
                  datetime.now().strftime("%Y-%m-%d"), result, remarks,
                  json.dumps(checkpoint_results), datetime.now().isoformat()))
            conn.commit()
            return {"success": True, "result": result, "pass_rate": f"{passed}/{total}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            conn.close()
