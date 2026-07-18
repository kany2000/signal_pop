#!/usr/bin/env python3
"""为 signal_pop daily 新闻稿生成配图，每张基于新闻内容独立定制prompt"""
import urllib.request, urllib.parse, os, sys

BASE = "/home/kan/shared/signal_pop/archive"
today = "20260705"
out_dir = os.path.join(BASE, f"img_{today}")
os.makedirs(out_dir, exist_ok=True)

# 每条新闻对应的定制化prompt — 严格基于新闻标题的具体场景
prompts = [
    # 1. 三伏天高温预警
    "Heat wave across China, thermometers showing 40 degrees Celsius, people carrying sun umbrellas on crowded city streets, heat shimmer distortion in summer air, dramatic orange sun, newspaper illustration style, vivid",
    # 2. 暑期旅游拥堵
    "Bustling Chinese tourist attraction during summer vacation, crowds of families with children queuing at ancient temple gates, red lanterns, stone archway, summer travel rush, documentary photo style",
    # 3. 医保药品目录调整
    "Chinese medicine cabinet with bottles of pills and blood pressure medication, elderly person's hands reaching for medicine, hospital pharmacy counter, warm lighting, medical illustration",
    # 4. 夏季用电高峰错峰用电
    "Power transmission towers under summer sunset, city skyline with lit windows, electrical substation, cooling towers, grid infrastructure, industrial photography style",
    # 5. 电商平台年中大促下沉市场
    "Rural Chinese village shop with smartphone in hand, delivery box with Chinese characters, excited farmer receiving online shopping package, village road, ecommerce boom in countryside, vibrant colors",
    # 6. 服务业回升强劲
    "Busy Chinese restaurant with waiter serving hot dishes, customers dining at round tables, steaming pots of hotpot, bustling service scene, economic recovery, warm golden lighting",
    # 7. 超导材料量子计算突破
    "Laboratory scientist in white coat examining glowing quantum chip, superconducting wire cooling device with liquid nitrogen vapor, high-tech research room, blue and purple glow, scientific breakthrough illustration",
    # 8. 顶流演员新片定档暑期
    "Movie poster reveal event, red carpet with photographers, Chinese film premiere, spotlight, popcorn and cinema tickets in foreground, entertainment news style, glamorous",
    # 9. 美联储利率决议避险情绪
    "Stock market trading floor in panic, red falling charts on monitors, dollar bills scattered, worried traders, Wall Street financial crisis atmosphere, dramatic cinematic lighting",
    # 10. 特朗普白宫与内塔尼亚胡会面
    "White House South Lawn meeting scene, two political leaders in dark suits walking towards each other on green lawn, American and Israeli flags, Secret Service agents nearby, presidential grounds, geopolitical news photo style",
]

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
headers = {"User-Agent": UA, "Referer": "https://pollinations.ai/"}

for n, prompt in enumerate(prompts, 1):
    q = urllib.parse.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{q}?width=1280&height=720&nologo=true&seed={n*42}"
    path = f"{out_dir}/{n:02d}.jpg"
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=120) as r:
            data = r.read()
        with open(path, "wb") as f:
            f.write(data)
        print(f"✓ 第{n}条 ({len(data)//1024}KB)")
    except Exception as e:
        print(f"✗ 第{n}条: {e}")

print("===== 配图生成完成 =====")
