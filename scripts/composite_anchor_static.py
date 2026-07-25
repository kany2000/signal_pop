#!/usr/bin/env python3
"""Signal Pop v2.2 AI主播合成 — 圆形透明裁切+呼吸动画"""
import sys, os, subprocess, re, tempfile

FFMPEG = "C:/Users/Administrator/AppData/Local/Microsoft/WinGet/Packages/Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-8.1.2-full_build/bin/ffmpeg.exe"

def create_anchor_video(anchor_img, out_video, duration, size=200):
    """生成圆形透明主播动画"""
    r = size // 2
    fade = 15
    inner = r - 2*fade
    cmd = [
        FFMPEG, '-y',
        '-loop', '1', '-i', anchor_img,
        '-t', str(duration),
        '-vf',
        f'scale={size}:{size}:force_original_aspect_ratio=increase,'
        f'crop={size}:{size},'
        # 圆形 alpha 遮罩：距离中心 > r-fade 全透明，< r-2fade 不透明，中间渐变
        f'format=rgba,'
        f'geq=r=\'r(X,Y)\':g=\'g(X,Y)\':b=\'b(X,Y)\':'
        f'a=\'if(lt(sqrt((X-{r})^2+(Y-{r})^2),{inner}),255,'
        f'if(lt(sqrt((X-{r})^2+(Y-{r})^2),{r-fade}),'
        f'255*(1-((sqrt((X-{r})^2+(Y-{r})^2)-{inner})/{fade})),0))\','
        # 呼吸缩放 + 微摆
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

def get_duration(video_path):
    r = subprocess.run([FFMPEG, '-i', video_path, '-f', 'null', '-'],
                       capture_output=True, text=True, timeout=60)
    m = re.search(r'Duration: (\d+):(\d+):(\d+)\.(\d+)', r.stderr)
    if m:
        h, mi, s, ms = int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4))
        return h*3600 + mi*60 + s + ms/100
    return 475.0

def composite(main_video, anchor_img, output_path, size=200):
    duration = get_duration(main_video)
    d = os.path.dirname(output_path)
    tmp = os.path.join(d, "_anchor_anim.mp4")
    create_anchor_video(anchor_img, tmp, duration, size)

    cmd = [
        FFMPEG, '-y',
        '-i', main_video,
        '-i', tmp,
        '-filter_complex',
        '[1:v]format=rgba[anchor];'
        '[0:v][anchor]overlay=W-w-30:H-h-40:shortest=1[outv]',
        '-map', '[outv]',
        '-map', '0:a',
        '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '24',
        '-c:a', 'copy',
        output_path
    ]
    print(f"Compositing anchor PiP (v2.2)...")
    subprocess.run(cmd, check=True, timeout=600)
    os.remove(tmp)
    mb = os.path.getsize(output_path) / 1_048_576
    print(f"Done: {output_path} ({mb:.1f}MB)")

if __name__ == "__main__":
    main = sys.argv[1]
    anchor = sys.argv[2]
    out = sys.argv[3] if len(sys.argv) > 3 else main.replace('.mp4', '_v2.mp4')
    size = int(sys.argv[4]) if len(sys.argv) > 4 else 200
    composite(main, anchor, out, size)