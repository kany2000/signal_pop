#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Signal Pop · 把逐字高亮字幕烧录到真实成片片段，产出可播放 MP4 demo

用 make_demo.py 生成的 karaoke_raw.ass（时间轴相对样本 0s），
从当期成片第 9s（片头结束、正片起）切出同长度片段并叠加 libass 卡拉OK字幕。
"""
import argparse
import os
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
FFMPEG_BIN = os.path.join(ROOT, "bin", "ffmpeg-9.0.1-essentials_build", "bin")
FFMPEG = os.path.join(FFMPEG_BIN, "ffmpeg.exe")
FFPROBE = os.path.join(FFMPEG_BIN, "ffprobe.exe")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default="20261106")
    ap.add_argument("--opening", type=float, default=9.0)
    ap.add_argument("--duration", type=float, default=41.693)
    ap.add_argument("--ass", default="karaoke_raw.ass")
    ap.add_argument("--out", default="karaoke_demo_20261106.mp4")
    ap.add_argument("--background", default=None,
                    help="指定静态背景图时生成干净的「纯字幕舞台」demo（不叠加成片，避开原字幕气泡）")
    args = ap.parse_args()

    src = os.path.join(ROOT, "output", "weekly", args.date,
                       f"signal_pop_weekly_{args.date}.mp4")
    out = os.path.join(HERE, args.out)
    if not os.path.exists(src):
        raise SystemExit(f"missing final video: {src}")

    if args.background:
        bg = args.background
        if not os.path.exists(bg):
            raise SystemExit(f"missing background image: {bg}")
        wav = os.path.join(HERE, "sample_16k.wav")
        cmd = [
            FFMPEG, "-y", "-v", "error",
            "-loop", "1", "-framerate", "30", "-i", bg,
            "-i", wav,
            "-t", f"{args.duration:.3f}",
            "-vf", f"scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,"
                   f"eq=brightness=-0.16:saturation=0.75,ass={args.ass}",
            "-c:v", "libx264", "-crf", "26", "-preset", "fast", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "128k", "-shortest",
            out,
        ]
    else:
        cmd = [
            FFMPEG, "-y", "-v", "error",
            "-ss", f"{args.opening:.3f}", "-i", src,
            "-t", f"{args.duration:.3f}",
            "-vf", f"ass={args.ass}",
            "-c:v", "libx264", "-crf", "26", "-preset", "fast", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "128k",
            out,
        ]
    print("[burn] " + " ".join(cmd), flush=True)
    subprocess.run(cmd, check=True, cwd=HERE)

    probe = subprocess.run(
        [FFPROBE, "-v", "error", "-show_entries", "format=duration,size",
         "-show_entries", "stream=codec_name,width,height,r_frame_rate",
         "-of", "default=noprint_wrappers=1", out],
        capture_output=True, text=True, check=True,
    )
    print("[burn] OK -> " + out)
    print(probe.stdout.strip())


if __name__ == "__main__":
    main()
