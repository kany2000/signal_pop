#!/usr/bin/env python3
"""Regenerate images 9 and 10 for daily_20260806 with corrected visual prompts."""
import sys
import os

# Resolve project root and add scripts dir to path
_HERE = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, os.path.join(_PROJECT_ROOT, 'scripts'))

from win_pipeline_daily import download_image

OUT_DIR = os.path.join(_PROJECT_ROOT, 'output', 'daily_20260806', 'images')

# Item 9: Ancient bronze wine vessel (correct prompt - emphasize the 2300-year sealed wine)
PROMPT_9 = (
    "Ancient bronze garlic-head-shaped wine vessel being carefully unsealed by gloved "
    "archaeologist hands, 2300-year-old sealed ancient grain wine inside being revealed, "
    "close-up macro shot of the bronze ritual vessel with intricate Chinese Warring States "
    "period patterns, golden liquid glinting inside the unsealed vessel, sterile laboratory "
    "archaeological environment with bright white lighting, dramatic museum-quality "
    "documentation photography, single vessel as the hero subject, "
    "no text, no words, no letters, no numbers, no characters, no typography, no signage, "
    "no labels, no captions, no UI, no writing, no screens with text, no charts, no data "
    "displays, no any text whatsoever, completely text-free image, no monitors with text, "
    "no screens showing data"
)

# Item 10: Sanitation worker wearing smart cooling vest (NOT a robot)
PROMPT_10 = (
    "Real Chinese sanitation worker wearing smart cooling vest with built-in micro "
    "refrigeration system, close-up portrait of a middle-aged urban street cleaner in "
    "orange high-visibility reflective vest with futuristic wearable air-conditioning "
    "device on torso, worker smiling confidently in summer heat on a clean modern city "
    "street, midday sunlight, the cooling vest technology is the hero subject, "
    "no text, no words, no letters, no numbers, no characters, no typography, no signage, "
    "no labels, no captions, no UI, no writing, no screens with text, no charts, no data "
    "displays, no any text whatsoever, completely text-free image, no monitors with text, "
    "no screens showing data"
)


def main():
    out9 = os.path.join(OUT_DIR, '09.jpg')
    out10 = os.path.join(OUT_DIR, '10.jpg')

    print("=== Regenerating 09.jpg (2300-year sealed ancient wine) ===")
    ok9 = download_image(PROMPT_9, 909, out9)
    print(f"  -> 09.jpg result: {'OK' if ok9 else 'FAILED'}")
    print()

    print("=== Regenerating 10.jpg (sanitation worker cooling vest) ===")
    ok10 = download_image(PROMPT_10, 1010, out10)
    print(f"  -> 10.jpg result: {'OK' if ok10 else 'FAILED'}")
    print()

    print("Done.")


if __name__ == "__main__":
    main()