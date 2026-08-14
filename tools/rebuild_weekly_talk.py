#!/usr/bin/env python3
"""Signal Pop 周末特别版 · 双人对话视频合成（信蓝组合）
视觉：左右双主播（阿信左·蓝气泡 / 小蓝右·粉气泡），谁说话谁的气泡高亮；新闻配图做背景。
用法：python tools/rebuild_weekly_talk.py [PREP_DATE]
"""
import os
import sys
import json
import shutil
import subprocess
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont, ImageFilter

PROJECT_ROOT = "E:/projects/signal_pop"
sys.path.insert(0, PROJECT_ROOT)

PREP_DATE = sys.argv[1] if len(sys.argv) > 1 else "20260814"
OUT_DIR = os.path.join(PROJECT_ROOT, "output", "weekly", PREP_DATE)
IMAGES_DIR = os.path.join(OUT_DIR, "images")
AUDIO_PATH = os.path.join(OUT_DIR, "audio", "tts.wav")
SEGMENTS_PATH = os.path.join(OUT_DIR, "audio", "tts_segments.json")
SCRIPT_FILE = os.path.join(PROJECT_ROOT, "archive", f"signal_pop_weekly_special_{PREP_DATE}.txt")
OUTPUT_VIDEO = os.path.join(OUT_DIR, f"signal_pop_weekly_{PREP_DATE}.mp4")

PUB_DT = datetime.strptime(PREP_DATE, "%Y%m%d") + timedelta(days=1)
PUB_DATE_FMT = f"{PUB_DT.year}年{PUB_DT.month:02d}月{PUB_DT.day:02d}日"
PUB_DATE_SHORT = f"{PUB_DT.year}.{PUB_DT.month:02d}.{PUB_DT.day:02d}"

WIDTH, HEIGHT = 1920, 1080
FFMPEG = "E:/projects/signal_pop/bin/ffmpeg-9.0.1-essentials_build/bin/ffmpeg.exe"
FONT = "C:/Windows/Fonts/msyh.ttc"
FONT_BOLD = "C:/Windows/Fonts/msyhbd.ttc"

# 配色：阿信蓝 / 小蓝粉
AXIN_BLUE = (58, 130, 210)
XIAOLAN_PINK = (220, 90, 150)
GOLD = (212, 175, 55)
WHITE = (245, 245, 250)
LIGHT_GREY = (190, 198, 210)
SPEAKERS = {"阿信": "axin", "小蓝": "xiaolan"}


def fnt(size, bold=False):
    return ImageFont.truetype(FONT_BOLD if bold else FONT, size)


def wrap_text(draw, text, font, max_width):
    lines = []
    current = ""
    for ch in text:
        bbox = draw.textbbox((0, 0), current + ch, font=font)
        if bbox[2] - bbox[0] <= max_width:
            current += ch
        else:
            if current:
                lines.append(current)
            current = ch
    if current:
        lines.append(current)
    return lines


def parse_talk_with_bg(text):
    """解析对话稿，给每段分配背景图（根据【第N名】等标签）。"""
    segs = []
    cur_group = "开场"
    bg_map = {"开场": "opening_bg.jpg", "本周之最": "00.jpg", "下周看点": "99.jpg", "结尾": "ending_bg.jpg"}
    for line in text.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        if line.startswith("【"):
            tag = line.strip("【】")
            if tag.startswith("第") and "名" in tag:
                try:
                    rank = int(tag.replace("第", "").replace("名", ""))
                    cur_group = f"rank{rank}"
                    bg_map[f"rank{rank}"] = f"{rank:02d}.jpg"
                except Exception:
                    cur_group = tag
            else:
                cur_group = tag
            continue
        for name, key in SPEAKERS.items():
            if line.startswith(f"{name}：") or line.startswith(f"{name}:"):
                content = line.split("：", 1)[1] if "：" in line else line.split(":", 1)[1]
                bg = bg_map.get(cur_group, "opening_bg.jpg")
                segs.append({"speaker": name, "key": key, "text": content.strip(),
                             "group": cur_group, "bg": bg})
                break
    return segs


def round_crop(img, size):
    """把头像裁成圆形。"""
    img = img.convert("RGBA").resize((size, size), Image.LANCZOS)
    mask = Image.new("L", (size, size), 0)
    md = ImageDraw.Draw(mask)
    md.ellipse([0, 0, size, size], fill=255)
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    out.paste(img, (0, 0), mask)
    return out


def draw_talk_frame(bg_path, seg, anchor_imgs, group_label):
    """双人对话帧：左阿信 / 右小蓝，说话人高亮。"""
    bg = Image.open(bg_path).convert("RGB").resize((WIDTH, HEIGHT), Image.LANCZOS)
    blurred = bg.filter(ImageFilter.GaussianBlur(radius=3))
    rgba = blurred.convert("RGBA")
    dark = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 80))
    base = Image.alpha_composite(rgba, dark).convert("RGB")
    d = ImageDraw.Draw(base)

    # 顶部标签
    d.text((960, 60), "隔天信号弹 · 周末特别版 · 信蓝组合", fill=GOLD, font=fnt(34, bold=True), anchor="mm")
    d.rectangle([960 - 160, 95, 960 + 160, 101], fill=GOLD)
    if group_label:
        d.text((960, 140), group_label, fill=LIGHT_GREY, font=fnt(28), anchor="mm")

    speaking = (seg["key"] == "axin")
    # 头像位置：左阿信(x=470, y=520) 右小蓝(x=1450, y=520)
    avatar_size = 300
    glow_size = 330
    for key, cx, cy in (("axin", 470, 520), ("xiaolan", 1450, 520)):
        is_me = (seg["key"] == key)
        # 光晕（说话人）
        halo = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
        hd = ImageDraw.Draw(halo)
        hd.ellipse([cx - glow_size//2, cy - glow_size//2, cx + glow_size//2, cy + glow_size//2],
                   fill=(255, 255, 255, 60) if is_me else (0, 0, 0, 0))
        halo = halo.filter(ImageFilter.GaussianBlur(radius=25))
        base = Image.alpha_composite(base.convert("RGBA"), halo).convert("RGB")
        d = ImageDraw.Draw(base)
        # 头像（先 paste 到全尺寸透明层，再合成，规避 alpha_composite 无偏移参数）
        av = round_crop(anchor_imgs[key], avatar_size)
        av_layer = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
        av_layer.paste(av, (cx - avatar_size // 2, cy - avatar_size // 2), av)
        base = Image.alpha_composite(base.convert("RGBA"), av_layer).convert("RGB")
        d = ImageDraw.Draw(base)
        # 名字
        name = "阿信" if key == "axin" else "小蓝"
        nc = AXIN_BLUE if key == "axin" else XIAOLAN_PINK
        d.text((cx, cy + avatar_size//2 + 40), name, fill=nc, font=fnt(40, bold=True), anchor="mm")
        # 说话人名字加"正在说"标记
        if is_me:
            d.text((cx, cy + avatar_size//2 + 95), "正在说…", fill=GOLD, font=fnt(24), anchor="mm")

    # 对话气泡（底部中央，说话人高亮边框）
    bubble_w, bubble_h = 1500, 190
    bx, by = (WIDTH - bubble_w) // 2, 800
    color = AXIN_BLUE if speaking else XIAOLAN_PINK
    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    od.rounded_rectangle([bx, by, bx + bubble_w, by + bubble_h], 24,
                         fill=(18, 20, 30, 225), outline=color, width=4 if speaking else 2)
    base = Image.alpha_composite(base.convert("RGBA"), overlay).convert("RGB")
    d = ImageDraw.Draw(base)
    # 说话人标签
    who = "阿信" if speaking else "小蓝"
    d.text((bx + 30, by + 30), who, fill=color, font=fnt(30, bold=True), anchor="lm")
    # 气泡文字
    body = seg["text"]
    bd_f = fnt(30)
    lines = wrap_text(d, body, bd_f, bubble_w - 60)[:3]
    if len(body) > sum(len(l) for l in lines):
        lines[-1] = lines[-1][:-1] + "…"
    y = by + 70
    for line in lines:
        d.text((bx + 30, y), line, fill=WHITE, font=bd_f, anchor="lm")
        y += 42

    # 底部品牌
    d.text((960, 1040), f"隔天信号弹 · {PUB_DATE_SHORT}", fill=LIGHT_GREY, font=fnt(22), anchor="mm")
    return base


def draw_ending_frame(pub_date_fmt):
    en_bg = os.path.join(IMAGES_DIR, "ending_bg.jpg")
    if not os.path.exists(en_bg):
        en_bg = os.path.join(IMAGES_DIR, "opening_bg.jpg")
    bg = Image.open(en_bg).convert("RGB").resize((WIDTH, HEIGHT), Image.LANCZOS)
    rgba = bg.convert("RGBA")
    dark = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 120))
    img = Image.alpha_composite(rgba, dark).convert("RGB")
    d = ImageDraw.Draw(img)
    for x in range(120, 1800):
        d.rectangle([x, 80, x + 1, 85], fill=GOLD)
    d.ellipse([950, 142, 970, 162], outline=GOLD, width=3)
    d.ellipse([957, 149, 963, 155], fill=GOLD)
    d.text((960, 260), "隔天信号弹", fill=GOLD, font=fnt(72, bold=True), anchor="mm")
    d.text((960, 360), "信蓝组合 · 下周见", fill=WHITE, font=fnt(48, bold=True), anchor="mm")
    d.text((960, 430), pub_date_fmt, fill=LIGHT_GREY, font=fnt(32), anchor="mm")
    d.text((960, 600), "您的一键三连", fill=GOLD, font=fnt(40, bold=True), anchor="mm")
    d.text((960, 660), "是我们更新制作的动力", fill=WHITE, font=fnt(32), anchor="mm")
    d.text((960, 720), "互动话题：本周哪条你最想聊？欢迎评论区留言！", fill=LIGHT_GREY, font=fnt(26), anchor="mm")
    return img


def draw_sanlian_icon(canvas, cx, cy, kind, glow):
    r = 62
    w, h = 220, 200
    icon = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    bd = ImageDraw.Draw(icon)
    ox, oy = w // 2, 90
    bd.ellipse([ox - r, oy - r, ox + r, oy + r], fill=(20, 26, 36, 235), outline=(212, 175, 55, 255), width=4)
    ic = (255, 240, 190)
    if kind == "subscribe":
        bd.arc([ox - 24, oy - 30, ox + 24, oy + 20], start=0, end=180, fill=ic, width=5)
        bd.line([ox - 24, oy - 5, ox - 24, oy + 10], fill=ic, width=5)
        bd.line([ox + 24, oy - 5, ox + 24, oy + 10], fill=ic, width=5)
        bd.arc([ox - 10, oy - 52, ox + 10, oy - 32], start=180, end=360, fill=ic, width=5)
        bd.ellipse([ox - 7, oy + 8, ox + 7, oy + 22], fill=ic)
    elif kind == "follow":
        bd.polygon([(ox, oy + 24), (ox - 26, oy - 6), (ox - 12, oy - 22), (ox, oy - 12),
                    (ox + 12, oy - 22), (ox + 26, oy - 6)], fill=ic)
        bd.ellipse([ox - 28, oy - 32, ox - 4, oy - 6], fill=ic)
        bd.ellipse([ox + 4, oy - 32, ox + 28, oy - 6], fill=ic)
    else:
        bd.arc([ox - 26, oy - 24, ox + 26, oy + 28], start=30, end=300, fill=ic, width=6)
        bd.polygon([(ox + 24, oy - 6), (ox + 34, oy - 18), (ox + 18, oy - 20)], fill=ic)
    lf = fnt(26, bold=True)
    bd.text((w // 2, h - 20), {"subscribe": "订阅", "follow": "关注", "share": "转发"}[kind],
            fill=(255, 255, 255), font=lf, anchor="mm")
    if glow > 0.02:
        halo = icon.filter(ImageFilter.GaussianBlur(radius=18))
        a = halo.split()[3].point(lambda v: int(v * min(1.0, glow)))
        halo.putalpha(a)
        canvas.alpha_composite(halo, (cx - w // 2, cy - oy))
    canvas.alpha_composite(icon, (cx - w // 2, cy - oy))


def render_ending_animation(pub_date_fmt, out_dir, dur, fps=25):
    n = max(2, int(dur * fps))
    frames = []
    appear_start, appear_end = 0.05, 0.45
    cx = [700, 960, 1220]
    cy = 900
    for i in range(n):
        t = i / n
        img = draw_ending_frame(pub_date_fmt).convert("RGBA")
        glows = [0.0, 0.0, 0.0]
        if t < appear_end:
            for k in range(3):
                seg = (appear_end - appear_start) / 3
                s = (t - appear_start) / seg
                if s > k:
                    glows[k] = min(1.0, (s - k) * 4)
        else:
            glows = [1.0, 1.0, 1.0]
        for k, g in enumerate(glows):
            if g > 0.02:
                draw_sanlian_icon(img, cx[k], cy, ["subscribe", "follow", "share"][k], g)
        p = os.path.join(out_dir, f"an_{i:04d}.png")
        img.convert("RGB").save(p)
        frames.append(p)
    return frames, fps


def encode_part_animation(frame_dir, output_mp4, dur, fps=25):
    pattern = os.path.join(frame_dir, "an_%04d.png").replace("\\", "/")
    cmd = [FFMPEG, "-y", "-framerate", str(fps), "-i", pattern, "-c:v", "libx264",
           "-preset", "fast", "-crf", "20", "-pix_fmt", "yuv420p", "-r", str(fps), output_mp4]
    subprocess.run(cmd, check=True, capture_output=True, timeout=180)


def encode_part(input_png, output_mp4, dur):
    cmd = [FFMPEG, "-y", "-loop", "1", "-framerate", "25", "-t", f"{dur:.3f}", "-i", input_png,
           "-c:v", "libx264", "-preset", "fast", "-crf", "22", "-tune", "stillimage",
           "-pix_fmt", "yuv420p", "-r", "25", output_mp4]
    subprocess.run(cmd, check=True, capture_output=True, timeout=120)


def main():
    if not os.path.exists(SEGMENTS_PATH):
        print(f"ERROR: {SEGMENTS_PATH} not found"); sys.exit(1)
    durations = json.load(open(SEGMENTS_PATH, encoding="utf-8"))
    segs = parse_talk_with_bg(open(SCRIPT_FILE, encoding="utf-8").read())
    if len(durations) != len(segs):
        print(f"ERROR: durations({len(durations)}) != segs({len(segs)})"); sys.exit(1)

    # 加载双人形象
    anchor_imgs = {}
    for key, fname in (("axin", "anchor_axin.jpg"), ("xiaolan", "anchor_xiaolan.jpg")):
        p = os.path.join(IMAGES_DIR, fname)
        if not os.path.exists(p):
            print(f"ERROR: 缺少主播形象 {fname}"); sys.exit(1)
        anchor_imgs[key] = Image.open(p)

    tmp = os.path.join(OUT_DIR, "split_build")
    if os.path.exists(tmp):
        shutil.rmtree(tmp)
    os.makedirs(tmp, exist_ok=True)

    print("=== 绘制双人对话帧 ===")
    frames = []
    for idx, (seg, dur_info) in enumerate(zip(segs, durations)):
        bg = os.path.join(IMAGES_DIR, seg["bg"])
        if not os.path.exists(bg):
            bg = os.path.join(IMAGES_DIR, "opening_bg.jpg")
        group_label = ""
        if seg["group"] != "开场":
            g = seg["group"]
            group_label = f"第{int(g[4:])}名" if g.startswith("rank") else g
        png = os.path.join(tmp, f"talk_{idx:03d}.png")
        draw_talk_frame(bg, seg, anchor_imgs, group_label).save(png)
        frames.append((f"talk{idx}", png, dur_info["dur"], "static"))

    # 三连动画（结尾）
    anim_dur = 6.0
    en_dir = os.path.join(tmp, "ending_anim")
    os.makedirs(en_dir, exist_ok=True)
    anim_frames, fps = render_ending_animation(PUB_DATE_FMT, en_dir, anim_dur)
    frames.append(("ending", en_dir, anim_dur, "anim"))

    total_dur = sum(f[2] for f in frames)
    print(f"\n  帧时长总和: {total_dur:.3f}s (音频 {sum(d['dur'] for d in durations):.2f}s + 动画 {anim_dur}s)")

    print("\n=== 每段独立编码 ===")
    part_files = []
    for idx, f in enumerate(frames):
        label, payload, dur, kind = f
        part_mp4 = os.path.join(tmp, f"part_{idx:02d}.mp4")
        if kind == "anim":
            encode_part_animation(payload, part_mp4, dur, fps)
        else:
            encode_part(payload, part_mp4, dur)
        print(f"  part {idx:02d} [{label}]: {dur:.2f}s -> {os.path.getsize(part_mp4)//1024}KB")
        part_files.append(part_mp4)

    with open(os.path.join(tmp, "concat.txt"), "w", encoding="utf-8") as f:
        for p in part_files:
            f.write(f"file '{os.path.basename(p)}'\n")

    print("\n=== concat 拼接 + 音频 ===")
    if os.path.exists(OUTPUT_VIDEO):
        os.remove(OUTPUT_VIDEO)
    # 补 6s 静音避免 -shortest 截断结尾动画（对话音频 + 动画时长对齐）
    audio_full = os.path.join(OUT_DIR, "audio", "tts_full.wav")
    if not os.path.exists(audio_full):
        import wave as _w
        with _w.open(AUDIO_PATH, "rb") as w:
            rate = w.getframerate()
            ch = w.getnchannels()
            sw = w.getsampwidth()
            raw = w.readframes(w.getnframes())
        with _w.open(audio_full, "wb") as out:
            out.setnchannels(ch)
            out.setsampwidth(sw)
            out.setframerate(rate)
            out.writeframes(raw + b"\x00\x00" * (rate * 6))
    print(f"  音频: {audio_full}")

    cmd = [FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", "concat.txt",
           "-i", audio_full, "-c:v", "copy", "-c:a", "aac", "-b:a", "128k",
           "-shortest", OUTPUT_VIDEO]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=300, cwd=tmp)
    if r.returncode != 0:
        print("FFMPEG STDERR:", r.stderr[-1200:])
        sys.exit(1)
    sz = os.path.getsize(OUTPUT_VIDEO) / 1024 / 1024
    print(f"\n  输出: {OUTPUT_VIDEO} ({sz:.1f}MB) 时长 {total_dur:.1f}s")
    print("  ✅ 双人对话视频完成")


if __name__ == "__main__":
    main()
