#!/usr/bin/env python3
"""
Signal Pop — 生成 opening_bg.jpg（开场/结束卡共用背景）

品牌硬规则（2026-07-09 用户确认）：
  - 新闻直播间后台风格，必须显示 "Sign-POP News" 字样台标
  - 如有人物，形态必须自然、不得扭曲（AI 常把下半身画错位）
  - "Sign-POP News" 用 PIL 精确叠加（AI 直出文字必糊），不用 prompt 出字

用法:
  python3 scripts/gen_opening_bg.py YYYYMMDD
  # 例: python3 scripts/gen_opening_bg.py 20260709
输出:
  /home/kan/shared/signal_pop/archive/img_YYYYMMDD/opening_bg.jpg
"""
import sys, os, io, urllib.request, urllib.parse
from PIL import Image, ImageDraw, ImageFont

ARCHIVE = "/home/kan/shared/signal_pop/archive"
W, H = 1920, 1080

# 场景 prompt：新闻直播间 + 人物自然比例 + 顶部留出干净区域放台标
PROMPT = ("Professional Chinese news broadcast studio, modern anchor desk, "
          "large LED video wall behind showing city skyline, warm gold and blue "
          "lighting, single news anchor with natural realistic body proportions "
          "no distortion, broadcast camera, newsroom, cinematic, no text, "
          "clean background screen area at top")

FONT = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"

def gen(date):
    out_dir = os.path.join(ARCHIVE, f"img_{date}")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, "opening_bg.jpg")

    # 1) Pollinations 出底图（1280x720，后续裁到 1920x1080）
    q = urllib.parse.quote(PROMPT)
    url = f"https://image.pollinations.ai/prompt/{q}?width=1280&height=720&nologo=true&seed=7"
    headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
               "Referer": "https://pollinations.ai/"}
    req = urllib.request.Request(url, headers=headers)
    data = urllib.request.urlopen(req, timeout=120).read()

    img = Image.open(io.BytesIO(data)).convert("RGB")
    iw, ih = img.size
    scale = max(W/iw, H/ih)
    nw, nh = int(iw*scale), int(ih*scale)
    img = img.resize((nw, nh), Image.LANCZOS)
    l = (nw - W)//2; t = (nh - H)//2
    img = img.crop((l, t, l+W, t+H)).convert("RGBA")

    # 2) 叠加清晰台标（顶部中央，金边深底）
    draw = ImageDraw.Draw(img)
    try:
        f_big = ImageFont.truetype(FONT, 64)
    except Exception:
        f_big = ImageFont.load_default()
    text = "Sign-POP News"
    tw = int(draw.textlength(text, font=f_big)) + 80
    th = 96
    bx, by = (W - tw)//2, 90
    draw.rounded_rectangle([(bx, by), (bx+tw, by+th)], radius=16, fill=(10, 20, 40, 180))
    draw.rectangle([(bx, by), (bx+tw, by+th)], outline=(255, 215, 0, 230), width=3)
    draw.text((W//2, by + th//2), text, fill=(255, 215, 0, 255), font=f_big, anchor="mm")

    img.convert("RGB").save(out, "JPEG", quality=92)
    print(f"✅ {out} ({os.path.getsize(out)//1024}KB)")
    print("⚠️ 改完 opening_bg 后必须重跑 build_daily_video.py 并重新 curl 上传 video+cover")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 gen_opening_bg.py YYYYMMDD")
        sys.exit(1)
    gen(sys.argv[1])
