#!/usr/bin/env python3
"""
Signal Pop 封面生成器 — 按 video_20260701.png 模板。
左 60% 暗灰网格文字栏 + 右 40% 主播竖图 + 四角青色 L 角标 + 标题青色辉光。
文字一律 PIL 叠加（AI 出图文字必糊）。复制后改 DATE / 文案 / seed。
依赖: PIL, 联网(pollinations 出人像)。
"""
import os
import datetime
from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO
import textwrap

# --- 配置 --- #
DATE = "20260717"  # 修改为新闻日期
TITLE = "周末特别版：科技巨头新动向与地缘政治风云"
SUBTITLE = "SpaceX星舰、AI智能体、超算互联、智谱ARR大涨、霍尔木兹海峡局势" # 副标题尽量简短
LOGO_PATH = os.path.expanduser("~/shared/her2home/signal_pop_logo_small.png")
FONT_PATH_TITLE = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
FONT_PATH_TEXT = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
OUTPUT_DIR = os.path.expanduser("~/shared/her2home")
TEMPLATE_16X9 = os.path.expanduser("~/shared/her2home/template_16x9.png")
TEMPLATE_4X3 = os.path.expanduser("~/shared/her2home/template_4x3.png")

# 定义主题色和字体大小
TEXT_COLOR = (255, 255, 255) # 白色
GLOW_COLOR = (0, 255, 255) # 青色辉光
FONT_SIZE_TITLE = 72 # 标题字体大小
FONT_SIZE_SUBTITLE = 36 # 副标题字体大小
FONT_SIZE_DATE = 30 # 日期字体大小

# Pollinations API for generating unique anchor images
# Ensure the date parameter is used to force a different image each time.
POLLINATIONS_API_URL = "https://image.pollinations.ai/prompt/cyberpunk%20female%20news%20anchor%20profile%20shot,%20futuristic%20newsroom,%20soft%20studio%20lighting,%20high%20detail,%20cyberpunk%20cityscape%20background,%20trending%20on%20artstation?width=400&height=1080&seed="

def fetch_anchor_image(seed):
    try:
        response = requests.get(f"{POLLINATIONS_API_URL}{seed}")
        response.raise_for_status()
        return Image.open(BytesIO(response.content)).convert("RGBA")
    except requests.exceptions.RequestException as e:
        print(f"Error fetching image from Pollinations: {e}")
        return None

def create_cover(aspect_ratio="16x9"):
    if aspect_ratio == "16x9":
        base_image_path = TEMPLATE_16X9
        title_pos = (50, 400)  # 标题位置 (x, y)
        subtitle_pos = (50, 500) # 副标题位置
        date_pos = (50, 60) # 日期位置
        anchor_x_offset = 1520 # 主播图片X轴偏移
        # Background texture (simplified, for demonstration)
        background_texture = Image.new("RGBA", (1920, 1080), (10, 10, 10, 255)) # Dark background
    elif aspect_ratio == "4x3":
        base_image_path = TEMPLATE_4X3
        title_pos = (50, 400) # 标题位置 (x, y)
        subtitle_pos = (50, 500) # 副标题位置
        date_pos = (50, 60) # 日期位置
        anchor_x_offset = 1000 # 主播图片X轴偏移
        background_texture = Image.new("RGBA", (1440, 1080), (10, 10, 10, 255)) # Dark background
    else:
        raise ValueError("Invalid aspect_ratio. Must be '16x9' or '4x3'.")

    # Use ImageDraw.textbbox for accurate text positioning
    try:
        font_title = ImageFont.truetype(FONT_PATH_TITLE, FONT_SIZE_TITLE)
        font_subtitle = ImageFont.truetype(FONT_PATH_TEXT, FONT_SIZE_SUBTITLE)
        font_date = ImageFont.truetype(FONT_PATH_TEXT, FONT_SIZE_DATE)
    except IOError:
        print("Error: Font file not found. Please check FONT_PATH_TITLE and FONT_PATH_TEXT.")
        return None

    # Generate a seed based on the DATE for consistent but unique images per day
    seed = int(datetime.datetime.strptime(DATE, "%Y%m%d").timestamp())
    anchor_image = fetch_anchor_image(seed)

    if anchor_image is None:
        print("Failed to fetch anchor image. Using a placeholder.")
        anchor_image = Image.new("RGBA", (400, 1080), (50, 50, 50, 255)) # Placeholder

    # Create a base image with the dark background texture
    base_img = background_texture.copy()
    draw = ImageDraw.Draw(base_img)

    # Load and paste logo
    if os.path.exists(LOGO_PATH):
        logo = Image.open(LOGO_PATH).convert("RGBA")
        base_img.paste(logo, (50, 120), logo) # Adjust logo position
    else:
        print(f"Warning: Logo not found at {LOGO_PATH}")

    # Wrap and draw title with glow effect
    wrapped_title = textwrap.fill(TITLE, width=20) # Adjust width as needed
    for offset in range(-2, 3): # Create a glow effect
        draw.text((title_pos[0] + offset, title_pos[1] + offset), wrapped_title, font=font_title, fill=GLOW_COLOR)
    draw.text(title_pos, wrapped_title, font=font_title, fill=TEXT_COLOR)

    # Wrap and draw subtitle
    wrapped_subtitle = textwrap.fill(SUBTITLE, width=30)
    draw.text(subtitle_pos, wrapped_subtitle, font=font_subtitle, fill=TEXT_COLOR)

    # Draw date
    draw.text(date_pos, f"隔天信号弹 · {DATE}", font=font_date, fill=TEXT_COLOR)

    # Paste anchor image (right side)
    if anchor_image:
        base_img.paste(anchor_image, (anchor_x_offset, 0), anchor_image)

    # Add L-shaped corner brackets (simplified)
    bracket_color = (0, 255, 255, 255) # Cyan
    bracket_thickness = 10
    bracket_length = 100

    # Top-left
    draw.line([(0, 0), (bracket_length, 0)], fill=bracket_color, width=bracket_thickness)
    draw.line([(0, 0), (0, bracket_length)], fill=bracket_color, width=bracket_thickness)
    # Top-right
    draw.line([(base_img.width - bracket_length, 0), (base_img.width, 0)], fill=bracket_color, width=bracket_thickness)
    draw.line([(base_img.width - bracket_thickness, 0), (base_img.width - bracket_thickness, bracket_length)], fill=bracket_color, width=bracket_thickness)
    # Bottom-left
    draw.line([(0, base_img.height), (bracket_length, base_img.height)], fill=bracket_color, width=bracket_thickness)
    draw.line([(0, base_img.height - bracket_length), (0, base_img.height)], fill=bracket_color, width=bracket_thickness)
    # Bottom-right
    draw.line([(base_img.width - bracket_length, base_img.height), (base_img.width, base_img.height)], fill=bracket_color, width=bracket_thickness)
    draw.line([(base_img.width - bracket_thickness, base_img.height - bracket_length), (base_img.width - bracket_thickness, base_img.height)], fill=bracket_color, width=bracket_thickness)

    return base_img

if __name__ == '__main__':
    # Generate 4x3 cover
    cover_4x3 = create_cover(aspect_ratio="4x3")
    if cover_4x3:
        output_path_4x3 = os.path.join(OUTPUT_DIR, f"cover_{DATE}.png")
        cover_4x3.save(output_path_4x3)
        print(f"✅ {output_path_4x3}")

    # Generate 16x9 cover
    cover_16x9 = create_cover(aspect_ratio="16x9")
    if cover_16x9:
        output_path_16x9 = os.path.join(OUTPUT_DIR, f"cover_{DATE}_16x9.png")
        cover_16x9.save(output_path_16x9)
        print(f"✅ {output_path_16x9}")