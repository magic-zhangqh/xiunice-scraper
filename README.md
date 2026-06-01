# Xiunice Scraper

秀人网 (xiunice.com) 爬虫工具包。支持搜索爬取图集列表、批量/单套下载图片、下载历史管理、Gotify 推送通知。

## 功能概述

一个完整的秀人网图集下载工具集，包含：

**搜索爬取** — 输入搜索关键词，爬取多页搜索结果（标题、封面图、详情页链接），保存为 CSV。

**批量下载** — 读取搜索结果 CSV，逐一进入每个图集详情页解析所有图片 URL，并全部下载到本地。异步并发 + 速率限制，避免被 ban。

**单套下载** — 输入一个图集 URL，自动解析标题和所有图片，下载到 images/ 目录，自动记录下载历史。支持重复下载检查。

**历史合并** — 合并多个爬取任务的结果到统一的下载历史 CSV，便于追溯已下载内容。

**通知推送** — 下载完成后通过 Gotify 发送通知到手机/桌面。

## 项目结构

```
xiunice_scraper/
├── src/xiunice_scraper/        # 共享 Python 模块
│   ├── utils.py                # 路径常量、目录名清理、令牌桶限速器
│   ├── downloader.py           # 异步 curl 下载 (asyncio + subprocess)
│   ├── parser.py               # HTML 解析 (搜索页、套图页)
│   ├── csv_util.py             # CSV 历史记录读写
│   └── notifier.py             # Gotify 推送
├── scripts/                    # 入口脚本 (可直接运行)
│   ├── scrape_search.py        # 搜索爬取 "年年" 结果 + 封面图下载
│   ├── download_all.py         # 从 CSV 批量下载所有套图
│   ├── download_album.py       # 单套图下载 (带历史检查)
│   ├── yintiantian_scraper.py  # 尹甜甜 搜索 + 批量下载
│   └── merge_history.py        # 合并下载历史到统一 CSV
├── data/                       # 输出数据 (CSV)
│   ├── search_results/         # 搜索结果
│   ├── yintiantian/            # 尹甜甜结果
│   ├── detailed_results.csv    # 详细下载结果
│   └── download_history.csv    # 合并的下载历史 (204 条记录)
├── debug/                      # 调试用 HTML 页面 (已 gitignore)
├── images/                     # 下载的图片 (5.4G, 已 gitignore)
├── downloads/                  # 历史封面图 (已 gitignore)
├── .gitignore
├── requirements.txt
└── README.md
```

## 安装

依赖只有 BeautifulSoup：

```bash
pip install -r requirements.txt
```

运行脚本无需额外安装，使用系统自带的 curl 作为 HTTP 后端。

## 使用示例

### 搜索爬取 "年年" 图集列表

```bash
python scripts/scrape_search.py
```

爬取 4 页搜索结果，输出到 `data/search_results/niannian_results.csv`，封面图下载到 `data/covers/`。

### 批量下载所有套图

```bash
python scripts/download_all.py
```

读取搜索结果 CSV，依次进入每个图集详情页，下载所有图片到 `images/` 目录下以套图命名的子目录。

### 下载单个图集

```bash
python scripts/download_album.py "https://xiunice.com/...-51p"
```

自动解析标题和图片 URL，下载到 `images/<标题>/`，记录到 `data/download_history.csv`。已下载过的 URL 会提示确认是否重新下载。

### 尹甜甜 搜索 + 批量下载

```bash
python scripts/yintiantian_scraper.py
```

两步走：先爬取 "尹甜甜" 搜索页，再逐一下载所有套图。

### 合并下载历史

```bash
python scripts/merge_history.py
```

将多个爬取任务的结果合并到统一的 `data/download_history.csv`。

## 技术细节

**下载后端**: 使用 curl 而非 requests/aiohttp，利用 curl 内置的重试、超时和代理支持，无需额外安装 HTTP 库。

**异步并发**: asyncio + subprocess 异步执行 curl，支持同时下载多张图片（MAX_CONCURRENT）和独立速率限制（MAX_RPS）。

**速率限制**: 令牌桶算法，对 xiunice.com（页面请求）和 photo.xiunice.com（图片下载）分别限速。

**防反爬**: 浏览器 User-Agent、Referer、Accept-Language 头伪装。

**通知**: 下载完成后通过 Gotify 自托管服务推送通知。

## 开发

共享代码在 `src/xiunice_scraper/`，通过 sys.path 注入让 `scripts/` 下的入口脚本导入。

```python
from xiunice_scraper.utils import RateLimiter, sanitize_dirname
from xiunice_scraper.downloader import curl_get, curl_download
from xiunice_scraper.parser import parse_search_page, parse_album_images
from xiunice_scraper.csv_util import load_history, append_history
from xiunice_scraper.notifier import send_gotify
```
