#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Signal Pop 周末特别版 · 双人封面生成 v2（信蓝组合）

新思路：主播脸部成为封面主体，脸部大特写占画面 70%+，文字仅在边角条带。

- 16:9 / 4:3 横版：左阿信右小蓝，各占半屏，中间留金色彩带放标题
- 3:4 竖版：上阿信下小蓝，各占 44% 高度，中间金色彩带分隔
- 头像：用 800x800 双人合体图（阿信左半 + 小蓝右半拼接）

用法：python tools/gen_weekly_talk_cover.py [PREP_DATE]
"""
import os
import sys
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps

PROJECT_ROOT = "E:/projects/signal_pop"
PREP_DATE = sys.argv[1] if len(sys.argv) > 1 else "20260814"
OUT_DIR = os.path.join(PROJECT_ROOT, "output", "weekly", PREP_DATE)
IMAGES_DIR = os.path.join(OUT_DIR, "images")
FONT = "C:/Windows/Fonts/msyh.ttc"
FONT_BOLD = "C:/Windows/Fonts/msyhbd.ttc"

PUB_DT = datetime.strptime(PREP_DATE, "%Y%m%d") + timedelta(days=1)
PUB_DATE_SHORT = f"{PUB_DT.year}.{PUB_DT.month:02d}.{PUB_DT.day:02d}"

GOLD = (212, 175, 55)
GOLD_BRIGHT = (255, 215, 100)
AXIN_BLUE = (58, 130, 210)
XIAOLAN_PINK = (220, 90, 150)
WHITE = (250, 250, 252)
LIGHT_GREY = (190, 198, 210)
DARK = (8, 10, 18)
DARK_NAVY = (15, 22, 42)


def fnt(size, bold=True):
    return ImageFont.truetype(FONT_BOLD if bold else FONT, size)


def fit_face(face_img, target_w, target_h, blur_overlay=True):
    """把主播脸部图裁剪适配到目标区域，中心裁剪保留脸部。返回 RGB 图。"""
    # 先按目标尺寸做中心裁剪（保持原比例），避免拉伸变形
    img = ImageOps.fit(face_img.convert("RGB"), (target_w, target_h), method=Image.LANCZOS, centering=(0.5, 0.4))
    # 左/右/顶部加渐变暗化，让文字更易读
    if blur_overlay:
        overlay = Image.new("RGBA", (target_w, target_h), (0, 0, 0, 0))
        od = ImageDraw.Draw(overlay)
        # 顶部暗化（标题区）
        top_h = int(target_h * 0.18)
        for i in range(top_h):
            a = int(120 * (1 - i / top_h))
            od.line([(0, i), (target_w, i)], fill=(0, 0, 0, a))
        # 底部暗化（信息条区）
        bot_h = int(target_h * 0.12)
        for i in range(bot_h):
            a = int(160 * (i / bot_h))
            od.line([(0, target_h - 1 - i), (target_w, target_h - 1 - i)], fill=(0, 0, 0, a))
        img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    return img


def add_bottom_band(canvas, w, h, ratio=0.10, color=DARK_NAVY, alpha=200):
    """底部加一条信息带。"""
    band_h = int(h * ratio)
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    od.rectangle([0, h - band_h, w, h], fill=(*color, alpha))
    return Image.alpha_composite(canvas.convert("RGBA"), overlay).convert("RGB")


def add_top_band(canvas, w, h, ratio=0.14, color=DARK_NAVY, alpha=210):
    """顶部加一条标题带。"""
    band_h = int(h * ratio)
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    od.rectangle([0, 0, w, band_h], fill=(*color, alpha))
    return Image.alpha_composite(canvas.convert("RGBA"), overlay).convert("RGB")


def build_cover_landscape(w, h, axin_img, xiaolan_img):
    """横版：左阿信右小蓝，中间金色彩带放标题。"""
    # 左右各占 (w - center_w) / 2，center_w 是中间标题条
    center_w = int(w * 0.16)
    half_w = (w - center_w) // 2
    face_h = h

    # 左半：阿信
    left = fit_face(axin_img, half_w, face_h)
    # 右半：小蓝
    right = fit_face(xiaolan_img, half_w, face_h)

    canvas = Image.new("RGB", (w, h), DARK)
    canvas.paste(left, (0, 0))
    canvas.paste(right, (w - half_w, 0))

    # 中间金色彩带
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    for x in range(center_w):
        ratio = x / center_w
        r = int(120 + 90 * (0.5 - abs(ratio - 0.5)))
        g = int(80 + 80 * (0.5 - abs(ratio - 0.5)))
        b = int(30 + 30 * (0.5 - abs(ratio - 0.5)))
        od.line([(half_w + x, 0), (half_w + x, h)], fill=(r, g, b, 255))
    canvas = Image.alpha_composite(canvas.convert("RGBA"), overlay).convert("RGB")

    d = ImageDraw.Draw(canvas)
    # === 中间彩带：只放主标题 ===
    title_size = int(center_w * 0.38)
    title_f = fnt(title_size, bold=True)
    cx = half_w + center_w // 2

    title_text = "本\n周\nTOP\n10"
    lines = title_text.split("\n")
    line_h = title_f.size + 4
    total_h = line_h * len(lines)
    y0 = (h - total_h) // 2
    for i, line in enumerate(lines):
        y = y0 + i * line_h
        # 描边
        for ox, oy in [(-2, 0), (2, 0), (0, -2), (0, 2)]:
            d.text((cx + ox, y + oy), line, fill=(40, 30, 10), font=title_f, anchor="mm")
        d.text((cx, y), line, fill=GOLD_BRIGHT, font=title_f, anchor="mm")

    # === 顶部条带：节目名（窄小字） ===
    top_label_f = fnt(int(w * 0.022), bold=True)
    top_sub_f = fnt(int(w * 0.016))
    d.text((w // 2, int(h * 0.04)), "隔天信号弹 · 周末特别版", fill=GOLD, font=top_label_f, anchor="mm")
    d.text((w // 2, int(h * 0.075)), "信蓝组合 · 本周 TOP10 对话脱口秀", fill=LIGHT_GREY, font=top_sub_f, anchor="mm")

    # === 底部条带：日期 ===
    date_f = fnt(int(w * 0.024), bold=True)
    d.text((w // 2, h - int(h * 0.05)), f"周六 08:00 · {PUB_DATE_SHORT}", fill=GOLD, font=date_f, anchor="mm")

    # === 左右角色名字（叠加在脸部下方，蓝/粉色加描边） ===
    name_size = int(h * 0.07)
    name_f = fnt(name_size, bold=True)
    # 阿信（左下）
    ax_pos = (half_w // 2, h - int(h * 0.13))
    for ox, oy in [(-3, 0), (3, 0), (0, -3), (0, 3)]:
        d.text((ax_pos[0] + ox, ax_pos[1] + oy), "阿信", fill=(20, 30, 60), font=name_f, anchor="mm")
    d.text(ax_pos, "阿信", fill=AXIN_BLUE, font=name_f, anchor="mm")
    # 小蓝（右下）
    xl_pos = (w - half_w // 2, h - int(h * 0.13))
    for ox, oy in [(-3, 0), (3, 0), (0, -3), (0, 3)]:
        d.text((xl_pos[0] + ox, xl_pos[1] + oy), "小蓝", fill=(60, 20, 40), font=name_f, anchor="mm")
    d.text(xl_pos, "小蓝", fill=XIAOLAN_PINK, font=name_f, anchor="mm")

    # 顶部底部金色装饰条
    d.rectangle([0, 0, w, 4], fill=GOLD)
    d.rectangle([0, h - 4, w, h], fill=GOLD)

    return canvas


def build_cover_portrait(w, h, axin_img, xiaolan_img):
    """竖版 3:4：上阿信下小蓝，中间金色彩带放标题。"""
    # 上下各占 (h - band_h) / 2，band_h 是中间标题条
    band_h = int(h * 0.13)
    half_h = (h - band_h) // 2
    face_w = w

    # 上：阿信
    top = fit_face(axin_img, face_w, half_h)
    # 下：小蓝
    bot = fit_face(xiaolan_img, face_w, half_h)

    canvas = Image.new("RGB", (w, h), DARK)
    canvas.paste(top, (0, 0))
    canvas.paste(bot, (0, h - half_h))

    # 中间金色彩带（横条）
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    for y in range(band_h):
        ratio = y / band_h
        a_r = int(70 + 90 * (0.5 - abs(ratio - 0.5)))
        a_g = int(50 + 70 * (0.5 - abs(ratio - 0.5)))
        a_b = int(20 + 25 * (0.5 - abs(ratio - 0.5)))
        od.line([(0, half_h + y), (w, half_h + y)], fill=(a_r, a_g, a_b, 255))
    canvas = Image.alpha_composite(canvas.convert("RGBA"), overlay).convert("RGB")

    d = ImageDraw.Draw(canvas)
    # 中间彩带文字
    band_cy = half_h + band_h // 2
    title_size = int(band_h * 0.55)
    sub_size = int(band_h * 0.20)
    title_f = fnt(title_size, bold=True)
    sub_f = fnt(sub_size, bold=True)
    # 主标题（横排）
    title = "本周 TOP10"
    # 描边
    for ox, oy in [(-2, 0), (2, 0), (0, -2), (0, 2)]:
        d.text((w // 2 + ox, band_cy - title_size * 0.4 + oy), title, fill=(40, 30, 10), font=title_f, anchor="mm")
    d.text((w // 2, band_cy - title_size * 0.4), title, fill=GOLD_BRIGHT, font=title_f, anchor="mm")
    # 副标题
    d.text((w // 2, band_cy + sub_size * 0.8), "信蓝组合 · 开聊！", fill=WHITE, font=sub_f, anchor="mm")

    # 顶部金色装饰条 + 节目名
    d.rectangle([0, 0, w, 5], fill=GOLD)
    top_label_f = fnt(int(w * 0.07), bold=True)
    d.text((w // 2, int(w * 0.06) + 8), "隔天信号弹 · 周末特别版", fill=GOLD, font=top_label_f, anchor="mm")

    # 底部金色装饰条 + 日期
    d.rectangle([0, h - 5, w, h], fill=GOLD)
    date_f = fnt(int(w * 0.06), bold=True)
    d.text((w // 2, h - int(w * 0.06) - 8), "8/15 周六 08:00", fill=GOLD, font=date_f, anchor="mm")

    # 左右角色名字（贴在上半底部/下半顶部）
    name_size = int(w * 0.085)
    name_f = fnt(name_size, bold=True)
    # 阿信名字（左下角）-- 描边
    ax_pos = (int(w * 0.12), half_h - int(w * 0.06))
    for ox, oy in [(-3, 0), (3, 0), (0, -3), (0, 3)]:
        d.text((ax_pos[0] + ox, ax_pos[1] + oy), "阿信", fill=(20, 30, 60), font=name_f, anchor="mm")
    d.text(ax_pos, "阿信", fill=AXIN_BLUE, font=name_f, anchor="mm")
    # 小蓝名字（右下角）
    xl_pos = (int(w * 0.88), h - half_h + int(w * 0.06))
    for ox, oy in [(-3, 0), (3, 0), (0, -3), (0, 3)]:
        d.text((xl_pos[0] + ox, xl_pos[1] + oy), "小蓝", fill=(60, 20, 40), font=name_f, anchor="mm")
    d.text(xl_pos, "小蓝", fill=XIAOLAN_PINK, font=name_f, anchor="mm")

    return canvas


def build_avatar(axin_img, xiaolan_img, size=800):
    """头像：800x800，左阿信右小蓝，中间金色分割线。"""
    half = size // 2
    left = fit_face(axin_img, half, size)
    right = fit_face(xiaolan_img, half, size)
    canvas = Image.new("RGB", (size, size), DARK)
    canvas.paste(left, (0, 0))
    canvas.paste(right, (half, 0))
    d = ImageDraw.Draw(canvas)
    d.rectangle([half - 4, 0, half + 4, size], fill=GOLD)
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
    for name, w, h, kind in covers:
        if kind == "landscape":
            img = build_cover_landscape(w, h, axin, xiaolan)
        else:
            img = build_cover_portrait(w, h, axin, xiaolan)
        out = os.path.join(OUT_DIR, f"cover_weekly_{PREP_DATE}_{name}.png")
        img.save(out, quality=92)
        print(f"✅ {name} ({w}x{h}): {out}")

    # 头像
    avatar = build_avatar(axin, xiaolan, 800)
    av_out = os.path.join(OUT_DIR, f"avatar_weekly_{PREP_DATE}.png")
    avatar.save(av_out, quality=92)
    print(f"✅ avatar: {av_out}")


if __name__ == "__main__":
    main()