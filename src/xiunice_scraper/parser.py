"""
HTML parsing utilities for xiunice.com pages.
"""

import re
from bs4 import BeautifulSoup


def parse_search_page(html: str) -> list[dict]:
    """
    Parse search result page HTML, extract collection links and cover images.
    Returns list of {title, url, cover_url}.
    """
    soup = BeautifulSoup(html, 'html.parser')
    results = []

    for mod in soup.find_all("div", class_="tdb_module_loop"):
        link_tag = mod.find("a", href=True)
        if not link_tag:
            continue
        url = link_tag.get("href", "").strip()
        title_tag = mod.find("h3", class_="entry-title")
        title = ""
        if title_tag:
            title_link = title_tag.find("a")
            if title_link:
                title = (title_link.get("title", "") or
                         title_link.get_text(strip=True))
        if not title:
            title = link_tag.get("title", "") or link_tag.get_text(strip=True)
        if not url or not title:
            continue

        # Extract cover image URL
        cover_url = ""
        thumb = mod.find("span", class_="entry-thumb")
        if thumb:
            if thumb.get("data-img-url"):
                cover_url = thumb["data-img-url"].strip()
            elif thumb.get("data-style"):
                m = re.search(r'url\([\'"]?([^\'")]+)[\'"]?\)',
                              thumb["data-style"])
                if m:
                    cover_url = m.group(1)
        if not cover_url:
            img = mod.find("img")
            if img:
                cover_url = (img.get("src", "") or
                             img.get("data-src", "") or "")

        results.append({
            "title": title,
            "url": url,
            "cover_url": cover_url,
        })

    return results


def parse_album_images(html: str) -> list[str]:
    """
    Parse a collection/album page, extract all image URLs.
    Returns list of image URLs.
    """
    soup = BeautifulSoup(html, 'html.parser')
    image_urls = []

    # A: <figure class="wp-block-image"> → <img src="...">
    for figure in soup.find_all(
            'figure',
            class_=lambda c: c and 'wp-block-image' in str(c) if c else False):
        img = figure.find('img')
        if img and img.get('src'):
            src = img['src'].strip()
            if src and src not in image_urls:
                image_urls.append(src)

    # B: Direct img tags with photo.xiunice.com
    if not image_urls:
        for img in soup.find_all('img'):
            src = img.get('src') or ''
            if ('photo.xiunice.com' in src or
                    'xiunice.com/wp-content/uploads' in src):
                src = src.strip()
                if src and src not in image_urls:
                    image_urls.append(src)

    # C: <a href="..."> pointing to images
    if not image_urls:
        for a in soup.find_all('a', href=True):
            href = a['href'].strip()
            if any(ext in href.lower()
                   for ext in ['.jpg', '.jpeg', '.png', '.webp']):
                if 'xiunice.com' in href or href.startswith('http'):
                    if href not in image_urls:
                        image_urls.append(href)

    return image_urls


def parse_album_title(html: str) -> str:
    """Extract the album title from an album page."""
    soup = BeautifulSoup(html, 'html.parser')
    title = ""
    t = soup.find('title')
    if t:
        title = t.get_text(strip=True)
        title = re.sub(
            r'\s*[-–—|]\s*Xiunice\.com.*$', '', title, flags=re.IGNORECASE
        ).strip()
    if not title or len(title) > 120:
        h1 = soup.find('h1', class_='entry-title')
        if h1:
            title = h1.get_text(strip=True)
    return title
