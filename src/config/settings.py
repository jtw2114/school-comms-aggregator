"""Application-wide paths, constants, and defaults."""

import os
from pathlib import Path

# Root of the project (two levels up from this file)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Data directory (created at runtime)
DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = DATA_DIR / "school_comms.db"
ATTACHMENTS_DIR = DATA_DIR / "attachments"
BW_SESSION_PATH = DATA_DIR / "brightwheel_session.json"
WA_SESSION_PATH = DATA_DIR / "whatsapp_session.json"

# Credentials directory
CREDENTIALS_DIR = PROJECT_ROOT / "credentials"
GOOGLE_CREDENTIALS_PATH = CREDENTIALS_DIR / "credentials.json"
GOOGLE_TOKEN_PATH = CREDENTIALS_DIR / "token.json"

# Gmail OAuth scopes
GMAIL_SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

# Keyring service name
KEYRING_SERVICE = "school-comms-aggregator"

# Sync defaults
SUMMARY_ROLLING_DAYS = 8
GMAIL_MAX_RESULTS = 100
BW_PAGE_SIZE = 50
BW_LOGIN_TIMEOUT_MS = 120_000
WA_LOGIN_TIMEOUT_MS = 120_000  # 2 min for QR code scanning

# Brightwheel base URL
BW_BASE_URL = "https://schools.mybrightwheel.com"
BW_API_BASE = "https://schools.mybrightwheel.com/api/v1"

# Claude model for summaries
CLAUDE_MODEL = "claude-haiku-4-5-20251001"

# Ensure runtime directories exist
def ensure_dirs():
    """Create data directories if they don't exist."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    ATTACHMENTS_DIR.mkdir(parents=True, exist_ok=True)
    CREDENTIALS_DIR.mkdir(parents=True, exist_ok=True)
