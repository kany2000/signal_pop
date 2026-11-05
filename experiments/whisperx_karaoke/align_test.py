#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Signal Pop · whisperX 逐字高亮字幕：真实 TTS 音频的强制对齐测试

关键设计（与常规 whisperX 用法不同）：
  * 本项目的 TTS 文稿是 100% 已知真值，**不需要 ASR 猜字**，只借 whisperX
    的 wav2vec2 强制对齐把每个字钉到时间轴上（transcript 直接喂已知文稿）。
  * 音频用 stdlib wave 读成 16k float32 ndarray 直接传入，绕开 whisperX
    load_audio() 内部调 ffmpeg 的 Windows PATH 陷阱。
  * 对齐结果再与原始文稿做 SequenceMatcher 回贴：模型词表外的标点、数字、
    拉丁字母（如「3.2℃」「AI」）保留原文并插值补时间，保证字幕文字零错字。

输出：
  align_raw.json  whisperX 原始结果（排查用）
  words.json      逐字时间戳（demo / 下期接入消费）
"""
import argparse
import difflib
import json
import os
import re
import sys
import time
import wave

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

import numpy as np  # noqa: E402
import whisperx  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_MODEL = os.path.join("G:", os.sep, "temp", "signal_pop_models", "wav2vec2-zh-cn")
PUNCT = set("，。！？；：、,.!?;:·—…“”‘’（）()《》〈〉「」『』％%~ \t\n")
CJK = re.compile(r"[\u4e00-\u9fff\u3400-\u4dbf]")
ALIGNABLE = re.compile(r"[\u4e00-\u9fff\u3400-\u4dbfA-Za-z0-9]")


def read_wav16k(path):
    with wave.open(path, "rb") as w:
        assert w.getframerate() == 16000, f"expect 16k, got {w.getframerate()}"
        assert w.getnchannels() == 1, "expect mono"
        raw = w.readframes(w.getnframes())
    a = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
    return a


def flatten_words(words):
    """whisperX word 可能是多字符；展开成单字并线性分配时间。"""
    flat = []
    for w in words or []:
        text = str(w.get("word", "") or "").strip()
        if not text:
            continue
        s, e, score = w.get("start"), w.get("end"), w.get("score")
        chars = list(text)
        for k, ch in enumerate(chars):
            if s is None or e is None:
                t0 = t1 = None
            else:
                t0 = float(s) + (float(e) - float(s)) * k / len(chars)
                t1 = float(s) + (float(e) - float(s)) * (k + 1) / len(chars)
            flat.append({"c": ch, "start": t0, "end": t1, "score": score})
    return flat


def reconcile(text, aligned_words, seg_start, seg_end):
    """把 whisperX 字级时间回贴到原始 TTS 文稿；标点/词表外字插值补时间。"""
    flat = flatten_words(aligned_words)
    # 只保留可对齐字符做序列匹配（模型不产出标点）
    a_idx = [i for i, c in enumerate(text) if ALIGNABLE.match(c)]
    A = [text[i] for i in a_idx]
    b_entries = [w for w in flat if ALIGNABLE.match(w["c"])]
    B = [w["c"] for w in b_entries]

    times = {}
    matcher = difflib.SequenceMatcher(None, A, B, autojunk=False)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag in ("equal", "replace"):
            n = min(i2 - i1, j2 - j1)
            for k in range(n):
                w = b_entries[j1 + k]
                if w["start"] is not None:
                    times[a_idx[i1 + k]] = (w["start"], w["end"], w["score"])
    # 补齐未匹配字符：用最近两侧已定时间线性插值
    known = sorted(times)
    for pos in a_idx:
        if pos in times:
            continue
        prev = [p for p in known if p < pos]
        nxt = [p for p in known if p > pos]
        left = times[prev[-1]][1] if prev else seg_start
        right = times[nxt[0]][0] if nxt else seg_end
        if right < left:
            right = left
        span = max(0.0, right - left)
        gaps_before = len([p for p in a_idx if p < pos and p not in known and (not prev or p > prev[-1])])
        t0 = left + span * min(0.9, gaps_before / 8.0)
        times[pos] = (t0, min(right, t0 + max(0.02, span * 0.4)), None)

    out = []
    for i, ch in enumerate(text):
        if i in times:
            s, e, score = times[i]
            out.append({"w": ch, "start": round(s, 4), "end": round(max(e, s + 0.01), 4),
                        "score": None if score is None else round(float(score), 4),
                        "punct": ch in PUNCT, "interp": score is None})
        else:
            # 标点/特殊符号：沿用前一个字的结尾（语音里对应停顿），不参与高亮
            prev_end = out[-1]["end"] if out else seg_start
            out.append({"w": ch, "start": round(prev_end, 4), "end": round(prev_end, 4),
                        "score": None, "punct": True, "interp": True})
    return out, len(A), len(flat)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", default=os.path.join(HERE, "sample_16k.wav"))
    ap.add_argument("--segments", default=os.path.join(HERE, "sample_segments.json"))
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--device", default="cpu")
    ap.add_argument("--out", default=os.path.join(HERE, "words.json"))
    ap.add_argument("--raw-out", default=os.path.join(HERE, "align_raw.json"))
    args = ap.parse_args()

    with open(args.segments, "r", encoding="utf-8") as f:
        meta = json.load(f)
    audio = read_wav16k(args.sample)
    print(f"[audio] {meta['duration']:.3f}s / {len(audio)/16000:.3f}s @16k mono", flush=True)

    # whisperX 只做强制对齐：transcript 用已知 TTS 文稿（含段落边界）
    transcript = [{"text": s["text"], "start": s["start"], "end": s["end"]}
                  for s in meta["segments"]]

    t0 = time.time()
    print(f"[model] loading {args.model} on {args.device} ...", flush=True)
    model_a, model_meta = whisperx.load_align_model(
        language_code="zh", device=args.device, model_name=args.model
    )
    print(f"[model] loaded in {time.time()-t0:.1f}s type={model_meta['type']}", flush=True)

    t1 = time.time()
    result = whisperx.align(
        transcript, model_a, model_meta, audio, args.device,
        return_char_alignments=True,
    )
    elapsed = time.time() - t1
    print(f"[align] done in {elapsed:.1f}s", flush=True)

    raw_segs = result["segments"] if isinstance(result, dict) else result
    with open(args.raw_out, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2, default=str)
    print(f"[raw  ] {args.raw_out}", flush=True)

    out_segs, total_chars, aligned_chars, matched = [], 0, 0, 0
    for src, raw in zip(meta["segments"], raw_segs):
        words, nA, nB = reconcile(src["text"], raw.get("words", []), src["start"], src["end"])
        total_chars += len(src["text"])
        aligned_chars += nB
        matched += sum(1 for w in words if not w["interp"])
        out_segs.append({
            "index": src["index"], "speaker": src["speaker"],
            "start": src["start"], "end": src["end"], "text": src["text"],
            "words": words,
        })
        print(f"  seg#{src['index']:02d} {src['start']:6.2f}-{src['end']:6.2f}s "
              f"chars={len(src['text']):3d} raw_words={nB:3d} "
              f"matched={sum(1 for w in words if not w['interp']):3d} "
              f"first={''.join(w['w'] for w in words[:12])}", flush=True)
        for w in words[:6]:
            print(f"       {w['w']!r} {w['start']:.3f}-{w['end']:.3f} "
                  f"score={w['score']} interp={w['interp']}", flush=True)

    stats = {
        "对齐模型": os.path.basename(args.model),
        "设备": args.device,
        "样本时长": f"{meta['duration']:.2f}s",
        "对齐耗时": f"{elapsed:.1f}s",
        "实时率": f"{elapsed/meta['duration']:.2f}×",
        "原文字数": total_chars,
        "模型给出字数": aligned_chars,
        "直接命中字数": matched,
        "命中率": f"{matched/total_chars*100:.1f}%",
        "插值补齐": total_chars - matched,
    }
    out = {
        "meta": {
            "date": meta["date"], "start": meta["source_start"], "end": meta["source_end"],
            "model": stats["对齐模型"], "device": args.device,
            "note": "已知 TTS 文稿 + whisperX wav2vec2 强制对齐；不经 ASR",
        },
        "stats": stats,
        "segments": out_segs,
    }
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"[words] {args.out}", flush=True)
    for k, v in stats.items():
        print(f"  {k}: {v}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
