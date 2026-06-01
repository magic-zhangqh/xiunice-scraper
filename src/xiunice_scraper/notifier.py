"""
Notification utility.

Supports two backends configured via .env:
  - gotify: self-hosted Gotify push server (default)
  - email: SMTP email notification

Config:
  NOTIFY_METHOD  — gotify | email (default: gotify)
  GOTIFY_URL     — Gotify server base URL
  GOTIFY_TOKEN   — Gotify application token
  SMTP_HOST      — SMTP server hostname
  SMTP_PORT      — SMTP server port (default: 465)
  SMTP_USER      — SMTP login username / sender address
  SMTP_PASSWORD  — SMTP login password / app password
  EMAIL_TO       — recipient address (default: same as SMTP_USER)
"""

import os
import smtplib
import subprocess
from email.mime.text import MIMEText
from pathlib import Path

from dotenv import load_dotenv

_env_path = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(_env_path)

# ── Gotify ──────────────────────────────────────────
GOTIFY_URL = os.getenv("GOTIFY_URL", "http://10.10.1.180:11080").rstrip("/")
GOTIFY_TOKEN = os.getenv("GOTIFY_TOKEN", "")
GOTIFY_PRIORITY = int(os.getenv("GOTIFY_PRIORITY", "5"))

# ── Email (SMTP) ────────────────────────────────────
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.qq.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
EMAIL_TO = os.getenv("EMAIL_TO") or SMTP_USER

# ── Method ──────────────────────────────────────────
NOTIFY_METHOD = os.getenv("NOTIFY_METHOD", "gotify").strip().lower()


# ── Gotify sender ───────────────────────────────────
def send_gotify(title: str, message: str, priority: int = GOTIFY_PRIORITY):
    """Send a notification via Gotify."""
    if not GOTIFY_TOKEN:
        return
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


# ── Email sender ────────────────────────────────────
def send_email(subject: str, body: str):
    """Send notification via SMTP email (SSL, port 465)."""
    if not SMTP_USER or not SMTP_PASSWORD:
        return
    try:
        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"] = SMTP_USER
        msg["To"] = EMAIL_TO
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=15) as s:
            s.login(SMTP_USER, SMTP_PASSWORD)
            s.send_message(msg)
    except Exception:
        pass


# ── Unified dispatcher ──────────────────────────────
def send_notification(subject: str, body: str, priority: int = GOTIFY_PRIORITY):
    """Send notification using the method configured in NOTIFY_METHOD."""
    if NOTIFY_METHOD == "email":
        send_email(subject, body)
    else:
        send_gotify(subject, body, priority)
