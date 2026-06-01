#!/usr/bin/env python3
"""
Xiunice 套图批量下载器 - 从 CSV 结果批量下载所有图片

用法:
    python scripts/download_all.py
"""

import os
import sys
import csv
import asyncio

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from xiunice_scraper.utils import BASE_DIR, sanitize_dirname, RateLimiter
from xiunice_scraper.downloader import curl_get, curl_download
from xiunice_scraper.parser import parse_album_images

IMAGES_DIR = os.path.join(BASE_DIR, "images")
CSV_IN_PATH = os.path.join(BASE_DIR, "data", "search_results", "niannian_results.csv")
CSV_OUT_PATH = os.path.join(BASE_DIR, "data", "detailed_results.csv")

MAX_RPS = 15


async def process_collection(row, rate_limiter_site, rate_limiter_photo,
                              idx, total):
    page_num = row['page']
    title = row['title']
    url = row['url']

    dir_name = sanitize_dirname(f"p{page_num}_{title}")
    collection_dir = os.path.join(IMAGES_DIR, dir_name)

    print(f"\n[{idx}/{total}] {title}")

    html = await curl_get(url, rate_limiter_site)
    if not html:
        print(f"  [SKIP] 无法获取页面: {url}")
        return {'title': title, 'url': url, 'downloaded': False,
                'total': 0, 'success': 0}

    image_urls = parse_album_images(html)
    total_images = len(image_urls)
    print(f"  发现 {total_images} 张图片")

    if total_images == 0:
        return {'title': title, 'url': url, 'downloaded': True,
                'total': 0, 'success': 0}

    success_count = 0
    for i, img_url in enumerate(image_urls, 1):
        ext = os.path.splitext(img_url.split('?')[0])[1]
        if not ext or len(ext) > 6:
            ext = '.jpg'
        filename = f"{i:03d}{ext}"
        filepath = os.path.join(collection_dir, filename)
        ok = await curl_download(img_url, filepath, rate_limiter_photo)
        if ok:
            sz = os.path.getsize(filepath)
            sz_str = f"{sz/1024:.0f}K" if sz < 1024*1024 else f"{sz/1024/1024:.1f}M"
            print(f"    [{i}/{total_images}] OK {sz_str} - {filename}",
                  end="\r" if i < total_images else "\n")
            success_count += 1
        else:
            print(f"\n    [{i}/{total_images}] FAIL - {filename}")

    print(f"  [完成] {success_count}/{total_images} 张下载成功")
    return {'title': title, 'url': url, 'downloaded': True,
            'total': total_images, 'success': success_count}


async def main():
    rows = []
    if os.path.exists(CSV_IN_PATH):
        with open(CSV_IN_PATH, 'r', encoding='utf-8-sig') as f:
            for row in csv.DictReader(f):
                rows.append(row)
    else:
        # Fallback: try the old output/results.csv
        old_path = os.path.join(BASE_DIR, "output", "results.csv")
        if os.path.exists(old_path):
            with open(old_path, 'r', encoding='utf-8-sig') as f:
                for row in csv.DictReader(f):
                    rows.append(row)
            print(f"从旧路径读取: {old_path}")
        else:
            print(f"未找到 CSV 输入文件: {CSV_IN_PATH}")
            return

    print(f"共读入 {len(rows)} 条套图记录")
    os.makedirs(IMAGES_DIR, exist_ok=True)

    rate_limiter_site = RateLimiter(MAX_RPS)
    rate_limiter_photo = RateLimiter(MAX_RPS)
    detailed_results = []

    for idx, row in enumerate(rows, 1):
        result = await process_collection(
            row, rate_limiter_site, rate_limiter_photo, idx, len(rows))
        detailed_results.append(result)
        if idx % 5 == 0 or idx == len(rows):
            done = sum(1 for r in detailed_results if r['downloaded'])
            total_success = sum(r['success'] for r in detailed_results)
            total_expected = sum(r['total'] for r in detailed_results)
            print(f"\n--- 进度: {idx}/{len(rows)} 套图, "
                  f"图片 {total_success}/{total_expected} 成功 ---")

    fieldnames = ['page', 'title', 'url', 'cover_url', 'local_path',
                  'downloaded', 'total_images', 'success_images']
    os.makedirs(os.path.dirname(CSV_OUT_PATH), exist_ok=True)
    with open(CSV_OUT_PATH, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row, detail in zip(rows, detailed_results):
            writer.writerow({
                'page': row['page'], 'title': row['title'],
                'url': row['url'], 'cover_url': row.get('cover_url', ''),
                'local_path': row.get('local_path', ''),
                'downloaded': '是' if detail['downloaded'] else '否',
                'total_images': detail['total'],
                'success_images': detail['success'],
            })

    total_s = sum(r['success'] for r in detailed_results)
    total_t = sum(r['total'] for r in detailed_results)
    success_collections = sum(1 for r in detailed_results if r['downloaded'])

    print(f"\n{'='*60}")
    print(f"全部完成！")
    print(f"套图总数: {len(rows)}")
    print(f"成功处理: {success_collections}")
    print(f"图片总计: {total_s}/{total_t} 张成功")
    print(f"详细 CSV: {CSV_OUT_PATH}")
    print(f"{'='*60}")


if __name__ == '__main__':
    asyncio.run(main())
