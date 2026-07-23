#!/usr/bin/env python3
"""Signal Pop — 临时新闻抓取脚本（Windows版）"""
import os, sys, json, io, requests, html, re, time
from datetime import datetime, timedelta
import feedparser

OUTPUT_DIR = "E:/projects/signal_pop/output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

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

def parse_date(entry):
    for attr in ['published', 'updated', 'created', 'start_date']:
        if hasattr(entry, attr):
            try:
                from dateutil import parser as dtparser
                return dtparser.parse(getattr(entry, attr))
            except:
                pass
    return None

def fetch_feed(feed):
    try:
        r = requests.get(feed["url"], timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
        d = feedparser.parse(io.BytesIO(r.content))
        entries = []
        for e in d.entries:
            summary = ""
            if hasattr(e, 'summary'): summary = e.summary
            elif hasattr(e, 'description'): summary = e.description
            summary = re.sub(r'<[^>]+>', '', summary)
            summary = html.unescape(summary).strip()
            if len(summary) > 300:
                m = re.search(r'[。！？.!?]', summary[:300])
                summary = summary[:m.end()] if m else summary[:300]
            entries.append({
                "title": e.get("title", ""),
                "link": e.get("link", ""),
                "source": feed["name"],
                "published": e.get("published", ""),
                "summary": summary,
            })
        return entries
    except Exception as ex:
        print(f"[fetch] {feed['name']}: {ex}")
        return []

def fetch_all():
    all_entries = []
    for feed in FEEDS:
        print(f"[fetch] {feed['name']}...")
        entries = fetch_feed(feed)
        print(f"[fetch]   -> {len(entries)} 条")
        all_entries.extend(entries)
        time.sleep(0.5)
    all_entries.sort(key=lambda x: x["published"], reverse=True)
    out_path = os.path.join(OUTPUT_DIR, "raw_feed.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(all_entries, f, ensure_ascii=False, indent=2)
    print(f"[fetch] 共 {len(all_entries)} 条 -> {out_path}")
    return all_entries

if __name__ == "__main__":
    fetch_all()