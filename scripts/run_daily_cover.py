#!/usr/bin/env python3
"""Signal Pop 每日封面 — 复用 run_cover.py 风格，参数适配"""
import sys, os, hashlib, urllib.request
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np

DATE = "20260724"
PUB_DT = datetime.strptime(DATE, "%Y%m%d")
PUB_DATE = PUB_DT.strftime("%Y%m%d")
PUB_DATE_FMT = f"{PUB_DATE[:4]}年{PUB_DATE[4:6]}月{PUB_DATE[6:8]}日"
PUB_DATE_SHORT = f"{PUB_DATE[:4]}.{PUB_DATE[4:6]}.{PUB_DATE[6:8]}"

OUT_DIR = "E:/projects/signal_pop/output/daily_20260724"
CACHE = os.path.join(OUT_DIR, ".cache")
os.makedirs(CACHE, exist_ok=True)

FONT_BOLD = "C:/Windows/Fonts/msyhbd.ttc"
FONT_REG = "C:/Windows/Fonts/msyh.ttc"
W, H = 1920, 1080

ANCHOR_POOL = [
    "https://images.unsplash.com/photo-1534528741775-53994a69daeb",
    "https://images.unsplash.com/photo-1508214751196-bcfd4ca60f91",
    "https://images.unsplash.com/photo-1544005313-94ddf0286df2",
    "https://images.unsplash.com/photo-1551836022-d5d88e9218df",
    "https://images.unsplash.com/photo-1567532939604-b6b5b0db2604",
    "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2",
    "https://images.unsplash.com/photo-1580489944761-15a19d654956",
    "https://images.unsplash.com/photo-1594744803329-e58b31de8bf5",
    "https://images.unsplash.com/photo-1573497019940-1c28c88b4f3e",
    "https://images.unsplash.com/photo-1517841905240-472988babdf9",
    "https://images.unsplash.com/photo-1524504388940-b1c1722653e1",
    "https://images.unsplash.com/photo-1494790108377-be9c29b29330",
    "https://images.unsplash.com/photo-1531746020798-e6953c6e8e04",
    "https://images.unsplash.com/photo-1489424731084-a5d8b219a5bb",
    "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d",
    "https://images.unsplash.com/photo-1542587222-f9172e5c1d6c",
    "https://images.unsplash.com/photo-1560250097-0b93528c311a",
]

CYAN = (0, 255, 255)
GOLD = (255, 200, 50)
WHITE = (255, 255, 255)


def fnt(size, bold=False):
    return ImageFont.truetype(FONT_BOLD if bold else FONT_REG, size)


def make_bg():
    arr = np.zeros((H, W, 3), dtype=np.uint8)
    cx, cy = W // 3, H // 2
    max_d = ((W // 2) ** 2 + (H // 2) ** 2) ** 0.5
    for y in range(H):
        for x in range(W):
            dist = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
            t = max(0, 1 - dist / max_d)
            arr[y, x] = [int(10 + t * 35), int(15 + t * 30), int(35 + t * 45)]
    bg = Image.fromarray(arr)
    draw = ImageDraw.Draw(bg)
    step = 60
    for x in range(0, W, step):
        draw.line([(x, 0), (x, H)], fill=(25, 35, 60), width=1)
    for y in range(0, H, step):
        draw.line([(0, y), (W, y)], fill=(25, 35, 60), width=1)
    return bg


def get_anchor():
    seed = int(hashlib.md5(DATE.encode()).hexdigest()[:8], 16)
    idx = seed % len(ANCHOR_POOL)
    url = f"{ANCHOR_POOL[idx]}?w=900&q=85"
    cache = os.path.join(CACHE, f"anchor_f_{idx}.jpg")
    if not os.path.exists(cache):
        print(f"  Downloading anchor #{idx}...")
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            with open(cache, "wb") as f:
                f.write(resp.read())
    return Image.open(cache).convert("RGBA")


def paste_anchor(bg, anchor):
    aw, ah = anchor.size
    crop = (aw // 5, 0, aw - aw // 5, ah)
    ac = anchor.crop(crop)
    scale = (W * 0.42) / aw
    nw, nh = int(aw * scale), int(ah * scale)
    ac = ac.resize((nw, nh), Image.LANCZOS)
    mask = Image.new("L", (nw, nh), 255)
    md = ImageDraw.Draw(mask)
    edge = min(nw, nh) // 5
    for i in range(edge):
        a = int(255 * (i / edge) ** 2)
        md.rectangle([i, i, nw - 1 - i, nh - 1 - i], outline=a)
    mask = mask.filter(ImageFilter.GaussianBlur(18))
    ac.putalpha(mask)
    ax = W - nw + 30
    ay = (H - nh) // 2
    bg.paste(ac, (ax, ay), ac)


def hud_corners(draw):
    for cx, cy, dx, dy in [(30, 30, 1, 1), (W-30, 30, -1, 1), (30, H-30, 1, -1), (W-30, H-30, -1, -1)]:
        draw.line([(cx, cy), (cx + dx * 80, cy)], fill=CYAN, width=2)
        draw.line([(cx, cy), (cx, cy + dy * 80)], fill=CYAN, width=2)


def make_cover():
    print(f"Building daily cover @ {W}x{H}...")
    bg = make_bg().convert("RGBA")
    draw = ImageDraw.Draw(bg)
    hud_corners(draw)

    draw.text((90, 60), "新闻 · 科技 · 财经", fill=(0, 200, 255), font=fnt(22, True))

    anchor = get_anchor()
    paste_anchor(bg, anchor)

    tx = 120
    title_font = fnt(72, bold=True)
    draw.text((tx, 260), "隔天信号弹", fill=WHITE, font=title_font)
    for ox, oy in [(2, 2), (-2, 2), (2, -2), (-2, -2)]:
        draw.text((tx + ox, 260 + oy), "隔天信号弹", fill=(0, 200, 255, 80), font=title_font)

    sub_font = fnt(34, bold=False)
    draw.text((tx, 365), "每日新闻播报", fill=(100, 220, 255), font=sub_font)
    for ox, oy in [(1, 1), (-1, 1)]:
        draw.text((tx + ox, 365 + oy), "每日新闻播报", fill=(0, 100, 150, 60), font=sub_font)

    mark_font = fnt(38, bold=True)
    draw.text((tx, 445), "MARK哥的创想引擎", fill=GOLD, font=mark_font)
    for ox, oy in [(1, 1), (-1, 1)]:
        draw.text((tx + ox, 445 + oy), "MARK哥的创想引擎", fill=(150, 100, 0, 60), font=mark_font)

    ft = fnt(20, bold=False)
    draw.text((60, H - 45), f"隔天信号弹 · {PUB_DATE_SHORT}", fill=(100, 120, 150), font=ft)
    draw.text((W - 60, H - 45), "10条核心新闻", fill=(100, 120, 150), font=ft, anchor="rt")

    return bg.convert("RGB")


def make_4x3(cover):
    cw, ch = 1440, 1080
    canvas = Image.new('RGB', (cw, ch), (10, 15, 35))
    draw = ImageDraw.Draw(canvas)
    for x in range(0, cw, 60):
        draw.line([(x, 0), (x, ch)], fill=(25, 35, 60), width=1)
    for y in range(0, ch, 60):
        draw.line([(0, y), (cw, y)], fill=(25, 35, 60), width=1)
    src = cover.resize((cw, int(1080 * cw / 1920)), Image.LANCZOS)
    top = (ch - src.height) // 2
    canvas.paste(src, (0, top))
    return canvas


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    for f in os.listdir(CACHE):
        if f.startswith("anchor_"):
            os.remove(os.path.join(CACHE, f))

    cover = make_cover()
    p16 = os.path.join(OUT_DIR, f"cover_{PUB_DATE}_16x9.png")
    cover.save(p16)
    print(f"16:9 -> {p16}")

    p43 = make_4x3(cover)
    p43_path = os.path.join(OUT_DIR, f"cover_{PUB_DATE}_4x3.png")
    p43.save(p43_path)
    print(f"4:3 -> {p43_path}")
    print("Done.")


if __name__ == "__main__":
    main()