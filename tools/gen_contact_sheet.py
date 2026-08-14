#!/usr/bin/env python3
"""Signal Pop — 生成配图 contact sheet 供用户审图。

把 images 目录下的 00.jpg(历史) + 01~10.jpg(新闻) 拼成网格，
每格标注编号，输出一张 contact_sheet.png 供人工审阅。

用法:
    python tools/gen_contact_sheet.py [制作日YYYYMMDD] [输出名]
"""
import os
import sys
from PIL import Image, ImageDraw, ImageFont

BASE = "E:/projects/signal_pop"


def find_font(size):
    """找一个可用的中文字体（用于编号标签）。"""
    candidates = [
        "C:/Windows/Fonts/msyh.ttc",       # 微软雅黑
        "C:/Windows/Fonts/msyhbd.ttc",     # 微软雅黑粗体
        "C:/Windows/Fonts/simhei.ttf",     # 黑体
        "C:/Windows/Fonts/simsun.ttc",     # 宋体
    ]
    for c in candidates:
        if os.path.exists(c):
            try:
                return ImageFont.truetype(c, size)
            except Exception:
                continue
    return ImageFont.load_default()


def main():
    date = sys.argv[1] if len(sys.argv) > 1 else None
    out_name = sys.argv[2] if len(sys.argv) > 2 else "contact_sheet.png"
    kind = sys.argv[3] if len(sys.argv) > 3 else "daily"  # daily | weekly

    sub = "weekly" if kind == "weekly" else "daily"
    if date:
        img_dir = os.path.join(BASE, "output", sub, date, "images")
        out_path = os.path.join(BASE, "output", sub, date, out_name)
    else:
        img_dir = os.path.join(BASE, "output", sub, "images")
        out_path = os.path.join(BASE, "output", out_name)

    # 自动扫描编号图片（排除 opening_bg/ending_bg），daily 支持 00=历史
    files = []
    for fname in sorted(os.listdir(img_dir)) if os.path.isdir(img_dir) else []:
        if not fname.endswith(".jpg"):
            continue
        stem = fname[:-4]
        if not stem.isdigit():
            continue
        n = int(stem)
        files.append((n, os.path.join(img_dir, fname)))
    files.sort(key=lambda x: x[0])

    if not files:
        print(f"[contact_sheet] 未找到配图：{img_dir}")
        sys.exit(1)

    thumb_w, thumb_h = 640, 360
    label_h = 44
    cols = 3
    rows = (len(files) + cols - 1) // cols
    pad = 12
    sheet_w = cols * thumb_w + (cols + 1) * pad
    sheet_h = rows * (thumb_h + label_h) + (rows + 1) * pad

    sheet = Image.new("RGB", (sheet_w, sheet_h), (24, 26, 30))
    draw = ImageDraw.Draw(sheet)
    font = find_font(26)

    for idx, (n, f) in enumerate(files):
        r, c = divmod(idx, cols)
        x = pad + c * (thumb_w + pad)
        y = pad + r * (thumb_h + label_h + pad)
        # 缩略图
        im = Image.open(f).convert("RGB")
        im = im.resize((thumb_w, thumb_h), Image.LANCZOS)
        sheet.paste(im, (x, y))
        # 编号标签
        label = "历史" if n == 0 else f"新闻{n:02d}"
        draw.rectangle([x, y, x + thumb_w, y + label_h], fill=(0, 0, 0))
        draw.text((x + 12, y + 8), label, fill=(255, 255, 0), font=font)

    sheet.save(out_path, quality=88)
    print(f"[contact_sheet] ✅ 已生成 {out_path}（{len(files)} 张，网格 {cols}x{rows}）")


if __name__ == "__main__":
    main()
