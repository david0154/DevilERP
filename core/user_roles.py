"""
Devil ERP — User Roles & Permissions
Developed by Devil One Pvt Ltd & Nexuzy Lab
Lead Developer: David K. Angel
Contact: nexuzylab@gmail.com | devilonepvtltd@gmail.com
"""

ROLES = {
    "owner": {
        "label": "Owner",
        "color": "#FF5722",
        "permissions": [
            "full_erp", "ai_analytics", "financial_reports",
            "employee_monitoring", "user_management", "settings",
            "billing", "inventory", "accounting", "hr", "backup",
            "ocr_scan", "reports", "purchase", "sales", "crm",
            "manufacturing", "projects", "pos", "payroll"
        ]
    },
    "manager": {
        "label": "Manager",
        "color": "#2196F3",
        "permissions": [
            "billing", "inventory", "reports", "staff_management",
            "purchase", "sales", "ocr_scan", "crm", "pos"
        ]
    },
    "employee": {
        "label": "Employee",
        "color": "#4CAF50",
        "permissions": [
            "pos_billing", "limited_inventory", "customer_billing"
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


def all_roles() -> list:
    return list(ROLES.keys())
