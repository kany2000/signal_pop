#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Signal Pop 封面生成脚本 — 生成 1920x1080 标准 16:9 封面
用法: python gen_cover.py [日期] [期数] [输出路径]
示例: python gen_cover.py 2026.07.01 7 /home/kan/shared/her2home/video_20260701.png
"""

import sys
from datetime import datetime
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("❌ 需安装 Pillow: pip install pillow")
    sys.exit(1)


def generate_cover(date_str: str, episode: int, output_path: str, news_items: list = None):
    """生成 1920x1080 16:9 标准封面"""
    img = Image.new('RGB', (1920, 1080), color='#0A1628')
    draw = ImageDraw.Draw(img)

    # 背景渐变
    for y in range(1080):
        ratio = y / 1080
        r = int(10 + ratio * 30)
        g = int(22 + ratio * 40)
        b = int(40 + ratio * 60)
        draw.line([(0, y), (1920, y)], fill=(r, g, b))

    # 右上角光晕装饰
    for i in range(50, 0, -1):
        alpha = int(30 * (1 - i/50))
        draw.ellipse([1700-i*10, -i*10, 2100+i*10, 400+i*10], outline=(0, 180, 255, alpha))

    # 左下角装饰线条
    draw.line([(100, 980), (400, 980)], fill='#00B4FF', width=4)
    draw.line([(100, 980), (100, 780)], fill='#00B4FF', width=4)

    # 字体加载 — 优先 NotoSansCJK（支持中文），回退 DejaVu
    NOTO_BOLD = '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'
    NOTO_REG  = '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
    DEV_BOLD  = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
    DEV_REG   = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'

    def load_font(path, fallback, size):
        try:
            return ImageFont.truetype(path, size)
        except:
            try:
                return ImageFont.truetype(fallback, size)
            except:
                return ImageFont.load_default()

    title_font = load_font(NOTO_BOLD, DEV_BOLD, 84)
    sub_font = load_font(NOTO_REG, DEV_REG, 36)
    date_font = load_font(NOTO_BOLD, DEV_BOLD, 48)
    content_font = load_font(NOTO_REG, DEV_REG, 28)
    num_font = load_font(NOTO_BOLD, DEV_BOLD, 20)

    # 主标题 - 左上
    draw.text((120, 140), "隔天信号弹", fill='#FFFFFF', font=title_font, stroke_width=2, stroke_fill='#00B4FF')
    draw.text((120, 250), "Signal Pop · 每日硬核资讯", fill='#00E5FF', font=sub_font)

    # 日期标签 - 右上
    draw.text((1920 - 320, 140), date_str, fill='#FFFFFF', font=date_font, anchor='rt')
    draw.text((1920 - 320, 210), f"周三 第 {episode} 期", fill='#88CCFF', font=sub_font, anchor='rt')

    # 默认新闻条目 (若未提供)
    if news_items is None:
        news_items = [
            "🌍 全球气候峰会达成 1.5°C 新协议",
            "🤖 G7 通过全球 AI 安全公约",
            "🔴 火星发现疑似微生物化石",
            "⚡ 固态电池突破 500Wh/kg",
            "🧮 量子计算机破解 RSA-2048",
            "💉 疫苗覆盖率创历史新高",
            "🚀 SpaceX 商业太空旅游首飞",
            "☀️ 可再生能源占比首超化石能源",
            "₿ FATF 统一加密货币监管",
            "🏆 诺贝尔奖提名档案解密",
        ]

    # 内容预览列表 - 左中
    for i, item in enumerate(news_items[:10]):
        y = 380 + i * 58
        circle_x, circle_y = 140, y + 14
        draw.ellipse([circle_x-18, circle_y-18, circle_x+18, circle_y+18], outline='#00B4FF', width=2)
        draw.text((circle_x, circle_y), str(i+1), fill='#00E5FF', font=num_font, anchor='mm')
        draw.text((190, y), item, fill='#E8F4FF', font=content_font)

    # 底部品牌行
    draw.line([(120, 1000), (1800, 1000)], fill='#00B4FF', width=1)
    draw.text((120, 1010), "隔天信号弹  ·  虾小图主播  ·  每周一三五 14:00 定时放送", fill='#6699CC', font=sub_font)

    # 右下角二维码占位
    qr_size = 120
    qr_x, qr_y = 1920-120-qr_size, 1080-120-qr_size
    draw.rectangle([qr_x, qr_y, qr_x+qr_size, qr_y+qr_size], outline='#00B4FF', width=2)
    draw.text((qr_x+qr_size/2, qr_y+qr_size/2), "扫码订阅", fill='#6699CC', font=sub_font, anchor='mm')

    # 保存
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, 'PNG', quality=95)
    print(f"✅ 封面已生成: {output_path} (1920x1080)")


if __name__ == "__main__":
    date_str = sys.argv[1] if len(sys.argv) > 1 else datetime.now().strftime("%Y.%m.%d")
    episode = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    output_path = sys.argv[3] if len(sys.argv) > 3 else f"/home/kan/shared/her2home/video_{datetime.now().strftime('%Y%m%d')}.png"
    generate_cover(date_str, episode, output_path)