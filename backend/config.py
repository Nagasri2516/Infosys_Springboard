"""
Application Configuration
All environment-based settings for Flask, SQLite, SMTP, and QR generation.
"""

import os
from pathlib import Path

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)


def _load_env_file(env_paths=None):
    """Load variables from a .env file if present."""
    if env_paths is None:
        env_paths = [Path(PROJECT_ROOT) / ".env", Path(BASE_DIR) / ".env"]

    for env_path in env_paths:
        if not env_path.exists():
            continue
        for raw_line in env_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value


_load_env_file()

# ─── Flask ────────────────────────────────────────────────────────────────────
SECRET_KEY = os.environ.get("SECRET_KEY", "eventcore-dev-secret-2026")
DEBUG = os.environ.get("FLASK_DEBUG", "true").lower() == "true"

# ─── Database ─────────────────────────────────────────────────────────────────
DATABASE_PATH = os.path.join(BASE_DIR, "database.db")

# ─── Static Assets ────────────────────────────────────────────────────────────
QR_CODE_DIR   = os.path.join(BASE_DIR, "static", "qrcodes")
OUTBOX_DIR    = os.path.join(BASE_DIR, "outbox")

# Ensure dirs exist at import time
os.makedirs(QR_CODE_DIR, exist_ok=True)
os.makedirs(OUTBOX_DIR,  exist_ok=True)

# ─── Email / SMTP ─────────────────────────────────────────────────────────────
# Fill these in your environment variables or a local .env file for real email delivery.
# If left blank the system will fall back to writing HTML files to outbox/.
SMTP_HOST     = os.environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT     = int(os.environ.get("SMTP_PORT", "587")) if os.environ.get("SMTP_PORT", "587").isdigit() else 587
SMTP_USE_TLS  = os.environ.get("SMTP_USE_TLS", "true").lower() == "true"
SMTP_USER     = os.environ.get("SMTP_USER", "")   # e.g. you@gmail.com
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
SENDER_NAME   = os.environ.get("SENDER_NAME", "EventCore System")
SENDER_EMAIL  = os.environ.get("SENDER_EMAIL", SMTP_USER or "noreply@eventcore.local")

# ─── App / Event Meta ─────────────────────────────────────────────────────────
EVENT_NAME    = "Infosys Tech Summit 2026"
EVENT_DATE    = "August 15, 2026"
EVENT_VENUE   = "Convention Center, Hall A"
