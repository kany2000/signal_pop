"""Re-run video build only (skip parse/images/tts, those are already done)."""
import sys
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, os.path.join(_PROJECT_ROOT, 'scripts'))

from win_pipeline_daily import (
    parse_daily_script,
    build_video,
    step,
)

OUT_DIR = os.path.join(_PROJECT_ROOT, 'output', 'daily_20260806')
IMAGES_DIR = os.path.join(OUT_DIR, 'images')
AUDIO_PATH = os.path.join(OUT_DIR, 'audio', 'tts.wav')
SEGMENTS_PATH = os.path.join(OUT_DIR, 'audio', 'tts_segments.json')
SCRIPT_FILE = os.path.join(_PROJECT_ROOT, 'archive', 'signal_pop_daily_20260806.txt')
PARSED_PATH = os.path.join(OUT_DIR, 'parsed_news.json')
OUTPUT_VIDEO = os.path.join(OUT_DIR, 'signal_pop_daily_20260806.mp4')


def main():
    # Re-parse script to get fresh items
    with open(SCRIPT_FILE, 'r', encoding='utf-8') as f:
        text = f.read()
    items = parse_daily_script(text)
    if not items:
        print("ERROR: parsed 0 items")
        sys.exit(1)
    print(f"Parsed {len(items)} items")

    # Save parsed JSON
    import json
    with open(PARSED_PATH, 'w', encoding='utf-8') as f:
        json.dump(items, f, ensure_ascii=False, indent=2)

    # Build video using existing images + audio
    step(f"Step 4/4: Build video -> {OUTPUT_VIDEO}")
    build_video(items, IMAGES_DIR, AUDIO_PATH, SEGMENTS_PATH, OUTPUT_VIDEO)
    print()
    print("=" * 60)
    print(f"  [OK] Video rebuilt")
    print(f"  Video: {OUTPUT_VIDEO}")
    print("=" * 60)


if __name__ == "__main__":
    main()