#!/usr/bin/env python3
"""Signal Pop 周末特别版 · 榜单版视频合成（本周 TOP10 倒计时揭晓）
视觉：黑金榜单风。左侧巨号排名（第10名→第1名），右侧配图+标题+上榜理由。
用法：python tools/rebuild_weekly_top.py [PREP_DATE]
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
PARSED_PATH = os.path.join(OUT_DIR, "parsed_news.json")
OUTPUT_VIDEO = os.path.join(OUT_DIR, f"signal_pop_weekly_{PREP_DATE}.mp4")

PUB_DT = datetime.strptime(PREP_DATE, "%Y%m%d") + timedelta(days=1)
PUB_DATE_FMT = f"{PUB_DT.year}年{PUB_DT.month:02d}月{PUB_DT.day:02d}日"
PUB_DATE_SHORT = f"{PUB_DT.year}.{PUB_DT.month:02d}.{PUB_DT.day:02d}"
PUB_WEEKDAY = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"][PUB_DT.weekday()]

WIDTH, HEIGHT = 1920, 1080
FFMPEG = "E:/projects/signal_pop/bin/ffmpeg-9.0.1-essentials_build/bin/ffmpeg.exe"
FONT = "C:/Windows/Fonts/msyh.ttc"
FONT_BOLD = "C:/Windows/Fonts/msyhbd.ttc"

# 黑金榜单配色
GOLD = (212, 175, 55)
GOLD_LIGHT = (255, 215, 0)
PANEL_BG = (12, 14, 22)       # 深黑蓝面板
ACCENT = GOLD
WHITE = (245, 245, 250)
LIGHT_GREY = (190, 198, 210)
BAR_COLOR = (40, 30, 12)


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


def full_bg(bg_path, dark_alpha=125):
    bg = Image.open(bg_path).convert("RGB").resize((WIDTH, HEIGHT), Image.LANCZOS)
    rgba = bg.convert("RGBA")
    dark = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, dark_alpha))
    return Image.alpha_composite(rgba, dark).convert("RGB")


def draw_opening_top():
    """榜单开场：本周 TOP10 · 倒计时揭晓"""
    op_bg = os.path.join(IMAGES_DIR, "opening_bg.jpg")
    if not os.path.exists(op_bg):
        op_bg = os.path.join(IMAGES_DIR, "01.jpg")
    img = full_bg(op_bg, dark_alpha=135)
    d = ImageDraw.Draw(img)
    # 顶部装饰线
    for x in range(120, 1800):
        d.rectangle([x, 80, x + 1, 85], fill=GOLD)
    # 主标题
    d.text((960, 250), "本周 TOP10", fill=GOLD_LIGHT, font=fnt(110, bold=True), anchor="mm")
    d.text((960, 360), "倒计时揭晓 · 哪条才是本周之最？", fill=WHITE, font=fnt(42, bold=True), anchor="mm")
    d.rectangle([960 - 180, 420, 960 + 180, 426], fill=GOLD)
    d.text((960, 490), "隔天信号弹 · 周末特别版", fill=LIGHT_GREY, font=fnt(36), anchor="mm")
    d.text((960, 545), f"{PUB_DATE_FMT} · {PUB_WEEKDAY}", fill=GOLD, font=fnt(32), anchor="mm")
    # 底部：从第十名到第一名
    d.text((960, 850), "从第 10 名到第 1 名", fill=WHITE, font=fnt(34), anchor="mm")
    d.text((960, 900), "每周一榜 · 本周大事", fill=LIGHT_GREY, font=fnt(28), anchor="mm")
    return img


def draw_rank_slide(bg_path, item, total):
    """榜单 slide：左侧巨号排名 + 右侧配图/标题/上榜理由"""
    bg = Image.open(bg_path).convert("RGB").resize((WIDTH, HEIGHT), Image.LANCZOS)
    blurred = bg.filter(ImageFilter.GaussianBlur(radius=42))
    blurred_rgba = blurred.convert("RGBA")
    dark = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 120))
    blurred_dark = Image.alpha_composite(blurred_rgba, dark).convert("RGB")

    # mask：左 0~760 用模糊面板，760~900 渐变，900+ 清晰
    mask = Image.new("L", (WIDTH, HEIGHT), 0)
    md = ImageDraw.Draw(mask)
    for x in range(0, WIDTH):
        if x < 760:
            a = 255
        elif x < 900:
            a = int(255 * (1 - (x - 760) / 140))
        else:
            a = 0
        md.rectangle([x, 0, x, HEIGHT], fill=a)
    base = Image.composite(blurred_dark, bg, mask)
    d = ImageDraw.Draw(base)

    rank = item.get("rank", 0)
    # ===== 左侧面板（榜单排名）=====
    cx = 400
    # 顶部标签
    d.text((cx, 120), "本 周 排 名", fill=LIGHT_GREY, font=fnt(30, bold=True), anchor="mm")
    d.rectangle([cx - 80, 150, cx + 80, 156], fill=GOLD)
    # 巨号数字（名次越小越大）
    rank_size = {1: 300, 2: 250, 3: 220}.get(rank, 190)
    d.text((cx, 420), f"{rank}", fill=GOLD_LIGHT, font=fnt(rank_size, bold=True), anchor="mm")
    # 名次文字
    suffix = {1: "第一名", 2: "第二名", 3: "第三名"}.get(rank, f"第{rank}名")
    d.text((cx, 560), suffix, fill=WHITE, font=fnt(44, bold=True), anchor="mm")
    # 分类标签
    cat = item.get("section", "新闻")
    cf = fnt(30, bold=True)
    bb = d.textbbox((0, 0), cat, font=cf)
    cw = bb[2] - bb[0] + 30
    d.rounded_rectangle([cx - cw//2, 640, cx + cw//2, 688], 10, fill=(40, 30, 12))
    d.text((cx, 664), cat, fill=GOLD_LIGHT, font=cf, anchor="mm")
    # 揭晓进度
    d.text((cx, 900), f"揭晓 {total - 10 + 1} / 10", fill=LIGHT_GREY, font=fnt(26), anchor="mm") if False else None
    d.text((cx, 940), "隔天信号弹 · 周末榜", fill=(170, 178, 190), font=fnt(22), anchor="mm")
    d.text((cx, 980), PUB_DATE_SHORT, fill=GOLD, font=fnt(22), anchor="mm")

    # ===== 右侧（配图 + 标题 + 上榜理由）=====
    TX = 940
    TW = WIDTH - TX - 70
    # 标题
    ttl_f = fnt(52, bold=True)
    title = item.get("title", "")
    lines = wrap_text(d, title, ttl_f, TW)[:3]
    y = 120
    for line in lines:
        for ox in (-2, 0, 2):
            for oy in (-2, 0, 2):
                if ox == 0 and oy == 0:
                    continue
                d.text((TX + ox, y + oy), line, fill=(0, 0, 0), font=ttl_f)
        d.text((TX, y), line, fill=WHITE, font=ttl_f)
        y += 70
    # "上榜理由"标签
    y += 14
    d.rectangle([TX, y - 4, TX + 8, y + 44], fill=GOLD)
    d.text((TX + 26, y + 18), "上榜理由", fill=GOLD_LIGHT, font=fnt(32, bold=True), anchor="lm")
    y += 62
    # 上榜理由正文
    body = item.get("body", item.get("full_body", ""))
    # 去掉"上榜理由："前缀（已在标签里）
    body = body.replace("上榜理由：", "").replace("上榜理由:", "")
    bd_f = fnt(30)
    bd_lines = wrap_text(d, body, bd_f, TW)[:6]
    if len(body) > sum(len(l) for l in bd_lines):
        bd_lines[-1] = bd_lines[-1][:-1] + "…"
    for line in bd_lines:
        for ox in (-1, 0, 1):
            for oy in (-1, 0, 1):
                if ox == 0 and oy == 0:
                    continue
                d.text((TX + ox, y + oy), line, fill=(0, 0, 0), font=bd_f)
        d.text((TX, y), line, fill=(235, 238, 245), font=bd_f)
        y += 46
    return base


def draw_award_slide(bg_path):
    """本周之最颁奖页"""
    img = full_bg(bg_path, dark_alpha=140)
    d = ImageDraw.Draw(img)
    for x in range(120, 1800):
        d.rectangle([x, 80, x + 1, 85], fill=GOLD)
    d.text((960, 200), "🏆 本周之最", fill=GOLD_LIGHT, font=fnt(76, bold=True), anchor="mm")
    d.rectangle([960 - 140, 250, 960 + 140, 256], fill=GOLD)
    # 三项奖
    awards = [
        ("最震撼", "平陆运河通航 · 世纪工程改写西南物流版图"),
        ("最暖心", "沈阳和平杯 · 青少年足球赛坚持十二年"),
        ("最意外", "Manus 独立运营 · AI 创业公司完成反转"),
    ]
    y = 400
    colors = [GOLD_LIGHT, (220, 120, 120), (140, 200, 255)]
    for i, (tag, txt) in enumerate(awards):
        d.rounded_rectangle([360, y, 1560, y + 130], 18, fill=(22, 24, 34, 235),
                            outline=colors[i], width=2)
        d.text((420, y + 65), tag, fill=colors[i], font=fnt(40, bold=True), anchor="lm")
        d.text((620, y + 65), txt, fill=WHITE, font=fnt(32), anchor="lm")
        y += 170
    return img


def draw_preview_slide(bg_path):
    """下周看点预告页"""
    img = full_bg(bg_path, dark_alpha=135)
    d = ImageDraw.Draw(img)
    for x in range(120, 1800):
        d.rectangle([x, 80, x + 1, 85], fill=GOLD)
    d.text((960, 240), "📅 下周看点", fill=GOLD_LIGHT, font=fnt(76, bold=True), anchor="mm")
    d.rectangle([960 - 120, 290, 960 + 120, 296], fill=GOLD)
    d.text((960, 430), "世界机器人大会即将开幕", fill=WHITE, font=fnt(44, bold=True), anchor="mm")
    d.text((960, 510), "人形机器人军团集中亮相", fill=LIGHT_GREY, font=fnt(36), anchor="mm")
    d.text((960, 650), "关注隔天信号弹，下周继续揭榜！", fill=GOLD, font=fnt(34), anchor="mm")
    return img


def draw_ending_frame(pub_date_fmt):
    en_bg = os.path.join(IMAGES_DIR, "ending_bg.jpg")
    if not os.path.exists(en_bg):
        en_bg = os.path.join(IMAGES_DIR, "10.jpg")
    img = full_bg(en_bg, dark_alpha=120)
    d = ImageDraw.Draw(img)
    for x in range(120, 1800):
        d.rectangle([x, 80, x + 1, 85], fill=GOLD)
    d.ellipse([950, 142, 970, 162], outline=GOLD, width=3)
    d.ellipse([957, 149, 963, 155], fill=GOLD)
    d.text((960, 260), "隔天信号弹", fill=GOLD, font=fnt(72, bold=True), anchor="mm")
    d.text((960, 360), "下期见", fill=WHITE, font=fnt(48, bold=True), anchor="mm")
    d.text((960, 430), pub_date_fmt, fill=LIGHT_GREY, font=fnt(32), anchor="mm")
    d.text((960, 600), "您的一键三连", fill=GOLD, font=fnt(40, bold=True), anchor="mm")
    d.text((960, 660), "是我们更新制作的动力", fill=WHITE, font=fnt(32), anchor="mm")
    d.text((960, 720), "互动话题：本周哪条新闻最值得关注？欢迎评论区留言！", fill=LIGHT_GREY, font=fnt(26), anchor="mm")
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
    appear_start, appear_end = 0.05, 0.40
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
    if not os.path.exists(PARSED_PATH):
        print(f"ERROR: {PARSED_PATH} not found"); sys.exit(1)
    if not os.path.exists(SEGMENTS_PATH):
        print(f"ERROR: {SEGMENTS_PATH} not found"); sys.exit(1)
    items = json.load(open(PARSED_PATH, encoding="utf-8"))
    durations = json.load(open(SEGMENTS_PATH, encoding="utf-8"))
    if len(durations) != len(items) + 2:
        print(f"ERROR: durations({len(durations)}) != items({len(items)})+2"); sys.exit(1)

    tmp = os.path.join(OUT_DIR, "split_build")
    if os.path.exists(tmp):
        shutil.rmtree(tmp)
    os.makedirs(tmp, exist_ok=True)

    print("=== 绘制榜单风格帧 ===")
    frames = []

    op_png = os.path.join(tmp, "00_opening.png")
    draw_opening_top().save(op_png)
    frames.append(("opening", op_png, durations[0], "static"))

    seg_idx = 1
    rank_items = [it for it in items if it.get("rank", 0) in range(1, 11)]
    for item in rank_items:
        rank = item.get("rank", 0)
        bg = os.path.join(IMAGES_DIR, f"{rank:02d}.jpg")
        if not os.path.exists(bg):
            bg = os.path.join(IMAGES_DIR, "opening_bg.jpg")
        png = os.path.join(tmp, f"rank{rank}_slide.png")
        draw_rank_slide(bg, item, len(rank_items)).save(png)
        dur = durations[seg_idx]
        frames.append((f"rank{rank}", png, dur, "static"))
        print(f"  第{rank}名: {dur:.2f}s")
        seg_idx += 1

    # 彩蛋（本周之最）
    award_items = [it for it in items if it.get("section") == "彩蛋"]
    if award_items:
        bg = os.path.join(IMAGES_DIR, "00.jpg")
        if not os.path.exists(bg):
            bg = os.path.join(IMAGES_DIR, "opening_bg.jpg")
        png = os.path.join(tmp, "award.png")
        draw_award_slide(bg).save(png)
        dur = durations[seg_idx]
        frames.append(("award", png, dur, "static"))
        print(f"  本周之最: {dur:.2f}s")
        seg_idx += 1

    # 看点（下周看点）
    preview_items = [it for it in items if it.get("section") == "看点"]
    if preview_items:
        bg = os.path.join(IMAGES_DIR, "99.jpg")
        if not os.path.exists(bg):
            bg = os.path.join(IMAGES_DIR, "opening_bg.jpg")
        png = os.path.join(tmp, "preview.png")
        draw_preview_slide(bg).save(png)
        dur = durations[seg_idx]
        frames.append(("preview", png, dur, "static"))
        print(f"  下周看点: {dur:.2f}s")
        seg_idx += 1

    # ending
    en_dir = os.path.join(tmp, "ending_anim")
    os.makedirs(en_dir, exist_ok=True)
    anim_frames, fps = render_ending_animation(PUB_DATE_FMT, en_dir, durations[-1])
    frames.append(("ending", en_dir, durations[-1], "anim"))
    print(f"  ending: {durations[-1]:.2f}s")

    total_dur = sum(f[2] for f in frames)
    print(f"\n  帧时长总和: {total_dur:.3f}s (音频 {sum(durations):.2f}s)")

    print("\n=== 每段独立编码 ===")
    part_files = []
    for idx, f in enumerate(frames):
        label, payload, dur, kind = f
        part_mp4 = os.path.join(tmp, f"part_{idx:02d}_{label}.mp4")
        if kind == "anim":
            encode_part_animation(payload, part_mp4, dur, fps)
        else:
            encode_part(payload, part_mp4, dur)
        print(f"  part {idx} [{label}]: {dur:.3f}s -> {os.path.getsize(part_mp4)//1024}KB")
        part_files.append(part_mp4)

    # concat（相对路径 + cwd=tmp，规避旧版 ffmpeg 绝对路径 bug）
    with open(os.path.join(tmp, "concat.txt"), "w", encoding="utf-8") as f:
        for p in part_files:
            f.write(f"file '{os.path.basename(p)}'\n")

    print("\n=== concat 拼接 + 音频 ===")
    if os.path.exists(OUTPUT_VIDEO):
        os.remove(OUTPUT_VIDEO)
    cmd = [FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", "concat.txt",
           "-i", AUDIO_PATH, "-c:v", "copy", "-c:a", "aac", "-b:a", "128k",
           "-shortest", os.path.basename(OUTPUT_VIDEO)]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=300, cwd=tmp)
    if r.returncode != 0:
        print("FFMPEG STDERR:", r.stderr[-1200:])
        sys.exit(1)
    sz = os.path.getsize(OUTPUT_VIDEO) / 1024 / 1024
    print(f"\n  输出: {OUTPUT_VIDEO} ({sz:.1f}MB) 时长 {total_dur:.1f}s")
    print("  ✅ 榜单版视频完成")


if __name__ == "__main__":
    main()
