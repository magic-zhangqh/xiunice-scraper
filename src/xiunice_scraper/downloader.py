"""
Async downloader using curl subprocess with rate limiting.
"""

import os
import asyncio
from urllib.parse import urlparse

from .utils import curl_base_args, RateLimiter


async def curl_get(url: str, rate_limiter: RateLimiter,
                   proxy_enable=False, proxy="http://127.0.0.1:7890",
                   retries=3, timeout=30) -> str | None:
    """Fetch a page asynchronously via curl."""
    args = curl_base_args(proxy_enable, proxy)
    # Override max-time for get
    args[args.index("--max-time") + 1] = str(timeout)
    args.append(url)

    for attempt in range(retries):
        await rate_limiter.acquire()
        try:
            proc = await asyncio.create_subprocess_exec(
                *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=timeout + 15)
            if proc.returncode == 0 and len(stdout) > 100:
                return stdout.decode('utf-8', errors='ignore')
        except (asyncio.TimeoutError, Exception):
            pass
        if attempt < retries - 1:
            await asyncio.sleep(2 ** attempt)
    return None


async def curl_download(url: str, filepath: str,
                        rate_limiter: RateLimiter,
                        proxy_enable=False, proxy="http://127.0.0.1:7890",
                        retries=3, min_size=1000) -> bool:
    """Download a single file asynchronously via curl."""
    if os.path.exists(filepath) and os.path.getsize(filepath) > min_size:
        return True
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    args = curl_base_args(proxy_enable, proxy)
    # Override max-time for download (longer)
    timeout = 60
    args[args.index("--max-time") + 1] = str(timeout)
    args += ["-o", filepath, url]

    for attempt in range(retries):
        await rate_limiter.acquire()
        try:
            proc = await asyncio.create_subprocess_exec(
                *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            _, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=timeout + 15)
            if proc.returncode == 0 and os.path.getsize(filepath) > min_size:
                return True
            if os.path.exists(filepath) and os.path.getsize(filepath) < min_size:
                os.remove(filepath)
        except (asyncio.TimeoutError, Exception):
            if os.path.exists(filepath):
                os.remove(filepath)
        if attempt < retries - 1:
            await asyncio.sleep(2 ** attempt)
    return False


def curl_sync(url: str, output_path: str, retries=3, max_time=30) -> bool:
    """Synchronous curl download, returns True on success."""
    import subprocess
    cmd = [
        "curl", "-s", "-S", "-L",
        "--retry", str(retries),
        "--max-time", str(max_time),
    ] + curl_base_args()[1:]  # skip the first -H flag duplication
    cmd += ["-o", output_path, url]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=max_time + 30)
    if result.returncode != 0:
        return False
    if os.path.getsize(output_path) < 100:
        os.remove(output_path)
        return False
    return True
