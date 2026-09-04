#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Signal Pop 周末特别版 · 双人封面生成 v4

主持人脸（阿信/小蓝 = 信蓝组合）为固定人设跨期复用（项目规则）。
版式每期轮换，保证新鲜感。七种风格：
  - split     : 经典左右分屏 + 金色中带（原 v1/v2，兜底）
  - magazine  : 杂志头条风（双人左侧 + 大刊头 + 本期 TOP3 标题预告）
  - neon      : 巨型数字风（巨大"15" + 双人圆形头像 + 霓虹光晕色）
  - newspaper : 报纸头版风（米白纸纹 + 衬线大标题 + 黑白红三色）
  - popart    : 波普漫画风（高饱和撞色 + 半调网点 + 爆炸星框）
  - glitch    : 赛博故障风（RGB 错位 + 扫描线 + 数据网格）
  - variety   : 综艺大字报风（渐变底 + 爆炸贴纸 + 超大描边字）

轮换机制（2026-09-04）：
  STYLE=auto（默认）按制作日 md5 选风格，记录到 output/used_cover_styles.json，
  避开最近 2 期不重复；正式出品（无 SUFFIX）才写记录，预览不污染历史。
  每种风格内置多套配色，按日期哈希取，风格重复时配色也不同。
  TOP3 头条自动读取本期 parsed_news.json（缺失时回退内置占位）。

用法：python tools/gen_weekly_talk_cover.py [PREP_DATE] [STYLE] [SUFFIX]
  STYLE : auto | split | magazine | neon | newspaper | popart | glitch | variety
  SUFFIX: 可选，附加到文件名做风格预览；正式出品不传 SUFFIX（输出规范名）
"""
import os
import sys
import json
import hashlib
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps

PROJECT_ROOT = "E:/projects/signal_pop"
PREP_DATE = sys.argv[1] if len(sys.argv) > 1 else "20260821"
STYLE = sys.argv[2] if len(sys.argv) > 2 else "auto"
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

# ===================== 风格轮换机制（2026-09-04） =====================
COVER_STYLES = ["split", "magazine", "neon", "newspaper", "popart", "glitch", "variety"]
USED_COVER_FILE = os.path.join(PROJECT_ROOT, "output", "used_cover_styles.json")


def pick_style_auto(prep_date, record=True, avoid=2):
    """按日期哈希选风格，避开最近 avoid 期用过的；record=False 时只选不记（预览用）。"""
    try:
        with open(USED_COVER_FILE, encoding="utf-8") as f:
            rec = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        rec = {}
    recent = [rec[d] for d in sorted(rec.keys())[-avoid:]]
    h = int(hashlib.md5(prep_date.encode()).hexdigest(), 16)
    chosen = COVER_STYLES[h % len(COVER_STYLES)]
    if chosen in recent:
        for i in range(1, len(COVER_STYLES)):
            s = COVER_STYLES[(h + i) % len(COVER_STYLES)]
            if s not in recent:
                chosen = s
                break
    if record:
        rec[prep_date] = chosen
        os.makedirs(os.path.dirname(USED_COVER_FILE), exist_ok=True)
        with open(USED_COVER_FILE, "w", encoding="utf-8") as f:
            json.dump(rec, f, ensure_ascii=False, indent=2)
    return chosen


def date_pick(prep_date, pool):
    """按日期哈希从配色池取一套，风格偶有重复时配色也不同。"""
    h = int(hashlib.md5(("pal_" + prep_date).encode()).hexdigest(), 16)
    return pool[h % len(pool)]


# 各风格配色池（每套 = 主色/辅色/底色组合，视觉差异明显）
NEWSPAPER_PALS = [
    {"bg": (243, 237, 222), "ink": (28, 26, 22), "accent": (178, 34, 34), "grey": (120, 114, 100)},   # 米白+正红
    {"bg": (240, 234, 214), "ink": (30, 28, 24), "accent": (20, 70, 140), "grey": (118, 112, 98)},    # 象牙+藏蓝
    {"bg": (238, 228, 208), "ink": (40, 32, 24), "accent": (150, 80, 20), "grey": (130, 116, 96)},    # 旧纸+赭石
]
POPART_PALS = [
    {"a": (236, 64, 122), "b": (255, 213, 40), "c": (38, 198, 218), "ink": (24, 20, 26)},    # 粉/黄/青
    {"a": (255, 112, 40), "b": (255, 224, 70), "c": (90, 160, 255), "ink": (24, 20, 26)},    # 橙/黄/蓝
    {"a": (150, 80, 240), "b": (70, 220, 160), "c": (255, 150, 190), "ink": (24, 20, 26)},   # 紫/绿/粉
]
GLITCH_PALS = [
    {"hue": (0, 230, 230), "warn": (255, 60, 90)},    # 青/红
    {"hue": (120, 255, 120), "warn": (255, 140, 40)}, # 绿/橙
    {"hue": (200, 120, 255), "warn": (60, 220, 200)}, # 紫/薄荷
]
VARIETY_PALS = [
    {"top": (230, 40, 60), "bot": (255, 150, 30), "burst": (255, 220, 60), "tag": (30, 200, 190)},   # 红→橙
    {"top": (190, 40, 160), "bot": (90, 40, 220), "burst": (255, 210, 60), "tag": (40, 230, 220)},   # 品红→紫
    {"top": (20, 110, 230), "bot": (40, 200, 180), "burst": (255, 220, 70), "tag": (255, 120, 150)}, # 蓝→青绿
]


def load_top3():
    """从本期 parsed_news.json 取 3 条真实头条（突发优先），缺失时回退占位。"""
    fallback = [
        ("01", "本周要闻盘点", "信蓝组合陪你开聊"),
        ("02", "突发与焦点", "一报一评不啰嗦"),
        ("03", "下周看点前瞻", "评论区聊聊你的看法"),
    ]
    try:
        with open(os.path.join(OUT_DIR, "parsed_news.json"), encoding="utf-8") as f:
            news = json.load(f)

        def punch(t):
            for sep in ["，", ",", "：", ":", "！", "?", "？", "！", "、"]:
                if sep in t:
                    t = t.split(sep)[0]
            t = t.strip()[:14]
            # 去掉截断产生的悬空尾词 / 半个英文单词
            while t and t[-1].isascii() and t[-1].isalnum():
                t = t[:-1]
            for tail in ["先后", "宣布", "公布", "曝光", "回应", "称", "已", "将", "再", "了"]:
                if t.endswith(tail) and len(t) > len(tail) + 2:
                    t = t[: -len(tail)]
            return t

        items = []
        ordered = [n for n in news if n.get("type") == "breaking"] + \
                  [n for n in news if n.get("type") != "breaking"]
        for n in ordered:
            t = punch(n.get("title", ""))
            if len(t) >= 4:
                items.append((f"{len(items) + 1:02d}", t, n.get("section", "要闻")))
            if len(items) == 3:
                break
        if len(items) == 3:
            return items
    except (FileNotFoundError, json.JSONDecodeError, KeyError, TypeError):
        pass
    return fallback


def week_hue():
    h = int(hashlib.md5(PREP_DATE.encode()).hexdigest(), 16)
    return NEON_HUES[h % len(NEON_HUES)]


def fnt(size, bold=True):
    return ImageFont.truetype(FONT_BOLD if bold else FONT, size)


def fit(font, text, max_w):
    """超过 max_w 时截断并加省略号，防止白字溢出面板（4:3 尤其易溢出）。"""
    if font.getlength(text) <= max_w:
        return text
    t = text
    while t and font.getlength(t + "…") > max_w:
        t = t[:-1]
    return t + "…"


def fit_size(text, max_w, start_size, bold=True, min_size=12):
    """从 start_size 开始缩小字号，直到 text 宽度 <= max_w，返回 (font, actual_size)。"""
    size = start_size
    while size > min_size:
        font = fnt(size, bold)
        if font.getlength(text) <= max_w:
            return font, size
        size = int(size * 0.92)
    return fnt(min_size, bold), min_size


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


def draw_outline(d, pos, text, font, fill, outline=(20, 16, 6), w=4, anchor="mm"):
    x, y = pos
    for ox, oy in [(-w, 0), (w, 0), (0, -w), (0, w), (-w, -w), (w, w), (-w, w), (w, -w)]:
        d.text((x + ox, y + oy), text, fill=outline, font=font, anchor=anchor)
    d.text(pos, text, fill=fill, font=font, anchor=anchor)


def rounded_panel(canvas, box, radius=28, color=PANEL, alpha=235, border=None):
    ov = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    d.rounded_rectangle(box, radius=radius, fill=(*color, alpha))
    if border:
        d.rounded_rectangle(box, radius=radius, outline=(*border, 255), width=3)
    return Image.alpha_composite(canvas.convert("RGBA"), ov).convert("RGB")


# 本期 TOP3 头条（杂志风展示用，与新闻稿同步：取「本周之最」三条）
TOP3 = [
    ("01", "GPT-6正式发布", "OpenAI宣告AGI时代到来"),
    ("02", "英伟达129亿美元收购HF", "开源生态走向引关注"),
    ("03", "SHEIN六年三城赴港上市", "广州起家跨境天花板"),
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
    tt = "本\n周\n15\n条"
    lines = tt.split("\n")
    lh = tf.size + 4
    y0 = (h - lh * len(lines)) // 2
    for i, ln in enumerate(lines):
        y = y0 + i * lh
        for ox, oy in [(-2, 0), (2, 0), (0, -2), (0, 2)]:
            d.text((cx + ox, y + oy), ln, fill=(40, 30, 10), font=tf, anchor="mm")
        d.text((cx, y), ln, fill=GOLD_BRIGHT, font=tf, anchor="mm")
    d.text((w // 2, int(h * 0.04)), "隔天信号弹 · 周末特别版", fill=GOLD, font=fnt(int(w * 0.022), True), anchor="mm")
    d.text((w // 2, int(h * 0.075)), "信蓝组合 · 本周15条新闻闲聊", fill=LIGHT_GREY, font=fnt(int(w * 0.016)), anchor="mm")
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
    title = "本周15条"
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
    """杂志横版：左区=大标题+双人头像，右区=TOP3面板，严格避免任何重叠/溢出。"""
    margin = int(w * 0.045)
    canvas = vgrad(w, h, (14, 20, 38), (8, 12, 24))
    canvas = add_glow(canvas, int(w * 0.18), int(h * 0.30), int(h * 0.60), AXIN_BLUE, 90)
    canvas = add_glow(canvas, int(w * 0.90), int(h * 0.88), int(h * 0.50), XIAOLAN_PINK, 80)
    d = ImageDraw.Draw(canvas)

    # 顶部 kicker
    d.text((margin, int(h * 0.06)), "隔天信号弹 · 周末特别版", fill=GOLD, font=fnt(int(w * 0.021), True), anchor="lm")
    d.text((margin, int(h * 0.115)), "SIGNAL POP · WEEKEND SPECIAL", fill=LIGHT_GREY, font=fnt(int(w * 0.012), False), anchor="lm")

    # 右侧面板先算尺寸，确保不溢出
    panel_w = int(w * 0.42)
    px2 = w - margin
    px1 = px2 - panel_w
    py1 = int(h * 0.16)
    py2 = h - int(h * 0.18)

    # 左侧大标题区：宽度 = px1 左侧留出边距
    title_max_w = px1 - margin * 2
    title_font, _ = fit_size("本周15条", title_max_w, int(h * 0.18), bold=True)
    title_y = int(h * 0.38)
    draw_outline(d, (margin, title_y), "本周15条", title_font, GOLD_BRIGHT, outline=(20, 14, 4), w=max(4, int(w * 0.004)), anchor="lm")

    line_y = title_y + int(title_font.size * 1.1)
    d.line([(margin, line_y), (margin + int(title_max_w * 0.55), line_y)], fill=GOLD, width=3)

    sub_font, _ = fit_size("本周要闻 · 信蓝组合盘点", title_max_w, int(h * 0.045), bold=True)
    sub_y = line_y + int(h * 0.045)
    d.text((margin, sub_y), "本周要闻 · 信蓝组合盘点", fill=WHITE, font=sub_font, anchor="lm")

    # 底部双人头像（左下）
    fs = min(int(h * 0.19), int((px1 - margin * 2 - int(w * 0.02)) // 2))
    ay = h - int(h * 0.16)
    gap = int(w * 0.02)
    a1 = circular_face(axin, fs, GOLD, 6)
    a2 = circular_face(xiaolan, fs, GOLD, 6)
    canvas.paste(a1, (margin, ay - fs // 2), a1)
    canvas.paste(a2, (margin + fs + gap, ay - fs // 2), a2)
    d = ImageDraw.Draw(canvas)
    nf = fnt(int(w * 0.021), True)
    draw_outline(d, (margin + fs // 2, ay + fs // 2 + int(h * 0.025)), "阿信", nf, AXIN_BLUE, outline=(10, 20, 40), w=4)
    draw_outline(d, (margin + fs + gap + fs // 2, ay + fs // 2 + int(h * 0.025)), "小蓝", nf, XIAOLAN_PINK, outline=(30, 10, 20), w=4)

    # 右侧面板
    canvas = rounded_panel(canvas, (px1, py1, px2, py2), radius=int(w * 0.015), color=PANEL, alpha=230, border=GOLD)
    d = ImageDraw.Draw(canvas)
    d.text((px1 + int(w * 0.03), py1 + int(h * 0.04)), "本周之最", fill=GOLD_BRIGHT, font=fnt(int(w * 0.024), True), anchor="lm")
    d.text((px1 + int(w * 0.16), py1 + int(h * 0.048)), "TOP 3", fill=LIGHT_GREY, font=fnt(int(w * 0.017), False), anchor="lm")
    d.line([(px1 + int(w * 0.03), py1 + int(h * 0.095)), (px2 - int(w * 0.03), py1 + int(h * 0.095))], fill=(*GOLD, 160), width=2)

    ty = py1 + int(h * 0.20)
    step = (py2 - ty - int(h * 0.03)) // 3
    rb = px1 + int(w * 0.05)
    rr = int(w * 0.023)
    tx = rb + rr + int(w * 0.03)
    max_w = px2 - tx - int(w * 0.025)
    tf_title = fnt(int(w * 0.023), True)
    tf_sub = fnt(int(w * 0.014), False)
    for rank, title, sub in TOP3:
        d.ellipse([rb - rr, ty - rr, rb + rr, ty + rr], fill=(*GOLD, 255), outline=(40, 30, 10), width=3)
        d.text((rb, ty), rank, fill=(20, 14, 4), font=fnt(int(w * 0.026), True), anchor="mm")
        d.text((tx, ty - int(h * 0.026)), fit(tf_title, title, max_w), fill=WHITE, font=tf_title, anchor="lm")
        d.text((tx, ty + int(h * 0.024)), fit(tf_sub, sub, max_w), fill=LIGHT_GREY, font=tf_sub, anchor="lm")
        ty += step

    # 底部日期条
    d.rectangle([0, h - 4, w, h], fill=GOLD)
    d.text((w // 2, h - int(h * 0.045)), f"{PUB_DT.month}/{PUB_DT.day} {WEEKDAY_CN} 08:00 · 信蓝组合 · 每周相见", fill=GOLD, font=fnt(int(w * 0.02), True), anchor="mm")
    return canvas


def build_magazine_portrait(w, h, axin, xiaolan):
    """杂志竖版：上=标题 中=双人头像 下=TOP3 面板，rank 数字用足够大的圆避免变形。"""
    margin = int(w * 0.06)
    canvas = vgrad(w, h, (14, 20, 38), (8, 12, 24))
    canvas = add_glow(canvas, int(w * 0.18), int(h * 0.12), int(w * 0.6), AXIN_BLUE, 90)
    canvas = add_glow(canvas, int(w * 0.92), int(h * 0.92), int(w * 0.55), XIAOLAN_PINK, 80)
    d = ImageDraw.Draw(canvas)

    # 顶部 kicker
    d.text((w // 2, int(h * 0.045)), "隔天信号弹 · 周末特别版", fill=GOLD, font=fnt(int(w * 0.05), True), anchor="mm")

    # 大标题（居中，但字号自适应宽度）
    title_max_w = w - margin * 2
    title_font, _ = fit_size("本周15条", title_max_w, int(w * 0.13), bold=True)
    title_y = int(h * 0.11)
    draw_outline(d, (w // 2, title_y), "本周15条", title_font, GOLD_BRIGHT, outline=(20, 14, 4), w=7)

    line_y = title_y + int(title_font.size * 0.7)
    d.line([(int(w * 0.25), line_y), (int(w * 0.75), line_y)], fill=GOLD, width=3)

    sub_font, _ = fit_size("本周要闻 · 信蓝组合盘点", title_max_w, int(w * 0.046), bold=True)
    sub_y = line_y + int(h * 0.040)
    d.text((w // 2, sub_y), "本周要闻 · 信蓝组合盘点", fill=WHITE, font=sub_font, anchor="mm")

    # 中部双人头像
    fs = min(int(h * 0.18), int((w - margin * 2 - int(w * 0.06)) // 2))
    ay = int(h * 0.28)
    a1 = circular_face(axin, fs, GOLD, 6)
    a2 = circular_face(xiaolan, fs, GOLD, 6)
    left_x = margin
    right_x = w - margin - fs
    canvas.paste(a1, (left_x, ay), a1)
    canvas.paste(a2, (right_x, ay), a2)
    d = ImageDraw.Draw(canvas)
    nf = fnt(int(w * 0.06), True)
    draw_outline(d, (left_x + fs // 2, ay + fs + int(h * 0.03)), "阿信", nf, AXIN_BLUE, outline=(10, 20, 40), w=4)
    draw_outline(d, (right_x + fs // 2, ay + fs + int(h * 0.03)), "小蓝", nf, XIAOLAN_PINK, outline=(30, 10, 20), w=4)

    # 底部 TOP3 面板
    py1 = int(h * 0.53)
    px1, px2 = int(w * 0.05), w - int(w * 0.05)
    py2 = h - int(h * 0.13)
    canvas = rounded_panel(canvas, (px1, py1, px2, py2), radius=int(w * 0.02), color=PANEL, alpha=230, border=GOLD)
    d = ImageDraw.Draw(canvas)
    d.text((px1 + int(w * 0.04), py1 + int(h * 0.03)), "本周之最 TOP 3", fill=GOLD_BRIGHT, font=fnt(int(w * 0.042), True), anchor="lm")
    d.line([(px1 + int(w * 0.04), py1 + int(h * 0.065)), (px2 - int(w * 0.04), py1 + int(h * 0.065))], fill=(*GOLD, 160), width=2)

    ty = py1 + int(h * 0.10)
    rb = px1 + int(w * 0.07)
    rr = int(w * 0.028)
    tx = rb + rr + int(w * 0.045)
    max_w = px2 - tx - int(w * 0.04)
    min_step = int(h * 0.060)
    step = max((py2 - ty - int(h * 0.02)) // 3, min_step)
    tf_title = fnt(int(w * 0.038), True)
    tf_sub = fnt(int(w * 0.024), False)
    rank_font = fnt(int(w * 0.032), True)
    for rank, title, sub in TOP3:
        d.ellipse([rb - rr, ty - rr, rb + rr, ty + rr], fill=(*GOLD, 255), outline=(40, 30, 10), width=3)
        d.text((rb, ty), rank, fill=(20, 14, 4), font=rank_font, anchor="mm")
        d.text((tx, ty - int(h * 0.018)), fit(tf_title, title, max_w), fill=WHITE, font=tf_title, anchor="lm")
        d.text((tx, ty + int(h * 0.024)), fit(tf_sub, sub, max_w), fill=LIGHT_GREY, font=tf_sub, anchor="lm")
        ty += step

    # 底部日期条
    d.rectangle([0, h - 5, w, h], fill=GOLD)
    d.text((w // 2, h - int(h * 0.045)), f"{PUB_DT.month}/{PUB_DT.day} {WEEKDAY_CN} 08:00 · 信蓝组合", fill=GOLD, font=fnt(int(w * 0.055), True), anchor="mm")
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
    d.text((cx, cy - int(h * 0.26)), "本 周", fill=(*hue, 255), font=fnt(int(h * 0.09), True), anchor="mm")
    d.text((cx, cy + int(h * 0.22)), "本周 15 条 · 一报一评", fill=WHITE, font=fnt(int(h * 0.05), True), anchor="mm")
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
    d.text((cx, cy + int(h * 0.16)), "本周 15 条", fill=WHITE, font=fnt(int(w * 0.07), True), anchor="mm")
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


# ===================== 共享绘制辅助（新风格用） =====================
def serif_fnt(size):
    """衬线字体（报纸风用），找不到就用微软雅黑粗体兜底。"""
    for p in ("C:/Windows/Fonts/simsun.ttc", "C:/Windows/Fonts/STSONG.TTF", "C:/Windows/Fonts/msyhbd.ttc"):
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except OSError:
                pass
    return fnt(size, True)


def add_noise(canvas, strength=14, density=0.02, seed=42):
    """细颗粒纸纹噪点。"""
    import random as _r
    rng = _r.Random(seed)
    ov = canvas.convert("RGBA")
    d = ImageDraw.Draw(ov)
    w, h = canvas.size
    for _ in range(int(w * h * density)):
        x, y = rng.randrange(w), rng.randrange(h)
        g = rng.randint(0, 70)
        d.point((x, y), fill=(g, g, g, strength))
    return ov.convert("RGB")


def halftone(canvas, box, color, step=14, rmax=5, alpha=80):
    """半调网点，点径沿 x 方向渐变（波普风）。"""
    ov = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    x1, y1, x2, y2 = box
    w = max(1, x2 - x1)
    y, row = y1, 0
    while y < y2:
        x = x1 + (step // 2 if row % 2 else 0)
        while x < x2:
            t = (x - x1) / w
            r = max(1, int(rmax * (1 - t * 0.8)))
            d.ellipse([x - r, y - r, x + r, y + r], fill=(*color, alpha))
            x += step
        y += step
        row += 1
    return Image.alpha_composite(canvas.convert("RGBA"), ov).convert("RGB")


def starburst(canvas, cx, cy, r_out, r_in, points, color, alpha=255):
    """爆炸星形多边形（波普/综艺风）。"""
    import math
    ov = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    pts = []
    for i in range(points * 2):
        ang = math.pi * i / points - math.pi / 2
        r = r_out if i % 2 == 0 else r_in
        pts.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
    d.polygon(pts, fill=(*color, alpha))
    return Image.alpha_composite(canvas.convert("RGBA"), ov).convert("RGB")


def scanlines(canvas, gap=4, alpha=28):
    ov = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    w, h = canvas.size
    for y in range(0, h, gap):
        d.line([(0, y), (w, y)], fill=(0, 0, 0, alpha))
    return Image.alpha_composite(canvas.convert("RGBA"), ov).convert("RGB")


def paste_rotated(canvas, layer, center, angle):
    rot = layer.rotate(angle, expand=True, resample=Image.BICUBIC)
    canvas.paste(rot, (center[0] - rot.width // 2, center[1] - rot.height // 2), rot)
    return canvas


def make_sticker(canvas, box, text, sub, bg_color, ink, angle=4, radius=18):
    """贴纸卡片：白底黑边圆角矩形 + 标题/副题，轻微旋转。"""
    x1, y1, x2, y2 = box
    pw, ph = x2 - x1, y2 - y1
    card = Image.new("RGBA", (pw, ph), (0, 0, 0, 0))
    cd = ImageDraw.Draw(card)
    cd.rounded_rectangle([0, 0, pw - 1, ph - 1], radius=radius, fill=(*bg_color, 245), outline=(*ink, 255), width=4)
    tf, _ = fit_size(text, pw - 44, int(ph * 0.30), bold=True, min_size=12)
    cd.text((pw // 2, int(ph * 0.36)), text, fill=(*ink, 255), font=tf, anchor="mm")
    subf, _ = fit_size(sub, pw - 44, int(ph * 0.17), bold=False, min_size=10)
    cd.text((pw // 2, int(ph * 0.68)), sub, fill=(110, 105, 95, 255), font=subf, anchor="mm")
    return paste_rotated(canvas, card, ((x1 + x2) // 2, (y1 + y2) // 2), angle)


def rgb_split_text(canvas, pos, text, font, base, hue, warn, split_dx):
    """赛博故障：红/青错位 + 白色主体。"""
    d = ImageDraw.Draw(canvas)
    x, y = pos
    d.text((x - split_dx, y), text, fill=(*warn, 255), font=font, anchor="mm")
    d.text((x + split_dx, y), text, fill=(*hue, 255), font=font, anchor="mm")
    d.text((x, y), text, fill=(*base, 255), font=font, anchor="mm")


def glitch_shift(canvas, prep_date, n=6, y1r=0.12, y2r=0.92, skip=None):
    """随机横带水平错位，模拟信号故障。skip=(a,b) 为保护带（比例），错位条不落在标题上。"""
    import random as _r
    w, h = canvas.size
    rng = _r.Random(int(hashlib.md5(prep_date.encode()).hexdigest()[:8], 16))
    placed = 0
    tries = 0
    while placed < n and tries < n * 8:
        tries += 1
        y = rng.randint(int(h * y1r), int(h * y2r))
        if skip and skip[0] * h <= y <= skip[1] * h:
            continue
        bh = rng.randint(6, 30)
        shift = rng.randint(-46, 46)
        strip = canvas.crop((0, y, w, y + bh))
        canvas.paste(strip, (shift, y))
        placed += 1
    return canvas


# ===================== NEWSPAPER（报纸头版风） =====================
def build_newspaper_landscape(w, h, axin, xiaolan):
    pal = date_pick(PREP_DATE, NEWSPAPER_PALS)
    canvas = add_noise(Image.new("RGB", (w, h), pal["bg"]))
    d = ImageDraw.Draw(canvas)
    m = int(w * 0.030)
    d.rectangle([m, m, w - m, h - m], outline=pal["ink"], width=max(4, int(w * 0.0035)))
    d.rectangle([m + 10, m + 10, w - m - 10, h - m - 10], outline=pal["ink"], width=2)

    # 刊头
    head_y = m + int(h * 0.07)
    d.text((w // 2, head_y), "隔天信号弹", fill=pal["ink"], font=serif_fnt(int(w * 0.055)), anchor="mm")
    df = serif_fnt(int(w * 0.014))
    d.text((m + int(w * 0.035), head_y), f"{PUB_DATE_SHORT} {WEEKDAY_CN}", fill=pal["ink"], font=df, anchor="lm")
    d.text((w - m - int(w * 0.035), head_y), "周末特刊 · 信蓝组合", fill=pal["ink"], font=df, anchor="rm")
    ry = head_y + int(h * 0.052)
    d.line([(m + 12, ry), (w - m - 12, ry)], fill=pal["ink"], width=max(4, int(w * 0.0038)))

    # 左侧大标题（"15"用强调色）
    tx = m + int(w * 0.045)
    hy = ry + int(h * 0.19)
    b1f, b2f = serif_fnt(int(h * 0.175)), serif_fnt(int(h * 0.175))
    w1 = b1f.getlength("本周")
    d.text((tx, hy), "本周", fill=pal["ink"], font=b1f, anchor="lm")
    d.text((tx + w1, hy), "15条", fill=pal["accent"], font=b2f, anchor="lm")
    d.line([(tx, hy + int(h * 0.115)), (tx + int(w * 0.40), hy + int(h * 0.115))], fill=pal["ink"], width=3)
    d.text((tx, hy + int(h * 0.155)), "要闻速览 · 一报一评", fill=pal["grey"], font=serif_fnt(int(w * 0.018)), anchor="lm")
    # 伪导语横线（报纸排版感）
    for i in range(3):
        ly = hy + int(h * 0.21) + i * int(h * 0.028)
        d.line([(tx, ly), (tx + int(w * (0.36 if i < 2 else 0.22)), ly)], fill=(*pal["grey"], ), width=2)

    # 左下双人圆形头像（粗黑环，center 定位避免出画）
    fs = int(h * 0.19)
    fy = h - int(h * 0.19)  # 圆心 y
    a1 = circular_face(axin, fs, pal["ink"], int(w * 0.004))
    a2 = circular_face(xiaolan, fs, pal["ink"], int(w * 0.004))
    canvas.paste(a1, (tx, fy - fs // 2), a1)
    canvas.paste(a2, (tx + fs + int(w * 0.015), fy - fs // 2), a2)
    d = ImageDraw.Draw(canvas)
    nf = serif_fnt(int(w * 0.017))
    d.text((tx + fs // 2, fy + fs // 2 + int(h * 0.022)), "阿信", fill=pal["ink"], font=nf, anchor="mm")
    d.text((tx + fs + int(w * 0.015) + fs // 2, fy + fs // 2 + int(h * 0.022)), "小蓝", fill=pal["ink"], font=nf, anchor="mm")

    # 右栏 TOP3（报纸条目式）
    cx1 = tx + int(w * 0.47)
    cx2 = w - m - int(w * 0.04)
    d.line([(cx1, ry + int(h * 0.06)), (cx1, h - m - int(h * 0.06))], fill=pal["ink"], width=2)
    ty = ry + int(h * 0.11)
    d.text((cx1 + int(w * 0.02), ty), "本期头条", fill=pal["accent"], font=serif_fnt(int(w * 0.022)), anchor="lm")
    d.line([(cx1 + int(w * 0.02), ty + int(h * 0.045)), (cx2, ty + int(h * 0.045))], fill=pal["ink"], width=2)
    ty += int(h * 0.085)
    step = int(h * 0.185)
    tf_title = serif_fnt(int(w * 0.021))
    tf_sub = serif_fnt(int(w * 0.013))
    for rank, title, sub in TOP3:
        d.rectangle([cx1 + int(w * 0.02), ty - 6, cx1 + int(w * 0.02) + 12, ty + 6], fill=pal["ink"])
        d.text((cx1 + int(w * 0.045), ty - int(h * 0.022)), fit(tf_title, title, cx2 - cx1 - int(w * 0.09)), fill=pal["ink"], font=tf_title, anchor="lm")
        d.text((cx1 + int(w * 0.045), ty + int(h * 0.020)), fit(tf_sub, f"{sub} · 详见内页", cx2 - cx1 - int(w * 0.09)), fill=pal["grey"], font=tf_sub, anchor="lm")
        ty += step

    # 底部黑条
    d.rectangle([m + 10, h - m - int(h * 0.055), w - m - 10, h - m - 10], fill=pal["ink"])
    d.text((w // 2, h - m - int(h * 0.028)), f"{PUB_DT.month}/{PUB_DT.day} {WEEKDAY_CN} 08:00 准时开聊", fill=pal["bg"], font=serif_fnt(int(w * 0.018)), anchor="mm")
    return canvas


def build_newspaper_portrait(w, h, axin, xiaolan):
    pal = date_pick(PREP_DATE, NEWSPAPER_PALS)
    canvas = add_noise(Image.new("RGB", (w, h), pal["bg"]))
    d = ImageDraw.Draw(canvas)
    m = int(w * 0.035)
    d.rectangle([m, m, w - m, h - m], outline=pal["ink"], width=max(3, int(w * 0.004)))
    d.rectangle([m + 8, m + 8, w - m - 8, h - m - 8], outline=pal["ink"], width=2)

    head_y = m + int(h * 0.045)
    d.text((w // 2, head_y), "隔天信号弹", fill=pal["ink"], font=serif_fnt(int(w * 0.085)), anchor="mm")
    df = serif_fnt(int(w * 0.024))
    d.text((w // 2, head_y + int(h * 0.045)), f"{PUB_DATE_SHORT} {WEEKDAY_CN} · 周末特刊", fill=pal["grey"], font=df, anchor="mm")
    ry = head_y + int(h * 0.075)
    d.line([(m + 10, ry), (w - m - 10, ry)], fill=pal["ink"], width=max(3, int(w * 0.005)))

    # 大标题
    hy = ry + int(h * 0.10)
    b1f, b2f = serif_fnt(int(w * 0.15)), serif_fnt(int(w * 0.15))
    w1 = b1f.getlength("本周")
    total = w1 + b2f.getlength("15条")
    x0 = w // 2 - int(total / 2)
    d.text((x0, hy), "本周", fill=pal["ink"], font=b1f, anchor="lm")
    d.text((x0 + w1, hy), "15条", fill=pal["accent"], font=b2f, anchor="lm")

    # 双人头像
    fs = int(w * 0.26)
    fy = hy + int(h * 0.075)
    a1 = circular_face(axin, fs, pal["ink"], int(w * 0.005))
    a2 = circular_face(xiaolan, fs, pal["ink"], int(w * 0.005))
    gap = int(w * 0.06)
    x1 = w // 2 - fs - gap // 2
    x2 = w // 2 + gap // 2
    canvas.paste(a1, (x1, fy), a1)
    canvas.paste(a2, (x2, fy), a2)
    d = ImageDraw.Draw(canvas)
    nf = serif_fnt(int(w * 0.030))
    d.text((x1 + fs // 2, fy + fs + int(h * 0.022)), "阿信", fill=pal["ink"], font=nf, anchor="mm")
    d.text((x2 + fs // 2, fy + fs + int(h * 0.022)), "小蓝", fill=pal["ink"], font=nf, anchor="mm")

    # 底部头条条目
    ty = fy + fs + int(h * 0.065)
    d.line([(m + 10, ty), (w - m - 10, ty)], fill=pal["ink"], width=2)
    d.text((w // 2, ty + int(h * 0.022)), "本期头条", fill=pal["accent"], font=serif_fnt(int(w * 0.035)), anchor="mm")
    ty += int(h * 0.055)
    tf_title = serif_fnt(int(w * 0.036))
    tf_sub = serif_fnt(int(w * 0.022))
    step = int(h * 0.062)
    for rank, title, sub in TOP3:
        d.rectangle([w // 2 - int(w * 0.38), ty - 4, w // 2 - int(w * 0.38) + 10, ty + 6], fill=pal["ink"])
        d.text((w // 2 - int(w * 0.34), ty), fit(tf_title, title, int(w * 0.62)), fill=pal["ink"], font=tf_title, anchor="lm")
        d.text((w // 2 - int(w * 0.34), ty + int(h * 0.024)), fit(tf_sub, sub, int(w * 0.62)), fill=pal["grey"], font=tf_sub, anchor="lm")
        ty += step

    d.rectangle([m + 8, h - m - int(h * 0.05), w - m - 8, h - m - 8], fill=pal["ink"])
    d.text((w // 2, h - m - int(h * 0.025)), f"{PUB_DT.month}/{PUB_DT.day} {WEEKDAY_CN} 08:00", fill=pal["bg"], font=serif_fnt(int(w * 0.030)), anchor="mm")
    return canvas


# ===================== POPART（波普漫画风） =====================
def build_popart_landscape(w, h, axin, xiaolan):
    pal = date_pick(PREP_DATE, POPART_PALS)
    # 三色对角分割
    canvas = Image.new("RGB", (w, h), pal["a"])
    od = ImageDraw.Draw(canvas)
    od.polygon([(int(w * 0.52), 0), (w, 0), (w, h), (int(w * 0.22), h)], fill=pal["b"])
    od.polygon([(int(w * 0.76), 0), (w, 0), (w, h), (int(w * 0.46), h)], fill=pal["c"])
    canvas = halftone(canvas, (int(w * 0.45), 0, w, h), pal["ink"], step=int(w * 0.018), rmax=int(w * 0.0055))

    # 左上爆炸星 + 大标题
    bx, by = int(w * 0.30), int(h * 0.34)
    canvas = starburst(canvas, bx, by, int(h * 0.40), int(h * 0.27), 12, pal["b"], 255)
    d = ImageDraw.Draw(canvas)
    tf = fnt(int(h * 0.145), True)
    draw_outline(d, (bx, by), "本周15条", tf, (255, 255, 255), outline=pal["ink"], w=max(6, int(h * 0.014)))

    # 漫画对话气泡
    bub_w, bub_h = int(w * 0.20), int(h * 0.14)
    bxx, byy = int(w * 0.60), int(h * 0.16)
    d.rounded_rectangle([bxx, byy, bxx + bub_w, byy + bub_h], radius=24, fill=(255, 255, 255), outline=pal["ink"], width=5)
    d.polygon([(bxx + 30, byy + bub_h - 6), (bxx + 90, byy + bub_h + 34), (bxx + 110, byy + bub_h - 6)], fill=(255, 255, 255), outline=pal["ink"])
    d.polygon([(bxx + 34, byy + bub_h - 8), (bxx + 94, byy + bub_h + 28), (bxx + 106, byy + bub_h - 8)], fill=(255, 255, 255))
    d.text((bxx + bub_w // 2, byy + bub_h // 2), "开聊！", fill=pal["ink"], font=fnt(int(h * 0.075), True), anchor="mm")

    # 左下双人头像（粗黑环 + 漫画名牌）
    fs = int(h * 0.21)
    fy = h - fs - int(h * 0.115)  # 头像顶边，留出名牌空间
    a1 = circular_face(axin, fs, pal["ink"], int(w * 0.0045))
    a2 = circular_face(xiaolan, fs, pal["ink"], int(w * 0.0045))
    canvas.paste(a1, (int(w * 0.05), fy), a1)
    canvas.paste(a2, (int(w * 0.05) + fs + int(w * 0.02), fy), a2)
    d = ImageDraw.Draw(canvas)
    nf = fnt(int(w * 0.020), True)
    for px, name, col in [(int(w * 0.05) + fs // 2, "阿信", (255, 255, 255)), (int(w * 0.05) + fs + int(w * 0.02) + fs // 2, "小蓝", (255, 255, 255))]:
        bw = int(w * 0.055)
        d.rounded_rectangle([px - bw // 2, fy + fs + 6, px + bw // 2, fy + fs + 6 + int(h * 0.052)], radius=14, fill=col, outline=pal["ink"], width=3)
        d.text((px, fy + fs + 6 + int(h * 0.026)), name, fill=pal["ink"], font=nf, anchor="mm")

    # 右下 TOP3 贴纸卡（三张轻微旋转）
    cw, chh = int(w * 0.24), int(h * 0.155)
    xs = w - cw - int(w * 0.055)
    for i, (rank, title, sub) in enumerate(TOP3):
        y = h - chh * 3 - int(h * 0.05) + i * (chh + int(h * 0.015))
        card = make_sticker(canvas, (xs, y, xs + cw, y + chh), f"{rank} {title}", sub, (255, 255, 255), pal["ink"], angle=(-4 if i % 2 else 3))
    d = ImageDraw.Draw(canvas)
    d.text((xs + cw // 2, h - chh * 3 - int(h * 0.075)), "本周之最", fill=(255, 255, 255), font=fnt(int(w * 0.018), True), anchor="mm",
           stroke_width=3, stroke_fill=pal["ink"])
    return canvas


def build_popart_portrait(w, h, axin, xiaolan):
    pal = date_pick(PREP_DATE, POPART_PALS)
    canvas = Image.new("RGB", (w, h), pal["b"])
    od = ImageDraw.Draw(canvas)
    od.polygon([(0, 0), (w, 0), (w, int(h * 0.34)), (0, int(h * 0.46))], fill=pal["a"])
    od.polygon([(0, int(h * 0.78)), (w, int(h * 0.70)), (w, h), (0, h)], fill=pal["c"])
    canvas = halftone(canvas, (0, int(h * 0.30), w, int(h * 0.50)), pal["ink"], step=int(w * 0.030), rmax=int(w * 0.009))

    bx, by = w // 2, int(h * 0.20)
    canvas = starburst(canvas, bx, by, int(w * 0.46), int(w * 0.31), 12, pal["b"], 255)
    d = ImageDraw.Draw(canvas)
    tf = fnt(int(w * 0.115), True)
    draw_outline(d, (bx, by), "本周15条", tf, (255, 255, 255), outline=pal["ink"], w=max(5, int(w * 0.016)))

    fs = int(w * 0.28)
    fy = int(h * 0.38)
    a1 = circular_face(axin, fs, pal["ink"], int(w * 0.006))
    a2 = circular_face(xiaolan, fs, pal["ink"], int(w * 0.006))
    gap = int(w * 0.07)
    canvas.paste(a1, (int(w * 0.08), fy), a1)
    canvas.paste(a2, (w - int(w * 0.08) - fs, fy), a2)
    d = ImageDraw.Draw(canvas)
    nf = fnt(int(w * 0.045), True)
    for px, name in [(int(w * 0.08) + fs // 2, "阿信"), (w - int(w * 0.08) - fs // 2, "小蓝")]:
        bw = int(w * 0.16)
        d.rounded_rectangle([px - bw // 2, fy + fs + 8, px + bw // 2, fy + fs + 8 + int(h * 0.045)], radius=16, fill=(255, 255, 255), outline=pal["ink"], width=4)
        d.text((px, fy + fs + 8 + int(h * 0.0225)), name, fill=pal["ink"], font=nf, anchor="mm")

    cw, chh = int(w * 0.62), int(h * 0.072)
    xs = w // 2 - cw // 2
    ys = int(h * 0.70)
    for i, (rank, title, sub) in enumerate(TOP3):
        make_sticker(canvas, (xs, ys + i * (chh + int(h * 0.010)), xs + cw, ys + i * (chh + int(h * 0.010)) + chh),
                     f"{rank} {title}", sub, (255, 255, 255), pal["ink"], angle=(-3 if i % 2 else 3), radius=14)
    d = ImageDraw.Draw(canvas)
    d.text((w // 2, h - int(h * 0.035)), f"{PUB_DT.month}/{PUB_DT.day} {WEEKDAY_CN} 08:00", fill=(255, 255, 255), font=fnt(int(w * 0.040), True), anchor="mm",
           stroke_width=4, stroke_fill=pal["ink"])
    return canvas


# ===================== GLITCH（赛博故障风） =====================
def build_glitch_landscape(w, h, axin, xiaolan):
    pal = date_pick(PREP_DATE, GLITCH_PALS)
    canvas = vgrad(w, h, (7, 7, 12), (15, 13, 26))
    d = ImageDraw.Draw(canvas)
    for x in range(0, w, 72):
        d.line([(x, 0), (x, h)], fill=(26, 26, 40))
    for y in range(0, h, 72):
        d.line([(0, y), (w, y)], fill=(26, 26, 40))

    # 幽灵巨型数字
    big = fnt(int(h * 0.42), True)
    d.text((w - int(w * 0.26), int(h * 0.42)), "15", fill=(32, 30, 52), font=big, anchor="mm")

    cx, cy = w // 2, int(h * 0.34)
    d.text((cx, cy - int(h * 0.155)), "本 周", fill=(*pal["hue"], 255), font=fnt(int(h * 0.065), True), anchor="mm")
    rgb_split_text(canvas, (cx, cy), "本周15条", fnt(int(h * 0.135), True), (250, 250, 255), pal["hue"], pal["warn"], int(w * 0.006))
    d = ImageDraw.Draw(canvas)
    d.text((cx, cy + int(h * 0.115)), "SIGNAL // POP // WEEKEND", fill=(140, 140, 170), font=fnt(int(w * 0.014)), anchor="mm")

    # 故障错位条（避开标题带）+ 扫描线
    canvas = glitch_shift(canvas, PREP_DATE, skip=(0.13, 0.48))
    canvas = scanlines(canvas)

    # 双人方形头像框（色环）
    d = ImageDraw.Draw(canvas)
    fs = int(h * 0.21)
    fy = h - fs - int(h * 0.12)
    a1 = circular_face(axin, fs, pal["hue"], 5)
    a2 = circular_face(xiaolan, fs, pal["warn"], 5)
    canvas.paste(a1, (int(w * 0.06), fy), a1)
    canvas.paste(a2, (int(w * 0.06) + fs + int(w * 0.02), fy), a2)
    d.text((int(w * 0.06) + fs // 2, fy + fs + int(h * 0.032)), "AXIN", fill=(*pal["hue"], 255), font=fnt(int(w * 0.015), True), anchor="mm")
    d.text((int(w * 0.06) + fs + int(w * 0.02) + fs // 2, fy + fs + int(h * 0.032)), "XIAOLAN", fill=(*pal["warn"], 255), font=fnt(int(w * 0.015), True), anchor="mm")

    # 右下数据式 TOP3
    lx = int(w * 0.42)
    ty = fy + int(h * 0.01)
    tf_t = fnt(int(w * 0.017), True)
    tf_s = fnt(int(w * 0.012))
    for rank, title, sub in TOP3:
        d.rectangle([lx, ty - 4, lx + 14, ty + 10], fill=(*pal["hue"], 255))
        d.text((lx + int(w * 0.020), ty), f"[{rank}] {fit(tf_t, title, int(w * 0.36))}", fill=(235, 235, 245), font=tf_t, anchor="lm")
        d.text((lx + int(w * 0.020), ty + int(h * 0.030)), f">> {fit(tf_s, sub, int(w * 0.34))}", fill=(120, 120, 150), font=tf_s, anchor="lm")
        ty += int(h * 0.085)
    d.text((w // 2, h - int(h * 0.045)), f"{PUB_DT.month}/{PUB_DT.day} {WEEKDAY_CN} 08:00", fill=(*pal["hue"], 255), font=fnt(int(w * 0.018), True), anchor="mm")
    return canvas


def build_glitch_portrait(w, h, axin, xiaolan):
    pal = date_pick(PREP_DATE, GLITCH_PALS)
    canvas = vgrad(w, h, (7, 7, 12), (15, 13, 26))
    d = ImageDraw.Draw(canvas)
    for y in range(0, h, 72):
        d.line([(0, y), (w, y)], fill=(26, 26, 40))
    d.text((w // 2, int(h * 0.045)), "隔天信号弹 · 信蓝组合", fill=(150, 150, 175), font=fnt(int(w * 0.038), True), anchor="mm")

    cx, cy = w // 2, int(h * 0.17)
    rgb_split_text(canvas, (cx, cy), "本周15条", fnt(int(w * 0.115), True), (250, 250, 255), pal["hue"], pal["warn"], int(w * 0.007))
    d = ImageDraw.Draw(canvas)

    fs = int(w * 0.27)
    fy = int(h * 0.30)
    a1 = circular_face(axin, fs, pal["hue"], 5)
    a2 = circular_face(xiaolan, fs, pal["warn"], 5)
    gap = int(w * 0.08)
    canvas.paste(a1, (w // 2 - fs - gap // 2, fy), a1)
    canvas.paste(a2, (w // 2 + gap // 2, fy), a2)

    canvas = glitch_shift(canvas, PREP_DATE, skip=(0.11, 0.25))
    canvas = scanlines(canvas)
    d = ImageDraw.Draw(canvas)

    ty = fy + fs + int(h * 0.045)
    tf_t = fnt(int(w * 0.032), True)
    tf_s = fnt(int(w * 0.022))
    for rank, title, sub in TOP3:
        d.rectangle([int(w * 0.08), ty - 4, int(w * 0.08) + 16, ty + 12], fill=(*pal["hue"], 255))
        d.text((int(w * 0.12), ty), f"[{rank}] {fit(tf_t, title, int(w * 0.72))}", fill=(235, 235, 245), font=tf_t, anchor="lm")
        d.text((int(w * 0.12), ty + int(h * 0.026)), f">> {fit(tf_s, sub, int(w * 0.70))}", fill=(120, 120, 150), font=tf_s, anchor="lm")
        ty += int(h * 0.075)
    d.text((w // 2, h - int(h * 0.045)), f"{PUB_DT.month}/{PUB_DT.day} {WEEKDAY_CN} 08:00", fill=(*pal["hue"], 255), font=fnt(int(w * 0.042), True), anchor="mm")
    return canvas


# ===================== VARIETY（综艺大字报风） =====================
def build_variety_landscape(w, h, axin, xiaolan):
    pal = date_pick(PREP_DATE, VARIETY_PALS)
    canvas = vgrad(w, h, pal["top"], pal["bot"])
    # 中央大爆炸星
    bx, by = w // 2, int(h * 0.40)
    canvas = starburst(canvas, bx, by, int(h * 0.46), int(h * 0.335), 14, pal["burst"], 255)
    d = ImageDraw.Draw(canvas)

    tf = fnt(int(h * 0.175), True)
    draw_outline(d, (bx, by), "本周15条", tf, (255, 255, 255), outline=(24, 18, 10), w=max(8, int(h * 0.016)))
    d.text((bx, by + int(h * 0.145)), "信蓝组合 · 周末开聊", fill=(255, 255, 255), font=fnt(int(h * 0.048), True), anchor="mm",
           stroke_width=4, stroke_fill=(24, 18, 10))

    # 左上/右上旋转贴纸标签
    for center, text, col, ang in [(int(w * 0.11), "周末特供", pal["tag"], -8),
                                   (w - int(w * 0.11), "每周相见", (255, 255, 255), 7)]:
        cy_st = int(h * 0.13)
        layer = Image.new("RGBA", (int(w * 0.22), int(h * 0.11)), (0, 0, 0, 0))
        ld = ImageDraw.Draw(layer)
        ld.rounded_rectangle([6, 6, layer.width - 6, layer.height - 6], radius=20, fill=(*col, 255), outline=(24, 18, 10, 255), width=4)
        ld.text((layer.width // 2, layer.height // 2), text, fill=(24, 18, 10), font=fnt(int(h * 0.048), True), anchor="mm")
        canvas = paste_rotated(canvas, layer, (center, cy_st), ang)
    d = ImageDraw.Draw(canvas)

    # 底部双人头像（白粗环 + 名牌）
    fs = int(h * 0.215)
    fy = h - fs - int(h * 0.10)
    a1 = circular_face(axin, fs, (255, 255, 255), int(w * 0.004))
    a2 = circular_face(xiaolan, fs, (255, 255, 255), int(w * 0.004))
    canvas.paste(a1, (int(w * 0.07), fy), a1)
    canvas.paste(a2, (w - int(w * 0.07) - fs, fy), a2)
    d = ImageDraw.Draw(canvas)
    nf = fnt(int(w * 0.019), True)
    for px, name in [(int(w * 0.07) + fs // 2, "阿信"), (w - int(w * 0.07) - fs // 2, "小蓝")]:
        bw = int(w * 0.052)
        d.rounded_rectangle([px - bw // 2, fy + fs + 8, px + bw // 2, fy + fs + 8 + int(h * 0.05)], radius=12, fill=(255, 255, 255), outline=(24, 18, 10), width=3)
        d.text((px, fy + fs + 8 + int(h * 0.025)), name, fill=(24, 18, 10), font=nf, anchor="mm")

    # 右下 TOP3 白色胶囊
    px1 = int(w * 0.30)
    px2 = w - int(w * 0.28)
    ty = fy + int(h * 0.015)
    d = ImageDraw.Draw(canvas, "RGBA")
    tf_t = fnt(int(w * 0.016), True)
    tf_s = fnt(int(w * 0.012))
    for rank, title, sub in TOP3:
        d.rounded_rectangle([px1, ty, px2, ty + int(h * 0.062)], radius=int(h * 0.031), fill=(255, 255, 255, 240), outline=(24, 18, 10), width=3)
        d.text((px1 + int(w * 0.012), ty + int(h * 0.016)), f"{rank}", fill=pal["top"], font=fnt(int(w * 0.018), True), anchor="lm")
        d.text((px1 + int(w * 0.038), ty + int(h * 0.017)), fit(tf_t, title, (px2 - px1) - int(w * 0.06)), fill=(24, 18, 10), font=tf_t, anchor="lm")
        d.text((px1 + int(w * 0.038), ty + int(h * 0.041)), fit(tf_s, sub, (px2 - px1) - int(w * 0.06)), fill=(110, 100, 90), font=tf_s, anchor="lm")
        ty += int(h * 0.075)
    d.text((w // 2, h - int(h * 0.032)), f"{PUB_DT.month}/{PUB_DT.day} {WEEKDAY_CN} 08:00", fill=(255, 255, 255), font=fnt(int(w * 0.018), True), anchor="mm",
           stroke_width=3, stroke_fill=(24, 18, 10))
    return canvas


def build_variety_portrait(w, h, axin, xiaolan):
    pal = date_pick(PREP_DATE, VARIETY_PALS)
    canvas = vgrad(w, h, pal["top"], pal["bot"])
    bx, by = w // 2, int(h * 0.22)
    canvas = starburst(canvas, bx, by, int(w * 0.48), int(w * 0.34), 14, pal["burst"], 255)
    d = ImageDraw.Draw(canvas)

    tf = fnt(int(w * 0.135), True)
    draw_outline(d, (bx, by), "本周15条", tf, (255, 255, 255), outline=(24, 18, 10), w=max(6, int(w * 0.015)))
    d.text((bx, by + int(w * 0.115)), "信蓝组合 · 周末开聊", fill=(255, 255, 255), font=fnt(int(w * 0.045), True), anchor="mm",
           stroke_width=3, stroke_fill=(24, 18, 10))

    fs = int(w * 0.27)
    fy = int(h * 0.40)
    a1 = circular_face(axin, fs, (255, 255, 255), int(w * 0.005))
    a2 = circular_face(xiaolan, fs, (255, 255, 255), int(w * 0.005))
    gap = int(w * 0.07)
    canvas.paste(a1, (w // 2 - fs - gap // 2, fy), a1)
    canvas.paste(a2, (w // 2 + gap // 2, fy), a2)
    d = ImageDraw.Draw(canvas)
    nf = fnt(int(w * 0.042), True)
    for px, name in [(w // 2 - gap // 2 - fs // 2, "阿信"), (w // 2 + gap // 2 + fs // 2, "小蓝")]:
        bw = int(w * 0.15)
        d.rounded_rectangle([px - bw // 2, fy + fs + 10, px + bw // 2, fy + fs + 10 + int(h * 0.042)], radius=14, fill=(255, 255, 255), outline=(24, 18, 10), width=4)
        d.text((px, fy + fs + 10 + int(h * 0.021)), name, fill=(24, 18, 10), font=nf, anchor="mm")

    px1, px2 = int(w * 0.06), w - int(w * 0.06)
    ty = fy + fs + int(h * 0.075)
    d = ImageDraw.Draw(canvas, "RGBA")
    tf_t = fnt(int(w * 0.030), True)
    tf_s = fnt(int(w * 0.021))
    for rank, title, sub in TOP3:
        d.rounded_rectangle([px1, ty, px2, ty + int(h * 0.068)], radius=int(h * 0.034), fill=(255, 255, 255, 240), outline=(24, 18, 10), width=3)
        d.text((px1 + int(w * 0.025), ty + int(h * 0.018)), f"{rank}", fill=pal["top"], font=fnt(int(w * 0.032), True), anchor="lm")
        d.text((px1 + int(w * 0.075), ty + int(h * 0.019)), fit(tf_t, title, (px2 - px1) - int(w * 0.10)), fill=(24, 18, 10), font=tf_t, anchor="lm")
        d.text((px1 + int(w * 0.075), ty + int(h * 0.043)), fit(tf_s, sub, (px2 - px1) - int(w * 0.10)), fill=(110, 100, 90), font=tf_s, anchor="lm")
        ty += int(h * 0.082)
    d.text((w // 2, h - int(h * 0.033)), f"{PUB_DT.month}/{PUB_DT.day} {WEEKDAY_CN} 08:00", fill=(255, 255, 255), font=fnt(int(w * 0.040), True), anchor="mm",
           stroke_width=4, stroke_fill=(24, 18, 10))
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
        d.text((size // 2, size // 2 - 30), "本周15条", font=fnt(int(size * 0.16), True), fill=(*hue, 255), anchor="mm")
        d.text((size // 2, size // 2 + 30), "本周要闻", font=fnt(int(size * 0.10), True), fill=WHITE, anchor="mm")
        fs = int(size * 0.30)
        a1 = circular_face(axin, fs, AXIN_BLUE, 4)
        a2 = circular_face(xiaolan, fs, XIAOLAN_PINK, 4)
        fy = size - fs - 30
        canvas.paste(a1, (int(size * 0.10), fy), a1)
        canvas.paste(a2, (size - fs - int(size * 0.10), fy), a2)
        return canvas
    if style == "newspaper":
        pal = date_pick(PREP_DATE, NEWSPAPER_PALS)
        canvas = add_noise(Image.new("RGB", (size, size), pal["bg"]))
        d = ImageDraw.Draw(canvas)
        d.rectangle([14, 14, size - 14, size - 14], outline=pal["ink"], width=5)
        d.text((size // 2, int(size * 0.16)), "隔天信号弹", fill=pal["ink"], font=serif_fnt(int(size * 0.115)), anchor="mm")
        d.line([(int(size * 0.14), int(size * 0.26)), (int(size * 0.86), int(size * 0.26))], fill=pal["ink"], width=4)
        fs = int(size * 0.30)
        fy = int(size * 0.34)
        a1 = circular_face(axin, fs, pal["ink"], 6)
        a2 = circular_face(xiaolan, fs, pal["ink"], 6)
        canvas.paste(a1, (int(size * 0.12), fy), a1)
        canvas.paste(a2, (size - int(size * 0.12) - fs, fy), a2)
        d = ImageDraw.Draw(canvas)
        d.text((size // 2, int(size * 0.78)), "本周15条 · 周末特刊", fill=pal["ink"], font=serif_fnt(int(size * 0.065)), anchor="mm")
        d.text((size // 2, size - int(size * 0.09)), f"{PUB_DATE_SHORT}", fill=pal["accent"], font=serif_fnt(int(size * 0.05)), anchor="mm")
        return canvas
    if style == "popart":
        pal = date_pick(PREP_DATE, POPART_PALS)
        canvas = Image.new("RGB", (size, size), pal["a"])
        od = ImageDraw.Draw(canvas)
        od.polygon([(0, int(size * 0.62)), (size, int(size * 0.52)), (size, size), (0, size)], fill=pal["b"])
        canvas = halftone(canvas, (0, int(size * 0.45), size, int(size * 0.70)), pal["ink"], step=int(size * 0.035), rmax=int(size * 0.010))
        canvas = starburst(canvas, size // 2, int(size * 0.26), int(size * 0.34), int(size * 0.23), 12, pal["b"], 255)
        d = ImageDraw.Draw(canvas)
        draw_outline(d, (size // 2, int(size * 0.26)), "本周15条", fnt(int(size * 0.085), True), (255, 255, 255), outline=pal["ink"], w=6)
        fs = int(size * 0.24)
        fy = int(size * 0.60)
        a1 = circular_face(axin, fs, pal["ink"], 5)
        a2 = circular_face(xiaolan, fs, pal["ink"], 5)
        canvas.paste(a1, (int(size * 0.13), fy), a1)
        canvas.paste(a2, (size - int(size * 0.13) - fs, fy), a2)
        d = ImageDraw.Draw(canvas)
        d.text((size // 2, size - int(size * 0.08)), "信蓝组合 · 开聊！", fill=pal["ink"], font=fnt(int(size * 0.06), True), anchor="mm")
        return canvas
    if style == "glitch":
        pal = date_pick(PREP_DATE, GLITCH_PALS)
        canvas = Image.new("RGB", (size, size), (7, 7, 12))
        d = ImageDraw.Draw(canvas)
        for y in range(0, size, 6):
            d.line([(0, y), (size, y)], fill=(20, 20, 32))
        rgb_split_text(canvas, (size // 2, int(size * 0.24)), "本周15条", fnt(int(size * 0.105), True), (250, 250, 255), pal["hue"], pal["warn"], int(size * 0.007))
        d = ImageDraw.Draw(canvas)
        fs = int(size * 0.26)
        fy = int(size * 0.44)
        a1 = circular_face(axin, fs, pal["hue"], 4)
        a2 = circular_face(xiaolan, fs, pal["warn"], 4)
        canvas.paste(a1, (int(size * 0.14), fy), a1)
        canvas.paste(a2, (size - int(size * 0.14) - fs, fy), a2)
        canvas = glitch_shift(canvas, PREP_DATE)
        canvas = scanlines(canvas)
        d = ImageDraw.Draw(canvas)
        d.text((size // 2, size - int(size * 0.08)), "SIGNAL // POP // WEEKEND", fill=(*pal["hue"], 255), font=fnt(int(size * 0.04), True), anchor="mm")
        return canvas
    if style == "variety":
        pal = date_pick(PREP_DATE, VARIETY_PALS)
        canvas = vgrad(size, size, pal["top"], pal["bot"])
        canvas = starburst(canvas, size // 2, int(size * 0.28), int(size * 0.40), int(size * 0.28), 14, pal["burst"], 255)
        d = ImageDraw.Draw(canvas)
        draw_outline(d, (size // 2, int(size * 0.28)), "本周15条", fnt(int(size * 0.10), True), (255, 255, 255), outline=(24, 18, 10), w=7)
        fs = int(size * 0.25)
        fy = int(size * 0.50)
        a1 = circular_face(axin, fs, (255, 255, 255), 5)
        a2 = circular_face(xiaolan, fs, (255, 255, 255), 5)
        canvas.paste(a1, (int(size * 0.14), fy), a1)
        canvas.paste(a2, (size - int(size * 0.14) - fs, fy), a2)
        d = ImageDraw.Draw(canvas)
        d.text((size // 2, size - int(size * 0.08)), f"{PUB_DT.month}/{PUB_DT.day} {WEEKDAY_CN} 08:00", fill=(255, 255, 255), font=fnt(int(size * 0.05), True), anchor="mm",
               stroke_width=3, stroke_fill=(24, 18, 10))
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


BUILDERS = {
    "split": (build_split_landscape, build_split_portrait),
    "magazine": (build_magazine_landscape, build_magazine_portrait),
    "neon": (build_neon_landscape, build_neon_portrait),
    "newspaper": (build_newspaper_landscape, build_newspaper_portrait),
    "popart": (build_popart_landscape, build_popart_portrait),
    "glitch": (build_glitch_landscape, build_glitch_portrait),
    "variety": (build_variety_landscape, build_variety_portrait),
}


def main():
    global TOP3
    # 风格解析：auto 按日期轮换（正式出品才记录历史），显式传风格则直接用
    if STYLE == "auto":
        style = pick_style_auto(PREP_DATE, record=(SUFFIX == ""))
        src = "auto"
    else:
        style = STYLE
        src = "manual"
    print(f"[cover] style={style} ({src}) date={PREP_DATE}" + (f" suffix={SUFFIX}" if SUFFIX else ""))
    TOP3 = load_top3()
    print(f"[cover] TOP3 = {[t for _, t, _ in TOP3]}")

    axin = Image.open(os.path.join(IMAGES_DIR, "anchor_axin.jpg"))
    xiaolan = Image.open(os.path.join(IMAGES_DIR, "anchor_xiaolan.jpg"))
    os.makedirs(OUT_DIR, exist_ok=True)
    covers = [
        ("16x9", 1920, 1080, "landscape"),
        ("4x3", 1440, 1080, "landscape"),
        ("3x4", 1080, 1440, "portrait"),
    ]
    build_ls, build_pt = BUILDERS.get(style, BUILDERS["magazine"])
    sfx = f"_{SUFFIX}" if SUFFIX else ""
    for name, w, h, kind in covers:
        img = build_ls(w, h, axin, xiaolan) if kind == "landscape" else build_pt(w, h, axin, xiaolan)
        out = os.path.join(OUT_DIR, f"cover_weekly_{PREP_DATE}{sfx}_{name}.png")
        img.save(out, quality=92)
        print(f"✅ {style} {name} ({w}x{h}): {out}")
    avatar = build_avatar(axin, xiaolan, 800, style)
    av = os.path.join(OUT_DIR, f"avatar_weekly_{PREP_DATE}{sfx}.png")
    avatar.save(av, quality=92)
    print(f"✅ {style} avatar: {av}")


if __name__ == "__main__":
    main()
