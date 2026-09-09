#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Signal Pop — 横竖版转换（参考 Easel video-reframe）

把 16:9 成片转成 9:16 竖版，供抖音 / 快手 / 微信视频号（竖屏流量更好）。
做法：模糊背景填充 + 前景居中（不裁掉内容，避免新闻文字被切）。

两种模式：
  --mode fit    （默认）整帧缩放至宽 1080，模糊背景补上下，内容零裁切
  --mode cover  缩放铺满高度 1920 后居中裁左右（更沉浸，但可能切边）

用法：
  python tools/make_vertical.py 20260908
  python tools/make_vertical.py 20260908 --mode cover --crf 26
  python tools/make_vertical.py --input out.mp4 --output out_9x16.mp4

输出：output/daily/{date}/signal_pop_daily_{date}_9x16.mp4（竖版）
约定：CRF 26 / yuv420p(tv) 与正片管线一致。
"""
import os
import sys
import subprocess
import argparse

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FFMPEG = os.path.join(
    PROJECT_ROOT, "bin", "ffmpeg-9.0.1-essentials_build", "bin", "ffmpeg.exe"
)
FFPROBE = os.path.join(
    PROJECT_ROOT, "bin", "ffmpeg-9.0.1-essentials_build", "bin", "ffprobe.exe"
)

W, H = 1080, 1920  # 9:16


def run(cmd):
    print("+ " + " ".join(cmd), flush=True)
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stderr[-2000:], file=sys.stderr)
    return r


def probe_dims(path):
    try:
        r = subprocess.run(
            [FFPROBE, "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=width,height", "-of", "csv=p=0", path],
            capture_output=True, text=True, timeout=30,
        )
        if r.returncode != 0:
            return None
        parts = [x for x in r.stdout.strip().split(",") if x.strip()]
        if len(parts) < 2:
            return None
        return int(parts[0]), int(parts[1])
    except Exception:
        return None


def build_filter(mode):
    if mode == "cover":
        # 铺满高度 1920 → 居中裁左右
        return (
            "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,"
            "crop=1080:1920,gblur=28[bg];"
            "[0:v]scale=-1:1920:force_original_aspect_ratio=decrease[fg];"
            "[bg][fg]overlay=(1080-w)/2:(1920-h)/2[v]"
        )
    # fit（默认）：整帧宽 1080，模糊背景补上下，零裁切
    return (
        "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,"
        "crop=1080:1920,gblur=28[bg];"
        "[0:v]scale=1080:-1:force_original_aspect_ratio=decrease[fg];"
        "[bg][fg]overlay=0:(1920-h)/2[v]"
    )


def make_vertical(in_path, out_path, mode="fit", crf=26):
    if not os.path.exists(in_path):
        raise SystemExit(f"输入视频不存在: {in_path}")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    vf = build_filter(mode)
    cmd = [
        FFMPEG, "-y", "-i", in_path,
        "-filter_complex", vf,
        "-map", "[v]", "-map", "0:a?",
        "-c:a", "aac", "-b:a", "128k",
        "-c:v", "libx264", "-crf", str(crf), "-preset", "fast",
        "-pix_fmt", "yuv420p", "-color_range", "tv",
        "-movflags", "+faststart",
        out_path,
    ]
    r = run(cmd)
    if r.returncode != 0:
        raise SystemExit(f"ffmpeg 失败: {r.returncode}")
    dims = probe_dims(out_path)
    size = os.path.getsize(out_path) // 1024 // 1024
    dims_str = f"{dims[0]}x{dims[1]}" if dims else "?"
    print(f"✅ 竖版产出: {out_path}  ({dims_str}, {size}MB)")
    if dims != (W, H):
        print(f"⚠️ 尺寸异常，期望 {W}x{H}，实际 {dims}")
        return False
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("date", nargs="?", help="制作日 YYYYMMDD（与 --input 二选一）")
    ap.add_argument("--kind", default="daily", choices=["daily", "weekly"])
    ap.add_argument("--input", help="直接指定输入视频")
    ap.add_argument("--output", help="直接指定输出视频")
    ap.add_argument("--mode", default="fit", choices=["fit", "cover"])
    ap.add_argument("--crf", type=int, default=26)
    args = ap.parse_args()

    if args.input:
        in_path = args.input
        out_path = args.output or (os.path.splitext(in_path)[0] + "_9x16.mp4")
    else:
        if not args.date:
            ap.error("需提供 date 或 --input")
        base = f"signal_pop_{args.kind}_{args.date}"
        in_path = os.path.join(PROJECT_ROOT, "output", args.kind, args.date, f"{base}.mp4")
        out_path = os.path.join(PROJECT_ROOT, "output", args.kind, args.date, f"{base}_9x16.mp4")

    ok = make_vertical(in_path, out_path, args.mode, args.crf)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
