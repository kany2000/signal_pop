---
name: openmontage-video-production
description: "Drive OpenMontage instruction-driven video production pipelines end-to-end: capability discovery, pipeline selection, stage-by-stage execution with checkpoints, final render."
category: mlops
tags: [openmontage, video-production, pipeline, remotion, hyperframes, animation]
version: "1.2"
---

# OpenMontage Video Production Workflow

## When to Use

Use this skill when the user wants to create videos using the **OpenMontage** instruction-driven video production system (located at `/home/kan/shared/OpenMontage/`). This covers the full pipeline: research, proposal, script, scene_plan, assets, edit, compose, publish.

OpenMontage is NOT a simple "generate video" tool -- it's a structured pipeline system where the AI agent reads pipeline manifests and stage director skills, then drives tools step by step with checkpoints and human approval gates.

## Prerequisites

- OpenMontage repo cloned at `/home/kan/shared/OpenMontage/`
- Python environment with dependencies installed (`pip install -r requirements.txt`)
- Node.js >= 22 for Remotion/HyperFrames
- FFmpeg installed
- At least one image generation provider configured (Google Imagen currently available)
- API keys in `.env` for any paid providers user wants to use

## Core Workflow

### 1. Project Setup
```bash
cd /home/kan/shared/OpenMontage
mkdir -p projects/<kebab-case-name>/artifacts
mkdir -p projects/<kebab-case-name>/assets/{images,video,audio,music}
mkdir -p projects/<kebab-case-name>/renders
```

### 0. MANDATORY: Output Verification (run BEFORE delivering any render)
**Never deliver a video without running the verification script.** User caught black-frame bug by file size alone — this step prevents that.

```bash
# After any Remotion/HyperFrames/FFmpeg render completes:
python scripts/verify-remotion-output.py <output_video_path>
# Exit code 0 = OK, 1 = all black, 2 = error
```

Verification checks:
- Duration > 0
- Sample 5 frames across timeline
- Mean pixel value > 1.0 on each sampled frame
- If ALL frames black -> FAIL (exit 1)
- If SOME frames black -> WARN (likely fade-in/out, OK if brief)

### 2. Capability Discovery (MANDATORY first step)
Always query the live tool registry -- never rely on memory:
```bash
python -c "
from tools.tool_registry import registry
import json
registry.discover()
print(json.dumps(registry.provider_menu_summary(), indent=2))
"
```
This returns the ground truth of what's configured vs. available.

### 3. Pipeline Selection
Match the request to a pipeline in `pipeline_defs/`:
| Pipeline | Best For | Stability |
|---|---|---|
| `animated-explainer` | Topic to fully generated explainer | production |
| `animation` | Motion graphics, kinetic typography, illustrative sequences | production |
| `cinematic` | Trailers, mood-led edits, brand films | production |
| `documentary-montage` | Thematic montage from stock footage (Adam Curtis style) | beta |
| `hybrid` | Source footage + support visuals | production |
| `avatar-spokesperson` | Presenter-led avatar/lip-sync | production |

**For "cinematic scene animation" requests -> use `animation` pipeline** (not `cinematic` which expects source footage).

### 4. Stage Execution (follow pipeline manifest)
For EACH stage in the pipeline manifest (`pipeline_defs/<pipeline>.yaml`):

1. **Read the stage director skill** at `skills/pipelines/<pipeline>/<stage>-director.md`
2. **Execute per the skill** -- using tools via the registry
3. **Write artifact** to `projects/<name>/artifacts/`
4. **Checkpoint** -- validate against schema, present to user if `human_approval_default: true`

Stage order: `research` -> `proposal` -> `script` -> `scene_plan` -> `assets` -> `edit` -> `compose` -> `publish`

### 5. Critical Governance Rules

**Present Both Composition Runtimes (HARD RULE)**
When both Remotion and HyperFrames are available (check `video_compose.get_info()["render_engines"]`), you MUST:
1. Present both with one-line fit + tradeoff for THIS brief
2. Recommend one with rationale tied to brief's delivery_promise
3. Wait for explicit user approval
4. Log `render_runtime_selection` decision with BOTH in `options_considered`

**No Silent Downgrades**
- If approved path blocked -> surface blocker, propose options, get approval
- Never swap Remotion->HyperFrames->FFmpeg without logged decision
- Never substitute still-led for motion-led without explicit opt-out

**Approval Gates**
Pipeline stages with `human_approval_default: true` MUST stop and present to user. Key gates:
- `proposal` -- concept selection, runtime lock, budget approval
- `script` -- narrative approval before asset spend
- `scene_plan` -- visual treatment approval
- `compose` -- final render review (sometimes)
- `publish` -- distribution approval

### 6. Tool Usage Pattern
```python
from tools.tool_registry import registry
from tools.video.video_compose import VideoCompose

registry.discover()
tool = VideoCompose()
result = tool.execute(params_dict)  # NOT .run()
# result.success, result.data, result.error
```

Use **selector tools** for multi-provider capabilities:
- `tts_selector` -> routes to available TTS providers
- `image_selector` -> routes to available image gen providers
- `video_selector` -> routes to available video gen providers

### 7. Cost Management
- Budget defined in pipeline manifest (`budget_default_usd`)
- Track via `tools/cost_tracker.py`
- `single_action_approval_usd: 0.50` in config.yaml -- ask before any paid call >$0.50
- Animation pipelines advantage: Manim, Remotion, diagram_gen are FREE
- Primary costs: TTS narration + AI images/video

## Current Environment State (as of last session)

| Capability | Configured/Total | Available Providers |
|---|---|---|
| Image Generation | 1/9 | Google Imagen |
| Video Generation | 0/16 | **None** (all need API keys) |
| Composition | 3/3 | FFmpeg, Remotion, HyperFrames |
| TTS | 1/4 | Google TTS |
| Music Search | 1/2 | Pixabay Music (free) |

**Viable approach for cinematic mood pieces:** Image-Based Animation (Google Imagen keyframes + Remotion 2.5D parallax + procedural shaders). ~$0.05/image.

## Common Pitfalls

1. **Skipping capability discovery** -> proposing unavailable tools
2. **Ignoring "Present Both Runtimes" rule** -> governance violation
3. **Proposing video generation when 0/16 configured** -> wastes user time
4. **Not reading stage director skill before executing** -> wrong artifact format
5. **Silent fallback from motion-led to still-led** -> critical reviewer finding
6. **Hardcoding provider names/costs** -> drift between releases; always read from registry
7. **Skipping approval gates** -> pipeline contract violation
8. **Remotion CLI output filename validation** -> must pass `--output` flag with .mp4/.mkv/.mov extension; positional output arg causes "h264 + aac requires mp4/mkv/mov" error
9. **Stock source availability drift (confirmed state 2026-07-02)**:
   - `archive_org` + `wikimedia`: most reliable free, no key needed
   - **Mixkit**: `MixkitSource.search()` works (scrapes site), BUT `download()` fails (can't parse detail page). **Workaround**: extract clip ID from search results, construct direct CDN URL: `https://assets.mixkit.co/videos/{id}/{id}-720.mp4` — works with curl/wget, no auth
   - **Coverr**: 401 even without API key flag — effectively broken without auth
   - **Pexels/Videvo/Pixabay**: need API keys (none configured in this env)
   - **YouTube**: blocked by bot detection even with valid cookies
   - Always read `tool.get_info()["source_provider_summary"]["available_source_names"]` at runtime
10. **HyperFrames npm package timeout** -> registry slow/offline; verify with `hyperframes_compose` operation='doctor' before locking render_runtime
11. **edit_decisions audio.music format** -> expects `asset_id` + ducking object; legacy top-level `music` object not used by compose path
12. **Free stock sources don't cover specific cinematic scenes** — "beautiful woman walking alone in rain night city" not in archive.org/wikimedia/coverr/mixkit; need AI video generation (CogVideo/Kling/Luma/Runway) for custom scenes
13. **Clip filename ≠ actual content — CRITICAL** → archive.org/wikimedia filenames are hashes or scrape artifacts, NOT content descriptions. `clips_woman_rain/` folder contained Christmas Rockettes show, hurricane flood, and street protest — nothing matching "woman in rain at night". **ALWAYS generate a thumbnail and pass to vision_analyze before including any clip in a scene plan.** The user will notice and correct you if content is wrong.
14. **Mixkit download workaround** → when `MixkitSource.search()` returns results but `download()` fails (page parse error), extract clip ID from source_id (e.g. `mixkit_young-woman-walking-under-a-cold-rain-46707` → ID `46707`) and construct direct URL: `https://assets.mixkit.co/videos/{id}/{id}-720.mp4` for 720p, or `{id}-1080.mp4` for 1080p. Verify with `curl -sI` first.
15. **Pre-render clip verification step missing** → Before composing a scene plan with N clips, generate a thumbnail of each clip (frame at 1s) and pass to vision_analyze to confirm content matches the intended scene description. User caught wrong-content bug in "city rain night woman" video because clips were assembled based on folder names alone.
16. **Mixkit CDN URLs are stable and fast** — download via: `curl -sL "https://assets.mixkit.co/videos/46707/46707-720.mp4" -o clip.mp4`. No auth, no rate limit observed. 720p files ~2-8MB. Use this for reliable B-roll acquisition when no stock API keys configured.
17. **Remotion CinematicRenderer all-black** — low-res source (400x220) gets covered by filter layers; pre-check source resolution ≥720p
18. **Rendering too slow** — Remotion ~4x realtime, FFmpeg compose ~6x realtime; 10min = 40-60min render
19. **Pre-transcode to unified format** → `-c copy` concat gives 10-20x speedup; transcode downloads to 1920x1080@30fps yuv420p libx264+aac first
20. **Remotion CLI requires `--props` flag** — without it, default `scenes: []` renders all black; always pass `--props=path/to/props.json`
21. **Remotion doesn't support `file://` protocol** — local assets must be in `public/` folder and referenced via relative paths (e.g., `clips_rain_h264/clip.mp4`), not absolute paths with `file://`
22. **WebM/VP8/VP9 crash Chromium in Remotion** — pre-transcode all sources to h264/yuv420p mp4: `ffmpeg -i in.webm -c:v libx264 -preset fast -crf 23 -pix_fmt yuv420p -movflags +faststart out.mp4`
23. **Always verify output before delivering** — check file size >1MB for 1080p, sample frames with `scripts/verify-remotion-output.py`; user caught black video by file size alone
24. **CinematicRenderer `fadeInFrames` causes black frames** — setting `fadeInFrames: N` in scene config renders first N frames black (at 30fps, 15 frames = 0.5s black); use `fadeInFrames: 0` for scene_01 to start with visible content, or verify first non-black frame timestamp
25. **Remotion background render fails silently without `--overwrite`** — in background mode (`background=true`), stdin isn't connected; Remotion's "File exists, overwrite? [y/N]" defaults to N and render exits 0 but writes nothing. ALWAYS pass `--overwrite` flag on re-runs.
26. **Remotion foreground timeout (~20min for 1245 frames)** — `concurrency=1` processes ~1 fps; a 41.5s/1245-frame render takes ~20 min, exceeding the 600s foreground timeout. Use `background=true` with `timeout=900` and `notify_on_complete=true`.
27. **Verify file existence AFTER background render completes** — background process exit code 0 + "Encoded N/N + X MB" does NOT guarantee the output file was written. Always stat the output path after the background completion notification.

## References

- `references/pipeline-selection-guide.md` -- detailed pipeline matching criteria
- `references/runtime-decision-matrix.md` -- Remotion vs HyperFrames vs FFmpeg decision framework
- `references/current-capability-snapshot.md` -- live registry snapshot template
- `references/openmontage-fastpath-test.md` -- **无 GPU/无 PyTorch 环境下 fast path 端到端实测记录** (direct_clip_search + video_compose + CinematicRenderer)
- `templates/project-structure.sh` -- project initialization script