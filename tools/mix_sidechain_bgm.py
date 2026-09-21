# -*- coding: utf-8 -*-
"""侧链闪避混音工具（mix_sidechain_bgm.py）

借鉴自开源项目 simontalk-investigation 的核心音频工艺：
    - 旁白人声说话时，背景音乐通过 sidechaincompress 滤镜毫秒级自动压低（ducking）；
    - 人声停顿/转场/呼吸气口时，BGM 在 350ms 内自然平滑回弹饱满；
    - 混音后经过 alimiter 峰值限幅（0.95），绝不破音；
    - 视频轨使用 -c:v copy，完全不重编码，极速导出。

用法示例：
    python tools/mix_sidechain_bgm.py input_video.mp4 bgm.mp3 -o output_video.mp4
    python tools/mix_sidechain_bgm.py input_video.mp4 bgm.mp3 --bgm-vol 0.20
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FFMPEG = ROOT / "bin" / "ffmpeg-9.0.1-essentials_build" / "bin" / "ffmpeg.exe"
FFPROBE = ROOT / "bin" / "ffmpeg-9.0.1-essentials_build" / "bin" / "ffprobe.exe"


def get_duration(media_path: Path) -> float:
    cmd = [
        str(FFPROBE), "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(media_path)
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    try:
        return float(res.stdout.strip())
    except (ValueError, IndexError):
        raise RuntimeError(f"无法读取媒体时长: {media_path} ({res.stderr})")


def mix_sidechain(
    video_path: Path,
    bgm_path: Path,
    output_path: Path,
    bgm_vol: float = 0.22,
    threshold: float = 0.008,
    ratio: float = 6.0,
    attack_ms: int = 20,
    release_ms: int = 350,
) -> bool:
    if not video_path.exists():
        print(f"[-] 错误: 视频文件不存在: {video_path}")
        return False
    if not bgm_path.exists():
        print(f"[-] 错误: 背景音乐文件不存在: {bgm_path}")
        return False

    dur = get_duration(video_path)
    fadeout_st = max(0.0, dur - 3.5)

    print(f"[*] 开始侧链闪避混音: {video_path.name} (时长: {dur:.2f}s)")
    print(f"[*] BGM: {bgm_path.name} (基础音量: {bgm_vol}, 压缩比: {ratio}, 阈值: {threshold})")

    # 滤镜链：
    # [1:a] BGM 音量缩放 -> 循环覆盖视频时长 -> 采样率对齐 -> 头尾淡入淡出 -> [bg]
    # [0:a] 原视频人声拆分 -> 一路保留 [nar]，一路作为侧链触发器 [key]
    # [bg][key] sidechaincompress 侧链压制 -> [duck]
    # [nar][duck] 混合并在 0.95 限幅防破音 -> [mix]
    filter_complex = (
        f"[1:a]volume={bgm_vol},aresample=48000,afade=t=in:st=0:d=1.5,afade=t=out:st={fadeout_st:.2f}:d=3.5[bg];"
        f"[0:a]asplit=2[nar][key];"
        f"[bg][key]sidechaincompress=threshold={threshold}:ratio={ratio}:attack={attack_ms}:release={release_ms}[duck];"
        f"[nar][duck]amix=inputs=2:duration=first:dropout_transition=0:normalize=0,alimiter=limit=0.95[mix]"
    )

    cmd = [
        str(FFMPEG), "-nostdin", "-y", "-v", "error",
        "-i", str(video_path),
        "-stream_loop", "-1", "-t", str(dur), "-i", str(bgm_path),
        "-filter_complex", filter_complex,
        "-map", "0:v", "-map", "[mix]",
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
        "-shortest", "-movflags", "+faststart",
        str(output_path),
    ]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"[-] 混音失败: {res.stderr}")
        return False

    print(f"[+] 混音成功，成片已导出至: {output_path}")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="FFmpeg 侧链闪避混音工具（旁白说话时 BGM 自动下潜）")
    parser.add_argument("video", type=Path, help="输入的视频文件 (含人声音轨)")
    parser.add_argument("bgm", type=Path, help="背景音乐音频文件 (mp3/wav)")
    parser.add_argument("-o", "--output", type=Path, default=None, help="输出视频路径，默认覆盖或加 _duck 后缀")
    parser.add_argument("--bgm-vol", type=float, default=0.22, help="BGM 基础音量比例 (默认 0.22)")
    parser.add_argument("--threshold", type=float, default=0.008, help="人声感应触发阈值 (默认 0.008)")
    parser.add_argument("--ratio", type=float, default=6.0, help="侧链压缩比 (默认 6.0)")

    args = parser.parse_args()

    out_path = args.output
    if out_path is None:
        out_path = args.video.with_name(f"{args.video.stem}_ducked.mp4")

    ok = mix_sidechain(
        args.video, args.bgm, out_path,
        bgm_vol=args.bgm_vol, threshold=args.threshold, ratio=args.ratio
    )
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
