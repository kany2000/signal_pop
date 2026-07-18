#!/usr/bin/env python3
"""
Signal Pop 封面图生成 — 明亮未来科技风格
参考: cover_20260703.png (银白渐变 + 青色四角框 + 白主标题 + 青霓虹副标题)

每期同时出 4:3 与 16:9 两张:
  cover_YYYYMMDD.png       -> 4:3  (1920x1440)  主用（发帖偏好）
  cover_YYYYMMDD_16x9.png  -> 16:9 (1920x1080)  宽版（YouTube 等）

用法: python3 gen_cover.py [日期] [输出目录]
  日期格式 YYYYMMDD（缺省 = 今天）
"""
import sys, os, urllib.request
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import numpy as np

Cyan = (0, 255, 255)
Silver = (200, 210, 220)
White = (255, 255, 255)
DarkGray = (80, 90, 100)

# 年轻活泼女性形象图池（Unsplash，每期按日期轮替）
ANCHOR_POOL = [
    "https://images.unsplash.com/photo-1534528741775-53994a69daeb",    # 0 冷蓝光影女
    "https://images.unsplash.com/photo-1508214751196-bcfd4ca60f91",    # 1 金发暖笑
    "https://images.unsplash.com/photo-1544005313-94ddf0286df2",       # 2 条纹衬衫
    "https://images.unsplash.com/photo-1551836022-d5d88e9218df",       # 3 蓝衫会议
    "https://images.unsplash.com/photo-1567532939604-b6b5b0db2604",    # 4 长发黑衫
    "https://images.unsplash.com/photo-1581403341630-a6e0b9d2d257",    # 5 黑高领
    "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2",    # 6 黑西装主播
    "https://images.unsplash.com/photo-1580489944761-15a19d654956",    # 7 微笑职业
    "https://images.unsplash.com/photo-1594744803329-e58b31de8bf5",    # 8 金丝眼镜
    "https://images.unsplash.com/photo-1573497019940-1c28c88b4f3e",    # 9 条纹西装
]

CJK_BOLD = "/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc"
CJK_REG  = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"

# 基准设计尺寸（所有布局按此缩放，保证两种比例下观感一致）
REF_W, REF_H = 1920, 1080


def lerp(a, b, t):
    t = max(0, min(1, t))
    return a + (b - a) * t


def build_bg(W, H):
    """银灰→白径向渐变背景（中心高光，四周微暗）"""
    arr = np.zeros((H, W, 3), dtype=np.uint8)
    cx, cy = W // 2, H // 2
    max_d = ((W // 2) ** 2 + (H // 2) ** 2) ** 0.5
    for y in range(H):
        for x in range(W):
            dist = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
            t = max(0, 1 - dist / max_d)
            arr[y, x] = [
                int(lerp(180, 255, t)),
                int(lerp(190, 255, t)),
                int(lerp(200, 255, t)),
            ]
    bg = Image.fromarray(arr)
    gd = ImageDraw.Draw(bg)
    step = int(80 * W / REF_W)
    for x in range(0, W, step):
        gd.line([(x, 0), (x, H)], fill=(180, 190, 200), width=1)
    for y in range(0, H, step):
        gd.line([(0, y), (W, y)], fill=(180, 190, 200), width=1)
    return bg


def neon_text(canvas, W, H, text, pos, font, color=(0, 255, 255), white_core=True):
    """青色霓虹发光效果"""
    r, g, b = color
    cx, cy = pos
    for (blur_r, density, offsets) in [
        (14, 10, range(-14, 15, 5)),
        (9, 22, range(-9, 10, 4)),
        (5, 50, range(-5, 6, 3)),
        (3, 90, range(-3, 4, 2)),
        (2, 130, range(-2, 3)),
    ]:
        for dr in offsets:
            for dc in offsets:
                dist = (dr ** 2 + dc ** 2) ** 0.5
                if dist > abs(offsets[0]):
                    continue
                alpha = int(density * (1 - dist / abs(offsets[0])))
                glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
                ImageDraw.Draw(glow).text((cx + dr, cy + dc), text, font=font, fill=(r, g, b, alpha))
                blur = glow.filter(ImageFilter.GaussianBlur(radius=blur_r))
                canvas.paste(blur, mask=blur.split()[3])
    if white_core:
        core = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(core).text((cx, cy), text, font=font, fill=(255, 255, 255, 255))
        canvas.paste(core, mask=core.split()[3])


def corner_brackets(canvas, W, H):
    """四角青色直角装饰线（HUD取景框）"""
    bd = ImageDraw.Draw(canvas)
    bw, bh = int(200 * W / REF_W), int(200 * H / REF_H)
    m = int(40 * W / REF_W)
    corners = [
        (m, m, m + bw, m + bh),                       # 左上
        (W - m - bw, m, W - m, m + bh),               # 右上
        (m, H - m - bh, m + bw, H - m),               # 左下
        (W - m - bw, H - m - bh, W - m, H - m),       # 右下
    ]
    for (x1, y1, x2, y2) in corners:
        for glow_w, glow_a in [(10, 12), (6, 25), (3, 60), (2, 150)]:
            bd.line([(x1, y1), (x2, y1)], fill=(0, 255, 255, glow_a), width=glow_w)
            bd.line([(x1, y1), (x1, y2)], fill=(0, 255, 255, glow_a), width=glow_w)


def get_anchor(date_str):
    """按日期选不同年轻女性形象，下载并羽化"""
    seed = sum(ord(c) for c in date_str)
    idx = seed % len(ANCHOR_POOL)
    url = f"{ANCHOR_POOL[idx]}?w=900&q=85"
    cache = f"/tmp/anchor_{date_str.replace('.', '')}.jpg"
    if not os.path.exists(cache):
        print(f"Downloading anchor #{idx} for {date_str}...")
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            with open(cache, "wb") as f:
                f.write(resp.read())
    anchor = Image.open(cache).convert("RGBA")
    return anchor


def build_anchor_masked(bg, anchor, W, H):
    """右侧叠加年轻女性形象（亮背景适配版：脸部清晰，仅最边缘羽化）"""
    aw, ah = anchor.size
    crop = (aw // 6, 0, aw - aw // 6, ah)
    ac = anchor.crop(crop)
    scale = (W * 0.45) / aw
    nw, nh = int(aw * scale), int(ah * scale)
    ac = ac.resize((nw, nh), Image.LANCZOS)
    mask = Image.new("L", (nw, nh), 255)
    md = ImageDraw.Draw(mask)
    edge_zone = min(nw, nh) // 5
    for i in range(edge_zone):
        alpha = int(255 * (i / edge_zone) ** 2)
        md.rectangle([i, i, nw - i, nh - i], outline=alpha)
    mask = mask.filter(ImageFilter.GaussianBlur(radius=12))
    ac.putalpha(mask)
    ax = W - nw + 20
    ay = (H - nh) // 2
    bg.paste(ac, (ax, ay), ac)


def make_cover(date_str="20260710", output=None, W=1920, H=1080):
    # 布局按基准尺寸等比缩放，保证 4:3 / 16:9 观感一致
    sx, sy = W / REF_W, H / REF_H
    print(f"Building cover for {date_str} @ {W}x{H}...")
    bg = build_bg(W, H).convert("RGBA")

    try:
        anchor = get_anchor(date_str)
        build_anchor_masked(bg, anchor, W, H)
    except Exception as e:
        print(f"[WARN] 主播图下载失败: {e}, 跳过主播图")

    font_main = ImageFont.truetype(CJK_BOLD, int(160 * sy))
    font_sub  = ImageFont.truetype(CJK_BOLD, int(58 * sy))
    font_tag  = ImageFont.truetype(CJK_REG,  int(40 * sy))

    txt_x = int(80 * sx)
    txt_top = H // 2 - int(130 * sy)

    neon_text(bg, W, H, "隔天信号弹", (txt_x, txt_top), font_main, Cyan, white_core=True)
    neon_text(bg, W, H, "MARK哥的创想引擎", (txt_x, txt_top + int(190 * sy)), font_sub, (0, 200, 255), white_core=True)

    ly = txt_top + int(260 * sy)
    for dx in range(int(560 * sx)):
        a = max(0, 1 - abs(dx - 280 * sx) / (280 * sx))
        for dy in range(3):
            bg.putpixel((txt_x + dx, ly + dy), (0, int(255 * a), int(255 * a), 200))

    corner_brackets(bg, W, H)

    tl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(tl).text((txt_x, int(50 * sy)), "AI · 科技 · 资讯", font=font_tag, fill=(0, 255, 255, 140))
    bg.paste(tl, mask=tl.split()[3])

    dl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(dl).text((txt_x, H - int(80 * sy)), date_str, font=font_tag, fill=(100, 180, 220, 180))
    bg.paste(dl, mask=dl.split()[3])

    if output is None:
        d = date_str.replace(".", "")
        output = f"/home/kan/signal_pop/daily/output/cover_{d}.png"
    bg_rgb = bg.convert("RGB")
    bg_rgb.save(output, "PNG", quality=95)
    size_kb = os.path.getsize(output) // 1024
    print(f"Cover saved: {output} ({size_kb}KB)")
    return output


if __name__ == "__main__":
    date_str = sys.argv[1] if len(sys.argv) > 1 else __import__("datetime").datetime.now().strftime("%Y%m%d")
    out_dir  = sys.argv[2] if len(sys.argv) > 2 else "/home/kan/signal_pop/daily/output"
    from datetime import datetime, timedelta
    dt = datetime.strptime(date_str, "%Y%m%d") + timedelta(days=1)
    display_date = dt.strftime("%Y%m%d")
    d = date_str.replace(".", "")
    # 1) 先出 16:9 母版（基准尺寸 REF_W x REF_H，布局完美）
    tmp_169 = "/tmp/cover_master_16x9.png"
    make_cover(display_date, tmp_169, 1920, 1080)
    master = Image.open(tmp_169).convert("RGBA")
    # 2) 16:9 母版分割 + 4:3 左中右拼接
    # 左: 文字区域 0-500px, 中: 网格过渡 500-670px, 右: 人物 670-1440px
    master = Image.open(tmp_169).convert("RGBA")
    left_part = master.crop((0, 0, 500, 1080))
    mid_part = master.crop((500, 0, 670, 1080))
    right_part = master.crop((670, 0, 1920, 1080))
    # 铺到 1440x1080
    canvas_43 = Image.new("RGBA", (1440, 1080), (0, 0, 0, 0))
    canvas_43.paste(left_part, (0, 0))
    canvas_43.paste(mid_part.resize((170, 1080), Image.LANCZOS), (500, 0))
    canvas_43.paste(right_part.resize((770, 1080), Image.LANCZOS), (670, 0))
    # 背景用银白渐变
    bg_43 = build_bg(1440, 1080).convert("RGBA")
    bg_43.paste(canvas_43, mask=canvas_43.split()[3])
    p43_path = f"{out_dir}/cover_{d}.png"
    bg_43.convert("RGB").save(p43_path, "PNG", quality=95)
    print(f"4:3 saved: {p43_path} ({os.path.getsize(p43_path)//1024}KB)")
    # 3) 16:9 母版直接输出
    p169 = tmp_169
    p169_path = f"{out_dir}/cover_{d}_16x9.png"
    master.convert("RGB").save(p169_path, "PNG", quality=95)
    print(f"16:9 saved: {p169_path} ({os.path.getsize(p169_path)//1024}KB)")
    print("===== 封面生成完成 =====")
    print(p43_path)
    print(p169_path)
