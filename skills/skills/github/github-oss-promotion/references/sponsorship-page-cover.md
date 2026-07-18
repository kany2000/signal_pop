# Buy Me a Coffee Cover Image Generator (1600×400)

Generate a branded cover image for your Buy Me a Coffee profile page using Python Pillow. Matches a dark-theme website with purple-blue gradient accents.

## Requirements

```bash
pip install pillow
```

## Full Script

```python
#!/usr/bin/env python3
from PIL import Image, ImageDraw, ImageFont
import math, random, os

W, H = 1600, 400
OUT = "bmc-cover.png"

# Brand colors
GRADIENT_A = (10, 10, 15)
GRADIENT_B = (18, 18, 26)
PURPLE = (102, 126, 234)
PURPLE_DEEP = (118, 75, 162)
WHITE = (255, 255, 255)

# Font paths (adjust for your system)
FONT_EN = "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf"
FONT_EN_REG = "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf"
FONT_CN = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
FONT_CN_MED = "/usr/share/fonts/opentype/noto/NotoSansCJK-Medium.ttc"

def lerp(a, b, t):
    return tuple(int(x + (y - x) * t) for x, y in zip(a, b))

def draw_rounded_rect(draw, xy, radius, fill=None):
    x1, y1, x2, y2 = xy
    draw.pieslice([x1, y1, x1+radius*2, y1+radius*2], 180, 270, fill=fill)
    draw.pieslice([x2-radius*2, y1, x2, y1+radius*2], 270, 360, fill=fill)
    draw.pieslice([x1, y2-radius*2, x1+radius*2, y2], 90, 180, fill=fill)
    draw.pieslice([x2-radius*2, y2-radius*2, x2, y2], 0, 90, fill=fill)
    draw.rectangle([x1+radius, y1, x2-radius, y2], fill=fill)
    draw.rectangle([x1, y1+radius, x2, y2-radius], fill=fill)

img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)

# Dark gradient background
for y in range(H):
    t = y / H
    draw.line([(0, y), (W, y)], fill=lerp(GRADIENT_A, GRADIENT_B, t))

# Glow behind logo
for r in range(180, 0, -1):
    alpha = max(0, int(16 * (1 - r / 180)))
    draw.ellipse([210-r, 200-r, 210+r, 200+r],
                 fill=(PURPLE[0], PURPLE[1], PURPLE[2], alpha))

# Decorative particles
random.seed(42)
for _ in range(30):
    x, y, sz = random.randint(0, W), random.randint(0, H), random.randint(2, 5)
    draw.ellipse([x, y, x+sz, y+sz],
                 fill=(*PURPLE, random.randint(30, 80)))

# Bottom accent bar (gradient, 4px)
for x in range(0, W, 2):
    t = x / W
    c = (int(PURPLE[0]+(PURPLE_DEEP[0]-PURPLE[0])*t),
         int(PURPLE[1]+(PURPLE_DEEP[1]-PURPLE[1])*t),
         int(PURPLE[2]+(PURPLE_DEEP[2]-PURPLE[2])*t))
    draw.line([(x, H-4), (x+2, H-4)], fill=c, width=4)

# Logo: rounded square with "QT" monogram
draw_rounded_rect(draw, (60, 130, 200, 270), 30, fill=PURPLE)
font_logo = ImageFont.truetype(FONT_EN, 48)
draw.text((130, 198), "QT", fill=WHITE, font=font_logo, anchor="mm")

# Title
font_title = ImageFont.truetype(FONT_EN, 56)
draw.text((280, 165), "QuickTranslate", fill=WHITE, font=font_title, anchor="lm")

# Tagline (CJK)
font_tag = ImageFont.truetype(FONT_CN, 28)
draw.text((280, 235), "选中文字 · 即刻翻译", fill=(180, 180, 200), font=font_tag, anchor="lm")

# Subtitle (EN)
font_sub = ImageFont.truetype(FONT_EN_REG, 18)
draw.text((280, 278), "Translate at the speed of thought", fill=(140, 140, 160), font=font_sub, anchor="lm")

# Badge
draw_rounded_rect(draw, (280, 305, 410, 335), 15, fill=(*PURPLE, 50))
draw.rounded_rectangle([280, 305, 410, 335], radius=15, outline=PURPLE+(180,), width=1)
font_badge = ImageFont.truetype(FONT_CN_MED, 16)
draw.text((345, 320), "✦ 开源免费", fill=PURPLE+(255,), font=font_badge, anchor="mm")

# Decorative right-side dot pattern
dot_x, dot_y = 1350, 100
for row in range(5):
    for col in range(6):
        ox = dot_x + col*30 + (row%2)*15
        oy = dot_y + row*36
        sz = 3 - (abs(row-2)+abs(col-2))%3 * 0.5
        if sz > 1:
            alpha = 30 + (row+col)*8
            draw.ellipse([ox-sz, oy-sz, ox+sz, oy+sz],
                         fill=(*PURPLE, min(alpha, 80)))

img.save(OUT)
print(f"Saved: {OUT} ({img.size[0]}x{img.size[1]}px)")
```

## Customization

| Element | Change | 
|---------|--------|
| Colors | Modify `GRADIENT_A`, `PURPLE`, `PURPLE_DEEP` variables |
| Project name | Replace `"QuickTranslate"` with your project name |
| Tagline | Replace `"选中文字 · 即刻翻译"` (CJK) and English subtitle |
| Logo | Replace `"QT"` monogram text, or draw an actual icon |
| Font paths | Update `FONT_*` paths to match your system (check `fc-list`) |
| Logo position | Edit `draw_rounded_rect` coordinates (60, 130, 200, 270) |

## CJK Font Discovery

```bash
# Find available CJK fonts
fc-list :lang=zh
# Common paths:
# /usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc
# /usr/share/fonts/truetype/arphic/uming.ttc
# /usr/share/fonts/truetype/wqy/wqy-zenhei.ttc
```
