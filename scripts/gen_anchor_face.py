#!/usr/bin/env python3
"""生成AI主播照片 — 根据TTS音色匹配性别"""
import sys, os, hashlib, urllib.request, urllib.parse
from datetime import datetime

# 默认男声（Yunyang），女声 Xioaxiao 时改为 female
VOICE = os.environ.get("TTS_VOICE", "zh-CN-YunyangNeural")
GENDER = "male" if "Yunyang" in VOICE else "female"
SEED = int(hashlib.md5(datetime.now().strftime("%Y%m%d%H").encode()).hexdigest()[:8], 16) % 99999

if GENDER == "female":
    prompt = ("professional Chinese female news anchor, head and shoulders portrait, "
              "natural realistic body proportions, neutral studio background, "
              "professional broadcast look, soft lighting, no text, no distortion")
else:
    prompt = ("professional Chinese male news anchor, head and shoulders portrait, "
              "natural realistic body proportions, neutral studio background, "
              "professional broadcast look, soft lighting, no text, no distortion")

q = urllib.parse.quote(prompt)
url = f"https://image.pollinations.ai/prompt/{q}?width=768&height=768&nologo=true&seed={SEED}"
out = sys.argv[1] if len(sys.argv) > 1 else "anchor.jpg"

print(f"Generating anchor face ({GENDER}, seed={SEED})...")
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=120) as r:
    with open(out, "wb") as f:
        f.write(r.read())
print(f"✅ {out} ({os.path.getsize(out)//1024}KB)")