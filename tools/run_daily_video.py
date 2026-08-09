#!/usr/bin/env python3
"""Signal Pop — 每日管线驱动（适配单行格式：第N条，[分类]新闻。标题。据 来源 报道，正文。）"""
import os
import sys
import re
import json
import asyncio

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)
_SCRIPTS = os.path.join(_PROJECT_ROOT, "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

from datetime import datetime, timedelta

PREP_DATE = os.getenv("SIGNAL_POP_PREP_DATE", "20260809")
SCRIPT_FILE = os.path.join(_PROJECT_ROOT, "archive", f"signal_pop_daily_{PREP_DATE}.txt")
OUT_DIR = os.path.join(_PROJECT_ROOT, "output", "daily", PREP_DATE)
IMAGES_DIR = os.path.join(OUT_DIR, "images")
AUDIO_DIR = os.path.join(OUT_DIR, "audio")
AUDIO_PATH = os.path.join(AUDIO_DIR, "tts.wav")
SEGMENTS_PATH = os.path.join(AUDIO_DIR, "tts_segments.json")
PARSED_PATH = os.path.join(OUT_DIR, "parsed_news.json")
OUTPUT_VIDEO = os.path.join(OUT_DIR, f"signal_pop_daily_{PREP_DATE}.mp4")

PUB_DT = datetime.strptime(PREP_DATE, "%Y%m%d") + timedelta(days=1)
PUB_DATE_FMT = f"{PUB_DT.year}年{PUB_DT.month:02d}月{PUB_DT.day:02d}日"
PUB_DATE_SHORT = f"{PUB_DT.year}.{PUB_DT.month:02d}.{PUB_DT.day:02d}"
PUB_WEEKDAY = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"][PUB_DT.weekday()]


def parse_daily_script(text):
    """解析单行格式：
    第N条，[分类]新闻。标题。据 来源 报道，正文[。主播观点：xxx]
    """
    items = []
    for line in text.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        if line.startswith("这里是隔天信号弹") or line.startswith("以上是本期"):
            continue
        m = re.match(r"^第(\d+)条[，,]\s*\[?(.+?)\]?\s*新闻[。.]\s*(.+?)[。.]\s*据\s*(.+?)\s*报道[，,]\s*(.+)$", line)
        if not m:
            continue
        num = int(m.group(1))
        section = m.group(2).strip()
        title = m.group(3).strip()
        source = m.group(4).strip()
        body = m.group(5).strip()
        opinion = ""
        if "主播观点：" in body:
            body, opinion = body.split("主播观点：", 1)
            body = body.rstrip("。.").strip()
            opinion = opinion.strip().rstrip("。.")
        items.append({
            "num": num,
            "section": section,
            "title": title,
            "source": source,
            "body": body,
            "opinion": opinion,
            "full_body": body,
        })
    return items


def main():
    os.makedirs(IMAGES_DIR, exist_ok=True)
    os.makedirs(AUDIO_DIR, exist_ok=True)

    # ===== Step 1: Parse =====
    print(f"\n{'='*60}\n  Step 1/4: Parse -> {PARSED_PATH}\n{'='*60}")
    with open(SCRIPT_FILE, "r", encoding="utf-8") as f:
        text = f.read()
    items = parse_daily_script(text)
    if not items:
        print("  ERROR: Parsed 0 items")
        sys.exit(1)
    with open(PARSED_PATH, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
    print(f"  Parsed {len(items)} items")
    for it in items:
        print(f"  #{it['num']} [{it['section']}] {it['title'][:42]}...")

    # ===== Step 2: Images =====
    print(f"\n{'='*60}\n  Step 2/4: Images -> {IMAGES_DIR}\n{'='*60}")
    from win_pipeline_images import gen_all_images
    gen_all_images(items, IMAGES_DIR)
    imgs = [f for f in os.listdir(IMAGES_DIR) if f.endswith(".jpg")]
    print(f"  Images: {len(imgs)} files")

    # ===== Step 3: TTS =====
    print(f"\n{'='*60}\n  Step 3/4: TTS -> {AUDIO_PATH}\n{'='*60}")
    from win_pipeline_tts import gen_tts
    asyncio.run(gen_tts(PARSED_PATH, AUDIO_PATH, PUB_DATE_FMT, PUB_WEEKDAY))

    # ===== Step 4: Video =====
    print(f"\n{'='*60}\n  Step 4/4: Build video -> {OUTPUT_VIDEO}\n{'='*60}")
    from win_pipeline_video import build_video
    build_video(items, IMAGES_DIR, AUDIO_PATH, SEGMENTS_PATH, OUTPUT_VIDEO,
                PUB_DATE_FMT, PUB_WEEKDAY, PUB_DATE_SHORT)

    print(f"\n{'='*60}\n  [OK] ALL DONE\n  Video: {OUTPUT_VIDEO}\n{'='*60}")


if __name__ == "__main__":
    main()
