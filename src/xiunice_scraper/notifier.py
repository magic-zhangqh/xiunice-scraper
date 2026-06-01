"""
Gotify notification utility.
"""

import subprocess

GOTIFY_URL = "http://10.10.1.180:11080/message?token=AAdURqv4P4R38Vh"


def send_gotify(title: str, message: str, priority: int = 5):
    """Send a notification via Gotify."""
    try:
        subprocess.run(
            ["curl", "-s", "-X", "POST", GOTIFY_URL,
             "-F", f"title={title}",
             "-F", f"message={message}",
             "-F", f"priority={priority}"],
            capture_output=True, timeout=10,
        )
    except Exception:
        pass
