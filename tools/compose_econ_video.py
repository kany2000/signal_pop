#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""将 huashu-art-motion 渲染的全屏动画底片 (econ_huashu_bg.mp4) 与：
- 左下/右下贴边双主播头像 (V2.1 放大防遮挡版：140×140，y=930..1070，名牌内嵌在头像下沿，绝不触碰上方 y=900 图表来源行)
- 夹在两头像之间的大字号底部字幕条 (x: 178..1742, y: 944..1064, 高 120px，42px 粗体大字 + 描边)
- 顶部轻量品牌栏
- 11 段双播真实 TTS 音频 (econ_audio/tts.wav)
合成为完整的「大家一起聊经济」独立成片 & 可直接接入周末版正片的视频段。
"""
import os
import re
import sys
import json
import subprocess
from PIL import Image, ImageDraw, ImageFont, ImageFilter

PROJECT_ROOT = "E:/projects/signal_pop"
FFMPEG = "E:/projects/signal_pop/bin/ffmpeg-9.0.1-essentials_build/bin/ffmpeg.exe"
PUBLIC_DIR = os.path.join(PROJECT_ROOT, "remotion_poc", "public")

PREP_DATE = sys.argv[1] if len(sys.argv) > 1 else "20261016"
OUT_DIR = os.path.join(PROJECT_ROOT, "output", "weekly", PREP_DATE)
ECON_AUDIO_WAV = os.path.join(OUT_DIR, "econ_audio", "tts.wav")
ECON_AUDIO_JSON = os.path.join(OUT_DIR, "econ_audio", "tts_segments.json")
ECON_BG_MP4 = os.path.join(OUT_DIR, "econ_huashu", "econ_huashu_bg.mp4")
HUD_DIR = os.path.join(OUT_DIR, "econ_huashu", "hud_pages")
FINAL_ECON_MP4 = os.path.join(OUT_DIR, f"econ_talk_{PREP_DATE}_huashu.mp4")

W, H = 1920, 1080
FPS = 30

AXIN_BLUE = (58, 130, 210)
XIAOLAN_PINK = (220, 90, 150)
GOLD = (212, 175, 55)
WHITE = (248, 248, 252)
SUB_GREY = (185, 195, 210)


def load_font(size, bold=False):
    cands = [
        "C:/Windows/Fonts/msyhbd.ttc" if bold else "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/simhei.ttf",
        "C:/Windows/Fonts/Dengb.ttf" if bold else "C:/Windows/Fonts/Deng.ttf",
    ]
    for p in cands:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def split_text_into_pages(text, max_len=25):
    """每页 ≤25 字以保证 42px 超大粗体字号"""
    trimmed = text.strip()
    if len(trimmed) <= max_len:
        return [trimmed]
    parts = [p for p in re.split(r"([。！？；]+)", trimmed) if p]
    sentences = []
    buf = ""
    for p in parts:
        if re.match(r"^[。！？；]+$", p):
            buf += p
            if len(buf) >= 9:
                sentences.append(buf.strip())
                buf = ""
        else:
            if buf and len(buf) + len(p) > max_len:
                sentences.append(buf.strip())
                buf = p
            else:
                buf += p
    if buf.strip():
        sentences.append(buf.strip())

    refined = []
    for s in sentences:
        if len(s) > max_len + 2 and ("，" in s or "、" in s or "——" in s):
            sub = [sp for sp in re.split(r"([，、—]+)", s) if sp]
            sbuf = ""
            for sp in sub:
                if re.match(r"^[，、—]+$", sp):
                    sbuf += sp
                    if len(sbuf) >= 10:
                        refined.append(sbuf.strip())
                        sbuf = ""
                else:
                    if sbuf and len(sbuf) + len(sp) > max_len:
                        refined.append(sbuf.strip())
                        sbuf = sp
                    else:
                        sbuf += sp
            if sbuf.strip():
                refined.append(sbuf.strip())
        else:
            refined.append(s)
    return refined if refined else [trimmed]


def make_circle_avatar(img_path, size):
    im = Image.open(img_path).convert("RGBA").resize((size, size), Image.Resampling.LANCZOS)
    mask = Image.new("L", (size, size), 0)
    d = ImageDraw.Draw(mask)
    d.ellipse((0, 0, size - 1, size - 1), fill=255)
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    out.paste(im, (0, 0), mask)
    return out


def render_hud_page(speaker, page_text, page_idx, total_pages, axin_av, xiaolan_av, fonts):
    """生成单页 1920x1080 RGBA 透明叠加层（V2.1 放大且名牌下置防遮挡版）：
    - 顶部轻量品牌条 (y: 0..56)
    - 左下阿信 136x136 贴边头像 (x: 22..158, y: 932..1068)，名牌压在头像下沿 (y: 1042..1072)
    - 右下小蓝 136x136 贴边头像 (x: 1762..1898, y: 932..1068)，名牌压在头像下沿 (y: 1042..1072)
    - 底部中央大字号字幕条 (x: 176..1744, y: 944..1064, 高 120px，42px 粗体大字)
    """
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)

    is_axin = (speaker == "阿信")
    accent = AXIN_BLUE if is_axin else XIAOLAN_PINK

    # 1. 顶部轻量品牌栏
    draw.rectangle((0, 0, W, 56), fill=(10, 14, 24, 185))
    draw.line((0, 56, W, 56), fill=(212, 175, 55, 105), width=1)
    top_title = "隔天信号弹 · 周末特别版  ｜  大家一起聊经济"
    tb = draw.textbbox((0, 0), top_title, font=fonts["top"])
    draw.text(((W - (tb[2] - tb[0])) // 2, 12), top_title, font=fonts["top"], fill=GOLD + (248,))

    # 2. 左下阿信 136x136 头像 (x=22, y=932，顶端绝不超过 y=922，完全避开 y=900 图表来源行)
    av_sz = 136
    lx, ly = 22, 932
    if is_axin:
        glow = Image.new("RGBA", (av_sz + 24, av_sz + 24), (0, 0, 0, 0))
        gd = ImageDraw.Draw(glow)
        gd.ellipse((3, 3, av_sz + 20, av_sz + 20), outline=AXIN_BLUE + (225,), width=5)
        glow = glow.filter(ImageFilter.GaussianBlur(4))
        canvas.alpha_composite(glow, (lx - 12, ly - 12))
        canvas.alpha_composite(axin_av, (lx, ly))
        draw.ellipse((lx - 2, ly - 2, lx + av_sz + 2, ly + av_sz + 2), outline=AXIN_BLUE + (255,), width=4)
        # 底部内嵌醒目名牌
        draw.rounded_rectangle((lx + 24, ly + av_sz - 28, lx + av_sz - 24, ly + av_sz + 4), radius=12, fill=AXIN_BLUE + (245,), outline=WHITE + (180,), width=1)
        draw.text((lx + 46, ly + av_sz - 27), "阿信", font=fonts["tag"], fill=WHITE + (255,))
    else:
        dim = axin_av.copy()
        r, g, b, a = dim.split()
        a = a.point(lambda p: int(p * 0.45))
        dim = Image.merge("RGBA", (r, g, b, a))
        canvas.alpha_composite(dim, (lx, ly))
        draw.ellipse((lx, ly, lx + av_sz - 1, ly + av_sz - 1), outline=(120, 140, 170, 110), width=2)
        draw.rounded_rectangle((lx + 26, ly + av_sz - 26, lx + av_sz - 26, ly + av_sz + 2), radius=11, fill=(18, 24, 38, 200))
        draw.text((lx + 46, ly + av_sz - 26), "阿信", font=fonts["tag"], fill=(165, 175, 190, 165))

    # 3. 右下小蓝 136x136 头像 (x=1762, y=932)
    rx, ry = W - 22 - av_sz, 932
    if not is_axin:
        glow = Image.new("RGBA", (av_sz + 24, av_sz + 24), (0, 0, 0, 0))
        gd = ImageDraw.Draw(glow)
        gd.ellipse((3, 3, av_sz + 20, av_sz + 20), outline=XIAOLAN_PINK + (225,), width=5)
        glow = glow.filter(ImageFilter.GaussianBlur(4))
        canvas.alpha_composite(glow, (rx - 12, ry - 12))
        canvas.alpha_composite(xiaolan_av, (rx, ry))
        draw.ellipse((rx - 2, ry - 2, rx + av_sz + 2, ry + av_sz + 2), outline=XIAOLAN_PINK + (255,), width=4)
        draw.rounded_rectangle((rx + 24, ry + av_sz - 28, rx + av_sz - 24, ry + av_sz + 4), radius=12, fill=XIAOLAN_PINK + (245,), outline=WHITE + (180,), width=1)
        draw.text((rx + 46, ry + av_sz - 27), "小蓝", font=fonts["tag"], fill=WHITE + (255,))
    else:
        dim = xiaolan_av.copy()
        r, g, b, a = dim.split()
        a = a.point(lambda p: int(p * 0.45))
        dim = Image.merge("RGBA", (r, g, b, a))
        canvas.alpha_composite(dim, (rx, ry))
        draw.ellipse((rx, ry, rx + av_sz - 1, ry + av_sz - 1), outline=(150, 120, 140, 110), width=2)
        draw.rounded_rectangle((rx + 26, ry + av_sz - 26, rx + av_sz - 26, ry + av_sz + 2), radius=11, fill=(18, 24, 38, 200))
        draw.text((rx + 46, ry + av_sz - 26), "小蓝", font=fonts["tag"], fill=(165, 175, 190, 165))

    # 4. 底部中央高可读性大字幕条 (x: 176..1744, y: 944..1064, 高 120px)
    bx0, by0, bx1, by1 = 176, 944, 1744, 1064
    draw.rounded_rectangle((bx0, by0, bx1, by1), radius=24, fill=(12, 18, 30, 238), outline=accent + (235,), width=3)

    # 说话人彩色竖条 + 36px 粗体名字
    draw.rounded_rectangle((bx0 + 22, by0 + 26, bx0 + 32, by1 - 26), radius=5, fill=accent + (255,))
    spk_label = f"{speaker}："
    draw.text((bx0 + 44, by0 + 33), spk_label, font=fonts["spk"], fill=accent + (255,))

    # 台词文本（42px 粗体为主，带黑色描边阴影）
    txt_x = bx0 + 158
    max_txt_w = (bx1 - 102) - txt_x
    f_sub = fonts["sub_42"]
    tb = draw.textbbox((0, 0), page_text, font=f_sub)
    if (tb[2] - tb[0]) > max_txt_w:
        f_sub = fonts["sub_38"]
        tb = draw.textbbox((0, 0), page_text, font=f_sub)
    if (tb[2] - tb[0]) > max_txt_w:
        f_sub = fonts["sub_34"]
        tb = draw.textbbox((0, 0), page_text, font=f_sub)

    txt_y = by0 + (by1 - by0 - (tb[3] - tb[1])) // 2 - 6
    draw.text((txt_x, txt_y), page_text, font=f_sub, fill=WHITE + (255,), stroke_width=2, stroke_fill=(0, 0, 0, 220))

    # 右侧分句页码指示
    if total_pages > 1:
        pg_str = f"{page_idx + 1}/{total_pages}"
        draw.rounded_rectangle((bx1 - 88, by0 + 36, bx1 - 20, by1 - 36), radius=14, fill=(255, 255, 255, 26), outline=accent + (140,), width=1)
        draw.text((bx1 - 74, by0 + 42), pg_str, font=fonts["tag"], fill=SUB_GREY + (245,))

    return canvas


def main():
    segs = json.load(open(ECON_AUDIO_JSON, encoding="utf-8"))
    os.makedirs(HUD_DIR, exist_ok=True)

    axin_av = make_circle_avatar(os.path.join(PUBLIC_DIR, "anchor_axin.jpg"), 136)
    xiaolan_av = make_circle_avatar(os.path.join(PUBLIC_DIR, "anchor_xiaolan.jpg"), 136)
    fonts = {
        "top": load_font(25, bold=True),
        "spk": load_font(36, bold=True),
        "sub_42": load_font(42, bold=True),
        "sub_38": load_font(38, bold=True),
        "sub_34": load_font(34, bold=True),
        "tag": load_font(21, bold=True),
    }

    cum_t = 0.0
    prev_f = 0
    page_items = []
    p_counter = 0

    for seg in segs:
        cum_t += seg["dur"]
        cur_f = round(cum_t * FPS)
        seg_f = cur_f - prev_f
        prev_f = cur_f

        pages = split_text_into_pages(seg["text"])
        total_chars = sum(max(len(p), 1) for p in pages)
        used_f = 0
        for i, p_txt in enumerate(pages):
            if i == len(pages) - 1:
                pf = seg_f - used_f
            else:
                pf = max(1, round(seg_f * (len(p_txt) / total_chars)))
                used_f += pf
            p_counter += 1
            png_path = os.path.join(HUD_DIR, f"hud_{p_counter:03d}.png")
            im = render_hud_page(seg["speaker"], p_txt, i, len(pages), axin_av, xiaolan_av, fonts)
            im.save(png_path)
            page_items.append((png_path, pf / FPS, pf))

    tot_f = sum(x[2] for x in page_items)
    print(f"已生成 {len(page_items)} 张透明 HUD 分句图层(V2.1名牌下置防遮挡版)，总帧数={tot_f} ({tot_f/FPS:.2f}s)")

    if "--hud-only" in sys.argv:
        return

    if not os.path.exists(ECON_BG_MP4):
        print(f"等待底片生成: {ECON_BG_MP4}")
        sys.exit(1)

    concat_file = os.path.join(HUD_DIR, "hud_concat.txt")
    with open(concat_file, "w", encoding="utf-8") as f:
        for png_p, dur_s, _ in page_items:
            f.write(f"file '{png_p.replace(chr(92), '/')}'\n")
            f.write(f"duration {dur_s:.6f}\n")
        f.write(f"file '{page_items[-1][0].replace(chr(92), '/')}'\n")

    cmd = [
        FFMPEG, "-y", "-v", "error",
        "-i", ECON_BG_MP4,
        "-f", "concat", "-safe", "0", "-i", concat_file,
        "-i", ECON_AUDIO_WAV,
        "-filter_complex", "[0:v][1:v]overlay=0:0:shortest=1[v]",
        "-map", "[v]", "-map", "2:a",
        "-c:v", "libx264", "-preset", "fast", "-crf", "18", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
        "-shortest", FINAL_ECON_MP4
    ]
    subprocess.run(cmd, check=True)
    print(f"\n✅ 聊经济(V2.1放大版)成片已合成: {FINAL_ECON_MP4}")


if __name__ == "__main__":
    main()
