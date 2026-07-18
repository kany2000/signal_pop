#!/usr/bin/env python3
"""
Signal Pop — 轻量版新闻抓取（无 feedparser 依赖）
从 RSS 源抓取 ≤48h 内的新闻
"""
import os
import sys
import json
import io
import requests
import html
import re
from datetime import datetime, timedelta
import time
import xml.etree.ElementTree as ET

OUTPUT_DIR = "/home/kan/signal_pop/data"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# RSS 订阅源（只使用可用的）
FEEDS = [
    {"name": "新浪新闻", "url": "https://rss.sina.com.cn/news/china/focus15.xml"},
]

def parse_rss_xml(xml_content, source_name):
    """解析 RSS XML，提取新闻条目"""
    entries = []
    try:
        root = ET.fromstring(xml_content)
        
        # 查找所有 item 元素
        items = root.findall('.//item')
        print(f"[parse] 找到 {len(items)} 个条目")
        
        for item in items:
            title_elem = item.find('title')
            link_elem = item.find('link')
            pub_elem = item.find('pubDate')
            
            if title_elem is None or link_elem is None:
                continue
            
            title = html.unescape(title_elem.text.strip()) if title_elem.text else ""
            link = link_elem.text
            published_str = pub_elem.text if pub_elem is not None else None
            
            # 过滤空标题
            if not title:
                continue
            
            # 简单过滤 48 小时内的新闻
            include = True
            if published_str:
                try:
                    # 解析日期格式：Thu, 26 Jun 2026 10:00:00 +0800
                    dt = datetime.strptime(published_str.replace('GMT', '+0800'), '%a, %d %b %Y %H:%M:%S %z')
                    if datetime.now() - dt > timedelta(hours=48):
                        include = False
                except:
                    pass
            
            if include:
                entries.append({
                    'title': title,
                    'link': link,
                    'published': published_str,
                    'source': source_name
                })
    except Exception as e:
        print(f"[parse] ❌ 解析失败：{e}")
    
    return entries

def fetch_feed(feed):
    """抓取单个 RSS 源"""
    try:
        resp = requests.get(feed['url'], timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
        resp.encoding = 'utf-8'
        content = resp.text
        
        entries = parse_rss_xml(content, feed['name'])
        print(f"[fetch] → {len(entries)} 条有效新闻")
        return entries
    except Exception as e:
        print(f"[fetch] ❌ {feed['name']} 失败：{e}")
        return []

def fetch_all():
    """抓取所有源，合并去重"""
    all_entries = []
    for i, feed in enumerate(FEEDS):
        print(f"[fetch] 📡 {feed['name']}...")
        entries = fetch_feed(feed)
        all_entries.extend(entries)
        time.sleep(0.5)
    
    # 按时间排序（最新的在前）
    all_entries.sort(key=lambda x: x.get('published', ''), reverse=True)
    
    # 去重（按标题）
    seen_titles = set()
    unique_entries = []
    for entry in all_entries:
        if entry['title'] not in seen_titles:
            seen_titles.add(entry['title'])
            unique_entries.append(entry)
    
    out_path = f"{OUTPUT_DIR}/raw_feed.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(unique_entries, f, ensure_ascii=False, indent=2)
    
    print(f"[fetch] ✅ 共 {len(unique_entries)} 条新闻已保存到 {out_path}")
    return unique_entries

if __name__ == "__main__":
    fetch_all()
