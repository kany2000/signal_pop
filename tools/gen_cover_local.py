#!/usr/bin/env python3
"""Generate Signal Pop cover locally (no network)."""
import sys, os, math
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1920, 1080
CJK_BOLD = "/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc"
CJK_REG  = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"

def neon_text(canvas, text, pos, font, color=(0, 255, 255)):
    r, g, b = color
    cx, cy = pos
    for (blur_r, density, offsets) in [
        (14, 10, range(-14, 15, 5)),
        (9,  22, range(-9, 10, 4)),
        (5,  50, range(-5, 6, 3)),
        (3,  90, range(-3, 4, 2)),
        (2, 130, range(-2, 3)),
    ]:
        for dr in offsets:
            for dc in offsets:
                dist = (dr**2 + dc**2) ** 0.5
                if dist > abs(offsets[0]): continue
                alpha = int(density * (1 - dist / abs(offsets[0])))
                glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
                ImageDraw.Draw(glow).text((cx+dr, cy+dc), text, font=font, fill=(r, g, b, alpha))
                blur = glow.filter(ImageFilter.GaussianBlur(radius=blur_r))
                canvas.paste(blur, mask=blur.split()[3])
    core = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(core).text((cx, cy), text, font=font, fill=(255, 255, 255, 255))
    canvas.paste(core, mask=core.split()[3])

def build_bg():
    bg = Image.new("RGB", (W, H), (3, 5, 14))
    for y in range(H):
        for x in range(W):
            dx, dy = x - W//2, y - H//2
            dist = (dx**2 + dy**2) ** 0.5
            max_d = ((W//2)**2 + (H//2)**2) ** 0.5
            t = max(0, 1 - dist / max_d)
            bg.putpixel((x, y), (int(3+(17*t)), int(5+(27*t)), int(14+(51*t))))
    gd = ImageDraw.Draw(bg)
    for x in range(0, W, 50):
        gd.line([(x, 0), (x, H)], fill=(0, 40, 60), width=1)
    for y in range(0, H, 50):
        gd.line([(0, y), (W, y)], fill=(0, 40, 60), width=1)
    vign = Image.new("L", (W, H), 255)
    vd = ImageDraw.Draw(vign)
    for i in range(80):
        v = int(255 * (1 - (i/80)**1.4))
        vd.rectangle([i, i, W-i, H-i], outline=v)
    vign = vign.filter(ImageFilter.GaussianBlur(radius=100))
    bg.paste(vign, mask=vign)
    return bg

def make_cover(date_str="2026.07.03", output=None):
    print(f"Building cover for {date_str}...")
    bg = build_bg()
    bg = bg.convert("RGBA")
    font_main = ImageFont.truetype(CJK_BOLD, 155)
    font_sub  = ImageFont.truetype(CJK_BOLD, 58)
    font_tag  = ImageFont.truetype(CJK_REG,  40)
    txt_x, txt_top = 80, H // 2 - 120
    neon_text(bg, "隔天信号弹", (txt_x, txt_top), font_main, (0, 255, 255))
    neon_text(bg, "MARK哥的创想引擎", (txt_x, txt_top + 185), font_sub, (0, 200, 255))
    ly = txt_top + 255
    for dx in range(560):
        a = max(0, 1 - abs(dx - 280) / 280)
        for dy in range(3):
            bg.putpixel((txt_x + dx, ly + dy), (0, int(255*a), int(255*a), 255))
    dl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(dl).text((txt_x, H - 75), date_str, font=font_tag, fill=(100, 180, 220, 200))
    bg.paste(dl, mask=dl.split()[3])
    tl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(tl).text((txt_x, 40), "AI · 科技 · 资讯", font=font_tag, fill=(0, 255, 255, 120))
    bg.paste(tl, mask=tl.split()[3])
    bd3 = ImageDraw.Draw(bg)
    for bx, by, bw, bh in [
        (40, 40, 160, 160), (W-160, 40, W-40, 160),
        (40, H-160, 160, H-40), (W-160, H-160, W-40, H-40)]:
        for glow_w, glow_a in [(8, 15), (5, 25), (3, 60), (1, 180)]:
            bd3.line([(bx, by), (bx+bw, by)], fill=(0, 255, 255, glow_a), width=glow_w)
            bd3.line([(bx, by), (bx, by+bh)], fill=(0, 255, 255, glow_a), width=glow_w)
    bg_rgb = bg.convert("RGB")
    if output is None:
        output = f"/home/kan/signal_pop/daily/output/cover_{date_str.replace('.','')}.png"
    bg_rgb.save(output, "PNG", quality=95)
    size_kb = os.path.getsize(output) // 1024
    print(f"Cover saved: {output} ({size_kb}KB)")
    return output

if __name__ == "__main__":
    date_str = sys.argv[1] if len(sys.argv) > 1 else "2026.07.03"
    output   = sys.argv[2] if len(sys.argv) > 2 else None
    make_cover(date_str, output)
