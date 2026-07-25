#!/usr/bin/env python3
"""Signal Pop v2.4 AI主播合成 — 直接overlay PNG，保持alpha"""
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
    print(f"  Circular PNG: {out_png}")


def composite(main_video, anchor_img, output_path, size=200):
    d = os.path.dirname(output_path)
    png = os.path.join(d, "_anchor_circular.png")
    make_circular_png(anchor_img, png, size)

    # 单步合成：不预编码，直接 overlay PNG（保持alpha）
    # 用 overlay 的 x/y 表达式做微摆动画，不用 zoompan（zoompan 会丢alpha）
    cmd = [
        FFMPEG, '-y',
        '-i', main_video,
        '-loop', '1', '-i', png,
        '-filter_complex',
        f'[1:v]format=rgba,'
        f'scale={size}:{size}:eval=frame[img];'
        f'[0:v][img]overlay='
        f'x=\'W-w-30+3*sin(2*PI*t*0.15)\':'
        f'y=\'H-h-40+2*sin(2*PI*t*0.1)\':'
        f'shortest=1[outv]',
        '-map', '[outv]',
        '-map', '0:a',
        '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '24',
        '-c:a', 'copy',
        output_path
    ]
    print(f"Compositing anchor PiP (v2.4)...")
    subprocess.run(cmd, check=True, timeout=600)

    os.remove(png)
    mb = os.path.getsize(output_path) / 1_048_576
    print(f"Done: {output_path} ({mb:.1f}MB)")


if __name__ == "__main__":
    main = sys.argv[1]
    anchor = sys.argv[2]
    out = sys.argv[3] if len(sys.argv) > 3 else main.replace('.mp4', '_v2.mp4')
    size = int(sys.argv[4]) if len(sys.argv) > 4 else 200
    composite(main, anchor, out, size)