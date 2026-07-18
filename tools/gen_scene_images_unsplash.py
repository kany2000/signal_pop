#!/usr/bin/env python3
"""Generate scene images via Unsplash Source API (high-quality, relevant)"""
import os, sys, time, urllib.request, urllib.parse, hashlib

DATE = sys.argv[1] if len(sys.argv) > 1 else "20260703"
IMG_DIR = f"/home/kan/signal_pop/daily/images/{DATE}"
os.makedirs(IMG_DIR, exist_ok=True)

# Unsplash Source API: https://source.unsplash.com/WIDTH/HEIGHT/?query1,query2,query3
# News-specific keywords mapped to each news item (1-10 + anchor_bg)
tags = {
    1: "sports,football,stadium,athlete,worldcup",
    2: "typhoon,storm,weather,ocean,waves",
    3: "mountain,nature,landscape,fence,outdoor",
    4: "gasstation,fuel,city,traffic,urban",
    5: "technology,computer,server,chip,processor",
    6: "hospital,medical,healthcare,emergency",
    7: "robot,robotics,technology,future,automation",
    8: "ai,neural,network,technology,digital,brain",
    9: "ai,voice,technology,speech,audio,digital",
    10: "philosophy,books,library,knowledge,thinking",
}

seen_md5s = set()

def download_unsplash(query, lock):
    """Fetch from Unsplash Source API with redirect handling"""
    # source.unsplash.com returns random image matching query via 302 redirect
    url = f"https://source.unsplash.com/1920x1080/?{urllib.parse.quote(query)}&lock={lock}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    for _ in range(5):
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                if resp.status in (301, 302, 303, 307, 308):
                    loc = resp.headers.get('Location')
                    if loc:
                        req = urllib.request.Request(loc, headers={"User-Agent": "Mozilla/5.0"})
                        continue
                return resp.read()
        except urllib.error.HTTPError as e:
            if e.code in (302, 500, 503):
                loc = e.headers.get('Location')
                if loc and e.code == 302:
                    req = urllib.request.Request(loc, headers={"User-Agent": "Mozilla/5.0"})
                    continue
                if e.code in (500, 503):
                    time.sleep(2)
                    continue
            raise
    return None

def gen_unique(path, query):
    """Get unique image >= 100KB"""
    for attempt in range(15):
        lock = (hash(query) + attempt * 77777) % 999999
        data = download_unsplash(query, lock)
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
sz = gen_unique(out, "technology,background,digital,abstract")
print(f"{'✓' if sz else '✗'} {sz//1024 if sz else 0}KB")

print("\nDone:")
import subprocess as sp
for line in sp.run(["ls", "-lh", IMG_DIR], capture_output=True, text=True).stdout.split("\n"):
    if ".jpg" in line:
        print(line)