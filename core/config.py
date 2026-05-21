"""
Devil ERP Global Configuration
"""

import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# ── Database ───────────────────────────────────────────────
DB_TYPE = os.getenv("DB_TYPE", "sqlite")        # "sqlite" or "postgresql"
DB_URI = os.getenv("DEVIL_ERP_DB_URI", f"sqlite:///{BASE_DIR}/database/devil_erp.sqlite")

# ── AI Models ─────────────────────────────────────────────
MODELS_DIR = BASE_DIR / "models"
AI_MODEL_FILE = MODELS_DIR / "gemma-2b-cpu.gguf"
EMBEDDINGS_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# ── Firebase ──────────────────────────────────────────────
FIREBASE_API_KEY = os.getenv("FIREBASE_API_KEY", "")
FIREBASE_AUTH_DOMAIN = os.getenv("FIREBASE_AUTH_DOMAIN", "")
FIREBASE_PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID", "")

# ── Google Drive ──────────────────────────────────────────
GDRIVE_CREDENTIALS_FILE = BASE_DIR / "backup" / "gdrive_credentials.json"
GDRIVE_BACKUP_FOLDER = "DevilERP_Backups"

# ── App ───────────────────────────────────────────────────
APP_NAME = "Devil ERP"
COMPANY = "Devil One Pvt Ltd"
LEAD_DEV = "David K. Angel"
SUPPORT_EMAIL = "nexuzylab@gmail.com"
CURRENCY = "INR"
CURRENCY_SYMBOL = "₹"
DEFAULT_LANGUAGE = "en"
SUPPORTED_LANGUAGES = ["en", "hi", "bn"]
