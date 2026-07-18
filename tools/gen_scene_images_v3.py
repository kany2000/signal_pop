#!/usr/bin/env python3
"""Regenerate ALL images - force Pollinations with extreme anti-people"""
import os, urllib.request, urllib.parse, sys, time, subprocess as sp

DATE = sys.argv[1] if len(sys.argv) > 1 else "20260629"
IMG_DIR = f"/home/kan/signal_pop/daily/images/{DATE}"
os.makedirs(IMG_DIR, exist_ok=True)

# 更强的场景描述，禁止人物
# 结构：先场景，最后 NO PEOPLE, empty, nobody, no humans
prompts = {
    1: "bird eye view semiconductor fabrication plant clean room yellow amber lighting industrial machinery equipment nobody no humans empty",
    2: "apple store minimalist white interior wooden display tables product shelves glass wall empty nobody no humans retail architecture",
    3: "Beijing China World Trade Center skyscraper modern architecture blue sky wide angle view no people nobody empty street",
    4: "Buckingham Palace London UK exterior facade fountain garden sunny day no people nobody empty street architectural photography",
    5: "Xbox PlayStation Nintendo Switch game consoles on shelf retail display electronics store product shot no people empty",
    6: "laptop on desk showing Steam game download page keyboard mouse RGB keyboard lighting blue glow no people empty room",
    7: "American diner interior red leather booth seats counter vintage jukebox check bill on table empty no people nobody",
    8: "Times Square New York empty street neon billboard ads digital screens evening blue hour no people nobody",
    9: "aerial view football soccer stadium green field empty seats blue sky clouds architecture no people nobody",
    10: "cargo shipping port container terminal crane ship dock aerial view industrial nobody no people empty"
}

anchor = "TV news broadcast studio empty set desk chairs green screen professional lighting no people nobody"

# 随机种子
import random
random.seed(int(DATE[-4:]))

def gen(url, out_path):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=180) as resp:
        data = resp.read()
    if len(data) > 5000:
        with open(out_path, "wb") as f: f.write(data)
        return len(data)
    raise ValueError(f"Too small: {len(data)}B")

for i in sorted(prompts.keys()):
    out = os.path.join(IMG_DIR, f"{i}.jpg")
    seed = random.randint(1000, 99999)
    # 用负面词
    neg = urllib.parse.quote("people,person,woman,man,face,portrait,character,human")
    url = (f"https://image.pollinations.ai/v1/images?"
           f"prompt={urllib.parse.quote(prompts[i])}&negative_prompt={neg}"
           f"&width=1920&height=1080&seed={seed}")
    print(f"[{i}/10] seed={seed}...", end=" ", flush=True)
    try:
        # 最多重试2次
        for attempt in range(3):
            try:
                sz = gen(url, out)
                break
            except Exception as e:
                if attempt < 2:
                    print(f"retry...", end=" ", flush=True)
                    time.sleep(10)
                else:
                    raise e
        print(f"✓ {sz//1024}KB")
    except Exception as e:
        print(f"✗ {e}")
    time.sleep(6)

# anchor
abg = os.path.join(IMG_DIR, "anchor_bg.jpg")
aseed = random.randint(10000, 99999)
aurl = (f"https://image.pollinations.ai/v1/images?"
        f"prompt={urllib.parse.quote(anchor)}&negative_prompt={neg}"
        f"&width=1920&height=1080&seed={aseed}")
print(f"[anchor] seed={aseed}...", end=" ", flush=True)
try:
    sz = gen(aurl, abg)
    print(f"✓ {sz//1024}KB")
except Exception as e:
    print(f"✗ {e}")

print("\nDone:")
for line in sp.run(["ls","-lh",IMG_DIR], capture_output=True, text=True).stdout.split("\n"):
    if ".jpg" in line: print(line)
