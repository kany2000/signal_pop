# Pipeline Selection Guide

## Quick Decision Tree

```
User Request Type
├── "Make an explainer about [topic]" → animated-explainer
├── "Animate this concept visually" → animation
├── "Cinematic trailer/mood piece" → cinematic (if have footage) OR animation (if pure generation)
├── "Montage from real footage" → documentary-montage
├── "Mix my footage + generated support" → hybrid
├── "Avatar presenter speaking" → avatar-spokesperson
├── "Screen recording demo" → screen-demo
├── "Clip long video into shorts" → clip-factory
├── "Podcast highlights" → podcast-repurpose
└── "Dub/translate video" → localization-dub
```

## Detailed Matching

### animation (production stability)
**Use when:** Pure generation, motion graphics, kinetic typography, illustrative sequences, math visuals.
**Key features:** Research-first, animation mode selection (Manim/Remotion/AI video), playbook system, sample protocol.
**Renderer:** Remotion (data viz, text cards) or HyperFrames (kinetic type, HTML/GSAP).
**Our setup:** Google Imagen + Remotion viable; Manim not installed; AI video 0/16.

### cinematic (production stability)
**Use when:** Have source footage/stills, need mood-led edit, trailer, brand film.
**Key features:** Source-media-aware, emotional arc design, color consistency, audio dynamics.
**Renderer:** Remotion (CinematicRenderer for video-led) or HyperFrames (kinetic titles).
**Our setup:** Works if user provides footage; pure generation → use animation instead.

### documentary-montage (beta)
**Use when:** Thematic montage from stock/archive footage (Prelinger, NASA, Wikimedia).
**Key features:** CLIP retrieval (needs torch), fast path (direct_clip_search), music sync, uniform grade.
**Renderer:** Remotion ONLY (end-tag overlay stack depends on CinematicRenderer).
**Our setup:** Fast path works (no torch); standard path blocked (torch install fails).

### animated-explainer (production)
**Use when:** Topic → fully generated explainer with narration.
**Key features:** Research → script → scenes → assets → compose.
**Renderer:** Remotion (text_card, stat_card, comparison, charts).
**Our setup:** Viable with Google Imagen + Google TTS + Remotion.

### hybrid (production)
**Use when:** Source footage primary, generated support visuals for gaps.
**Key features:** Source-first, generated inserts limited and justified.
**Renderer:** Remotion or HyperFrames.
**Our setup:** Viable if user provides footage.

## Stability Notes
- **production**: Fully audited, reliable
- **beta**: Works but expect rough edges -- mention to user
- **test**: Smoke test only

## Anti-Patterns
- Using `cinematic` for pure generation (no source footage) → use `animation`
- Using `documentary-montage` for single-scene cinematic → use `animation`
- Using `animated-explainer` for mood piece without narration → use `animation`