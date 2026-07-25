#!/usr/bin/env python3
"""Signal Pop v2.1 AI主播合成 — 头像圆形裁切+呼吸+微摆"""
import sys, os, subprocess, tempfile

FFMPEG = "C:/Users/Administrator/AppData/Local/Microsoft/WinGet/Packages/Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-8.1.2-full_build/bin/ffmpeg.exe"

def create_anchor_video(anchor_img, out_video, duration, size=280):
    """生成主播动画视频：圆形裁切+呼吸缩放+微摆"""
    r = size // 2
    fade = 20  # 羽化像素
    cmd = [
        FFMPEG, '-y',
        '-loop', '1', '-i', anchor_img,
        '-t', str(duration),
        '-vf',
        f'scale={size}:{size}:force_original_aspect_ratio=increase,'
        f'crop={size}:{size},'
        f'format=rgba,'
        # 圆形裁切+羽化: pixel center distance > r-fade → alpha 0
        f'geq=r=\'r(X,Y)\':g=\'g(X,Y)\':b=\'b(X,Y)\':'
        f'a=\'if(gt(sqrt((X-{r})^2+(Y-{r})^2),{r-fade}),0,if(gt(sqrt((X-{r})^2+(Y-{r})^2),{r-2*fade}),255*(1-((sqrt((X-{r})^2+(Y-{r})^2)-({r-2*fade}))/{(fade)})),255))\','
        # 缩放微动（呼吸感）
        f'zoompan=z=\'1+0.015*sin(2*PI*0.3*on)\':d=1:'
        f'x=\'iw/2-(iw/zoom/2)+3*sin(2*PI*0.12*on)\':'
        f'y=\'ih/2-(ih/zoom/2)\':'
        f's={size}x{size}:fps=25',
        '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '28',
        '-pix_fmt', 'yuva420p',
        out_video
    ]
    subprocess.run(cmd, check=True, timeout=300)
    print(f"  Anchor video: {out_video}")


def composite(main_video, anchor_img, output_path, size=280):
    # 获取主视频时长
    r = subprocess.run([
        FFMPEG, '-i', main_video,
        '-f', 'null', '-'
    ], capture_output=True, text=True, timeout=60)
    import re
    m = re.search(r'Duration: (\d+):(\d+):(\d+)\.(\d+)', r.stderr)
    if m:
        h, mi, s, ms = int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4))
        duration = h*3600 + mi*60 + s + ms/100
    else:
        duration = 475.0

    # 先生成主播动画视频
    tmp = os.path.join(os.path.dirname(output_path), "_anchor_anim.mp4")
    create_anchor_video(anchor_img, tmp, duration, size)

    # 合成
    cmd = [
        FFMPEG, '-y',
        '-i', main_video,
        '-i', tmp,
        '-filter_complex',
        f'[1:v]format=rgba[anchor];'
        f'[0:v][anchor]overlay=W-w-40:H-h-60:shortest=1[outv]',
        '-map', '[outv]',
        '-map', '0:a',
        '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '24',
        '-c:a', 'copy',
        output_path
    ]
    print(f"Compositing anchor PiP (v2.1 circular+sway)...")
    subprocess.run(cmd, check=True, timeout=600)

    # 清理临时文件
    os.remove(tmp)
    mb = os.path.getsize(output_path) / 1_048_576
    print(f"Done: {output_path} ({mb:.1f}MB)")


if __name__ == "__main__":
    main = sys.argv[1]
    anchor = sys.argv[2]
    out = sys.argv[3] if len(sys.argv) > 3 else main.replace('.mp4', '_v2.mp4')
    composite(main, anchor, out)