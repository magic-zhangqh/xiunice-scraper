"""
CSV utilities for download history and results.
"""

import os
import csv
from datetime import datetime, timezone

HISTORY_FIELDS = [
    'url', 'title', 'download_dir',
    'downloaded_at', 'total_images', 'success_images',
]


def load_history(csv_path: str) -> dict[str, dict]:
    """Load history CSV into {url: row_dict}."""
    if not os.path.exists(csv_path):
        return {}
    result = {}
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        for row in csv.DictReader(f):
            url = row.get('url', '').strip()
            if url:
                result[url] = row
    return result


def append_history(csv_path: str, url: str, title: str,
                   download_dir: str, total: int, success: int):
    """Append one record to the history CSV."""
    now = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    is_new = not os.path.exists(csv_path)
    with open(csv_path, 'a', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=HISTORY_FIELDS)
        if is_new:
            writer.writeheader()
        writer.writerow({
            'url': url,
            'title': title,
            'download_dir': download_dir,
            'downloaded_at': now,
            'total_images': total,
            'success_images': success,
        })
