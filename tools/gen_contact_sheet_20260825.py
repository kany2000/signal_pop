#!/usr/bin/env python3
"""20260825 审图拼图：含 opening_bg / 00~15 / ending_bg 全部 18 张，带标签。"""
import os
from PIL import Image, ImageDraw, ImageFont

BASE = "E:/projects/signal_pop"
DATE = "20260825"
IMG_DIR = os.path.join(BASE, "output", "daily", DATE, "images")
OUT = os.path.join(BASE, "output", "daily", DATE, "contact_sheet.png")

LABELS = {
    "opening_bg": "开场背景",
    "00": "历史上的今天",
    "01": "01 OpenAI Codex",
    "02": "02 阿里配售",
    "03": "03 夜间旅游",
    "04": "04 加拿大关税",
    "05": "05 中国机器人",
    "06": "06 低空经济",
    "07": "07 扶老人无过错",
    "08": "08 宜宾地震",
    "09": "09 羽球男双",
    "10": "10 多晶硅关税",
    "11": "11 英伟达Groq3",
    "12": "12 奔县游",
    "13": "13 早稻2817万",
    "14": "14 Win11技巧",
    "15": "15 记忆层协作",
    "ending_bg": "结尾背景",
}

def find_font(size):
    for c in ["C:/Windows/Fonts/msyhbd.ttc", "C:/Windows/Fonts/msyh.ttc",
              "C:/Windows/Fonts/simhei.ttf", "C:/Windows/Fonts/simsun.ttc"]:
        if os.path.exists(c):
            try:
                return ImageFont.truetype(c, size)
            except Exception:
                continue
    return ImageFont.load_default()

# 固定顺序：开场背景 + 00~15 + 结尾背景
order = ["opening_bg"] + [f"{i:02d}" for i in range(0, 16)] + ["ending_bg"]
files = [(L, os.path.join(IMG_DIR, L + ".jpg")) for L in order if os.path.exists(os.path.join(IMG_DIR, L + ".jpg"))]

thumb_w, thumb_h = 640, 360
label_h = 40
cols = 3
rows = (len(files) + cols - 1) // cols
pad = 12
sheet_w = cols * thumb_w + (cols + 1) * pad
sheet_h = rows * (thumb_h + label_h) + (rows + 1) * pad

sheet = Image.new("RGB", (sheet_w, sheet_h), (24, 26, 30))
draw = ImageDraw.Draw(sheet)
font = find_font(24)

for idx, (lbl, f) in enumerate(files):
    r, c = divmod(idx, cols)
    x = pad + c * (thumb_w + pad)
    y = pad + r * (thumb_h + label_h + pad)
    im = Image.open(f).convert("RGB").resize((thumb_w, thumb_h), Image.LANCZOS)
    sheet.paste(im, (x, y))
    draw.rectangle([x, y, x + thumb_w, y + label_h], fill=(0, 0, 0))
    draw.text((x + 12, y + 7), LABELS.get(lbl, lbl), fill=(255, 215, 0), font=font)

sheet.save(OUT, quality=90)
print(f"[contact_sheet] ✅ {OUT}（{len(files)} 张，网格 {cols}x{rows}）")
