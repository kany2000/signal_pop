#!/usr/bin/env python3
"""
Signal Pop — 新闻抓取
从 RSS 源抓取 ≤48h 内的新闻
"""
import os
import sys
import json
import io
import feedparser
import requests
import html
import re
from datetime import datetime, timedelta
from dateutil import parser as dtparser
import time

OUTPUT_DIR = "/home/kan/signal_pop/data"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# RSS 订阅源
FEEDS = [
    {"name": "腾讯新闻", "url": "https://news.qq.com/newsrss.xml"},
    {"name": "新浪新闻", "url": "https://rss.sina.com.cn/news/china/focus15.xml"},
    {"name": "澎湃新闻", "url": "https://www.thepaper.cn/rss/default.xml"},
    {"name": "36kr", "url": "https://36kr.com/feed"},
    {"name": "BBC中文", "url": "https://feeds.bbci.co.uk/zhongwen/simp/rss.xml"},
    {"name": "BBC英文", "url": "https://feeds.bbci.co.uk/news/rss.xml"},
    {"name": "路透中文", "url": "https://feeds.reuters.com/reuters/CNTopStories"},
    {"name": "联合国新闻", "url": "https://news.un.org/feed/subscribe/zh/news/beat/science-technology/feed"},
]

MAX_AGE_HOURS = 48


def parse_date(entry):
    """解析 entry 的发布时间"""
    for attr in ['published', 'updated', 'created', 'start_date']:
        if hasattr(entry, attr):
            try:
                return dtparser.parse(getattr(entry, attr))
            except:
                pass
    return None


def fetch_feed(feed):
    """抓取单个 RSS 源"""
    try:
        r = requests.get(feed["url"], timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
        d = feedparser.parse(io.BytesIO(r.content))
        entries = []
        cutoff = datetime.utcnow() - timedelta(hours=MAX_AGE_HOURS)

        for e in d.entries:
            pub_date = parse_date(e)
            if pub_date and pub_date.tzinfo:
                pub_date = pub_date.replace(tzinfo=None)

            if pub_date is None:
                continue
            if pub_date < cutoff:
                continue

            # 提取摘要/描述
            summary = ""
            if hasattr(e, 'summary'):
                summary = e.summary
            elif hasattr(e, 'description'):
                summary = e.description
            # 清理 HTML 并解码实体
            summary = re.sub(r'<[^>]+>', '', summary)
            summary = html.unescape(summary).strip()
            # 智能截断：在句号/问号/感叹号处截断，最长 300 字
            if len(summary) > 300:
                match = re.search(r'[。！？.!?]', summary[:300])
                if match:
                    summary = summary[:match.end()]
                else:
                    summary = summary[:300]

            entries.append({
                "title": e.get("title", ""),
                "link": e.get("link", ""),
                "source": feed["name"],
                "published": pub_date.isoformat() if pub_date else "",
                "summary": summary,
            })
        return entries
    except Exception as ex:
        print(f"[fetch] ⚠️ {feed['name']}: {ex}", file=sys.stderr)
        return []


def fetch_all():
    """抓取所有源，合并去重"""
    all_entries = []
    for feed in FEEDS:
        print(f"[fetch] 📡 {feed['name']}...")
        entries = fetch_feed(feed)
        print(f"[fetch]   → {len(entries)} 条 ≤48h 新闻")
        all_entries.extend(entries)
        time.sleep(0.5)

    # 按时间排序
    all_entries.sort(key=lambda x: x["published"], reverse=True)

    out_path = f"{OUTPUT_DIR}/raw_feed.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(all_entries, f, ensure_ascii=False, indent=2)

    print(f"[fetch] ✅ 共 {len(all_entries)} 条新闻已保存到 {out_path}")
    return all_entries


if __name__ == "__main__":
    fetch_all()