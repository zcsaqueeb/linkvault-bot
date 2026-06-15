"""
Configuration — reads from environment variables (populated by .env via python-dotenv).
"""

import os
from typing import List

# ── Required ──────────────────────────────────────────────────────────────────
BOT_TOKEN: str  = os.environ.get("BOT_TOKEN", "").strip()
API_ID: int     = int(os.environ.get("API_ID", "0").strip() or "0")
API_HASH: str   = os.environ.get("API_HASH", "").strip()

# ── Channel IDs ───────────────────────────────────────────────────────────────
def _int_env(key: str, default: int = 0) -> int:
    parts = os.environ.get(key, "").strip().split()
    try:
        return int(parts[0]) if parts else default
    except (ValueError, IndexError):
        return default

LOG_CHANNEL: int        = _int_env("LOG_CHANNEL", 0)
DB_CHANNEL: int         = _int_env("DB_CHANNEL", 0)
FORCE_SUB_CHANNEL: int  = _int_env("FORCE_SUB_CHANNEL", 0)

# ── Admins ────────────────────────────────────────────────────────────────────
_raw_admins = os.environ.get("ADMINS", "").strip()
ADMINS: List[int] = [
    int(x.strip())
    for x in _raw_admins.replace(",", " ").split()
    if x.strip().lstrip("-").isdigit()
]

# ── Bot identity ──────────────────────────────────────────────────────────────
BOT_NAME: str     = os.environ.get("BOT_NAME", "File-to-Link Bot").strip()
BOT_USERNAME: str = os.environ.get("BOT_USERNAME", "").strip()

# ── Web server ────────────────────────────────────────────────────────────────
WEB_SERVER: bool         = os.environ.get("WEB_SERVER", "False").strip().lower() == "true"
WEB_SERVER_BIND_ADDRESS  = os.environ.get("WEB_SERVER_BIND_ADDRESS", "0.0.0.0")
WEB_SERVER_PORT: int     = _int_env("PORT", 8080)

# ── Link settings ─────────────────────────────────────────────────────────────
STREAM_MODE: bool = os.environ.get("STREAM_MODE", "True").strip().lower() == "true"
URL: str          = os.environ.get("URL", "").strip().rstrip("/")

# ── Misc ──────────────────────────────────────────────────────────────────────
TG_BOT_WORKERS: int = _int_env("TG_BOT_WORKERS", 4)
MONGO_URI: str      = os.environ.get("MONGO_URI", "").strip()
