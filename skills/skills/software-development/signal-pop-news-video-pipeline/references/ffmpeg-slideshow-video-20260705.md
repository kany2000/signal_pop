# FFmpeg News Video Assembly (Signal Pop v4 — 2026-07-05)

## Overview

v4: TTS audio (actual per-segment durations) + 10 custom images + separate opening/ending studio bg
→ MP4 at 275.5s, 10.4MB, 1920×1080, H.264.

**Single-pass ffconcat** — no intermediate segment encoding.

## Architecture

```
12 frames (opening_bg.jpg + 01..10.jpg + opening_bg.jpg) + durations.json
    → ffconcat (images with actual-TTS-duration directives)
    → ffmpeg single encode: concat + audio overlay
    → video_YYYYMMDD.mp4
```

### ffconcat file format

```txt
ffconcat version 1.0
file '/tmp/frames/001_opening.png'
duration 7.84
file '/tmp/frames/002_news_01.png'
duration 29.28
file '/tmp/frames/003_news_02.png'
duration 26.40
...
file '/tmp/frames/012_ending.png'
duration 3.00
```

### Single ffmpeg command

```bash
ffmpeg -y -f concat -safe 0 -i concat.txt \
  -i audio.wav \
  -c:v libx264 -preset veryfast -crf 24 -pix_fmt yuv420p -r 30 \
  -c:a aac -b:a 192k \
  -shortest -movflags +faststart output.mp4
```

**Key details:**
- `-preset veryfast` (not ultrafast) — better quality/size
- `-crf 24` — good for 1080p spoken content
- Image framerate = 30, but concat shows each image for its `duration` seconds

### Timing (v4 real-TTS approach)

**Do NOT estimate durations from character count.** Actual WAV durations:

```python
durations = json.load(open('/home/kan/signal_pop/output/daily/durations.json'))
# Example: [7.84, 29.28, 26.40, 25.28, 27.04, 26.40, 26.88, 24.16, 27.84, 23.84, 30.56]
# 12 frames = opening (dur[0]) + 10 news (dur[1:10]) + ending (dur[10]-3.0)
# Last TTS segment is 30.56s, ending card takes 3.0s → ending frame = 3.0s
```

**Verification**: `ffprobe` shows video ≈ audio (within 0.5s).

---

## Frame Layout (v4)

Each frame is 1920×1080 PIL composite. Uses **RGBA overlay** for transparency — never draw semi-transparent shapes on RGB images (see Alpha Gradient Bug in SKILL.md).

### Opening Card

- Background: `opening_bg.jpg` (separate studio image, prompt "新闻播报直播间")
- RGBA dark overlay (α=160) over whole image
- Gold horizontal rules (top/bottom decoration)
- "隔天信号弹" in bold gold, 72px
- "每日新闻播报" subtitle, white 32px
- Date line: "2026年07月05日 · 星期日 · 10条新闻", gray 28px

### News Slide

Layout: **Full-screen image background + Left gradient + Text overlay**

```
┌─────────────────────────────────────────────────┐
│[国内民生]  #01          ← tag badge (blue pill) │
│                                          ← page │
│  全国多地进入三伏天，                                │
│  气象台发布高温预警及                                  │
│  防暑降温提醒。                                      │
│                                                    │
│  据新华网报道，随着夏季气温                            │
│  攀升，全国大部分地区                                  │
│  已正式进入三伏天。气象                                │
│  部门提醒广大市民...                                  │
│                                                    │
│  隔天信号弹 · 2026.07.05              1/10          │
│                                                    │
│  ← LEFT GRADIENT overlay (α=255→0 over 960px)      │
└─────────────────────────────────────────────────┘
```

**Elements:**
1. Background: news image full-bleed (1920×1080)
2. Left gradient: RGBA overlay, 255→0 alpha over 960px, then 60→0 over 960-1920
3. Category tag: blue pill `[国内民生]` at (60, 130), font 22px bold
4. Page number: `#01` next to tag, gray 20px, AND `1/10` at bottom-right
5. Title: bold white (240,240,250), 46px, left-aligned at y=200, wrapped 2-3 lines
6. Body text: grey-white (240,240,250), 24px, 3-4 lines on left gradient mask
7. **9-direction text shadow** for readability — text rendered 9 times at offsets (±1,±2) in dark grey before main white text
8. Emoji → geometric replacements (no PIL emoji support):
   - 📡 → gold circle (outer ring 22px + filled dot 6px)
   - ✅ → filled green circle
9. Footer: left `隔天信号弹 · YYYY.MM.DD`, right `N/10`, 22px gray

### Ending Card

- Same background as opening (`opening_bg.jpg`)
- RGBA dark overlay (α=180)
- Gold horizontal rules
- "隔天信号弹" in bold gold, 64px
- "明天见" subtitle, white 36px
- Date line, gray 28px

---

## Font Paths

```python
FONT      = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
FONT_BOLD = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
```

---

## Image Sources

| Source | Endpoint | Notes |
|--------|----------|-------|
| Pollinations | `image.pollinations.ai/prompt/{q}?width=1024&height=576&seed=N&model=flux&nofeed=true` | ⚠️ Unstable, poor faces. Use `&nofeed=true`. |
| Mixkit frames | `assets.mixkit.co/videos/{id}/{id}-720.mp4` | ✅ Real photos — extract keyframe with ffmpeg |

Opening background prompt: `"新闻播报直播间, 绿幕演播室, 摄像机, 灯光设备, 专业新闻电视台, 4k, 超清, 电影质感, 实景拍摄"` — **must not be same as any news image**.

---

## Verification Checklist

- [ ] Opening card has background image (not solid color)
- [ ] Opening/ending bg is different from all news images
- [ ] All 10 news slides have text (category + title + body)
- [ ] Page numbers on each slide
- [ ] Body text readable on bright backgrounds (gradient + shadow working)
- [ ] Duration matches audio (ffprobe: video ≈ audio, within 0.5s)
- [ ] No □ tofu boxes (correct Noto Sans CJK font)
- [ ] No emoji → □ (all emoji replaced with geometric shapes)
- [ ] No black rectangles or image fracturing (α bug avoided)
- [ ] No visible face distortion in images
- [ ] Copy to her2home succeeded + metadata JSON valid
- [ ] Cron one-shot scheduled (not recurring)
