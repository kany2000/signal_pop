#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Signal Pop — 每日版 Remotion 管线：渲染画面轨 + 合并音频

用法:
  python tools/export_daily_remotion.py 20260823    # 先生成 daily_segs.json + 配图
  node node_modules/@remotion/cli/remotion-cli.js render DailyNews out/DailyNews_silent.mp4 --codec=h264 \\
    --browser-executable="C:/Program Files/Google/Chrome/Application/chrome.exe"
  python tools/remotion_daily_build.py 20260823    # 合并音频，CRF 26

也可以直接：
  python tools/remotion_daily_build.py 20260823 --render   # 一次性执行数据导出+Remotion 渲染+合并

CRF 26（2026-08-21 用户长期规则，与周末版对齐）：~250kb/s，10 分钟视频约 22MB
"""
import os
import sys
import json
import subprocess

PROJECT_ROOT = "E:/projects/signal_pop"
REMOTION_POC = os.path.join(PROJECT_ROOT, "remotion_poc")
REMOTION_CLI = os.path.join(REMOTION_POC, "node_modules", "@remotion", "cli", "remotion-cli.js")
NODE = "C:/Users/Administrator/.workbuddy/binaries/node/versions/22.22.2-2/node.exe"
CHROME = "C:/Program Files/Google/Chrome/Application/chrome.exe"
FFMPEG = "E:/projects/signal_pop/bin/ffmpeg-9.0.1-essentials_build/bin/ffmpeg.exe"

WEEKDAYS = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]


def render_silent(date):
    """Remotion 渲染 DailyNews 画面轨（静音 mp4）。"""
    out = os.path.join(REMOTION_POC, "out", f"DailyNews_{date}_silent.mp4")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    cmd = [
        NODE, REMOTION_CLI, "render",
        os.path.join(REMOTION_POC, "src", "index.ts"),
        "DailyNews", out,
        "--codec=h264",
        f"--browser-executable={CHROME}",
    ]
    print(" ".join(cmd))
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=3600, cwd=REMOTION_POC)
    print(r.stdout[-1500:])
    if r.returncode != 0:
        print("STDERR:", r.stderr[-1500:])
        raise SystemExit(f"Remotion render failed: {r.returncode}")
    print(f"✅ 画面轨: {out} ({os.path.getsize(out)//1024//1024}MB)")
    return out


def merge_audio(video_path, audio_path, output_path, crf=26):
    """视频轨 + 音频 合并（CRF 26，对齐周末版约定）。"""
    cmd = [
        FFMPEG, "-y",
        "-i", video_path, "-i", audio_path,
        "-c:v", "libx264", "-preset", "fast", "-crf", str(crf), "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", "-ar", "24000", "-ac", "1",
        "-map", "0:v:0", "-map", "1:a:0",
        output_path,
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if r.returncode != 0:
        print(r.stderr[-600:])
        raise SystemExit(f"ffmpeg merge failed: {r.returncode}")
    print(f"✅ 合并完成: {output_path} ({os.path.getsize(output_path)//1024//1024}MB)")


def check_timeline(date):
    """校验画面轨时长 ≈ 音频时长。"""
    out_dir = os.path.join(PROJECT_ROOT, "output", "daily", date)
    segs_path = os.path.join(REMOTION_POC, "src", "daily_segs.json")
    audio_path = os.path.join(out_dir, "audio", "tts.wav")
    if not os.path.exists(segs_path) or not os.path.exists(audio_path):
        return False
    segs = json.load(open(segs_path, encoding="utf-8"))
    seg_total = sum(s["dur"] for s in segs)
    r = subprocess.run([FFMPEG, "-i", audio_path], capture_output=True, text=True)
    import re
    m = re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)", r.stderr)
    if m:
        h, mm, ss = map(float, m.groups())
        audio_total = h * 3600 + mm * 60 + ss
        print(f"  视频段总时长: {seg_total:.2f}s, 音频: {audio_total:.2f}s, 差值: {abs(seg_total-audio_total):.2f}s")
    return abs(seg_total - audio_total) < 1.0 if m else False


def main():
    date = sys.argv[1] if len(sys.argv) > 1 else "20260823"
    do_render = "--render" in sys.argv
    out_dir = os.path.join(PROJECT_ROOT, "output", "daily", date)
    silent = os.path.join(REMOTION_POC, "out", f"DailyNews_{date}_silent.mp4")
    audio = os.path.join(out_dir, "audio", "tts.wav")
    out = os.path.join(out_dir, f"signal_pop_daily_{date}.mp4")

    os.makedirs(out_dir, exist_ok=True)

    if do_render:
        print("=== 1/3 数据导出 ===")
        subprocess.run([sys.executable, os.path.join(PROJECT_ROOT, "tools", "export_daily_remotion.py"), date], check=True)
        print("\n=== 2/3 Remotion 渲染画面轨（首次需 ~10 分钟）===")
        silent = render_silent(date)

    if not os.path.exists(silent):
        print(f"❌ 画面轨不存在: {silent}（先跑 --render 或手动 remotion render）")
        sys.exit(1)
    if not os.path.exists(audio):
        print(f"❌ 音频不存在: {audio}")
        sys.exit(1)

    print("\n=== 3/3 合并音频（CRF 26）===")
    check_timeline(date)
    merge_audio(silent, audio, out, crf=26)


if __name__ == "__main__":
    main()
