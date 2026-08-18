#!/usr/bin/env python3
"""Step 2: Generate images for each news item via Sensenova API (Pollinations fallback)"""

import sys
import os
import json
import time
import io
import urllib.request
import urllib.parse
from PIL import Image

# Ensure project root is on sys.path
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from config import SENSENOVA_API_KEY  # noqa: E402
from logger import logger  # noqa: E402

SENSENOVA_URL = "https://token.sensenova.cn/v1/images/generations"
SENSENOVA_MODEL = "sensenova-u1-fast"
SENSENOVA_SIZE = "2752x1536"  # 16:9

POLLINATIONS_TPL = "https://image.pollinations.ai/prompt/{q}?width=1216&height=832&seed={seed}&model=flux&nofeed=true"

NEWS_PROMPTS = {
    "opening": "Chinese news broadcasting studio, professional television studio, blue and gold lighting, large LED screen showing world map, modern broadcast desk, cinematic, professional photography, 8K",
    "ending": "blurred city skyline at night with bokeh lights, dark blue gradient, abstract background, no text, no words, no letters, no writing, no signs, no labels, clean abstract background",
}

NO_TEXT = ", no text, no words, no labels, no captions, no UI, clean image without any writing"

SCENE_PROMPTS = {
    "豆包": "modern Windows desktop computer screen showing a virtual desktop session with cursor and highlighted UI elements, AI agent operating the computer, glowing cursor pointer hovering over application windows, automation concept, blue ambient glow, no people, no text, no words, no letters, no numbers, no logos, no UI text"
    + NO_TEXT,
    "汽车出口": "massive car carrier ship loaded with new energy vehicles docked at busy container port, rows of colorful new cars on dock waiting for export, cranes and shipping containers in background, China automotive export concept, golden hour lighting, aerial perspective, no text, no words, no letters, no numbers, no signage"
    + NO_TEXT,
    "宇树": "humanoid robot silhouette standing on a stock exchange trading floor with glowing red and green stock tickers and digital price charts in background, IPO listing concept, futuristic finance and robotics fusion, dramatic lighting, no people, no text, no words, no letters, no numbers, no logos"
    + NO_TEXT,
    "县域消费": "vibrant county town market street with shops, street vendors and colorful goods, shoppers browsing, rural commercial vitality concept, warm daylight, modern Chinese small city commerce, no text, no words, no letters, no numbers, no signage"
    + NO_TEXT,
    "上海科技馆": "modern science museum building with futuristic architecture, families with children entering glass dome entrance, science exhibition posters without text, educational tourism concept, blue sky, no text, no words, no letters, no numbers, no signage"
    + NO_TEXT,
    "乒乓球": "two humanoid robots playing table tennis across a green ping pong table viewed from above at 45 degrees, table oriented horizontally across the frame, robot arms holding red and black paddles mid-swing, white ball frozen mid-air above the net, indoor sports arena lighting, robotic agility concept, dynamic action shot, no people, no text, no words, no letters, no numbers"
    + NO_TEXT,
    "Arm": "glowing central processor chip with ARM architecture logo pattern on dark circuit board, semiconductor design concept, macro photography, blue and gold light traces, no text, no words, no letters, no numbers, no logos"
    + NO_TEXT,
    "三星显示": "ultra-thin flexible OLED display panel being lifted by a clean room robot arm inside a semiconductor fabrication factory, glowing edge lit glass substrate, futuristic display manufacturing line with overhead robotic arms and precision machinery, no phones, no devices, no people, no text, no words, no letters, no numbers, no logos"
    + NO_TEXT,
    "OLED": "ultra-thin flexible OLED display panel being lifted by a clean room robot arm inside a semiconductor fabrication factory, glowing edge lit glass substrate, futuristic display manufacturing line with overhead robotic arms and precision machinery, no phones, no devices, no people, no text, no words, no letters, no numbers, no logos"
    + NO_TEXT,
    "芡实": "fresh green water caltrop seed pods and white lotus seeds in traditional bamboo basket, Suzhou water town wetland background, farm harvest scene, natural sunlight, close-up food photography, no text, no words, no letters, no numbers, no people"
    + NO_TEXT,
    "乒联": "two table tennis rackets crossed above a green ping pong table viewed from above at 45 degrees, white ball frozen mid-air between them, world map hologram projection in background, professional championship atmosphere, dramatic spotlight, no people, no text, no words, no letters, no numbers"
    + NO_TEXT,
    "太空摆渡车": "space tug spacecraft with glowing engines docking with a satellite in low Earth orbit, orbital transfer vehicle concept, Earth and stars in background, blue engine thrust, futuristic space logistics, cinematic space photography, no text, no words, no letters, no numbers"
    + NO_TEXT,
    "人形机器人": "rows of humanoid robots standing on a sports stadium field, robot athletes competing in track and field, jumping and lifting events, large-scale robotics competition venue with spotlights, thousands of robots lined up, futuristic technology olympics concept, cinematic wide shot, no people, no text, no words, no letters, no numbers"
    + NO_TEXT,
    "机器人运动会": "rows of humanoid robots standing on a sports stadium field, robot athletes competing in track and field, jumping and lifting events, large-scale robotics competition venue with spotlights, thousands of robots lined up, futuristic technology olympics concept, cinematic wide shot, no people, no text, no words, no letters, no numbers"
    + NO_TEXT,
    "Cursor": "SpaceX rocket launching at sunset with streams of glowing digital code and holographic programming lines flowing across the sky, artificial intelligence software acquisition concept, futuristic aerospace and AI fusion, cinematic, no people, no text, no words, no letters, no numbers"
    + NO_TEXT,
    "Anthropic": "giant glowing AI brain above a stock market trading floor, digital IPO concept, golden light rays and floating stock chart holograms, futuristic artificial intelligence company listing, dramatic financial technology scene, no people, no text, no words, no letters, no numbers"
    + NO_TEXT,
    "唐钱婷": "indoor swimming pool with crystal clear water, golden medal and trophy placed on pool deck edge, Chinese national flag draped beside, subtle water ripples and blue waves, championship victory concept, no people, no text, no words, no letters, no numbers"
    + NO_TEXT,
    "蛙泳": "indoor swimming pool with crystal clear water, golden medal and trophy placed on pool deck edge, Chinese national flag draped beside, subtle water ripples and blue waves, championship victory concept, no people, no text, no words, no letters, no numbers"
    + NO_TEXT,
    "电动自行车": "urban city street with a dedicated bicycle lane, rows of electric bikes parked neatly at designated parking area, modern city infrastructure with clear lane markings, urban mobility management concept, daytime, no people, no text, no words, no letters, no numbers, no signage"
    + NO_TEXT,
    "原创音乐": "open-air summer night concert stage with warm golden stage lights, audience silhouettes with raised hands, night sky with stars, outdoor music festival atmosphere, bokeh lights, cinematic, no text, no words, no letters, no numbers"
    + NO_TEXT,
    "NVIDIA": "NVIDIA GPU chip glowing green, massive AI data center with rows of server racks and glowing cooling fans, digital money and stock charts flowing as light streams above, artificial intelligence computing infrastructure investment concept, cinematic tech photography, no people, no text, no words, no letters, no numbers"
    + NO_TEXT,
    "历史上的今天": "Great Wall of China stretching across misty green mountain ridges, ancient stone watchtowers winding along the ridgeline, Chinese landscape photography at sunrise, Badaling or Mutianyu section, rolling hills and historical architecture, panoramic wide shot, no text, no words, no letters, no numbers"
    + NO_TEXT,
    "IBM": "Vintage 1980s computer scene, classic beige IBM PC with CRT monitor on wooden desk, retro technology, warm nostalgic lighting, old newspapers and calendar in background, archival photography style"
    + NO_TEXT,
    "个人电脑": "Vintage 1980s computer scene, classic beige IBM PC with CRT monitor on wooden desk, retro technology, warm nostalgic lighting, old newspapers and calendar in background, archival photography style"
    + NO_TEXT,
    "SpaceX": "SpaceX Starship rocket on launch pad at Boca Chica Texas, dramatic sunset, launch tower, aerospace technology, documentary photography"
    + NO_TEXT,
    "台风": "Massive typhoon spiral over East China Sea seen from space, swirling storm clouds approaching coastal city, dramatic satellite view, storm surge, meteorology"
    + NO_TEXT,
    "居民消费价格": "Chinese supermarket with fresh produce and price tags, shopper checking prices, consumer economy, everyday life, warm lighting"
    + NO_TEXT,
    "医疗垃圾": "Phone case production line inspection, laboratory testing, magnifying glass over smartphone case, safety inspection concept, industrial photography"
    + NO_TEXT,
    "手机壳": "Phone case production line inspection, laboratory testing, magnifying glass over smartphone case, safety inspection concept, industrial photography"
    + NO_TEXT,
    "折叠iPhone": "Foldable smartphone floating in dark studio, sleek silver and dark blue design, product photography, dramatic rim lighting, premium tech"
    + NO_TEXT,
    "iPhone": "Sleek modern all-glass smartphone, seamless glass unibody with edge-to-edge transparent display, standard smartphone shape held at slight angle, reflective glass surface, dark studio background, premium product photography, rim lighting, photorealistic, no hands, no people, no text"
    + NO_TEXT,
    "大气田": "Offshore oil and gas platform in Bohai Sea, golden hour, industrial energy production, drilling rigs, maritime engineering, dramatic sky"
    + NO_TEXT,
    "AI流量": "Massive data center with glowing server racks, network traffic visualization as streams of light, artificial intelligence infrastructure, futuristic technology"
    + NO_TEXT,
    "Cloudflare": "Massive data center with glowing server racks, network traffic visualization as streams of light, artificial intelligence infrastructure, futuristic technology"
    + NO_TEXT,
    "斯诺克": "Real professional snooker table seen from above, green baize cloth, EXACTLY six pockets: four corner pockets at the four corners of the table, and two middle pockets at the center of the left and right long side rails. The center of the top short side and the center of the bottom short side have NO pocket. Triangle rack of 15 red balls at one end, six colored balls (yellow green brown blue pink black) and white cue ball on the cloth, wooden cushion rails, overhead triangular lamp, championship tournament hall, photorealistic, accurate sports photography"
    + NO_TEXT,
    "非遗": "Chinese intangible cultural heritage handicrafts, young people wearing traditional Yi ethnic festival attire, torch festival celebration, vibrant colors, cultural tourism"
    + NO_TEXT,
    "运动相机": "Action camera mounted on bike handlebar, outdoor adventure sports, mountain trail, dynamic sports photography, rugged tech"
    + NO_TEXT,
    "核科学": "Science olympiad laboratory, young students in competition, nuclear science equipment, medals on table, bright modern lab, educational achievement"
    + NO_TEXT,
    "超算": "Chinese supercomputer center with glowing blue server racks, neural network visualization, futuristic technology"
    + NO_TEXT,
    "超算": "Chinese supercomputer center with glowing blue server racks, neural network visualization, futuristic technology"
    + NO_TEXT,
    "千问": "Modern AI earphones product on minimalist white desk, sleek design, technology concept" + NO_TEXT,
    "文远知行": "Autonomous driving test car on smart city road, LiDAR sensors, futuristic transportation" + NO_TEXT,
    "中科天塔": "Satellite laser communication terminal in cleanroom laboratory, aerospace engineering, precision optics"
    + NO_TEXT,
    "智谱": "Chinese AI startup office, glowing data dashboard, modern glass building, business photography" + NO_TEXT,
    "蚂蚁": "extreme macro photograph of a single ant, its delicate antennae touching a glowing blue tactile sensor surface, biomimetic tactile sensing concept, shallow depth of field, dark background, dramatic cinematic lighting, scientific nature photography, one ant only, no text, no words, no letters, no numbers, no hands, no people, no other insects, no watermarks"
    + NO_TEXT,
    "阿里": "B2B ecommerce platform automation, factory AI trading concept, industrial internet" + NO_TEXT,
    "A股": "Chinese stock market trading floor with red and green digital tickers, investors watching screens"
    + NO_TEXT,
    "港科大": "Advanced robotics laboratory, humanoid robot hand with tactile sensors, research scientist working"
    + NO_TEXT,
    "美国6月": "American shopping mall and retail stores, customers shopping, commerce and consumer spending" + NO_TEXT,
    "欧洲央行": "European Central Bank headquarters Frankfurt, euro currency symbol, financial district architecture"
    + NO_TEXT,
    "ABB": "Industrial automation factory, robotic arms on assembly line, precision manufacturing" + NO_TEXT,
    "本田": "Honda dealer showroom with electric SUV on display, automotive, clean commercial photography" + NO_TEXT,
    "美国对伊朗": "Persian Gulf coast, Strait of Hormuz aerial view, naval ships, geopolitical tension" + NO_TEXT,
    "DeepSeek": "DeepSeek AI large language model inference visualization, glowing neural network with streaming text tokens flowing through layers, futuristic dark data center with blue server racks, AI model training concept, cinematic tech photography, no people, no text, no words, no letters, no numbers, no logos"
    + NO_TEXT,
    "智能外骨骼": "Smart exoskeleton suit on display, futuristic wearable technology, augmented reality smart glasses, consumer electronics show, innovative tech products"
    + NO_TEXT,
    "智能眼镜": "Smart augmented reality glasses on modern desk, future wearable technology, digital display interface, consumer electronics innovation"
    + NO_TEXT,
    "中际旭创": "Fiber optic cable with glowing light signals, high-speed data transmission technology, optical communication equipment, modern telecommunications infrastructure, professional photography"
    + NO_TEXT,
    "旭创": "Optical transceiver module close-up, fiber optic technology, data center connectivity, high-speed internet infrastructure, clean tech photography"
    + NO_TEXT,
    "AI取代": "Professional office worker standing next to AI robot, human and artificial intelligence collaboration, modern workplace, futuristic office environment, technology concept"
    + NO_TEXT,
    "AI Agents": "Digital AI agent interface on holographic screen, artificial intelligence automation, virtual assistant concept, futuristic technology, glowing data streams"
    + NO_TEXT,
    "OPEC": "OPEC headquarters building Vienna, oil barrels and petroleum refinery, OPEC flag and member country flags, global energy summit, oil industry photography"
    + NO_TEXT,
    "OPEC+": "World oil map with petroleum pipelines, oil drilling rigs at sunset, OPEC energy ministers meeting, global oil production concept, industrial photography"
    + NO_TEXT,
    "全玻璃": "Modern transparent smartphone concept, sleek glass smartphone floating on dark studio background, minimal product photography, glowing edge lighting, no hands, no people"
    + NO_TEXT,
    "贝索斯": "Liverpool football stadium Anfield green pitch at dusk with dramatic floodlights, large elegant golden business handshake sculpture at center of pitch, modern city skyscrapers skyline behind stands, football club acquisition deal concept, luxury corporate sports business photography, cinematic warm lighting, no people, no hands, no text"
    + NO_TEXT,
    "横店": "Chinese ancient town film set, traditional wooden buildings and red lanterns, vintage street with movie props, warm daylight, cinematic scenery, no text, no signs"
    + NO_TEXT,
    "山洪": "Torrential mountain flood water rushing down valley, dramatic storm clouds, wet rocks and trees, dramatic weather photography, no text, no signs"
    + NO_TEXT,
    "博物馆": "Spacious modern museum interior with visitors viewing ancient cultural relics display, warm gallery lighting, elegant exhibition hall, cultural heritage photography, no text"
    + NO_TEXT,
    "文博": "Spacious modern museum interior with visitors viewing ancient cultural relics display, warm gallery lighting, elegant exhibition hall, cultural heritage photography, no text"
    + NO_TEXT,
    "上海博物馆": "Spacious modern museum interior with visitors viewing ancient cultural relics display, warm gallery lighting, elegant exhibition hall, cultural heritage photography, no text"
    + NO_TEXT,
    "谷歌": "Gemini AI model concept, abstract colorful neural network glowing in dark space, futuristic artificial intelligence brain, Google technology, geometric light patterns, no people, no text, no words, no letters, no numbers"
    + NO_TEXT,
    "韦布": "James Webb Space Telescope with golden hexagonal mirror segments floating in deep space, distant star surrounded by dust and water vapor, cosmic nebula, black hole region, deep space astronomy, cinematic photography, no people, no text, no words, no letters, no numbers"
    + NO_TEXT,
    "电动车": "modern electric vehicles charging at sleek charging stations, futuristic EV on city street, clean energy transportation concept, European street scene, no people, no text, no words, no letters, no numbers, no price tags, no signage"
    + NO_TEXT,
    "超导": "ultra-thin superconducting material layer, atomic-scale copper oxide crystal lattice glowing blue, levitating magnetic field concept, laboratory scientific research equipment, quantum physics, no people, no text, no words, no letters, no numbers"
    + NO_TEXT,
    "机器人手机": "futuristic smartphone with mechanical robotic elements, sleek robotic phone concept floating in dark studio, glowing accent lights, premium product photography, no hands, no people, no text, no words, no letters, no numbers"
    + NO_TEXT,
    "日全食": "total solar eclipse, black sun with glowing corona ring, dramatic dusk sky with orange and purple sunset, silhouette of landscape below, rare astronomical phenomenon, cinematic photography, no people, no text, no words, no letters, no numbers"
    + NO_TEXT,
    "柯桥": "colorful textile fabric rolls and curtain fabrics, elegant hanging curtains in various colors, textile wholesale market display, soft fabric textures, industrial textile production, no people, no text, no words, no letters, no numbers, no price tags, no signage"
    + NO_TEXT,
    "乌镇": "Wuzhen ancient water town in China, traditional white-wall black-tile buildings along canals, stone arch bridge, wooden boats on water, red lanterns, summer travel scenery, warm sunlight, no people, no text, no words, no letters, no numbers, no signage"
    + NO_TEXT,
    "金价": "gold bars and gold coins stacked on dark reflective surface, shimmering golden bullion, financial market investment concept, dramatic lighting, macro photography, no text, no words, no letters, no numbers, no hands, no people, no price tags"
    + NO_TEXT,
    "歌舞剧": "Guizhou ethnic minority dance performance on stage, traditional Miao costumes with silver jewelry and embroidery, colorful national stage art, vibrant cultural show, dramatic stage lighting, no text, no words, no letters, no numbers, no signs, no banners"
    + NO_TEXT,
    "智能手机": "modern smartphones displayed on retail counter, several smartphone models with clean screens, consumer electronics market concept, store display, soft lighting, no text, no words, no letters, no numbers, no price tags, no signage, no people"
    + NO_TEXT,
    "Siri": "modern smartphone with glowing AI assistant interface on desk, stacked newspapers and books beside it, digital news publishing and artificial intelligence concept, clean bright workspace, no text, no words, no letters, no numbers, no logos, no people, no text bubbles"
    + NO_TEXT,
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
    if not SENSENOVA_API_KEY:
        raise ValueError("SENSENOVA_API_KEY not set in environment variables")

    payload = json.dumps(
        {
            "model": SENSENOVA_MODEL,
            "prompt": prompt,
            "size": SENSENOVA_SIZE,
            "n": 1,
        }
    ).encode()
    req = urllib.request.Request(
        SENSENOVA_URL,
        data=payload,
        headers={
            "Authorization": f"Bearer {SENSENOVA_API_KEY}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        resp = json.loads(r.read())
    url = resp["data"][0]["url"]
    with urllib.request.urlopen(url, timeout=timeout) as img_r:
        img_bytes = img_r.read()
    return img_bytes


def gen_pollinations(prompt, seed, timeout=120):
    """Call Pollinations API, return JPEG bytes."""
    q = urllib.parse.quote(prompt)
    url = POLLINATIONS_TPL.format(q=q, seed=seed)
    req = urllib.request.Request(
        url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        img_bytes = r.read()
    return img_bytes


def download_image(prompt, seed, out_path, max_retries=3):
    """Download image, Sensenova first then Pollinations fallback. Save to out_path."""
    for attempt in range(max_retries):
        # Try Sensenova
        try:
            logger.info("  Trying Sensenova...")
            img_bytes = gen_sensenova(prompt)
            _save_image(img_bytes, out_path)
            logger.info("  -> OK (Sensenova)")
            return True
        except Exception as e:
            logger.warning(f"  Sensenova failed: {e}")

        # Fallback to Pollinations
        try:
            logger.info("  Pollinations fallback...")
            img_bytes = gen_pollinations(prompt, seed + attempt)
            _save_image(img_bytes, out_path)
            logger.info("  -> OK (Pollinations)")
            return True
        except Exception as e:
            logger.warning(f"  Pollinations failed: {e}")

        logger.info(f"  Retry {attempt+1}/{max_retries}...")
        time.sleep(3)

    logger.error(f"  FAILED after {max_retries} retries")
    # Create a fallback colored image
    img = Image.new("RGB", (1216, 832), (30, 40, 60))
    img.save(out_path, quality=85)
    logger.info("  -> Generated fallback placeholder")
    return False


def _save_image(img_bytes, out_path):
    """Save image bytes, convert RGBA->RGB if needed, resize to 1920x1080."""
    img = Image.open(io.BytesIO(img_bytes))
    if img.mode == "RGBA":
        img = img.convert("RGB")
    img = img.resize((1920, 1080), Image.LANCZOS)
    img.save(out_path, quality=85)


def gen_all_images(items, out_dir):
    """Generate all images: opening_bg, 01-NN, ending_bg."""
    os.makedirs(out_dir, exist_ok=True)

    # Opening background
    opening_path = os.path.join(out_dir, "opening_bg.jpg")
    if not os.path.exists(opening_path):
        logger.info("[Opening BG]")
        download_image(NEWS_PROMPTS["opening"], 42, opening_path)
    else:
        logger.info("  opening_bg.jpg exists, skip")

    # News images（历史条目 num=0 -> 00.jpg，新闻按 num 编号）
    for item in items:
        n = item.get("num", 0)
        fname = f"{n:02d}.jpg"
        out_path = os.path.join(out_dir, fname)
        if os.path.exists(out_path) and os.path.getsize(out_path) > 5000:
            logger.info(f"  {fname} exists, skip")
            continue
        vp = item.get("visual_prompt") or ""
        prompt = vp if vp else make_prompt(item["title"], item.get("full_body", item.get("body", "")))
        logger.info(f"[{fname}] {item['title'][:40]}...")
        logger.debug(f"  Prompt: {prompt[:80]}...")
        download_image(prompt, item["num"] * 100, out_path)

    # Ending background
    ending_path = os.path.join(out_dir, "ending_bg.jpg")
    if not os.path.exists(ending_path):
        logger.info("[Ending BG]")
        download_image(NEWS_PROMPTS["ending"], 999, ending_path)
    else:
        logger.info("  ending_bg.jpg exists, skip")

    return out_dir


if __name__ == "__main__":
    items_path = sys.argv[1]
    out_dir = sys.argv[2] if len(sys.argv) > 2 else os.path.join(_PROJECT_ROOT, "output", "images")
    with open(items_path, "r", encoding="utf-8") as f:
        items = json.load(f)
    gen_all_images(items, out_dir)
