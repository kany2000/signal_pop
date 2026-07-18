# YouTube Watermark / Channel Logo (150×150)

> Programmatic channel logo creation with PIL for YouTube video watermarks.
> YouTube requires 150×150 watermarks uploadable under Channel → Branding → Video watermark.

## Pattern: Tech-Style Small Logo with PIL

```python
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import math

S = 150
CX, CY = S//2, S//2

def create_logo(monogram="QT"):
    im = Image.new('RGBA', (S, S), (0,0,0,0))
    d = ImageDraw.Draw(im)
    
    # 1. Background — dark rounded rect
    d.rounded_rectangle([0,0,S-1,S-1], radius=16, fill=(10, 14, 23, 255))
    
    # 2. Grid dot pattern
    for x in range(10, S, 20):
        for y in range(10, S, 20):
            d.ellipse([x-1, y-1, x+1, y+1], fill=(20, 28, 45, 180))
    
    # 3. Hexagonal circuit lines
    for r, aoff in [(38, 0), (28, 15)]:
        pts = [(CX + r*math.cos(math.radians(60*i + aoff)),
                CY + r*math.sin(math.radians(60*i + aoff))) for i in range(6)]
        for i in range(6):
            d.line([pts[i], pts[(i+1)%6]], fill=(20, 28, 45, 200), width=1)
    
    # 4. Diagonal tech lines
    for i in range(-S, S*2, 15):
        d.line([(i, 0), (i-S, S)], fill=(0, 180, 255, 40), width=1)
        d.line([(0, i), (S, i-S)], fill=(88, 120, 255, 40), width=1)
    
    # 5. Glow behind text (radial falloff)
    for r in range(20, 0, -1):
        a = int(15 * (1 - r/20))
        d.ellipse([CX-26, CY-26, CX+26, CY+26], fill=(0, 200, 255, a))
    
    # 6. Outer rings
    d.ellipse([CX-32, CY-32, CX+32, CY+32], outline=(0, 180, 255, 100), width=2)
    d.ellipse([CX-28, CY-28, CX+28, CY+28], outline=(88, 120, 255, 60), width=1)
    
    # 7. Monogram text with glow
    fnt = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 52)
    bb = d.textbbox((0,0), monogram, font=fnt)
    tw, th = bb[2]-bb[0], bb[3]-bb[1]
    tx, ty = CX - tw//2, CY - th//2 - 2
    
    # Glow passes (GaussianBlur)
    for dx, dy, sz in [(-1,0,1),(1,0,1),(0,-1,1),(0,1,1),(-2,-2,3),(2,2,3)]:
        glow = Image.new('RGBA', (S,S), (0,0,0,0))
        gd = ImageDraw.Draw(glow)
        lc = (0, 180, 255, 30 if sz==3 else 60)
        gd.text((tx+dx, ty+dy), monogram, font=fnt, fill=lc)
        glow = glow.filter(ImageFilter.GaussianBlur(sz))
        im = Image.alpha_composite(im, glow)
        d = ImageDraw.Draw(im)
    
    # Main text in white
    d.text((tx, ty), monogram, font=fnt, fill=(230, 245, 255, 255))
    
    # 8. Corner accent dots
    for dx, dy in [(1,1), (-1,1), (1,-1), (-1,-1)]:
        px, py = CX + dx*42, CY + dy*42
        d.ellipse([px-2, py-2, px+2, py+2], fill=(0, 180, 255, 200))
    
    # 9. Bottom tech line
    d.rectangle([CX-25, CY+20, CX+25, CY+21], fill=(0, 180, 255, 120))
    
    return im
```

## Design Elements Reference

| Element | Purpose | Alpha | Size |
|---------|---------|-------|------|
| Dark rounded bg | Base canvas, tech feel | 255 | 150×150, r=16 |
| Dot grid | Tech texture, subtle | 180 | spacing 20px |
| Hex lines | Circuit-board aesthetic | 200 | r=38, r=28 |
| Diagonal lines | Sci-fi depth | 40 | spacing 15px |
| Text glow | Neon effect (GaussianBlur) | 30-60 | blur r=1, r=3 |
| Outer rings | Framing, focus | 60-100 | r=28, r=32 |
| White monogram | High contrast center | 255 | DejaVu Sans Bold 52px |
| Corner dots | Finishing detail | 200 | r=2 |
| Bottom line | Anchor line | 120 | 50px wide |

## Key Constraints

- **150×150 exact** — YouTube rejects other sizes for watermark upload
- **RGBA mode** — transparency blends with video content
- **16px rounded corners** — avoids harsh edges on dark video backgrounds
- **Keep center clear** — YouTube's default watermark placement is bottom-right; avoid critical content near edges
- **Font size 48-56pt** for 2-3 char monograms at 150px — bigger fills the square, smaller disappears on mobile
- **CJK font fallback**: use `/usr/share/fonts/truetype/arphic/ukai.ttc` for Chinese channel names — same technique, different font path

## Usage

```python
logo = create_logo("QT")
logo.save("yt-watermark.png")
```

## See Also

- `scripts/promo-video-moviepy.sh` for full 640×360 promo video creation
- `references/asset-creation-pillow.md` for larger promotional assets (banners, social cards)
