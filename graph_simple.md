# Project Knowledge Graph — Overview

**61 nodes · 65 edges · 14 communities**

## God Nodes (most connected — core abstractions)
- `gen_cover.py` — 7 edges
- `make_cover()` — 6 edges
- `batch_gen_images.py` — 4 edges
- `main()` — 4 edges
- `composite_video.py` — 4 edges
- `create_text_bg()` — 4 edges
- `build_bg()` — 4 edges
- `add_ticker.py` — 3 edges
- `find_prompts_file()` — 3 edges
- `short_prompt()` — 3 edges

## Communities
- **C0** (10): gen_cover.py, lerp(), build_bg(), neon_text(), corner_brackets(), get_anchor(), build_anchor_masked(), make_cover() … (+2)
- **C1** (7): batch_gen_images.py, find_prompts_file(), short_prompt(), download_with_retry(), main(), 根据输入找到 visual_prompts 文件, 从 prompt 或 title 缩略出适合 API 的文本
- **C2** (7): composite_video.py, create_text_bg(), find_chinese_font(), build_timeline_from_script(), main(), 用 ffmpeg drawtext 生成文字背景图（占位用，无图时 fallback）, 从播报脚本和 visual_prompts 自动构建时间线（估算时长）
- **C3** (5): gen_hyperframes_html.py, parse_srt(), find_news_time_ranges(), esc(), Escape special chars for JS
- **C4** (5): gen_scene_images_lorem.py, download_loremflickr(), gen_unique(), Fetch from loremflickr with redirect handling, Get unique image >= 100KB
- **C5** (5): gen_scene_images_unsplash.py, download_unsplash(), gen_unique(), Fetch from Unsplash Source API with redirect handling, Get unique image >= 100KB
- **C6** (4): add_ticker.py, build_srt(), build_srt_proper(), main()
- **C7** (4): gen_cover_local.py, neon_text(), build_bg(), make_cover()
- **C8** (4): render_daily_video.py, main(), parse_script(), wrap_text()
- **C9** (2): gen_missing_images.py, gen()
- **C10** (2): gen_scene_images.py, gen_image()
- **C11** (2): gen_scene_images_v2.py, gen()
- **C12** (2): gen_scene_images_v3.py, gen()
- **C13** (2): gen_timeline.py, main()

## Full interactive view
Open `graph.html` in a browser for the clickable force-directed graph.
