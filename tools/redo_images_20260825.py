#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""20260825 定向重做配图：opening_bg + 04~09（基于真实报道重写提示词，Sensenova 原图带水印输出）。
不触碰其他图，不处理水印。"""
import os
import sys

ROOT = "E:/projects/signal_pop"
sys.path.insert(0, os.path.join(ROOT, "scripts"))
sys.path.insert(0, ROOT)

from win_pipeline_images import download_image  # noqa: E402

OUT_DIR = os.path.join(ROOT, "output", "daily", "20260825", "images")

NO_TXT = ", no text, no words, no letters, no numbers, no signs, no labels, no UI, clean image without any writing"

REDO = {
    "opening_bg.jpg": (
        "Chinese television news broadcasting studio, professional modern studio with blue and gold lighting, "
        "a large LED video wall glowing with abstract blue light patterns behind a sleek broadcast desk, "
        "clean elegant set, cinematic professional photography"
        + NO_TXT
    ),
    "04.jpg": (
        "a symbolic Canada-United States trade standoff at an international border crossing, long rows of "
        "shipping containers and freight trucks queued on both sides of the border, a Canadian maple-leaf flag "
        "and an American stars-and-stripes flag facing each other across the lane, a translucent glowing "
        "barrier wall representing new tariffs between the two sides, dramatic overcast sky, cool steel-blue "
        "and grey palette, cinematic wide shot, no people"
        + NO_TXT
    ),
    "05.jpg": (
        "the Second World Humanoid Robot Games inside Beijing National Speed Skating Oval Ice Ribbon, humanoid "
        "robots competing across multiple events on one arena floor, robot sprinters racing on a 100m track, a "
        "robot lifting a barbell at a weightlifting platform, robots playing table tennis and football, robot "
        "dancers performing, bright spotlights and a futuristic stadium, thousands of spectator silhouettes in "
        "the stands, dynamic multi-event robotics competition, cinematic wide shot, no people"
        + NO_TXT
    ),
    "06.jpg": (
        "an EH216-S passenger eVTOL aircraft taking off vertically from a riverside urban helipad along the "
        "Pearl River in Guangzhou at golden hour, the Canton Tower and city skyscrapers in the background, a "
        "small delivery drone flying nearby, low-altitude economy over a modern Chinese megacity, cinematic "
        "aerial perspective, no people"
        + NO_TXT
    ),
    "07.jpg": (
        "a warm neighborhood chess-and-card shop in a Chinese county town, a kind female shopkeeper in an apron "
        "helping an elderly man who feels faint to sit, another customer calling emergency services on a phone, "
        "soft daylight through the doorway, compassionate community atmosphere, documentary photography"
        + NO_TXT
    ),
    "08.jpg": (
        "a residential home in a Sichuan riverside town after a mild earthquake, cracked wall tiles and a few "
        "fallen items on the floor, a resident standing at the open doorway looking outside where neighbors have "
        "gathered outdoors, muted earthy tones, documentary photography"
        + NO_TXT
    ),
    "09.jpg": (
        "badminton men's doubles championship celebration at an indoor arena in New Delhi, two Chinese athletes "
        "embracing and raising a gold medal after winning the world championship, a shuttlecock and rackets "
        "beside them, dramatic floodlights, victory atmosphere, sports photography"
        + NO_TXT
    ),
}


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    for i, (fname, prompt) in enumerate(REDO.items()):
        out_path = os.path.join(OUT_DIR, fname)
        seed = 1000 + i * 7
        # 先删旧图，确保覆盖（download_image 会覆盖写，但显式删除更稳）
        if os.path.exists(out_path):
            os.remove(out_path)
        logger_tag = fname.replace(".jpg", "")
        print(f"[redo {logger_tag}] regenerating...")
        ok = download_image(prompt, seed, out_path)
        print(f"  -> {'OK' if ok else 'FAILED'} ({out_path})")
    print("===== 20260825 定向重做完成（opening_bg + 04~09，带水印原图，待用户自清） =====")


if __name__ == "__main__":
    main()
