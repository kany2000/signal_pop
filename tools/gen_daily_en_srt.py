#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Signal Pop 每日版 · 英文外挂字幕生成（无中文字幕版）

规则 #7（2026-08-21）：中文版视频不烧字幕、不生成中文字幕 SRT，只保留英文外挂
signal_pop_daily_{DATE}.en_US.srt（海外平台文案提取 + 质检用）。

与周末版 gen_weekly_en_srt.py 同思路：直接读 parsed_news.json 的口播文本
（复用 win_pipeline_tts.build_segments 的段文本逻辑）+ audio/tts_segments.json
的实际时长推算时间轴，再用 MyMemory 免费 API 逐段翻译成英文。

用法：python tools/gen_daily_en_srt.py [PREP_DATE]
"""
import os
import re
import sys
import json
import time
import urllib.parse
import urllib.request

PROJECT_ROOT = "E:/projects/signal_pop"
PREP_DATE = sys.argv[1] if len(sys.argv) > 1 else "20260823"
OUT_DIR = os.path.join(PROJECT_ROOT, "output", "daily", PREP_DATE)
PARSED = os.path.join(OUT_DIR, "parsed_news.json")
SEGMENTS = os.path.join(OUT_DIR, "audio", "tts_segments.json")
SRT_EN = os.path.join(OUT_DIR, f"signal_pop_daily_{PREP_DATE}.en_US.srt")


def build_segments_text(items):
    """与 win_pipeline_tts.build_segments 完全一致的段文本（不含 intro/outro 之外的前缀差异）。"""
    segs = []
    segs.append(("intro", "这里是隔天信号弹，今天是发布日，欢迎收看本期信号弹，以下是本期精选的核心新闻。"))
    for item in items:
        n = item.get("num", 0)
        if n == 0:
            segs.append(("item0", f"历史上的今天。{item['full_body']}"))
            continue
        txt = f"第{n}条，{item['section']}。{item['title']}。{item['full_body']}"
        if item.get("opinion"):
            txt += f".主播观点：{item['opinion']}"
        segs.append((f"item{n}", txt))
    segs.append(("outro", "您的一键三连是我们更新制作的动力。互动话题：您最关注哪条新闻？欢迎在评论区留言讨论！感谢您的关注，我们下期见~"))
    return segs


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
    if not os.path.exists(PARSED):
        print(f"ERROR: 找不到 {PARSED}")
        sys.exit(1)
    if not os.path.exists(SEGMENTS):
        print(f"ERROR: 找不到 {SEGMENTS}")
        sys.exit(1)
    items = json.load(open(PARSED, encoding="utf-8"))
    durations = json.load(open(SEGMENTS, encoding="utf-8"))
    segs = build_segments_text(items)

    if len(durations) != len(segs):
        print(f"ERROR: durations({len(durations)}) != segs({len(segs)})")
        sys.exit(1)

    out = []
    t = 0.0
    for i, (label, text) in enumerate(segs):
        dur = durations[i]
        start = t
        end = t + dur
        en = translate(text) if text.strip() else ""
        print(f"  [{i + 1}][{label}] {text[:28]}... -> {en[:46]}")
        out.append(f"{i + 1}\n{fmt(start)} --> {fmt(end)}\n{en}\n")
        t = end
        time.sleep(0.6)

    with open(SRT_EN, "w", encoding="utf-8") as f:
        f.write("\n".join(out))
    print(f"\n✅ 英文字幕已生成: {SRT_EN}（{len(segs)} 段，总长 {t:.1f}s）")


if __name__ == "__main__":
    main()
