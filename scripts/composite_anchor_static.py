#!/usr/bin/env python3
"""Signal Pop v2.0 AI主播合成 — 静态照片+微妙动画

用法：
  python scripts/composite_anchor_static.py <主视频> <主播照片> [输出路径]

效果：
  - 右下角320x240 PiP小窗
  - 主播照片有轻微呼吸缩放动画
  - 圆角+阴影边框
  - 无口型同步，零依赖
"""
import sys, os, subprocess, json

FFMPEG = "C:/Users/Administrator/AppData/Local/Microsoft/WinGet/Packages/Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-8.1.2-full_build/bin/ffmpeg.exe"

def composite(main_video, anchor_img, output_path, pip_size=320):
    """合成主播小窗到主视频右下角"""
    cmd = [
        FFMPEG, '-y',
        '-i', main_video,
        '-loop', '1', '-i', anchor_img,
        '-filter_complex',
        f'[1:v]'
        f'scale={pip_size}:{pip_size*4//3}:force_original_aspect_ratio=increase,'
        f'crop={pip_size}:{pip_size*4//3},'
        f'format=rgba,'
        # 圆角遮罩
        f'drawbox=x=0:y=0:w={pip_size}:h={pip_size*4//3}:color=black@0:t=fill,'
        f'drawbox=x=2:y=2:w={pip_size-4}:h={pip_size*4//3-4}:color=black@0:t=fill,'
        # 呼吸缩放动画 (zoompan 缩放到1.02倍再缓慢回到1.0)
        f'zoompan=z=\'if(lte(zoom,1.0),1.02,zoom-0.0005)\':d=1:s={pip_size}x{pip_size*4//3}:fps=25,'
        # 阴影
        f'pad=w={pip_size+8}:h={pip_size*4//3+8}:x=4:y=4:color=black@0.3,'
        f'format=rgba[anchor];'
        f'[0:v][anchor]overlay=W-w-30:H-h-30:shortest=1[outv]',
        '-map', '[outv]',
        '-map', '0:a',
        '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '24',
        '-c:a', 'copy',
        output_path
    ]
    print(f"Compositing anchor PiP...")
    subprocess.run(cmd, check=True, timeout=600)
    mb = os.path.getsize(output_path) / 1_048_576
    print(f"Done: {output_path} ({mb:.1f}MB)")

if __name__ == "__main__":
    main = sys.argv[1]
    anchor = sys.argv[2]
    out = sys.argv[3] if len(sys.argv) > 3 else main.replace('.mp4', '_v2.mp4')
    composite(main, anchor, out)