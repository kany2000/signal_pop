#!/usr/bin/env python3
"""Signal Pop 封面 — 精确复刻 cover_20260712 模板风格"""
import sys, os
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont

DATE = "20260717"
PUB_DT = datetime.strptime(DATE, "%Y%m%d") + timedelta(days=1)
PUB_DATE = PUB_DT.strftime("%Y%m%d")
PUB_DATE_FMT = f"{PUB_DATE[:4]}年{PUB_DATE[4:6]}月{PUB_DATE[6:8]}日"
PUB_DATE_SHORT = f"{PUB_DATE[:4]}.{PUB_DATE[4:6]}.{PUB_DATE[6:8]}"
WEEKDAY = ["星期一","星期二","星期三","星期四","星期五","星期六","星期日"][PUB_DT.weekday()]

FONT = "C:/Windows/Fonts/msyh.ttc"
FONT_BOLD = "C:/Windows/Fonts/msyhbd.ttc"
W, H = 1920, 1080
OUT_DIR = "E:/projects/signal_pop/output/weekly_20260717"


def fnt(size, bold=False):
    return ImageFont.truetype(FONT_BOLD if bold else FONT, size)


def draw_shadow(draw, x, y, text, font, fill=(240,242,245), shadow=(100,110,120), anchor="mm", off=2):
    for ox in (-off, 0, off):
        for oy in (-off, 0, off):
            if ox == 0 and oy == 0: continue
            draw.text((x+ox, y+oy), text, fill=shadow, font=font, anchor=anchor)
    draw.text((x, y), text, fill=fill, font=font, anchor=anchor)


def make_bg():
    """Silver gradient background matching cover_20260712 style."""
    bg = Image.new('RGB', (W, H), (182, 192, 202))
    draw = ImageDraw.Draw(bg)
    # Subtle radial highlight in center
    cx, cy = W // 3, H // 2
    for y in range(H):
        for x in range(W):
            dx, dy = x - cx, y - cy
            dist = (dx*dx + dy*dy) ** 0.5
            factor = max(0, 1 - dist / 1200)
            R = min(255, int(182 + factor * 30))
            G = min(255, int(192 + factor * 30))
            B = min(255, int(202 + factor * 30))
            bg.putpixel((x, y), (R, G, B))
    # Subtle grid
    draw = ImageDraw.Draw(bg)
    grid_color = (160, 170, 180)
    for x in range(0, W, 40):
        draw.line([(x, 0), (x, H)], fill=grid_color, width=1)
    for y in range(0, H, 40):
        draw.line([(0, y), (W, y)], fill=grid_color, width=1)
    return bg


def paste_anchor(bg):
    """Paste the extracted anchor from reference."""
    anchor_path = os.path.join(OUT_DIR, "anchor_extracted.png")
    if os.path.exists(anchor_path):
        anchor = Image.open(anchor_path).convert('RGBA')
        # Place at same position as reference
        bg.paste(anchor, (1300, 0), anchor)
        return True
    return False


def draw_text(bg):
    """Draw text in the reference style: silver bg, white text, center-left."""
    draw = ImageDraw.Draw(bg)

    # Top accent line (gold)
    for x in range(340, 1580):
        draw.rectangle([x, 55, x+1, 58], fill=(212, 175, 55))

    # Main title
    title_font = fnt(66, bold=True)
    draw_shadow(draw, 820, 320, "隔天信号弹", title_font, (240, 242, 245), (120, 130, 140), "mm", 3)

    # Subtitle
    sub_font = fnt(34, bold=False)
    draw_shadow(draw, 820, 395, "周末特别版 · 本周新闻汇总", sub_font, (212, 175, 55), (120, 120, 100), "mm", 2)

    # Date + weekday
    date_font = fnt(26, bold=False)
    draw_shadow(draw, 820, 445, f"{PUB_DATE_FMT}  {WEEKDAY}", date_font, (100, 110, 120), (160, 170, 180), "mm", 1)

    # Bottom info bar
    draw.rectangle([0, 1020, W, 1080], fill=(160, 170, 180, 80))
    ft = fnt(20, bold=False)
    draw.text((60, 1040), f"隔天信号弹 · {PUB_DATE_SHORT}", fill=(100, 110, 120), font=ft)
    draw.text((1860, 1040), "15条核心新闻", fill=(100, 110, 120), font=ft, anchor="rt")

    # Bottom accent
    for x in range(340, 1580):
        draw.rectangle([x, 1020, x+1, 1022], fill=(212, 175, 55))

    return bg


def make_4x3(cover_16x9):
    """4:3 from 16:9: center on silver canvas with side panels."""
    out = Image.new('RGB', (1440, 1080), (182, 192, 202))
    draw = ImageDraw.Draw(out)
    # Grid on canvas
    for x in range(0, 1440, 40):
        draw.line([(x, 0), (x, 1080)], fill=(160, 170, 180), width=1)
    for y in range(0, 1080, 40):
        draw.line([(0, y), (1440, y)], fill=(160, 170, 180), width=1)
    # Paste 16:9 centered
    src = cover_16x9.resize((1440, 810), Image.LANCZOS)
    out.paste(src, (0, 135))
    return out


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    bg = make_bg()
    paste_anchor(bg)
    cover = draw_text(bg)

    p16 = os.path.join(OUT_DIR, f"cover_{PUB_DATE}_16x9.png")
    cover.save(p16)
    print(f"16:9 -> {p16}")

    p43 = make_4x3(cover)
    p43_path = os.path.join(OUT_DIR, f"cover_{PUB_DATE}_4x3.png")
    p43.save(p43_path)
    print(f"4:3 -> {p43_path}")


if __name__ == "__main__":
    main()