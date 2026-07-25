#!/usr/bin/env python3
"""Signal Pop v3.0 AI主播合成 — 支持静态照片/口型视频双模式"""
import sys, os, subprocess, re
from PIL import Image, ImageDraw, ImageFilter

FFMPEG = "C:/Users/Administrator/AppData/Local/Microsoft/WinGet/Packages/Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-8.1.2-full_build/bin/ffmpeg.exe"

def make_circular_png(anchor_img, out_png, size=200):
    img = Image.open(anchor_img).convert("RGBA")
    w, h = img.size
    side = min(w, h)
    img = img.crop(((w - side)//2, (h - side)//2, (w + side)//2, (h + side)//2))
    img = img.resize((size, size), Image.LANCZOS)
    mask = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse([4, 4, size-4, size-4], fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(radius=6))
    img.putalpha(mask)
    img.save(out_png, "PNG")

def get_duration(video_path):
    r = subprocess.run([FFMPEG, '-i', video_path, '-f', 'null', '-'],
                       capture_output=True, text=True, timeout=60)
    m = re.search(r'Duration: (\d+):(\d+):(\d+)\.(\d+)', r.stderr)
    if m:
        h, mi, s, ms = int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4))
        return h*3600 + mi*60 + s + ms/100
    return None

def composite_photo(main_video, anchor_img, output_path, size=200):
    """静态照片模式 — 圆形裁切+微摆"""
    d = os.path.dirname(output_path)
    png = os.path.join(d, "_anchor_circular.png")
    make_circular_png(anchor_img, png, size)
    cmd = [
        FFMPEG, '-y',
        '-i', main_video,
        '-loop', '1', '-i', png,
        '-filter_complex',
        f'[1:v]format=rgba,scale={size}:{size}:eval=frame[img];'
        f'[0:v][img]overlay=x=\'W-w-30+3*sin(2*PI*t*0.15)\':y=\'H-h-40+2*sin(2*PI*t*0.1)\':shortest=1[outv]',
        '-map', '[outv]', '-map', '0:a',
        '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '24',
        '-c:a', 'copy', output_path
    ]
    subprocess.run(cmd, check=True, timeout=600)
    os.remove(png)

def composite_video(main_video, anchor_video, output_path, size=200):
    """口型视频模式 — 圆形裁切+微摆+唇动"""
    d = os.path.dirname(output_path)
    cmd = [
        FFMPEG, '-y',
        '-i', main_video,
        '-i', anchor_video,
        '-filter_complex',
        f'[1:v]scale={size}:{size}:force_original_aspect_ratio=increase,'
        f'crop={size}:{size},format=rgba,'
        f'geq=r=\'r(X,Y)\':g=\'g(X,Y)\':b=\'b(X,Y)\':'
        f'a=\'if(lt(sqrt((X-{size//2})^2+(Y-{size//2})^2),{size//2-6}),255,'
        f'if(lt(sqrt((X-{size//2})^2+(Y-{size//2})^2),{size//2}),'
        f'255*(1-((sqrt((X-{size//2})^2+(Y-{size//2})^2)-({size//2}-6))/6)),0))\','
        f'setpts=PTS+0.05*sin(2*PI*0.2*T)[anchor];'
        f'[0:v][anchor]overlay=W-w-30:H-h-40:shortest=1[outv]',
        '-map', '[outv]', '-map', '0:a',
        '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '24',
        '-c:a', 'copy', output_path
    ]
    subprocess.run(cmd, check=True, timeout=600)

def composite(main_video, anchor_input, output_path, size=200):
    """自动检测输入类型：图片或视频"""
    ext = os.path.splitext(anchor_input)[1].lower()
    if ext in ('.jpg', '.jpeg', '.png'):
        print(f"Mode: static photo ({size}px)")
        composite_photo(main_video, anchor_input, output_path, size)
    elif ext in ('.mp4', '.mov', '.avi'):
        print(f"Mode: lip-sync video ({size}px)")
        composite_video(main_video, anchor_input, output_path, size)
    else:
        print(f"Unknown input type: {ext}")
        sys.exit(1)
    mb = os.path.getsize(output_path) / 1_048_576
    print(f"Done: {output_path} ({mb:.1f}MB)")

if __name__ == "__main__":
    main = sys.argv[1]
    anchor = sys.argv[2]
    out = sys.argv[3] if len(sys.argv) > 3 else main.replace('.mp4', '_v3.mp4')
    size = int(sys.argv[4]) if len(sys.argv) > 4 else 200
    composite(main, anchor, out, size)