#!/usr/bin/env python3
"""为 signal_pop daily/weekly 新闻稿生成配图 — Sensenova-u1-fast 优先，Pollinations 备选"""
import urllib.request, os, sys, re, json, io
import urllib.parse
from datetime import date
from PIL import Image

BASE = "/home/kan/shared/signal_pop/archive"
today = date.today().strftime("%Y%m%d")

# ---------- Sensenova ----------
SENSENOVA_URL = "https://token.sensenova.cn/v1/images/generations"
SENSENOVA_KEY = "sk-Orks5KCFxdjhRSm7EEFY57UdykEWzWIQ"
SENSENOVA_MODEL = "sensenova-u1-fast"
SENSENOVA_SIZE = "2752x1536"  # 16:9

def gen_sensenova(prompt, timeout=120):
    payload = json.dumps({
        "model": SENSENOVA_MODEL,
        "prompt": prompt,
        "size": SENSENOVA_SIZE,
        "n": 1,
    }).encode()
    req = urllib.request.Request(
        SENSENOVA_URL, data=payload,
        headers={
            "Authorization": f"Bearer {SENSENOVA_KEY}",
            "Content-Type": "application/json",
        },
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        resp = json.loads(r.read())
    url = resp.get("data", [{}])[0].get("url")
    if not url:
        raise Exception("no URL in response")
    # 下载 PNG → 转 JPEG
    img_req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(img_req, timeout=timeout) as ir:
        img = Image.open(io.BytesIO(ir.read()))
    out = io.BytesIO()
    img.convert("RGB").save(out, "JPEG", quality=88)
    return out.getvalue()

def gen_pollinations(prompt, seed, timeout=120):
    q = urllib.parse.quote(f"{prompt}?width=1280&height=720&nologo=true&seed={seed}")
    url = f"https://image.pollinations.ai/prompt/{q}"
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
        "Referer": "https://pollinations.ai/",
    })
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()

def gen_image(prompt, seed, timeout=120):
    """Sensenova 优先 → Pollinations 备选。返回 bytes."""
    try:
        return gen_sensenova(prompt, timeout), "sensenova"
    except Exception as e:
        print(f"  Sensenova 失败({e})→ Pollinations降级")
        try:
            return gen_pollinations(prompt, seed, timeout), "pollinations"
        except Exception as e2:
            raise Exception(f"Sensenova+Pollinations 均失败: {e} / {e2}")

# ---------- Prompt building ----------
keyword_map = [
    ("游戏", "modern gaming company office, colorful character posters on wall, clean design workspace, bright natural light, no people, no screens"),
    ("房价", "quiet residential street in Shanghai, rows of apartment buildings, warm sunrise light, tree-lined road, no people"),
    ("ETF", "modern technology campus, glass office buildings reflecting blue sky, clean architectural design, no people"),
    ("脑机", "hospital operating room with medical equipment, MRI scanner, clean white interior, blue lighting, no people"),
    ("SpaceX", "SpaceX Falcon 9 rocket on launch pad at dawn, Cape Canaveral, smoke trailing, industrial architecture, wide landscape, no people, no screens"),
    ("AI", "pharmaceutical research laboratory, glass vials on white shelves, blue liquid, clean sterile environment, no people"),
    ("制药", "modern biomedical research laboratory, rows of glass flasks, blue ambient light, clean white workbench, no people, no screens"),
    ("巴菲特", "wood-paneled corporate boardroom, empty leather chairs, afternoon sunlight through blinds, warm wood tones, no people"),
    ("世界杯", "large empty football stadium, green grass pitch, floodlights, dramatic sunset sky, wide angle"),
    ("法国", "elegant French government building facade, Palais Bourbon, classical columns, overcast sky, no people"),
    ("特朗普", "Middle Eastern desert landscape, distant military silhouettes, dramatic dusk sky, sand and mountains, wide panorama"),
    ("经济", "modern city skyline at golden hour, skyscraper silhouettes, warm orange sky, clean wide shot"),
    ("科技", "modern technology research center exterior, glass and steel architecture, blue sky, clean lines"),
    ("国内", "traditional Chinese garden, curved roof pavilion, green bamboo, peaceful pond reflection, no people"),
    ("上市", "modern financial district skyline, high-rise buildings, sunrise, clean architectural shot"),
    ("房价", "residential neighborhood, modern apartment complex, morning light, tree shadow on facade"),
    ("油价", "petrol station canopy, empty gas pumps, blue sky, clean geometric architecture, no cars"),
    ("保险", "modern insurance company office interior, clean reception area, soft lighting, no people"),
    ("发射", "rocket launch gantry at spaceport, industrial structure against clear sky, wide landscape"),
]
# Generic fallback — natural scene based on headline text
def build_prompt(title, index):
    # Per-index overrides for specific news items that need exact match
    custom = {
        6: f"SpaceX Falcon 9 rocket standing on ocean droneship platform, glowing exhaust trail, dawn sky over Atlantic, Cape Canaveral industrial silhouette in distance, clean photography, no people, no screens, no text",
        10: f"Middle East desert night landscape, fighter jet silhouette streaking across dark sky, distant explosion glow on horizon, military operation scene at dusk, wide panorama, cinematic, no screens, no text",
    }
    if index in custom:
        return f"{custom[index]}, no text, no labels, no characters, clean visual, empty scene"
    for kw, template in keyword_map:
        if kw in title:
            extra = title.replace(kw, "").strip()[:40]
            p = f"{template}, {extra}" if extra else template
            return f"{p}, no text, no labels, no characters, clean visual, empty scene"
    return f"nature landscape or architecture scene inspired by {title[:40]}, cinematic photography, no text, no labels, no characters, clean visual"

def extract_titles(text):
    titles = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        m = re.match(r'^第\d+条[，,]\s*[^。]+[。，]\s*(.+?)\s*[。，]?\s*$', line)
        if m:
            titles.append(m.group(1))
    return titles

def generate_images(news_file, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    with open(news_file, "r") as f:
        text = f.read()
    titles = extract_titles(text)
    seen = set()
    titles = [t for t in titles if not (t in seen or seen.add(t))]
    if not titles:
        return []
    results = []
    for n, title in enumerate(titles, 1):
        path = f"{out_dir}/{n:02d}.jpg"
        if os.path.exists(path) and os.path.getsize(path) > 1000:
            results.append(f"→ 第{n}条 (已存在): {title[:25]}")
            continue
        prompt = build_prompt(title, n)
        try:
            data, source = gen_image(prompt, n * 37)
            with open(path, "wb") as f:
                f.write(data)
            results.append(f"✓ 第{n}条 [{source}] ({len(data)//1024}KB): {title[:25]}")
        except Exception as e:
            results.append(f"✗ 第{n}条: {e}")
    return results

# 处理 daily
daily_file = os.path.join(BASE, f"signal_pop_daily_{today}.txt")
if os.path.exists(daily_file):
    out_dir = os.path.join(BASE, f"img_{today}")
    print(f"===== Daily: {daily_file} =====")
    for r in generate_images(daily_file, out_dir):
        print(r)
else:
    print(f"无 daily: {daily_file}")

# 处理 weekly
weekly_file = os.path.join(BASE, f"signal_pop_weekly_{today}.txt")
if os.path.exists(weekly_file):
    out_dir = os.path.join(BASE, f"img_weekly_{today}")
    print(f"===== Weekly: {weekly_file} =====")
    for r in generate_images(weekly_file, out_dir):
        print(r)
else:
    print(f"无 weekly: {weekly_file}")

print("===== 配图生成完成 =====")