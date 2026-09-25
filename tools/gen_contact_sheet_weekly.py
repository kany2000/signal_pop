#!/usr/bin/env python3
"""Signal Pop 周末版 — 拼配图 contact sheet 供用户审图。

扫描 output/weekly/{date}/images/ 下命名图片：
breaking / news_01..14 / summary / watch / interactive / pick，
每格标注章节名，输出 contact_sheet.png。

用法:
    python tools/gen_contact_sheet_weekly.py 20260904 [输出名]
"""
import os
import sys
from PIL import Image, ImageDraw, ImageFont

BASE = "E:/projects/signal_pop"

# 展示顺序与中文章节标签（精确对应 20260925 期用户指定顺序）
ORDER = [
    ("breaking", "特别报道·Claude5.5"),
    ("news_01", "01 水产秋收"),
    ("news_02", "02 市场监管食品"),
    ("news_03", "03 银行存款利率"),
    ("news_04", "04 车企造机器人"),
    ("news_05", "05 11.3万亿吨冰"),
    ("news_06", "06 西贝股权质押"),
    ("news_07", "07 改装RTX5090"),
    ("news_08", "08 华为HAIP平台"),
    ("news_09", "09 天关卫星拉索"),
    ("news_10", "10 钟南山肺结节"),
    ("news_11", "11 智谱ZCode整改"),
    ("news_12", "12 酒店长租公寓"),
    ("news_13", "13 阿里语音模型"),
    ("news_14", "14 英国返还文物"),
    ("interactive", "互动话题·AI变笨"),
    ("pick", "每期精选·fmhy"),
    ("econ_slide_1", "聊经济01·开场"),
    ("econ_slide_2", "聊经济02·真假摔"),
    ("econ_slide_3", "聊经济03·情绪杀"),
    ("econ_slide_4", "聊经济04·价值锚定"),
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


def main():
    date = sys.argv[1]
    out_name = sys.argv[2] if len(sys.argv) > 2 else "contact_sheet.png"
    img_dir = os.path.join(BASE, "output", "weekly", date, "images")
    out_path = os.path.join(BASE, "output", "weekly", date, out_name)

    items = [(stem, label, os.path.join(img_dir, stem + ".jpg")) for stem, label in ORDER
             if os.path.exists(os.path.join(img_dir, stem + ".jpg"))]
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
    print(f"[contact_sheet_weekly] ✅ 已生成 {out_path}（{len(items)}/{len(ORDER)} 张，网格 {cols}x{rows}）")
    missing = [stem for stem, _ in ORDER if not os.path.exists(os.path.join(img_dir, stem + ".jpg"))]
    if missing:
        print(f"[contact_sheet_weekly] ⚠️ 缺图: {missing}")


if __name__ == "__main__":
    main()
