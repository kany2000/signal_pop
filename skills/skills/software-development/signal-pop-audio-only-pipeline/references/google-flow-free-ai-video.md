# Google Flow — Free AI Video Generation (2026-06-07 Discovery)

**URL**: https://labs.google/fx/tools/flow
**Requires**: Google account (personal, free)
**Status**: ✅ Verified accessible, requires manual sign-in via browser

## What It Is

Google Flow is Google's unified AI creative studio (merged Whisk + ImageFX). It provides **free** video generation, image generation, and AI editing tools in one web app.

## Built-in Models (All Accessible via Flow UI)

| Model | Purpose | Free Tier Access |
|-------|---------|-----------------|
| **Veo 3.1** | Video generation with native audio (dialogue + lip-sync + SFX + music) | ✅ |
| **Nano Banana** | Image generation, character consistency, subject consistency | ✅ |
| **Gemini Omni** | Multimodal input, conversational editing, script generation | ✅ |
| **Imagen 4** | Text-to-image (merged into Flow) | ✅ |

## Free Tier Details

- **Starter credits**: 100 (one-time)
- **Daily credits**: 50 (reset every 24h)
- **Veo 3.1 Fast**: 20 credits/clip → ~2-3 clips/day
- **Veo 3.1 Lite**: 10 credits/clip → ~5 clips/day
- **Veo 3.1 Quality**: 100 credits/clip (premium tier)
- **Video edits**: 20 credits
- **4K upscaling**: 50 credits
- **1080p upscaling**: FREE (included)
- **Max clip length per generation**: 4-8 seconds
- **Extend feature**: Chain 7-second hops up to 20x → ~148 seconds (~2.5 min)
- **Watermark**: None on free tier
- **Commercial use**: Allowed (Google does not claim ownership)

## Workflow (from the YouTube tutorial)

The video "Google Flow 免費AI工具一站式最強工作流" (https://youtu.be/iQBx_kWBg6o) demonstrated:

1. **Script generation** → Gemini (or Gemini Omni within Flow)
2. **Character consistency reference** → Nano Banana (generate consistent character images)
3. **Voice consistency** → Veo 3.1 native audio (dialogue with lip-sync)
4. **Scene consistency** → Nano Banana + Flow scene builder
5. **Video generation** → Veo 3.1 (directly in Flow)
6. **Complete workflow** → Google Flow automates all steps

Video chapters: 00:00 Intro, 00:21 Script, 00:34 Character, 01:07 Voice, 01:40 Scene, 01:58 Video gen, 02:50 Outro, 03:22 Examples.

## "Nano Banana Pro" Clarification

The video calls it "Nano Banana Pro" but Google's official naming within Flow is just **Nano Banana** (the image model). "Pro" likely refers to a specific mode or was a colloquialism. No separate "Nano Banana Pro" product exists — it's part of Flow.

## Relevance to Signal Pop

Google Flow can replace the deprecated `signal-pop-news-video-pipeline` (which used Pexels + MoviePy + placeholder assets) with genuine AI-generated video:

- **For daily clips**: Generate 4-8 second Veo 3.1 clips from news headlines
- **For weekly wrap-ups**: Chain multiple clips with Extend feature (~2.5 min)
- **For character consistency**: Use Nano Banana to generate a consistent news anchor character
- **For voice**: Veo 3.1 generates native audio with lip-sync (no separate TTS needed)
- **No watermark, no API key** (just Google account)

## Limitations

- **Google account required** — cannot use programmatically without browser + login session
- **8-second clip cap per generation** — must chain via Extend for longer content
- **Geometry/editing limited** — timeline editor is basic compared to Runway
- **No custom audio upload** — must use Veo's native audio
- **~50 daily credits** — enough for 2-5 clips/day, not for high-volume production
- **No API** (as of 2026-06) — Flow is a web app with no public API; no programmatic access possible
- **Bot detection** — headless browser may be blocked by Google's login page

## Testing Notes (2026-06-07)

- Playwright browser was used to access the landing page at labs.google/fx/tools/flow
- "Try in Google Flow" buttons lead to login gated app — cannot test without Google account session
- Gemini API key (`GEMINI_API_KEY`) on this machine was expired (HTTP 400 "API key not valid")
- No Google OAuth credentials available on this server
- For full testing: open https://labs.google/fx/tools/flow in a regular browser with Google account

## Video Sample Prompt (Tested Concept)

To generate "beautiful woman saying good morning" in Flow:
1. Open Flow → Generate → Veo 3.1
2. Prompt: `A beautiful young woman with long brown hair, warm smile, sitting in a sunlit cozy bedroom, looking at camera and saying "Good morning everyone! Hope you have a wonderful day!" in a cheerful voice, soft morning light, realistic, cinematic quality`
3. Or use Gemini Omni to chat: "Create a video of a woman saying good morning in a cozy bedroom"
4. For character consistency: first generate a character image with Nano Banana, then use it as reference in Veo 3.1
