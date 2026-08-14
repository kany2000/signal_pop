#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Signal Pop — 周末特别版管线驱动（输出到 output/weekly/，不走 daily）
用法：python tools/weekend_pipeline.py [PREP_DATE] [步骤]
步骤: parse | images | tts | video | all
"""
import os
import sys
import json
from datetime import datetime, timedelta

PROJECT_ROOT = "E:/projects/signal_pop"
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, "scripts"))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "tools"))

PREP_DATE = sys.argv[1] if len(sys.argv) > 1 else "20260814"
STEP = sys.argv[2] if len(sys.argv) > 2 else "parse"

SCRIPT_FILE = os.path.join(PROJECT_ROOT, "archive", f"signal_pop_weekly_special_{PREP_DATE}.txt")
OUT_DIR = os.path.join(PROJECT_ROOT, "output", "weekly", PREP_DATE)
IMAGES_DIR = os.path.join(OUT_DIR, "images")
AUDIO_DIR = os.path.join(OUT_DIR, "audio")
PARSED_PATH = os.path.join(OUT_DIR, "parsed_news.json")
AUDIO_PATH = os.path.join(AUDIO_DIR, "tts.wav")
OUTPUT_VIDEO = os.path.join(OUT_DIR, f"signal_pop_weekly_{PREP_DATE}.mp4")

PUB_DT = datetime.strptime(PREP_DATE, "%Y%m%d") + timedelta(days=1)
PUB_DATE_FMT = f"{PUB_DT.year}年{PUB_DT.month:02d}月{PUB_DT.day:02d}日"
PUB_DATE_SHORT = f"{PUB_DT.year}.{PUB_DT.month:02d}.{PUB_DT.day:02d}"
PUB_WEEKDAY = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"][PUB_DT.weekday()]

# 15 条配图提示词（按标题关键词映射；遵循无文字/无手/无人群标准）
VISUAL_PROMPTS = {
    "净水器": "modern water purifier appliance on kitchen counter, clean home appliance product photography, fresh water droplets, no text, no words, no letters, no numbers, no people, no hands",
    "广告拦截": "desktop computer screen with shield protection icons, browser security concept, digital freedom, modern office, no text, no words, no letters, no numbers, no people, no UI text, no logos",
    "和平杯": "youth football players on green pitch, soccer ball on grass, stadium lights, youth sports competition, no text, no words, no letters, no numbers, no people faces closeup, no signage",
    "DOTA2": "epic esports arena with large screens and stage lighting, competitive gaming atmosphere, no text, no words, no letters, no numbers, no people closeup, no UI",
    "机车": "sleek modern motorcycle in showroom, dark background with dramatic lighting, industrial design, product photography, no text, no words, no letters, no numbers, no people, no signage",
    "相机": "professional camera with interchangeable lens on desk, camera body with lens, photography equipment product shot, no text, no words, no letters, no numbers, no people, no hands",
    "零跑": "modern electric car silhouette at dusk, EV on road, clean automotive design, no text, no words, no letters, no numbers, no people, no logos",
    "Manus": "glowing AI agent interface hologram, futuristic digital assistant concept, blue light streams, no text, no words, no letters, no numbers, no people, no UI text",
    "Pixel": "modern smartphone with clean screen floating in dark studio, premium product photography, rim lighting, no text, no words, no letters, no numbers, no people, no hands, no UI text",
    "Armoury": "laptop with glowing warning shield hologram, cybersecurity vulnerability concept, digital protection, dark tech background, no text, no words, no letters, no numbers, no people, no UI text",
    "享界": "luxury smart electric SUV on city road at dusk, futuristic headlights, intelligent driving concept, premium automotive design, no text, no words, no letters, no numbers, no people, no logos",
    "平陆运河": "grand canal with ships, waterway through green landscape, shipping barges, infrastructure engineering, aerial view, no text, no words, no letters, no numbers, no people, no signage",
    "本周之最": "golden trophy cup with award ribbons on pedestal, celebration confetti, awards ceremony concept, dramatic lighting, no text, no words, no letters, no numbers, no people",
    "下周看点": "futuristic humanoid robots lined up in exhibition hall, robotics expo, sci-fi technology, no text, no words, no letters, no numbers, no people, no signage",
}


def parse_weekly_top(text):
    """解析榜单格式：
    本周第10名，[分类]新闻。标题。上榜理由：xxx
    本周之最。最震撼，xxx。最暖心，xxx。最意外，xxx。
    下周看点。xxx
    返回 items（顺序=脚本顺序，第10名→第1名→彩蛋→看点）
    """
    import re as _re
    items = []
    for line in text.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        if line.startswith("这里是") or line.startswith("以上是"):
            continue
        m = _re.match(r"^本周第(\d+)名[，,]\s*\[?(.+?)\]?\s*新闻[。.]\s*(.+?)[。.]\s*上榜理由[：:]\s*(.+)$", line)
        if m:
            rank = int(m.group(1))
            items.append({
                "num": rank,          # 排名（10..1）
                "rank": rank,
                "section": m.group(2).strip(),
                "title": m.group(3).strip(),
                "body": m.group(4).strip(),
                "opinion": "",
                "full_body": f"本周第{rank}名，{m.group(2).strip()}。{m.group(3).strip()}。上榜理由：{m.group(4).strip()}",
            })
            continue
        m2 = _re.match(r"^本周之最[。.]\s*(.+)$", line)
        if m2:
            items.append({
                "num": 0, "rank": 0, "section": "彩蛋", "title": "本周之最",
                "body": m2.group(1).strip(), "opinion": "",
                "full_body": f"本周之最。{m2.group(1).strip()}",
            })
            continue
        m3 = _re.match(r"^下周看点[。.]\s*(.+)$", line)
        if m3:
            items.append({
                "num": 99, "rank": 99, "section": "看点", "title": "下周看点",
                "body": m3.group(1).strip(), "opinion": "",
                "full_body": f"下周看点。{m3.group(1).strip()}",
            })
            continue
    return items


def assign_visual_prompts(items):
    for it in items:
        t = it.get("title", "")
        for kw, prompt in VISUAL_PROMPTS.items():
            if kw in t:
                it["visual_prompt"] = prompt
                break
        if not it.get("visual_prompt") and it.get("section") == "彩蛋":
            it["visual_prompt"] = VISUAL_PROMPTS.get("本周之最", "")
        if not it.get("visual_prompt") and it.get("section") == "看点":
            it["visual_prompt"] = VISUAL_PROMPTS.get("下周看点", "")


def step_parse():
    text = open(SCRIPT_FILE, encoding="utf-8").read()
    items = parse_weekly_top(text)
    assign_visual_prompts(items)
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(PARSED_PATH, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
    print(f"[parse] {len(items)} 段 -> {PARSED_PATH}")
    for it in items:
        print(f"  #{it['num']:>2} [{it['section']}] {it['title'][:24]} vp={'有' if it.get('visual_prompt') else '无'}")
    return items


def step_images():
    from win_pipeline_images import gen_all_images
    items = json.load(open(PARSED_PATH, encoding="utf-8"))
    os.makedirs(IMAGES_DIR, exist_ok=True)
    gen_all_images(items, IMAGES_DIR)
    print(f"[images] -> {IMAGES_DIR}")


def step_tts():
    import asyncio
    from win_pipeline_tts import gen_tts
    os.makedirs(AUDIO_DIR, exist_ok=True)
    asyncio.run(gen_tts(PARSED_PATH, AUDIO_PATH, PUB_DATE_FMT, PUB_WEEKDAY))
    print(f"[tts] -> {AUDIO_PATH}")


if __name__ == "__main__":
    if STEP in ("parse", "all"):
        step_parse()
    if STEP in ("images", "all"):
        step_images()
    if STEP in ("tts", "all"):
        step_tts()
    print("DONE")
