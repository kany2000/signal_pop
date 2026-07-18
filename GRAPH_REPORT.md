# Graph Report - /tmp/graphify-test  (2026-07-09)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 61 nodes · 65 edges · 14 communities (12 shown, 2 thin omitted)
- Extraction: 100% EXTRACTED · 0% INFERRED · 0% AMBIGUOUS
- Token cost: 480 input · 671 output

## Community Hubs (Navigation)
- Cover Image Generation
- Prompt File Processing
- Video Timeline Composition
- SRT Parsing and HTML
- LoremFlickr Image Downloader
- Unsplash Image Downloader
- SRT Ticker Generation
- Local Cover Generation
- Daily Video Rendering

## God Nodes (most connected - your core abstractions)
1. `make_cover()` - 6 edges
2. `main()` - 4 edges
3. `create_text_bg()` - 4 edges
4. `build_bg()` - 4 edges
5. `find_prompts_file()` - 3 edges
6. `short_prompt()` - 3 edges
7. `build_anchor_masked()` - 3 edges
8. `make_cover()` - 3 edges
9. `download_loremflickr()` - 3 edges
10. `gen_unique()` - 3 edges

## Surprising Connections (you probably didn't know these)
- None detected - all connections are within the same source files.

## Import Cycles
- None detected.

## Communities (14 total, 2 thin omitted)

### Community 0 - "Cover Image Generation"
Cohesion: 0.33
Nodes (9): build_anchor_masked(), build_bg(), corner_brackets(), get_anchor(), lerp(), make_cover(), neon_text(), 右侧叠加年轻女性形象（亮背景适配版：脸部清晰，仅最边缘羽化） (+1 more)

### Community 1 - "Prompt File Processing"
Cohesion: 0.43
Nodes (6): download_with_retry(), find_prompts_file(), main(), 根据输入找到 visual_prompts 文件, 从 prompt 或 title 缩略出适合 API 的文本, short_prompt()

### Community 2 - "Video Timeline Composition"
Cohesion: 0.38
Nodes (6): build_timeline_from_script(), create_text_bg(), find_chinese_font(), main(), 用 ffmpeg drawtext 生成文字背景图（占位用，无图时 fallback）, 从播报脚本和 visual_prompts 自动构建时间线（估算时长）

### Community 4 - "LoremFlickr Image Downloader"
Cohesion: 0.50
Nodes (4): download_loremflickr(), gen_unique(), Fetch from loremflickr with redirect handling, Get unique image >= 100KB

### Community 5 - "Unsplash Image Downloader"
Cohesion: 0.50
Nodes (4): download_unsplash(), gen_unique(), Fetch from Unsplash Source API with redirect handling, Get unique image >= 100KB

### Community 7 - "Local Cover Generation"
Cohesion: 0.83
Nodes (3): build_bg(), make_cover(), neon_text()

### Community 8 - "Daily Video Rendering"
Cohesion: 0.83
Nodes (3): main(), parse_script(), wrap_text()

## Knowledge Gaps
- **2 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What connects `根据输入找到 visual_prompts 文件`, `从 prompt 或 title 缩略出适合 API 的文本`, `用 ffmpeg drawtext 生成文字背景图（占位用，无图时 fallback）` to the rest of the system?**
  _11 weakly-connected nodes found - possible documentation gaps or missing edges._