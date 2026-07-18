#!/usr/bin/env python3
"""Generate scene images via Unsplash (high-quality, relevant)"""
import os, sys, time, urllib.request, urllib.parse, hashlib

DATE = sys.argv[1] if len(sys.argv) > 1 else "20260629"
IMG_DIR = f"/home/kan/signal_pop/daily/images/{DATE}"
os.makedirs(IMG_DIR, exist_ok=True)

# High-volume tags that reliably return images on loremflickr
tags = {
    1: "science",
    2: "robot",
    3: "computer",
    4: "finance",
    5: "gas",
    6: "car",
    7: "3d",
    8: "phone",
    9: "storm",
    10: "ai",
}

seen_md5s = set()

def download_loremflickr(query, lock):
    """Fetch from loremflickr with redirect handling"""
    url = f"https://loremflickr.com/1920/1080/{urllib.parse.quote(query)}?lock={lock}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"})
    for attempt in range(10):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return resp.read()
        except urllib.error.HTTPError as e:
            if e.code == 302:
                loc = e.headers.get('Location')
                if loc:
                    req = urllib.request.Request(loc, headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"})
                    continue
            elif e.code in (500, 503, 403):
                time.sleep(1)
                continue
            raise
    return None

def gen_unique(path, query):
    """Get unique image >= 100KB"""
    for attempt in range(15):
        lock = (hash(query) + attempt * 77777) % 999999
        data = download_loremflickr(query, lock)
        if not data or len(data) < 100000:
            print(f"small,retry", end=" ", flush=True)
            time.sleep(1)
            continue
        md5 = hashlib.md5(data).hexdigest()
        if md5 not in seen_md5s:
            seen_md5s.add(md5)
            with open(path, "wb") as f:
                f.write(data)
            return len(data)
        print(f"dup,retry", end=" ", flush=True)
        time.sleep(1)
    return 0

for i in sorted(tags.keys()):
    out = os.path.join(IMG_DIR, f"{i}.jpg")
    print(f"[{i}/10] {tags[i]}...", end=" ", flush=True)
    sz = gen_unique(out, tags[i])
    print(f"{'✓' if sz else '✗'} {sz//1024 if sz else 0}KB")
    time.sleep(0.5)

# anchor background
out = os.path.join(IMG_DIR, "anchor_bg.jpg")
print(f"[anchor]... ", end=" ", flush=True)
sz = gen_unique(out, "technology,background")
print(f"{'✓' if sz else '✗'} {sz//1024 if sz else 0}KB")

print("\nDone:")
import subprocess as sp
for line in sp.run(["ls", "-lh", IMG_DIR], capture_output=True, text=True).stdout.split("\n"):
    if ".jpg" in line:
        print(line)