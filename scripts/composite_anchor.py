#!/usr/bin/env python3
"""PiP合成：将AI主播口型视频叠加到新闻视频右下角"""
import subprocess, sys, os

FFMPEG = "C:/Users/Administrator/AppData/Local/Microsoft/WinGet/Packages/Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-8.1.2-full_build/bin/ffmpeg.exe"

def composite_anchor(main_video, anchor_video, output_path, scale=320):
    """将anchor_video以PiP形式叠加到main_video右下角"""
    cmd = [
        FFMPEG, '-y',
        '-i', main_video,       # 0: 主视频
        '-i', anchor_video,     # 1: 主播视频
        '-filter_complex',
        f'[1:v]scale={scale}:{scale*4//3}:force_original_aspect_ratio=decrease,format=rgba,'
        f'pad={scale}:{scale*4//3}:(ow-iw)/2:(oh-ih)/2:color=black@0[anchor];'
        f'[0:v][anchor]overlay=W-w-40:H-h-40:shortest=1[outv]',
        '-map', '[outv]',
        '-map', '0:a',
        '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '24',
        '-c:a', 'copy',
        output_path
    ]
    print(f"Compositing anchor video...")
    subprocess.run(cmd, check=True, timeout=600)
    size = os.path.getsize(output_path) / 1_048_576
    print(f"✅ {output_path} ({size:.1f}MB)")


if __name__ == "__main__":
    main = sys.argv[1]
    anchor = sys.argv[2]
    out = sys.argv[3] if len(sys.argv) > 3 else main.replace('.mp4', '_with_anchor.mp4')
    composite_anchor(main, anchor, out)