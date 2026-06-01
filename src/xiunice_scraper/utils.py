"""
Shared utilities for Xiunice scraper.
"""

import os
import re
import time
import asyncio

BASE_DIR = os.path.expanduser("~/Desktop/xiunice_scraper")

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)

CURL_HEADERS = [
    "-H", f"User-Agent: {USER_AGENT}",
    "-H", "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "-H", "Accept-Language: zh-CN,zh;q=0.9,en;q=0.8",
    "-H", "Referer: https://xiunice.com/",
]


def sanitize_dirname(name: str, max_len: int = 80) -> str:
    """Sanitize a string for use as a directory name."""
    name = name.strip().replace('/', '_').replace('\\', '_')
    name = re.sub(r'[<>:"|?*]', '', name)
    name = re.sub(r'[^\w\- ]', '_', name)
    name = re.sub(r'_+', '_', name)
    name = name[:max_len].strip('_ .')
    return name


class RateLimiter:
    """Token-bucket rate limiter for async curl requests."""

    def __init__(self, max_per_second: float):
        self.max_per_second = max_per_second
        self.tokens = max_per_second
        self.last_refill = time.monotonic()
        self.lock = asyncio.Lock()

    async def acquire(self):
        async with self.lock:
            now = time.monotonic()
            elapsed = now - self.last_refill
            self.tokens = min(self.max_per_second,
                              self.tokens + elapsed * self.max_per_second)
            self.last_refill = now
            if self.tokens >= 1:
                self.tokens -= 1
                return
            wait_time = (1 - self.tokens) / self.max_per_second
            self.tokens = 0
            self.last_refill = now + wait_time
        await asyncio.sleep(wait_time)


def curl_base_args(proxy_enable=False, proxy="http://127.0.0.1:7890"):
    """Build base curl args list."""
    args = ["curl", "-s", "-S", "-L", "--retry", "1", "--max-time", "30"]
    if proxy_enable:
        args += ["--proxy", proxy]
    args += CURL_HEADERS
    return args
