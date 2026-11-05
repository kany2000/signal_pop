#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成片尾「一键三连」收场卡（1920x1080 RGBA 透明素材，供 ffmpeg overlay）

背景：末段 CTA 挂在 index40（econ_slide_4），而 577.76~708.92s 整段被 huashu
经济动画替换 → WeeklyTalk 里画的三连图标随 Remotion 画面一起被抹掉。
改为在最终编码阶段把本卡叠加到片尾最后 CTA_DUR 秒，带 0.6s 淡入。

卡片用本地 PIL 绘制，符号为几何图形（三角形/五角星/箭头），避免字体缺字乱码。
输出落在 output/weekly/shared/（清理门禁白名单），每期复用。

用法: python tools/gen_cta_sanlian.py [输出png]
"""
import math
import os
import sys

from PIL import Image, ImageDraw, ImageFont

W, H = 1920, 1080
GOLD = (212, 175, 55, 255)
GOLD_SOFT = (240, 205, 110, 255)
WHITE = (240, 246, 255, 255)
GREY = (164, 179, 198, 255)
FONT_BOLD = "C:/Windows/Fonts/msyhbd.ttc"
FONT_REG = "C:/Windows/Fonts/msyh.ttc"


def font(size, bold=True):
    p = FONT_BOLD if bold else FONT_REG
    try:
        return ImageFont.truetype(p, size)
    except Exception:
        return ImageFont.load_default()


def centered(draw, xy, text, f, fill, stroke=0, stroke_fill=None):
    x, y = xy
    bb = draw.textbbox((0, 0), text, font=f)
    draw.text((x - (bb[2] - bb[0]) / 2 - bb[0], y - (bb[3] - bb[1]) / 2 - bb[1]),
              text, font=f, fill=fill, stroke_width=stroke,
              stroke_fill=stroke_fill or (10, 16, 30, 255))


def star_points(cx, cy, r_outer, r_inner, count=5):
    pts = []
    for i in range(count * 2):
        a = -math.pi / 2 + i * math.pi / count
        r = r_outer if i % 2 == 0 else r_inner
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        root, "output", "weekly", "shared", "cta_sanlian.png")
    os.makedirs(os.path.dirname(out), exist_ok=True)

    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)

    # 完全不透明深色蒙版：经济动画收尾是白字图表，半透明会让底层文字
    # 透出来与收场卡标题重叠（2026-11-05 实测），故做干净的全屏收场板。
    d.rectangle((0, 0, W, H), fill=(8, 12, 24, 255))

    # 顶部品牌小标
    centered(d, (W // 2, 132), "隔天信号弹 · 信蓝组合周末版", font(34, False), GREY)
    d.line((W // 2 - 300, 178, W // 2 + 300, 178), fill=(212, 175, 55, 120), width=2)

    # 主标题
    centered(d, (W // 2, 292), "喜欢这期？一键三连", font(86, True), GOLD_SOFT,
             stroke=3, stroke_fill=(10, 16, 30, 255))
    centered(d, (W // 2, 402), "订阅  ·  关注  ·  转发", font(40, False), GREY)

    # 三个圆形图标
    cx_list = [560, 960, 1360]
    cy = 660
    r = 100
    labels = ["订阅", "关注", "转发"]
    for idx, (cx, label) in enumerate(zip(cx_list, labels)):
        # 干净的双层金边圆（不用半透明外发光：低 alpha 像素叠到视频上会泛白圈）
        d.ellipse((cx - r - 8, cy - r - 8, cx + r + 8, cy + r + 8),
                  fill=(20, 26, 38, 246), outline=(212, 175, 55, 90), width=3)
        d.ellipse((cx - r, cy - r, cx + r, cy + r),
                  fill=(20, 26, 38, 246), outline=GOLD, width=6)

        if idx == 0:  # ▶ 播放/订阅
            d.polygon([(cx - 30, cy - 44), (cx - 30, cy + 44), (cx + 42, cy)],
                      fill=(255, 240, 190, 255))
        elif idx == 1:  # ★ 关注
            d.polygon(star_points(cx, cy, 52, 22), fill=(255, 240, 190, 255))
        else:  # ↗ 转发
            d.line((cx - 42, cy + 42, cx + 38, cy - 38), fill=(255, 240, 190, 255), width=13)
            d.polygon([(cx + 6, cy - 46), (cx + 52, cy - 46), (cx + 52, cy)],
                      fill=(255, 240, 190, 255))

        centered(d, (cx, cy + r + 62), label, font(40, True), WHITE)

    # 底部收尾语
    centered(d, (W // 2, 940), "每周六 8 点，阿信和小蓝陪你聊透本周大事", font(36, False), GREY)
    centered(d, (W // 2, 1006), "我们下期见", font(48, True), GOLD_SOFT)

    im.save(out, "PNG")
    print(f"OK  {out}  {W}x{H}  {os.path.getsize(out) // 1024}KB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
