#!/usr/bin/env python3
"""Signal Pop Windows Pipeline Orchestrator — 一键运行所有步骤"""
import sys, os, json, asyncio
from datetime import datetime, timedelta

# ========== CONFIG ==========
SCRIPT_FILE = "E:/projects/signal_pop/archive/signal_pop_weekly_special_20260717.txt"
DATE = "20260717"  # Prep date (from filename)
OUTPUT_BASE = "E:/projects/signal_pop/output"

# Compute pub date (prep date + 1)
PUB_DT = datetime.strptime(DATE, "%Y%m%d") + timedelta(days=1)
PUB_DATE = PUB_DT.strftime("%Y%m%d")
PUB_DATE_FMT = f"{PUB_DATE[:4]}年{PUB_DATE[4:6]}月{PUB_DATE[6:8]}日"
PUB_DATE_SHORT = f"{PUB_DATE[:4]}.{PUB_DATE[4:6]}.{PUB_DATE[6:8]}"
PUB_WEEKDAY = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"][PUB_DT.weekday()]

OUT_DIR = os.path.join(OUTPUT_BASE, f"weekly_{DATE}")
IMAGES_DIR = os.path.join(OUT_DIR, "images")
AUDIO_DIR = os.path.join(OUT_DIR, "audio")
AUDIO_PATH = os.path.join(AUDIO_DIR, "tts.wav")
SEGMENTS_PATH = os.path.join(AUDIO_DIR, "tts_segments.json")
PARSED_PATH = os.path.join(OUT_DIR, "parsed_news.json")
OUTPUT_VIDEO = os.path.join(OUT_DIR, f"signal_pop_weekly_special_{DATE}.mp4")

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))


def step(msg):
    """Print step header."""
    print(f"\n{'='*60}")
    print(f"  {msg}")
    print(f"{'='*60}")


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    os.makedirs(IMAGES_DIR, exist_ok=True)
    os.makedirs(AUDIO_DIR, exist_ok=True)

    # ===== Step 1: Parse Script =====
    step(f"Step 1/4: Parse news script -> {PARSED_PATH}")
    sys.path.insert(0, SCRIPTS_DIR)
    with open(SCRIPT_FILE, 'r', encoding='utf-8') as f:
        text = f.read()
    from win_pipeline_parse import parse_script
    items = parse_script(text)
    if not items:
        print("  ERROR: Parsed 0 items. Check parse_script regex.")
        sys.exit(1)
    with open(PARSED_PATH, 'w', encoding='utf-8') as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
    print(f"  Parsed {len(items)} news items")

    # ===== Step 2: Generate Images =====
    step(f"Step 2/4: Generate images -> {IMAGES_DIR}")
    from win_pipeline_images import gen_all_images
    gen_all_images(items, IMAGES_DIR)
    # Verify
    img_files = [f for f in os.listdir(IMAGES_DIR) if f.endswith('.jpg')]
    print(f"  Images: {len(img_files)} files")

    # ===== Step 3: Generate TTS (continuous + silence detection) =====
    step(f"Step 3/4: Generate TTS (continuous + silence detection) -> {AUDIO_PATH}")
    from win_pipeline_tts import gen_tts
    asyncio.run(gen_tts(PARSED_PATH, AUDIO_PATH))

    # ===== Step 4: Build Video =====
    step(f"Step 4/4: Build video -> {OUTPUT_VIDEO}")
    from win_pipeline_video import build_video
    build_video(items, IMAGES_DIR, AUDIO_PATH, SEGMENTS_PATH, OUTPUT_VIDEO,
                PUB_DATE_FMT, PUB_WEEKDAY, PUB_DATE_SHORT)

    print(f"\n{'='*60}")
    print(f"  ✅ ALL DONE")
    print(f"  Video: {OUTPUT_VIDEO}")
    print(f"{'='*60}")
    print(f"\nNext steps:")
    print(f"  - Publish to social platforms (auto_publish)")
    print(f"  - Copy to her2home for distribution")


if __name__ == "__main__":
    main()