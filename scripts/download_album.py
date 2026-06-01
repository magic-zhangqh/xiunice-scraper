#!/usr/bin/env python3
"""
Xiunice 单套图下载器

用法:
    python scripts/download_album.py <图集URL>
    python scripts/download_album.py https://xiunice.com/...-51p
"""

import os
import sys
import asyncio

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from xiunice_scraper.utils import BASE_DIR, sanitize_dirname, RateLimiter
from xiunice_scraper.downloader import curl_get, curl_download
from xiunice_scraper.parser import parse_album_images, parse_album_title
from xiunice_scraper.csv_util import load_history, append_history
from xiunice_scraper.notifier import send_notification

IMAGES_DIR = os.path.join(BASE_DIR, "images")
HISTORY_CSV = os.path.join(BASE_DIR, "data", "download_history.csv")
MAX_RPS = 10
MAX_CONCURRENT = 5


def prompt_confirm(record: dict) -> bool:
    """Ask user if they want to re-download."""
    print("\n" + "=" * 60)
    print("该图集已在下载历史中！")
    print("=" * 60)
    print(f"  标题:      {record['title']}")
    print(f"  上次下载:  {record['downloaded_at']}")
    print(f"  图片:      {record['success_images']}/{record['total_images']} 张")
    print(f"  保存目录:  {record['download_dir']}")
    print()
    print("  选项: y/yes - 重新下载, n/no - 跳过, info - 查看本地详情")
    while True:
        ans = input("  ? ").strip().lower()
        if ans in ('y', 'yes'):
            return True
        if ans in ('n', 'no', ''):
            return False
        if ans == 'info':
            d = record.get('download_dir', '')
            if os.path.exists(d):
                files = [f for f in os.listdir(d)
                         if os.path.isfile(os.path.join(d, f))]
                total_size = sum(os.path.getsize(os.path.join(d, f))
                                 for f in files)
                size_str = f"{total_size / 1024 / 1024:.1f} MB"
                print(f"  本地文件: {len(files)} 个, {size_str}")
            else:
                print(f"  本地目录不存在: {d}")
        else:
            print("  输入 y(重新下载), n(跳过), info(详情)")


async def download_album(album_url: str) -> bool:
    os.makedirs(IMAGES_DIR, exist_ok=True)

    existing = load_history(HISTORY_CSV).get(album_url)
    if existing:
        if not prompt_confirm(existing):
            print("\n[跳过] 已取消下载")
            return True
        print("\n[继续] 重新下载...\n")

    rate_limiter_site = RateLimiter(MAX_RPS)
    rate_limiter_photo = RateLimiter(MAX_RPS)

    print(f"[1/4] 正在获取图集页面: {album_url}")
    html = await curl_get(album_url, rate_limiter_site)
    if not html:
        print("[失败] 无法获取页面")
        return False

    print("[2/4] 解析页面...")
    title = parse_album_title(html)
    image_urls = parse_album_images(html)
    if not title:
        from urllib.parse import urlparse
        title = os.path.basename(urlparse(album_url).path).strip('/') or "unknown"

    print(f"  标题: {title}")
    print(f"  图片数: {len(image_urls)}")

    if not image_urls:
        print("[失败] 未找到任何图片 URL")
        debug_path = os.path.join(IMAGES_DIR, "_debug_page.html")
        with open(debug_path, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"  已保存 HTML 到: {debug_path}")
        return False

    dir_name = sanitize_dirname(title)
    collection_dir = os.path.join(IMAGES_DIR, dir_name)
    os.makedirs(collection_dir, exist_ok=True)
    print(f"[3/4] 保存目录: {collection_dir}")

    import time
    total = len(image_urls)
    success = 0
    start_time = time.time()
    sem = asyncio.Semaphore(MAX_CONCURRENT)
    done_count = 0

    async def download_one(img_url, i):
        nonlocal success, done_count
        parsed = __import__('urllib.parse').urlparse(img_url)
        ext = os.path.splitext(parsed.path)[1].lower()
        if not ext or len(ext) > 6 or ext not in ('.jpg', '.jpeg', '.png', '.webp', '.gif'):
            ext = '.jpg'
        filename = f"{i:03d}{ext}"
        filepath = os.path.join(collection_dir, filename)
        async with sem:
            ok = await curl_download(img_url, filepath, rate_limiter_photo)
        if ok:
            success += 1
        done_count += 1
        elapsed = time.time() - start_time
        speed = f"{success/elapsed:.1f}/s" if elapsed > 0 else "?"
        print(f"  [{i:3d}/{total}]  | {success}/{done_count} 成功  | {speed}",
              end="\r" if done_count < total else "\n")

    tasks = [download_one(url, i) for i, url in enumerate(image_urls, 1)]
    await asyncio.gather(*tasks)

    elapsed = time.time() - start_time
    print(f"\n[4/4] 下载完成！")
    summary = (f"图集: {title}\n"
               f"图片: {success}/{total} 张成功\n"
               f"耗时: {elapsed:.1f} 秒\n"
               f"路径: {collection_dir}")
    print(summary)

    os.makedirs(os.path.dirname(HISTORY_CSV), exist_ok=True)
    append_history(HISTORY_CSV, album_url, title, collection_dir, total, success)
    print(f"[历史] 已记录到: {HISTORY_CSV}")

    emoji = "✅" if success == total else "⚠️"
    send_notification(
        f"{emoji} Xiunice 图集下载{'完成' if success == total else '部分完成'}",
        f"{title}\n{success}/{total} 张成功\n{elapsed:.0f}秒",
    )
    return success > 0


def main():
    if len(sys.argv) < 2:
        print("用法: python scripts/download_album.py <图集URL>")
        sys.exit(1)
    asyncio.run(download_album(sys.argv[1]))


if __name__ == '__main__':
    main()
