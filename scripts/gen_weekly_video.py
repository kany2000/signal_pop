#!/usr/bin/env python3
"""Generate video for weekly special — 15 news items, weekend edition"""
import sys, os, json, re, subprocess, wave
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, timedelta

# === CONFIG ===
DATE = "20260731"
PUB_DT = datetime.strptime(DATE, "%Y%m%d") + timedelta(days=1)
PUB_DATE = PUB_DT.strftime("%Y%m%d")
PUB_DATE_FMT = f"{PUB_DATE[:4]}年{PUB_DATE[4:6]}月{PUB_DATE[6:8]}日"
PUB_DATE_SHORT = f"{PUB_DATE[:4]}.{PUB_DATE[4:6]}.{PUB_DATE[6:8]}"
PUB_WEEKDAY = ["星期一","星期二","星期三","星期四","星期五","星期六","星期日"][PUB_DT.weekday()]

PARSED = "E:/projects/signal_pop/output/parsed_weekly_20260731.json"
IMG_DIR = "E:/projects/signal_pop/output/daily_20260731/images"
AUDIO = "E:/projects/signal_pop/output/daily_20260731/audio/tts.wav"
SEGMENTS = "E:/projects/signal_pop/output/daily_20260731/audio/tts_segments.json"
OUTPUT = "E:/projects/signal_pop/output/daily_20260731/signal_pop_weekly_20260731.mp4"

FFMPEG = "C:/Users/Administrator/AppData/Local/Microsoft/WinGet/Packages/Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-8.1.2-full_build/bin/ffmpeg.exe"
FONT = "C:/Windows/Fonts/msyh.ttc"
FONT_BOLD = "C:/Windows/Fonts/msyhbd.ttc"
W, H = 1920, 1080
GOLD = (212, 175, 55)
WHITE = (240, 240, 250)
LIGHT_GREY = (200, 200, 210)

FRAME_DIR = "E:/projects/signal_pop/output/daily_20260731/frames"
os.makedirs(FRAME_DIR, exist_ok=True)

# Style - gold theme for weekend
STYLE = {'bar': (30, 85, 130), 'accent': GOLD, 'sub': LIGHT_GREY}

def fnt(size, bold=False):
    return ImageFont.truetype(FONT_BOLD if bold else FONT, size)

def wrap_text(text, font, max_w, draw, max_lines=10):
    lines = []
    for ch in text:
        if not lines:
            lines.append(ch)
            continue
        bb = draw.textbbox((0, 0), lines[-1] + ch, font=font)
        if bb[2] - bb[0] <= max_w:
            lines[-1] += ch
        else:
            lines.append(ch)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] = lines[-1][:-1] + '…'
    return lines

def draw_shadow(d, x, y, text, font, fill=WHITE, shadow=(0,0,0,160), anchor="mm", off=2):
    for ox in (-off, 0, off):
        for oy in (-off, 0, off):
            if ox == 0 and oy == 0: continue
            d.text((x+ox, y+oy), text, fill=shadow, font=font, anchor=anchor)
    d.text((x, y), text, fill=fill, font=font, anchor=anchor)

def dark_overlay(alpha=160):
    return Image.new('RGBA', (W, H), (0, 0, 0, alpha))

def make_gradient(left_w=1300):
    ov = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    for x in range(W):
        a = int(255 * (1 - x/left_w)) if x < left_w else max(0, int(60 * (1 - (x-left_w)/(W-left_w))))
        d.rectangle([x, 0, x, H], fill=(0, 0, 0, max(0, a)))
    for y in range(H-80, H):
        a = int(120 * (1 - (y-(H-80))/80))
        d.rectangle([0, y, W, y], fill=(0, 0, 0, a))
    return ov

def bottom_fade(fade_h=120):
    ov = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    for y in range(H-fade_h, H):
        a = int(180 * (1 - (y-(H-fade_h))/fade_h))
        d.rectangle([0, y, W, y], fill=(0, 0, 0, a))
    return ov

def load_bg(path):
    img = Image.open(path).convert('RGB').resize((W, H), Image.LANCZOS)
    return img

def draw_opening(bg_path, items):
    bg = load_bg(bg_path)
    drk = dark_overlay(160)
    bf = bottom_fade(180)
    img = Image.alpha_composite(bg.convert('RGBA'), drk)
    img = Image.alpha_composite(img, bf).convert('RGB')
    d = ImageDraw.Draw(img)

    # Gold lines
    for x in range(200, 1720):
        d.rectangle([x, 85, x+1, 90], fill=GOLD)
    for x in range(200, 1720):
        d.rectangle([x, 480, x+1, 482], fill=GOLD)

    # Emblem
    cx, cy = 960, 145
    d.ellipse([cx-18, cy-18, cx+18, cy+18], outline=GOLD, width=3)
    d.ellipse([cx-5, cy-5, cx+5, cy+5], fill=GOLD)

    draw_shadow(d, 960, 210, "隔天信号弹", fnt(72, True), GOLD)
    draw_shadow(d, 960, 280, "周末特别版", fnt(36), GOLD)
    draw_shadow(d, 960, 360, f"{PUB_DATE_FMT} · {PUB_WEEKDAY}", fnt(32), LIGHT_GREY)

    intro = ["欢迎收看本期信号弹周末特别版", f"本周精选 {len(items)} 条核心新闻"]
    y = 580
    for line in intro:
        draw_shadow(d, 960, y, line, fnt(36), WHITE, off=2)
        y += 50

    return img

def draw_slide(bg_path, item, idx, total):
    bg = load_bg(bg_path)
    grad = make_gradient(1300)
    img = Image.alpha_composite(bg.convert('RGBA'), grad).convert('RGB')
    d = ImageDraw.Draw(img)

    sec = item.get("section", "综合")
    tf, nf = fnt(22, True), fnt(20, True)
    tw = d.textbbox((0, 0), f"  {sec}  ", font=tf)
    tx, ty = 60, 60
    tw_w, tw_h = tw[2]-tw[0]+20, tw[3]-tw[1]+12
    d.rounded_rectangle([tx, ty, tx+tw_w, ty+tw_h], 6, fill=(30, 80, 160, 200))
    d.text((tx+10, ty+6), f"  {sec}  ", fill=WHITE, font=tf)

    nt = f"#{idx:02d}"
    nw = d.textbbox((0, 0), nt, font=nf)
    nx = tx + tw_w + 12
    nw_w, nw_h = nw[2]-nw[0]+16, nw[3]-nw[1]+8
    d.rounded_rectangle([nx, ty, nx+nw_w, ty+nw_h], 6, fill=(60, 60, 70, 180))
    d.text((nx+8, ty+4), nt, fill=LIGHT_GREY, font=nf)

    # Title
    ttl_f = fnt(46, True)
    ttl = wrap_text(item["title"], ttl_f, 1700, d, 3)
    if len(item["title"]) > sum(len(l) for l in ttl):
        ttl[-1] = ttl[-1][:-1] + '…'
    y = 140
    for line in ttl:
        draw_shadow(d, 60, y, line, ttl_f, WHITE, anchor="lt", off=2)
        y += 62

    # Body
    bd_f = fnt(26)
    bd = wrap_text(item.get("body", ""), bd_f, 1700, d, 6)
    if len(item.get("body", "")) > sum(len(l) for l in bd):
        bd[-1] = bd[-1][:-1] + '…'
    y += 30
    for line in bd:
        draw_shadow(d, 60, y, line, bd_f, LIGHT_GREY, anchor="lt", off=1)
        y += 38

    # Opinion
    if item.get("opinion"):
        op_f = fnt(22)
        op = wrap_text(f"主播观点：{item['opinion']}", op_f, 1700, d, 3)
        if len(item['opinion']) > sum(len(l) for l in op):
            op[-1] = op[-1][:-1] + '…'
        y += 20
        for line in op:
            draw_shadow(d, 60, y, line, op_f, GOLD, anchor="lt", off=1)
            y += 30

    # Footer
    ft_f = fnt(20)
    d.text((60, 1020), f"隔天信号弹 · {PUB_DATE_SHORT}", fill=LIGHT_GREY, font=ft_f)
    d.text((1860, 1020), f"{idx}/{total}", fill=LIGHT_GREY, font=ft_f, anchor="rt")
    return img

def draw_ending(bg_path):
    bg = load_bg(bg_path)
    drk = dark_overlay(180)
    bf = bottom_fade(180)
    img = Image.alpha_composite(bg.convert('RGBA'), drk)
    img = Image.alpha_composite(img, bf).convert('RGB')
    d = ImageDraw.Draw(img)

    for x in range(200, 1720):
        d.rectangle([x, 85, x+1, 90], fill=GOLD)
    for x in range(200, 1720):
        d.rectangle([x, 480, x+1, 482], fill=GOLD)

    cx, cy = 960, 145
    d.ellipse([cx-18, cy-18, cx+18, cy+18], outline=GOLD, width=3)
    d.ellipse([cx-5, cy-5, cx+5, cy+5], fill=GOLD)

    draw_shadow(d, 960, 210, "隔天信号弹", fnt(64, True), GOLD)
    draw_shadow(d, 960, 280, "周末特别版", fnt(36), GOLD)
    draw_shadow(d, 960, 360, "下期见", fnt(36), WHITE)
    draw_shadow(d, 960, 420, PUB_DATE_FMT, fnt(28), LIGHT_GREY)
    draw_shadow(d, 960, 650, "今天主播：图图", fnt(28), LIGHT_GREY)
    draw_shadow(d, 960, 690, "互动话题：您最关注哪条新闻？欢迎在评论区留言讨论！", fnt(26), WHITE)
    draw_shadow(d, 960, 730, "感谢您的关注，我们下期见~", fnt(28), LIGHT_GREY)
    return img

def main():
    with open(PARSED, 'r', encoding='utf-8') as f:
        items = json.load(f)
    print(f"Loaded {len(items)} items")

    # Load segment durations
    seg_durations = None
    if os.path.exists(SEGMENTS):
        with open(SEGMENTS) as f:
            seg_durations = json.load(f)
        print(f"Loaded {len(seg_durations)} segment durations")
    else:
        seg_durations = [10.0] + [8.0]*len(items) + [6.0]
        print("Using default durations")

    # Generate frames
    frames = []

    # Opening
    op_bg = os.path.join(IMG_DIR, "opening_bg.jpg")
    if os.path.exists(op_bg):
        print(f"Opening ({seg_durations[0]:.2f}s)...")
        frame = draw_opening(op_bg, items)
        p = os.path.join(FRAME_DIR, "opening.png")
        frame.save(p)
        frames.append((p, seg_durations[0]))

    # News slides
    for i, item in enumerate(items):
        dur = seg_durations[i+1]
        bg = os.path.join(IMG_DIR, f"{i+1:02d}.jpg")
        if not os.path.exists(bg):
            bg = op_bg
        print(f"Slide {i+1}/{len(items)} ({dur:.2f}s)...")
        frame = draw_slide(bg, item, i+1, len(items))
        p = os.path.join(FRAME_DIR, f"slide_{i+1:03d}.png")
        frame.save(p)
        frames.append((p, dur))

    # Ending
    en_bg = os.path.join(IMG_DIR, "ending_bg.jpg")
    if not os.path.exists(en_bg):
        en_bg = op_bg
    print(f"Ending ({seg_durations[-1]:.2f}s)...")
    frame = draw_ending(en_bg)
    p = os.path.join(FRAME_DIR, "ending.png")
    frame.save(p)
    frames.append((p, seg_durations[-1]))

    total_dur = sum(d for _, d in frames)
    print(f"Total: {total_dur:.2f}s ({len(frames)} frames)")

    # Build video using ffconcat (faster than filter_complex for static images)
    print(f"\nEncoding video...")
    concat_file = os.path.join(FRAME_DIR, "concat.txt")
    with open(concat_file, "w") as f:
        f.write("ffconcat version 1.0\n")
        for png, dur in frames:
            # Use absolute path with escaped backslashes
            abs_png = os.path.abspath(png).replace('\\', '/')
            f.write(f"file '{abs_png}'\nduration {dur:.3f}\n")

    # Step 1: Concatenate frames into video
    temp_video = OUTPUT.replace('.mp4', '_temp.mp4')
    cmd1 = [FFMPEG, '-y', '-f', 'concat', '-safe', '0', '-i', concat_file,
            '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '24',
            '-pix_fmt', 'yuv420p', '-r', '25',
            temp_video]
    r1 = subprocess.run(cmd1, capture_output=True, text=True, timeout=300)
    if r1.returncode != 0:
        print(f"FFmpeg concat error: {r1.stderr[-500:]}")
        sys.exit(1)

    # Step 2: Add audio
    cmd2 = [FFMPEG, '-y', '-i', temp_video, '-i', AUDIO,
            '-c:v', 'copy',
            '-c:a', 'aac', '-b:a', '128k',
            '-shortest', '-movflags', '+faststart',
            OUTPUT]
    r2 = subprocess.run(cmd2, capture_output=True, text=True, timeout=300)
    if r2.returncode != 0:
        print(f"FFmpeg audio error: {r2.stderr[-500:]}")
        sys.exit(1)

    os.remove(temp_video)

    size_mb = os.path.getsize(OUTPUT) / 1_048_576
    print(f"✅ {OUTPUT}")
    print(f"   Size: {size_mb:.1f}MB")
    print(f"   Duration: {total_dur:.1f}s")

    # Verify duration
    r2 = subprocess.run([FFMPEG, '-i', OUTPUT], capture_output=True, text=True, timeout=30)
    m = re.search(r'Duration: (\d+):(\d+):(\d+)\.(\d+)', r2.stderr)
    if m:
        h, mi, s, ms = int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4))
        vdur = h*3600 + mi*60 + s + ms/100
        print(f"   Video duration: {vdur:.2f}s")

if __name__ == "__main__":
    main()