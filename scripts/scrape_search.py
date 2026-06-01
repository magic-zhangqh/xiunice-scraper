#!/usr/bin/env python3
"""
Xiunice 搜索爬虫 - 爬取"年年"搜索结果 (4页) 的图集封面和链接

用法:
    python scripts/scrape_search.py
"""

import os
import sys
import csv

# Add src/ to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from xiunice_scraper.utils import BASE_DIR
from xiunice_scraper.parser import parse_search_page
from xiunice_scraper.downloader import curl_sync

DOWNLOADS_DIR = os.path.join(BASE_DIR, "data", "covers")
OUTPUT_DIR = os.path.join(BASE_DIR, "data", "search_results")
CSV_PATH = os.path.join(OUTPUT_DIR, "niannian_results.csv")

PAGES = {
    1: "https://xiunice.com/?s=%E5%B9%B4%E5%B9%B4",
    2: "https://xiunice.com/page/2?s=%E5%B9%B4%E5%B9%B4",
    3: "https://xiunice.com/page/3?s=%E5%B9%B4%E5%B9%B4",
    4: "https://xiunice.com/page/4?s=%E5%B9%B4%E5%B9%B4",
}

os.makedirs(DOWNLOADS_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)


def main():
    all_results = []

    for page_num in sorted(PAGES.keys()):
        page_url = PAGES[page_num]
        print(f"\n{'='*60}")
        print(f"Fetching Page {page_num}: {page_url}")
        print(f"{'='*60}")

        html_path = os.path.join(BASE_DIR, "debug", f"page_{page_num}.html")
        if not os.path.exists(html_path):
            if not curl_sync(page_url, html_path):
                print(f"  [SKIP] Could not fetch page {page_num}")
                continue
        else:
            print("  (Using existing cached HTML)")

        collections = parse_search_page(html_path)
        print(f"  Extracted {len(collections)} collections from page {page_num}")

        for item in collections:
            print(f"\n  [{len(all_results) + 1}] {item['title']}")
            print(f"       URL: {item['url']}")
            print(f"       Cover: {item['cover_url']}")

            prefix = f"p{page_num}_{item['title'][:30]}"
            safe_prefix = ''.join(c if c.isalnum() or c in '-_. ' else '_'
                                  for c in prefix)[:60]
            ext = ".jpg"
            local_path = os.path.join(DOWNLOADS_DIR, f"{safe_prefix}{ext}")

            if item['cover_url']:
                ok = curl_sync(item['cover_url'], local_path)
                if ok:
                    sz = os.path.getsize(local_path)
                    print(f"       Downloaded ({sz} bytes)")
                else:
                    local_path = ""
            else:
                local_path = ""

            all_results.append({
                "page": page_num,
                "title": item["title"],
                "url": item["url"],
                "cover_url": item["cover_url"],
                "local_path": local_path if local_path else "",
            })

    fieldnames = ["page", "title", "url", "cover_url", "local_path"]
    with open(CSV_PATH, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_results)

    print(f"\n{'='*60}")
    print(f"DONE! 总计: {len(all_results)} 个图集")
    print(f"CSV: {CSV_PATH}")
    print(f"封面目录: {DOWNLOADS_DIR}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
