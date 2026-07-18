#!/usr/bin/env python3
"""Signal Pop 逐条定制配图生成器（template）。
每条新闻给独立场景 prompt（避免重复赛博隧道/数据中心风），并生成 opening_bg（新闻播报直播间）。

用法：
  python3 references/tailored-img-gen-template.py YYYYMMDD
  # 或直接改 DATE 常量。脚本对 >1KB 已存在的 jpg 自动跳过 → 安全重跑。
"""
import urllib.request, urllib.parse, os, sys

BASE = "/home/kan/shared/signal_pop/archive"
DATE = sys.argv[1] if len(sys.argv) > 1 else "20260709"
out_dir = os.path.join(BASE, f"img_{DATE}")
os.makedirs(out_dir, exist_ok=True)

# 每条新闻对应独立场景（实战 20260709，10条）。换稿期替换此 list。
# 规则：不同类别用不同场景类型（经济/金融→交易所屏；国际→实地；科技→晶圆厂…）。
prompts = [
    "China National Bureau of Statistics building, large digital LED screen showing CPI inflation chart, government economic data report, professional news photo, blue tone",
    "Stock exchange trading floor, three big A-share index boards all in green rising, traders watching screens, Shanghai stock market, dynamic financial photo",
    "People's Bank of China headquarters, monetary policy operation concept, yuan currency symbol glowing, reverse repo liquidity injection, clean financial illustration",
    "Hong Kong stock exchange floor, Hang Seng Index board slightly red down, Hong Kong skyline through window, financial district, cinematic",
    "Pacific ocean launch scene, submarine launching strategic missile trail over horizon, military news illustration, dramatic sky, serious tone",
    "Southeast Asia immigration border checkpoint, concerned officers reviewing documents, human trafficking awareness, documentary news photo, realistic",
    "US Supreme Court building columns, gavel and legal documents, birthright citizenship ruling, Washington DC, solemn institutional photo",
    "West African coastal fishing village, large industrial trawler far offshore, local small boats, Senegal fishermen, documentary photo, ocean blue",
    "FIFA World Cup trophy on stage, football stadium lights, FIFA congress hall, sports governance, cinematic blue",
    "Semiconductor wafer fabrication cleanroom, AI chip macro, glowing circuit, domestic substitution concept, tech blue glow, photorealistic",
]

# opening_bg：新闻播报直播间（与新闻配图不同，非纯色）
opening_prompt = ("Professional Chinese news broadcast studio, modern anchor desk with city skyline LED wall behind, warm gold and blue lighting, broadcast camera, newsroom, cinematic, no text")

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
headers = {"User-Agent": UA, "Referer": "https://pollinations.ai/"}

def fetch(prompt, path, seed):
    q = urllib.parse.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{q}?width=1280&height=720&nologo=true&seed={seed}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=120) as r:
        data = r.read()
    with open(path, "wb") as f:
        f.write(data)
    return len(data)

op = os.path.join(out_dir, "opening_bg.jpg")
if os.path.exists(op) and os.path.getsize(op) > 1000:
    print("✓ opening_bg (已存在)")
else:
    try:
        print(f"✓ opening_bg ({fetch(opening_prompt, op, 7)//1024}KB)")
    except Exception as e:
        print(f"✗ opening_bg: {e}")

for n, prompt in enumerate(prompts, 1):
    path = f"{out_dir}/{n:02d}.jpg"
    if os.path.exists(path) and os.path.getsize(path) > 1000:
        print(f"✓ 第{n}条 (已存在)"); continue
    try:
        print(f"✓ 第{n}条 ({fetch(prompt, path, n*37)//1024}KB)")
    except Exception as e:
        print(f"✗ 第{n}条: {e}")

print("===== 配图生成完成 =====")
