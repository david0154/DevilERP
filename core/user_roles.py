"""
Devil ERP — User Roles & Permission System
Developed by Devil One Pvt Ltd & Nexuzy Lab
Lead Developer: David K. Angel
"""

ROLES = {
    "owner": {
        "label": "Owner",
        "color": "#C62828",
        "permissions": [
            "full_erp", "ai_analytics", "financial_reports",
            "employee_monitoring", "user_management", "settings",
            "billing", "inventory", "accounting", "hr", "backup",
            "ocr_scan", "reports", "purchase", "sales", "crm",
            "manufacturing", "projects", "payroll", "pos",
            "shipping", "quality", "marketing", "timesheet",
            "analytic_account"
        ]
    },
    "manager": {
        "label": "Manager",
        "color": "#1565C0",
        "permissions": [
            "billing", "inventory", "reports", "staff_management",
            "purchase", "sales", "ocr_scan", "crm", "pos",
            "shipping", "quality", "timesheet"
        ]
    },
    "employee": {
        "label": "Employee",
        "color": "#2E7D32",
        "permissions": [
            "pos_billing", "limited_inventory", "customer_billing", "timesheet"
        ]
    }
}


def get_permissions(role: str) -> list:
    return ROLES.get(role, {}).get("permissions", [])


def has_permission(role: str, permission: str) -> bool:
    return permission in get_permissions(role)


def get_role_label(role: str) -> str:
    return ROLES.get(role, {}).get("label", "Unknown")


def get_role_color(role: str) -> str:
    return ROLES.get(role, {}).get("color", "#888888")


def get_all_roles() -> list:
    return list(ROLES.keys())
