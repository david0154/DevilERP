"""
Devil ERP — Firebase Authentication Module
Handles login, logout, device verification, password recovery.
User roles: owner / manager / employee
"""

import json
from pathlib import Path
from core.config import FIREBASE_API_KEY, FIREBASE_AUTH_DOMAIN, FIREBASE_PROJECT_ID, BASE_DIR

SESSION_FILE = BASE_DIR / "auth" / ".session.json"

class FirebaseAuth:
    def __init__(self):
        self._user = None
        self._load_session()

    def _load_session(self):
        if SESSION_FILE.exists():
            try:
                with open(SESSION_FILE) as f:
                    self._user = json.load(f)
            except Exception:
                self._user = None

    def _save_session(self, user_data: dict):
        SESSION_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(SESSION_FILE, "w") as f:
            json.dump(user_data, f)
        self._user = user_data

    def is_logged_in(self) -> bool:
        return self._user is not None

    def current_user(self) -> dict:
        return self._user or {}

    def login(self, email: str, password: str) -> dict:
        """
        Authenticate user via Firebase REST API.
        Returns user dict with role on success.
        """
        import requests
        url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_API_KEY}"
        payload = {"email": email, "password": password, "returnSecureToken": True}
        resp = requests.post(url, json=payload)
        data = resp.json()
        if "idToken" in data:
            user = {
                "uid": data["localId"],
                "email": data["email"],
                "token": data["idToken"],
                "role": "owner",  # Fetch from Firestore/DB in production
            }
            self._save_session(user)
            return {"success": True, "user": user}
        return {"success": False, "error": data.get("error", {}).get("message", "Login failed")}

    def logout(self):
        self._user = None
        if SESSION_FILE.exists():
            SESSION_FILE.unlink()

    def reset_password(self, email: str) -> dict:
        import requests
        url = f"https://identitytoolkit.googleapis.com/v1/accounts:sendOobCode?key={FIREBASE_API_KEY}"
        payload = {"requestType": "PASSWORD_RESET", "email": email}
        resp = requests.post(url, json=payload)
        data = resp.json()
        if "email" in data:
            return {"success": True}
        return {"success": False, "error": data.get("error", {}).get("message")}


USER_ROLES = {
    "owner": [
        "full_erp", "ai_analytics", "financial_reports",
        "employee_monitoring", "settings", "backup",
    ],
    "manager": [
        "inventory", "billing", "reports", "staff_management",
    ],
    "employee": [
        "pos_billing", "limited_inventory", "customer_billing",
    ],
}

def has_permission(user: dict, permission: str) -> bool:
    role = user.get("role", "employee")
    return permission in USER_ROLES.get(role, [])
