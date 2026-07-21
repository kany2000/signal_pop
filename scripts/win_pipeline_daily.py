#!/usr/bin/env python3
"""Signal Pop Daily Pipeline — 每日信号弹视频制作"""
import sys, os, json, re, asyncio, io, struct, wave, subprocess, time, urllib.request, urllib.parse
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont

# ========== CONFIG ==========
SCRIPT_FILE = "E:/projects/signal_pop/archive/signal_pop_daily_20260721.txt"
DATE = "20260722"
OUTPUT_BASE = "E:/projects/signal_pop/output"

SCRIPTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, SCRIPTS_DIR)

# Parse date
PUB_DT = datetime.strptime(DATE, "%Y%m%d")
PUB_DATE = PUB_DT.strftime("%Y%m%d")
PUB_DATE_FMT = f"{PUB_DATE[:4]}年{PUB_DATE[4:6]}月{PUB_DATE[6:8]}日"
PUB_DATE_SHORT = f"{PUB_DATE[:4]}.{PUB_DATE[4:6]}.{PUB_DATE[6:8]}"
PUB_WEEKDAY = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"][PUB_DT.weekday()]

OUT_DIR = os.path.join(OUTPUT_BASE, f"daily_{DATE}")
IMAGES_DIR = os.path.join(OUT_DIR, "images")
AUDIO_DIR = os.path.join(OUT_DIR, "audio")
AUDIO_PATH = os.path.join(AUDIO_DIR, "tts.wav")
SEGMENTS_PATH = os.path.join(AUDIO_DIR, "tts_segments.json")
PARSED_PATH = os.path.join(OUT_DIR, "parsed_news.json")
OUTPUT_VIDEO = os.path.join(OUT_DIR, f"signal_pop_daily_{DATE}.mp4")

# Video constants
WIDTH, HEIGHT = 1920, 1080
FFMPEG = "C:/Users/Administrator/AppData/Local/Microsoft/WinGet/Packages/Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-8.1.2-full_build/bin/ffmpeg.exe"
FONT = "C:/Windows/Fonts/msyh.ttc"
FONT_BOLD = "C:/Windows/Fonts/msyhbd.ttc"
GOLD = (212, 175, 55)
WHITE = (240, 240, 250)
LIGHT_GREY = (200, 200, 210)

# Image generation
SENSENOVA_URL = "https://token.sensenova.cn/v1/images/generations"
SENSENOVA_KEY = "sk-Orks5KCFxdjhRSm7EEFY57UdykEWzWIQ"
SENSENOVA_MODEL = "sensenova-u1-fast"
SENSENOVA_SIZE = "2752x1536"
POLLINATIONS_TPL = "https://image.pollinations.ai/prompt/{q}?width=1216&height=832&seed={seed}&model=flux&nofeed=true"
NO_TEXT = ", no text, no words, no letters, no numbers, no characters, no typography, no signage, no labels, no captions, no UI, no writing, no screens with text, no charts, no data displays, no any text whatsoever, completely text-free image, no monitors with text, no screens showing data"

NEWS_PROMPTS = {
    "opening": "Chinese news broadcasting studio, professional television studio, blue and gold lighting, large LED screen, modern broadcast desk, cinematic, 8K" + NO_TEXT,
    "ending": "Chinese news broadcasting studio, warm lighting, wide shot, elegant, cinematic" + NO_TEXT,
}

SCENE_PROMPTS = {
    "ETF": "Chinese stock market trading floor, ETF fund charts, fund manager meeting, modern financial district" + NO_TEXT,
    "货币政策": "PBOC headquarters, Chinese central bank building, monetary policy meeting, financial data charts" + NO_TEXT,
    "A股": "Chinese stock market, red and green digital tickers, investors watching screens, trading terminal" + NO_TEXT,
    "Kimi": "AI supercomputer server room, neural network visualization, GPU chips, futuristic technology" + NO_TEXT,
    "光伏": "Solar panel field, photovoltaic power station, renewable energy, blue sky, green technology" + NO_TEXT,
    "券商": "Securities company headquarters, stock trading floor, financial professionals, modern office" + NO_TEXT,
    "关税": "US-Canada border, trade war concept, customs, shipping containers, flags" + NO_TEXT,
    "伊朗": "Middle East map, military operations, Strait of Hormuz, oil tankers, geopolitical tension" + NO_TEXT,
    "Paramount": "Hollywood film studio, entertainment industry, movie production, media company headquarters" + NO_TEXT,
    "英国": "10 Downing Street, UK Parliament, British politics, economic data" + NO_TEXT,
    "AI": "Artificial intelligence concept, neural network, data center, futuristic technology" + NO_TEXT,
    "新能源": "Wind turbines and solar panels, renewable energy landscape, green energy" + NO_TEXT,
    "美国": "United States, White House, American flag, Washington DC" + NO_TEXT,
}
DEFAULT_SCENE = "news event scene, documentary photography" + NO_TEXT


# ========== STEP 1: PARSE ==========
def parse_daily_script(text):
    """Parse daily signal pop format into structured items."""
    items = []
    current_section = "综合"

    for line in text.strip().split('\n'):
        line = line.strip()
        if not line:
            continue

        # Skip intro lines
        if line.startswith("这里是隔天信号弹") or line.startswith("欢迎收看"):
            continue
        if line.startswith("以上是本期"):
            continue

        # Detect news item: 第N条，[section]。标题：[title]。
        m = re.match(r'^第(\d+)条[，,]\s*(.+?)[。.]\s*标题[：:]\s*(.+?)[。.]$', line)
        if m:
            num = int(m.group(1))
            section = m.group(2).strip()
            title = m.group(3).strip()
            items.append({
                "num": num,
                "section": section,
                "title": title,
                "body": "",
                "opinion": "",
                "visual_prompt": "",
            })
            continue

        # 详情：[body]
        dm = re.match(r'^详情[：:]\s*(.+?)$', line)
        if dm and items:
            items[-1]["body"] = dm.group(1).strip()
            continue

        # 主播观点：[opinion]
        om = re.match(r'^主播观点[：:]\s*(.+?)$', line)
        if om and items:
            items[-1]["opinion"] = om.group(1).strip()
            continue

        # 视觉提示词：[prompt]
        vm = re.match(r'^视觉提示词[：:]\s*(.+?)$', line)
        if vm and items:
            items[-1]["visual_prompt"] = vm.group(1).strip()
            continue

    return items


# ========== STEP 2: IMAGES ==========
def make_prompt(item):
    """Generate visual prompt from news title/body."""
    txt = item["title"] + " " + item["body"]
    for kw, prompt in SCENE_PROMPTS.items():
        if kw in txt:
            return prompt
    return f"{item['title']}, news event scene, documentary photography" + NO_TEXT


def gen_sensenova(prompt, timeout=180):
    payload = json.dumps({"model": SENSENOVA_MODEL, "prompt": prompt, "size": SENSENOVA_SIZE, "n": 1}).encode()
    req = urllib.request.Request(
        SENSENOVA_URL, data=payload,
        headers={"Authorization": f"Bearer {SENSENOVA_KEY}", "Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        resp = json.loads(r.read())
    url = resp["data"][0]["url"]
    with urllib.request.urlopen(url, timeout=timeout) as img_r:
        return img_r.read()


def gen_pollinations(prompt, seed, timeout=120):
    q = urllib.parse.quote(prompt)
    url = POLLINATIONS_TPL.format(q=q, seed=seed)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def _save_image(img_bytes, out_path):
    img = Image.open(io.BytesIO(img_bytes))
    if img.mode == 'RGBA':
        img = img.convert('RGB')
    img = img.resize((1920, 1080), Image.LANCZOS)
    img.save(out_path, quality=85)


def download_image(prompt, seed, out_path, max_retries=5):
    for attempt in range(max_retries):
        try:
            print(f"  Sensenova (attempt {attempt+1})...")
            img_bytes = gen_sensenova(prompt, timeout=300)
            _save_image(img_bytes, out_path)
            print(f"  -> OK (Sensenova)")
            return True
        except Exception as e:
            print(f"  Sensenova failed: {e}")
        try:
            print(f"  Pollinations fallback...")
            img_bytes = gen_pollinations(prompt, seed + attempt)
            _save_image(img_bytes, out_path)
            print(f"  -> OK (Pollinations)")
            return True
        except Exception as e:
            print(f"  Pollinations failed: {e}")
        print(f"  Retry {attempt+1}/{max_retries}...")
        time.sleep(3)
    print(f"  FAILED, creating fallback")
    img = Image.new('RGB', (1920, 1080), (30, 40, 60))
    img.save(out_path, quality=85)
    return False


def gen_all_images(items, out_dir):
    os.makedirs(out_dir, exist_ok=True)

    # Opening
    op_path = os.path.join(out_dir, "opening_bg.jpg")
    if not os.path.exists(op_path):
        print(f"\n[Opening BG]")
        download_image(NEWS_PROMPTS["opening"], 42, op_path)
    else:
        print(f"  opening_bg.jpg exists, skip")

    # News items
    for i, item in enumerate(items, 1):
        fname = f"{i:02d}.jpg"
        out_path = os.path.join(out_dir, fname)
        if os.path.exists(out_path) and os.path.getsize(out_path) > 5000:
            print(f"  {fname} exists, skip")
            continue
        prompt = item.get("visual_prompt") or make_prompt(item)
        print(f"\n[{fname}] {item['title'][:40]}...")
        print(f"  Prompt: {prompt[:80]}...")
        download_image(prompt, item["num"] * 100, out_path)

    # Ending
    en_path = os.path.join(out_dir, "ending_bg.jpg")
    if not os.path.exists(en_path):
        print(f"\n[Ending BG]")
        download_image(NEWS_PROMPTS["ending"], 999, en_path)
    else:
        print(f"  ending_bg.jpg exists, skip")


# ========== STEP 3: TTS ==========
def build_segments(items):
    segs = []
    segs.append(("intro", f"这里是隔天信号弹，今天是{PUB_DATE_FMT}，{PUB_WEEKDAY}。欢迎收看本期信号弹，以下是本期精选的{len(items)}条核心新闻。"))
    for i, item in enumerate(items, 1):
        txt = f"第{i}条，{item['section']}。{item['title']}。{item['body']}"
        if item["opinion"]:
            txt += f".主播观点：{item['opinion']}"
        segs.append((f"item{i}", txt))
    segs.append(("outro", "以上是本期信号弹的全部内容。感谢您的关注，我们下期见~"))
    return segs


async def gen_one_segment(idx, label, text, voice, audio_dir, max_retries=3):
    mp3 = os.path.join(audio_dir, f'_s{idx:03d}.mp3')
    import aiohttp.resolver
    import edge_tts
    for attempt in range(max_retries):
        try:
            print(f"  [{label}] {len(text)}c...", end="", flush=True)
            conn = aiohttp.TCPConnector(
                resolver=aiohttp.resolver.ThreadedResolver(),
            )
            communicate = edge_tts.Communicate(text, voice, connector=conn, connect_timeout=30, receive_timeout=120)
            await communicate.save(mp3)
            print(f" OK")
            return (idx, label, mp3)
        except Exception as e:
            print(f" fail (attempt {attempt+1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(3)
            else:
                raise


async def gen_tts(items, output_wav):
    segs = build_segments(items)
    print(f"  TTS segments: {len(segs)}")

    audio_dir = os.path.dirname(output_wav)
    os.makedirs(audio_dir, exist_ok=True)

    VOICE = "zh-CN-XiaoxiaoNeural"
    # Serial execution to avoid 503 rate limiting
    results = []
    for i, (l, t) in enumerate(segs):
        r = await gen_one_segment(i, l, t, VOICE, audio_dir)
        results.append(r)
    results.sort(key=lambda x: x[0])

    durations = []
    all_pcm = bytearray()

    for idx, label, mp3 in results:
        wav = mp3.replace('.mp3', '.wav')
        subprocess.run([FFMPEG, '-y', '-i', mp3, '-acodec', 'pcm_s16le', '-ar', '24000', '-ac', '1', wav],
                       check=True, capture_output=True, timeout=60)
        os.remove(mp3)

        with wave.open(wav, 'rb') as w:
            rate = w.getframerate()
            raw = w.readframes(w.getnframes())

        samples = [int.from_bytes(raw[i:i+2], 'little', signed=True) for i in range(0, len(raw), 2)]

        # Trim silence
        threshold = 200
        start = 0
        for i in range(min(len(samples), int(rate * 0.5))):
            if abs(samples[i]) > threshold:
                start = i
                break
        end = len(samples)
        for i in range(len(samples) - 1, max(0, len(samples) - int(rate * 0.3)) - 1, -1):
            if abs(samples[i]) > threshold:
                end = i + 1
                break
        trimmed = samples[start:end]
        dur = len(trimmed) / rate
        for s in trimmed:
            all_pcm.extend(struct.pack('<h', s))
        print(f" {dur:.2f}s")
        durations.append(dur)
        os.remove(wav)

    with wave.open(output_wav, 'wb') as out:
        out.setnchannels(1)
        out.setsampwidth(2)
        out.setframerate(24000)
        out.writeframes(bytes(all_pcm))

    total = len(all_pcm) / 48000
    print(f"  Combined: {total:.2f}s")

    seg_path = output_wav.replace('.wav', '_segments.json')
    with open(seg_path, 'w') as f:
        json.dump(durations, f)
    print(f"  Saved: {len(durations)} segments")
    return output_wav, durations


# ========== STEP 4: VIDEO ==========
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


def dark_overlay(width, height, alpha=160):
    return Image.new('RGBA', (width, height), (0, 0, 0, alpha))


def bottom_fade(width, height, fade_h=120):
    o = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    d = ImageDraw.Draw(o)
    for y in range(height - fade_h, height):
        a = int(180 * (1 - (y - (height - fade_h)) / fade_h))
        d.rectangle([0, y, width, y], fill=(0, 0, 0, a))
    return o


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


def draw_opening(bg_path, items):
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
    draw_shadow(d, 960, 295, f"{PUB_DATE_FMT} · {PUB_WEEKDAY}", fnt(32), LIGHT_GREY)

    intro = ["这里是隔天信号弹", f"今天是{PUB_DATE_FMT}，{PUB_WEEKDAY}",
             f"欢迎收看本期信号弹，以下是本期精选的{len(items)}条核心新闻"]
    y = 665
    for line in intro:
        draw_shadow(d, 960, y, line, fnt(36), WHITE, off=2)
        y += 50
    return bg


def draw_slide(bg_path, item, idx, total):
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
    bd = wrap_text(item.get("body", ""), bd_f, 1700, d)[:6]
    if len(item.get("body", "")) > sum(len(l) for l in bd):
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
    d.text((60, 1020), f"隔天信号弹 · {PUB_DATE_SHORT}", fill=LIGHT_GREY, font=ft_f)
    d.text((1860, 1020), f"{idx}/{total}", fill=LIGHT_GREY, font=ft_f, anchor="rt")
    return bg


def draw_ending(bg_path):
    bg = Image.open(bg_path).convert('RGB').resize((WIDTH, HEIGHT), Image.LANCZOS)
    drk = dark_overlay(WIDTH, HEIGHT, 180)
    bf = bottom_fade(WIDTH, HEIGHT, 180)
    bg = Image.alpha_composite(bg.convert('RGBA'), drk)
    bg = Image.alpha_composite(bg, bf).convert('RGB')
    d = ImageDraw.Draw(bg)

    for x in range(200, 1720):
        d.rectangle([x, 85, x + 1, 90], fill=GOLD)
    cx, cy = 960, 145
    d.ellipse([cx - 18, cy - 18, cx + 18, cy + 18], outline=GOLD, width=3)
    d.ellipse([cx - 5, cy - 5, cx + 5, cy + 5], fill=GOLD)
    draw_shadow(d, 960, 210, "隔天信号弹", fnt(64, True), GOLD)
    draw_shadow(d, 960, 295, "下期见", fnt(36), WHITE)
    draw_shadow(d, 960, 350, PUB_DATE_FMT, fnt(28), LIGHT_GREY)
    draw_shadow(d, 960, 650, "今天主播：图图", fnt(28), LIGHT_GREY)
    draw_shadow(d, 960, 690, "互动话题：您最关注哪条新闻？欢迎在评论区留言讨论！", fnt(26), WHITE)
    draw_shadow(d, 960, 730, "感谢您的关注，我们下期见~", fnt(28), LIGHT_GREY)
    return bg


def build_video(items, img_dir, audio_path, segments_path, output_path):
    print(f"\nBuilding video ({len(items)} items)...")

    seg_durations = None
    if segments_path and os.path.exists(segments_path):
        with open(segments_path) as f:
            seg_durations = json.load(f)
    if not seg_durations:
        seg_durations = [10.0] + [8.0] * len(items) + [6.0]

    frames_dir = os.path.join(os.path.dirname(output_path), "frames_exact")
    os.makedirs(frames_dir, exist_ok=True)
    frame_list = []

    op_bg = os.path.join(img_dir, "opening_bg.jpg")
    if os.path.exists(op_bg):
        print(f"  Opening frame ({seg_durations[0]:.2f}s)...")
        frame = draw_opening(op_bg, items)
        p = os.path.join(frames_dir, "opening.png")
        frame.save(p)
        frame_list.append(("opening", p, round(seg_durations[0], 3)))

    for i, item in enumerate(items):
        dur = seg_durations[i + 1]
        bg = os.path.join(img_dir, f"{i+1:02d}.jpg")
        if not os.path.exists(bg):
            bg = op_bg
        print(f"  Slide {i+1}/{len(items)} ({dur:.2f}s)...")
        frame = draw_slide(bg, item, i + 1, len(items))
        p = os.path.join(frames_dir, f"slide_{i+1:03d}.png")
        frame.save(p)
        frame_list.append((f"slide_{i+1}", p, round(dur, 3)))

    en_bg = os.path.join(img_dir, "ending_bg.jpg")
    if not os.path.exists(en_bg):
        en_bg = op_bg
    print(f"  Ending frame ({seg_durations[-1]:.2f}s)...")
    frame = draw_ending(en_bg)
    p = os.path.join(frames_dir, "ending.png")
    frame.save(p)
    frame_list.append(("ending", p, round(seg_durations[-1], 3)))

    total_dur = sum(d for _, _, d in frame_list)
    print(f"  Total: {total_dur:.3f}s ({len(frame_list)} frames)")

    # Build ffmpeg filter_complex command
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

    r2 = subprocess.run([FFMPEG, '-i', output_path], capture_output=True, text=True, timeout=30)
    m = re.search(r'Duration: (\d+):(\d+):(\d+)\.(\d+)', r2.stderr)
    if m:
        h, mi, s, ms = int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4))
        vdur = h * 3600 + mi * 60 + s + ms / 100
        print(f"  Video: {vdur:.2f}s, Audio: {total_dur:.2f}s, Diff: {abs(vdur-total_dur):.3f}s")

    print(f"  Output: {output_path}")
    return output_path


# ========== MAIN ==========
def step(msg):
    print(f"\n{'='*60}")
    print(f"  {msg}")
    print(f"{'='*60}")


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    os.makedirs(IMAGES_DIR, exist_ok=True)
    os.makedirs(AUDIO_DIR, exist_ok=True)

    # Step 1: Parse
    step(f"Step 1/4: Parse daily script -> {PARSED_PATH}")
    with open(SCRIPT_FILE, 'r', encoding='utf-8') as f:
        text = f.read()
    items = parse_daily_script(text)
    if not items:
        print("  ERROR: Parsed 0 items")
        sys.exit(1)
    with open(PARSED_PATH, 'w', encoding='utf-8') as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
    print(f"  Parsed {len(items)} news items")
    for it in items:
        print(f"  #{it['num']} [{it['section']}] {it['title'][:50]}...")

    # Step 2: Images
    step(f"Step 2/4: Generate images -> {IMAGES_DIR}")
    gen_all_images(items, IMAGES_DIR)
    img_files = [f for f in os.listdir(IMAGES_DIR) if f.endswith('.jpg')]
    print(f"  Images: {len(img_files)} files")

    # Step 3: TTS
    step(f"Step 3/4: Generate TTS -> {AUDIO_PATH}")
    asyncio.run(gen_tts(items, AUDIO_PATH))

    # Step 4: Video
    step(f"Step 4/4: Build video -> {OUTPUT_VIDEO}")
    build_video(items, IMAGES_DIR, AUDIO_PATH, SEGMENTS_PATH, OUTPUT_VIDEO)

    print(f"\n{'='*60}")
    print(f"  ✅ ALL DONE")
    print(f"  Video: {OUTPUT_VIDEO}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()