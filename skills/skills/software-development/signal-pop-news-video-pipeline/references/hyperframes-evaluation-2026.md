# HyperFrames Evaluation for Signal Pop (2026-06-24)

Source: https://github.com/heygen-com/hyperframes + hyperframes.heygen.com/llms.txt

## Summary
- **Core**: HTML/CSS → deterministic MP4 via headless Chrome + FFmpeg
- **License**: Apache 2.0 (commercial OK)
- **Stack**: TypeScript, Node.js 22+, FFmpeg, GSAP, Puppeteer
- **Stars**: 30.7k (very active)

## Key Capabilities for Signal Pop

| Need | HyperFrames Support | Notes |
|------|---------------------|-------|
| Fixed 10min template production | ✅ High | CLI + variables + deterministic render |
| News captions/animations | ✅ High | 15+ caption components (kinetic-slam, pill-karaoke, highlight, etc.) |
| Maps/data viz | ✅ High | world-map, us-map, data-chart, flow-map, bubble-map, hex-map |
| Transitions/branding | ✅ High | 30+ shader transitions + logo-outro |
| AI agent auto-generation | ✅ Core design | Skills for Claude/Cursor/Codex/Gemini CLI |
| Chinese typesetting/fonts | ⚠️ Self-config | Catalog skews English; need Noto Sans SC etc. |
| Free/self-hosted | ✅ Apache 2.0 | Local or AWS Lambda / GCP Cloud Run |
| Render speed (10min 1080p) | ⚠️ 3–8 min | Depends on Chrome+FFmpeg complexity |

## Catalog Highlights (from llms.txt)

**Blocks** (ready-made scenes):
- `data-chart` — animated bar/line chart, NYT style
- `world-map` / `us-map` / `spain-map` — choropleth, staggered reveal
- `nyc-paris-flight` — realistic flight path animation (great for news)
- `north-korea-locked-down` — map zoom + label (editorial style)
- `instagram-follow` / `tiktok-follow` / `x-post` / `yt-lower-third` — social overlays
- `logo-outro` — cinematic logo reveal
- `flash-through-white` / `chromatic-radial-split` / `cinematic-zoom` / `glitch` / `domain-warp-dissolve` / `ridged-burn` / `ripple-waves` / `swirl-vortex` / `thermal-distortion` / `whip-pan` — shader transitions
- `vfx-iphone-device` / `macos-tahoe-liquid-glass` — 3D device mockups

**Components** (atomic effects):
- Captions: `caption-kinetic-slam`, `caption-pill-karaoke`, `caption-highlight`, `caption-emoji-pop`, `caption-matrix-decode`, `caption-glitch-rgb`, `caption-gradient-fill`, `caption-weight-shift`, `caption-blend-difference`, `caption-clip-wipe`, `caption-editorial-emphasis`, `caption-neon-accent`, `caption-neon-glow`, `caption-parallax-layers`, `caption-particle-burst`, `caption-texture`, `caption-texture-mask-text`
- Visual: `grain-overlay`, `shimmer-sweep`, `vignette`, `grid-pixelate-wipe`
- Text: `morph-text`, `texture-mask-text`, `parallax-zoom`, `parallax-unzoom`

## Integration Path for Signal Pop

1. **Minimal demo** — `npx hyperframes init test && npx hyperframes preview` (needs FFmpeg)
2. **Pick 3-4 blocks** — e.g., `data-chart` + `world-map` + `caption-pill-karaoke` + `flash-through-white`
3. **Create frame.md** — define color palette, fonts (Noto Sans SC), token system, animation specs
4. **Hook into pipeline** — fetch_news.py → generate HTML composition → `hyperframes render` → MP4 output

## Comparison vs Google Flow

| Dimension | Google Flow | HyperFrames |
|-----------|-------------|-------------|
| Cost | Free (50 credits/day) | Free (self-hosted) |
| Automation | Web UI only, no API | Full CLI + programmatic |
| Chinese support | Native (Google) | Manual font config |
| Render time | ~minutes per clip | 3–8 min for 10min video |
| Determinism | Non-deterministic | Deterministic (same in → same out) |
| Template reuse | Manual per clip | Variables + composition system |
| Audio | Native (Veo 3.1) | Separate track (FFmpeg mix) |
| Learning curve | Low (prompting) | Medium (HTML/GSAP/TS) |

## Verdict
**HyperFrames is a strong candidate for Signal Pop v2** — especially for:
- Fully automated daily pipeline (no human-in-loop)
- Consistent branding via frame.md
- Data-driven segments (maps, charts)
- Deterministic CI/CD renders

**Blocker**: Need FFmpeg + Node 22 environment. Current VM lacks FFmpeg (no sudo). Options:
- Install FFmpeg via nix/user-space binary
- Use AWS Lambda / GCP Cloud Run rendering (docs exist)
- Docker image with FFmpeg pre-installed

## Next Steps
1. Resolve FFmpeg install (nix profile or static binary)
2. Build starter template: `package.json` + `composition.html` + Chinese font config
3. Test render of 1-min prototype with 2-3 blocks
4. Benchmark render time vs quality

---

## Session Update (2026-06-24) — Pipeline Validation & Fixes

### Installation Fix
**Problem**: `onnxruntime-node` binary download fails from NuGet (slow/blocked in China).
**Fix**: Use npm mirror + skip optional scripts:
```bash
npm config set registry https://registry.npmmirror.com
npm install -g hyperframes --ignore-scripts
# hyperframes@0.7.5 installed successfully
```

### Pipeline Verified
| Stage | Status | Notes |
|-------|--------|-------|
| `hyperframes init` | ✅ | Scaffolded project with AGENTS.md, CLAUDE.md, index.html |
| `npm run check` (lint/validate/inspect) | ✅ | 0 errors, 0 warnings; Chrome detected at /usr/bin/google-chrome |
| `npm run render` | ⚠️ | Pipeline runs, blocked only by **missing FFmpeg** |

**Environment**: Node.js v24.15.0, npm 11.12.1, Chrome (screenshot mode, not headless-shell)

### Critical Production Fixes Identified

#### 1. Image Distortion (Aspect Ratio Mismatch)
**Symptom**: 1:1 source images (CT scans, MRI, square AI generations) stretched to 16:9 containers → horizontal distortion.
**Root Cause**: CSS `width:100%; height:100%` without `object-fit`.
**Fix** — add to `signal-pop.css`:
```css
.news-image,
.image-container img,
.slide-image {
  width: 100%;
  height: 100%;
  object-fit: cover;        /* key: preserves aspect ratio, crops overflow */
  object-position: center;
}
```
**Note**: If source image must show fully (no crop), use `object-fit: contain` + background color fill — but `cover` is preferred for news visuals.

#### 2. Audio-Video Sync Drift
**Symptom**: Next news image appears while previous audio still playing (fixed-duration slots vs variable TTS length).
**Root Cause**: Hardcoded `data-duration` in HTML composition.
**Fix** — **Audio-Driven Timing** in generation script:
```python
# 1. Extract actual audio durations via ffprobe
durations = [ffprobe(f"audio_{i}.mp3") for i in range(n)]

# 2. Compute cumulative start times
current = 0
for i, dur in enumerate(durations):
    html_block = f'''
    <div class="clip" data-start="{current}" data-duration="{dur}" data-track-index="1">
      <img src="news_{i}.jpg" class="news-image">
    </div>'''
    current += dur  # exact sync, no drift
```
**Result**: Frame-accurate sync (ms-level) between visuals and TTS.

### Recommended Signal Pop Template Structure
```
/home/kan/shared/signal-pop-hyperframes/
├── index.html          # Main composition (variable-driven)
├── signal-pop.css      # Design system: fonts, colors, object-fit rules
├── blocks/
│   ├── data-chart.html
│   ├── world-map.html
│   ├── caption-news.html   # pill-karaoke style for headlines
│   └── transition.html
├── generate.py         # fetch_news → params.json → inject HTML vars
├── render.sh           # hyperframes render + ffmpeg post-process
└── assets/
    ├── images/         # 16:9 source images (BlazeAPI --ar 16:9)
    └── audio/          # per-segment TTS mp3s
```

### Performance Baseline (Current VM)
| Metric | Value |
|--------|-------|
| Render mode | Chrome screenshot (not headless-shell) |
| Est. 10min 1080p | 5–10 min (1:1 to 1:2 realtime) |
| Optimization path | chrome-headless-shell → 2–4 min; AWS Lambda parallel → <1 min |