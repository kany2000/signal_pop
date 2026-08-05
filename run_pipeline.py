#!/usr/bin/env python3
"""
Signal Pop - Unified Pipeline Runner

Works on both Windows and Linux. Uses centralized config and logger.
Replaces the platform-specific scripts as the primary entry point.

Usage:
    python run_pipeline.py                    # Run with default config (yesterday's date)
    SIGNAL_POP_PREP_DATE=20260717 python run_pipeline.py  # Run for specific date
    python run_pipeline.py --weekly           # Run weekly special variant
"""
import argparse
import asyncio
import json
import os
import sys

# Ensure project root is on sys.path
_PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)
_SCRIPTS_DIR = os.path.join(_PROJECT_ROOT, "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

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
from logger import logger, log_and_raise, NewsParseError
from styles import get_style_for_date


def step(msg):
    """Log a step header."""
    border = "=" * 60
    logger.info(f"\n{border}")
    logger.info(f"  {msg}")
    logger.info(border)


def parse_args():
    parser = argparse.ArgumentParser(description="Signal Pop Pipeline Runner")
    parser.add_argument(
        "--weekly",
        action="store_true",
        help="Run weekly special variant (default: daily)",
    )
    parser.add_argument(
        "--skip-images",
        action="store_true",
        help="Skip image generation step",
    )
    parser.add_argument(
        "--skip-tts",
        action="store_true",
        help="Skip TTS generation step",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    try:
        variant = "weekly" if args.weekly else "daily"
        logger.info(f"Starting Signal Pop {variant} pipeline for prep date: {PREP_DATE_STR}")

        # Show selected style
        style = get_style_for_date(PREP_DATE_STR)
        logger.info(f"Style theme: bar={style['bar']}, accent={style['accent']}")

        # Create directories
        for d in [OUT_DIR, IMAGES_DIR, AUDIO_DIR, FRAME_DIR]:
            os.makedirs(d, exist_ok=True)

        # ===== Step 1: Parse Script =====
        step(f"Step 1/4: Parse news script -> {PARSED_NEWS_PATH}")
        if not os.path.exists(SCRIPT_FILE):
            log_and_raise(NewsParseError, f"Script file not found: {SCRIPT_FILE}")

        with open(SCRIPT_FILE, "r", encoding="utf-8") as f:
            text = f.read()

        from win_pipeline_parse import parse_script

        items = parse_script(text)
        if not items:
            log_and_raise(NewsParseError, "Parsed 0 items. Check parse_script regex.")

        with open(PARSED_NEWS_PATH, "w", encoding="utf-8") as f:
            json.dump(items, f, ensure_ascii=False, indent=2)
        logger.info(f"Parsed {len(items)} news items")

        # ===== Step 2: Generate Images =====
        if args.skip_images:
            step("Step 2/4: SKIPPED (image generation)")
        else:
            step(f"Step 2/4: Generate images -> {IMAGES_DIR}")
            from win_pipeline_images import gen_all_images

            gen_all_images(items, IMAGES_DIR)
            img_files = [f for f in os.listdir(IMAGES_DIR) if f.endswith(".jpg")]
            logger.info(f"Generated {len(img_files)} images")

        # ===== Step 3: Generate TTS =====
        if args.skip_tts:
            step("Step 3/4: SKIPPED (TTS generation)")
        else:
            step(f"Step 3/4: Generate TTS -> {AUDIO_PATH}")
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
        print("  ALL DONE")
        print(f"  Video: {OUTPUT_VIDEO_PATH}")
        print("=" * 60)
        print("\nNext steps:")
        print("  - Publish to social platforms")
        print("  - Copy to her2home for distribution")

    except Exception as e:
        logger.error(f"Pipeline failed with error: {e}", exc_info=True)
        print("\n" + "=" * 60)
        print("  PIPELINE FAILED")
        print(f"  Error: {e}")
        print(f"  Check log file for details: {LOG_FILE}")
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()
