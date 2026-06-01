#!/usr/bin/env python3
"""
合并历史下载记录到根目录 CSV

从 data/yintiantian/detailed_results.csv 和 output/detailed_results.csv
合并到 data/download_history.csv

用法:
    python scripts/merge_history.py
"""

import os
import sys
import csv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from xiunice_scraper.utils import BASE_DIR

HISTORY_CSV = os.path.join(BASE_DIR, "data", "download_history.csv")

SOURCES = [
    {
        'path': os.path.join(BASE_DIR, "data", "yintiantian", "detailed_results.csv"),
        'label': 'yintiantian (尹甜甜)',
        'download_base': os.path.join(BASE_DIR, "images", "yintiantian"),
    },
    {
        'path': os.path.join(BASE_DIR, "output", "detailed_results.csv"),
        'label': 'output (年年)',
        'download_base': os.path.join(BASE_DIR, "images"),
    },
]

FIELDS = ['url', 'title', 'download_dir', 'downloaded_at',
          'total_images', 'success_images']


def merge():
    existing_urls = set()
    all_rows = []

    if os.path.exists(HISTORY_CSV):
        with open(HISTORY_CSV, 'r', encoding='utf-8-sig') as f:
            for row in csv.DictReader(f):
                existing_urls.add(row['url'])
                all_rows.append(row)
        print(f"已有历史记录: {len(all_rows)} 条")

    new_count = 0
    skipped_count = 0

    for source in SOURCES:
        csv_path = source['path']
        if not os.path.exists(csv_path):
            print(f"  [跳过] 文件不存在: {csv_path}")
            continue

        src_new = 0
        src_skip = 0
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            for row in csv.DictReader(f):
                url = row.get('url', '').strip()
                title = row.get('title', '').strip()
                if not url:
                    continue

                page = row.get('page', '')
                safe_title = title.replace('/', '_').replace('\\', '_')[:60]
                download_dir = os.path.join(
                    source['download_base'],
                    f"p{page}_{safe_title}" if page else safe_title
                )
                total = row.get('total_images', row.get('total', '0'))
                success = row.get('success_images', row.get('success', '0'))

                if url in existing_urls:
                    src_skip += 1
                    continue

                all_rows.append({
                    'url': url,
                    'title': title,
                    'download_dir': download_dir,
                    'downloaded_at': '2026-05-31T15:00:00',
                    'total_images': total,
                    'success_images': success,
                })
                existing_urls.add(url)
                src_new += 1

        print(f"  [{source['label']}] 新增 {src_new} 条 (跳过 {src_skip} 重复)")
        new_count += src_new
        skipped_count += src_skip

    os.makedirs(os.path.dirname(HISTORY_CSV), exist_ok=True)
    with open(HISTORY_CSV, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"\n合并完成!")
    print(f"总计: {len(all_rows)} 条记录")
    print(f"新增: {new_count} 条")


if __name__ == '__main__':
    merge()
