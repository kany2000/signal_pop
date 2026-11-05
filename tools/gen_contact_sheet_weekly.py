#!/usr/bin/env python3
"""Signal Pop 周末版 — 拼配图 contact sheet 供用户审图。

2026-11-06 改造：原先 ORDER 是 20260925 期的硬编码列表，每期都要改代码。
现在改为**读当期 parsed_news.json 自动推导顺序与标签**，零代码只换配置。

顺序 = parsed_news.json 里的条目顺序（= 实际播报顺序）；
标签 = 「表号 板块 · 标题前 12 字」；末尾自动追加 shared 三张与聊经济 4 张（若存在）。

用法:
    python tools/gen_contact_sheet_weekly.py 20261106 [输出名]
"""
import json
import os
import sys
from PIL import Image, ImageDraw, ImageFont

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 聊经济环节的 4 张幻灯片（存在才拼进去）
ECON_SLIDES = [
    ("econ_slide_1", "聊经济01·开场"),
    ("econ_slide_2", "聊经济02·成因"),
    ("econ_slide_3", "聊经济03·共振"),
    ("econ_slide_4", "聊经济04·收束"),
]


def find_font(size):
    for c in ("C:/Windows/Fonts/msyh.ttc", "C:/Windows/Fonts/msyhbd.ttc",
              "C:/Windows/Fonts/simhei.ttf", "C:/Windows/Fonts/simsun.ttc"):
        if os.path.exists(c):
            try:
                return ImageFont.truetype(c, size)
            except Exception:
                continue
    return ImageFont.load_default()


def build_order(date):
    """从当期 parsed_news.json 推导 (stem, label) 顺序表。"""
    pj = os.path.join(BASE, "output", "weekly", date, "parsed_news.json")
    order = []
    if os.path.exists(pj):
        with open(pj, encoding="utf-8") as f:
            items = json.load(f)
        for i, it in enumerate(items):
            stem = os.path.splitext(it.get("img", ""))[0]
            if not stem:
                continue
            label = f"{i + 1:02d} {it.get('section', '')}·{it.get('title', '')[:12]}"
            order.append((stem, label))
    else:
        print(f"[contact_sheet_weekly] ⚠️ 未找到 {pj}，退回旧硬编码顺序")
        order = [("breaking", "特别报道"), ("interactive", "互动话题"), ("pick", "每期精选")]
    order += ECON_SLIDES
    return order


def resolve(img_dir, stem):
    """定位配图实际路径。

    聊经济 4 张幻灯片是跨期复用的静态图，放在 remotion_poc/public/ 而不在期次 images/ 下
    （Remotion 从 public 目录读 staticFile），所以这里两处都找。
    """
    for d in (img_dir, os.path.join(BASE, "remotion_poc", "public")):
        p = os.path.join(d, stem + ".jpg")
        if os.path.exists(p):
            return p
    return None


def main():
    date = sys.argv[1]
    out_name = sys.argv[2] if len(sys.argv) > 2 else "contact_sheet.png"
    # 可选第 3 参数：配图子目录（默认 images；images_nomark = 无生图标记版）
    sub = sys.argv[3] if len(sys.argv) > 3 else "images"
    img_dir = os.path.join(BASE, "output", "weekly", date, sub)
    out_path = os.path.join(BASE, "output", "weekly", date, out_name)

    order = build_order(date)
    items = []
    missing = []
    for stem, label in order:
        p = resolve(img_dir, stem)
        if p:
            items.append((stem, label, p))
        else:
            missing.append(stem)
    if not items:
        print(f"[contact_sheet_weekly] 未找到配图：{img_dir}")
        sys.exit(1)

    thumb_w, thumb_h = 640, 360
    label_h = 44
    cols = 3
    rows = (len(items) + cols - 1) // cols
    pad = 12
    sheet_w = cols * thumb_w + (cols + 1) * pad
    sheet_h = rows * (thumb_h + label_h) + (rows + 1) * pad

    sheet = Image.new("RGB", (sheet_w, sheet_h), (24, 26, 30))
    draw = ImageDraw.Draw(sheet)
    font = find_font(26)

    for idx, (stem, label, f) in enumerate(items):
        r, c = divmod(idx, cols)
        x = pad + c * (thumb_w + pad)
        y = pad + r * (thumb_h + label_h + pad)
        im = Image.open(f).convert("RGB")
        im = im.resize((thumb_w, thumb_h), Image.LANCZOS)
        sheet.paste(im, (x, y))
        draw.rectangle([x, y, x + thumb_w, y + label_h], fill=(0, 0, 0))
        draw.text((x + 12, y + 8), label, fill=(255, 255, 0), font=font)

    sheet.save(out_path, quality=88)
    print(f"[contact_sheet_weekly] ✅ 已生成 {out_path}（{len(items)}/{len(order)} 张，网格 {cols}x{rows}）")
    if missing:
        print(f"[contact_sheet_weekly] ⚠️ 缺图: {missing}")


if __name__ == "__main__":
    main()
