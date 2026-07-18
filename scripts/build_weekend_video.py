#!/usr/bin/env python3
"""
Signal Pop 每日视频 v4 — 全屏背景 + 精准α叠加 + 按段时长对齐
"""
import os, sys, json, re, subprocess, wave
from PIL import Image, ImageDraw, ImageFont

# 使用周末特别版的日期
DATE = "20260717"
# Publication date = preparation date + 1 day (news → next day publish)
from datetime import datetime, timedelta
PUB_DATE_DT = datetime.strptime(DATE, "%Y%m%d") + timedelta(days=1)
PUB_DATE = PUB_DATE_DT.strftime("%Y%m%d")
PUB_DATE_FMT = f"{PUB_DATE[:4]}年{PUB_DATE[4:6]}月{PUB_DATE[6:8]}日"
PUB_DATE_SHORT = f"{PUB_DATE[:4]}.{PUB_DATE[4:6]}.{PUB_DATE[6:8]}"
PUB_WEEKDAY = ['星期一','星期二','星期三','星期四','星期五','星期六','星期日'][PUB_DATE_DT.weekday()]

IMG_DIR = f"/home/kan/shared/signal_pop/archive/img_{DATE}"
AUDIO = f"/home/kan/signal_pop/output/weekly/signal_pop_weekly_{DATE}.wav"
AUDIO_SEGMENTS_JSON = f"/home/kan/signal_pop/output/weekly/signal_pop_weekly_{DATE}_segments.json"
NEWS_FILE = f"/home/kan/shared/signal_pop/archive/signal_pop_weekly_special_{DATE}.txt"
OUTPUT = f"/home/kan/signal_pop/output/daily/signal_pop_daily_{DATE}_v4.mp4"
HER2HOME_VIDEO = f"/home/kan/shared/her2home/video_{DATE}.mp4"
HER2HOME_COVER = f"/home/kan/shared/her2home/cover_{DATE}.png"
FONT = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
FONT_BOLD = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
FRAME_DIR = "/tmp/frames_v4"
ffmpeg = "/home/kan/.hermes/hermes-agent/venv/lib/python3.11/site-packages/imageio_ffmpeg/binaries/ffmpeg-linux-x86_64-v7.0.2"
W, H = 1920, 1080
FPS = 30
# === 风格轮盘（每期自动换） ===
import hashlib
STYLE_SEED = int(hashlib.md5(DATE.encode()).hexdigest()[:8], 16)
STYLE_THEMES = [
    # (标签色, 强调色, 金色, 副标题色)
    { 'bar': (30, 85, 130), 'accent': (255, 215, 0), 'sub': (200, 200, 220) },  # 蓝白经典
    { 'bar': (180, 70, 30), 'accent': (255, 160, 40), 'sub': (220, 200, 180) },  # 橙黑科技
    { 'bar': (20, 100, 70), 'accent': (0, 210, 150), 'sub': (180, 220, 200) },  # 墨绿财经
    { 'bar': (80, 40, 120), 'accent': (200, 160, 255), 'sub': (210, 200, 220) },  # 紫金国际
]
STYLE = STYLE_THEMES[STYLE_SEED % len(STYLE_THEMES)]
print(f"[Style] Theme #{STYLE_SEED % len(STYLE_THEMES)} — bar={STYLE['bar']}")

OPENING_BG = f"{IMG_DIR}/opening_bg.jpg"

os.makedirs(FRAME_DIR, exist_ok=True)

# === 1. Font ===
def fnt(size, bold=False):
    try: return ImageFont.truetype(FONT_BOLD if bold else FONT, size)
    except: return ImageFont.load_default()

# === 2. Parse news ===
def parse_news(filepath):
    with open(filepath, encoding='utf-8') as f: text = f.read()
    # Split by "第N条" pattern — handles both blank-line-separated and continuous format
    items = re.split(r'(?=第\d+条[，,])', text)
    parsed = []
    for item in items:
        item = item.strip()
        if not item or item.startswith('以上是') or item.startswith('这里是') or item.startswith('欢迎收看'):
            continue
        lines = [l.strip() for l in item.split('\n') if l.strip()]
        if not lines: continue
        m = re.match(r'第(\d+)条[，,]\s*(.+)', lines[0])
        if not m: continue
        rest = m.group(2)
        idx = rest.find('。')
        if idx == -1: continue
        cat_name = rest[:idx]
        title = rest[idx+1:].strip()
        if not title.endswith('。'): title += '。'
        body = ' '.join(l for l in lines[1:] if l.strip()).strip()
        if body:
            if not body.endswith('。'): body += '。'
            body = body.replace('（', '').replace('）', '').replace('(', '').replace(')', '')
        cm = {'国内新闻':'国内民生','经济新闻':'经济财经','科技新闻':'科技前沿',
              '娱乐新闻':'文化娱乐','国际新闻':'国际综合'}
        cat = '热点'
        for k, v in cm.items():
            if k in cat_name: 
                cat = v
                break
        parsed.append((cat, title, body))
    return parsed

news_items = parse_news(NEWS_FILE)
print(f"Parsed {len(news_items)} news items")

# === 3. Load actual segment durations from TTS output ===
seg_durations = None
if os.path.exists(AUDIO_SEGMENTS_JSON):
    with open(AUDIO_SEGMENTS_JSON) as f:
        seg_durations = json.load(f)
    print(f"Loaded {len(seg_durations)} segment durations from TTS")
    for i, d in enumerate(seg_durations):
        print(f"  Seg {i}: {d:.2f}s")

# === 4. Helper: wrap text ===
def wrap_text(draw, text, font, max_w, max_lines=4):
    lines = []
    remaining = text
    while remaining and len(lines) < max_lines:
        for w in range(len(remaining), 0, -1):
            if draw.textlength(remaining[:w], font=font) <= max_w or w <= 2:
                lines.append(remaining[:w])
                remaining = remaining[w:]
                break
        else:
            lines.append(remaining); remaining = ''
    if remaining and len(lines) >= max_lines:
        lines[-1] = lines[-1][:-1] + '…'
    return lines

# === 5. Helper: load & fill background ===
def load_bg(path):
    """Load image, resize to fill 1920x1080 (center-crop if needed for aspect)"""
    try:
        img = Image.open(path).convert('RGB')
        iw, ih = img.size
        # Scale to cover 1920x1080
        scale = max(W/iw, H/ih)
        nw, nh = int(iw*scale), int(ih*scale)
        img = img.resize((nw, nh), Image.LANCZOS)
        # Center crop
        l = (nw - W) // 2
        t = (nh - H) // 2
        return img.crop((l, t, l+W, t+H))
    except:
        return Image.new('RGB', (W, H), (18, 18, 36))

# === 6. Dark gradient overlay (RGBA) — left side for text ===
def make_left_gradient():
    """Create smooth left-to-right dark gradient overlay"""
    ov = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    # Strong gradient: alpha 255→0 over full left half + fade
    for x in range(0, 1920, 10):
        # Piecewise: steep drop over 0-960, gentle fade 960-1920
        if x < 960:
            alpha = int(255 * (1 - x/960))
        else:
            alpha = int(60 * (1 - (x-960)/960))
        alpha = max(0, min(255, alpha))
        block_w = 10 if x < 1910 else 1920 - x
        d.rectangle([(x, 0), (x+block_w, H)], fill=(0, 0, 0, alpha))
    return ov

def make_bottom_gradient():
    """Bottom fade on RGBA"""
    ov = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    for y in range(H-200, H):
        a = int(120 * (1 - (H - y)/200))
        d.rectangle([(0, y), (W, y)], fill=(0, 0, 0, max(0, min(255, a))))
    return ov

# === 7. Opening card ===
def draw_opening():
    bg = load_bg(OPENING_BG)
    # Apply dark uniform overlay
    ov = Image.new('RGBA', (W, H), (0, 0, 0, 90))
    img = Image.alpha_composite(bg.convert('RGBA'), ov)
    # Add left + bottom gradients for text area
    img = Image.alpha_composite(img, make_left_gradient())
    img = Image.alpha_composite(img, make_bottom_gradient())
    draw = ImageDraw.Draw(img)
    
    # Gold lines
    draw.rectangle([(200, 340), (1720, 342)], fill=STYLE['accent'])
    draw.rectangle([(200, 580), (1720, 582)], fill=STYLE['accent'])
    
    # Emblem circle
    draw.ellipse([(930, 375), (990, 435)], fill=None, outline=STYLE['accent'], width=3)
    draw.ellipse([(945, 390), (975, 420)], fill=STYLE['accent'])
    
    draw.text((960, 465), "隔天信号弹", fill=STYLE['accent'], font=fnt(72, True), anchor="mm")
    draw.text((960, 525), "每日新闻播报", fill=STYLE['sub'], font=fnt(32), anchor="mm")
    draw.text((960, 620), f"{PUB_DATE_FMT} · {len(news_items)}条新闻", fill=STYLE['sub'], font=fnt(30), anchor="mm")
    
    # No intro text overlay — user wants clean opening card
    
    path = f"{FRAME_DIR}/opening.png"
    img.convert('RGB').save(path)
    return path

# === 8. News slide ===
def draw_news_slide(cat, title, body, num, total, img_path):
    bg = load_bg(img_path)
    # Left gradient for text
    img = Image.alpha_composite(bg.convert('RGBA'), make_left_gradient())
    # Bottom fade
    img = Image.alpha_composite(img, make_bottom_gradient())
    draw = ImageDraw.Draw(img)
    
    # Category tag
    ft = fnt(22)
    tw = int(draw.textlength(cat, font=ft)) + 30
    draw.rounded_rectangle([(60, 100), (60+tw, 136)], radius=18, fill=STYLE['bar'])
    draw.text((75, 118), cat, fill=(220, 235, 255), font=ft, anchor="lm")
    draw.text((80+tw, 118), f"#{num:02d}", fill=(180, 180, 200), font=fnt(20), anchor="lm")
    
    # Title
    ft2 = fnt(46, True)
    y = 170
    for line in wrap_text(draw, title, ft2, 1100, 3):
        draw.text((60, y), line, fill=(255, 255, 255), font=ft2)
        y += 54
    
    # Body with text shadow for readability
    if body:
        ft3 = fnt(24)
        yb = y + 12
        for line in wrap_text(draw, body, ft3, 1100, 4):
            # Draw shadow (thick for readability on bright backgrounds)
            for ox, oy in [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(1,1),(-1,1),(1,-1),(0,2)]:
                draw.text((60+ox, yb+oy), line, fill=(0, 0, 0, 100), font=ft3)
            draw.text((60, yb), line, fill=(240, 240, 250), font=ft3)
            yb += 32
    
    # Footer
    ff = fnt(22)
    draw.text((60, H-40), f"隔天信号弹 · {PUB_DATE_SHORT}", fill=(160, 160, 180), font=ff, anchor="lm")
    draw.text((W-60, H-40), f"{num}/{total}", fill=(160, 160, 180), font=ff, anchor="rm")
    
    path = f"{FRAME_DIR}/news_{num:02d}.png"
    img.convert('RGB').save(path)
    return path

# === 9. Ending card ===
def draw_ending():
    bg = load_bg(OPENING_BG)
    ov = Image.new('RGBA', (W, H), (0, 0, 0, 100))
    img = Image.alpha_composite(bg.convert('RGBA'), make_left_gradient())
    img = Image.alpha_composite(img, ov)
    draw = ImageDraw.Draw(img)
    
    draw.rectangle([(200, 390), (1720, 392)], fill=STYLE['accent'])
    draw.ellipse([(930, 425), (990, 485)], fill=None, outline=STYLE['accent'], width=3)
    draw.ellipse([(945, 440), (975, 470)], fill=STYLE['accent'])
    draw.text((960, 515), "隔天信号弹", fill=STYLE['accent'], font=fnt(64, True), anchor="mm")
    draw.text((960, 580), "下期见", fill=STYLE['sub'], font=fnt(36), anchor="mm")
    draw.rectangle([(200, 630), (1720, 632)], fill=STYLE['accent'])
    draw.text((960, 680), PUB_DATE_FMT, fill=STYLE['sub'], font=fnt(28), anchor="mm")
    
    path = f"{FRAME_DIR}/ending.png"
    img.convert('RGB').save(path)
    return path

# === 10. Generate all frames ===
print("\n=== Generating frames ===")
opening = draw_opening()
print("✅ Opening card")

if seg_durations and len(seg_durations) >= len(news_items) + 1:
    # Use actual segment durations from TTS
    # seg_durations[0]=intro, seg_durations[1..N]=news, no separate outro seg
    intro_dur = seg_durations[0]
    outro_dur = 3.0  # ending card time, trimmed from last news frame
    news_durs = list(seg_durations[1:1+len(news_items)])
    # Trim outro time from last news item so total video = total audio
    if news_durs[-1] > outro_dur + 1:
        news_durs[-1] = news_durs[-1] - outro_dur
    else:
        outro_dur = 0.5  # fallback: minimal outro
    print(f"Using TTS actual durations: intro={intro_dur:.1f}s, news={[f'{d:.1f}' for d in news_durs]}, outro={outro_dur:.1f}s")
elif seg_durations:
    # Has intro segment but not enough for all news — use intro from TTS, proportional for rest
    with wave.open(AUDIO, 'rb') as w:
        total_dur = w.getnframes() / w.getframerate()
    intro_dur = seg_durations[0]  # real intro duration from TTS
    outro_dur = 6.0
    news_chars = [len(t)+len(b) for _,t,b in news_items]
    news_total = total_dur - intro_dur - outro_dur
    news_durs = [news_total * c / sum(news_chars) for c in news_chars]
    print(f"Using partial TTS intro={intro_dur:.1f}s, proportional news: total={total_dur:.1f}s")
else:
    # Fallback: proportional based on char count
    with wave.open(AUDIO, 'rb') as w:
        total_dur = w.getnframes() / w.getframerate()
    intro_dur = 8.0; outro_dur = 6.0
    news_chars = [len(t)+len(b) for _,t,b in news_items]
    news_total = total_dur - intro_dur - outro_dur
    news_durs = [news_total * c / sum(news_chars) for c in news_chars]
    print(f"Using proportional timing: total={total_dur:.1f}s")

frames = [(opening, intro_dur)]
for i, (cat, title, body) in enumerate(news_items):
    img_path = f"{IMG_DIR}/{i+1:02d}.jpg"
    slide = draw_news_slide(cat, title, body, i+1, len(news_items), img_path)
    frames.append((slide, news_durs[i]))
    print(f"✅ News {i+1}/{len(news_items)} — {cat} ({news_durs[i]:.1f}s)")

ending = draw_ending()
frames.append((ending, outro_dur))
print(f"✅ Ending ({outro_dur:.1f}s)")

# Split total audio per segment for SRT sync check
for i, (_,dur) in enumerate(frames):
    print(f"  Frame {i}: {dur:.1f}s")

# === 11. Assemble video ===
print("\n=== Assembling video ===")
concat_file = "/tmp/concat_v4.txt"
with open(concat_file, "w") as f:
    f.write("ffconcat version 1.0\n")
    for path, dur in frames:
        f.write(f"file '{path}'\nduration {dur:.1f}\n")

cmd = [ffmpeg, '-y', '-f', 'concat', '-safe', '0', '-i', concat_file,
       '-i', AUDIO,
       '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '24',
       '-pix_fmt', 'yuv420p', '-r', str(FPS),
       '-c:a', 'aac', '-b:a', '192k',
       '-shortest', '-movflags', '+faststart', OUTPUT]
subprocess.run(cmd, check=True, timeout=600)

size_mb = os.path.getsize(OUTPUT) / 1_048_576
print(f"✅ {OUTPUT} ({size_mb:.1f}MB)")

# Copy to her2home
import shutil
shutil.copy2(OUTPUT, HER2HOME_VIDEO)
# Copy cover files (16:9 and 4:3)
for cover in [f"/home/kan/shared/her2home/cover_{DATE}.png", f"/home/kan/shared/her2home/cover_{DATE}_16x9.png"]:
    if os.path.exists(cover):
        pass  # already in place
print(f"✅ Copied to her2home")
print("\n🎉 Done!")