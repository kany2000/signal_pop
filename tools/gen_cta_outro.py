#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成片尾「一键三连」动画短片（1920x1080 / 30fps / 6.0s / 无音轨）

2026-11-05 用户复审反馈：静态 cta_sanlian.png 只是「一张背景」，既没有背景图，
也不是「一键三连」动画。本脚本取代它，产出一段带夜景城市天际线背景的
真·动画收场板，在 render_weekly_py.py 的最终编码阶段 overlay 到片尾。

动效编排（本地时间 t，0~6.0s）：
  0.00~0.45  背景由底层画面交叉淡入（alpha fade 在最终编码里做）+ 缓慢推近
  0.15~1.35  品牌小标、主标题（淡入上移 30px）、副标题分层淡入
  1.05/1.60/2.15  三个圆形按钮 easeOutBack 依次弹入，各带一圈点击涟漪并点亮
  2.85~3.75  三连完成：中心扩散金色光波 + 三按钮同步脉冲 +「三连已点亮」
  全程       点亮后金色呼吸光晕 + 金粒子上浮
  3.50~4.60  两行收尾语依次淡入
  5.00~6.00  主流程 fade out 到黑（由 render_weekly_py.py 统一处理）

实现：PIL 逐帧绘制 → rawvideo RGB24 管道直喂 ffmpeg，不落 180 张中间 PNG。
背景默认 remotion_poc/public/base_ending_bg.jpg（平日版通用片尾夜景），
首次运行复制到 output/weekly/shared/cta_outro_bg.jpg（清理门禁白名单目录）；
可用 SIGNAL_POP_CTA_BG 指向任意图片覆盖。

⚠️ 改动本脚本 DUR 时必须同步 tools/render_weekly_py.py 的 CTA_DUR。

用法: python tools/gen_cta_outro.py [输出mp4]
"""
import math
import os
import random
import shutil
import subprocess
import sys

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FF = os.path.join(ROOT, "bin", "ffmpeg-9.0.1-essentials_build", "bin", "ffmpeg.exe")

W, H = 1920, 1080
FPS = 30
DUR = 6.0
N_FRAMES = int(FPS * DUR)

BG_SOURCE = os.path.join(ROOT, "remotion_poc", "public", "base_ending_bg.jpg")
BG_SHARED = os.path.join(ROOT, "output", "weekly", "shared", "cta_outro_bg.jpg")
OUT_DEFAULT = os.path.join(ROOT, "output", "weekly", "shared", "cta_outro.mp4")

GOLD = (212, 175, 55, 255)
GOLD_SOFT = (240, 205, 110, 255)
WHITE = (240, 246, 255, 255)
GREY = (164, 179, 198, 255)
DARK = (8, 12, 24, 255)
FONT_BOLD = "C:/Windows/Fonts/msyhbd.ttc"
FONT_REG = "C:/Windows/Fonts/msyh.ttc"

CX = [560, 960, 1360]
CY = 660
R = 100
LABELS = ["订阅", "关注", "转发"]
STARTS = [1.05, 1.60, 2.15]

# 固定种子，保证每次生成的动画完全一致（可复现、便于审片比对）
_rng = random.Random(20261106)
PARTICLES = [
    (_rng.randint(90, W - 90), _rng.randint(0, H),
     _rng.uniform(16, 46), _rng.uniform(0, 6.28),
     _rng.randint(2, 5), _rng.randint(70, 190))
    for _ in range(46)
]


def clamp(v, a=0.0, b=1.0):
    return max(a, min(b, v))


def ease_out_cubic(x):
    return 1.0 - (1.0 - x) ** 3


def ease_out_back(x):
    """Remotion 原三连动画用的同一条曲线，末端带轻微回弹。"""
    c1, c3 = 1.70158, 2.70158
    return 1.0 + c3 * (x - 1.0) ** 3 + c1 * (x - 1.0) ** 2


def fade(t, start, end):
    if t <= start:
        return 0.0
    if t >= end:
        return 1.0
    return ease_out_cubic((t - start) / (end - start))


def lerp_color(c1, c2, k):
    return tuple(int(a + (b - a) * k) for a, b in zip(c1, c2))


def font(size, bold=True):
    try:
        return ImageFont.truetype(FONT_BOLD if bold else FONT_REG, size)
    except Exception:
        return ImageFont.load_default()


def text_layer(text, size, color, bold=True, stroke=0):
    """把一行文字预渲染成带 alpha 的小图，避免每帧重排字体。"""
    f = font(size, bold)
    probe = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    bb = probe.textbbox((0, 0), text, font=f, stroke_width=stroke)
    w, h = bb[2] - bb[0] + 28, bb[3] - bb[1] + 28
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.text((14 - bb[0], 14 - bb[1]), text, font=f, fill=color,
           stroke_width=stroke, stroke_fill=DARK)
    return im


def alpha_scaled(layer, k):
    """用 256 项 LUT 缩放 alpha（比 point(lambda) 快一个数量级）。"""
    k = clamp(k)
    if k >= 0.999:
        return layer
    lut = [int(i * k) for i in range(256)]
    im = layer.copy()
    im.putalpha(layer.getchannel("A").point(lut))
    return im


def paste_center(dst, layer, cx, cy, k=1.0, dy=0):
    if k <= 0.001:
        return
    l = alpha_scaled(layer, k)
    dst.paste(l, (int(cx - l.width / 2), int(cy - l.height / 2 + dy)), l)


def star_points(cx, cy, r_outer, r_inner, count=5):
    pts = []
    for i in range(count * 2):
        a = -math.pi / 2 + i * math.pi / count
        r = r_outer if i % 2 == 0 else r_inner
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def make_background(path):
    """夜景城市天际线 → 暗化 + 蓝调 + 上下压暗渐变，输出 1.09 倍大图供推近。"""
    src = Image.open(path).convert("RGB")
    bw, bh = int(W * 1.09), int(H * 1.09)
    big = ImageOps.fit(src, (bw, bh), Image.LANCZOS)
    big = ImageEnhance.Brightness(big).enhance(0.60)
    big = ImageEnhance.Color(big).enhance(0.88)
    rgba = Image.alpha_composite(
        big.convert("RGBA"),
        Image.new("RGBA", (bw, bh), (6, 14, 30, 96)))
    grad = Image.new("RGBA", (bw, bh), (0, 0, 0, 0))
    gd = ImageDraw.Draw(grad)
    for y in range(bh):
        u = y / bh
        a = int(18 + 112 * (2 * abs(u - 0.5)) ** 1.6)
        gd.line((0, y, bw, y), fill=(4, 10, 22, a))
    return Image.alpha_composite(rgba, grad)


def bg_frame(big, t):
    """Ken Burns：裁切框从 1.085 倍缓慢收窄到 1.0 倍，形成极轻微推近。"""
    p = clamp(t / DUR)
    f = 1.085 - 0.085 * p
    cw, ch = int(W * f), int(H * f)
    x0, y0 = (big.width - cw) // 2, (big.height - ch) // 2
    return big.crop((x0, y0, x0 + cw, y0 + ch)).resize((W, H), Image.BICUBIC)


def make_glow(size=360):
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse((48, 48, size - 48, size - 48),
              outline=(212, 175, 55, 235), width=20)
    return im.filter(ImageFilter.GaussianBlur(22))


def build_layers():
    """所有静态文字层 + 光晕图 + 分隔线，一次性生成。"""
    layers = {
        "brand": text_layer("隔天信号弹 · 信蓝组合周末版", 34, GREY, False),
        "title": text_layer("喜欢这期？一键三连", 86, GOLD_SOFT, True, stroke=3),
        "sub": text_layer("订阅  ·  关注  ·  转发", 40, GREY, False),
        "done": text_layer("三连已点亮", 34, GOLD_SOFT, True),
        "foot1": text_layer("每周六 8 点，阿信和小蓝陪你聊透本周大事", 36, GREY, False),
        "foot2": text_layer("我们下期见", 48, GOLD_SOFT, True),
        "labels": [text_layer(s, 40, WHITE, True) for s in LABELS],
        "rule": Image.new("RGBA", (600, 3), (212, 175, 55, 190)),
        "glow": make_glow(),
    }
    return layers


def render_frame(t, big, L):
    frame = bg_frame(big, t)

    # ---- 1) 呼吸光晕（在按钮下方）----
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    for k, cx in enumerate(CX):
        st = STARTS[k]
        if t < st + 0.35:
            continue
        k_on = fade(t, st + 0.35, st + 0.95)
        breath = 0.30 + 0.15 * math.sin(t * 2.4 - k * 0.9)
        g = L["glow"]
        paste_center(glow, g, cx, CY, k_on * breath)
    frame = Image.alpha_composite(frame, glow)

    # ---- 2) 特效层：点击涟漪、三连光波、金色粒子 ----
    fx = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(fx)
    for k, cx in enumerate(CX):
        st = STARTS[k]
        p = (t - st - 0.02) / 0.72
        if 0.0 <= p <= 1.0:
            rr = R * 0.55 + 215 * ease_out_cubic(p)
            a = int(215 * (1.0 - p))
            d.ellipse((cx - rr, CY - rr, cx + rr, CY + rr),
                      outline=(240, 205, 110, a), width=7)
            r2 = rr * 0.72
            d.ellipse((cx - r2, CY - r2, cx + r2, CY + r2),
                      outline=(255, 244, 205, int(a * 0.55)), width=3)
    p = (t - 2.85) / 0.90
    if 0.0 <= p <= 1.0:
        rr = 90 + 1050 * ease_out_cubic(p)
        a = int(165 * (1.0 - p))
        d.ellipse((960 - rr, CY - rr, 960 + rr, CY + rr),
                  outline=(240, 205, 110, a), width=10)
    for (x0, y0, sp, ph, rad, aa) in PARTICLES:
        y = (y0 - sp * t) % (H + 80) - 40
        x = x0 + 14 * math.sin(t * 1.1 + ph)
        a = int(aa * fade(t, 0.55, 1.7) * (0.62 + 0.38 * math.sin(t * 2.0 + ph)))
        if a > 0:
            d.ellipse((x - rad, y - rad, x + rad, y + rad),
                      fill=(240, 205, 110, a))
    frame = Image.alpha_composite(frame, fx)

    # ---- 3) 按钮层：三圆依次弹入并点亮 ----
    btn = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    b = ImageDraw.Draw(btn)
    pulse = 1.0
    if 2.75 <= t <= 3.55:
        pulse = 1.0 + 0.09 * math.sin((t - 2.75) / 0.80 * math.pi)
    for k, cx in enumerate(CX):
        st = STARTS[k]
        if t < st:
            continue
        x = clamp((t - st) / 0.60)
        g = clamp(ease_out_back(x), 0.0, 1.12)
        r_now = max(4, int(R * (0.30 + 0.70 * g) * pulse))
        lit = fade(t, st, st + 0.55)
        ring = lerp_color((112, 130, 158, 255), GOLD, lit)
        b.ellipse((cx - r_now - 8, CY - r_now - 8, cx + r_now + 8, CY + r_now + 8),
                  fill=(20, 26, 38, 246), outline=(212, 175, 55, 90), width=3)
        b.ellipse((cx - r_now, CY - r_now, cx + r_now, CY + r_now),
                  fill=(20, 26, 38, 246), outline=ring, width=6)
        s = 0.38 + 0.62 * g
        col = lerp_color((96, 112, 138, 255), (255, 240, 190, 255), lit)
        if k == 0:  # ▶
            b.polygon([(cx - 30 * s, CY - 44 * s), (cx - 30 * s, CY + 44 * s),
                       (cx + 42 * s, CY)], fill=col)
        elif k == 1:  # ★
            b.polygon(star_points(cx, CY, 52 * s, 22 * s), fill=col)
        else:  # ↗
            b.line((cx - 42 * s, CY + 42 * s, cx + 38 * s, CY - 38 * s),
                   fill=col, width=max(2, int(13 * s)))
            b.polygon([(cx + 6 * s, CY - 46 * s), (cx + 52 * s, CY - 46 * s),
                       (cx + 52 * s, CY)], fill=col)
    frame = Image.alpha_composite(frame, btn)

    # ---- 4) 文字层（各自淡入，标题带上移）----
    paste_center(frame, L["brand"], W // 2, 132, fade(t, 0.15, 0.75))
    paste_center(frame, L["rule"], W // 2, 178, fade(t, 0.30, 0.90))
    paste_center(frame, L["title"], W // 2, 292, fade(t, 0.30, 1.00),
                 dy=int(30 * (1.0 - fade(t, 0.30, 1.00))))
    paste_center(frame, L["sub"], W // 2, 402, fade(t, 0.85, 1.35))
    for k, cx in enumerate(CX):
        st = STARTS[k]
        paste_center(frame, L["labels"][k], cx, CY + R + 62,
                     fade(t, st + 0.20, st + 0.62))
    paste_center(frame, L["done"], W // 2, 490, fade(t, 2.95, 3.50))
    paste_center(frame, L["foot1"], W // 2, 916, fade(t, 3.50, 4.10))
    paste_center(frame, L["foot2"], W // 2, 1006, fade(t, 4.05, 4.60))

    return frame.convert("RGB")


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else OUT_DEFAULT
    os.makedirs(os.path.dirname(out), exist_ok=True)

    bg_path = os.environ.get("SIGNAL_POP_CTA_BG", BG_SHARED)
    if not os.path.exists(bg_path):
        if not os.path.exists(BG_SOURCE):
            print(f"ERROR: 找不到片尾背景图 {BG_SOURCE}", file=sys.stderr)
            return 1
        os.makedirs(os.path.dirname(BG_SHARED), exist_ok=True)
        shutil.copy(BG_SOURCE, BG_SHARED)
        bg_path = BG_SHARED
        print(f"背景图已归档: {BG_SHARED}")

    big = make_background(bg_path)
    L = build_layers()
    log = os.path.join(os.path.dirname(out), "cta_outro_ffmpeg.log")

    cmd = [FF, "-y", "-v", "error",
           "-f", "rawvideo", "-pix_fmt", "rgb24",
           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-an", "-c:v", "libx264", "-preset", "fast", "-crf", "18",
           "-pix_fmt", "yuv420p", "-r", str(FPS),
           "-movflags", "+faststart", out]
    with open(log, "w", encoding="utf-8") as lf:
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=lf, stderr=subprocess.STDOUT)
        for i in range(N_FRAMES):
            p.stdin.write(render_frame(i / FPS, big, L).tobytes())
            if (i + 1) % 30 == 0:
                print(f"  帧 {i + 1}/{N_FRAMES}", flush=True)
        p.stdin.close()
        rc = p.wait()
    if rc != 0:
        print(f"ERROR: ffmpeg 退出码 {rc}，详见 {log}", file=sys.stderr)
        return rc
    print(f"OK  {out}  {W}x{H} / {FPS}fps / {DUR:.2f}s / {N_FRAMES}帧 / "
          f"{os.path.getsize(out) // 1024}KB")
    print(f"    背景: {bg_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
