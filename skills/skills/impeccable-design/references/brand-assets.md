# Brand Asset Generation (Pillow)

Generate marketing/social media brand images programmatically with Python/Pillow, matching an existing website's design language.

## When to Use

User asks for: "cover image", "banner", "social media image", "Buy Me a Coffee cover", "GitHub social preview", "brand image", "marketing asset", "OG image"

## Prerequisites

```python
from PIL import Image, ImageDraw, ImageFont
```

## Workflow

### 1. Extract Brand DNA from Existing Site

Read the site's CSS to capture:
- **Color palette:** `--gradient-start`, `--gradient-end`, `--bg-dark`, `--text`, `--text-secondary`
- **Typography:** font families, weights, sizes
- **Design motifs:** particles, glow effects, gradient accents, border radii, glassmorphism

### 2. Choose Canvas Dimensions

| Platform | Size |
|----------|------|
| Buy Me a Coffee | 1600×400 |
| GitHub Social Preview | 1280×640 |
| Twitter/X Header | 1500×500 |
| YouTube Banner | 2560×1440 |
| OG Image (link preview) | 1200×630 |

### 3. Build the Image

**Linear gradient background:**
```python
def lerp_color(a, b, t):
    return tuple(int(x + (y - x) * t) for x, y in zip(a, b))

for y in range(H):
    t = y / H
    color = lerp_color(GRADIENT_A, GRADIENT_B, t)
    draw.line([(0, y), (W, y)], fill=color)
```

**Glow effect (behind logo):**
```python
for r in range(180, 0, -1):
    alpha = max(0, int(16 * (1 - r / 180)))
    cx, cy = 210, 200
    draw.ellipse([cx - r, cy - r, cx + r, cy + r],
                 fill=(*PURPLE, alpha))
```

**Rounded rectangle:**
```python
def draw_rounded_rect(draw, xy, radius, fill=None, outline=None, width=1):
    x1, y1, x2, y2 = xy
    draw.pieslice([x1, y1, x1 + radius*2, y1 + radius*2], 180, 270, fill=fill)
    draw.pieslice([x2 - radius*2, y1, x2, y1 + radius*2], 270, 360, fill=fill)
    draw.pieslice([x1, y2 - radius*2, x1 + radius*2, y2], 90, 180, fill=fill)
    draw.pieslice([x2 - radius*2, y2 - radius*2, x2, y2], 0, 90, fill=fill)
    draw.rectangle([x1 + radius, y1, x2 - radius, y2], fill=fill)
    draw.rectangle([x1, y1 + radius, x2, y2 - radius], fill=fill)
```

**CJK font support** (for Chinese/Japanese/Korean brands):
```python
FONT_CN = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
FONT_CN_MED = "/usr/share/fonts/opentype/noto/NotoSansCJK-Medium.ttc"
```

**Decorative elements:**
- Particles: random-position ellipses with alpha
- Bottom gradient bar: horizontal line with per-pixel color lerp
- Dot matrix patterns: offset grid of small circles
- Sine-wave accent lines: `y = baseline + amplitude * sin(x / period)`

### 4. Pitfalls

- **Pillow text anchor:** Use `anchor="lm"` for left-middle, `anchor="mm"` for center-middle. Without anchor, text positioning is from top-left corner.
- **CJK fonts:** `.ttc` files work with Pillow but `font.truetype()` handles them fine. Always specify the font file path as a system font, not a guessed path.
- **RGBA vs RGB:** Save as RGBA if using alpha blending. Convert to RGB before saving as JPEG.
- **Font fallback:** Check `fc-list :lang=zh` for CJK fonts. DejaVu won't render CJK characters.
- **Random seed:** Set `random.seed(42)` (or any fixed value) for reproducible decorative elements.
- **File too large:** PNG at 1600×400 is ~150-300KB. For social platforms, this is fine. For OG images, optimize with `pngquant` or save as JPEG.

## Example Invocation

See full working example at the session's output path. The pattern:
1. Extract colors/fonts from site CSS variables
2. Build gradient bg + glow + logo + text + decoration
3. Match the site's theme (dark vs light mode, brand colors)
4. Save as PNG
