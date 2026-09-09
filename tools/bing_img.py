#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fetch real news/photo images via Bing Images search; download originals.

Usage: python tools/bing_img.py <date> "NN|query" ["NN|query" ...]
Saves output/daily/<date>/images/NN.jpg (cover-cropped to 1920x1080).
"""
import os
import re
import sys
import io
import urllib.request
import urllib.parse

PROJECT_ROOT = "E:/projects/signal_pop"
sys.path.insert(0, os.path.join(PROJECT_ROOT, "scripts"))
from win_pipeline_images import _save_image  # noqa: E402

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")


def bing_image_urls(query, n=15):
    q = urllib.parse.quote(query)
    url = f"https://www.bing.com/images/search?q={q}&form=HDRSC2&first=1"
    req = urllib.request.Request(url, headers={
        "User-Agent": UA, "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8"})
    html = urllib.request.urlopen(req, timeout=20).read().decode("utf-8", "ignore")
    urls = []
    # media url (original)
    for m in re.finditer(r'"murl":"(https?:[^"]+)"', html):
        urls.append(m.group(1))
    for m in re.finditer(r'murl&quot;:&quot;(https?:[^&]+)&quot;', html):
        urls.append(m.group(1))
    # thumbnail src as fallback
    for m in re.finditer(r'"(?:src|thumbnailUrl)":"(https://th\.bing\.com/[^"]+)"', html):
        urls.append(m.group(1))
    # any https image url
    for m in re.finditer(r'https://[^\s"\'<>]+\.(?:jpg|jpeg|png|webp)', html):
        u = m.group(0)
        if "bing.com" not in u or "th.bing.com" in u:
            urls.append(u)
    seen = set()
    out = []
    for u in urls:
        if u in seen:
            continue
        seen.add(u)
        out.append(u)
    return out[:n]


def download(u, referer=None):
    headers = {"User-Agent": UA,
               "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8"}
    if referer:
        headers["Referer"] = referer
    req = urllib.request.Request(u, headers=headers)
    data = urllib.request.urlopen(req, timeout=25).read()
    if len(data) < 8000:
        raise ValueError("too small %d" % len(data))
    return data


def main():
    date = sys.argv[1]
    targets = sys.argv[2:]
    out_dir = os.path.join(PROJECT_ROOT, "output", "daily", date, "images")
    os.makedirs(out_dir, exist_ok=True)
    results = []
    for t in targets:
        num, query = t.split("|", 1)
        num = num.strip()
        query = query.strip()
        print(f"\n=== [{num}] {query}")
        saved = False
        try:
            cand = bing_image_urls(query)
            print(f"  candidates: {len(cand)}")
            for i, u in enumerate(cand[:15]):
                try:
                    ref = urllib.parse.urlparse(u).scheme + "://" + urllib.parse.urlparse(u).netloc
                    data = download(u, referer=ref)
                    # verify + resize via project helper
                    _save_image(data, os.path.join(out_dir, f"{num}.jpg"))
                    print(f"  OK [{i}] {u[:100]}")
                    saved = True
                    break
                except Exception as e:
                    print(f"  fail[{i}] {urllib.parse.urlparse(u).netloc}: {e}")
        except Exception as e:
            print(f"  search error: {e}")
        results.append((num, saved))
    print("\nSUMMARY:")
    for num, ok in results:
        print(f"  {num}.jpg: {'OK' if ok else 'FAILED'}")


if __name__ == "__main__":
    main()
