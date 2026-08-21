#!/usr/bin/env python3
"""
从 script.txt 生成 ASS 字幕 — 固定底部区域 + 动态字号
按文字量自动选字号（长文→小字），最多3行，底部居中
"""
import re, sys, os

CHARS_PER_SEC = 4.5
MAX_LINES = 3
BOTTOM_MARGIN = 40       # 距底边距离
SIDE_PAD = 80            # 左右留白
VIDEO_W = 1920
MAX_W = VIDEO_W - SIDE_PAD * 2


def fmt_ass_time(seconds):
    """ASS 时间格式: H:MM:SS.cc"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    cs = int((seconds - int(seconds)) * 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def best_fontsize(text):
    """按字数+宽度找最大字号，保证 wrap 后 ≤ MAX_LINES 行"""
    from PIL import Image, ImageDraw, ImageFont
    FONT = "C:/Windows/Fonts/msyhbd.ttc"
    draw = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    for fs in range(60, 20, -2):
        try:
            font = ImageFont.truetype(FONT, fs)
        except:
            font = ImageFont.load_default()
        lines, cur = [], ""
        for ch in text:
            if not cur:
                cur = ch
                continue
            bbox = draw.textbbox((0, 0), cur + ch, font=font)
            if bbox[2] - bbox[0] <= MAX_W:
                cur += ch
            else:
                lines.append(cur)
                cur = ch
        if cur:
            lines.append(cur)
        if len(lines) <= MAX_LINES:
            return fs
    return 22


def wrap_text_pil(text, fontsize):
    """PIL 换行，返回行列表"""
    from PIL import Image, ImageDraw, ImageFont
    FONT = "C:/Windows/Fonts/msyhbd.ttc"
    draw = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    try:
        font = ImageFont.truetype(FONT, fontsize)
    except:
        font = ImageFont.load_default()
    lines, cur = [], ""
    for ch in text:
        if not cur:
            cur = ch
            continue
        bbox = draw.textbbox((0, 0), cur + ch, font=font)
        if bbox[2] - bbox[0] <= MAX_W:
            cur += ch
        else:
            lines.append(cur)
            cur = ch
    if cur:
        lines.append(cur)
    return lines[:MAX_LINES]


def build_ass_header():
    """ASS 文件头（固定底部样式）"""
    return """[Script Info]
ScriptType: v4.00+
PlayDepth: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Microsoft YaHei,40,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,1,2,0,5,20,20,40,134

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def gen_ass(text_path, ass_path):
    with open(text_path, "r", encoding="utf-8") as f:
        lines = [l.strip() for l in f if l.strip()]

    segments = []

    # 找第一条新闻
    news_start = None
    for i, line in enumerate(lines):
        if re.match(r'^\d+[.、]', line) or re.match(r'^第\d+条', line):
            news_start = i
            break
    if news_start is None:
        print("Error: no news items found")
        return

    # Intro
    if news_start > 0:
        segments.append(("intro", " ".join(lines[:news_start])))

    # News items
    i = news_start
    while i < len(lines):
        line = lines[i]
        m = re.match(r'^(\d+)[.、]\s*(.*)', line)
        m2 = re.match(r'^第(\d+)条[，,、]\s*(.*)', line)
        if m or m2:
            num = int(m.group(1)) if m else int(m2.group(1))
            text = m.group(2) if m else m2.group(2)
            i += 1
            while i < len(lines):
                nxt = lines[i]
                if re.match(r'^\d+[.、]', nxt) or re.match(r'^第\d+条', nxt):
                    break
                text += " " + nxt
                i += 1
            segments.append((f"news_{num}", text))
        else:
            i += 1

    # Outro
    last_news = None
    for i, line in enumerate(lines):
        if re.match(r'^\d+[.、]', line) or re.match(r'^第\d+条', line):
            last_news = i
    if last_news is not None and last_news < len(lines) - 1:
        segments.append(("outro", " ".join(lines[last_news+1:])))

    # 生成 ASS
    current_time = 0.0
    ass_lines = [build_ass_header()]

    for seg_id, seg_text in segments:
        if not seg_text.strip():
            continue
        duration = max(1.5, len(seg_text) / CHARS_PER_SEC)
        start = current_time
        end = current_time + duration
        current_time = end

        fs = best_fontsize(seg_text)
        wrapped = wrap_text_pil(seg_text, fs)
        # ASS 多行用 \N 分隔，\fs 控制字号
        text = "\\N".join(wrapped)
        # 每段 override 字号（\fs 不支持小数，用整数）
        text = f"{{\\fs{fs}}}{text}"

        start_ts = fmt_ass_time(start)
        end_ts = fmt_ass_time(end)
        ass_lines.append(
            f"Dialogue: 0,{start_ts},{end_ts},Default,,0,0,0,,{text}"
        )
        print(f"  [{seg_id:>8}] {start:7.1f}-{end:7.1f}s ({len(seg_text):3d}字) -> 字号 {fs}px, {len(wrapped)}行")

    with open(ass_path, "w", encoding="utf-8") as f:
        f.write("\n".join(ass_lines))

    print(f"\nASS written: {ass_path}")
    print(f"Total duration: {current_time:.1f}s")


def main():
    if len(sys.argv) < 2:
        date = "20260705"
    else:
        date = sys.argv[1]

    base = "E:/projects/signal_pop"
    text_path = f"{base}/archive/signal_pop_daily_{date}.txt"
    ass_path = f"{base}/output/daily/{date}/signal_pop_daily_{date}.ass"

    if not os.path.exists(text_path):
        text_path = f"{base}/daily/data/script_{date}.txt"
        ass_path = f"{base}/daily/output/signal_pop_daily_{date}.ass"
    if not os.path.exists(text_path):
        print(f"Error: not found {text_path}")
        sys.exit(1)

    os.makedirs(os.path.dirname(ass_path), exist_ok=True)
    print(f"Reading: {text_path}")
    print(f"Output:  {ass_path}\n")
    gen_ass(text_path, ass_path)


if __name__ == "__main__":
    main()
