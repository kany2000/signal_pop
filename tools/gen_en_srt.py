#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Signal Pop — 生成英文字幕文件（en.srt）
读中文 SRT → 逐段翻译成英文 → 输出 *_en.srt（时间轴与中文版完全一致）
用法：python tools/gen_en_srt.py [PREP_DATE]
依赖：免费 MyMemory 翻译 API（无需 key）；SENSENOVA/MiMo 不可用于文本翻译
"""
import os
import re
import sys
import time
import json
import urllib.parse
import urllib.request

PROJECT_ROOT = "E:/projects/signal_pop"
PREP_DATE = sys.argv[1] if len(sys.argv) > 1 else "20260809"
OUT_DIR = os.path.join(PROJECT_ROOT, "output", "daily", PREP_DATE)
SRT_ZH = os.path.join(OUT_DIR, f"signal_pop_daily_{PREP_DATE}.srt")
SRT_EN = os.path.join(OUT_DIR, f"signal_pop_daily_{PREP_DATE}_en.srt")


def translate(text):
    """调用 MyMemory 免费翻译 zh-CN -> en（带重试）"""
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
            return text  # 翻译失败回退中文
        except Exception:
            time.sleep(2)
    return text


def main():
    if not os.path.exists(SRT_ZH):
        print(f"ERROR: 中文字幕不存在 {SRT_ZH}")
        sys.exit(1)

    with open(SRT_ZH, encoding="utf-8") as f:
        srt_text = f.read()

    # 按块解析：序号 + 时间行 + 文本
    blocks = re.split(r"\n\n+", srt_text.strip())
    out_blocks = []
    for b in blocks:
        lines = b.strip().split("\n")
        if len(lines) < 2:
            continue
        seq = lines[0].strip()
        time_line = lines[1].strip()
        text = " ".join(lines[2:]).strip()
        if not text:
            out_blocks.append(f"{seq}\n{time_line}\n\n")
            continue
        en = translate(text)
        print(f"  [{seq}] {text[:30]}... -> {en[:50]}")
        out_blocks.append(f"{seq}\n{time_line}\n{en}\n")
        time.sleep(0.5)  # 限速，避免触发频率限制

    with open(SRT_EN, "w", encoding="utf-8") as f:
        f.write("\n".join(out_blocks))
    print(f"\n英文字幕已生成: {SRT_EN}")


if __name__ == "__main__":
    main()
