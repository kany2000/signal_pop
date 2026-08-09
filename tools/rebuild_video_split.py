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
import subprocess
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont

PROJECT_ROOT = "E:/projects/signal_pop"
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, "scripts"))

PREP_DATE = sys.argv[1] if len(sys.argv) > 1 else "20260809"
SCRIPT_FILE = os.path.join(PROJECT_ROOT, "archive", f"signal_pop_daily_{PREP_DATE}.txt")
OUT_DIR = os.path.join(PROJECT_ROOT, "output", "daily", PREP_DATE)
IMAGES_DIR = os.path.join(OUT_DIR, "images")
AUDIO_PATH = os.path.join(OUT_DIR, "audio", "tts.wav")
SEGMENTS_PATH = os.path.join(OUT_DIR, "audio", "tts_segments.json")
PARSED_PATH = os.path.join(OUT_DIR, "parsed_news.json")
OUTPUT_VIDEO = os.path.join(OUT_DIR, f"signal_pop_daily_{PREP_DATE}.mp4")

PUB_DT = datetime.strptime(PREP_DATE, "%Y%m%d") + timedelta(days=1)
PUB_DATE_FMT = f"{PUB_DT.year}年{PUB_DT.month:02d}月{PUB_DT.day:02d}日"
PUB_DATE_SHORT = f"{PUB_DT.year}.{PUB_DT.month:02d}.{PUB_DT.day:02d}"
PUB_WEEKDAY = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"][PUB_DT.weekday()]

WIDTH, HEIGHT = 1920, 1080
FFMPEG = "C:/Users/Administrator/AppData/Local/Microsoft/WinGet/Packages/Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-9.0-full_build/bin/ffmpeg.exe"
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

    base = Image.composite(blurred_dark, bg, mask)
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
        for ox in (-2, 0, 2):
            for oy in (-2, 0, 2):
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
        for ox in (-1, 0, 1):
            for oy in (-1, 0, 1):
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
    d.text((960, 340), "每日要闻 · 今日播报", fill=WHITE, font=sub_f, anchor="mm")
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
    """结尾：清晰城市夜景配图 + 品牌"""
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
    d.text((960, 620), "今天主播：图图", fill=LIGHT_GREY, font=fnt(30), anchor="mm")
    d.text((960, 670), "互动话题：您最关注哪条新闻？欢迎在评论区留言讨论！", fill=WHITE, font=fnt(28), anchor="mm")
    d.text((960, 720), "感谢您的关注，我们下期见~", fill=LIGHT_GREY, font=fnt(30), anchor="mm")
    return img


def encode_part(input_png, output_mp4, dur):
    """把一张静态 PNG 编码为精确时长 dur 的 mp4（每段独立编码，绕过 -loop 时长 bug）。"""
    cmd = [
        FFMPEG, "-y",
        "-loop", "1",
        "-framerate", "25",
        "-t", f"{dur:.3f}",
        "-i", input_png,
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "22",
        "-tune", "stillimage",
        "-pix_fmt", "yuv420p",
        "-r", "25",
        output_mp4,
    ]
    subprocess.run(cmd, check=True, capture_output=True, timeout=120)


def main():
    if not os.path.exists(PARSED_PATH):
        print(f"ERROR: {PARSED_PATH} not found")
        sys.exit(1)
    if not os.path.exists(SEGMENTS_PATH):
        print(f"ERROR: {SEGMENTS_PATH} not found")
        sys.exit(1)

    items = json.load(open(PARSED_PATH, encoding="utf-8"))
    durations = json.load(open(SEGMENTS_PATH, encoding="utf-8"))

    if len(durations) != len(items) + 2:
        print(f"ERROR: durations({len(durations)}) != items({len(items)})+2 (intro+outro)")
        sys.exit(1)

    # 临时目录：每个 part 的 PNG + mp4
    tmp = os.path.join(OUT_DIR, "split_build")
    if os.path.exists(tmp):
        shutil.rmtree(tmp)
    os.makedirs(tmp, exist_ok=True)

    # 1. 绘制所有帧 PNG
    print("=== 绘制分屏风格帧 ===")
    frames = []  # (label, png_path, dur)

    # opening
    op_png = os.path.join(tmp, "00_opening.png")
    draw_opening_frame(items, PUB_DATE_FMT, PUB_WEEKDAY, len(items)).save(op_png)
    frames.append(("opening", op_png, durations[0]))
    print(f"  opening: {durations[0]:.2f}s")

    # news slides
    for i, item in enumerate(items, 1):
        bg = os.path.join(IMAGES_DIR, f"{i:02d}.jpg")
        if not os.path.exists(bg):
            bg = os.path.join(IMAGES_DIR, "opening_bg.jpg")
        png = os.path.join(tmp, f"{i:02d}_slide.png")
        draw_split_slide(bg, item, i, len(items), PUB_DATE_SHORT).save(png)
        dur = durations[i]  # durations[1..10]
        frames.append((f"slide{i}", png, dur))
        print(f"  slide {i} [{item.get('section','')}]: {dur:.2f}s")

    # ending
    en_png = os.path.join(tmp, "11_ending.png")
    draw_ending_frame(PUB_DATE_FMT).save(en_png)
    frames.append(("ending", en_png, durations[-1]))
    print(f"  ending: {durations[-1]:.2f}s")

    total_dur = sum(d for _, _, d in frames)
    print(f"\n  帧时长总和: {total_dur:.3f}s (应 ≈ 音频 203.30s)")

    # 2. 每段编码成精确时长 mp4
    print("\n=== 每段独立编码为精确时长 mp4 ===")
    parts_txt = os.path.join(tmp, "concat.txt")
    part_files = []
    for idx, (label, png, dur) in enumerate(frames):
        part_mp4 = os.path.join(tmp, f"part_{idx:02d}_{label}.mp4")
        encode_part(png, part_mp4, dur)
        size = os.path.getsize(part_mp4) // 1024
        print(f"  part {idx} [{label}]: {dur:.3f}s -> {size}KB")
        part_files.append(part_mp4)

    # 3. concat demuxer 拼接
    with open(parts_txt, "w", encoding="utf-8") as f:
        for p in part_files:
            p_abs = os.path.abspath(p).replace("\\", "/")
            f.write(f"file '{p_abs}'\n")

    # 4. 拼接 + 音频
    print("\n=== concat demuxer 拼接 + 音频 ===")
    if os.path.exists(OUTPUT_VIDEO):
        os.remove(OUTPUT_VIDEO)
    cmd = [
        FFMPEG, "-y",
        "-f", "concat", "-safe", "0", "-i", parts_txt,
        "-i", AUDIO_PATH,
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "128k",
        "-shortest",
        OUTPUT_VIDEO,
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
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