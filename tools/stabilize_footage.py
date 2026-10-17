#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Signal Pop · 工业级视频防抖与画中画平滑预处理工具

针对现场录屏、手机拍摄、转播源素材在画中画（PiP）小窗中出现的剧烈抖动、高频微颤、
3:2 Pulldown 恶性跳帧等问题，执行标准工业级三步法流水线：

1. 抽骨去重（mpdecimate）：剔除恶性静止幽灵帧，恢复真实时间戳，消除一顿一挫的跳步脉冲；
2. 两遍式全局防抖（vidstabdetect + vidstabtransform）：
   - Pass 1: 特征点全局运动矢量分析，生成 .trf 轨迹；
   - Pass 2: 执行高阶平滑补偿（smoothing=30），自适应修边，熨平手持颠簸；
3. 双向光流插值与 16:9 固化（minterpolate + scale/pad）：
   - 生成纯净流畅的真实 30fps 插值过渡；
   - 强制固化为标准 1280x720 (16:9)，从根源避免 Chromium 亚像素缩放抖动。

用法：
  python tools/stabilize_footage.py <输入视频> [输出视频] [截取起点秒] [持续时长秒]
示例：
  python tools/stabilize_footage.py raw.mp4 stabilized_pip.mp4 8.5 6.0
"""

import sys
import os
import subprocess
import shutil

FFMPEG = "E:/projects/Y2A-Auto/ffmpeg/ffmpeg.exe"
if not os.path.exists(FFMPEG):
    FFMPEG = "ffmpeg"


def stabilize(input_video, output_video, start=None, duration=None, smoothing=30):
    if not os.path.exists(input_video):
        print(f"❌ 找不到输入文件: {input_video}")
        return False

    out_dir = os.path.dirname(os.path.abspath(output_video)) or "."
    os.makedirs(out_dir, exist_ok=True)
    tmp_dir = os.path.join(out_dir, "_stab_tmp")
    os.makedirs(tmp_dir, exist_ok=True)

    trf_file = os.path.join(tmp_dir, "transforms.trf").replace("\\", "/")
    decimated = os.path.join(tmp_dir, "decimated.mp4").replace("\\", "/")

    trim_opts = []
    if start is not None:
        trim_opts.extend(["-ss", str(start)])
    if duration is not None:
        trim_opts.extend(["-t", str(duration)])

    print(f"🎬 [1/3] 执行抽骨去重 (mpdecimate)...")
    cmd1 = [
        FFMPEG, "-y", *trim_opts, "-i", input_video,
        "-vf", "mpdecimate=hi=64*20:lo=64*10:frac=0.33,setpts=N/FRAME_RATE/TB",
        "-c:v", "libx264", "-preset", "fast", "-crf", "16", "-an",
        decimated
    ]
    subprocess.run(cmd1, check=True, capture_output=True)

    print(f"🔍 [2/3] 执行特征点全局运动追踪 (vidstabdetect)...")
    cmd2 = [
        FFMPEG, "-y", "-i", decimated,
        "-vf", f"vidstabdetect=shakiness=8:accuracy=15:result={trf_file}",
        "-f", "null", "-"
    ]
    subprocess.run(cmd2, check=True, capture_output=True)

    print(f"✨ [3/3] 执行高阶平滑补偿与 16:9 光流插值 (vidstabtransform + minterpolate)...")
    filter_chain = (
        f"vidstabtransform=input={trf_file}:smoothing={smoothing}:optzoom=1:crop=black,"
        f"minterpolate=fps=30:mi_mode=mci:mc_mode=aobmc,"
        f"scale=1280:720:force_original_aspect_ratio=decrease,"
        f"pad=1280:720:(ow-iw)/2:(oh-ih)/2:black,"
        f"unsharp=5:5:0.5:3:3:0.2,setsar=1"
    )
    cmd3 = [
        FFMPEG, "-y", "-i", decimated,
        "-vf", filter_chain,
        "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p",
        "-an", "-movflags", "+faststart",
        output_video
    ]
    subprocess.run(cmd3, check=True, capture_output=True)

    shutil.rmtree(tmp_dir, ignore_errors=True)
    print(f"✅ 工业级防抖视频生成成功: {output_video}")
    return True


def main():
    if len(sys.argv) < 2:
        print("用法: python tools/stabilize_footage.py <输入视频> [输出视频] [起点秒] [时长秒]")
        return 1

    src = sys.argv[1]
    dst = sys.argv[2] if len(sys.argv) > 2 else "stabilized_pip.mp4"
    start = float(sys.argv[3]) if len(sys.argv) > 3 else None
    dur = float(sys.argv[4]) if len(sys.argv) > 4 else None

    ok = stabilize(src, dst, start, dur)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
