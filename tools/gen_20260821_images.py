#!/usr/bin/env python3
"""20260821 周末版配图生成：14 张 sensenova（02 边缘行者已用真实图）+ 99 下周看点
用法: python tools/gen_20260821_images.py
"""
import os, sys
sys.path.insert(0, os.path.join("E:/projects/signal_pop", "scripts"))
from win_pipeline_images import download_image, logger

OUT_DIR = "E:/projects/signal_pop/output/weekly/20260821/images"
os.makedirs(OUT_DIR, exist_ok=True)

# 按新闻内容定制 prompt（无文字/无手/无人群 + 核心要素）
PROMPTS = {
    1: "national science research laboratory interior, advanced technology equipment, futuristic lab with blue and gold lighting, microscope and holographic displays, government-funded science innovation concept, cinematic, no text, no words, no letters, no numbers, no signage, no people",
    3: "solid state battery cell technology close-up, layered battery material stack with metallic luster, futuristic energy storage design, soft studio lighting, dark background with blue accents, no text, no words, no letters, no numbers, no people, no hands",
    4: "modern smart factory quality inspection line, robotic arms inspecting precision metal parts, industrial quality control concept, clean manufacturing environment, dramatic lighting, no text, no words, no letters, no numbers, no people",
    5: "3D stacked DRAM memory chip macro photography, layered semiconductor wafer architecture with blue and gold tech lighting, futuristic technology concept, no text, no words, no letters, no numbers, no people, no hands",
    6: "high-speed train interior with rows of blue seats, empty modern train carriage, bright daylight streaming through windows, clean travel photography, perspective view, no text, no words, no letters, no numbers, no people",
    7: "open source AI code displayed as flowing colorful light streams, digital neural network visualization, open collaboration concept, deep blue tech background with glowing connections, no text, no words, no letters, no numbers, no UI text, no people",
    8: "smartphone with glowing digital shield and lock icon, cybersecurity protection concept, dark background with blue light streams, futuristic device security, no text, no words, no letters, no numbers, no people, no hands, no UI text",
    9: "delivery courier riding electric scooter on urban street with delivery box, motion blur effect, bright daylight, fast delivery service concept, modern city backdrop, no text, no words, no letters, no numbers, no people closeup, no signage",
    10: "modular data center containers stacked in rows, prefabricated computing infrastructure, server racks glowing blue, industrial park at dusk, no text, no words, no letters, no numbers, no people",
    11: "modern telemedicine consultation scene, doctor with tablet connecting remote patient via video call, smart hospital concept, clean bright medical environment, blue and white lighting, no text, no words, no letters, no numbers, no people faces closeup",
    12: "AI digital assistant connecting multiple office application icons floating around laptop, productivity concept, bright modern workspace, glowing connection lines, no text, no words, no letters, no numbers, no people, no hands, no UI text",
    13: "modern driver service center exterior, taxi drivers resting lounge with comfortable seating, city street view, welcoming service station, daylight, no text, no words, no letters, no numbers, no people closeup, no signage",
    14: "smart AI glasses on minimalist white desk, futuristic eyewear product photography, soft studio lighting with rim light, tech product shot, premium feel, no text, no words, no letters, no numbers, no people, no hands",
    15: "rural village basketball court with enthusiastic crowd and string lights, countryside sports festival atmosphere, evening golden hour, vibrant community event, wooden bleachers, no text, no words, no letters, no numbers, no signage",
    99: "tech product launch event stage with laptop on pedestal, dark auditorium with dramatic spotlight, new product reveal concept, premium presentation, no text, no words, no letters, no numbers, no people closeup, no signage",
}

for num, prompt in PROMPTS.items():
    fname = f"{num:02d}.jpg"
    out = os.path.join(OUT_DIR, fname)
    if os.path.exists(out) and os.path.getsize(out) > 5000:
        print(f"  ⏭ {fname} 存在，跳过")
        continue
    print(f"[{fname}] 生成中...")
    download_image(prompt, seed=num * 100, out_path=out)
print("\n✅ 全部完成")
