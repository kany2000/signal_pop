#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Signal Pop 周末特别版 · 英文外挂字幕生成（无中文字幕版）

规则 #7（2026-08-21）：周末版不生成中文字幕 SRT，只保留英文外挂
signal_pop_weekly_{DATE}.en_US.srt（海外平台文案提取 + 质检用）。

本工具不同于 daily 版 gen_en_srt.py（它读中文 srt 翻译），这里直接读
talk_segments.json 的口语文本，用音频 wav 实际时长推算时间轴，再用
MyMemory 免费 API 逐段翻译成英文，写出与视频对齐的 en_US.srt。

用法：python tools/gen_weekly_en_srt.py [PREP_DATE]
依赖：Python 标准库 wave（读 wav 时长）+ urllib（MyMemory，无需 key）
"""
import os
import re
import sys
import time
import json
import wave
import urllib.parse
import urllib.request

PROJECT_ROOT = "E:/projects/signal_pop"
PREP_DATE = sys.argv[1] if len(sys.argv) > 1 else "20260821"
OUT_DIR = os.path.join(PROJECT_ROOT, "output", "weekly", PREP_DATE)
AUDIO_DIR = os.path.join(OUT_DIR, "audio")
SEG_JSON = os.path.join(OUT_DIR, "talk_segments.json")
SRT_EN = os.path.join(OUT_DIR, f"signal_pop_weekly_{PREP_DATE}.en_US.srt")


def seg_duration(idx):
    """读 audio/_sNNN.wav 实际时长（秒），失败回退 3.0。"""
    wav = os.path.join(AUDIO_DIR, f"_s{idx:03d}.wav")
    try:
        with wave.open(wav, "rb") as w:
            return w.getnframes() / float(w.getframerate())
    except Exception:
        return 3.0


def translate(text):
    """MyMemory 免费翻译 zh-CN -> en（带重试）。"""
    for attempt in range(3):
        try:
            q = urllib.parse.quote(text[:450])
            url = f"https://api.mymemory.translated.net/get?q={q}&langpair=zh-CN|en"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=30) as r:
                d = json.loads(r.read().decode("utf-8"))
            if d.get("responseStatus") == 200:
                t = d["responseData"]["translatedText"].strip()
                if t and "MYMEMORY WARNING" not in t:
                    return t
            return text
        except Exception:
            time.sleep(2)
    return text


def fmt(sec):
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = int(sec % 60)
    ms = int((sec - int(sec)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def main():
    if not os.path.exists(SEG_JSON):
        print(f"ERROR: 找不到 {SEG_JSON}")
        sys.exit(1)
    segs = json.load(open(SEG_JSON, encoding="utf-8"))

    out = []
    t = 0.0
    for i, seg in enumerate(segs):
        text = seg.get("text", "").strip()
        dur = seg_duration(i)
        start = t
        end = t + dur
        if text:
            en = translate(text)
            print(f"  [{i + 1}] {text[:28]}... -> {en[:46]}")
            out.append(f"{i + 1}\n{fmt(start)} --> {fmt(end)}\n{en}\n")
        else:
            out.append(f"{i + 1}\n{fmt(start)} --> {fmt(end)}\n\n")
        t = end
        time.sleep(0.6)  # 限速，避免 MyMemory 频率限制

    with open(SRT_EN, "w", encoding="utf-8") as f:
        f.write("\n".join(out))
    print(f"\n✅ 英文字幕已生成: {SRT_EN}（{len(segs)} 段）")


if __name__ == "__main__":
    main()
