#!/usr/bin/env python3
"""Signal Pop Windows Pipeline Orchestrator — 一键运行所有步骤"""

import sys
import os
import json
import asyncio

# Ensure project root is on sys.path so config/logger are importable
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from config import (
    SCRIPT_FILE,
    PREP_DATE_STR,
    PUB_DATE_FMT,
    PUB_WEEKDAY,
    PUB_DATE_SHORT,
    OUT_DIR,
    IMAGES_DIR,
    AUDIO_DIR,
    AUDIO_PATH,
    AUDIO_SEGMENTS_PATH,
    PARSED_NEWS_PATH,
    OUTPUT_VIDEO_PATH,
    FRAME_DIR,
    LOG_FILE,
)
from logger import (
    logger,
    log_and_raise,
    NewsParseError,
)

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)


def step(msg):
    """Log step header."""
    logger.info(f"\n{'='*60}")
    logger.info(f"  {msg}")
    logger.info(f"{'='*60}")


def main():
    try:
        logger.info(f"Starting Signal Pop pipeline for prep date: {PREP_DATE_STR}")
        os.makedirs(OUT_DIR, exist_ok=True)
        os.makedirs(IMAGES_DIR, exist_ok=True)
        os.makedirs(AUDIO_DIR, exist_ok=True)
        os.makedirs(FRAME_DIR, exist_ok=True)

        # ===== Step 1: Parse Script =====
        step(f"Step 1/4: Parse news script -> {PARSED_NEWS_PATH}")
        with open(SCRIPT_FILE, "r", encoding="utf-8") as f:
            text = f.read()
        from win_pipeline_parse import parse_script

        items = parse_script(text)
        if not items:
            logger.error("Parsed 0 items. Check parse_script regex.")
            log_and_raise(NewsParseError, "Parsed 0 items. Check parse_script regex.")
        with open(PARSED_NEWS_PATH, "w", encoding="utf-8") as f:
            json.dump(items, f, ensure_ascii=False, indent=2)
        logger.info(f"Parsed {len(items)} news items")

        # ===== Step 2: Generate Images =====
        step(f"Step 2/4: Generate images -> {IMAGES_DIR}")
        from win_pipeline_images import gen_all_images

        gen_all_images(items, IMAGES_DIR)
        # Verify
        img_files = [f for f in os.listdir(IMAGES_DIR) if f.endswith(".jpg")]
        logger.info(f"Generated {len(img_files)} images")

        # ===== Step 3: Generate TTS (continuous + silence detection) =====
        step(f"Step 3/4: Generate TTS (continuous + silence detection) -> {AUDIO_PATH}")
        from win_pipeline_tts import gen_tts

        asyncio.run(gen_tts(PARSED_NEWS_PATH, AUDIO_PATH))

        # ===== Step 4: Build Video =====
        step(f"Step 4/4: Build video -> {OUTPUT_VIDEO_PATH}")
        from win_pipeline_video import build_video

        build_video(
            items,
            IMAGES_DIR,
            AUDIO_PATH,
            AUDIO_SEGMENTS_PATH,
            OUTPUT_VIDEO_PATH,
            PUB_DATE_FMT,
            PUB_WEEKDAY,
            PUB_DATE_SHORT,
        )

        logger.info("Pipeline completed successfully.")
        print("\n" + "=" * 60)
        print("  ✅ ALL DONE")
        print(f"  Video: {OUTPUT_VIDEO_PATH}")
        print("=" * 60)
        print("\nNext steps:")
        print("  - Publish to social platforms (auto_publish)")
        print("  - Copy to her2home for distribution")

    except Exception as e:
        logger.error(f"Pipeline failed with error: {e}", exc_info=True)
        print("\n" + "=" * 60)
        print("  ❌ PIPELINE FAILED")
        print(f"  Error: {e}")
        print(f"  Check log file for details: {LOG_FILE}")
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()
