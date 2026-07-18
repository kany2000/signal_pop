# OpenMontage Fast Path 端到端实测记录 (无 GPU / 无 PyTorch)

## 环境
- Ubuntu 24.04, CPU only, 无 PyTorch/ML 框架
- OpenMontage `/home/kan/shared/OpenMontage/` (commit ~2026-06)
- FFmpeg 7.x, Node.js 24, Remotion composer (node_modules 已装)
- HyperFrames: npm 包 `hyperframes` 解析超时 (registry 慢)

## 验证路径
```
direct_clip_search (archive_org + wikimedia)
    ↓ 免费素材直连，无需 API key
video_compose (operation="compose", render_runtime="ffmpeg")
    ↓ FFmpeg concat + 音轨混音 + ASS 字幕烧录 + 转码标准化
Remotion CinematicRenderer (可选)
    ↓ 文艺蒙太奇：冷色调分级 + 信号线纹理 + 弹簧动画标题 + 双音轨
```

## 关键工具调用模式

### 1. 素材搜索 (direct_clip_search)
```python
from tools.video.direct_clip_search import DirectClipSearch

tool = DirectClipSearch()
result = tool.execute({
    "output_dir": "projects/xyz/assets/video/raw",
    "queries": [{"query": "rain city night", "slot_id": "slot_01", "kind": "video"}],
    "sources": ["archive_org", "wikimedia"],  # 免费、免 key、可用
    "clips_per_query": 3,
    "filters": {"orientation": "landscape", "min_duration": 5, "max_duration": 30},
    "extract_thumbnails": True,
    "skip_existing": True
})
```
**可用源实测**: `archive_org` ✅, `wikimedia` ✅, `coverr` ❌(401), `mixkit` ❌(下载页解析失败), `pexels`/`pixabay_video` ❌(不可用)

### 2. FFmpeg 合成 (video_compose compose)
```python
from tools.video.video_compose import VideoCompose

tool = VideoCompose()
result = tool.execute({
    "operation": "compose",
    "edit_decisions": {
        "version": "1.0",
        "render_runtime": "ffmpeg",
        "cuts": [
            {"id": "c1", "source": "/abs/path/clip1.mp4", "in_seconds": 0, "out_seconds": 7, "layer": "primary", "transition_in": "fade", "transition_out": "fade", "transition_duration": 1.0},
            {"id": "c2", "source": "/abs/path/clip2.mp4", "in_seconds": 0, "out_seconds": 8, "layer": "primary", "transition_in": "fade", "transition_out": "fade", "transition_duration": 1.0},
        ],
        "audio": {"music": {"asset_id": "music_01", "volume": 0.25, "fade_in_seconds": 2, "fade_out_seconds": 3, "ducking": {"enabled": True}}},
        "subtitles": {"enabled": True, "style": "word-by-word", "source": "/abs/path/sub.ass"}
    },
    "output_path": "projects/xyz/renders/final.mp4",
    "audio_path": "/abs/path/music.mp3",
    "subtitle_path": "/abs/path/sub.ass",
    "codec": "libx264", "crf": 23, "preset": "medium"
})
```
**注意**:
- `source` 必须是**绝对路径**
- `audio.music` 使用 `asset_id` 引用 asset_manifest；若直接给音频路径需走 `audio_path` 参数
- ASS 字幕路径需转义冒号: `str(Path(path).resolve()).replace('\\', '/').replace(':', '\\:')`

### 3. Remotion CinematicRenderer
```bash
cd /home/kan/shared/OpenMontage/remotion-composer
npx remotion render CinematicRenderer ../projects/xyz/cinematic_props.json ../projects/xyz/renders/cinematic.mp4
```
**cinematic_props.json 结构** (见 `src/cinematic/types.ts`):
```json
{
  "scenes": [
    {"id": "s1", "kind": "video", "startSeconds": 0, "durationSeconds": 7, "src": "/abs/clip1.mp4", "tone": "cold", "fadeInFrames": 15, "fadeOutFrames": 15},
    {"id": "s2", "kind": "video", "startSeconds": 6.5, "durationSeconds": 8, "src": "/abs/clip2.mp4", "tone": "cold", "fadeInFrames": 15, "fadeOutFrames": 15},
    {"id": "title", "kind": "title", "startSeconds": 32.5, "durationSeconds": 4, "text": "Signal Pop\n隔天信号弹", "accent": "#00D4FF", "intensity": 0.8, "variant": "overlay"}
  ],
  "titleFontSize": 84, "titleWidth": 1400, "signalLineCount": 20,
  "music": {"src": "/abs/music.mp3", "volume": 0.18, "fadeInSeconds": 2, "fadeOutSeconds": 3}
}
```
**注意**: 必须用 `--output` 标志而非位置参数，否则报 `h264 + aac requires mp4/mkv/mov`

## 实测产出 (Signal Pop 雨夜城市主题)

| 文件 | 时长 | 大小 | 路径 |
|---|---|---|---|
| output_test.mp4 | 15s | 5.3MB | 3段基础拼接 |
| output_rain2.mp4 | 15s | 3.1MB | 2段雨夜 + 音乐 |
| output_rain_full.mp4 | 35s | 9.7MB | **5段完整版 + 音乐 + ASS字幕 (FFmpeg)** |
| output_remotion_cinematic.mp4 | 30s | 1.3MB | **CinematicRenderer: 文艺蒙太 + 滤镜分级 + 信号纹理 + 标题卡** |

素材已就绪: `projects/signal_pop_test/clips_rain/clips/` (5片段), `music_pixabay.mp3`, `subtitles_rain.ass`

## 经验总结

| 场景 | 推荐路径 | 理由 |
|---|---|---|
| 纯素材拼接 + 音乐 + 字幕 | `video_compose compose` (FFmpeg) | 最快、最稳、无 Node 依赖 |
| 文艺蒙太奇、色调分级、动态纹理、弹簧标题 | `Remotion CinematicRenderer` | 视觉质感强、可编程控制 |
| 动态字幕逐字、图表、对比卡、产品发布 | `Remotion Explainer` / `CaptionOverlay` | 组件库完整 |
| 动态排版、网页转视频、注册块驱动 | `HyperFrames` | HTML/CSS/GSAP 生态，**需先验证 npm 包可用** |
| 长视频切短、口播自动剪 | `clip-factory` pipeline | 专用 pipeline |

## 已知坑点
1. `video_compose` 不读 `edit_decisions.audio.music.asset_id` -> 需配合 `asset_manifest` 或直接用 `audio_path` 参数
2. `edit_decisions.subtitles.source` 为空时不报错但无字幕 -> 需显式传 `subtitle_path`
3. Remotion CLI 输出文件名校验严格 -> 必须用 `--output=xxx.mp4`
4. `direct_clip_search` 下载的 archive_org 片部分辨率低 (400x220) -> compose 会自动 letterbox 到 1920x1080
5. HyperFrames npm 包解析经常超时 -> 选型前必跑 `make hyperframes-doctor` 或 `hyperframes_compose doctor`
6. **免费库素材覆盖面极窄** — `archive_org`/`wikimedia` 只有新闻/纪录片/风景，**没有**「美女独自雨夜城市街头散步」等电影级特定场景
7. **Coverr API 需认证 (401)**，**Mixkit 下载页解析失败** — 实测仅 `archive_org` + `wikimedia` 稳定可用
8. **Remotion CinematicRenderer 全黑** — 当素材分辨率极低 (如 400x220) 被 cover 滤镜层遮盖，需预检素材分辨率 ≥ 720p
9. **渲染太慢** — Remotion ~4x 实时，FFmpeg compose ~6x 实时；10分钟成片需 40-60min
10. **预转码统一格式** → `-c copy` concat 可 10-20x 加速，建议下载后统一转码 1920x1080@30fps yuv420p libx264+aac
11. **Remotion CLI 无 `--props` 渲染全黑** — 默认 `scenes: []` 导致空序列；必须传 `--props=path/to/props.json`
12. **Remotion 不支持 `file://` 协议** — 本地素材需放 `public/` 目录，用相对路径引用 (如 `clips_rain/clip.mp4`)
13. **WebM/VP8/VP9 编码导致 Chromium 崩溃** — 必须先转码为 h264/yuv420p mp4 (`ffmpeg -i in.webm -c:v libx264 -pix_fmt yuv420p out.mp4`)
14. **交付前必验证输出** — 检查文件大小、抽帧验证像素均值 > 0；用户仅凭文件大小即识别出全黑视频

## 验证脚本
- `scripts/verify-remotion-output.py` — 渲染完成后自动抽帧检测全黑，CI/交付前必跑

## AI 视频生成补齐方案 (无免费素材时)

| 方案 | 本地/云 | 显存/门槛 | 适用场景 |
|---|---|---|---|
| **CogVideo** (`tools/video/cogvideo_video.py`) | 本地 | 24GB+ VRAM | 文生视频，完全可控，免费跑 |
| **Kling** (`tools/video/kling_video.py`) | 云 API | 需 Key | 文生/图生视频，质量高，付费 |
| **Luma Dream Machine** (`tools/video/luma_video.py`) | 云 API | 需 Key | 图生视频强，首帧一致性好 |
| **Runway Gen-2/Gen-3** | 云 API | 需 Key | 行业标杆，贵 |
| **SVD / AnimateDiff** | 本地 | 8-12GB VRAM | 图生视频，需先用 SDXL/Flux 生首帧 |

**推荐工作流 (有 GPU)**: SDXL/Flux 生高质首帧 → SVD/AnimateDiff 动图 → 5s 片段 → 预转码 → FFmpeg concat
**推荐工作流 (无 GPU)**: Kling/Luma API 生 5-10s 片段 → 预转码 → FFmpeg concat
**避坑**: 直接用文生视频做长镜头不稳定，**首帧控制 (图生视频) 质量更可控**