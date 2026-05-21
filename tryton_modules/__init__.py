"""
Devil ERP — Tryton Modules Integration Layer
Developed by Devil One Pvt Ltd & Nexuzy Lab
Lead Developer: David K. Angel

This package integrates all Tryton ERP modules into Devil ERP.
Each sub-module wraps the corresponding trytond module with
Devil ERP’s offline-first, Indian-market enhancements.
"""

MODULES = [
    # Accounting
    "account",
    "account_invoice",
    "account_asset",
    "account_tax",
    "account_statement",
    # Sales & Purchase
    "sale",
    "sale_point",
    "purchase",
    # Inventory & Production
    "stock",
    "stock_package",
    "production",
    "quality_control",
    # HR & Payroll
    "company_employee",
    "payroll",
    "timesheet",
    # CRM & Projects
    "crm",
    "project",
    # Reporting & Marketing
    "analytic_account",
    "marketing",
]

__all__ = MODULES
