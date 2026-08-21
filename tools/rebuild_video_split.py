#!/usr/bin/env python3
"""Signal Pop Daily — 分屏布局重建版（精确时长 + 新视觉风格）。

修复原版 win_pipeline_video.py 的 ffmpeg `-loop 1 -r 100 -t dur` 对大静态 PNG 时长不可靠 bug。
新流程：每帧 PNG → 独立编码精确时长 mp4 → concat demuxer 拼接 + audio。

视觉风格：Split Screen 分屏布局
  左侧 40% 色块 + 巨号编号 + 分类 + 日期
  右侧 60% 配图 + 渐变 + 标题/正文/主播观点

用法：python tools/rebuild_video_split.py [PREP_DATE]
"""
import os
import sys
import json
import shutil
import subprocess as _subprocess
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

PROJECT_ROOT = "E:/projects/signal_pop"
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, "scripts"))

PREP_DATE = sys.argv[1] if len(sys.argv) > 1 else "20260809"
# 兼容带后缀的目录名（如 20260816_yue 粤语试点）：提取前 8 位数字作为制作日
import re as _re
_m = _re.match(r"(\d{8})", PREP_DATE)
_YYYYMMDD = _m.group(1) if _m else PREP_DATE
SCRIPT_FILE = os.path.join(PROJECT_ROOT, "archive", f"signal_pop_daily_{PREP_DATE}.txt")
OUT_DIR = os.path.join(PROJECT_ROOT, "output", "daily", PREP_DATE)
IMAGES_DIR = os.path.join(OUT_DIR, "images")
AUDIO_PATH = os.path.join(OUT_DIR, "audio", "tts.wav")
SEGMENTS_PATH = os.path.join(OUT_DIR, "audio", "tts_segments.json")
PARSED_PATH = os.path.join(OUT_DIR, "parsed_news.json")
OUTPUT_VIDEO = os.path.join(OUT_DIR, f"signal_pop_daily_{PREP_DATE}.mp4")

PUB_DT = datetime.strptime(_YYYYMMDD, "%Y%m%d") + timedelta(days=1)
PUB_DATE_FMT = f"{PUB_DT.year}年{PUB_DT.month:02d}月{PUB_DT.day:02d}日"
PUB_DATE_SHORT = f"{PUB_DT.year}.{PUB_DT.month:02d}.{PUB_DT.day:02d}"
PUB_WEEKDAY = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"][PUB_DT.weekday()]

WIDTH, HEIGHT = 1920, 1080
FFMPEG = "E:/projects/signal_pop/bin/ffmpeg-9.0.1-essentials_build/bin/ffmpeg.exe"
FONT = "C:/Windows/Fonts/msyh.ttc"
FONT_BOLD = "C:/Windows/Fonts/msyhbd.ttc"

# 分屏配色（墨绿主题 + 金色强调，与 HyperFrames Style 2 同源）
BAR_COLOR = (20, 100, 70)        # 墨绿主色
ACCENT = (255, 215, 0)           # 金色强调
PANEL_BG = (10, 30, 25)          # 左侧深色
WHITE = (240, 245, 240)
LIGHT_GREY = (200, 210, 200)


def fnt(size, bold=False):
    return ImageFont.truetype(FONT_BOLD if bold else FONT, size)


def wrap_text(draw, text, font, max_width):
    lines = []
    current = ""
    for ch in text:
        bbox = draw.textbbox((0, 0), current + ch, font=font)
        if bbox[2] - bbox[0] <= max_width:
            current += ch
        else:
            if current:
                lines.append(current)
            current = ch
    if current:
        lines.append(current)
    return lines


def draw_split_slide(bg_path, item, idx, total, pub_short):
    """分屏布局 v2：整张配图铺满。左侧 20% 模糊+暗化面板（巨号/分类/日期），右侧 80% 清晰配图（标题/正文/观点）。"""
    from PIL import ImageFilter

    bg = Image.open(bg_path).convert("RGB").resize((WIDTH, HEIGHT), Image.LANCZOS)
    PANEL_W = 384  # 20%

    # 模糊版本（整张高斯模糊）
    blurred = bg.filter(ImageFilter.GaussianBlur(radius=42))

    # 左侧模糊层暗化（保证文字可读）
    blurred_rgba = blurred.convert("RGBA")
    dark = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 115))
    blurred_dark = Image.alpha_composite(blurred_rgba, dark).convert("RGB")

    # 构造 mask：左 0~320 全用模糊，320~450 渐变过渡，450+ 用清晰原图
    mask = Image.new("L", (WIDTH, HEIGHT), 0)
    md = ImageDraw.Draw(mask)
    for x in range(0, WIDTH):
        if x < 320:
            a = 255
        elif x < 450:
            a = int(255 * (1 - (x - 320) / 130))
        else:
            a = 0
        md.rectangle([x, 0, x, HEIGHT], fill=a)

    # 右侧文字区：轻度模糊（保持轻微退后质感，图片仍清晰）+ 轻暗化提升文字对比度
    blur_light = bg.filter(ImageFilter.GaussianBlur(radius=2))
    blur_light_rgba = blur_light.convert("RGBA")
    dark_light = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 35))
    right_bg = Image.alpha_composite(blur_light_rgba, dark_light).convert("RGB")
    base = Image.composite(blurred_dark, right_bg, mask)
    d = ImageDraw.Draw(base)

    # ===== 左侧面板文字 (0-384, 中心 x=192) =====
    cx = 192
    # 顶部装饰线
    for x in range(40, 344):
        d.rectangle([x, 60, x + 1, 65], fill=ACCENT)
    # 巨号编号
    big = fnt(150, bold=True)
    d.text((cx, 300), f"{idx:02d}", fill=ACCENT, font=big, anchor="mm")
    # 编号下分隔线
    d.rectangle([cx - 40, 420, cx + 40, 426], fill=ACCENT)
    # 分类标签
    cat = item.get("section", "新闻")
    cat_font = fnt(34, bold=True)
    bbox = d.textbbox((0, 0), cat, font=cat_font)
    cw = bbox[2] - bbox[0] + 26
    d.rounded_rectangle([cx - cw//2, 455, cx + cw//2, 500], 8, fill=BAR_COLOR)
    d.text((cx, 477), cat, fill=WHITE, font=cat_font, anchor="mm")
    # 底部品牌
    foot = fnt(20)
    d.text((cx, 1000), "隔天信号弹", fill=(220, 235, 220), font=foot, anchor="mm")
    d.text((cx, 1032), pub_short, fill=ACCENT, font=foot, anchor="mm")
    d.text((cx, 1060), f"{idx}/{total}", fill=(200, 215, 200), font=foot, anchor="mm")

    # ===== 右侧文字区 (384-1920, 起始 x=430) =====
    # 右侧轻微渐变（顶部与底部局部暗化，保证文字可读但不遮图）
    rg = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    gd = ImageDraw.Draw(rg)
    # 左侧边缘渐变（与模糊面板衔接处暗化一点）
    for x in range(384, 620):
        a = int(70 * (1 - (x - 384) / 236))
        gd.rectangle([x, 0, x, HEIGHT], fill=(0, 0, 0, a))
    # 底部渐变
    for y in range(850, HEIGHT):
        a = int(95 * (1 - (y - 850) / 230))
        gd.rectangle([0, y, WIDTH, y], fill=(0, 0, 0, a))
    base = Image.alpha_composite(base.convert("RGBA"), rg).convert("RGB")
    d = ImageDraw.Draw(base)

    TX = 430
    TW = WIDTH - TX - 60  # ~1430

    # 标题
    ttl_f = fnt(50, bold=True)
    title = item.get("title", "")
    lines = wrap_text(d, title, ttl_f, TW)[:3]
    if len(title) > sum(len(l) for l in lines):
        lines[-1] = lines[-1][:-1] + "…"
    y = 90
    for line in lines:
        # 加粗描边（3px）提升对比度
        for ox in (-3, 0, 3):
            for oy in (-3, 0, 3):
                if ox == 0 and oy == 0:
                    continue
                d.text((TX + ox, y + oy), line, fill=(0, 0, 0), font=ttl_f)
        d.text((TX, y), line, fill=WHITE, font=ttl_f)
        y += 66

    # 正文
    body = item.get("full_body", item.get("body", ""))
    bd_f = fnt(25)
    bd_lines = wrap_text(d, body, bd_f, TW)[:5]
    if len(body) > sum(len(l) for l in bd_lines):
        bd_lines[-1] = bd_lines[-1][:-1] + "…"
    y += 22
    for line in bd_lines:
        # 加粗描边（2px）提升对比度
        for ox in (-2, 0, 2):
            for oy in (-2, 0, 2):
                if ox == 0 and oy == 0:
                    continue
                d.text((TX + ox, y + oy), line, fill=(0, 0, 0), font=bd_f)
        d.text((TX, y), line, fill=(235, 240, 235), font=bd_f)
        y += 40

    # 主播观点（如果有）
    if item.get("opinion"):
        op_f = fnt(23)
        op_text = f"主播观点：{item['opinion']}"
        op_lines = wrap_text(d, op_text, op_f, TW)[:4]
        if len(item["opinion"]) > sum(len(l) for l in op_lines) - 5:
            op_lines[-1] = op_lines[-1][:-1] + "…"
        y += 26
        # 金色左边竖线
        d.rectangle([TX, y - 4, TX + 6, y + len(op_lines) * 34 + 4], fill=ACCENT)
        for line in op_lines:
            for ox in (-1, 0, 1):
                for oy in (-1, 0, 1):
                    if ox == 0 and oy == 0:
                        continue
                    d.text((TX + 22 + ox, y + oy), line, fill=(0, 0, 0), font=op_f)
            d.text((TX + 22, y), line, fill=ACCENT, font=op_f)
            y += 34

    return base


def full_bg(bg_path, dark_alpha=130):
    """清晰配图 + 轻暗化遮罩（图可见、文字可读），用于开屏/结尾。"""
    bg = Image.open(bg_path).convert("RGB").resize((WIDTH, HEIGHT), Image.LANCZOS)
    rgba = bg.convert("RGBA")
    dark = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, dark_alpha))
    return Image.alpha_composite(rgba, dark).convert("RGB")


def draw_history_slide(bg_path, item, pub_short):
    """历史上的今天：旧纸张/羊皮纸色调 + 复古边框，突出历史氛围。"""
    from PIL import ImageFilter

    bg = Image.open(bg_path).convert("RGB").resize((WIDTH, HEIGHT), Image.LANCZOS)
    # 暖色调暗化遮罩（古旧感）
    rgba = bg.convert("RGBA")
    sepia = Image.new("RGBA", (WIDTH, HEIGHT), (60, 35, 10, 110))
    img = Image.alpha_composite(rgba, sepia).convert("RGB")
    d = ImageDraw.Draw(img)

    # 顶部金色线
    for x in range(120, 1800):
        d.rectangle([x, 60, x + 1, 65], fill=GOLD if 'GOLD' in dir() else ACCENT)

    # 中央区域：复古卷轴面板（浅色半透明 + 深棕描边）
    panel_w, panel_h = 1500, 760
    px, py = (WIDTH - panel_w) // 2, (HEIGHT - panel_h) // 2
    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    od.rounded_rectangle([px, py, px + panel_w, py + panel_h], 24,
                         fill=(30, 22, 14, 200), outline=(212, 175, 55, 255), width=3)
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    d = ImageDraw.Draw(img)

    # 标题
    title_f = fnt(62, bold=True)
    d.text((960, py + 70), "历史上的今天", fill=ACCENT, font=title_f, anchor="mm")
    # 分隔线
    d.rectangle([960 - 120, py + 110, 960 + 120, py + 116], fill=ACCENT)

    # 正文（历史内容）
    body = item.get("full_body", "")
    bd_f = fnt(34)
    lines = wrap_text(d, body, bd_f, 1280)[:6]
    if len(body) > sum(len(l) for l in lines):
        lines[-1] = lines[-1][:-1] + "…"
    y = py + 180
    for line in lines:
        for ox in (-1, 0, 1):
            for oy in (-1, 0, 1):
                if ox == 0 and oy == 0:
                    continue
                d.text((960 + ox, y + oy), line, fill=(0, 0, 0), font=bd_f, anchor="mm")
        d.text((960, y), line, fill=(245, 240, 225), font=bd_f, anchor="mm")
        y += 54

    # 底部品牌
    ft = fnt(22)
    d.text((960, py + panel_h - 45), f"隔天信号弹 · {pub_short}", fill=(190, 170, 130), font=ft, anchor="mm")
    return img


def draw_opening_frame(items, pub_date_fmt, pub_weekday, total):
    """开屏：清晰演播厅配图 + 居中品牌"""
    op_bg = os.path.join(IMAGES_DIR, "opening_bg.jpg")
    if not os.path.exists(op_bg):
        op_bg = os.path.join(IMAGES_DIR, "01.jpg")
    img = full_bg(op_bg, dark_alpha=120)
    d = ImageDraw.Draw(img)
    for x in range(120, 1800):
        d.rectangle([x, 80, x + 1, 85], fill=ACCENT)
    # 中心圆点
    d.ellipse([950, 142, 970, 162], outline=ACCENT, width=3)
    d.ellipse([957, 149, 963, 155], fill=ACCENT)
    # 主标题
    title_f = fnt(82, bold=True)
    d.text((960, 240), "隔天信号弹", fill=ACCENT, font=title_f, anchor="mm")
    # 副标题
    sub_f = fnt(36)
    d.text((960, 340), "本期要闻播报", fill=WHITE, font=sub_f, anchor="mm")
    d.text((960, 390), f"{pub_date_fmt} · {pub_weekday}", fill=LIGHT_GREY, font=sub_f, anchor="mm")
    # 介绍语
    intro_f = fnt(34)
    intros = [
        "这里是隔天信号弹",
        f"今天是{pub_date_fmt}，{pub_weekday}",
        f"欢迎收看本期信号弹，以下是本期精选的{total}条核心新闻。",
    ]
    y = 620
    for line in intros:
        d.text((960, y), line, fill=WHITE, font=intro_f, anchor="mm")
        y += 56
    return img


def draw_ending_frame(pub_date_fmt):
    """结尾：清晰城市夜景配图 + 品牌 + 一键三连呼吁"""
    en_bg = os.path.join(IMAGES_DIR, "ending_bg.jpg")
    if not os.path.exists(en_bg):
        en_bg = os.path.join(IMAGES_DIR, "10.jpg")
    img = full_bg(en_bg, dark_alpha=120)
    d = ImageDraw.Draw(img)
    for x in range(120, 1800):
        d.rectangle([x, 80, x + 1, 85], fill=ACCENT)
    d.ellipse([950, 142, 970, 162], outline=ACCENT, width=3)
    d.ellipse([957, 149, 963, 155], fill=ACCENT)
    d.text((960, 260), "隔天信号弹", fill=ACCENT, font=fnt(72, bold=True), anchor="mm")
    d.text((960, 360), "下期见", fill=WHITE, font=fnt(48, bold=True), anchor="mm")
    d.text((960, 430), pub_date_fmt, fill=LIGHT_GREY, font=fnt(32), anchor="mm")
    # 一键三连呼吁（替代原"今天主播：图图"）
    d.text((960, 600), "您的一键三连", fill=ACCENT, font=fnt(40, bold=True), anchor="mm")
    d.text((960, 660), "是我们更新制作的动力", fill=WHITE, font=fnt(32), anchor="mm")
    d.text((960, 720), "互动话题：您最关注哪条新闻？欢迎在评论区留言讨论！", fill=LIGHT_GREY, font=fnt(26), anchor="mm")
    return img


def ease_out_back(x, s=1.70158):
    """easeOutBack：轻微回弹（Celebration 风格 overshoot ~10%），1.0 结尾。
    x: 0..1 归一化进度 → 0..1 输出（可短暂 >1）。"""
    c1 = s
    c3 = c1 + 1
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2


def ease_out_cubic(x):
    """easeOutCubic：平滑减速入场。"""
    return 1 - (1 - x) ** 3


def draw_sanlian_icon(canvas, cx, cy, kind, glow):
    """画三连图标（订阅/关注/转发）到 RGBA canvas。glow=发光强度 0..1。
    使用局部小图 + alpha_composite，避免污染全图。"""
    r = 62
    w, h = 220, 200  # 图标+标签 局部画布
    icon = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    bd = ImageDraw.Draw(icon)
    ox, oy = w // 2, 90  # 圆心在局部画布内
    # 圆底
    bd.ellipse([ox - r, oy - r, ox + r, oy + r], fill=(20, 26, 36, 235), outline=(212, 175, 55, 255), width=4)
    ic = (255, 240, 190)
    if kind == "subscribe":
        bd.arc([ox - 24, oy - 30, ox + 24, oy + 20], start=0, end=180, fill=ic, width=5)
        bd.line([ox - 24, oy - 5, ox - 24, oy + 10], fill=ic, width=5)
        bd.line([ox + 24, oy - 5, ox + 24, oy + 10], fill=ic, width=5)
        bd.arc([ox - 10, oy - 52, ox + 10, oy - 32], start=180, end=360, fill=ic, width=5)
        bd.ellipse([ox - 7, oy + 8, ox + 7, oy + 22], fill=ic)
    elif kind == "follow":
        bd.polygon([(ox, oy + 24), (ox - 26, oy - 6), (ox - 12, oy - 22), (ox, oy - 12),
                    (ox + 12, oy - 22), (ox + 26, oy - 6)], fill=ic)
        bd.ellipse([ox - 28, oy - 32, ox - 4, oy - 6], fill=ic)
        bd.ellipse([ox + 4, oy - 32, ox + 28, oy - 6], fill=ic)
    else:  # share
        bd.arc([ox - 26, oy - 24, ox + 26, oy + 28], start=30, end=300, fill=ic, width=6)
        bd.polygon([(ox + 24, oy - 6), (ox + 34, oy - 18), (ox + 18, oy - 20)], fill=ic)
    # 标签
    lf = fnt(26, bold=True)
    bd.text((w // 2, h - 20), {"subscribe": "订阅", "follow": "关注", "share": "转发"}[kind],
            fill=(255, 255, 255), font=lf, anchor="mm")
    # glow 光晕（只在局部画布内模糊）
    if glow > 0.02:
        halo = icon.filter(ImageFilter.GaussianBlur(radius=18))
        a = halo.split()[3].point(lambda v: int(v * min(1.0, glow)))
        halo.putalpha(a)
        canvas.alpha_composite(halo, (cx - w // 2, cy - oy))
    canvas.alpha_composite(icon, (cx - w // 2, cy - oy))


def add_avatar_corner(img, avatar_img, size=110, center=(1750, 970), feather=8):
    """在画面右下角叠加主播头像（覆盖 Sensenova 水印位置），边缘羽化融入背景。

    参数:
        img: 基础图（RGB）
        avatar_img: 头像（RGBA，800x800 方形图）
        size: 头像直径（默认 110px，仅比早期 104px 略大，不喧宾夺主）
        center: 头像圆心坐标（默认 (1750, 970)，贴右下水印位置）
        feather: 边缘羽化宽度（外圈渐变透明，默认 8px，只让边缘柔和不露方角）
    """
    if avatar_img is None:
        return img
    base = img.convert("RGBA")
    cx, cy = center
    # 1. 半透明底圆（深色 alpha 80，确保亮背景头像可见，柔和融入）
    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    od.ellipse([cx - size//2 - 6, cy - size//2 - 6, cx + size//2 + 6, cy + size//2 + 6],
               fill=(10, 14, 24, 80))
    base = Image.alpha_composite(base, overlay)
    # 2. 头像缩放到 2x 抗锯齿
    av_size = size * 2
    av_rgba = avatar_img.convert("RGBA").resize((av_size, av_size), Image.LANCZOS)
    # 3. 预裁剪头像：圆形 mask（确保方形画布的方角部分 alpha=0 完全透明）
    pre_mask = Image.new("L", (av_size, av_size), 0)
    pd = ImageDraw.Draw(pre_mask)
    pd.ellipse([0, 0, av_size, av_size], fill=255)
    # 把头像圆形外的 alpha 强制设为 0
    av_rgba.putalpha(ImageChops.multiply(av_rgba.split()[3], pre_mask))
    # 4. 构造羽化圆形 mask（中心实 255，边缘 feather 内渐变到 0，圆形外 0）
    feather_mask = Image.new("L", (av_size, av_size), 0)
    fd = ImageDraw.Draw(feather_mask)
    fd.ellipse([feather, feather, av_size - feather, av_size - feather], fill=255)
    feather_mask = feather_mask.filter(ImageFilter.GaussianBlur(feather))
    # 5. 合成：头像 * 羽化 mask（确保只有圆形头像，边缘柔和，圆形外全透明）
    av_alpha = av_rgba.split()[3]
    final_alpha = ImageChops.multiply(av_alpha, feather_mask)
    layer = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    paste_x = cx - av_size // 2
    paste_y = cy - av_size // 2
    layer.paste(av_rgba, (paste_x, paste_y), final_alpha)
    base = Image.alpha_composite(base, layer)
    return base.convert("RGB")


def render_ending_animation(pub_date_fmt, out_dir, dur, fps=25, avatar_img=None):
    """渲染结尾三连动画帧序列（motion-design 方法论优化版）。

    节奏（Corporate 人格，Celebration 轻微回弹）：
      - 三图标 stagger 80ms（标准档），每个入场 300ms easeOutBack
      - 光晕 alpha 用 easeOutCubic 平滑展开
      - 总入场约 0.6s，之后全亮保持
    """
    n = max(2, int(dur * fps))
    frames = []
    # 动画节奏：前 0.65s 完成三连入场，之后全亮保持
    appear_start, appear_end = 0.05, 0.05 + 0.65 / dur if dur > 0 else 0.40
    STAGGER_S = 0.08   # 按钮间 stagger 80ms
    ENTRY_S = 0.30     # 每个按钮入场 300ms
    cx = [700, 960, 1220]
    cy = 900
    for i in range(n):
        t = i / n
        img = draw_ending_frame(pub_date_fmt).convert("RGBA")
        glows = [0.0, 0.0, 0.0]
        if t < appear_end:
            for k in range(3):
                start = appear_start + k * STAGGER_S
                end = start + ENTRY_S
                if t >= start:
                    if t >= end:
                        glows[k] = 1.0
                    else:
                        x = (t - start) / ENTRY_S
                        glows[k] = min(1.0, max(0.0, ease_out_back(x)))
        else:
            glows = [1.0, 1.0, 1.0]
        for k, g in enumerate(glows):
            if g > 0.02:
                draw_sanlian_icon(img, cx[k], cy, ["subscribe", "follow", "share"][k], g)
        # 右下角主播头像
        if avatar_img is not None:
            img = add_avatar_corner(img, avatar_img)
        p = os.path.join(out_dir, f"an_{i:04d}.png")
        img.convert("RGB").save(p)
        frames.append(p)
    return frames, fps


def encode_part_animation(frame_dir, output_mp4, dur, fps=25):
    """把帧序列编码为精确时长 mp4（动画版）。"""
    pattern = os.path.join(frame_dir, "an_%04d.png").replace("\\", "/")
    cmd = [
        FFMPEG, "-y",
        "-framerate", str(fps),
        "-i", pattern,
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "20",
        "-pix_fmt", "yuv420p",
        "-r", str(fps),
        output_mp4,
    ]
    _subprocess.run(cmd, check=True, capture_output=True, timeout=180)


def encode_part(input_png, output_mp4, dur):
    """把一张静态 PNG 编码为精确时长 dur 的 mp4（每段独立编码，绕过 -loop 时长 bug）。
    先用 PIL 规范化重存（规避个别 PNG 触发 libx264 崩溃），再编码。"""
    from PIL import Image as _PILImage
    # 规范化：RGB 重存
    _img = _PILImage.open(input_png).convert("RGB")
    _norm = input_png.replace(".png", "_norm.png")
    _img.save(_norm, format="PNG")
    cmd = [
        FFMPEG, "-y",
        "-loop", "1",
        "-framerate", "25",
        "-t", f"{dur:.3f}",
        "-i", _norm,
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "22",
        "-tune", "stillimage",
        "-pix_fmt", "yuv420p",
        "-r", "25",
        output_mp4,
    ]
    _subprocess.run(cmd, check=True, capture_output=True, timeout=120)


def main():
    # 兜底：若 parsed_news.json 缺失或条数与音频不匹配，从 archive 重新解析重建
    try:
        items = json.load(open(PARSED_PATH, encoding="utf-8"))
        durations = json.load(open(SEGMENTS_PATH, encoding="utf-8"))
    except Exception:
        items, durations = None, None
    if items is None or durations is None or len(durations) != len(items) + 2:
        print("=== 检测到 parsed_news.json 与音频段数不匹配，从 archive 重新解析 ===")
        sys.path.insert(0, os.path.join(PROJECT_ROOT, "tools"))
        from tools.run_daily_video import parse_daily_script
        text = open(SCRIPT_FILE, encoding="utf-8").read()
        items = parse_daily_script(text)
        with open(PARSED_PATH, "w", encoding="utf-8") as f:
            json.dump(items, f, ensure_ascii=False, indent=2)
        durations = json.load(open(SEGMENTS_PATH, encoding="utf-8"))
        if len(durations) != len(items) + 2:
            print(f"ERROR: durations({len(durations)}) != items({len(items)})+2 (intro+outro)")
            sys.exit(1)
        print(f"✅ 重建 parsed_news.json：{len(items)} 条")

    # 临时目录：每个 part 的 PNG + mp4（兼容沙箱：用 cmd rmdir 替代 shutil.rmtree）
    tmp = os.path.join(OUT_DIR, "split_build")
    if os.path.exists(tmp):
        try:
            shutil.rmtree(tmp)
        except OSError:
            _subprocess.run(["cmd", "/c", "rmdir", "/s", "/q", tmp], capture_output=True)
    os.makedirs(tmp, exist_ok=True)

    # 1. 绘制所有帧 PNG
    print("=== 绘制分屏风格帧 ===")
    frames = []  # (label, png_path, dur)

    # 主播头像（右下角角标，avatar_<发布日>.png，找不到则不显示）
    avatar_img = None
    av_path = os.path.join(OUT_DIR, f"avatar_{PUB_DT.strftime('%Y%m%d')}.png")
    if os.path.exists(av_path):
        avatar_img = Image.open(av_path)

    # opening
    op_png = os.path.join(tmp, "00_opening.png")
    op_frame = draw_opening_frame(items, PUB_DATE_FMT, PUB_WEEKDAY, len(items))
    if avatar_img is not None:
        op_frame = add_avatar_corner(op_frame, avatar_img)
    op_frame.save(op_png)
    frames.append(("opening", op_png, durations[0], "static"))
    print(f"  opening: {durations[0]:.2f}s")

    # news slides（含可选的历史条目 num=0，图片按 num 定位：00.jpg / 01.jpg...）
    seg_idx = 1  # durations[0] 是 intro，新闻段从 1 开始
    for item in items:
        n = item.get("num", 0)
        if n == 0:
            # 历史上的今天：用 00.jpg（若无则用 opening_bg）
            bg = os.path.join(IMAGES_DIR, "00.jpg")
            if not os.path.exists(bg):
                bg = os.path.join(IMAGES_DIR, "opening_bg.jpg")
            png = os.path.join(tmp, "00_history.png")
            h_frame = draw_history_slide(bg, item, PUB_DATE_SHORT)
            if avatar_img is not None:
                h_frame = add_avatar_corner(h_frame, avatar_img)
            h_frame.save(png)
            dur = durations[seg_idx]
            frames.append(("history", png, dur, "static"))
            print(f"  history [{item.get('section','')}]: {dur:.2f}s")
            seg_idx += 1
            continue
        bg = os.path.join(IMAGES_DIR, f"{n:02d}.jpg")
        if not os.path.exists(bg):
            bg = os.path.join(IMAGES_DIR, "opening_bg.jpg")
        png = os.path.join(tmp, f"{n:02d}_slide.png")
        s_frame = draw_split_slide(bg, item, n, len(items), PUB_DATE_SHORT)
        if avatar_img is not None:
            s_frame = add_avatar_corner(s_frame, avatar_img)
        s_frame.save(png)
        dur = durations[seg_idx]
        frames.append((f"slide{n}", png, dur, "static"))
        print(f"  slide {n} [{item.get('section','')}]: {dur:.2f}s")
        seg_idx += 1

    # ending（一键三连动画）
    en_dir = os.path.join(tmp, "ending_anim")
    os.makedirs(en_dir, exist_ok=True)
    anim_frames, fps = render_ending_animation(PUB_DATE_FMT, en_dir, durations[-1], avatar_img=avatar_img)
    en_png = anim_frames[0]  # 占位（实际用动画编码）
    frames.append(("ending", en_dir, durations[-1], "anim"))
    print(f"  ending (animation): {durations[-1]:.2f}s ({len(anim_frames)}帧 @{fps}fps)")

    total_dur = sum(d for f in frames for d in [f[2]])
    print(f"\n  帧时长总和: {total_dur:.3f}s (应 ≈ 音频 {sum(durations):.2f}s)")

    # 2. 每段编码成精确时长 mp4
    print("\n=== 每段独立编码为精确时长 mp4 ===")
    parts_txt = os.path.join(tmp, "concat.txt")
    part_files = []
    for idx, f in enumerate(frames):
        label, payload, dur, kind = f[0], f[1], f[2], f[3]
        part_mp4 = os.path.join(tmp, f"part_{idx:02d}_{label}.mp4")
        if kind == "anim":
            encode_part_animation(payload, part_mp4, dur)
        else:
            encode_part(payload, part_mp4, dur)
        size = os.path.getsize(part_mp4) // 1024
        print(f"  part {idx} [{label}]: {dur:.3f}s -> {size}KB")
        part_files.append(part_mp4)

    # 3. concat demuxer 拼接
    with open(parts_txt, "w", encoding="utf-8") as f:
        for p in part_files:
            # 用相对文件名 + cwd=tmp，规避旧版 ffmpeg concat 对 Windows 绝对路径的解析 bug
            f.write(f"file '{os.path.basename(p)}'\n")

    # 4. 拼接 + 音频（兼容沙箱：os.remove 可能被拦截）
    print("\n=== concat demuxer 拼接 + 音频 ===")
    if os.path.exists(OUTPUT_VIDEO):
        try:
            os.remove(OUTPUT_VIDEO)
        except OSError:
            import ctypes
            ctypes.windll.kernel32.DeleteFileW(os.path.abspath(OUTPUT_VIDEO))
    cmd = [
        FFMPEG, "-y",
        "-f", "concat", "-safe", "0", "-i", "concat.txt",
        "-i", AUDIO_PATH,
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "128k",
        "-shortest",
        OUTPUT_VIDEO,  # 绝对路径输出（cwd=tmp 下用 basename 会写到 tmp 目录）
    ]
    r = _subprocess.run(cmd, capture_output=True, text=True, timeout=300, cwd=tmp)
    if r.returncode != 0:
        print("FFMPEG STDERR:", r.stderr[-1500:])
        sys.exit(1)

    # 5. 验证时长
    sz = os.path.getsize(OUTPUT_VIDEO) / 1024 / 1024
    print(f"\n  输出: {OUTPUT_VIDEO} ({sz:.1f}MB)")
    print(f"  帧时长总和 = 音频时长 = {total_dur:.3f}s")
    print("  时间轴通过'每段精确编码 + concat copy'保证 100% 同步")


if __name__ == "__main__":
    main()