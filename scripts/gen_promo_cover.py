#!/usr/bin/env python3
"""Signal Pop 宣传封面 — 1080x1080 方形版 + 1080x1440 3:4竖版"""
import sys, os, hashlib, urllib.request
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np

FONT_BOLD = "C:/Windows/Fonts/msyhbd.ttc"
FONT_REG = "C:/Windows/Fonts/msyh.ttc"
W, H = 1080, 1080

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
LIGHT_GREY = (180, 190, 200)

OUT_DIR = "E:/projects/signal_pop/output/promo"
os.makedirs(OUT_DIR, exist_ok=True)


def fnt(size, bold=False):
    return ImageFont.truetype(FONT_BOLD if bold else FONT_REG, size)


def make_bg():
    """深色径向渐变带网格"""
    arr = np.zeros((H, W, 3), dtype=np.uint8)
    cx, cy = W // 3, H // 2
    max_d = (W**2 + H**2) ** 0.5
    for y in range(H):
        for x in range(W):
            dist = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
            t = max(0, 1 - dist / max_d)
            arr[y, x] = [int(8 + t * 40), int(12 + t * 35), int(30 + t * 50)]
    bg = Image.fromarray(arr)
    draw = ImageDraw.Draw(bg)
    step = 60
    for x in range(0, W, step):
        draw.line([(x, 0), (x, H)], fill=(25, 35, 60), width=1)
    for y in range(0, H, step):
        draw.line([(0, y), (W, y)], fill=(25, 35, 60), width=1)
    return bg


def get_anchor():
    idx = 3
    url = f"{ANCHOR_POOL[idx]}?w=600&q=85"
    cache = os.path.join(OUT_DIR, ".cache", "promo_anchor.jpg")
    os.makedirs(os.path.dirname(cache), exist_ok=True)
    if not os.path.exists(cache):
        print(f"  Downloading anchor...")
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            with open(cache, "wb") as f:
                f.write(resp.read())
    return Image.open(cache).convert("RGBA")


def paste_anchor(bg, anchor):
    """右侧叠加女主播，方形布局更紧凑"""
    aw, ah = anchor.size
    crop = (aw // 5, 0, aw - aw // 5, ah)
    ac = anchor.crop(crop)
    scale = (W * 0.45) / aw
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
    ax = W - nw + 20
    ay = (H - nh) // 2
    bg.paste(ac, (ax, ay), ac)


def hud_corners(draw):
    L, B = 70, 3
    for cx, cy, dx, dy in [(25, 25, 1, 1), (W-25, 25, -1, 1), (25, H-25, 1, -1), (W-25, H-25, -1, -1)]:
        draw.line([(cx, cy), (cx + dx * L, cy)], fill=CYAN, width=B)
        draw.line([(cx, cy), (cx, cy + dy * L)], fill=CYAN, width=B)


def glow_text(draw, x, y, text, font, color, glow_color, glow_radius=6):
    glow_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow_layer)
    gd.text((x, y), text, fill=glow_color, font=font)
    glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(glow_radius))
    draw.bitmap((0, 0), glow_layer, fill=None)
    draw.text((x, y), text, fill=color, font=font)


def make_promo():
    print(f"Building promo cover @ {W}x{H}...")
    bg = make_bg().convert("RGBA")
    draw = ImageDraw.Draw(bg)

    hud_corners(draw)

    draw.text((60, 45), "每周一三五 · 周六特别版", fill=(0, 200, 255), font=fnt(18, True))

    anchor = get_anchor()
    paste_anchor(bg, anchor)

    tx = 70

    # 金色装饰线
    for x in range(tx, tx + 400):
        draw.rectangle([x, 155, x + 1, 157], fill=GOLD)

    # 主标题
    title_font = fnt(58, bold=True)
    glow_text(draw, tx, 185, "隔天信号弹", title_font, WHITE, (0, 200, 255, 200), 6)
    draw.text((tx, 185), "隔天信号弹", fill=WHITE, font=title_font)

    # 副标题
    sub_font = fnt(28, bold=False)
    draw.text((tx, 270), "每周一三五 · 周六特别版", fill=(100, 220, 255), font=sub_font)
    for ox, oy in [(1, 1), (-1, 1)]:
        draw.text((tx + ox, 270 + oy), "每周一三五 · 周六特别版", fill=(0, 100, 150, 60), font=sub_font)

    # 金色装饰线
    for x in range(tx, tx + 400):
        draw.rectangle([x, 318, x + 1, 320], fill=GOLD)

    # 标语
    slogan_font = fnt(24, bold=True)
    draw.text((tx, 350), "MARK哥的创想引擎", fill=GOLD, font=slogan_font)
    for ox, oy in [(1, 1), (-1, 1)]:
        draw.text((tx + ox, 350 + oy), "MARK哥的创想引擎", fill=(150, 100, 0, 60), font=slogan_font)

    # 特性
    features = [
        "✦ 每周一三五 · 平日新闻",
        "✦ 每周六 · 周末特别版",
        "✦ 科技 · 财经 · 民生 · 国际",
        "✦ 主播AI语音播报",
    ]
    ft_font = fnt(20, bold=False)
    fy = 420
    for line in features:
        draw.text((tx + 10, fy), line, fill=LIGHT_GREY, font=ft_font)
        fy += 34

    # 底部
    ft = fnt(16, bold=False)
    draw.text((40, H - 35), "隔天信号弹 · 每周一三五", fill=(100, 120, 150), font=ft)
    draw.text((W - 40, H - 35), "关注获取最新资讯", fill=(100, 120, 150), font=ft, anchor="rt")

    return bg.convert("RGB")


def make_3x4(square_cover):
    """1080x1080 -> 1080x1440 (3:4), 上下扩展深色背景"""
    pw, ph = 1080, 1440
    canvas = Image.new('RGB', (pw, ph), (10, 15, 35))
    draw = ImageDraw.Draw(canvas)
    # 网格覆盖全画布
    for x in range(0, pw, 60):
        draw.line([(x, 0), (x, ph)], fill=(25, 35, 60), width=1)
    for y in range(0, ph, 60):
        draw.line([(0, y), (pw, y)], fill=(25, 35, 60), width=1)
    # 方形封面居中
    top = (ph - H) // 2
    canvas.paste(square_cover, (0, top))
    return canvas


def main():
    cover = make_promo()
    path = os.path.join(OUT_DIR, "promo_1080x1080.png")
    cover.save(path, "PNG")
    size_kb = os.path.getsize(path) / 1024
    print(f"1:1 -> {path} ({size_kb:.0f}KB)")

    p34 = make_3x4(cover)
    p34_path = os.path.join(OUT_DIR, "promo_1080x1440.png")
    p34.save(p34_path)
    size_kb = os.path.getsize(p34_path) / 1024
    print(f"3:4 -> {p34_path} ({size_kb:.0f}KB)")
    print("Done.")


if __name__ == "__main__":
    main()