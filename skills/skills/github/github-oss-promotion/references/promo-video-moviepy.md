# Programmatic Promo Video (640×360) with MoviePy + PIL

> Full scene-by-scene animated promo video created entirely with Python — no video editor needed.
> Output: MP4 H.264, 640×360, 24fps, ~26s.
> Dependencies: `pip install pillow moviepy numpy`

## Architecture

Each scene is a function returning a list of numpy arrays (frames). Scenes are concatenated and fed to `ImageSequenceClip`.

```python
from moviepy import ImageSequenceClip
import numpy as np

all_frames = scene0() + scene1() + scene2()  # each returns list[np.array]
clip = ImageSequenceClip(all_frames, fps=24)
clip.write_videofile("promo.mp4", codec='libx264', fps=24, preset='fast')
```

## Scene Templates

| Scene | Duration | Content |
|-------|----------|---------|
| Title | 3s (72fr) | Logo animates in, tagline fades, star badge appears |
| Feature 1 | 5s (120fr) | Browser simulator + text highlight + translation popup |
| Feature 2 | 5s (120fr) | Alt+1 screenshot OCR sequence |
| Feature 3 | 5s (120fr) | Hover translate (Alt key) + floating panel |
| Feature Grid | 4.5s (108fr) | 4×2 grid of feature icons animating in |
| CTA | 4s (96fr) | Stars background, install button, GitHub star badge |

## Dark Theme Color Palette

```python
bg=(13,17,23)    card=(22,27,34)    border=(48,54,61)
primary=(88,166,255)    green=(63,185,80)
orange=(210,153,34)     pink=(247,120,186)
text=(230,237,243)      text2=(139,148,158)
```

## Browser Widget Pattern

```python
def browser(d, bx, by, bw, bh, url="..."):
    # Window frame with OS buttons (red/yellow/green circles)
    # URL bar with domain
    d.rectangle([bx, by, bx+bw, by+bh], fill=card, outline=border)
    d.rectangle([bx+1, by+1, bx+bw-1, by+24], fill=card)
    for i, c in enumerate([(255,95,86),(255,189,46),(39,201,63)]):
        d.ellipse([bx+8+i*14, by+6, bx+14+i*14, by+12], fill=c)
    d.rectangle([bx+55, by+4, bx+bw-12, by+20], fill=bg, outline=border)
    d.text((bx+60, by+6), url, font=f_sm, fill=text2)
```

## Translation Popup Widget

```python
def popup(d, x, y, src_text, tr_text, accent_color):
    # Card with colored header bar
    d.rounded_rectangle([x, y, x+200, y+52], radius=6, fill=card, outline=accent, width=1)
    d.rectangle([x+1, y+1, x+199, y+18], fill=accent)
    d.text((x+8, y+3), "QuickTranslate", font=f_sm, fill='white')
    d.text((x+8, y+22), src_text, font=f_sm, fill=text)
    d.text((x+8, y+38), f"→ {tr_text}", font=f_sm_cn, fill=accent)
```

## Animation Techniques

- **Fade in**: `a = int(min(t * factor, 1) * 255)` — multiply by 255 for alpha channel
- **Line grow**: `width = int(max_width * min(t*2, 1))` — animates from center
- **Slide up**: `y_offset = int(40 * (1 - progress))` — objects move into position
- **Staggered grid**: `cp = min(max((t - 0.04*idx) / 0.15, 0), 1)` — items appear one by one
- **Cursor**: Draw a white polygon shaped like an arrow cursor, animate its (x,y)
- **Stars background**: `sin(θ + t*3)` for position + `sin(φ + t*2)` for drift — constant gentle motion

## Known Pitfalls

- **Font auto-detection**: Detect CJK characters via Unicode range before choosing font — mixed content needs `f_sm` for ASCII, `f_sm_cn` for CJK in the same scene
- **RGBA→RGB conversion**: MoviePy requires numpy arrays; ensure `Image.new('RGB', ...)` not RGBA for `write_videofile`
- **Frame count**: 24fps × desired seconds = frames per scene. Round to whole number. 72fr = 3s, 120fr = 5s, 96fr = 4s.
- **Text glow at 640-wide**: GaussianBlur at this resolution looks pixelated — use multi-pass semi-transparent text offsets instead of blur for sharper results at small sizes
- **Scene transitions**: Hard cuts only (this script). For fades, pre-render scenes then crossfade using MoviePy `CompositeVideoClip` with opacity

## Quick Reference: Font Setup for 640×360

```python
FONT_CJK = '/usr/share/fonts/truetype/arphic/ukai.ttc'
FONT_EN  = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
f_big = ImageFont.truetype(FONT_EN, 40)      # Title
f_sub = ImageFont.truetype(FONT_CJK, 22)     # Subtitle / CJK heading
f_mid = ImageFont.truetype(FONT_EN, 18)      # Body English
f_sm  = ImageFont.truetype(FONT_EN_REG, 12)  # Small English
f_sm_cn = ImageFont.truetype(FONT_CJK, 12)   # Small CJK
```

## Full Script Location

The complete runnable script for QuickTranslate's promo video lives at:
`/home/kan/QuickTranslate-assets/make_video.py`

Adapt scenes, colors, and text for your project's features.
