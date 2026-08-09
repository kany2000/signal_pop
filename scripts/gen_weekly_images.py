#!/usr/bin/env python3
"""Generate images for weekly special — 15 news items + opening + ending"""
import sys, os, json, re, io, time, urllib.request, urllib.parse
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

PARSED = "E:/projects/signal_pop/output/parsed_weekly_20260807.json"
OUT_DIR = "E:/projects/signal_pop/output/daily_20260808/images"

SENSENOVA_URL = "https://token.sensenova.cn/v1/images/generations"
SENSENOVA_KEY = "sk-Orks5KCFxdjhRSm7EEFY57UdykEWzWIQ"
SENSENOVA_MODEL = "sensenova-u1-fast"
SENSENOVA_SIZE = "2752x1536"
POLLINATIONS_TPL = "https://image.pollinations.ai/prompt/{q}?width=1216&height=832&seed={seed}&model=flux&nofeed=true"
NO_TEXT = ", no text, no words, no labels, no captions, no UI, no signs, no writing, clean image without any text"

# Weekly special prompts
SCENE_PROMPTS = {
    "机器人": "Humanoid robot in futuristic warehouse, robotic arms sorting packages, automation technology, industrial robotics, documentary photography" + NO_TEXT,
    "英国零售": "Modern British retail store with automated systems, warehouse robots, smart logistics, UK shopping street" + NO_TEXT,
    "甲骨文": "Oracle headquarters building, cloud computing data center, enterprise technology, modern glass architecture" + NO_TEXT,
    "谷歌": "Google headquarters campus, AI technology, modern office, Silicon Valley tech company" + NO_TEXT,
    "Gemini": "Google Gemini AI concept, neural network visualization, artificial intelligence, futuristic technology" + NO_TEXT,
    "Chrome": "Computer screen showing Chrome browser with security shield, cybersecurity concept, digital protection" + NO_TEXT,
    "AI辅助": "AI security analysis dashboard, code vulnerability detection, cybersecurity technology, digital defense" + NO_TEXT,
    "人形机器人": "Humanoid robot standing in factory, realistic full-body shot, advanced robotics, industrial automation, documentary photography" + NO_TEXT,
    "换电": "Robotic battery swapping station, automated charging infrastructure, robot maintenance, technology concept" + NO_TEXT,
    "宇树科技": "Unitree robotics company showroom, quadruped robot and humanoid robot on display, Chinese robotics company" + NO_TEXT,
    "科创板": "Shanghai Stock Exchange building, SSE STAR Market board, Chinese financial district, modern architecture" + NO_TEXT,
    "政治局": "Zhongnanhai leadership compound, Chinese government meeting, political conference, Beijing" + NO_TEXT,
    "内需": "Chinese shopping mall with consumers shopping, retail stores, domestic consumption, bustling commercial street" + NO_TEXT,
    "SHEIN": "SHEIN fast fashion warehouse, clothing racks, e-commerce fulfillment center, fashion logistics" + NO_TEXT,
    "希音": "SHEIN fast fashion photography, model wearing trendy clothes, e-commerce fashion brand" + NO_TEXT,
    "离岸": "Offshore financial center concept, international banking, global finance, business district" + NO_TEXT,
    "富豪": "Luxury lifestyle, wealthy businessman, private jet, high-end real estate, wealth management concept" + NO_TEXT,
    "极端天气": "Extreme weather damage, flooded street, storm damage, climate change impact, natural disaster photography" + NO_TEXT,
    "保险": "Insurance company building, claims processing, risk management concept, financial protection" + NO_TEXT,
    "Anthropic": "Anthropic AI company office, ethical AI research, safety testing, futuristic technology" + NO_TEXT,
    "AI模型": "Artificial intelligence neural network, deep learning model visualization, glowing circuit board brain" + NO_TEXT,
    "熊本": "Kumamoto Japan earthquake damage, cracked road, collapsed building, disaster area, rescue workers" + NO_TEXT,
    "日本地震": "Japan earthquake aftermath, rescue operation, damaged infrastructure, natural disaster" + NO_TEXT,
    "中东石油": "Middle East oil refinery, oil tankers at port, Strait of Hormuz, petroleum industry, sunset" + NO_TEXT,
    "石油": "Oil drilling rig, crude oil transportation, energy industry, global oil supply" + NO_TEXT,
    "美联储": "Federal Reserve building Washington DC, American flag, central bank, monetary policy" + NO_TEXT,
    "利率": "Stock market chart with interest rate graph, financial data, economic indicators" + NO_TEXT,
    "KOSPI": "Korean stock exchange trading floor, KOSPI index board, Seoul financial district, digital ticker" + NO_TEXT,
    "韩国股市": "South Korea stock market, Seoul skyline, financial district, trading terminal with charts" + NO_TEXT,
    "欧足联": "UEFA headquarters, European football stadium, Champions League trophy, soccer concept" + NO_TEXT,
    "FIFA": "FIFA headquarters Zurich, World Cup trophy, international football, soccer governing body" + NO_TEXT,
    "足球": "Football stadium with fans, soccer match, professional sports, arena atmosphere" + NO_TEXT,
}

DEFAULT_SCENE = "news event scene, documentary photography, cinematic" + NO_TEXT

NEWS_PROMPTS = {
    "opening": "Chinese news broadcasting studio, professional television studio, blue and gold lighting, large LED screen, modern broadcast desk, cinematic, 8K" + NO_TEXT,
    "ending": "Chinese news broadcasting studio, warm lighting, wide shot, elegant, cinematic" + NO_TEXT,
}

def make_prompt(title, body):
    txt = title + " " + body
    for kw, prompt in SCENE_PROMPTS.items():
        if kw in txt:
            return prompt
    return DEFAULT_SCENE

def gen_sensenova(prompt, timeout=180):
    payload = json.dumps({"model": SENSENOVA_MODEL, "prompt": prompt, "size": SENSENOVA_SIZE, "n": 1}).encode()
    req = urllib.request.Request(SENSENOVA_URL, data=payload,
        headers={"Authorization": f"Bearer {SENSENOVA_KEY}", "Content-Type": "application/json"},
        method="POST")
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
    if img.mode == 'RGBA': img = img.convert('RGB')
    img = img.resize((1920, 1080), Image.LANCZOS)
    img.save(out_path, quality=85)

def download_image(prompt, seed, out_path, max_retries=5):
    for attempt in range(max_retries):
        try:
            print(f"  Sensenova...")
            img_bytes = gen_sensenova(prompt, timeout=300)
            _save_image(img_bytes, out_path)
            print(f"  -> OK")
            return True
        except Exception as e:
            print(f"  Sensenova fail: {e}")
        try:
            print(f"  Pollinations fallback...")
            img_bytes = gen_pollinations(prompt, seed + attempt)
            _save_image(img_bytes, out_path)
            print(f"  -> OK (Pollinations)")
            return True
        except Exception as e:
            print(f"  Pollinations fail: {e}")
        print(f"  Retry {attempt+1}/{max_retries}...")
        time.sleep(3)
    img = Image.new('RGB', (1920, 1080), (30, 40, 60))
    img.save(out_path, quality=85)
    print(f"  -> Fallback placeholder")
    return False

def main():
    with open(PARSED, 'r', encoding='utf-8') as f:
        items = json.load(f)

    os.makedirs(OUT_DIR, exist_ok=True)

    # Opening
    op_path = os.path.join(OUT_DIR, "opening_bg.jpg")
    if not os.path.exists(op_path):
        print(f"\n[Opening BG]")
        download_image(NEWS_PROMPTS["opening"], 42, op_path)
    else:
        print(f"  opening_bg.jpg exists, skip")

    # News items
    for i, item in enumerate(items, 1):
        fname = f"{i:02d}.jpg"
        out_path = os.path.join(OUT_DIR, fname)
        if os.path.exists(out_path) and os.path.getsize(out_path) > 5000:
            print(f"  {fname} exists, skip")
            continue
        prompt = item.get("visual_prompt") or make_prompt(item["title"], item["body"])
        print(f"\n[{fname}] {item['title'][:40]}...")
        print(f"  Prompt: {prompt[:80]}...")
        download_image(prompt, item["num"] * 100, out_path)

    # Ending
    en_path = os.path.join(OUT_DIR, "ending_bg.jpg")
    if not os.path.exists(en_path):
        print(f"\n[Ending BG]")
        download_image(NEWS_PROMPTS["ending"], 999, en_path)
    else:
        print(f"  ending_bg.jpg exists, skip")

    print(f"\nDone! Images in {OUT_DIR}")

if __name__ == "__main__":
    main()