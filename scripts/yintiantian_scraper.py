#!/usr/bin/env python3
"""
Xiunice 尹甜甜 批量下载器
步骤1: 爬取搜索页获取所有套图链接
步骤2: 逐一下载每套图的所有图片
限速 20张/秒

用法:
    python scripts/yintiantian_scraper.py
"""

import os
import sys
import csv
import asyncio
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from xiunice_scraper.utils import BASE_DIR, sanitize_dirname, RateLimiter
from xiunice_scraper.downloader import curl_get, curl_download
from xiunice_scraper.parser import parse_search_page, parse_album_images
from xiunice_scraper.notifier import send_notification

WORK_DIR = os.path.join(BASE_DIR, "data", "yintiantian")
IMAGES_DIR = os.path.join(BASE_DIR, "images", "yintiantian")
CSV_PATH = os.path.join(WORK_DIR, "results.csv")
DETAILED_CSV = os.path.join(WORK_DIR, "detailed_results.csv")

SEARCH_URL = "https://xiunice.com/?s=%E5%B0%B9%E7%94%9C%E7%94%9C"
PAGE_URLS = {
    1: SEARCH_URL,
    2: "https://xiunice.com/page/2?s=%E5%B0%B9%E7%94%9C%E7%94%9C",
    3: "https://xiunice.com/page/3?s=%E5%B0%B9%E7%94%9C%E7%94%9C",
    4: "https://xiunice.com/page/4?s=%E5%B0%B9%E7%94%9C%E7%94%9C",
}
MAX_RPS = 20


async def step1_scrape():
    print("=" * 60)
    print("步骤1: 爬取搜索页 (4页)")
    print("=" * 60)

    rate_limiter = RateLimiter(MAX_RPS)
    all_collections = []

    for page_num in sorted(PAGE_URLS.keys()):
        url = PAGE_URLS[page_num]
        print(f"\n获取第{page_num}页: {url}")
        html = await curl_get(url, rate_limiter)
        if not html:
            print(f"  [SKIP] 第{page_num}页获取失败")
            continue
        collections = parse_search_page(html)
        print(f"  找到 {len(collections)} 个图集")
        for c in collections:
            c['page'] = page_num
        all_collections.extend(collections)

    if not all_collections:
        print("未找到任何图集，退出")
        return []

    print(f"\n共找到 {len(all_collections)} 个图集")
    os.makedirs(WORK_DIR, exist_ok=True)
    with open(CSV_PATH, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=['page', 'title', 'url', 'cover_url'])
        writer.writeheader()
        for c in all_collections:
            writer.writerow(c)

    print(f"已保存到: {CSV_PATH}")
    return all_collections


async def step2_download(collections):
    print("\n" + "=" * 60)
    print(f"步骤2: 下载所有套图图片 (限速 {MAX_RPS}/s)")
    print(f"目标: {len(collections)} 个套图")
    print("=" * 60)

    rate_limiter_site = RateLimiter(MAX_RPS)
    rate_limiter_photo = RateLimiter(MAX_RPS)
    detailed_results = []
    total_all = len(collections)

    for idx, col in enumerate(collections, 1):
        title = col['title']
        url = col['url']
        page_num = col['page']
        dir_name = sanitize_dirname(f"p{page_num}_{title}")
        collection_dir = os.path.join(IMAGES_DIR, dir_name)

        print(f"\n[{idx}/{total_all}] {title}")

        html = await curl_get(url, rate_limiter_site)
        if not html:
            print(f"  [SKIP] 无法获取页面")
            detailed_results.append({**col, 'downloaded': False, 'total': 0, 'success': 0})
            continue

        image_urls = parse_album_images(html)
        total_images = len(image_urls)
        print(f"  发现 {total_images} 张图片")

        if total_images == 0:
            detailed_results.append({**col, 'downloaded': True, 'total': 0, 'success': 0})
            continue

        success_count = 0
        for i, img_url in enumerate(image_urls, 1):
            ext = os.path.splitext(img_url.split('?')[0])[1]
            if not ext or len(ext) > 6:
                ext = '.jpg'
            filename = f"{i:03d}{ext}"
            filepath = os.path.join(collection_dir, filename)
            ok = await curl_download(img_url, filepath, rate_limiter_photo)
            if ok:
                success_count += 1
            if i % 5 == 0 or i == total_images:
                print(f"    {success_count}/{i} ...",
                      end="\r" if i < total_images else "\n")

        print(f"  [完成] {success_count}/{total_images} 张")
        detailed_results.append({**col, 'downloaded': True,
                                 'total': total_images, 'success': success_count})

        if idx % 10 == 0 or idx == total_all:
            done = sum(1 for r in detailed_results if r.get('downloaded'))
            s = sum(r.get('success', 0) for r in detailed_results)
            t = sum(r.get('total', 0) for r in detailed_results)
            print(f"\n--- 进度: {idx}/{total_all} 套图, {s}/{t} 图片成功 ---")

    os.makedirs(WORK_DIR, exist_ok=True)
    with open(DETAILED_CSV, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, ['page', 'title', 'url', 'cover_url',
                                      'downloaded', 'total_images', 'success_images'])
        writer.writeheader()
        for r in detailed_results:
            writer.writerow({
                'page': r['page'], 'title': r['title'], 'url': r['url'],
                'cover_url': r.get('cover_url', ''),
                'downloaded': '是' if r.get('downloaded') else '否',
                'total_images': r.get('total', 0),
                'success_images': r.get('success', 0),
            })

    total_s = sum(r.get('success', 0) for r in detailed_results)
    total_t = sum(r.get('total', 0) for r in detailed_results)
    ok = sum(1 for r in detailed_results if r.get('downloaded'))

    print(f"\n{'='*60}")
    print(f"全部完成！")
    print(f"套图: {ok}/{total_all}")
    print(f"图片: {total_s}/{total_t} 张成功")
    print(f"目录: {IMAGES_DIR}")
    print(f"{'='*60}")

    send_notification(
        "✅ Xiunice 下载完成",
        f"尹甜甜: {ok}/{total_all}套图，{total_s}/{total_t}张成功",
    )


async def main():
    cols = await step1_scrape()
    if cols:
        await step2_download(cols)


if __name__ == '__main__':
    asyncio.run(main())
