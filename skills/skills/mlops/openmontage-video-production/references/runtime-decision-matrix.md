# Runtime Decision Matrix: Remotion vs HyperFrames vs FFmpeg

## Hard Rule (Governance)
When both Remotion and HyperFrames are available on the machine (check `video_compose.get_info()["render_engines"]`), you MUST:
1. Present both with brief-specific fit + tradeoff
2. Recommend one with rationale tied to brief's delivery_promise
3. Wait for explicit user approval
4. Log `render_runtime_selection` with BOTH in `options_considered`

## Decision Cheat Sheet

| Brief Characteristic | Lean Toward | Why |
|---|---|---|
| Data charts, stat cards, KPI grids, text_card heavy | **Remotion** | Built-in React component library |
| MathAnimate/Manim scenes in animatic | **Remotion** | Manim renders to video, composed in Remotion |
| Kinetic typography, product promo, launch reel | **HyperFrames** | HTML/CSS/GSAP native motion graphics |
| Website-to-video, UI-driven composition | **HyperFrames** | Registry blocks, DOM-driven |
| Word-level/karaoke caption burn required | **Remotion** | HyperFrames caption parity deferred |
| Simple concat, trim, subtitle burn | **FFmpeg** | No composition overhead |
| Custom GLSL shaders, particle systems | **HyperFrames** | Shader registry blocks, Three.js easier |
| Existing Remotion scene components (anime_scene, hero_title, terminal_scene) | **Remotion** | Reuse beats rewrite |
| CinematicRenderer end-tag overlay (documentary-montage) | **Remotion** | HyperFrames parity deferred |

## For This Project's Typical Requests

### Cinematic Mood Piece (rainy night, neon noir, etc.)
- **Remotion** ✅ RECOMMENDED
  - `anime_scene` component = built for this (2.5D parallax, particles, vignette)
  - Three.js post-processing for rain shaders, god rays
  - Proven in previous session
- **HyperFrames**
  - More shader flexibility via custom registry blocks
  - But: must build parallax/camera system from scratch
  - Tradeoff: flexibility vs. 2hr setup time

### Kinetic Typography / Title Sequence
- **HyperFrames** ✅ RECOMMENDED
  - GSAP + SplitText = industry standard for type animation
  - HTML/CSS = easier typographic control
- **Remotion**
  - Possible but more verbose for complex type choreography

### Data Visualization / Explainer
- **Remotion** ✅ RECOMMENDED
  - stat_card, kpi_grid, bar_chart, line_chart, pie_chart, progress_bar built-in
  - Spring animations, staggered reveals
- **HyperFrames**
  - Chart.js / D3 in registry blocks possible but more work

### Simple Source Footage Edit
- **FFmpeg** ✅ RECOMMENDED
  - Concatenate, trim, crossfade, subtitle burn
  - Zero overhead, fastest render

## Current Machine Status
```bash
python -c "
from tools.tool_registry import registry
registry.discover()
info = registry._tools['video_compose'].get_info()
print('Remotion:', info['render_engines']['remotion'])
print('HyperFrames:', info['render_engines']['hyperframes'])
print('FFmpeg:', info['render_engines']['ffmpeg'])
"
```
Output (last check): All three `true`.

## Logging Format
```json
{
  "category": "render_runtime_selection",
  "selected": "remotion",
  "options_considered": [
    {"runtime": "remotion", "fit": "...", "tradeoff": "...", "recommended": true},
    {"runtime": "hyperframes", "fit": "...", "tradeoff": "...", "recommended": false}
  ],
  "reason": "anime_scene + Three.js rain shader matches cinematic mood piece brief; HyperFrames would require custom parallax system"
}
```