"""
Gotify notification utility.

Configuration loaded from environment variables (via .env file):
- GOTIFY_URL     — Gotify server base URL (default: http://10.10.1.180:11080)
- GOTIFY_TOKEN   — Gotify application token (required)
- GOTIFY_PRIORITY — Default notification priority (default: 5)
"""

import os
import subprocess
from pathlib import Path

from dotenv import load_dotenv

# Load .env from project root (two levels up from this file)
_env_path = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(_env_path)

GOTIFY_URL = os.getenv("GOTIFY_URL", "http://10.10.1.180:11080").rstrip("/")
GOTIFY_TOKEN = os.getenv("GOTIFY_TOKEN", "")
GOTIFY_PRIORITY = int(os.getenv("GOTIFY_PRIORITY", "5"))


def send_gotify(title: str, message: str, priority: int = GOTIFY_PRIORITY):
    """Send a notification via Gotify."""
    if not GOTIFY_TOKEN:
        return  # silently skip if not configured

    url = f"{GOTIFY_URL}/message?token={GOTIFY_TOKEN}"
    try:
        subprocess.run(
            ["curl", "-s", "-X", "POST", url,
             "-F", f"title={title}",
             "-F", f"message={message}",
             "-F", f"priority={priority}"],
            capture_output=True, timeout=10,
        )
    except Exception:
        pass
