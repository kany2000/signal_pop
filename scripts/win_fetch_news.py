#!/usr/bin/env python3
"""Signal Pop — 新闻抓取脚本（Windows版，多源 / 非政治导向）"""
import os, sys, json, io, time, html, re
import requests
import feedparser

OUTPUT_DIR = "E:/projects/signal_pop/output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 以综合 / 科技 / 财经 / 民生类媒体为主，规避政治重源（BBC中文、路透、联合国等）
# 2026-08-23 复核：剔除 8 个长期失效源（404/超时/连接重置），保留并新增已验证可用源。
# 当前可用源：新浪/IT之家/少数派/中新网/量子位/36氪/钛媒体/人民网（共 8 家，满足媒体≥5家）。
FEEDS = [
    {"name": "新浪新闻", "url": "https://rss.sina.com.cn/news/china/focus15.xml"},
    {"name": "36氪", "url": "https://www.36kr.com/feed"},
    {"name": "IT之家", "url": "https://www.ithome.com/rss/"},
    {"name": "少数派", "url": "https://sspai.com/feed"},
    {"name": "中国新闻网", "url": "https://www.chinanews.com/rss/scroll-news.xml"},
    {"name": "量子位", "url": "https://www.qbitai.com/feed"},
    {"name": "钛媒体", "url": "https://www.tmtpost.com/rss.xml"},
    {"name": "人民网", "url": "http://www.people.com.cn/rss/politics.xml"},
]

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
            published = e.get("published", "") or e.get("updated", "")
            iso = ""
            pp = getattr(e, "published_parsed", None) or getattr(e, "updated_parsed", None)
            if pp:
                try:
                    iso = time.strftime("%Y-%m-%dT%H:%M:%S", pp)
                except Exception:
                    pass
            entries.append({
                "title": e.get("title", ""),
                "link": e.get("link", ""),
                "source": feed["name"],
                "published": published,
                "published_iso": iso,
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

    def sortkey(x):
        return x.get("published_iso") or "0000"
    all_entries.sort(key=sortkey, reverse=True)
    out_path = os.path.join(OUTPUT_DIR, "raw_feed.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(all_entries, f, ensure_ascii=False, indent=2)
    print(f"[fetch] 共 {len(all_entries)} 条 -> {out_path}")
    return all_entries

if __name__ == "__main__":
    fetch_all()
