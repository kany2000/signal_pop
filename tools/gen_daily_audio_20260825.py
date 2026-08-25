#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""20260825 平日版：解析 archive -> parsed_news.json，再生成 TTS 音频。
复用既有模块：tools/run_daily_video.parse_daily_script + scripts/win_pipeline_tts.gen_tts。
注意：不重新生成配图（配图已由用户清完水印）。
"""
import os
import sys
import json
import asyncio

PROJECT_ROOT = "E:/projects/signal_pop"
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, "tools"))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "scripts"))

from datetime import datetime, timedelta
from tools.run_daily_video import parse_daily_script
from scripts.win_pipeline_tts import gen_tts

PREP = "20260825"
SCRIPT_FILE = os.path.join(PROJECT_ROOT, "archive", f"signal_pop_daily_{PREP}.txt")
OUT_DIR = os.path.join(PROJECT_ROOT, "output", "daily", PREP)
AUDIO_DIR = os.path.join(OUT_DIR, "audio")
PARSED = os.path.join(OUT_DIR, "parsed_news.json")
AUDIO = os.path.join(AUDIO_DIR, "tts.wav")

PUB = datetime.strptime(PREP, "%Y%m%d") + timedelta(days=1)
PUB_FMT = f"{PUB.year}年{PUB.month:02d}月{PUB.day:02d}日"
PUB_WD = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"][PUB.weekday()]


def main():
    os.makedirs(AUDIO_DIR, exist_ok=True)
    text = open(SCRIPT_FILE, encoding="utf-8").read()
    items = parse_daily_script(text)
    if not items:
        print("ERROR: parse 0 items")
        sys.exit(1)
    json.dump(items, open(PARSED, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"✅ parsed {len(items)} items (历史+新闻)")
    for it in items:
        print(f"  #{it['num']:02d} [{it['section']}] {it['title'][:34]}")
    news = sum(1 for it in items if it.get('num', 0) != 0)
    print(f"  新闻条数(不含历史): {news}")

    print(f"\n=== TTS (发布日 {PUB_FMT} {PUB_WD}, 女声 Xiaoxiao) ===")
    asyncio.run(gen_tts(PARSED, AUDIO, PUB_FMT, PUB_WD))
    print(f"\n✅ TTS 完成: {AUDIO} ({os.path.getsize(AUDIO)//1024//1024}MB)")


if __name__ == "__main__":
    main()
