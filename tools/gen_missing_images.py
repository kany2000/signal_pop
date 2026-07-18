#!/usr/bin/env python3
"""补生成缺失的4张图"""
import os, urllib.request, urllib.parse, sys, subprocess as sp

DATE = sys.argv[1] if len(sys.argv) > 1 else "20260629"
IMG_DIR = f"/home/kan/signal_pop/daily/images/{DATE}"
os.makedirs(IMG_DIR, exist_ok=True)

missing = {
    8: "Times Square New York at night, giant LED billboards, bright neon signs, empty street, NO PEOPLE, cityscape photography, telephoto lens, flat perspective",
    9: "Empty football stadium aerial view, soccer field with green grass, international flags, sunny day, NO PEOPLE, empty stands, sports architecture, telephoto lens",
    10: "Cargo port aerial view, shipping containers stacked in rows, container ship at dock, logistics cranes, NO PEOPLE, industrial photography, telephoto lens, flat perspective"
}

anchor_prompt = "Empty TV news studio, minimalist futuristic set design, blue white ambient lighting, glass panels, broadcast equipment, NO PEOPLE, empty room, interior architecture"

import time, json

def gen(url, out_path):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = resp.read()
    if len(data) > 5000:
        with open(out_path, "wb") as f: f.write(data)
        return len(data)
    raise ValueError(f"Too small: {len(data)}B")

for i in sorted(missing.keys()):
    out = os.path.join(IMG_DIR, f"{i}.jpg")
    url = f"https://image.pollinations.ai/v1/images?prompt={urllib.parse.quote(missing[i])}&width=1920&height=1080&model=flux&n=1&seed={i*100+99}"
    print(f"[{i}/10] {missing[i][:50]}...", end=" ", flush=True)
    try:
        sz = gen(url, out)
        print(f"✓ {sz//1024}KB")
    except Exception as e:
        print(f"✗ {e}")
    time.sleep(5)

abg = os.path.join(IMG_DIR, "anchor_bg.jpg")
aurl = f"https://image.pollinations.ai/v1/images?prompt={urllib.parse.quote(anchor_prompt)}&width=1920&height=1080&model=flux&n=1&seed=42"
print(f"[anchor] studio bg...", end=" ", flush=True)
try:
    sz = gen(aurl, abg)
    print(f"✓ {sz//1024}KB")
except Exception as e:
    print(f"✗ {e}")

print("\nDone:")
for line in sp.run(["ls","-lh",IMG_DIR], capture_output=True, text=True).stdout.split("\n"):
    if ".jpg" in line: print(line)
