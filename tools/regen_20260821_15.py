#!/usr/bin/env python3
"""重做 15 配图（村字号赛事·乡村篮球赛），新提示词"""
import os, sys
sys.path.insert(0, os.path.join("E:/projects/signal_pop", "scripts"))
from win_pipeline_images import download_image

OUT = "E:/projects/signal_pop/output/weekly/20260821/images/15.jpg"

PROMPT = (
    "night scene of a village basketball court in rural China, "
    "simple concrete court with a basic basketball hoop and backboard, "
    "warm string lights hanging across the court, "
    "wooden benches and villagers watching from the sidelines in the distance, "
    "countryside houses and trees silhouetted behind, "
    "lively grassroots village sports festival atmosphere, "
    "warm evening light, cinematic photography, "
    "no text, no words, no letters, no numbers, no signage, no people closeup, no hands"
)

print("[15.jpg] 重新生成...")
download_image(PROMPT, seed=1500 + 13, out_path=OUT)
print("✅ 完成")
