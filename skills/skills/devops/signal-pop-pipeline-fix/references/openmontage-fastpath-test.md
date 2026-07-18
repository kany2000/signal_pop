# OpenMontage Fast Path 实测记录 (2026-06-26)

**背景**: 无 GPU、无 PyTorch/CLIP 环境下，验证 `direct_clip_search` + `video_compose` (FFmpeg) 端到端链路。

---

## 环境

| 组件 | 版本 | 状态 |
|------|------|------|
| Python | 3.11.14 | ✅ |
| Node.js | 24.15.0 | ✅ |
| FFmpeg | 7.0.2 (static) | ✅ |
| PyTorch | 未安装 | ❌ (pytorch.org 网络超时) |
| CLIP embeddings | 不可用 | ⚠️ 需 torch |
| Remotion composer | 已 npm install | ✅ |
| HyperFrames | npx 可用 | ✅ |
| Piper TTS | 已安装 | ✅ (需下载语音模型) |

---

## 免费素材源实测 (direct_clip_search)

### 测试命令
```python
from tools.video.direct_clip_search import DirectClipSearch

tool = DirectClipSearch()
result = tool.execute({
    'operation': 'search',
    'queries': [
        {'query': 'rain city night', 'clips_per_query': 2},
        {'query': 'city street rain night', 'clips_per_query': 2},
        {'query': 'urban night lights rain', 'clips_per_query': 2},
        {'query': 'rain window city', 'clips_per_query': 1},
        {'query': 'wet streets night lights', 'clips_per_query': 1}
    ],
    'sources': ['archive_org', 'wikimedia', 'nasa', 'mixkit', 'dareful'],
    'output_dir': '/home/kan/shared/OpenMontage/signal_pop_test/clips'
})
```

### 结果统计

| 源 | 下载成功 | 视频数 | 总大小 | 时长范围 | 缩略图 |
|---|---|---|---|---|---|
| `archive_org` | ✅ | 1 | 7.8 MB | 107s | ✅ |
| `wikimedia` | ✅ | 2 | 15.4 MB | 18s, 1338s | ✅ (1/2) |
| `nasa` | ⚠️ | 0 | - | - | - |
| `mixkit` | ⚠️ | 0 | - | - | - |
| `dareful` | ⚠️ | 0 | - | - | - |

**实际下载到 3 个片段**（archive_org 1个 + wikimedia 2个），其他源搜索有结果但下载阶段可能超时或格式不匹配。

### 片段详情
```
archive_org_BrotherCanYouSpareADimePlayedByFritzSwischerwithVideo.mp4  7.8MB  107.97s
wikimedia_66989018.webm  6.5MB   18.20s   (Heavy rain in Hefei city center)
wikimedia_68513601.webm  8.9MB  1338.14s  (Hoi An city tour - 超长需裁剪)
```

---

## 视频合成实测 (video_compose FFmpeg)

### 测试命令
```python
from tools.video.video_compose import VideoCompose

tool = VideoCompose()
result = tool.execute({
    'operation': 'compose',
    'edit_decisions': {
        'render_runtime': 'ffmpeg',
        'cuts': [
            {'source': '.../archive_org_....mp4', 'in_seconds': 0, 'out_seconds': 10, 'transition': 'none'},
            {'source': '.../wikimedia_66989018.webm', 'in_seconds': 0, 'out_seconds': 10, 'transition': 'crossfade'},
            {'source': '.../wikimedia_68513601.webm', 'in_seconds': 0, 'out_seconds': 10, 'transition': 'crossfade'}
        ],
        'audio': {'source': 'none'},
        'output': {'resolution': '1920x1080', 'fps': 30, 'codec': 'libx264', 'crf': 23}
    },
    'output_path': '/home/kan/shared/OpenMontage/signal_pop_test/output_test.mp4'
})
```

### 结果
- **成功**: ✅
- **输出时长**: 28.01s (3个10s片段 + 2个1s crossfade)
- **分辨率**: 1920x1080
- **编码**: H.264, CRF 23
- **文件大小**: 10.9 MB
- **耗时**: ~10 秒

---

## 关键结论

### ✅ 可用于 Signal Pop Daily/Weekly 的核心链路
```
用户提示 → idea-director (brief + scene_plan)
    ↓
asset-director: direct_clip_search (archive_org + wikimedia + nasa + mixkit + dareful)
    ↓
edit-director: 生成 edit_decisions (时间轴、转场、音乐同步)
    ↓
compose-director: video_compose (FFmpeg/Remotion/HyperFrames)
    ↓
输出: MP4 + SRT + 音频混音
```

### ⚠️ 需补齐的拼图
| 需求 | 方案 | 优先级 |
|------|------|--------|
| **中文旁白** | MiMo TTS (已有 Key: `sk-c6i...5odm`) | 🔴 高 |
| **背景音乐** | 免版税库 / Suno API / 本地素材 | 🟡 中 |
| **逐字字幕** | WhisperX (需 torch) / 现成 SRT 烧录 | 🟡 中 |
| **片尾观点卡片** | Remotion 组件 / HyperFrames | 🟢 低 |
| **竖屏 9:16** | `auto_reframe` + `video_compose` | 🟢 低 |

### 🚫 当前阻塞项
| 项 | 原因 | 影响 | 绕过方案 |
|----|------|------|----------|
| PyTorch 安装 | pytorch.org 网络超时 | 无 CLIP 语义检索、无 corpus_builder 完整功能 | 使用 `direct_clip_search` fast path |
| Piper 中文模型 | 需手动下载 huggingface.co | 无本地中文 TTS | 用 MiMo TTS 云 API |
| coverr/LOC/NARA/Pond5/NOAA | 403/解析失败 | 素材源减少 | 依赖 archive_org + wikimedia + nasa + mixkit + dareful |

### ❌ 免费素材源覆盖面极窄 (2026-07-01 新发现)
**实测：`archive_org`/`wikimedia`/`coverr`/`mixkit`/`dareful` 等免费库均无「美女独自雨夜城市街头散步」等电影级特定场景**
- `archive_org`: 仅档案/纪录片/教育片，无电影感城市雨夜人像
- `wikimedia`: 仅新闻/事件/地标实拍，无电影感构图
- `coverr`: API 需认证 (401)
- `mixkit`: 下载页解析失败
- **结论**: 需特定电影级场景时，**必须用 AI 视频生成补齐**

### ⚠️ Remotion CinematicRenderer 全黑坑点 (2026-07-01 新发现)
- **现象**: 素材分辨率极低 (如 400x220) 时，被 cover 滤镜层遮盖 → 输出全黑
- **预检**: 素材分辨率必须 ≥ 720p，建议预转码统一 1920x1080@30fps yuv420p

### ⚡ 渲染太慢 & 预转码加速 (2026-07-01 新发现)
| 路径 | 速度 | 10分钟成片耗时 |
|------|------|----------------|
| Remotion CinematicRenderer | ~4x 实时 | ~40 分钟 |
| FFmpeg compose | ~6x 实时 | ~20 分钟 |
| **预转码统一格式 → `-c copy` concat** | **10-20x** | **< 1 分钟** |

**推荐工作流**: 下载后统一转码 1920x1080@30fps yuv420p libx264+aac → 合成时直接 concat copy

### 🤖 AI 视频生成补齐方案 (无免费素材时)
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

---

## 迁移建议

### 阶段 1: 替换视频合成层 (1-2 天)
- 保留现有 `fetch_news.py` → `filter_news.py` → `generate_script.py` → `tts_mimo.py`
- 用 OpenMontage `video_compose` 替代 `generate_video.py` + HyperFrames
- 素材源接入 `direct_clip_search` (archive_org + wikimedia 为主)

### 阶段 2: 接入语义检索 (待 torch 解决)
- 安装 torch (尝试清华/阿里云镜像源)
- 启用 `corpus_builder` + `clip_search` 完整流程
- 享受 CLIP 语义匹配、去重、多样化选片

### 阶段 3: 全流水线迁移 (长期)
- 映射 Signal Pop daily/weekly 到 `documentary-montage` / `hybrid` pipeline
- 复用 checkpoint 审批、质量门控、预算控制
- MiMo TTS 注册为 custom provider

---

## 文件位置记录

| 产物 | 路径 |
|------|------|
| 素材下载目录 | `/home/kan/shared/OpenMontage/signal_pop_test/clips/` |
| 合成输出视频 | `/home/kan/shared/OpenMontage/signal_pop_test/output_test.mp4` |
| corpus 测试目录 | `/home/kan/shared/OpenMontage/corpus_mini3/` |
| OpenMontage 根目录 | `/home/kan/shared/OpenMontage/` |

---

## 下一步行动建议

1. **集成 MiMo TTS** → 生成中文旁白 → `audio_mixer` 混入视频
2. **测试字幕烧录** → `remotion_caption_burn` 或 FFmpeg `subtitles` filter
3. **跑完整 documentary-montage pipeline (fast path)** 生成一期 60s "城市雨夜"
4. **对比现有 HyperFrames+BlazeAPI 方案** 的输出质量与稳定性