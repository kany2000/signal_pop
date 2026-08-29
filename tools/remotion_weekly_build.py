#!/usr/bin/env python3
"""Signal Pop — Remotion 周末版管线：视频轨 + 音频合并

用法:
  python tools/remotion_weekly_build.py [制作日YYYYMMDD]

流程:
  1. 读 weekly_segs.json（Remotion 数据）+ audio/tts.wav（TTS 音频）
  2. Remotion 渲染画面轨（静音 mp4）— 需先手动执行 remotion render
  3. ffmpeg 合并音频 → signal_pop_weekly_{date}.mp4
"""
import sys, os, json, subprocess

PROJECT_ROOT = "E:/projects/signal_pop"
FFMPEG = "E:/projects/signal_pop/bin/ffmpeg-9.0.1-essentials_build/bin/ffmpeg.exe"

def merge_audio(video_path, audio_path, output_path, crf=26):
    """视频轨 + 音频 合并（视频 libx264 CRF 压缩，音频保持原始时长）

    CRF 说明（2026-08-21 用户确认目标 ~26MB/3min）:
      Remotion 默认 CRF 18 → 1080p 3388kb/s ≈ 76MB，太大
      CRF 26 → 1061kb/s ≈ 26MB（画质清晰，与旧管线 CRF 20-22 风格一致）
    """
    cmd = [
        FFMPEG, "-y",
        "-i", video_path,
        "-i", audio_path,
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", str(crf),
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-ar", "24000",
        "-ac", "1",
        "-af", "loudnorm=I=-14:TP=-1.5:LRA=11",  # 整片响度标准化，兜底消除段间残留波动
        "-map", "0:v:0",
        "-map", "1:a:0",
        output_path,
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if r.returncode != 0:
        print(r.stderr[-600:])
        raise SystemExit(f"ffmpeg merge failed: {r.returncode}")
    print(f"✅ 合并完成: {output_path} ({os.path.getsize(output_path)//1024//1024}MB)")


def check_timeline(date):
    """校验 Remotion 画面轨时长 == 音频时长"""
    out_dir = os.path.join(PROJECT_ROOT, "output", "weekly", date)
    segs_path = os.path.join(PROJECT_ROOT, "remotion_poc", "src", "weekly_segs.json")
    audio_path = os.path.join(out_dir, "audio", "tts.wav")
    if not os.path.exists(segs_path):
        print("❌ weekly_segs.json 不存在，需先导出"); return
    segs = json.load(open(segs_path, encoding="utf-8"))
    seg_total = sum(s["dur"] for s in segs)
    r = subprocess.run([FFMPEG, "-i", audio_path], capture_output=True, text=True)
    import re
    m = re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)", r.stderr)
    if m:
        h, mm, ss = map(float, m.groups())
        audio_total = h * 3600 + mm * 60 + ss
    else:
        audio_total = -1
    print(f"视频段总时长: {seg_total:.2f}s, 音频时长: {audio_total:.2f}s, 差值: {abs(seg_total-audio_total):.2f}s")
    return abs(seg_total - audio_total) < 0.5


if __name__ == "__main__":
    date = sys.argv[1] if len(sys.argv) > 1 else "20260821"
    out_dir = os.path.join(PROJECT_ROOT, "output", "weekly", date)
    silent = os.path.join(PROJECT_ROOT, "remotion_poc", "out", "WeeklyTalk_silent.mp4")
    audio = os.path.join(out_dir, "audio", "tts.wav")
    out = os.path.join(out_dir, f"signal_pop_weekly_{date}.mp4")
    if not os.path.exists(silent):
        print(f"❌ 画面轨不存在: {silent}（先跑 remotion render）"); sys.exit(1)
    if not os.path.exists(audio):
        print(f"❌ 音频不存在: {audio}"); sys.exit(1)
    os.makedirs(out_dir, exist_ok=True)
    check_timeline(date)
    crf = 26
    if "--crf" in sys.argv:
        crf = int(sys.argv[sys.argv.index("--crf") + 1])
    merge_audio(silent, audio, out, crf=crf)
