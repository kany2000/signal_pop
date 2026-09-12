#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Signal Pop 周末特别版 · 英文外挂字幕生成（无中文字幕版）

规则 #7（2026-08-21）：周末版不生成中文字幕 SRT，只保留英文外挂
signal_pop_weekly_{DATE}.en_US.srt（海外平台文案提取 + 质检用）。

本工具不同于 daily 版 gen_en_srt.py（它读中文 srt 翻译），这里直接读
talk_segments.json 的口语文本，用音频 wav 实际时长推算时间轴，再用
MyMemory 免费 API 逐段翻译成英文，写出与视频对齐的 en_US.srt。

2026-09-12：接入 subtitle_layout 智能换行（移植自 short-video-factory 的
line-break 算法）——每条字幕最多 2 行、行首禁则标点、中英混排自适应，
替代原先「整段译文单行」的写法。新增 --rewrap 离线模式：对已生成的
SRT 直接重排换行，不重跑网络翻译。

用法：python tools/gen_weekly_en_srt.py [PREP_DATE]
      python tools/gen_weekly_en_srt.py [PREP_DATE] --rewrap   # 仅重排换行
依赖：Python 标准库 wave（读 wav 时长）+ urllib（MyMemory，无需 key）；
      换行度量优先 Pillow+jieba（缺失自动退化，不阻塞）
"""
import os
import re
import sys
import time
import json
import wave
import urllib.parse
import urllib.request

_TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
if _TOOLS_DIR not in sys.path:
    sys.path.insert(0, _TOOLS_DIR)

from subtitle_layout import wrap_srt_text  # noqa: E402

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


TIMING_RE = re.compile(r"\d{1,2}:\d{2}:\d{2}[,.]\d{3}\s*-->\s*\d{1,2}:\d{2}:\d{2}[,.]\d{3}")


def parse_srt_cues(raw):
    """解析 SRT 为 cue 列表 [{idx, timing, text:[原始行]}]。

    兼容两种写法：标准「空行分隔」与 gen_weekly_publish_assets 产出的
    「单换行紧凑」格式——统一按「序号行 + 时间轴行」扫描，不按空行 split。
    注意：cue 内「序号行」和「时间轴行」是同一个 cue 的两段，不能
    在时间轴处重复开新 cue（首版曾因此把 58 条解析成 116 条）。
    """
    lines = raw.strip().splitlines()
    TIM = TIMING_RE
    cues = []
    cur = None  # dict(idx, timing, text)
    n = len(lines)
    for i, line in enumerate(lines):
        s = line.strip()
        nxt = lines[i + 1].strip() if i + 1 < n else ""
        if cur is not None and not cur["timing"] and TIM.search(s):
            cur["timing"] = s  # 当前 cue 还没时间轴：此行就是它的时间轴
        elif TIM.search(s):
            if cur:
                cues.append(cur)
            cur = {"idx": "", "timing": s, "text": []}
        elif cur is None:
            if s:
                cur = {"idx": s, "timing": "", "text": []}
        elif s.isdigit() and TIM.search(nxt):
            cues.append(cur)  # 新 cue 起点：纯数字行且下一行是时间轴
            cur = {"idx": s, "timing": "", "text": []}
        else:
            cur["text"].append(line)
    if cur:
        cues.append(cur)
    return cues


def rewrap_srt():
    """离线重排：读已有 SRT，解开旧行再按智能换行重排（不重跑翻译）。"""
    if not os.path.exists(SRT_EN):
        print(f"ERROR: 找不到 {SRT_EN}")
        sys.exit(1)
    raw = open(SRT_EN, encoding="utf-8").read()
    cues = parse_srt_cues(raw)
    out_blocks = []
    changed = 0
    for i, cue in enumerate(cues):
        idx = cue["idx"] or str(i + 1)
        if not cue["timing"]:  # 异常 cue：原样回写
            out_blocks.append("\n".join([idx] + cue["text"]))
            continue
        text = " ".join(t.strip() for t in cue["text"] if t.strip())
        new_text = wrap_srt_text(text) if text else ""
        if new_text != text:
            changed += 1
        block = [idx, cue["timing"]] + ([new_text] if new_text else [])
        out_blocks.append("\n".join(block))
    with open(SRT_EN, "w", encoding="utf-8") as f:
        f.write("\n\n".join(out_blocks) + "\n")
    print(f"✅ 智能换行重排完成: {SRT_EN}（{changed}/{len(cues)} 条变更，已标准化为空行分隔）")


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
            out.append(f"{i + 1}\n{fmt(start)} --> {fmt(end)}\n{wrap_srt_text(en)}\n")
        else:
            out.append(f"{i + 1}\n{fmt(start)} --> {fmt(end)}\n\n")
        t = end
        time.sleep(0.6)  # 限速，避免 MyMemory 频率限制

    with open(SRT_EN, "w", encoding="utf-8") as f:
        f.write("\n".join(out))
    print(f"\n✅ 英文字幕已生成: {SRT_EN}（{len(segs)} 段）")


if __name__ == "__main__":
    if "--rewrap" in sys.argv:
        rewrap_srt()
    else:
        main()
