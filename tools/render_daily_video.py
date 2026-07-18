#!/usr/bin/env python3
"""Signal Pop Daily Video Render v2: 大字体 + 大文字区
Usage: python3 render_daily_video.py YYYYMMDD
"""
import os, sys, re, subprocess, shutil
from PIL import Image, ImageDraw, ImageFont

DATE = sys.argv[1] if len(sys.argv) > 1 else __import__("datetime").datetime.now().strftime("%Y%m%d")
IMG_SRC = f"/home/kan/signal_pop/daily/images/{DATE}"
TEMP_DIR = f"/tmp/signal_pop_frames_{DATE}"
AUDIO = f"/home/kan/signal_pop/daily/output/daily_news_{DATE}.mp3"
VIDEO_OUT = f"/home/kan/signal_pop/daily/output/signal_pop_daily_{DATE}.mp4"
SCRIPT = f"/home/kan/signal_pop/daily/data/script_{DATE}.txt"
CONCAT = f"/tmp/sigpop_final_{DATE}.txt"
N = 10

def main():
    os.makedirs(TEMP_DIR, exist_ok=True)

    # 音频时长
    r = subprocess.run(["ffprobe","-v","error","-show_entries","format=duration",
                         "-of","default=noprint_wrappers=1:nokey=1",AUDIO],
                        capture_output=True, text=True)
    audio_dur = float(r.stdout.strip())
    per = audio_dur / N
    print(f"Audio: {audio_dur:.1f}s, per-news: {per:.1f}s")

    paragraphs = parse_script(SCRIPT)

    # 字体
    font_path = next((p for p in [
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"
    ] if os.path.exists(p)), None)
    if not font_path:
        print("No CJK font found!"); sys.exit(1)

    ft = ImageFont.truetype(font_path, 56)  # 标题行
    fb = ImageFont.truetype(font_path, 42)  # 正文
    fn = ImageFont.truetype(font_path, 72)  # 编号
    fs = ImageFont.truetype(font_path, 28)  # footer

    W, H = 1920, 1080
    TEXT_TOP = int(H * 0.48)  # 文字区从 48% 开始（更大区域）
    TEXT_H = H - TEXT_TOP     # 底部 52%

    for i in range(1, N+1):
        para = next((t for n,t in paragraphs if n==i), "")
        img_path = os.path.join(IMG_SRC, f"{i}.jpg")
        if not os.path.exists(img_path):
            img_path = os.path.join(IMG_SRC, "anchor_bg.jpg")
        if os.path.exists(img_path):
            bg = Image.open(img_path).convert("RGB").resize((W, H), Image.LANCZOS)
        else:
            bg = Image.new("RGB", (W, H), (20, 30, 50))

        # 底部半透明黑色遮罩（文字区）
        bg_rgba = bg.convert("RGBA")
        overlay = Image.new("RGBA", (W, TEXT_H), (0, 0, 0, 210))
        bg_rgba.paste(overlay, (0, TEXT_TOP))
        # 渐变色过渡（图像→文字区）
        for y in range(TEXT_TOP-30, TEXT_TOP):
            alpha = int(255 * (1 - (y - (TEXT_TOP-30)) / 30))
            shade = Image.new("RGBA", (W, 1), (0, 0, 0, alpha))
            bg_rgba.paste(shade, (0, y))
        bg = bg_rgba.convert("RGB")
        d = ImageDraw.Draw(bg)

        # 编号
        d.text((40, TEXT_TOP+8), f"#{i}", fill=(59,130,246), font=fn)

        # 清洗 emoji
        clean = re.sub(r"[\U0001f300-\U0001fad6\U000e0100-\U000e01ef]", "", para).strip()
        if not clean: clean = f"新闻 #{i}"

        # 文字换行
        lines = wrap_text(d, clean, fb, 1760)

        # 标题行（第一行或第一个冒号/丨前的部分）用大字体
        title = lines[0] if lines else clean
        # 如果标题有 "丨" 或 "｜" 符号，突出显示前半段
        if "丨" in title or "｜" in title:
            d.text((40, TEXT_TOP+90), title, fill=(255,255,255), font=ft)
            body_start_y = TEXT_TOP + 160
        else:
            d.text((40, TEXT_TOP+90), title, fill=(255,255,255), font=ft)
            body_start_y = TEXT_TOP + 160

        # 正文行
        body_lines = lines[1:] if len(lines) > 1 else []
        y = body_start_y
        max_lines = 6  # 最多显示 8 行
        for line in body_lines[:max_lines]:
            d.text((40, y), line, fill=(200,210,220), font=fb)
            y += 56

        # 底部品牌名
        d.text((1580, 1030), "隔天信号弹", fill=(150,165,185), font=fs)

        out = os.path.join(TEMP_DIR, f"frame_{i:02d}.jpg")
        bg.save(out, "JPEG", quality=92)
        print(f"  frame_{i:02d}.jpg ({len(clean)} chars, {min(len(body_lines) if body_lines else 0, max_lines)+1} lines)")

    # Concatenate
    with open(CONCAT, "w") as f:
        for i in range(1, N+1):
            for _ in range(2):
                f.write(f"file '{TEMP_DIR}/frame_{i:02d}.jpg'\nduration {per*0.5:.1f}\n")
        for _ in range(2):
            f.write(f"file '{TEMP_DIR}/frame_10.jpg'\nduration {per*0.5:.1f}\n")

    print(f"Concatenating 22 frames → ~{22*per*0.5:.0f}s total (-shortest to {audio_dur:.0f}s)...")

    if os.path.exists(VIDEO_OUT):
        os.remove(VIDEO_OUT)

    subprocess.run(["ffmpeg","-y","-f","concat","-safe","0","-i",CONCAT,
                    "-i",AUDIO,
                    "-c:v","libx264","-preset","fast","-crf","23",
                    "-c:a","aac","-b:a","128k","-shortest",VIDEO_OUT],
                   timeout=300)

    # Verify
    r = subprocess.run(["ffprobe","-v","error","-show_entries","format=duration",
                         "-of","default=noprint_wrappers=1:nokey=1",VIDEO_OUT],
                        capture_output=True, text=True)
    d = float(r.stdout.strip())
    sz = os.path.getsize(VIDEO_OUT) / 1024 / 1024
    ok = "✓" if abs(d - audio_dur) < 1 else "✗"
    print(f"Video: {d:.1f}s, {sz:.1f}MB, duration match: {ok}")

    shutil.rmtree(TEMP_DIR, ignore_errors=True)
    os.remove(CONCAT)

def parse_script(path):
    with open(path, encoding="utf-8") as f:
        lines = f.read().strip().split("\n")
    paragraphs, cur_num, cur_text = [], None, []
    for line in lines:
        line = line.strip()
        if not line: continue
        m = re.match(r"^(\d+)[.、]\s*(.*)", line)
        if m:
            if cur_num is not None: paragraphs.append((cur_num, " ".join(cur_text)))
            cur_num, cur_text = int(m.group(1)), [m.group(2)]
        elif cur_num is not None:
            cur_text.append(line)
    if cur_num is not None: paragraphs.append((cur_num, " ".join(cur_text)))
    return paragraphs

def wrap_text(draw, text, font, max_w):
    chars, lines_out, current = list(text), [], ""
    for ch in chars:
        if draw.textbbox((0,0), current+ch, font=font)[2] > max_w:
            if current: lines_out.append(current)
            current = ch
        else: current += ch
    if current: lines_out.append(current)
    return lines_out

if __name__ == "__main__":
    main()
