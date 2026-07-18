#!/usr/bin/env python3
"""Step 2: Generate images for each news item via Sensenova API (Pollinations fallback)"""
import sys, os, json, re, time, io, urllib.request, urllib.parse
from PIL import Image

SENSENOVA_URL = "https://token.sensenova.cn/v1/images/generations"
SENSENOVA_KEY = "sk-Orks5KCFxdjhRSm7EEFY57UdykEWzWIQ"
SENSENOVA_MODEL = "sensenova-u1-fast"
SENSENOVA_SIZE = "2752x1536"  # 16:9

POLLINATIONS_TPL = "https://image.pollinations.ai/prompt/{q}?width=1216&height=832&seed={seed}&model=flux&nofeed=true"

# Pre-defined prompts for each news item (index starts at 0 for opening_bg)
NEWS_PROMPTS = {
    "opening": "Chinese news broadcasting studio, professional television studio, blue and gold lighting, large LED screen showing world map, modern broadcast desk, cinematic, professional photography, 8K",
    "ending": "Chinese news broadcasting studio, warm lighting, professional television studio, wide shot, elegant, cinematic, professional photography",
}

NO_TEXT = ", no text, no words, no labels, no captions, no UI, clean image without any writing"

SCENE_PROMPTS = {
    "SpaceX": "SpaceX Starship rocket on launch pad at Boca Chica Texas, dramatic sunset, launch tower, aerospace technology, documentary photography" + NO_TEXT,
    "超算": "Chinese supercomputer center with glowing blue server racks, neural network visualization, futuristic technology" + NO_TEXT,
    "千问": "Modern AI earphones product on minimalist white desk, sleek design, technology concept" + NO_TEXT,
    "文远知行": "Autonomous driving test car on smart city road, LiDAR sensors, futuristic transportation" + NO_TEXT,
    "中科天塔": "Satellite laser communication terminal in cleanroom laboratory, aerospace engineering, precision optics" + NO_TEXT,
    "智谱": "Chinese AI startup office, glowing data dashboard, modern glass building, business photography" + NO_TEXT,
    "蚂蚁": "Ant Group headquarters building in Hangzhou, AI health interface on large screen, modern fintech" + NO_TEXT,
    "阿里": "B2B ecommerce platform automation, factory AI trading concept, industrial internet" + NO_TEXT,
    "A股": "Chinese stock market trading floor with red and green digital tickers, investors watching screens" + NO_TEXT,
    "港科大": "Advanced robotics laboratory, humanoid robot hand with tactile sensors, research scientist working" + NO_TEXT,
    "美国6月": "American shopping mall and retail stores, customers shopping, commerce and consumer spending" + NO_TEXT,
    "欧洲央行": "European Central Bank headquarters Frankfurt, euro currency symbol, financial district architecture" + NO_TEXT,
    "ABB": "Industrial automation factory, robotic arms on assembly line, precision manufacturing" + NO_TEXT,
    "本田": "Honda dealer showroom with electric SUV on display, automotive, clean commercial photography" + NO_TEXT,
    "美国对伊朗": "Persian Gulf coast, Strait of Hormuz aerial view, naval ships, geopolitical tension" + NO_TEXT,
}
DEFAULT_SCENE = "news event scene, documentary photography" + NO_TEXT


def make_prompt(title, body):
    """Generate a visual prompt from news title."""
    for kw, prompt in SCENE_PROMPTS.items():
        if kw in title or kw in body:
            return prompt
    return f"{title}, news event scene, documentary photography" + NO_TEXT


def gen_sensenova(prompt, timeout=180):
    """Call Sensenova API, return JPEG bytes."""
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
    url = resp["data"][0]["url"]
    # Download the image
    with urllib.request.urlopen(url, timeout=timeout) as img_r:
        img_bytes = img_r.read()
    return img_bytes


def gen_pollinations(prompt, seed, timeout=120):
    """Call Pollinations API, return JPEG bytes."""
    q = urllib.parse.quote(prompt)
    url = POLLINATIONS_TPL.format(q=q, seed=seed)
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        img_bytes = r.read()
    return img_bytes


def download_image(prompt, seed, out_path, max_retries=3):
    """Download image, Sensenova first then Pollinations fallback. Save to out_path."""
    for attempt in range(max_retries):
        # Try Sensenova
        try:
            print(f"  Sensenova...")
            img_bytes = gen_sensenova(prompt)
            _save_image(img_bytes, out_path)
            print(f"  -> OK (Sensenova)")
            return True
        except Exception as e:
            print(f"  Sensenova failed: {e}")

        # Fallback to Pollinations
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

    print(f"  FAILED after {max_retries} retries")
    # Create a fallback colored image
    img = Image.new('RGB', (1216, 832), (30, 40, 60))
    img.save(out_path, quality=85)
    print(f"  -> Generated fallback placeholder")
    return False


def _save_image(img_bytes, out_path):
    """Save image bytes, convert RGBA->RGB if needed, resize to 1920x1080."""
    img = Image.open(io.BytesIO(img_bytes))
    if img.mode == 'RGBA':
        img = img.convert('RGB')
    # Resize to 1920x1080 (cover)
    img = img.resize((1920, 1080), Image.LANCZOS)
    img.save(out_path, quality=85)


def gen_all_images(items, out_dir):
    """Generate all images: opening_bg, 01-NN, ending_bg."""
    os.makedirs(out_dir, exist_ok=True)

    # Opening background
    opening_path = os.path.join(out_dir, "opening_bg.jpg")
    if not os.path.exists(opening_path):
        print(f"\n[Opening BG]")
        download_image(NEWS_PROMPTS["opening"], 42, opening_path)
    else:
        print(f"  opening_bg.jpg exists, skip")

    # News images
    for i, item in enumerate(items, 1):
        fname = f"{i:02d}.jpg"
        out_path = os.path.join(out_dir, fname)
        if os.path.exists(out_path) and os.path.getsize(out_path) > 5000:
            print(f"  {fname} exists, skip")
            continue
        prompt = make_prompt(item["title"], item["full_body"])
        print(f"\n[{fname}] {item['title'][:40]}...")
        print(f"  Prompt: {prompt[:80]}...")
        download_image(prompt, item["num"] * 100, out_path)

    # Ending background
    ending_path = os.path.join(out_dir, "ending_bg.jpg")
    if not os.path.exists(ending_path):
        print(f"\n[Ending BG]")
        download_image(NEWS_PROMPTS["ending"], 999, ending_path)
    else:
        print(f"  ending_bg.jpg exists, skip")

    return out_dir


if __name__ == "__main__":
    import sys
    items_path = sys.argv[1]
    out_dir = sys.argv[2] if len(sys.argv) > 2 else "E:/projects/signal_pop/output/weekly_20260717/images"
    with open(items_path, 'r', encoding='utf-8') as f:
        items = json.load(f)
    gen_all_images(items, out_dir)