#!/usr/bin/env python3
"""Step 4: Build video — EXACT frame durations via ffmpeg filter_complex concat.

Uses -loop 1 -t N for each frame (sample-accurate), then concat filter.
NO concat demuxer rounding.
"""
import sys, os, json, subprocess, re, math
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont

WIDTH, HEIGHT = 1920, 1080
FFMPEG = "C:/Users/Administrator/AppData/Local/Microsoft/WinGet/Packages/Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-8.1.2-full_build/bin/ffmpeg.exe"

FONT = "C:/Windows/Fonts/msyh.ttc"
FONT_BOLD = "C:/Windows/Fonts/msyhbd.ttc"

GOLD = (212, 175, 55)
WHITE = (240, 240, 250)
LIGHT_GREY = (200, 200, 210)


def fnt(size, bold=False):
    return ImageFont.truetype(FONT_BOLD if bold else FONT, size)


def wrap_text(text, font, max_width, draw):
    lines = []
    for ch in text:
        if not lines:
            lines.append(ch)
            continue
        bbox = draw.textbbox((0, 0), lines[-1] + ch, font=font)
        if bbox[2] - bbox[0] <= max_width:
            lines[-1] += ch
        else:
            lines.append(ch)
    return lines


def draw_shadow(draw, x, y, text, font, fill=WHITE, shadow=(0, 0, 0, 160), anchor="mm", off=2):
    for ox in (-off, 0, off):
        for oy in (-off, 0, off):
            if ox == 0 and oy == 0:
                continue
            draw.text((x + ox, y + oy), text, fill=shadow, font=font, anchor=anchor)
    draw.text((x, y), text, fill=fill, font=font, anchor=anchor)


def make_gradient(width, height, left_w=1300):
    overlay = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    for x in range(width):
        a = int(255 * (1 - x / left_w)) if x < left_w else max(0, int(60 * (1 - (x - left_w) / (width - left_w))))
        a = max(0, a)
        draw.rectangle([x, 0, x, height], fill=(0, 0, 0, a))
    for y in range(height - 80, height):
        a = int(120 * (1 - (y - (height - 80)) / 80))
        draw.rectangle([0, y, width, y], fill=(0, 0, 0, a))
    return overlay


def dark_overlay(width, height, alpha=160):
    return Image.new('RGBA', (width, height), (0, 0, 0, alpha))


def bottom_fade(width, height, fade_h=120):
    o = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    d = ImageDraw.Draw(o)
    for y in range(height - fade_h, height):
        a = int(180 * (1 - (y - (height - fade_h)) / fade_h))
        d.rectangle([0, y, width, y], fill=(0, 0, 0, a))
    return o


def draw_opening(bg_path, items, pub_date_fmt, pub_weekday):
    bg = Image.open(bg_path).convert('RGB').resize((WIDTH, HEIGHT), Image.LANCZOS)
    drk = dark_overlay(WIDTH, HEIGHT, 160)
    bf = bottom_fade(WIDTH, HEIGHT, 180)
    bg = Image.alpha_composite(bg.convert('RGBA'), drk)
    bg = Image.alpha_composite(bg, bf).convert('RGB')
    d = ImageDraw.Draw(bg)

    for x in range(200, 1720):
        d.rectangle([x, 85, x + 1, 90], fill=GOLD)
    cx, cy = 960, 145
    d.ellipse([cx - 18, cy - 18, cx + 18, cy + 18], outline=GOLD, width=3)
    d.ellipse([cx - 5, cy - 5, cx + 5, cy + 5], fill=GOLD)
    draw_shadow(d, 960, 210, "隔天信号弹", fnt(72, True), GOLD)
    draw_shadow(d, 960, 295, "周末特别版 · 本周新闻汇总", fnt(32), LIGHT_GREY)
    draw_shadow(d, 960, 345, f"{pub_date_fmt} · {pub_weekday}", fnt(28), LIGHT_GREY)

    intro = ["这里是隔天信号弹，", f"今天是{pub_date_fmt}，{pub_weekday}。",
             f"欢迎收看本期周末特别版，以下是本周精选的{len(items)}条核心新闻。"]
    y = 665
    for line in intro:
        draw_shadow(d, 960, y, line, fnt(36), WHITE, off=2)
        y += 50
    return bg


def draw_slide(bg_path, item, idx, total, pub_short):
    bg = Image.open(bg_path).convert('RGB').resize((WIDTH, HEIGHT), Image.LANCZOS)
    grad = make_gradient(WIDTH, HEIGHT, 1300)
    bg = Image.alpha_composite(bg.convert('RGBA'), grad).convert('RGB')
    d = ImageDraw.Draw(bg)

    sec = item.get("section", "综合")
    tf, nf = fnt(22, True), fnt(20, True)
    tw = d.textbbox((0, 0), f"  {sec}  ", font=tf)
    tx, ty = 60, 60
    tw_w, tw_h = tw[2] - tw[0] + 20, tw[3] - tw[1] + 12
    d.rounded_rectangle([tx, ty, tx + tw_w, ty + tw_h], 6, fill=(30, 80, 160, 200))
    d.text((tx + 10, ty + 6), f"  {sec}  ", fill=WHITE, font=tf)

    nt = f"#{idx:02d}"
    nw = d.textbbox((0, 0), nt, font=nf)
    nx = tx + tw_w + 12
    nw_w, nw_h = nw[2] - nw[0] + 16, nw[3] - nw[1] + 8
    d.rounded_rectangle([nx, ty, nx + nw_w, ty + nw_h], 6, fill=(60, 60, 70, 180))
    d.text((nx + 8, ty + 4), nt, fill=LIGHT_GREY, font=nf)

    ttl_f = fnt(46, True)
    ttl = wrap_text(item["title"], ttl_f, 1700, d)[:3]
    if len(item["title"]) > sum(len(l) for l in ttl):
        ttl[-1] = ttl[-1][:-1] + "…"
    y = 140
    for line in ttl:
        draw_shadow(d, 60, y, line, ttl_f, WHITE, anchor="lt", off=2)
        y += 62

    bd_f = fnt(26)
    bd = wrap_text(item.get("full_body", ""), bd_f, 1700, d)[:6]
    if len(item.get("full_body", "")) > sum(len(l) for l in bd):
        bd[-1] = bd[-1][:-1] + "…"
    y += 30
    for line in bd:
        draw_shadow(d, 60, y, line, bd_f, LIGHT_GREY, anchor="lt", off=1)
        y += 38

    if item.get("opinion"):
        op_f = fnt(22)
        op = wrap_text(f"主播观点：{item['opinion']}", op_f, 1700, d)[:3]
        if len(item['opinion']) > sum(len(l) for l in op):
            op[-1] = op[-1][:-1] + "…"
        y += 20
        for line in op:
            draw_shadow(d, 60, y, line, op_f, GOLD, anchor="lt", off=1)
            y += 30

    ft_f = fnt(20)
    d.text((60, 1020), f"隔天信号弹 · {pub_short}", fill=LIGHT_GREY, font=ft_f)
    d.text((1860, 1020), f"{idx}/{total}", fill=LIGHT_GREY, font=ft_f, anchor="rt")
    return bg


def draw_ending(bg_path, pub_date_fmt):
    bg = Image.open(bg_path).convert('RGB').resize((WIDTH, HEIGHT), Image.LANCZOS)
    drk = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 140))
    bg = Image.alpha_composite(bg.convert('RGBA'), drk).convert('RGB')
    d = ImageDraw.Draw(bg)

    # Gold lines
    for x in range(200, 1720):
        d.rectangle([x, 85, x + 1, 90], fill=GOLD)
    cx, cy = 960, 145
    d.ellipse([cx - 18, cy - 18, cx + 18, cy + 18], outline=GOLD, width=3)
    d.ellipse([cx - 5, cy - 5, cx + 5, cy + 5], fill=GOLD)
    # Brand + date
    draw_shadow(d, 960, 210, "隔天信号弹", fnt(64, True), GOLD)
    draw_shadow(d, 960, 295, "下期见", fnt(36), WHITE)
    draw_shadow(d, 960, 350, pub_date_fmt, fnt(28), LIGHT_GREY)
    # Interactive text
    draw_shadow(d, 960, 600, "今天主播：图图", fnt(28), LIGHT_GREY)
    draw_shadow(d, 960, 640, "互动话题：您最关注哪条新闻？欢迎在评论区留言讨论！", fnt(26), WHITE)
    draw_shadow(d, 960, 680, "感谢您的关注，我们下期见~", fnt(28), LIGHT_GREY)
    return bg


def build_video(items, img_dir, audio_path, segments_path, output_path,
                pub_date_fmt, pub_weekday, pub_date_short):
    print(f"\nBuilding video ({len(items)} items)...")

    # Read segment durations
    seg_durations = None
    if segments_path and os.path.exists(segments_path):
        with open(segments_path) as f:
            seg_durations = json.load(f)
    if not seg_durations:
        seg_durations = [10.0] + [8.0] * len(items) + [6.0]

    # Frame list: (label, image_path, duration)
    frames_dir = os.path.join(os.path.dirname(output_path), "frames_exact")
    os.makedirs(frames_dir, exist_ok=True)

    frame_list = []

    # Opening
    op_bg = os.path.join(img_dir, "opening_bg.jpg")
    if os.path.exists(op_bg):
        print(f"  Opening frame ({seg_durations[0]:.2f}s)...")
        frame = draw_opening(op_bg, items, pub_date_fmt, pub_weekday)
        p = os.path.join(frames_dir, "opening.png")
        frame.save(p)
        frame_list.append(("opening", p, round(seg_durations[0], 3)))

    # News slides
    for i, item in enumerate(items):
        dur = seg_durations[i + 1]
        bg = os.path.join(img_dir, f"{i+1:02d}.jpg")
        if not os.path.exists(bg):
            bg = op_bg
        print(f"  Slide {i+1}/{len(items)} ({dur:.2f}s)...")
        frame = draw_slide(bg, item, i + 1, len(items), pub_date_short)
        p = os.path.join(frames_dir, f"slide_{i+1:03d}.png")
        frame.save(p)
        frame_list.append((f"slide_{i+1}", p, round(dur, 3)))

    # Ending
    en_bg = os.path.join(img_dir, "ending_bg.jpg")
    if not os.path.exists(en_bg):
        en_bg = op_bg
    print(f"  Ending frame ({seg_durations[-1]:.2f}s)...")
    frame = draw_ending(en_bg, pub_date_fmt)
    p = os.path.join(frames_dir, "ending.png")
    frame.save(p)
    frame_list.append(("ending", p, round(seg_durations[-1], 3)))

    total_dur = sum(d for _, _, d in frame_list)
    print(f"  Total: {total_dur:.3f}s ({len(frame_list)} frames)")

    # Build filter_complex command
    # Each frame: -loop 1 -r 100 -t DUR -i FRAME.png
    # Then concat filter, then fps=25 at output
    inputs = []
    filter_parts = []
    for idx, (label, png, dur) in enumerate(frame_list):
        inputs += ['-loop', '1', '-r', '100', '-t', str(dur), '-i', png]
        filter_parts.append(f'[{idx}:v]setpts=PTS-STARTPTS[v{idx}]')

    ci = ''.join(f'[v{i}]' for i in range(len(frame_list)))
    fc = ';'.join(filter_parts) + f';{ci}concat=n={len(frame_list)}:v=1:a=0[outv];[outv]fps=25[outv25]'

    cmd = [FFMPEG, '-y'] + inputs + ['-i', audio_path] + [
        '-filter_complex', fc,
        '-map', '[outv25]', '-map', f'{len(frame_list)}:a',
        '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '24',
        '-pix_fmt', 'yuv420p',
        '-c:a', 'aac', '-b:a', '128k',
        '-t', str(total_dur),
        output_path
    ]

    print(f"\n  Encoding...")
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=600)

    # Verify
    r2 = subprocess.run([FFMPEG, '-i', output_path], capture_output=True, text=True, timeout=30)
    m = re.search(r'Duration: (\d+):(\d+):(\d+)\.(\d+)', r2.stderr)
    if m:
        h, mi, s, ms = int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4))
        vdur = h * 3600 + mi * 60 + s + ms / 100
        print(f"  Video: {vdur:.2f}s, Audio: {total_dur:.2f}s, Diff: {abs(vdur-total_dur):.3f}s")

    print(f"  Output: {output_path}")
    return output_path


if __name__ == "__main__":
    import json
    items = json.load(open(sys.argv[1], 'r', encoding='utf-8'))
    build_video(items, sys.argv[2] if len(sys.argv)>2 else "E:/projects/signal_pop/output/weekly_20260717/images",
                sys.argv[3], sys.argv[3].replace('.wav','_segments.json'),
                sys.argv[4] if len(sys.argv)>4 else "E:/projects/signal_pop/output/weekly_20260717/ss.mp4",
                "2026年07月18日", "星期六", "2026.07.18")