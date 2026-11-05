#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Signal Pop 周末版 · handraw 涂鸦封面合成器（2026-11-03 新增）

流程：handraw-style 技能（Pop Magazine Doodle Overlay / Hattie Stewart）生成
无文字底图 → 本 PIL 脚本合成封面文字 / 双人头像 / TOP3 / 日期胶囊。
文字零乱码（配图定律：AI 画面内禁止出现可读文字）。

底图来源：output/weekly/{PREP_DATE}/_cover_tmp/ 下两张生成图（横版 + 竖版）。
输出（SUFFIX 预览名，不覆盖正式名）：
  cover_weekly_{PREP_DATE}_handraw_16x9.png / _4x3 / _3x4
  avatar_weekly_{PREP_DATE}_handraw.png
"""
import os
import sys
import glob
from PIL import Image, ImageDraw, ImageFont, ImageOps

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PREP_DATE = sys.argv[1] if len(sys.argv) > 1 else "20261106"
SUFFIX = sys.argv[2] if len(sys.argv) > 2 else "handraw"

OUT_DIR = os.path.join(PROJECT_ROOT, "output", "weekly", PREP_DATE)
TMP_DIR = os.path.join(OUT_DIR, "cover_art_src")
FACE_A = os.path.join(PROJECT_ROOT, "remotion_poc", "public", "anchor_axin.jpg")
FACE_X = os.path.join(PROJECT_ROOT, "remotion_poc", "public", "anchor_xiaolan.jpg")
FONT_BOLD = "C:/Windows/Fonts/msyhbd.ttc"
FONT = "C:/Windows/Fonts/msyh.ttc"

INK = (24, 20, 26)
KLEIN = (0, 47, 167)
YELLOW = (255, 214, 48)
PINK = (236, 64, 122)
WHITE = (255, 255, 255)
GREY = (110, 105, 115)

# 播出日 = 制作日所在周的周六
from datetime import datetime, timedelta
_dt = datetime.strptime(PREP_DATE, "%Y%m%d")
PUB = _dt + timedelta(days=(5 - _dt.weekday()) % 7)
DATE_TXT = f"{PUB.month}.{PUB.day:02d} 周六 · 准时开聊"

# 本期 TOP3（与新闻稿同步，表号 1/2/3）
TOP3 = [
    ("01", "超强厄尔尼诺正式形成", "或成有记录以来最强"),
    ("02", "首个太空算力云平台发布", "天地算力统一调度"),
    ("03", "币安恢复提现", "95%被盗资产已补足"),
]


def fnt(size, bold=True):
    return ImageFont.truetype(FONT_BOLD if bold else FONT, size)


def paste_rot(canvas, layer, center, angle):
    rot = layer.rotate(angle, expand=True, resample=Image.BICUBIC)
    canvas.paste(rot, (int(center[0] - rot.width / 2), int(center[1] - rot.height / 2)), rot)
    return canvas


def capsule(canvas, center, text, bg, fg, size, angle=0, pad=(30, 12), ow=3):
    """圆角胶囊贴纸：bg 底 + ink 描边 + 居中文字，整体可旋转。"""
    f = fnt(size)
    tw = f.getlength(text)
    w, h = int(tw + pad[0] * 2), int(size * 1.3 + pad[1] * 2)
    layer = Image.new("RGBA", (w + 80, h + 80), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.rounded_rectangle([40, 40, 40 + w, 40 + h], radius=h // 2,
                        fill=(*bg, 255), outline=(*INK, 255), width=ow)
    d.text((40 + w / 2, 40 + h / 2), text, font=f, fill=(*fg, 255), anchor="mm")
    return paste_rot(canvas, layer, center, angle)


def title_sticker(canvas, box, angle=-1.5, title_size=140, sub_size=40):
    """白色标题贴纸：「本周10条」（10条 用克莱因蓝强调）+ 副题。"""
    x1, y1, x2, y2 = box
    w, h = x2 - x1, y2 - y1
    layer = Image.new("RGBA", (w + 80, h + 80), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.rounded_rectangle([40, 40, 40 + w, 40 + h], radius=40,
                        fill=(*WHITE, 250), outline=(*INK, 255), width=5)
    tf = fnt(title_size)
    w1 = tf.getlength("本周")
    w2 = tf.getlength("10条")
    tx = 40 + (w - w1 - w2) / 2
    ty = 40 + int(h * 0.30)
    d.text((tx, ty), "本周", font=tf, fill=(*INK, 255), anchor="lm")
    d.text((tx + w1, ty), "10条", font=tf, fill=(*KLEIN, 255), anchor="lm")
    d.line([(40 + w * 0.12, 40 + h * 0.62), (40 + w * 0.88, 40 + h * 0.62)],
           fill=(*YELLOW, 255), width=6)
    sf = fnt(sub_size)
    d.text((40 + w / 2, 40 + h * 0.80), "信蓝组合 · 一报一评开聊",
           font=sf, fill=(*GREY, 255), anchor="mm")
    return paste_rot(canvas, layer, ((x1 + x2) / 2, (y1 + y2) / 2), angle)


def top3_rows(canvas, x1, x2, y_start, row_h, gap, title_size=28):
    """三行 TOP3 白色胶囊行（轻微交替旋转）。"""
    rank_colors = [YELLOW, PINK, KLEIN]
    for i, (rank, title, sub) in enumerate(TOP3):
        y = y_start + i * (row_h + gap)
        w = x2 - x1
        layer = Image.new("RGBA", (w + 80, row_h + 80), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        d.rounded_rectangle([40, 40, 40 + w, 40 + row_h], radius=row_h // 2,
                            fill=(*WHITE, 248), outline=(*INK, 255), width=3)
        rc = rank_colors[i]
        rr = row_h * 0.32
        rcx = 40 + row_h * 0.55
        d.ellipse([rcx - rr, 40 + row_h / 2 - rr, rcx + rr, 40 + row_h / 2 + rr], fill=(*rc, 255))
        d.text((rcx, 40 + row_h / 2), rank, font=fnt(int(row_h * 0.42)),
               fill=(*INK, 255) if i != 2 else (*WHITE, 255), anchor="mm")
        tf = fnt(title_size)
        d.text((rcx + rr + 18, 40 + row_h / 2), title,
               font=tf, fill=(*INK, 255), anchor="lm")
        sf = fnt(int(title_size * 0.66), bold=False)
        sw = sf.getlength(sub)
        d.text((40 + w - 24, 40 + row_h / 2), sub, font=sf,
               fill=(*GREY, 255), anchor="rm")
        canvas = paste_rot(canvas, layer, (x1 + w / 2, y + row_h / 2), -1.2 if i % 2 else 1.2)
    return canvas


def host(canvas, path, cx, cy, size, name, name_bg):
    """圆形主持人头像：白环 + 墨线 + 下方名牌胶囊。"""
    img = ImageOps.fit(Image.open(path).convert("RGB"), (size, size),
                       Image.LANCZOS, centering=(0.5, 0.4))
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, size, size], fill=255)
    face = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    face.paste(img, (0, 0), mask)
    canvas.paste(face, (int(cx - size / 2), int(cy - size / 2)), face)
    d = ImageDraw.Draw(canvas)
    d.ellipse([cx - size / 2, cy - size / 2, cx + size / 2, cy + size / 2],
              outline=WHITE, width=max(6, size // 18))
    d.ellipse([cx - size / 2 - 4, cy - size / 2 - 4, cx + size / 2 + 4, cy + size / 2 + 4],
              outline=INK, width=3)
    cap_w = int(size * 0.78)
    cap_h = int(size * 0.24)
    layer = Image.new("RGBA", (cap_w + 80, cap_h + 80), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    ld.rounded_rectangle([40, 40, 40 + cap_w, 40 + cap_h], radius=cap_h // 2,
                         fill=(*name_bg, 255), outline=(*INK, 255), width=3)
    ld.text((40 + cap_w / 2, 40 + cap_h / 2), name, font=fnt(int(cap_h * 0.52)),
            fill=(*WHITE, 255), anchor="mm")
    paste_rot(canvas, layer, (cx, cy + size / 2 + cap_h * 0.75), 0)
    return canvas


def load_art():
    """从 _cover_tmp 取生成图：横版(宽>高) + 竖版(高>宽)。"""
    files = glob.glob(os.path.join(TMP_DIR, "*.png"))
    land = port = None
    for f in files:
        im = Image.open(f)
        if im.width >= im.height and land is None:
            land = im.convert("RGB")
        elif im.height > im.width and port is None:
            port = im.convert("RGB")
    if land is None or port is None:
        raise FileNotFoundError(f"底图不全: {files}")
    return land, port


def scale_crop(img, tw, th, crop="bottom", x_bias=0.5):
    """缩放至覆盖目标尺寸后裁切。crop: bottom=全裁底部 | center | top。"""
    s = max(tw / img.width, th / img.height)
    w, h = round(img.width * s), round(img.height * s)
    img = img.resize((w, h), Image.LANCZOS)
    if crop == "bottom":
        x0 = round((w - tw) * x_bias)
        return img.crop((x0, h - th, x0 + tw, h))
    if crop == "top":
        x0 = round((w - tw) * x_bias)
        return img.crop((x0, 0, x0 + tw, th))
    x0, y0 = round((w - tw) * x_bias), round((h - th) / 2)
    return img.crop((x0, y0, x0 + tw, y0 + th))


def build_16x9(art):
    canvas = scale_crop(art, 1920, 1080, crop="top")  # 裁底部 → 顺带裁掉水印
    d = ImageDraw.Draw(canvas)
    capsule(canvas, (315, 90), "隔天信号弹 · 周末特别版", YELLOW, INK, 30, angle=-2)
    title_sticker(canvas, (70, 150, 850, 530), title_size=140, sub_size=42)
    canvas = top3_rows(canvas, 70, 810, 580, 60, 18, title_size=30)
    host(canvas, FACE_A, 175, 905, 168, "阿信", KLEIN)
    host(canvas, FACE_X, 395, 905, 168, "小蓝", PINK)
    d = ImageDraw.Draw(canvas)
    capsule(canvas, (1712, 1018), DATE_TXT, WHITE, INK, 30, angle=0)
    return canvas


def build_4x3(art):
    canvas = scale_crop(art, 1440, 1080, crop="top", x_bias=0.0)  # 保左蓝区，右裁掉水印
    capsule(canvas, (250, 85), "隔天信号弹 · 周末特别版", YELLOW, INK, 27, angle=-2)
    title_sticker(canvas, (60, 135, 740, 490), title_size=116, sub_size=36)
    canvas = top3_rows(canvas, 60, 700, 535, 55, 16, title_size=27)
    host(canvas, FACE_A, 145, 890, 150, "阿信", KLEIN)
    host(canvas, FACE_X, 340, 890, 150, "小蓝", PINK)
    capsule(canvas, (1245, 1010), DATE_TXT, WHITE, INK, 26, angle=0)
    return canvas


def build_3x4(art):
    canvas = scale_crop(art, 1080, 1440, crop="top")  # 裁底部 → 裁掉水印
    capsule(canvas, (540, 85), "隔天信号弹 · 周末特别版", YELLOW, INK, 28, angle=-2)
    title_sticker(canvas, (110, 150, 970, 530), title_size=120, sub_size=38)
    canvas = top3_rows(canvas, 100, 980, 575, 58, 16, title_size=28)
    host(canvas, FACE_A, 330, 950, 190, "阿信", KLEIN)
    host(canvas, FACE_X, 750, 950, 190, "小蓝", PINK)
    capsule(canvas, (860, 1330), DATE_TXT, WHITE, INK, 28, angle=0)
    return canvas


def build_avatar(art):
    """头像 800×800：取横版底图巨浪+信号弹区域。"""
    # y 0..976：避开原底图右下角 y≈985 起的水印带
    sq = art.crop((560, 0, 1536, 976)).resize((800, 800), Image.LANCZOS)
    capsule(sq, (400, 738), "信蓝组合 · 周末开聊", WHITE, INK, 40, angle=0)
    return sq


def main():
    land, port = load_art()
    sfx = f"_{SUFFIX}" if SUFFIX else ""
    outs = [
        (build_16x9(land), f"cover_weekly_{PREP_DATE}{sfx}_16x9.png"),
        (build_4x3(land), f"cover_weekly_{PREP_DATE}{sfx}_4x3.png"),
        (build_3x4(port), f"cover_weekly_{PREP_DATE}{sfx}_3x4.png"),
        (build_avatar(land), f"avatar_weekly_{PREP_DATE}{sfx}.png"),
    ]
    for img, name in outs:
        p = os.path.join(OUT_DIR, name)
        img.save(p, quality=92)
        print(f"✅ {name}  {img.size}  {os.path.getsize(p) // 1024}KB")


if __name__ == "__main__":
    main()
