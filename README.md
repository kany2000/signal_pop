# Signal Pop 信号弹

新闻短视频自动生成管线。从 RSS 抓取新闻 → AI 筛选 → 脚本生成 → 图片生成 → TTS 语音 → 合成视频。

## 项目结构

```
signal_pop/
├── src/                    # 核心模块
│   ├── fetch_news.py       # RSS 新闻抓取
│   ├── fetch_news_lite.py  # 轻量版抓取
│   ├── filter_news.py      # AI 新闻筛选
│   ├── generate_script.py  # 脚本生成
│   ├── generate_video.py   # 视频合成
│   ├── monitor_pipeline.py # 管线监控
│   ├── parse_xiaoxiaotu.py # 小红书解析
│   ├── tts_google.py       # Google TTS
│   └── tts_mimo.py         # Mimo TTS
├── tools/                  # 工具模块
│   ├── add_ticker.py       # 滚动字幕叠加
│   ├── batch_gen_images.py # 批量图片生成
│   ├── composite_video.py  # 视频合成
│   ├── gen_cover.py        # 封面生成（AI）
│   ├── gen_cover_local.py  # 封面生成（本地）
│   ├── gen_hyperframes_html.py  # HyperFrames HTML 渲染
│   ├── gen_missing_images.py    # 补图
│   ├── gen_scene_images*.py     # 场景图片生成（多版本）
│   ├── gen_srt.py          # 字幕生成
│   ├── gen_timeline.py     # 时间线生成
│   └── render_daily_video.py    # 每日视频渲染
├── scripts/                # Windows 本地执行管线
│   ├── win_pipeline_run.py    # 管线入口（一键运行）
│   ├── win_pipeline_parse.py  # 脚本解析
│   ├── win_pipeline_tts.py    # TTS 生成
│   ├── win_pipeline_images.py # 图片生成
│   ├── win_pipeline_cover.py  # 封面生成
│   ├── win_pipeline_video.py  # 视频合成
│   ├── build_daily_video.py   # 每日视频构建（Linux）
│   ├── build_weekend_video.py # 周末视频构建
│   ├── gen_custom_images.py   # 自定义图片生成
│   ├── gen_news_images.py     # 新闻图片生成
│   ├── generate_weekend_cover.py  # 周末封面生成
│   ├── run_cover.py           # 封面运行入口
│   ├── sensenova_client.py    # 商汤 SenseNova API 客户端
│   └── generate_audio_only.sh # 仅音频生成脚本
├── daily/                  # 每日数据目录
├── output/                 # 输出产物
├── archive/                # 历史归档
└── skills/                 # 技能配置
```

## 依赖

- Python 3.10+
- [Pillow](https://python-pillow.org/) — 图片处理
- [requests](https://requests.readthedocs.io/) — HTTP 请求
- [feedparser](https://feedparser.readthedocs.io/) — RSS 解析
- [numpy](https://numpy.org/) — 数值计算
- [python-dateutil](https://dateutil.readthedocs.io/) — 日期解析
- ffmpeg — 视频合成（需系统安装）

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

确保系统已安装 ffmpeg 并加入 PATH：

```bash
# Windows (choco)
choco install ffmpeg

# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt install ffmpeg
```

### 2. 配置

各脚本顶部有 CONFIG 区域，需修改：

- `DATE` — 准备日期（YYYYMMDD）
- `OUTPUT_BASE` — 输出目录
- `SCRIPT_FILE` — 原始脚本文件路径
- API 密钥（如适用）— 商汤 SenseNova、Unsplash 等

### 3. 运行

**Windows 一键管线：**

```bash
cd scripts
python win_pipeline_run.py
```

**Linux 每日视频构建：**

```bash
python scripts/build_daily_video.py
```

## 管线流程

```
┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
│ 抓取新闻  │ → │ AI 筛选  │ → │ 脚本生成  │ → │ 图片生成  │ → │ TTS 语音 │
│ fetch    │   │ filter   │   │ script   │   │ images   │   │ tts      │
└──────────┘   └──────────┘   └──────────┘   └──────────┘   └──────────┘
                                                              │
┌──────────┐   ┌──────────┐   ┌──────────┐                   │
│ 发布输出  │ ← │ 视频合成  │ ← │ 封面生成  │ ← ────────────────┘
│ publish  │   │ video    │   │ cover    │
└──────────┘   └──────────┘   └──────────┘
```

## 视频样式

- 深色霓虹风格（青蓝/紫色调）
- 全屏背景 + 新闻标题叠加
- 滚动字幕（ticker）
- TTS 语音旁白
- 自定义封面（含日期、标题、女主播形象）

## 许可

MIT