#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Signal Pop · whisperX 逐字高亮字幕测试：样本准备

从某期周末版 audio/tts.wav + audio/tts_segments.json 切出一段真实音频，
并把已知 TTS 文稿按累计时长换算成带段落边界的 whisperX segments。

本项目 TTS 文稿是 100% 已知真值，所以逐字时间戳不需要 ASR 猜文本，
只用 whisperX 的强制对齐（wav2vec2）把每个字钉到时间轴上。
"""
import argparse
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FFMPEG_DIR = os.path.join(ROOT, "bin", "ffmpeg-9.0.1-essentials_build", "bin")
FFMPEG = os.path.join(FFMPEG_DIR, "ffmpeg.exe")


def load_timeline(seg_path):
    with open(seg_path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    segs, t = [], 0.0
    for i, item in enumerate(raw):
        dur = float(item["dur"])
        segs.append({
            "index": i,
            "start": t,
            "end": t + dur,
            "dur": dur,
            "speaker": item.get("speaker", ""),
            "text": item.get("text", ""),
        })
        t += dur
    return segs, t


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default="20261106")
    ap.add_argument("--start", type=float, default=0.0)
    ap.add_argument("--end", type=float, default=42.0)
    ap.add_argument("--out-dir", default=None)
    args = ap.parse_args()

    week_dir = os.path.join(ROOT, "output", "weekly", args.date)
    seg_path = os.path.join(week_dir, "audio", "tts_segments.json")
    wav_path = os.path.join(week_dir, "audio", "tts.wav")
    out_dir = args.out_dir or os.path.dirname(os.path.abspath(__file__))
    os.makedirs(out_dir, exist_ok=True)

    segs, total = load_timeline(seg_path)
    print(f"[timeline] segments={len(segs)} total={total:.3f}s source={seg_path}")

    a, b = args.start, min(args.end, total)
    picked = []
    for s in segs:
        if s["end"] <= a or s["start"] >= b:
            continue
        # 段落被样本边界切断时，按重叠区间裁文本比例（仅用于对齐边界，不猜字）
        picked.append({
            "index": s["index"],
            "start": round(max(s["start"], a) - a, 4),
            "end": round(min(s["end"], b) - a, 4),
            "seg_full_start": round(s["start"], 4),
            "seg_full_end": round(s["end"], 4),
            "speaker": s["speaker"],
            "text": s["text"],
            "clipped": max(s["start"], a) > s["start"] + 1e-6 or min(s["end"], b) < s["end"] - 1e-6,
        })

    sample_wav = os.path.join(out_dir, "sample_16k.wav")
    cmd = [
        FFMPEG, "-y", "-v", "error",
        "-ss", f"{a:.3f}", "-t", f"{b - a:.3f}",
        "-i", wav_path,
        "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", sample_wav,
    ]
    subprocess.run(cmd, check=True)
    print(f"[audio] {a:.3f}s -> {b:.3f}s ({(b-a):.3f}s) -> {sample_wav}")

    seg_out = os.path.join(out_dir, "sample_segments.json")
    with open(seg_out, "w", encoding="utf-8") as f:
        json.dump({
            "date": args.date,
            "source_start": a,
            "source_end": b,
            "duration": b - a,
            "total_audio_duration": total,
            "sample_wav": sample_wav,
            "segments": picked,
        }, f, ensure_ascii=False, indent=2)
    print(f"[segments] {len(picked)} 段 -> {seg_out}")
    for s in picked:
        flag = " (clipped)" if s["clipped"] else ""
        print(f"  #{s['index']:02d} {s['start']:7.3f}-{s['end']:7.3f}s "
              f"{s['speaker']}: {s['text'][:28]}...{flag}")


if __name__ == "__main__":
    sys.exit(main())
