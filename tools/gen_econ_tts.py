#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""为周末版「大家一起聊经济」环节独立生成双播 TTS 音频与分段精确时长。
用法：python tools/gen_econ_tts.py [PREP_DATE]
读取：output/weekly/<PREP_DATE>/section_economy_talk_v1.md
输出：output/weekly/<PREP_DATE>/econ_audio/tts.wav
      output/weekly/<PREP_DATE>/econ_audio/tts_segments.json
"""
import os
import re
import sys
import asyncio

PROJECT_ROOT = "E:/projects/signal_pop"
sys.path.insert(0, os.path.join(PROJECT_ROOT, "tools"))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "scripts"))
import gen_dual_tts as G


def main():
    prep_date = sys.argv[1] if len(sys.argv) > 1 else "20261016"
    out_dir = os.path.join(PROJECT_ROOT, "output", "weekly", prep_date)
    md_path = os.path.join(out_dir, "section_economy_talk_v1.md")
    if not os.path.exists(md_path):
        print(f"ERROR: 找不到 {md_path}")
        sys.exit(1)

    raw = open(md_path, encoding="utf-8").read()
    body = raw.split("## 对话稿")[1].split("## 幻灯")[0]
    lines = []
    for l in body.splitlines():
        l = l.strip()
        if l.startswith("**小蓝**") or l.startswith("**阿信**"):
            lines.append(re.sub(r"\*\*(小蓝|阿信)\*\*", r"\1", l))

    script_txt = "\n".join(lines)
    segs = G.parse_talk(script_txt)
    print(f"解析出 {len(segs)} 段，BACKEND={G.BACKEND}")
    econ_audio_dir = os.path.join(out_dir, "econ_audio")
    asyncio.run(G.gen_tts_all(segs, out_dir=econ_audio_dir))


if __name__ == "__main__":
    main()
