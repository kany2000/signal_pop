# v3 Full‑Screen Layout Reference (2026-07-05)

Record of the corrections that led from v2 (inset image, no opening bg) to v3 (full‑bleed image bg, matches July 1 reference).

## Build Script

```bash
/home/kan/signal_pop/scripts/build_daily_video.py
```

Full implementation: PIL frames + ffconcat + ffmpeg. ~220 lines.

## ffconcat Format (Verified Working)

```ffconcat
ffconcat version 1.0
file '/tmp/frames_v3/opening.png'
duration 10.0
file '/tmp/frames_v3/news_01.png'
duration 26.6
...
file '/tmp/frames_v3/ending.png'
duration 8.0
```

Run with:
```bash
ffmpeg -y -f concat -safe 0 -i concat.txt -i audio.wav \
  -c:v libx264 -preset veryfast -crf 24 -pix_fmt yuv420p -r 30 \
  -c:a aac -b:a 192k -shortest -movflags +faststart output.mp4
```

## Left Gradient Mask Implementation

```python
ov = Image.new('RGBA', (W, H), (0, 0, 0, 0))
d = ImageDraw.Draw(ov)
for x in range(0, 1300):
    alpha = int(200 * (1 - x/1300)) if x < 1300 else 0
    d.rectangle([(x, 0), (x+1, H)], fill=(0, 0, 0, max(0, min(255, alpha))))
# Bottom fade
for y in range(H-200, H):
    alpha = int(120 * (1 - (H - y)/200))
    d.rectangle([(0, y), (W, y)], fill=(0, 0, 0, max(0, min(255, alpha))))
img = Image.alpha_composite(img.convert('RGBA'), ov).convert('RGB')
```

## User Corrections Log

| # | User said | v2 had | v3 fix |
|---|-----------|--------|--------|
| 1 | "开场图片没有" | Solid dark bg | News #01 image as full‑bleed bg, darkened |
| 2 | "配图不能缩成小图" | Right inset 700×550 | Full‑screen image bg |
| 3 | "每条新闻没有配文字稿" | Body text missing (parser bug) | Split‑on‑blank‑lines parser |
| 4 | "文字也是乱码" | DejaVu Sans → □ | Noto Sans CJK |
| 5 | "脸部有变形" | Pollinations people faces | Regenerated #3, #5, #6, #8, #10 without people |
| 6 | "需要结尾图" | No ending | Added ending card matching opening |
| 7 | "文字乱码 | □ | emoji | PIL can't render emoji | Gold circle shapes instead |

## Verification Checklist

- [ ] Opening: background image visible, not solid color
- [ ] Opening: gold title, no □/emoji squares
- [ ] News 1-10: full‑bleed image bg, NOT inset/thumbnail
- [ ] News 1-10: category badge + title + body text visible
- [ ] News 1-10: page number N/10 matches
- [ ] Ending: consistent with opening
- [ ] Duration matches audio (±2s)
- [ ] No garbled Chinese text anywhere
- [ ] No visible face distortion in images
- [ ] `video_YYYYMMDD.mp4` copied to `her2home/`
- [ ] `cover_YYYYMMDD.png` updated
