"""
Tryton ERP Engine Initialization
Configures and boots the Tryton backend for Devil ERP.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_DIR = BASE_DIR / "database"

def get_tryton_config():
    """Return Tryton configuration dictionary."""
    return {
        "database": {
            "uri": os.getenv("DEVIL_ERP_DB_URI", f"sqlite:///{DB_DIR}/devil_erp.sqlite"),
        },
        "web": {
            "listen": "127.0.0.1:8000",
        },
        "session": {
            "timeout": 3600,
        },
    }

def init_tryton():
    """Bootstrap Tryton with Devil ERP configuration."""
    try:
        import trytond.pool as pool
        config = get_tryton_config()
        print(f"[DevilERP] Tryton engine initializing with DB: {config['database']['uri']}")
        return True
    except ImportError:
        print("[DevilERP] Tryton not installed. Run: pip install trytond")
        return False
