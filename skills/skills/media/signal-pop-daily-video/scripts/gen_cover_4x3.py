#!/usr/bin/env python3
"""Signal Pop 4:3 封面生成 (1440x1080) — 完整排版，非截图裁剪"""
import sys, re
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

NOTO_BOLD = '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'
NOTO_REG  = '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
DEV_BOLD  = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
DEV_REG   = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'

def load_font(path, fallback, size):
    try: return ImageFont.truetype(path, size)
    except:
        try: return ImageFont.truetype(fallback, size)
        except: return ImageFont.load_default()

def make_cover_4x3(date_str, output, news_items=None):
    W, H = 1440, 1080
    img = Image.new('RGB', (W, H), '#0A1628')
    draw = ImageDraw.Draw(img)

    # 渐变背景
    for y in range(H):
        r = int(10 + y/H * 30)
        g = int(22 + y/H * 40)
        b = int(40 + y/H * 60)
        draw.line([(0, y), (W, y)], fill=(r, g, b))

    # 右上光晕
    for i in range(40, 0, -1):
        draw.ellipse([W-200-i*8, -i*8, W+200+i*8, 300+i*8], outline=(0, 180, 255, int(25*(1-i/40))))

    # 左下装饰线
    draw.line([(80, 980), (350, 980)], fill='#00B4FF', width=3)
    draw.line([(80, 980), (80, 800)], fill='#00B4FF', width=3)

    title_font = load_font(NOTO_BOLD, DEV_BOLD, 72)
    sub_font   = load_font(NOTO_REG, DEV_REG, 28)
    date_font  = load_font(NOTO_BOLD, DEV_BOLD, 40)
    content_font = load_font(NOTO_REG, DEV_REG, 22)
    num_font   = load_font(NOTO_BOLD, DEV_BOLD, 18)

    draw.text((100, 120), "隔天信号弹", fill='#FFFFFF', font=title_font, stroke_width=2, stroke_fill='#00B4FF')
    draw.text((100, 210), "Signal Pop · 每日硬核资讯", fill='#00E5FF', font=sub_font)

    draw.text((W - 60, 120), date_str, fill='#FFFFFF', font=date_font, anchor='rt')
    draw.text((W - 60, 175), "周一 · 10条新闻", fill='#88CCFF', font=sub_font, anchor='rt')

    if news_items is None:
        news_items = [f"新闻 {i+1}" for i in range(10)]

    # 新闻列表 — 右外边距严格控制
    for i, item in enumerate(news_items[:10]):
        y = 330 + i * 56
        cx, cy = 100, y + 12
        draw.ellipse([cx-14, cy-14, cx+14, cy+14], outline='#00B4FF', width=2)
        draw.text((cx, cy), str(i+1), fill='#00E5FF', font=num_font, anchor='mm')
        max_w = 1200
        txt = item
        while draw.textlength(txt, font=content_font) > max_w:
            txt = txt[:-5]
        draw.text((138, y), txt, fill='#E8F4FF', font=content_font)

    # 底部品牌行 — 缩短文本避免右侧裁切
    draw.line([(80, 1000), (W-80, 1000)], fill='#00B4FF', width=1)
    draw.text((80, 1015), "隔天信号弹 · 虾小图主播 · 每周一三五放送", fill='#6699CC', font=sub_font)

    Path(output).parent.mkdir(parents=True, exist_ok=True)
    img.save(output, 'PNG', quality=95)
    print(f"4:3 cover: {output} ({W}x{H})")

if __name__ == '__main__':
    script_dir = Path('/home/kan/shared/signal_pop/archive')
    news_files = sorted(script_dir.glob('signal_pop_daily_*.txt'))
    news_items = None
    if news_files:
        text = news_files[-1].read_text()
        items = re.findall(r'第\d+条.*?。', text)
        if items:
            news_items = []
            for item in items[:10]:
                clean = re.sub(r'主播观点.*', '', item)
                clean = re.sub(r'视觉提示词.*', '', clean)
                if clean:
                    news_items.append(clean.strip())

    DATE = max(n.strip() for n in news_files[-1].read_text().split('\n') if n.strip())[:10] if False else ''
    # 从文件名取日期
    m = re.search(r'(\d{8})', news_files[-1].name)
    date_str = f"{m.group(1)[:4]}.{m.group(1)[4:6]}.{m.group(1)[6:8]}" if m else "2026.07.13"

    make_cover_4x3(
        date_str=date_str,
        output=f'/home/kan/shared/her2home/cover_{m.group(1)}_4x3.png' if m else '/home/kan/shared/her2home/cover_4x3.png',
        news_items=news_items
    )