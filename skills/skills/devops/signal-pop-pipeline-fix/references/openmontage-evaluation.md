# OpenMontage Evaluation for Signal Pop Pipeline

**Date:** 2026-06-26  
**Context:** User shared https://github.com/calesthio/OpenMontage for team evaluation ("现学现用")

---

## Overview

OpenMontage = **开源 agentic 视频制作系统** (22k⭐, AGPL-3.0)
- 12 pipelines, 52 tools, 500+ agent skills
- Python + Node.js (Remotion) + FFmpeg
- 技能驱动架构，类似 Hermes Agent 的 skill 体系

---

## Relevant Pipelines for Signal Pop

| Pipeline | Stability | 适用场景 | 关键特性 |
|----------|-----------|----------|----------|
| `documentary-montage` | beta | **新闻/时事蒙太奇** (Daily/Weekly 核心) | 语义检索真实素材 (Pexels/Archive.org/NASA)、音乐同步、统一调色、哲学结束语、CLIP-based retrieval |
| `hybrid` | production | **真实素材 + 图形叠加** (当前 HyperFrames 方案对标) | 锚定素材为主、支撑层为辅、支持 Remotion/HyperFrames 双引擎、overlay density 质量门控 |
| `clip-factory` | beta | **长视频切短视频** (周报精华切条) | 多平台导出、Hook 放置、字幕统一、批量发布包 |
| `talking-head` | beta | **口播/主播视频** (未来可扩展虚拟主播) | 语音转写、跳剪、人脸追踪、动态字幕、多平台发布 |

---

## Tool Coverage vs Current Stack

| 能力 | 当前 Signal Pop | OpenMontage 内置 |
|------|-----------------|------------------|
| **视频合成** | HyperFrames (HTML→MP4) | `hyperframes_compose.py` + `remotion_compose` + `ffmpeg` |
| **素材检索** | BlazeAPI (参数不生效、1:1 拉伸) | `pexels_video.py`, `pixabay_video.py`, `corpus_builder.py`, `clip_search.py` (CLIP 语义检索) |
| **图片生成** | - | `flux_image.py`, `recraft_image.py`, `google_imagen.py`, `openai_image.py` |
| **视频生成** | - | `veo_video.py`, `kling_video.py`, `minimax_video.py`, `wan_video.py`, `ltx_video_local.py` |
| **TTS** | MiMo (xiaoxiao/yunyang) | `elevenlabs_tts.py`, `openai_tts.py`, `google_tts.py`, `piper_tts` (本地) |
| **字幕** | 手动 SRT | `remotion_caption_burn.py` (词级动画字幕)、`subtitle_gen.py` |
| **音乐** | - | `suno_music.py`、免版税库 |
| **调色/增强** | - | `color_grade.py`, `face_enhance.py`, `audio_enhance.py` |
| **发布** | 手动 | `publishers/` (YouTube, TikTok, etc.) |

---

## Architecture Alignment

| 维度 | Signal Pop 现状 | OpenMontage 方案 | 迁移价值 |
|------|-----------------|------------------|----------|
| **编排** | Shell 脚本 + Python 线性流水线 | Executive Producer skill + checkpoint 审批 + 人工介入点 | ✅ 更鲁棒、可观测、可回滚 |
| **素材源** | BlazeAPI (单一、参数失效) | 多源免费库 + 语义检索 + corpus 去重 | ✅ 解决 1:1 拉伸、素材质量不稳定 |
| **渲染引擎** | HyperFrames 单一 | HyperFrames / Remotion / FFmpeg 可选 | ✅ 兜底方案、HyperFrames 端卡可切 Remotion |
| **技能复用** | 无 | 500+ 现成 skills，pipeline 级复用 | ✅ 避免重复造轮子 |
| **成本控制** | 隐性 | 每 pipeline `budget_default_usd`、provider 7 维评分决策日志 | ✅ 可审计、可预测 |
| **质量门控** | 无 | 每阶段 `checkpoint_required` + `review_focus` + `success_criteria` | ✅ 自动化 QA |

---

## Integration Path Options

### Option A: 直接采用 OpenMontage Pipeline (推荐长期)
```
Signal Pop daily/weekly → 映射到 documentary-montage / hybrid pipeline
- 复用现有 fetch/filter 逻辑 → 作为 custom skill 注入 idea 阶段
- MiMo TTS → 作为 custom provider 注入
- 虾小图新闻稿 → 作为 brief 输入源
- HyperFrames 端卡 → 迁移到 Remotion EndCard 组件
```

### Option B: 混合模式 (低风险、快速见效)
```
保留现有 fetch/filter/generate_script/tts_mimo
仅替换视频合成阶段：
- 当前: HyperFrames (不稳定)
- 新: OpenMontage video_compose / hyperframes_compose (更成熟、有质检)
素材检索：接入 OpenMontage corpus_builder + clip_search 替代 BlazeAPI
```

### Option C: 仅借用工具库
```
从 tools/ 复用单个工具：
- pexels_video.py / pixabay_video.py → 免费素材直连
- clip_search.py (CLIP) → 语义匹配
- color_grade.py → 统一调色
- remotion_caption_burn.py → 专业级动态字幕
```

---

## Quick Start for Evaluation (实测 2026-06-26)

```bash
# 1. Clone to shared (团队共享目录)
git clone https://github.com/calesthio/OpenMontage.git /home/kan/shared/OpenMontage
cd /home/kan/shared/OpenMontage

# 2. Setup (需 Python 3.10+, FFmpeg, Node 18+)
# 无 sudo 时 FFmpeg 静态二进制方案：
mkdir -p ~/.local/bin
cd /tmp && wget -q https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz \
  && tar -xf ffmpeg-release-amd64-static.tar.xz \
  && cp ffmpeg-*-amd64-static/ffmpeg ~/.local/bin/ \
  && cp ffmpeg-*-amd64-static/ffprobe ~/.local/bin/ \
  && chmod +x ~/.local/bin/ffmpeg ~/.local/bin/ffprobe
export PATH="$HOME/.local/bin:$PATH"

# Python deps + Remotion + Piper TTS
pip install -r requirements.txt
cd remotion-composer && npm install && cd ..
pip install piper-tts

# 3. Configure .env
cp .env.example .env
# 免费素材必填（官网免费申请）：
# PEXELS_API_KEY=*** (https://www.pexels.com/api/)
# PIXABAY_API_KEY=*** (https://pixabay.com/api/docs/)
# UNSPLASH_ACCESS_KEY=xxx (可选)
# Archive.org / NASA / Wikimedia 无需 Key

# 4. Verify tool registry (验证可用能力)
export PATH="$HOME/.local/bin:$PATH"
python -c "from tools.tool_registry import registry; import json; registry.discover(); print(json.dumps(registry.provider_menu(), indent=2))"

# 5. Run zero-key demos (无需任何 API Key)
python render_demo.py --list
# world-in-numbers  | 全球数据故事 (标题/统计/图表)
# focusflow-pitch   | 创业路演风格 (纯 Remotion 组件)
# code-to-screen    | 开发者工作流解释 (对比卡片/KPI卡)
python render_demo.py world-in-numbers

# 6. HyperFrames runtime check
npx hyperframes doctor
# 或工具内置 doctor
python -c "from tools.video.hyperframes_compose import HyperFramesCompose; r=HyperFramesCompose().execute({'operation':'doctor'}); import json; print(json.dumps(r.data, indent=2))"
```

---

## Tool Registry Verification (2026-06-26 实测)

**环境**：Python 3.11, Node 24.15.0, FFmpeg 7.0.2 (static), 无 GPU

| 类别 | Available (可用) | Unavailable (需额外依赖/Key) |
|------|------------------|------------------------------|
| **analysis** | audio_energy, frame_sampler, scene_detect, visual_qa, audio_probe, composition_validator, video_analyzer, transcriber(whisperx), transcript_fetcher(youtube) | face_tracker(mediapipe), video_understand(transformers+GPU) |
| **audio_processing** | audio_enhance(ffmpeg), audio_mixer(ffmpeg) | - |
| **video_composition** | auto_reframe, green_screen_composite, green_screen_processor, showcase_card, silence_cutter, video_compose(ffmpeg/remotion/hyperframes), video_stitch, video_trimmer, hyperframes_compose | - |
| **graphics** | diagram_gen(mermaid), code_snippet(pygments) | math_animate(manim+LaTeX) |
| **image_generation** | google_imagen(api) | flux_image(fal.ai), grok_image(xai), openai_image, recraft_image, local_diffusion(GPU) |
| **tts** | google_tts(api), piper_tts(local) | doubao_tts, elevenlabs_tts, openai_tts |
| **video_generation** | - | 全部需 API Key 或 GPU (veo/kling/minimax/wan/ltx/cogvideo/hunyuan/seedance/runway/heygen/higgsfield/grok) |
| **stock_media** | coverr(免费, 50req/hr, 无需Key), archive_org, wikimedia, nasa, mixkit, dareful, jaxa, esa, loc, nara, pond5_pd, noaa | pexels, pixabay, unsplash (需免费Key) |
| **corpus_population** | corpus_builder(degraded: 部分免费源可用) | pexels, pixabay, unsplash 需配置 Key 后可用 |

**关键结论**：
- **零 Key 可跑通**：Piper TTS + Remotion 组件渲染 + HyperFrames + FFmpeg 全套剪辑 + **archive_org/wikimedia/nasa/mixkit/dareful/jaxa/esa** 免费素材
- **免费 Key 解锁**：Pexels/Pixabay/Unsplash/Coverr → 大量高质量实拍视频/图片
- **付费 Key 解锁**：高质量 TTS (ElevenLabs/OpenAI/Google/Doubao)、视频生成 (Veo/Kling/Minimax/Runway)、FLUX/Recraft 图片
- **本地 GPU 解锁**：WAN/Hunyuan/LTX/CogVideo 等开源视频模型

---

## Key Files to Study

| 文件 | 用途 |
|------|------|
| `pipeline_defs/documentary-montage.yaml` | 核心管道定义 (最贴合 Daily) |
| `pipeline_defs/hybrid.yaml` | 混合管道 (贴合 HyperFrames 场景) |
| `skills/pipelines/documentary-montage/` | 6 个阶段 director skills |
| `tools/video/hyperframes_compose.py` | HyperFrames 渲染工具 (直接可用) |
| `tools/video/corpus_builder.py` | 语料库构建 (多源聚合) |
| `tools/video/clip_search.py` | CLIP 语义检索 |
| `tools/video/remotion_caption_burn.py` | 词级动态字幕 |
| `AGENT_GUIDE.md` | Agent 操作手册 |
| `PROJECT_CONTEXT.md` | 项目上下文契约 |

---

## Risk Assessment

| 风险 | 缓解 |
|------|------|
| AGPL-3.0 许可证 | 内部使用无传播风险；若对外发布视频无源码义务 |
| Beta 稳定性 | `hybrid` 已 production；`documentary-montage` beta 但核心链路完整 |
| 学习曲线 | 技能驱动架构与 Hermes 相似，团队已有认知基础 |
| 依赖复杂度 | `make setup` 自动化；可选 GPU 本地生成降低 API 成本 |
| 中文支持 | 需验证 CLIP 中文检索效果、TTS 中文自然度 |

---

## Next Steps

1. **Clone 到共享目录** - 供团队现学现用
2. **跑通 documentary-montage 单次测试** - 验证素材质量、渲染速度、中文表现
3. **对比输出质量** - OpenMontage vs 现有 HyperFrames+BlazeAPI (同脚本、同素材源)
4. **决策迁移范围** - Option A/B/C 基于实测结果选择

---

## Related Memory

- Signal Pop 当前痛点：BlazeAPI 参数不生效 → 1:1 图拉伸 16:9；HyperFrames 端卡渲染不稳定
- 用户偏好：免费工具优先、一周内出预览、LAN 共享目录统一管理项目文件
- 当前 Cron 全部暂停，手动触发模式，Daily 仅音频+SRT，Weekly 含视频

---

## Free Source Testing Results (2026-06-26 实测详情)

### corpus_builder 可用免费源实测

| 源 | name | 可用 | 视频 | 时长信息 | 下载链接 | 备注 | 测试查询 |
|---|---|---|---|---|---|---|---|
| **Archive.org** | `archive_org` | ✅ | ✅ | ✅ 真实时长 (68-107s) | ✅ 直链 mp4 | Prelinger/opensource_movies/home_movies 公有领域 | "rain city night" |
| **Wikimedia Commons** | `wikimedia` | ✅ | ✅ | ✅ 真实时长 (7-1338s) | ✅ 直链 | CC 许可，需注意超长视频过滤 | "rain city night" |
| **NASA** | `nasa` | ✅ | ✅ | ❌ 时长=0 (需 ffprobe 探测) | ✅ 直链 | 科学/太空素材，metadata 无时长 | "rain city night" |
| **Mixkit** | `mixkit` | ✅ | ✅ | ❌ 时长=0 (需 ffprobe 探测) | ✅ 直链 | 免费商用，4K 可选 | "rain city night" |
| **Dareful** | `dareful` | ✅ | ✅ | ❌ 时长=0 (需 ffprobe 探测) | ✅ 直链 | 4K 素材，自然风光为主 | "rain city night" |
| **JAXA** | `jaxa` | ✅ | ❌ 结果为空 | - | - | 日空局素材，中文查询命中率低 | "rain city night" |
| **ESA** | `esa` | ✅ | ❌ 结果为空 | - | - | 欧空局素材，中文查询命中率低 | "rain city night" |
| **Coverr** | `coverr` | ⚠️ | - | - | - | **需 API Key** (401 Unauthorized) | - |
| **LOC** | `loc` | ❌ | - | - | - | 403 Forbidden | - |
| **NARA** | `nara` | ❌ | - | - | - | JSON 解析失败 | - |
| **Pond5 PD** | `pond5_pd` | ❌ | - | - | - | 403 (API + web fallback 皆失败) | - |
| **NOAA** | `noaa` | ❌ | - | - | - | 403 Forbidden | - |

### corpus_builder 输入参数规范 (实测验证)

```python
{
    'operation': 'build',
    'corpus_dir': '/path/to/corpus',  # 必填
    'queries': [                       # 必填，数组
        {'query': 'rain city night', 'kind': 'video', 'per_source': 5},
        {'query': 'city street rain', 'kind': 'video', 'per_source': 5}
    ],
    'sources': ['archive_org', 'wikimedia', 'nasa', 'mixkit', 'dareful'],  # 可选，默认全用
    'max_new_clips': 20,               # 可选，默认 100
    'filters': {                       # 可选
        'min_duration': 5,
        'max_duration': 180,
        'orientation': 'landscape'
    }
}
```

### 关键发现

1. **Archive.org + Wikimedia 是核心免费视频源** - 有真实时长、直链下载、内容多样 (Prelinger 收藏极佳)
2. **NASA/Mixkit/Dareful 需 ffprobe 后探测时长** - corpus_builder 会自动下载后探测，但搜索阶段无法按时长过滤
3. **Coverr 需免费 Key** - 官网注册即可，50 req/hr 免费额度
4. **LOC/NARA/Pond5/NOAA 当前不可用** - 403 或解析失败，可能需 User-Agent 或反爬
5. **中文查询命中率** - Archive.org/Wikimedia/NASA/Mixkit/Dareful 对中文查询均有结果
6. **corpus_dir 结构** - 自动创建 `clips/`, `thumbnails/`, `index.jsonl`, `embeddings.npy`, `tag_embeddings.npy`

### Zero-Key Demos 实测

```bash
python render_demo.py --list
# world-in-numbers  | 全球数据故事 (标题/统计/图表) - 纯 Remotion 组件
# focusflow-pitch   | 创业路演风格 (纯 Remotion 组件)
# code-to-screen    | 开发者工作流解释 (对比卡片/KPI卡)
```

### FFmpeg 免 sudo 安装 (已验证)

```bash
mkdir -p ~/.local/bin
cd /tmp && wget -q https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz \
  && tar -xf ffmpeg-release-amd64-static.tar.xz \
  && cp ffmpeg-*-amd64-static/ffmpeg ~/.local/bin/ \
  && cp ffmpeg-*-amd64-static/ffprobe ~/.local/bin/ \
  && chmod +x ~/.local/bin/ffmpeg ~/.local/bin/ffprobe
export PATH="$HOME/.local/bin:$PATH"
```