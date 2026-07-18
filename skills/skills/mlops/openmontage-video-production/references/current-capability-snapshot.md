# Current Capability Snapshot (Session: 2026-07-01)

*Run `python -c "from tools.tool_registry import registry; import json; registry.discover(); print(json.dumps(registry.provider_menu_summary(), indent=2))"` to refresh.*

## Composition Runtimes
- FFmpeg: ✅
- Remotion: ✅
- HyperFrames: ✅

## Capabilities Summary

| Capability | Configured/Total | Available Providers | Unavailable (need setup) |
|---|---|---|---|
| analysis | 9/11 | ffmpeg, ffprobe, local, multi, whisperx, youtube-transcript-api | mediapipe, transformers |
| audio_generation | 0/1 | — | piper |
| audio_processing | 2/2 | ffmpeg | — |
| avatar | 0/2 | — | sadtalker, wav2lip |
| character_animation | 6/6 | openmontage | — |
| clip_acquisition | 1/1 | openmontage | — |
| clip_retrieval | 0/1 | — | openmontage |
| corpus_population | 0/1 | — | openmontage |
| enhancement | 2/6 | ffmpeg | codeformer, mediapipe, realesrgan, rembg |
| graphics | 2/3 | mermaid, pygments | manim |
| image_generation | 1/9 | google_imagen | flux, grok, local_diffusion, multi, openai, pexels, pixabay, recraft |
| music_generation | 0/2 | — | elevenlabs, suno |
| music_search | 1/2 | pixabay_music | freesound |
| screen_capture | 2/2 | cap, ffmpeg | — |
| source_ingest | 1/1 | yt-dlp | — |
| subtitle | 2/2 | openmontage, remotion | — |
| tts | 1/4 | google_tts | doubao, elevenlabs, openai |
| video_generation | 0/16 | — | cogvideo, grok, heygen, higgsfield, hunyuan, kling, ltx, ltx-modal, minimax, pexels, pixabay, runway, seedance, veo, wan |
| video_post | 9/9 | ffmpeg, hyperframes | — |

## Quick Setup Offers (1-minute env var fixes)

| Capability | Provider | Env Var | Where to Get |
|---|---|---|---|
| image_generation | flux | FAL_KEY | https://fal.ai/dashboard/keys |
| image_generation | grok | XAI_API_KEY | xAI developer console |
| image_generation | openai (DALL-E 3) | OPENAI_API_KEY | https://platform.openai.com/ |
| image_generation | pexels | PEXELS_API_KEY | https://www.pexels.com/api/ (free) |
| image_generation | pixabay | PIXABAY_API_KEY | https://pixabay.com/api/docs/ (free) |
| image_generation | recraft | FAL_KEY | https://fal.ai/dashboard/keys |
| video_generation | kling | FAL_KEY | https://fal.ai/dashboard/keys |
| video_generation | minimax | FAL_KEY | https://fal.ai/dashboard/keys |
| video_generation | runway | RUNWAY_API_KEY | https://dev.runwayml.com/ |
| video_generation | veo | FAL_KEY | https://fal.ai/dashboard/keys |
| video_generation | pexels | PEXELS_API_KEY | https://www.pexels.com/api/ (free) |
| video_generation | pixabay | PIXABAY_API_KEY | https://pixabay.com/api/docs/ (free) |
| tts | elevenlabs | ELEVENLABS_API_KEY | https://elevenlabs.io |
| tts | openai | OPENAI_API_KEY | https://platform.openai.com/ |
| music_generation | elevenlabs | ELEVENLABS_API_KEY | https://elevenlabs.io |
| music_generation | suno | SUNO_API_KEY | https://sunoapi.org/api-key |
| music_search | freesound | FREESOUND_API_KEY | https://freesound.org/apiv2/apply/ (free) |

## Viable Production Paths (No New Keys)

### Path A: Image-Based Animation (Remotion) ✅ RECOMMENDED
- **Tools**: google_imagen + video_compose (remotion) + audio_mixer
- **Cost**: ~$0.05/image × 12-18 images = $0.60-0.90
- **Best for**: Cinematic mood pieces, anime-style, 2.5D parallax + shaders
- **Proven**: Yes (previous session test)

### Path B: Stock Footage Montage (documentary-montage fast path) ✅
- **Tools**: direct_clip_search (archive_org, wikimedia, nasa, mixkit, dareful) + video_compose (ffmpeg/remotion)
- **Cost**: Free (no API keys)
- **Best for**: Thematic montages, Adam Curtis style
- **Proven**: Yes (signal_pop_test output_test.mp4)

### Path C: Diagram + Ken Burns (Remotion/FFmpeg) ✅
- **Tools**: diagram_gen (mermaid) + image_selector (google_imagen) + video_compose
- **Cost**: ~$0.05/image for backgrounds only
- **Best for**: Technical explainers, architecture diagrams

### Path D: Pure Remotion Data Viz ✅
- **Tools**: video_compose (remotion) only -- built-in stat_card, kpi_grid, charts
- **Cost**: Free
- **Best for**: Data-driven videos, no AI generation needed

## Blocked Paths (Require Keys)

- AI video clip generation (0/16 providers)
- High-quality TTS (ElevenLabs, OpenAI)
- Custom music generation (Suno, ElevenLabs)
- FLUX/Grok/DALL-E image generation
- Avatar/lip-sync (SadTalker, Wav2Lip need GPU + PyTorch)
- Enhancement (RealESRGAN, CodeFormer, rembg need GPU)

## Music Library
Check `/home/kan/shared/OpenMontage/music_library/` for local tracks (gitignored).
Pixabay Music search available free via `pixabay_music` tool.