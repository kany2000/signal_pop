#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Signal Pop 周末特别版 · 双人封面生成 v3

主持人脸（阿信/小蓝 = 信蓝组合）为固定人设跨期复用（项目规则）。
版式每周变化，避免视觉雷同。三种风格：
  - split    : 经典左右分屏 + 金色中带（原 v1/v2，兜底）
  - magazine : 杂志头条风（双人左侧 + 大刊头 TOP15 + 本期 TOP3 标题预告）
  - neon     : 巨型数字风（巨大"15" + 双人圆形头像 + 每周哈希轮换的霓虹光晕色）

用法：python tools/gen_weekly_talk_cover.py [PREP_DATE] [STYLE] [SUFFIX]
  STYLE : split | magazine | neon   默认 magazine
  SUFFIX: 可选，附加到文件名做风格预览；正式出品不传 SUFFIX（输出规范名）
"""
import os
import sys
import hashlib
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps

PROJECT_ROOT = "E:/projects/signal_pop"
PREP_DATE = sys.argv[1] if len(sys.argv) > 1 else "20260821"
STYLE = sys.argv[2] if len(sys.argv) > 2 else "magazine"
SUFFIX = sys.argv[3] if len(sys.argv) > 3 else ""

OUT_DIR = os.path.join(PROJECT_ROOT, "output", "weekly", PREP_DATE)
IMAGES_DIR = os.path.join(OUT_DIR, "images")
FONT = "C:/Windows/Fonts/msyh.ttc"
FONT_BOLD = "C:/Windows/Fonts/msyhbd.ttc"

PUB_DT = datetime.strptime(PREP_DATE, "%Y%m%d") + timedelta(days=1)
PUB_DATE_SHORT = f"{PUB_DT.year}.{PUB_DT.month:02d}.{PUB_DT.day:02d}"
WEEKDAY_CN = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][PUB_DT.weekday()]

# 调色板
AXIN_BLUE = (58, 130, 210)
XIAOLAN_PINK = (220, 90, 150)
GOLD = (212, 175, 55)
GOLD_BRIGHT = (255, 215, 100)
WHITE = (250, 250, 252)
LIGHT_GREY = (190, 198, 210)
DARK = (8, 10, 18)
DARK_NAVY = (15, 22, 42)
PANEL = (18, 24, 44)

# 霓虹光晕色池（按日期哈希取，避免连续周同色）
NEON_HUES = [
    (110, 80, 220),   # 紫
    (60, 180, 220),   # 青
    (220, 90, 150),   # 粉
    (80, 200, 120),   # 绿
    (230, 150, 60),   # 橙
    (180, 60, 200),   # 品红
]


def week_hue():
    h = int(hashlib.md5(PREP_DATE.encode()).hexdigest(), 16)
    return NEON_HUES[h % len(NEON_HUES)]


def fnt(size, bold=True):
    return ImageFont.truetype(FONT_BOLD if bold else FONT, size)


def fit_face(face_img, w, h, blur_overlay=True):
    img = ImageOps.fit(face_img.convert("RGB"), (w, h), method=Image.LANCZOS, centering=(0.5, 0.4))
    if blur_overlay:
        ov = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        d = ImageDraw.Draw(ov)
        th = int(h * 0.18)
        for i in range(th):
            a = int(120 * (1 - i / th))
            d.line([(0, i), (w, i)], fill=(0, 0, 0, a))
        bh = int(h * 0.12)
        for i in range(bh):
            a = int(160 * (i / bh))
            d.line([(0, h - 1 - i), (w, h - 1 - i)], fill=(0, 0, 0, a))
        img = Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB")
    return img


def circular_face(face_img, size, ring_color=GOLD, ring_w=5):
    face = fit_face(face_img, size, size, blur_overlay=False)
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, size, size], fill=255)
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    out.paste(face.convert("RGBA"), (0, 0), mask)
    if ring_w:
        ring = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        ImageDraw.Draw(ring).ellipse([0, 0, size, size], outline=(*ring_color, 255), width=ring_w)
        out = Image.alpha_composite(out, ring)
    return out


def vgrad(w, h, c1, c2):
    base = Image.new("RGB", (w, h), c1)
    d = ImageDraw.Draw(base)
    for y in range(h):
        t = y / h
        col = tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))
        d.line([(0, y), (w, y)], fill=col)
    return base


def add_glow(canvas, cx, cy, r, color, max_alpha=110):
    ov = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    steps = 36
    for i in range(steps, 0, -1):
        rr = int(r * i / steps)
        a = int(max_alpha * (1 - i / steps))
        d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], fill=(*color, a))
    return Image.alpha_composite(canvas.convert("RGBA"), ov).convert("RGB")


def draw_outline(d, pos, text, font, fill, outline=(20, 16, 6), w=4):
    x, y = pos
    for ox, oy in [(-w, 0), (w, 0), (0, -w), (0, w), (-w, -w), (w, w), (-w, w), (w, -w)]:
        d.text((x + ox, y + oy), text, fill=outline, font=font, anchor="mm")
    d.text(pos, text, fill=fill, font=font, anchor="mm")


def rounded_panel(canvas, box, radius=28, color=PANEL, alpha=235, border=None):
    ov = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    d.rounded_rectangle(box, radius=radius, fill=(*color, alpha))
    if border:
        d.rounded_rectangle(box, radius=radius, outline=(*border, 255), width=3)
    return Image.alpha_composite(canvas.convert("RGBA"), ov).convert("RGB")


# 本期 TOP3 头条（杂志风展示用，与新闻稿同步）
TOP3 = [
    ("01", "财政部五年加码科技投入", "研发经费超 3.9 万亿"),
    ("02", "边缘行者 2 定档 10.20", "赛博朋克衍生动画续作"),
    ("03", "固态电池首项国际标准", "中国牵头立项"),
]


# ===================== SPLIT（原版，兜底） =====================
def build_split_landscape(w, h, axin, xiaolan):
    center_w = int(w * 0.16)
    half_w = (w - center_w) // 2
    left = fit_face(axin, half_w, h)
    right = fit_face(xiaolan, half_w, h)
    canvas = Image.new("RGB", (w, h), DARK)
    canvas.paste(left, (0, 0))
    canvas.paste(right, (w - half_w, 0))
    ov = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    for x in range(center_w):
        r2 = x / center_w
        r = int(120 + 90 * (0.5 - abs(r2 - 0.5)))
        g = int(80 + 80 * (0.5 - abs(r2 - 0.5)))
        b = int(30 + 30 * (0.5 - abs(r2 - 0.5)))
        od.line([(half_w + x, 0), (half_w + x, h)], fill=(r, g, b, 255))
    canvas = Image.alpha_composite(canvas.convert("RGBA"), ov).convert("RGB")
    d = ImageDraw.Draw(canvas)
    title_size = int(center_w * 0.34)
    tf = fnt(title_size, True)
    cx = half_w + center_w // 2
    tt = "本\n周\nTOP\n15"
    lines = tt.split("\n")
    lh = tf.size + 4
    y0 = (h - lh * len(lines)) // 2
    for i, ln in enumerate(lines):
        y = y0 + i * lh
        for ox, oy in [(-2, 0), (2, 0), (0, -2), (0, 2)]:
            d.text((cx + ox, y + oy), ln, fill=(40, 30, 10), font=tf, anchor="mm")
        d.text((cx, y), ln, fill=GOLD_BRIGHT, font=tf, anchor="mm")
    d.text((w // 2, int(h * 0.04)), "隔天信号弹 · 周末特别版", fill=GOLD, font=fnt(int(w * 0.022), True), anchor="mm")
    d.text((w // 2, int(h * 0.075)), "信蓝组合 · 本周 TOP15 对话脱口秀", fill=LIGHT_GREY, font=fnt(int(w * 0.016)), anchor="mm")
    d.text((w // 2, h - int(h * 0.05)), f"{WEEKDAY_CN} 08:00 · {PUB_DATE_SHORT}", fill=GOLD, font=fnt(int(w * 0.024), True), anchor="mm")
    nf = fnt(int(h * 0.07), True)
    ap = (half_w // 2, h - int(h * 0.13))
    for ox, oy in [(-3, 0), (3, 0), (0, -3), (0, 3)]:
        d.text((ap[0] + ox, ap[1] + oy), "阿信", fill=(20, 30, 60), font=nf, anchor="mm")
    d.text(ap, "阿信", fill=AXIN_BLUE, font=nf, anchor="mm")
    xp = (w - half_w // 2, h - int(h * 0.13))
    for ox, oy in [(-3, 0), (3, 0), (0, -3), (0, 3)]:
        d.text((xp[0] + ox, xp[1] + oy), "小蓝", fill=(60, 20, 40), font=nf, anchor="mm")
    d.text(xp, "小蓝", fill=XIAOLAN_PINK, font=nf, anchor="mm")
    d.rectangle([0, 0, w, 4], fill=GOLD)
    d.rectangle([0, h - 4, w, h], fill=GOLD)
    return canvas


def build_split_portrait(w, h, axin, xiaolan):
    band_h = int(h * 0.13)
    half_h = (h - band_h) // 2
    top = fit_face(axin, w, half_h)
    bot = fit_face(xiaolan, w, half_h)
    canvas = Image.new("RGB", (w, h), DARK)
    canvas.paste(top, (0, 0))
    canvas.paste(bot, (0, h - half_h))
    ov = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    for y in range(band_h):
        r2 = y / band_h
        ar = int(70 + 90 * (0.5 - abs(r2 - 0.5)))
        ag = int(50 + 70 * (0.5 - abs(r2 - 0.5)))
        ab = int(20 + 25 * (0.5 - abs(r2 - 0.5)))
        od.line([(0, half_h + y), (w, half_h + y)], fill=(ar, ag, ab, 255))
    canvas = Image.alpha_composite(canvas.convert("RGBA"), ov).convert("RGB")
    d = ImageDraw.Draw(canvas)
    bcy = half_h + band_h // 2
    ts = int(band_h * 0.55)
    ss = int(band_h * 0.20)
    tf = fnt(ts, True)
    sf = fnt(ss, True)
    title = "本周 TOP15"
    for ox, oy in [(-2, 0), (2, 0), (0, -2), (0, 2)]:
        d.text((w // 2 + ox, bcy - ts * 0.4 + oy), title, fill=(40, 30, 10), font=tf, anchor="mm")
    d.text((w // 2, bcy - ts * 0.4), title, fill=GOLD_BRIGHT, font=tf, anchor="mm")
    d.text((w // 2, bcy + ss * 0.8), "信蓝组合 · 开聊！", fill=WHITE, font=sf, anchor="mm")
    d.rectangle([0, 0, w, 5], fill=GOLD)
    d.text((w // 2, int(w * 0.06) + 8), "隔天信号弹 · 周末特别版", fill=GOLD, font=fnt(int(w * 0.07), True), anchor="mm")
    d.rectangle([0, h - 5, w, h], fill=GOLD)
    d.text((w // 2, h - int(w * 0.06) - 8), f"{PUB_DT.month}/{PUB_DT.day} {WEEKDAY_CN} 08:00", fill=GOLD, font=fnt(int(w * 0.06), True), anchor="mm")
    nf = fnt(int(w * 0.085), True)
    ap = (int(w * 0.12), half_h - int(w * 0.06))
    for ox, oy in [(-3, 0), (3, 0), (0, -3), (0, 3)]:
        d.text((ap[0] + ox, ap[1] + oy), "阿信", fill=(20, 30, 60), font=nf, anchor="mm")
    d.text(ap, "阿信", fill=AXIN_BLUE, font=nf, anchor="mm")
    xp = (int(w * 0.88), h - half_h + int(w * 0.06))
    for ox, oy in [(-3, 0), (3, 0), (0, -3), (0, 3)]:
        d.text((xp[0] + ox, xp[1] + oy), "小蓝", fill=(60, 20, 40), font=nf, anchor="mm")
    d.text(xp, "小蓝", fill=XIAOLAN_PINK, font=nf, anchor="mm")
    return canvas


# ===================== MAGAZINE =====================
def build_magazine_landscape(w, h, axin, xiaolan):
    canvas = vgrad(w, h, (14, 20, 38), (8, 12, 24))
    canvas = add_glow(canvas, int(w * 0.25), int(h * 0.35), int(h * 0.65), AXIN_BLUE, 95)
    canvas = add_glow(canvas, int(w * 0.85), int(h * 0.85), int(h * 0.55), XIAOLAN_PINK, 80)
    d = ImageDraw.Draw(canvas)
    d.text((70, 60), "隔天信号弹 · 周末特别版", fill=GOLD, font=fnt(38, True), anchor="lm")
    d.text((70, 108), "SIGNAL POP / WEEKEND SPECIAL", fill=LIGHT_GREY, font=fnt(20), anchor="lm")
    # 双人圆形头像
    fs = 330
    ay = int(h * 0.62)
    a1 = circular_face(axin, fs, GOLD, 6)
    a2 = circular_face(xiaolan, fs, GOLD, 6)
    canvas.paste(a1, (170, ay - fs // 2), a1)
    canvas.paste(a2, (520, ay - fs // 2), a2)
    nf = fnt(46, True)
    draw_outline(d, (170 + fs // 2, ay + fs // 2 + 55), "阿信", nf, AXIN_BLUE, outline=(10, 20, 40), w=4)
    draw_outline(d, (520 + fs // 2, ay + fs // 2 + 55), "小蓝", nf, XIAOLAN_PINK, outline=(30, 10, 20), w=4)
    # 右侧大刊头面板
    px1, py1, px2, py2 = 980, 200, w - 70, h - 160
    canvas = rounded_panel(canvas, (px1, py1, px2, py2), radius=30, color=PANEL, alpha=225, border=GOLD)
    d = ImageDraw.Draw(canvas)
    mh = fnt(150, True)
    draw_outline(d, ((px1 + px2) // 2, py1 + 110), "TOP 15", mh, GOLD_BRIGHT, outline=(20, 14, 4), w=6)
    d.text(((px1 + px2) // 2, py1 + 180), "本周大事 · 信蓝组合盘点", fill=WHITE, font=fnt(34, True), anchor="mm")
    ty = py1 + 270
    for rank, title, sub in TOP3:
        rb = px1 + 60
        d.ellipse([rb - 42, ty - 42, rb + 42, ty + 42], fill=(*GOLD, 255), outline=(40, 30, 10), width=3)
        d.text((rb, ty), rank, fill=(20, 14, 4), font=fnt(40, True), anchor="mm")
        d.text((px1 + 130, ty - 18), title, fill=WHITE, font=fnt(36, True), anchor="lm")
        d.text((px1 + 130, ty + 24), sub, fill=LIGHT_GREY, font=fnt(24), anchor="lm")
        ty += 105
    # 底部署名条
    ov = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    od.rectangle([0, h - 90, w, h], fill=(8, 10, 18, 225))
    canvas = Image.alpha_composite(canvas.convert("RGBA"), ov).convert("RGB")
    d = ImageDraw.Draw(canvas)
    d.rectangle([0, h - 4, w, h], fill=GOLD)
    d.text((w // 2, h - 48), f"{PUB_DT.month}/{PUB_DT.day} {WEEKDAY_CN} 08:00 · 信蓝组合 · 每周相见", fill=GOLD, font=fnt(36, True), anchor="mm")
    return canvas


def build_magazine_portrait(w, h, axin, xiaolan):
    canvas = vgrad(w, h, (14, 20, 38), (8, 12, 24))
    canvas = add_glow(canvas, int(w * 0.2), int(h * 0.18), int(w * 0.7), AXIN_BLUE, 90)
    canvas = add_glow(canvas, int(w * 0.9), int(h * 0.88), int(w * 0.6), XIAOLAN_PINK, 80)
    d = ImageDraw.Draw(canvas)
    d.text((w // 2, 80), "隔天信号弹 · 周末特别版", fill=GOLD, font=fnt(int(w * 0.07), True), anchor="mm")
    d.text((w // 2, 140), "WEEKEND SPECIAL", fill=LIGHT_GREY, font=fnt(int(w * 0.04)), anchor="mm")
    mh = fnt(int(w * 0.24), True)
    draw_outline(d, (w // 2, 260), "TOP 15", mh, GOLD_BRIGHT, outline=(20, 14, 4), w=7)
    d.text((w // 2, 350), "本周大事 · 信蓝组合盘点", fill=WHITE, font=fnt(int(w * 0.055), True), anchor="mm")
    # 双人
    fs = int(w * 0.30)
    ay = 440
    a1 = circular_face(axin, fs, GOLD, 6)
    a2 = circular_face(xiaolan, fs, GOLD, 6)
    canvas.paste(a1, (int(w * 0.13), ay), a1)
    canvas.paste(a2, (int(w * 0.57), ay), a2)
    d = ImageDraw.Draw(canvas)
    draw_outline(d, (int(w * 0.13) + fs // 2, ay + fs + 30), "阿信", fnt(int(w * 0.07), True), AXIN_BLUE, outline=(10, 20, 40), w=4)
    draw_outline(d, (int(w * 0.57) + fs // 2, ay + fs + 30), "小蓝", fnt(int(w * 0.07), True), XIAOLAN_PINK, outline=(30, 10, 20), w=4)
    # 头条面板
    py1 = ay + fs + 110
    px1, px2 = 50, w - 50
    py2 = h - 140
    canvas = rounded_panel(canvas, (px1, py1, px2, py2), radius=26, color=PANEL, alpha=225, border=GOLD)
    d = ImageDraw.Draw(canvas)
    ty = py1 + 70
    step = (py2 - py1 - 70) // 3
    for rank, title, sub in TOP3:
        rb = px1 + 55
        d.ellipse([rb - 36, ty - 36, rb + 36, ty + 36], fill=(*GOLD, 255), outline=(40, 30, 10), width=3)
        d.text((rb, ty), rank, fill=(20, 14, 4), font=fnt(int(w * 0.07), True), anchor="mm")
        d.text((px1 + 115, ty - 18), title, fill=WHITE, font=fnt(int(w * 0.055), True), anchor="lm")
        d.text((px1 + 115, ty + 24), sub, fill=LIGHT_GREY, font=fnt(int(w * 0.038)), anchor="lm")
        ty += step
    # 底部署名
    ov = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    od.rectangle([0, h - 110, w, h], fill=(8, 10, 18, 230))
    canvas = Image.alpha_composite(canvas.convert("RGBA"), ov).convert("RGB")
    d = ImageDraw.Draw(canvas)
    d.rectangle([0, h - 5, w, h], fill=GOLD)
    d.text((w // 2, h - 60), f"{PUB_DT.month}/{PUB_DT.day} {WEEKDAY_CN} 08:00 · 信蓝组合", fill=GOLD, font=fnt(int(w * 0.06), True), anchor="mm")
    return canvas


# ===================== NEON =====================
def build_neon_landscape(w, h, axin, xiaolan):
    hue = week_hue()
    canvas = vgrad(w, h, (6, 8, 16), (10, 14, 28))
    canvas = add_glow(canvas, w // 2, int(h * 0.45), int(h * 0.7), hue, 115)
    canvas = add_glow(canvas, int(w * 0.18), int(h * 0.78), int(h * 0.4), AXIN_BLUE, 55)
    canvas = add_glow(canvas, int(w * 0.82), int(h * 0.22), int(h * 0.4), XIAOLAN_PINK, 55)
    d = ImageDraw.Draw(canvas)
    d.text((w // 2, 70), "隔天信号弹 · 周末特别版 · 信蓝组合", fill=LIGHT_GREY, font=fnt(int(w * 0.022), True), anchor="mm")
    # 巨型 "15"
    big = fnt(int(h * 0.38), True)
    cx, cy = w // 2, int(h * 0.42)
    for r, a in [(32, 35), (22, 55), (14, 85), (8, 130)]:
        ov = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        od = ImageDraw.Draw(ov)
        od.text((cx, cy), "15", font=big, fill=(*hue, a), anchor="mm")
        ov = ov.filter(ImageFilter.GaussianBlur(radius=r / 3))
        canvas = Image.alpha_composite(canvas.convert("RGBA"), ov).convert("RGB")
    d = ImageDraw.Draw(canvas)
    draw_outline(d, (cx, cy), "15", big, WHITE, outline=(*hue, 255), w=10)
    d.text((cx, cy - int(h * 0.26)), "T O P", fill=(*hue, 255), font=fnt(int(h * 0.09), True), anchor="mm")
    d.text((cx, cy + int(h * 0.22)), "本周 15 件大事 · 一报一评", fill=WHITE, font=fnt(int(h * 0.05), True), anchor="mm")
    # 双人圆形头像
    fs = int(h * 0.22)
    fy = h - fs - 110
    a1 = circular_face(axin, fs, AXIN_BLUE, 5)
    a2 = circular_face(xiaolan, fs, XIAOLAN_PINK, 5)
    canvas.paste(a1, (int(w * 0.05), fy), a1)
    canvas.paste(a2, (w - fs - int(w * 0.05), fy), a2)
    d = ImageDraw.Draw(canvas)
    d.text((w // 2, h - 45), f"{PUB_DT.month}/{PUB_DT.day} {WEEKDAY_CN} 08:00", fill=(*hue, 255), font=fnt(int(w * 0.022), True), anchor="mm")
    return canvas


def build_neon_portrait(w, h, axin, xiaolan):
    hue = week_hue()
    canvas = vgrad(w, h, (6, 8, 16), (10, 14, 28))
    canvas = add_glow(canvas, w // 2, int(h * 0.42), int(h * 0.38), hue, 130)
    d = ImageDraw.Draw(canvas)
    d.text((w // 2, 60), "隔天信号弹 · 周末特别版", fill=LIGHT_GREY, font=fnt(int(w * 0.06), True), anchor="mm")
    d.text((w // 2, 115), "信蓝组合", fill=(*hue, 255), font=fnt(int(w * 0.07), True), anchor="mm")
    big = fnt(int(h * 0.30), True)
    cx, cy = w // 2, int(h * 0.42)
    for r, a in [(28, 35), (20, 55), (12, 85), (7, 130)]:
        ov = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        od = ImageDraw.Draw(ov)
        od.text((cx, cy), "15", font=big, fill=(*hue, a), anchor="mm")
        ov = ov.filter(ImageFilter.GaussianBlur(radius=r / 3))
        canvas = Image.alpha_composite(canvas.convert("RGBA"), ov).convert("RGB")
    d = ImageDraw.Draw(canvas)
    draw_outline(d, (cx, cy), "15", big, WHITE, outline=(*hue, 255), w=8)
    d.text((cx, cy + int(h * 0.16)), "本周 15 件大事", fill=WHITE, font=fnt(int(w * 0.07), True), anchor="mm")
    # 双人
    fs = int(w * 0.28)
    fy = int(h * 0.70)
    a1 = circular_face(axin, fs, AXIN_BLUE, 5)
    a2 = circular_face(xiaolan, fs, XIAOLAN_PINK, 5)
    canvas.paste(a1, (int(w * 0.10), fy), a1)
    canvas.paste(a2, (int(w * 0.62), fy), a2)
    d = ImageDraw.Draw(canvas)
    d.text((int(w * 0.10) + fs // 2, fy + fs + 12), "阿信", fill=AXIN_BLUE, font=fnt(int(w * 0.06), True), anchor="mm")
    d.text((int(w * 0.62) + fs // 2, fy + fs + 12), "小蓝", fill=XIAOLAN_PINK, font=fnt(int(w * 0.06), True), anchor="mm")
    d.text((w // 2, h - 55), f"{PUB_DT.month}/{PUB_DT.day} {WEEKDAY_CN} 08:00", fill=(*hue, 255), font=fnt(int(w * 0.055), True), anchor="mm")
    return canvas


# ===================== AVATAR =====================
def build_avatar(axin, xiaolan, size=800, style="magazine"):
    if style == "split":
        half = size // 2
        left = fit_face(axin, half, size)
        right = fit_face(xiaolan, half, size)
        canvas = Image.new("RGB", (size, size), DARK)
        canvas.paste(left, (0, 0))
        canvas.paste(right, (half, 0))
        d = ImageDraw.Draw(canvas)
        d.rectangle([half - 4, 0, half + 4, size], fill=GOLD)
        return canvas
    if style == "neon":
        hue = week_hue()
        canvas = Image.new("RGB", (size, size), (6, 8, 16))
        canvas = add_glow(canvas, size // 2, size // 2, int(size * 0.55), hue, 115)
        d = ImageDraw.Draw(canvas)
        d.text((size // 2, size // 2 - 30), "TOP 15", font=fnt(int(size * 0.18), True), fill=(*hue, 255), anchor="mm")
        d.text((size // 2, size // 2 + 30), "本周大事", font=fnt(int(size * 0.10), True), fill=WHITE, anchor="mm")
        fs = int(size * 0.30)
        a1 = circular_face(axin, fs, AXIN_BLUE, 4)
        a2 = circular_face(xiaolan, fs, XIAOLAN_PINK, 4)
        fy = size - fs - 30
        canvas.paste(a1, (int(size * 0.10), fy), a1)
        canvas.paste(a2, (size - fs - int(size * 0.10), fy), a2)
        return canvas
    # magazine
    canvas = Image.new("RGB", (size, size), DARK_NAVY)
    canvas = add_glow(canvas, int(size * 0.25), int(size * 0.35), int(size * 0.6), AXIN_BLUE, 90)
    canvas = add_glow(canvas, int(size * 0.8), int(size * 0.85), int(size * 0.5), XIAOLAN_PINK, 80)
    fs = int(size * 0.42)
    a1 = circular_face(axin, fs, GOLD, 5)
    a2 = circular_face(xiaolan, fs, GOLD, 5)
    ay = (size - fs) // 2
    canvas.paste(a1, (int(size * 0.06), ay), a1)
    canvas.paste(a2, (size - fs - int(size * 0.06), ay), a2)
    d = ImageDraw.Draw(canvas)
    nf = fnt(int(size * 0.07), True)
    d.text((int(size * 0.06) + fs // 2, ay + fs + 25), "阿信", fill=AXIN_BLUE, font=nf, anchor="mm")
    d.text((size - fs - int(size * 0.06) + fs // 2, ay + fs + 25), "小蓝", fill=XIAOLAN_PINK, font=nf, anchor="mm")
    return canvas


def main():
    axin = Image.open(os.path.join(IMAGES_DIR, "anchor_axin.jpg"))
    xiaolan = Image.open(os.path.join(IMAGES_DIR, "anchor_xiaolan.jpg"))
    os.makedirs(OUT_DIR, exist_ok=True)
    covers = [
        ("16x9", 1920, 1080, "landscape"),
        ("4x3", 1440, 1080, "landscape"),
        ("3x4", 1080, 1440, "portrait"),
    ]
    sfx = f"_{SUFFIX}" if SUFFIX else ""
    for name, w, h, kind in covers:
        if STYLE == "split":
            img = build_split_landscape(w, h, axin, xiaolan) if kind == "landscape" else build_split_portrait(w, h, axin, xiaolan)
        elif STYLE == "magazine":
            img = build_magazine_landscape(w, h, axin, xiaolan) if kind == "landscape" else build_magazine_portrait(w, h, axin, xiaolan)
        else:
            img = build_neon_landscape(w, h, axin, xiaolan) if kind == "landscape" else build_neon_portrait(w, h, axin, xiaolan)
        out = os.path.join(OUT_DIR, f"cover_weekly_{PREP_DATE}{sfx}_{name}.png")
        img.save(out, quality=92)
        print(f"✅ {STYLE} {name} ({w}x{h}): {out}")
    avatar = build_avatar(axin, xiaolan, 800, STYLE)
    av = os.path.join(OUT_DIR, f"avatar_weekly_{PREP_DATE}{sfx}.png")
    avatar.save(av, quality=92)
    print(f"✅ {STYLE} avatar: {av}")


if __name__ == "__main__":
    main()
