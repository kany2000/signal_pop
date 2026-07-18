#!/usr/bin/env python3
"""
Signal Pop — 视频生成 (HeyGen / D-ID / 本地 ffmpeg 合成)
输入：音频 MP3 + SRT 字幕 + 可选背景图/虚拟主播
输出：MP4 视频
"""
import os
import sys
import json
import subprocess
import argparse
from pathlib import Path

# ========== 配置 ==========
OUTPUT_DIR = "/home/kan/signal_pop/output"
ASSETS_DIR = "/home/kan/signal_pop/assets"  # 背景图、Logo、水印等
os.makedirs(ASSETS_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 默认背景图（可替换为实际素材）
DEFAULT_BG = f"{ASSETS_DIR}/studio_bg.jpg"
LOGO_PATH = f"{ASSETS_DIR}/logo.png"
WATERMARK_PATH = f"{ASSETS_DIR}/watermark.png"

# 视频规格
VIDEO_WIDTH = 1920
VIDEO_HEIGHT = 1080
FPS = 30
FONT_SIZE = 48
FONT_COLOR = "white"
BOX_COLOR = "0x000000AA"  # 半透明黑底


def get_ffmpeg():
    """获取 ffmpeg 路径"""
    venv_ffmpeg = "/home/kan/.hermes/hermes-agent/venv/lib/python3.11/site-packages/imageio_ffmpeg/binaries/ffmpeg-linux-x86_64-v7.0.2"
    if os.path.exists(venv_ffmpeg):
        return venv_ffmpeg
    return "ffmpeg"


def get_audio_duration(audio_path: str) -> float:
    """获取音频时长（秒）"""
    ffmpeg = get_ffmpeg()
    result = subprocess.run(
        [ffmpeg, "-i", audio_path, "-f", "null", "-"],
        capture_output=True, text=True
    )
    # 从 stderr 解析时长
    import re
    match = re.search(r"time=(\d+):(\d+):(\d+\.\d+)", result.stderr)
    if match:
        h, m, s = match.groups()
        return int(h) * 3600 + int(m) * 60 + float(s)
    return 0.0


def parse_srt(srt_path: str) -> list:
    """解析 SRT 字幕文件，返回 [(start_sec, end_sec, text), ...]"""
    import re
    segments = []
    if not os.path.exists(srt_path):
        return segments
    with open(srt_path, encoding="utf-8") as f:
        content = f.read()
    blocks = content.strip().split("\n\n")
    for block in blocks:
        lines = block.strip().split("\n")
        if len(lines) < 3:
            continue
        # 时间行: 00:00:01,500 --> 00:00:04,200
        time_line = lines[1]
        match = re.match(r"(\d+):(\d+):(\d+),(\d+) --> (\d+):(\d+):(\d+),(\d+)", time_line)
        if not match:
            continue
        h1, m1, s1, ms1, h2, m2, s2, ms2 = map(int, match.groups())
        start = h1 * 3600 + m1 * 60 + s1 + ms1 / 1000
        end = h2 * 3600 + m2 * 60 + s2 + ms2 / 1000
        text = " ".join(lines[2:])
        segments.append((start, end, text))
    return segments


def build_drawtext_filter(segments: list, video_w: int, video_h: int) -> str:
    """构建 ffmpeg drawtext 滤镜字符串"""
    filters = []
    for i, (start, end, text) in enumerate(segments):
        # 转义文本中的特殊字符
        safe_text = text.replace("'", r"\'").replace(":", r"\:").replace(",", r"\,")
        # 字幕位置：底部居中，留出边距
        y_pos = f"h-{FONT_SIZE * 2}-50"
        filter_str = (
            f"drawtext="
            f"fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf:"
            f"text='{safe_text}':"
            f"fontsize={FONT_SIZE}:"
            f"fontcolor={FONT_COLOR}:"
            f"box=1:boxcolor={BOX_COLOR}:"
            f"boxborderw=10:"
            f"x=(w-tw)/2:y={y_pos}:"
            f"enable='between(t,{start},{end})'"
        )
        filters.append(filter_str)
    return ",".join(filters)


def generate_video_local(audio_path: str, srt_path: str, output_path: str, bg_image: str = None) -> str:
    """
    本地 ffmpeg 合成视频：背景图/视频 + 音频 + 字幕烧录
    """
    ffmpeg = get_ffmpeg()
    
    # 确定背景输入
    if bg_image and os.path.exists(bg_image):
        bg_input = ["-loop", "1", "-i", bg_image]
    else:
        # 生成纯色背景
        bg_input = ["-f", "lavfi", "-i", f"color=c=0x1a1a2e:size={VIDEO_WIDTH}x{VIDEO_HEIGHT}:rate={FPS}"]
    
    # 解析字幕
    segments = parse_srt(srt_path)
    drawtext_filter = build_drawtext_filter(segments, VIDEO_WIDTH, VIDEO_HEIGHT) if segments else ""
    
    # 构建滤镜链
    filter_complex = []
    if drawtext_filter:
        filter_complex.append(f"[0:v]{drawtext_filter}[vout]")
        filter_complex = ["-filter_complex", ";".join(filter_complex), "-map", "[vout]"]
    else:
        filter_complex = ["-map", "0:v"]
    
    # 音频时长
    duration = get_audio_duration(audio_path)
    if duration <= 0:
        print(f"[Video] ⚠️ 无法获取音频时长，使用字幕推算")
        duration = max((end for _, end, _ in segments), default=60)
    
    cmd = [
        ffmpeg, "-y",
        *bg_input,
        "-i", audio_path,
        *filter_complex,
        "-map", "1:a",
        "-t", str(duration + 1),  # 留 1 秒缓冲
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-crf", "28",
        "-c:a", "aac",
        "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-r", str(FPS),
        output_path
    ]
    
    print(f"[Video] 🎬 生成视频: {output_path}")
    print(f"[Video] ⏱️ 时长: {duration:.1f}s, 字幕段数: {len(segments)}")
    
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if result.returncode != 0:
        print(f"[Video] ❌ ffmpeg 失败: {result.stderr[-500:]}", file=sys.stderr)
        raise RuntimeError(f"Video generation failed: {result.stderr}")
    
    print(f"[Video] ✅ 完成: {output_path}")
    return output_path


def main():
    parser = argparse.ArgumentParser(description="Signal Pop 视频生成")
    parser.add_argument("mode", choices=["daily", "weekly"], help="模式")
    parser.add_argument("--date", help="日期 YYYYMMDD，默认今天")
    parser.add_argument("--bg", help="背景图路径")
    args = parser.parse_args()
    
    from datetime import datetime
    date_str = args.date or datetime.now().strftime("%Y%m%d")
    mode = args.mode
    
    subdir = f"{OUTPUT_DIR}/{mode}"
    audio_path = f"{subdir}/signal_pop_{mode}_latest.mp3"
    srt_path = f"{subdir}/signal_pop_{mode}_latest.srt"
    output_path = f"{subdir}/signal_pop_{mode}_{date_str}.mp4"
    
    if not os.path.exists(audio_path):
        print(f"[Video] ❌ 音频不存在: {audio_path}", file=sys.stderr)
        sys.exit(1)
    if not os.path.exists(srt_path):
        print(f"[Video] ⚠️ 字幕不存在: {srt_path}，将生成无字幕视频")
        srt_path = None
    
    bg = args.bg or (f"{ASSETS_DIR}/studio_bg.jpg" if os.path.exists(f"{ASSETS_DIR}/studio_bg.jpg") else None)
    
    generate_video_local(audio_path, srt_path, output_path, bg)
    
    # 同时更新 _latest.mp4
    latest_mp4 = f"{subdir}/signal_pop_{mode}_latest.mp4"
    import shutil
    shutil.copy(output_path, latest_mp4)
    print(f"[Video] ✅ 已更新: {latest_mp4}")


if __name__ == "__main__":
    main()