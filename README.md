# Signal Pop 信号弹

新闻短视频自动生成管线。从 RSS 抓取新闻 → AI 筛选 → 脚本生成 → 图片生成 → TTS 语音 → 合成视频。

## 项目结构

```
signal_pop/
├── config.py               # 集中配置管理（路径、API密钥、样式等）
├── logger.py               # 统一日志与错误处理模块
├── styles.py               # 视频样式管理（颜色主题、字体）
├── run_pipeline.py          # 统一管线入口（跨平台，支持 --weekly / --skip-images）
├── .env.example             # 环境变量配置模板
├── .flake8                  # 代码质量检查配置
├── pytest.ini               # 测试框架配置
├── tests/                   # 单元测试
│   ├── conftest.py          # 测试 fixtures
│   ├── test_config.py       # 配置模块测试
│   ├── test_parse.py        # 新闻解析测试
│   ├── test_images.py       # 图片生成提示词测试
│   └── test_styles.py       # 样式管理测试
├── src/                     # 核心模块
│   ├── fetch_news.py        # RSS 新闻抓取
│   ├── fetch_news_lite.py   # 轻量版抓取
│   ├── filter_news.py       # AI 新闻筛选
│   ├── generate_script.py   # 脚本生成
│   ├── generate_video.py    # 视频合成
│   ├── monitor_pipeline.py  # 管线监控
│   ├── parse_xiaoxiaotu.py  # 小红书解析
│   ├── tts_google.py        # Google TTS
│   └── tts_mimo.py          # Mimo TTS
├── tools/                   # 工具模块
│   ├── add_ticker.py        # 滚动字幕叠加
│   ├── batch_gen_images.py  # 批量图片生成
│   ├── composite_video.py   # 视频合成
│   ├── gen_cover.py         # 封面生成（AI）
│   ├── gen_cover_local.py   # 封面生成（本地）
│   ├── gen_hyperframes_html.py  # HyperFrames HTML 渲染
│   ├── gen_missing_images.py    # 补图
│   ├── gen_scene_images*.py     # 场景图片生成（多版本）
│   ├── gen_srt.py          # 字幕生成
│   ├── gen_timeline.py     # 时间线生成
│   └── render_daily_video.py    # 每日视频渲染
├── scripts/                # 管线脚本
│   ├── win_pipeline_run.py    # Windows 管线入口
│   ├── win_pipeline_parse.py  # 脚本解析
│   ├── win_pipeline_tts.py    # TTS 生成
│   ├── win_pipeline_images.py # 图片生成
│   ├── win_pipeline_cover.py  # 封面生成
│   ├── win_pipeline_video.py  # 视频合成
│   ├── build_daily_video.py   # 每日视频构建（Linux）
│   ├── build_weekend_video.py # 周末视频构建
│   └── logger.py              # 日志桥接模块
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
- [ffmpeg-python](https://github.com/kkroening/ffmpeg-python) — FFmpeg Python 封装
- ffmpeg — 视频合成（需系统安装）

### 开发依赖（可选）

- [flake8](https://flake8.pycqa.org/) — 代码质量检查
- [black](https://black.readthedocs.io/) — 代码格式化
- [pytest](https://docs.pytest.org/) — 单元测试框架

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt

# 开发依赖（可选）
pip install flake8 black pytest pytest-cov
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

复制 `.env.example` 为 `.env` 并填入你的配置：

```bash
cp .env.example .env
```

关键配置项：

| 环境变量 | 说明 | 默认值 |
|---------|------|--------|
| `SIGNAL_POP_PREP_DATE` | 准备日期 (YYYYMMDD) | 昨天 |
| `SIGNAL_POP_SCRIPT_FILE` | 新闻脚本文件路径 | archive/signal_pop_daily_*.txt |
| `SENSENOVA_API_KEY` | 商汤 SenseNova API 密钥 | （无，必须设置） |
| `FFMPEG_PATH` | ffmpeg 可执行文件路径 | ffmpeg (PATH) |
| `SIGNAL_POP_FONT_REGULAR` | 常规字体路径 | NotoSansCJK-Regular.ttc |
| `SIGNAL_POP_LOG_LEVEL` | 日志级别 | INFO |

也可以在 `config.py` 中直接修改配置，或通过环境变量覆盖。

### 3. 运行

**统一管线入口（推荐，跨平台）：**

```bash
# 每日视频
python run_pipeline.py

# 周末特别版
python run_pipeline.py --weekly

# 跳过图片生成（已有图片时）
python run_pipeline.py --skip-images

# 指定日期
SIGNAL_POP_PREP_DATE=20260717 python run_pipeline.py
```

**Windows 一键管线：**

```bash
python scripts/win_pipeline_run.py
```

**Linux 每日视频构建：**

```bash
python scripts/build_daily_video.py
```

### 4. 测试

```bash
# 运行全部测试
python -m pytest tests/ -v

# 代码质量检查
python -m flake8 config.py logger.py styles.py scripts/*.py

# 代码格式化
python -m black --line-length=120 config.py logger.py styles.py scripts/*.py
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
- 4 套颜色主题自动轮换（蓝白经典/橙黑科技/墨绿财经/紫金国际）
- 全屏背景 + 新闻标题叠加
- 滚动字幕（ticker）
- TTS 语音旁白
- 自定义封面（含日期、标题、女主播形象）

## 架构设计

### 配置管理

所有配置集中在 `config.py`，支持环境变量覆盖：

```python
from config import OUTPUT_VIDEO_PATH, SENSENOVA_API_KEY, get_style_for_date
```

### 日志与错误处理

统一的日志记录和自定义异常类：

```python
from logger import logger, log_and_raise, NewsParseError

try:
    # 业务逻辑
except Exception as e:
    log_and_raise(NewsParseError, f"解析失败: {e}")
```

### 样式管理

按日期自动选择颜色主题，支持自定义扩展：

```python
from styles import get_style_for_date, get_video_resolution

style = get_style_for_date("20260717")
# style = {'bar': (30,85,130), 'accent': (255,215,0), 'sub': (200,200,220)}
```

## 许可

MIT
