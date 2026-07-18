---
name: signal-pop-pipeline-fix
description: Signal Pop 新闻播报流水线修复 - 解决 HTML 实体残留、摘要截断、垃圾内容混入、繁体未转简体、英文标题未翻译等问题
category: devops
tags: [signal-pop, news-pipeline, python, rss, filtering]
---

# Signal Pop 流水线修复记录

## 问题背景
每日新闻脚本出现：
- HTML 实体未解码：`作者&nbsp;|&nbsp;王晗玉`
- 摘要硬截断半句：`此次融资将..`、`过...`
- 体育/娱乐/财经行情/博彩广告混入
- BBC 中文繁体未转简体
- 英文标题未翻译直接输出

## 修复方案

### 1. fetch_news.py - 摘要清理与智能截断
```python
import html
import re

# 解码 HTML 实体
summary = html.unescape(summary)

# 智能截断：在句号/问号/感叹号处截断
if len(summary) > 300:
    match = re.search(r'[。！？.!?]', summary[:300])
    if match:
        summary = summary[:match.end()]
    else:
        summary = summary[:300]
```

### 2. filter_news.py - 多层过滤与清理
```python
# 依赖
pip install opencc-python-reimplemented

# 核心功能
- HTML 实体解码: html.unescape()
- 繁体转简体: OpenCC('t2s')
- 垃圾内容关键词过滤 (体育/娱乐/财经行情/博彩/低质)
- 英文标题检测过滤 (正则 + 中文字符占比)
```

### 3. 垃圾关键词清单 (SPAM_KEYWORDS)
- 体育: 世界杯、FIFA、NBA、奥运、裁判、进球、比分...
- 娱乐: 票房、电影、玩具总动员、漫威、奥斯卡...
- 财经行情: 美元指数、期铜、LME、收盘、涨停、北向资金...
- 博彩广告: 点击浏览、即时更新、精彩进球、赔率、盘口...
- 低质: quiz、是什么、你是什么...

### 4. 英文标题检测逻辑
```python
# 全英文
re.match(r'^[A-Za-z\s\.,\-\'\?]+$', title)

# 英文句式开头无中文
re.match(r'^[A-Z][a-z]+\s+[a-z]+', title) and not re.search(r'[\u4e00-\u9fff]', title)

# 英文单词占比 >70% 且无中文
english_words / total_words > 0.7 and no_chinese
```

## 验证结果
修复后输出示例：
```
第1条，国内新闻。金饰克价一夜又跌11元。
据 36kr 报道，6月20日，国内黄金饰品价格对比显示...
第5条，科技新闻。诺贝尔奖得主约翰·江珀宣布加盟Anthropic。
据 36kr 报道，当地时间6月19日...
```

## 人工选题分工 (2026-06-20 约定)
- **新闻选题负责人**：虾小图 (@opclwtg_one_bot)
- **职责**：每期从原始 70 条 `raw_feed.json` 中精选 10 条，剔除重复/标题不对题/低质内容
- **介入点**：`filter_news.py` 运行前，人工生成/修订 `filtered_news.json`
- **后续自动化**：`generate_script.py` → `tts_mimo.py` → 视频合成保持不变

## 工作流模式对比 (2026-06-22 实测)

| 维度 | Monitor 方式 (新) | 脚本方式 (旧) |
|------|-------------------|---------------|
| 触发 | 文件落地即触发 (≤10 min) | 固定时间 cron |
| 人工介入 | 虾小图投放 filtered_news.json | filter_news.py 自动跑 |
| 灵活性 | 高 - 可随时补发/改发 | 低 - 错过时间点需手动跑 |
| 稳定性 | 高 - 内容 hash 去重 | 中 - 依赖时间判断 |
| 当前状态 | **主流程** | 回退/兼容 |

> Monitor 方式已验证端到端通：6月20日周六新闻 → filtered_news.json → monitor_pipeline.py → 脚本+双声道音频+归档，全程自动。

### 文件位置
- `/home/kan/signal_pop/src/fetch_news.py`
- `/home/kan/signal_pop/src/filter_news.py`
- `/home/kan/signal_pop/src/generate_script.py`
- `/home/kan/signal_pop/src/tts_mimo.py`
- `/home/kan/signal_pop/src/tts_google.py`
- `/home/kan/signal_pop/src/monitor_pipeline.py`  # 监控触发器
- `/home/kan/signal_pop/src/parse_xiaoxiaotu.py`  # 虾小图稿件解析
- `/home/kan/signal_pop/src/generate_video.py`  # 视频合成

**视频产出与分发位置（本次会话新增）**：
- 马小v 视频产出：`/home/kan/shared/upload/signal_pop_daily_YYYYMMDD.mp4`
- 分发监控目录：`/home/kan/shared/her2home/video_YYYYMMDD.mp4` + `video_YYYYMMDD.png` + `video_YYYYMMDD.json`
- **需手动复制/重命名** 到分发目录，auto_publish.py 才能扫描到
- 封面命名必须与视频同名（`video_` 前缀，非 `cover_`）

**人工确认发布流程（本次会话新增）**：
用户要求**每期视频发布前人工确认** — 完整流水线跑完生成视频后，**不自动分发**，等用户确认 "可以发布" 再执行上传。当前 cron 任务均已暂停，改为手动触发模式。

## 监控流水线自动化 (2026-06-20 新增)

### 触发机制
监控 `/home/kan/shared/signal_pop/filtered_news.json`，检测到新文件即触发完整流水线：
1. 复制到 `/home/kan/signal_pop/data/filtered_news.json`
2. 运行 `generate_script.py daily` → 生成播报脚本
3. 运行 `tts_mimo.py (female)` → 生成女声音频
4. 运行 `tts_mimo.py (male)` → 生成男声音频 (备用)
5. 输出文件到 `/home/kan/signal_pop/output/daily/`
6. 处理完成后，将源文件重命名为 `filtered_news_YYYYMMDD_HHMMSS.json` 归档

### 去重策略
- 使用 **内容 SHA-256 hash** 作为主键去重（而非 mtime）
- 状态持久化到 `/home/kan/signal_pop/.pipeline_state.json`
- 重启后仍能识别已处理文件

### 定时任务建议
```bash
# 每 10 分钟检查一次 (monitor 方式 - 推荐)
*/10 * * * * cd /home/kan/signal_pop && python src/monitor_pipeline.py >> /home/kan/signal_pop/logs/monitor.log 2>&1
```

### 已部署的 Cron 任务 (2026-06-22)
| 任务名 | Job ID | 计划 | 方式 |
|--------|--------|------|------|
| signal-pop-monitor | 9967e8b8c86f | `*/10 * * * *` | Monitor: 监控 shared 目录 filtered_news.json |
| signal-pop-weekly | 7968abe94f69 | `0 9 * * 6` (周六 09:00) | Weekly: 生成带观点的周报 |

**预存 Cron 任务 (脚本方式，保留兼容)**
| 任务名 | 计划 | 方式 |
|--------|------|------|
| signal-pop-daily-news | `30 8 * * 1,3,5` (周一三五 08:30) | 脚本: `scripts/generate_audio_one.sh` |
| signal-pop-weekly-news | `0 9 * * 6` (周六 09:00) | 脚本: `scripts/generate_audio_one.sh weekly` |
| signal-pop-daily-check | `0 9 * * 1,3,5` (周一三五 09:00) | 健康检查 daily-news |

> **优先级**: Monitor 方式 (human-in-the-loop) 为主流程，脚本方式保留作为回退。虾小图在 shared 目录投放 `filtered_news.json` 即触发 monitor 流水线。

### 关键修复记录
- **Bug**: 归档移动文件后尝试 stat 原路径导致 FileNotFoundError
- **Fix**: 先获取 stat 和 hash，再执行移动操作
- **优化**: 去重从 `mtime + hash` 简化为仅 `hash`，避免同一文件不同时间戳被重复处理

### 5. TTS 文本规范化 (2026-06-22 新增)

**问题**: TTS 朗读时 `（-11元）`、`(-9元)` 等括号内负数会被逐字读出（"左括号 负 11 元 右括号"），影响收听体验。

**修复** (`generate_script.py` 新增 `normalize_for_tts()` 函数，在输出前统一处理)：
```python
def normalize_for_tts(text: str) -> str:
    # 1. （-11元）→ 跌11元 （全角括号）
    text = re.sub(r'（-\s*(\d+(?:\.\d+)?)\s*元）', r'跌\1元', text)
    # 2. (-11元) → 跌11元 （半角括号）
    text = re.sub(r'\(-\s*(\d+(?:\.\d+)?)\s*元\)', r'跌\1元', text)
    # 3. （-9元）→ 跌9元 等类似模式（全角/半角）
    text = re.sub(r'（-\s*(\d+(?:\.\d+)?)\s*([元美元%])\）', r'跌\1\2', text)
    text = re.sub(r'\(-\s*(\d+(?:\.\d+)?)\s*([元美元%])\\)', r'跌\1\2', text)
    # 4. （-数字）通用 → 下跌数字
    text = re.sub(r'（-\s*(\d+(?:\.\d+)?)\）', r'下跌\1', text)
    text = re.sub(r'\(-\s*(\d+(?:\.\d+)?)\)', r'下跌\1', text)
    # 5. （+数字）通用 → 上涨数字
    text = re.sub(r'（\+\s*(\d+(?:\.\d+)?)\）', r'上涨\1', text)
    text = re.sub(r'\(\+\s*(\d+(?:\.\d+)?)\)', r'上涨\1', text)
    # 6. 清理重复标点/多余空格
    text = re.sub(r'[。，]{2,}', '。', text)
    text = re.sub(r'\s{2,}', ' ', text)
    return text
```

**处理对照**:
| 原文 | 规范化后 | 说明 |
|------|----------|------|
| `老庙黄金1268元/克（-11元）` | `老庙黄金1268元/克跌11元` | 全角括号 |
| `周生生1263元/克(-9元)` | `周生生1263元/克跌9元` | 半角括号 |
| `（+5%）` | `上涨5%` | 正向变动 |
| `（-100）` | `下跌100` | 无单位通用 |

**验证**: 6月20日新闻重新生成音频，女声/男声均正确朗读 "跌11元"、"跌9元"。

---

## 6. 虾小图新闻稿直接接入 (2026-06-24 新增)

**背景**: 用户要求每期新闻由「虾小图」出稿，Pipeline 直接读取其成品稿，不再自动抓取 RSS。

**实现**:
1. 新增 `parse_xiaoxiaotu.py` — 解析虾小图格式新闻稿
2. 修改 `scripts/generate_audio_only.sh` — 优先读取虾小图稿，回退到 RSS

### 解析器特性 (`src/parse_xiaoxiaotu.py`)
- **文件位置**: `/home/kan/shared/xiaxiaotu/daily_news_latest.txt` (推荐)
- **格式识别**: Emoji 编号 (1️⃣2️⃣...🔟)、圈数字 (①②③...)、普通数字
- **清理**: 移除表情符号、修复双句号、去除 variation selector
- **输出**: TTS 友好纯文本，格式统一为 `第1条，标题。内容。`

### Shell 脚本逻辑 (`scripts/generate_audio_only.sh`)
```bash
# Step 1: 尝试读取虾小图新闻稿
SCRIPT_CONTENT=$(python3 "$PARSE_XIAOXIAOTU" 2>/dev/null || true)

if [ -n "$SCRIPT_CONTENT" ] && [ ${#SCRIPT_CONTENT} -gt 100 ]; then
    USE_XIAOXIAOTU=1  # 成功，跳过抓取/过滤/生成脚本
else:
    USE_XIAOXIAOTU=0  # 回退到原 RSS 流程
    # fetch_news.py → filter_news.py → generate_script.py
fi
```

### 支持的文件位置 (优先级)
1. `/home/kan/shared/xiaxiaotu/daily_news_latest.txt`
2. `/home/kan/shared/xiaxiaotu/daily_news_YYYYMMDD.txt`
3. `/home/kan/shared/signal_pop/xiaoxiaotu_daily_latest.txt`
4. `/home/kan/shared/signal_pop/xiaoxiaotu_daily_YYYYMMDD.txt`

### 文件要求
- UTF-8 编码
- mtime 为当天（用于判断是否为今日稿件）
- 格式见 `/home/kan/signal_pop/XIAOXIAOTU_NEWS.md`

### 定时任务无需变更
现有 Cron 任务直接调用 `scripts/generate_audio_only.sh`，逻辑内部已兼容：
- `signal-pop-daily-news` (02d2c8d722bb): 周一三五 08:30
- `signal-pop-weekly-news` (b231e16a2ec3): 周六 09:00

---

## 7. 播报规格与字幕输出 (2026-06-24 新增)

### Daily（隔天信号弹）
- **频次**：每周一、三、五 08:30
- **条数**：10 则新闻
- **主播**：女声主打 (MiMo xiaoxiao)，男声偶尔随机 (MiMo yunyang)
- **输出目录**：`/home/kan/signal_pop/output/daily/`
  - `signal_pop_daily_latest.txt` — 播报脚本
  - `signal_pop_daily_latest.mp3` — 音频
  - `signal_pop_daily_latest.srt` — **字幕文件 (SRT 格式，新增)**

### Weekly（每周信号弹）
- **频次**：每周六 09:00
- **条数**：约 15 条本周热点新闻 + 主播个人观点评论
- **主播**：男声主打 (MiMo yunyang)，女声偶尔 (MiMo xiaoxiao)
- **输出目录**：`/home/kan/signal_pop/output/weekly/`
  - `signal_pop_weekly_latest.txt` — 播报脚本 (含【个人观点】段落)
  - `signal_pop_weekly_latest.mp3` — 音频
  - `signal_pop_weekly_latest.srt` — **字幕文件 (SRT 格式，新增)**

> 字幕文件与音频/脚本同目录，供视频剪辑直接导入。SRT 时间轴按语音生成时同步生成（需在 tts_mimo.py 增加时间戳输出）。

---

## 7. parse_xiaoxiaotu.py 就绪格式支持与 Emoji 正则修复 (2026-06-24 新增)

**问题**: 虾小图实际输出的新闻稿已是 TTS 就绪格式（`第1条，标题。内容。`），而非预期的 Emoji 编号格式（`1️⃣ 标题\n内容...`）。原解析器按行解析 Emoji 导致识别失败，且 emoji 正则含错误 Unicode 范围 `\U0001F1F1E00-\U00011EFF` 导致中文被误删。

**现象**: `python3 src/parse_xiaoxiaotu.py` 输出乱码 `.%.%.%.%`，原文被清空。

**修复** (`src/parse_xiaoxiaotu.py`):

```python
# 1. 顶层提取通用清理函数，避免重复定义
def clean_text(text: str) -> str:
    """移除表情符号、修复重复标点"""
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map
        "\U0001F1E0-\U0001F1FF"  # flags (修正：移除错误范围 \U0001F1F1E00-\U00011EFF)
        "\U00002700-\U000027BF"  # dingbats
        "\U0001F900-\U0001F9FF"  # supplemental symbols
        "\U00002600-\U000026FF"  # misc symbols
        "\U0000FE00-\U0000FE0F"  # variation selectors
        "]+", flags=re.UNICODE
    )
    text = emoji_pattern.sub('', text)
    text = re.sub(r'。+', '。', text)
    text = re.sub(r'\.+', '.', text)
    return text.strip()

# 2. 入口早期检测就绪格式
def parse_xiaoxiaotu_script(content: str) -> str:
    content = content.strip()
    # 已是 TTS 就绪格式（含"第1条"且"第2条"）
    if '第1条' in content and '第2条' in content:
        return clean_ready_format(content)  # 内部复用 clean_text
    # 否则按行解析 Emoji 格式...
```

**关键点**:
- 错误范围 `\U0001F1F1E00-\U00011EFF` 超出 Unicode 最大值 (0x10FFFF)，导致正则编译异常或误伤中文
- 正确 flags 范围仅 `\U0001F1E0-\U0001F1FF` (Regional Indicator Symbols)
- 就绪格式检测只需 `'第1条' in content and '第2条' in content`，无需完美匹配

**验证**: 修复后 `python3 src/parse_xiaoxiaotu.py` 正确输出 10 条新闻全文，TTS 合成成功。

---

### 8. 手动流水线执行与 tts_mimo.py Bug 修复 (2026-06-26新增)

**背景**: 所有 Cron jobs 已暂停（`signal-pop-daily-news`、`signal-pop-weekly-news`、`signal-pop-monitor`），需手动触发完整流水线生成当日播报。

### 完整手动执行流程

```bash
cd /home/kan/signal_pop

# 1. 抓取新闻 (RSS + 虾小图回退)
python3 src/fetch_news.py
# → 生成 data/raw_feed.json

# 2. 过滤新闻 (或使用虾小图人工稿)
python3 src/filter_news.py
# → 生成 data/filtered_news.json

# 3. 生成播报脚本
python3 src/generate_script.py
# → 生成 output/daily/signal_pop_daily_YYYYMMDD.txt

# 4. TTS 合成 (女声主打)
python3 src/tts_mimo.py "$(cat output/daily/signal_pop_daily_YYYYMMDD.txt)" --voice female \
  --output output/daily/signal_pop_daily_YYYYMMDD_female.mp3

# 5. TTS 合成 (男声备用)
python3 src/tts_mimo.py "$(cat output/daily/signal_pop_daily_YYYYMMDD.txt)" --voice male \
  --output output/daily/signal_pop_daily_YYYYMMDD_male.mp3

# 6. 更新 latest 软链接
cd output/daily
ln -sf signal_pop_daily_YYYYMMDD.txt signal_pop_daily_latest.txt
ln -sf signal_pop_daily_YYYYMMDD_female.mp3 signal_pop_daily_latest.mp3
ln -sf signal_pop_daily_YYYYMMDD_female.srt signal_pop_daily_latest.srt
```

### tts_mimo.py Bug修复

**问题**: `synthesize_long_text()` 返回 `(wav_path, segments)` 元组，但 `__main__` 入口未解包，导致 `convert_to_mp3()` 接收 tuple 而非字符串路径，报错：
```
AttributeError: 'tuple' object has no attribute 'replace'
```

**修复** (`src/tts_mimo.py:324-325`):
```python
# 修复前
wav_path = synthesize_long_text(text, voice_gender=gender, output_path=output)

# 修复后
wav_path, _ = synthesize_long_text(text, voice_gender=gender, output_path=output)
```

**验证**: 修复后女声/男声 TTS 均正常生成 MP3，SRT 字幕同步输出。

### 文本分段逻辑验证

`text_to_segments()` 正确按 `第X条` 模式分段：
- 识别 `第1条、第2条...第7条` 等中文数字/阿拉伯数字条目
- 单条超 500 字自动按句子二次切分
- 开头引导语 (`这里是隔天信号弹...`) 自动作为独立段落
- 6月26日稿件实际分为 8 段，TTS 分段合成成功

### 9. Pipeline优化：每日仅音频+周报含视频 & ffmpeg加速 (2026-06-26新增)

---

## 10. OpenMontage 评估参考 (2026-06-26新增)

**文件**: `references/openmontage-evaluation.md`

OpenMontage (calesthio/OpenMontage, 22k⭐) 是开源 agentic 视频制作系统，与 Signal Pop 架构高度相关：

- **核心管道**: `documentary-montage` (新闻蒙太奇)、`hybrid` (混合素材+生成，对标 HyperFrames)、`clip-factory` (长切短)、`talking-head` (口播)
- **工具覆盖**: 免费素材直连 (Pexels/Pixabay/Archive.org)、CLIP 语义检索、多渲染引擎 (HyperFrames/Remotion/FFmpeg)、专业级动态字幕、TTS 多提供商
- **架构对齐**: Executive Producer 编排 + checkpoint 审批 + 质量门控 + 预算控制 + 技能复用
- **迁移路径**: 三选项 (全量采用/混合替换视频合成/仅借用工具库)，详见参考文件

> 团队已 clone 到 `/home/kan/shared/OpenMontage/` 供现学现用。建议先跑通 documentary-montage 单次测试对比现有输出质量。

## 13. OpenMontage Fast Path 集成实测 (2026-07-01新增)

**背景**: 验证 OpenMontage 核心工具链 (`direct_clip_search` + `video_compose` FFmpeg + Remotion CinematicRenderer) 在无 GPU/无 PyTorch 环境下的端到端可用性，作为 Signal Pop 视频合成层的替代/增强方案。

### 验证结果摘要

| 路径 | 状态 | 适用场景 | 耗时 |
|---|---|---|---|
| `direct_clip_search` (archive_org + wikimedia) | ✅ 通过 | 免费素材获取 | ~30s/查询 |
| `video_compose compose` (FFmpeg) | ✅ 通过 | 素材拼接 + 音乐混音 + ASS字幕 | ~20-40s |
| `Remotion CinematicRenderer` | ✅ 通过 | 文艺蒙太奇、色调分级、动态纹理、标题卡 | ~2min |
| `HyperFrames` | ❌ 不可用 | 动态排版、网页转视频 | - (npm包解析超时) |

### 核心能力对 Signal Pop 的价值

1. **免费素材管道**: `archive_org` + `wikimedia` 免 key、免费、景深丰富 (城市雨夜、自然环境、档案素材)
2. **专业级合成**: FFmpeg 路径标准化转码 (1920x1080@30fps yuv420p)、crossfade 转场、音轨鸭音、ASS 字幕烧录
3. **文艺蒙太奇渲染**: CinematicRenderer 提供冷/钢/虚空色调、信号线纹理、弹簧动画标题卡 — 契合 "隔天信号弹" 品牌调性
4. **双引擎策略**: Daily 用 FFmpeg 快速出片；Weekly/专题用 Remotion 文艺升级

### 迁移接入点 (最小侵入)

```
现有: fetch_news.py → filter_news.py → generate_script.py → tts_mimo.py → generate_video.py (HyperFrames)
替代: fetch_news.py → filter_news.py → generate_script.py → tts_mimo.py/piper_tts.py → 
      direct_clip_search (素材) → video_compose compose (FFmpeg) / CinematicRenderer (Remotion)
```

**关键适配点**:
- TTS 输出 → `video_compose` 的 `audio_path` 或 `edit_decisions.audio.narration`
- 字幕 SRT → 转 ASS → `subtitle_path`
- 选题关键词 → `direct_clip_search` queries (如 "rain city night", "urban neon rain")
- 背景音乐 → Pixabay Music (已有免费源) 或本地素材库

### 实测产出文件 (已归档)
| 文件 | 路径 | 说明 |
|---|---|---|
| FFmpeg 完整版 (含字幕) | `/home/kan/shared/OpenMontage/signal_pop_test/output_rain_full.mp4` | 35s, 9.7MB, 5段+音乐+ASS |
| Remotion 文艺版 | `/home/kan/shared/OpenMontage/signal_pop_test/output_remotion_cinematic.mp4` | 30s, 1.3MB, CinematicRenderer |
| 素材库 | `/home/kan/shared/OpenMontage/signal_pop_test/clips_rain/clips/` | 5个雨夜片段 |
| 音乐 | `/home/kan/shared/OpenMontage/signal_pop_test/music_pixabay.mp3` | Pixabay 免版税 |
| 字幕 | `/home/kan/shared/OpenMontage/signal_pop_test/subtitles_rain.ass` | 中文 ASS 样式 |

详细技术细节见 `mlops/openmontage-video-production` skill 的 `references/openmontage-fastpath-test.md`

**问题**: 原流水线每次都生成视频（ffmpeg `libx264 preset=medium`），导致单次执行超30分钟，超过cron默认180s超时。

**优化方案**：

1. **区分 Daily/Weekly 视频生成** (`scripts/generate_audio_only.sh`)：
   - Daily（周一/三/五）：仅生成音频 + SRT字幕，**跳过视频**
   - Weekly（周六）：生成完整视频（音频 + 字幕 + 背景合成）

2. **ffmpeg编码加速** (`src/generate_video.py`)：
   ```python
   # 修改前
   "-preset", "medium",
   "-crf", "23",
   
   # 修改后
   "-preset", "ultrafast",
   "-crf", "28",
   ```
   - `ultrafast` 编码速度提升 ~10x
   - `crf=28` 画质轻微下降但文件更小，新闻播报场景可接受

3. **实测结果**：
   - 优化前：>30分钟（视频编码瓶颈）
   - 优化后：**1分47秒**完成Daily全流程（含11段TTS分段合成）
   - 远低于cron 180s超时限制

**关键路径记录**

| 文件 | 用途 |
|------|------|
| `src/fetch_news.py` | RSS 抓取 (feedparser 已装好，无需额外安装) |
| `src/filter_news.py` | 过滤/清洗/去重 |
| `src/generate_script.py` | 生成 TTS 就绪脚本 (含 `normalize_for_tts`) |
| `src/tts_mimo.py` | MiMo TTS 合成 + SRT 生成 |
| `src/parse_xiaoxiaotu.py` | 虾小图稿件解析 (优先级高于 RSS) |
| `src/generate_video.py` | 视频合成 (ultrafast preset, 仅Weekly调用) |
| `scripts/generate_audio_only.sh` | 编排脚本 (Daily跳过视频) |
| `output/daily/` | Daily 输出目录 |
| `output/weekly/` | Weekly 输出目录 |

---

## 12. social-auto-upload 多平台分发集成 (2026-06-29新增)

### 背景
Signal Pop 视频生成后需分发到 B站、小红书、快手 (抖音待登录、YouTube CLI 支持但未启用)。使用 `social-auto-upload` (dreammis/social-auto-upload) 统一 CLI 分发。

### 部署位置
- **项目**: `/home/kan/shared/social-auto-upload`
- **CLI**: `sau` (已链接到 venv)
- **自动分发脚本**: `/home/kan/shared/social-auto-upload/auto_publish.py`
- **监控目录**: `/home/kan/shared/her2home/`
- **状态记录**: `/home/kan/shared/her2home/.publish_state.json`

### 分发流程
1. 马小v 产出视频 → `/home/kan/shared/upload/signal_pop_daily_YYYYMMDD.mp4`
2. 手动复制重命名到分发目录:
   ```bash
   cp /home/kan/shared/upload/signal_pop_daily_YYYYMMDD.mp4 /home/kan/shared/her2home/video_YYYYMMDD.mp4
   mv /home/kan/shared/her2home/cover_YYYYMMDD.png /home/kan/shared/her2home/video_YYYYMMDD.png
   ```
3. 用户确认 "可以发布" 后，执行:
   ```bash
   cd /home/kan/shared/social-auto-upload && python auto_publish.py
   ```

### 关键坑点
- **封面命名必须匹配**: `video_YYYYMMDD.png` (非 `cover_` 前缀)，否则报 "缺少封面"
- **JSON 可选**: 缺失时使用默认标题/简介/标签
- **浏览器依赖**: 必须 `patchright install chromium` (非 playwright)，否则小红书/快手上传失败
- **顺序执行**: auto_publish.py 顺序上传 (避免浏览器冲突)，非并行
- **人工确认模式**: 所有 cron 已暂停，每期需用户确认后手动触发分发

### 实测结果 (2026-06-29)
- Bilibili: ✅ 成功 (tid=249 科技/数码，定时次日 08:30)
- 小红书: ✅ 成功 (headless + 封面)
- 快手: ✅ 成功 (headless + 封面)
- 抖音: 待登录 (`sau douyin login --account her2home`)
- YouTube: CLI 支持但 PLATFORMS 未启用，需修改 auto_publish.py 加入 `"youtube"`

### 相关参考文档
- `references/social-auto-upload-deployment.md` — 详细部署记录、CLI 用法、常见问题

---

## 11. Piper TTS 集成替代 MiMo (2026-06-26新增)

**背景**: MiMo TTS API 存在硬性时长限制 (~1s 固定输出，不随文本长度变化)，无法满足 60s+ 新闻播报需求。本地部署 Piper TTS 解决此问题。

### 部署记录

```bash
# 安装
pip install piper-tts

# 下载中文模型 (zh_CN-huayan-x_low, 20MB, 低资源占用)
python3 -c "
from pathlib import Path
from piper.download_voices import download_voice
download_voice('zh_CN-huayan-x_low', Path('/home/kan/shared/OpenMontage/signal_pop_test/piper_models'))
"

# 模型文件
/home/kan/shared/OpenMontage/signal_pop_test/piper_models/
├── zh_CN-huayan-x_low.onnx          # 20MB 模型
└── zh_CN-huayan-x_low.onnx.json     # 配置
```

### 测试结果

| 指标 | MiMo API | Piper (zh_CN-huayan-x_low) |
|------|----------|---------------------------|
| 最大时长 | ~1s (固定) | **62s+ (无限制)** |
| 成本 | API 调用收费 | **免费离线** |
| 中文自然度 | 优 | 良 (可用) |
| 语速控制 | 有限 | `length_scale` 参数 |
| 部署复杂度 | 低 | 中 (需模型下载) |

### 新增工具: `tools/audio/piper_tts.py`

OpenMontage 工具库新增 `PiperTTS` 类，标准工具接口：

```python
from tools.audio.piper_tts import PiperTTS

tool = PiperTTS()
result = tool.execute({
    "operation": "synthesize",
    "text": "欢迎收看隔天信号弹...完整60秒脚本...",
    "output_path": "/home/kan/shared/OpenMontage/signal_pop_test/narration_piper_final.wav",
    "length_scale": 1.1  # 新闻语速略慢
})
# result.data.duration_seconds = 62.3
```

**关键修复**: `SynthesisConfig` 参数名 `noise_w_scale` (非 `noise_w`)

### 完整流水线验证 (OpenMontage)

```
✅ 1. piper_tts (script → narration.wav, 62s)
✅ 2. audio_mixer (narration + silence → mixed.wav, 标准化 -16 LUFS)
✅ 3. direct_clip_search (queries → 4 clips from archive.org/wikimedia)
✅ 4. video_compose (clips + audio → video.mp4, 1080p, crossfade)
✅ 5. ffmpeg subtitles (video + srt → video_subs.mp4, 中文字幕样式)
```

**最终视频**: `/home/kan/shared/OpenMontage/signal_pop_test/final_piper_complete.mp4` (25MB, 62s, 1080p)

### 双引擎策略 (建议)

| 场景 | 推荐引擎 |
|------|----------|
| Daily (10条, ~60s) | **Piper TTS** (本地、免费、无限时长) |
| Weekly (15条+观点, ~3min) | Piper TTS |
| 紧急/临时/高自然度需求 | MiMo API (女声 xiaoxiao / 男声 yunyang) |
| 多语言/特定音色 | ElevenLabs / OpenAI TTS |

---

## 相关参考文档

- `references/openmontage-evaluation.md` — OpenMontage 全面评估、架构对齐、迁移路径选项
- `references/social-auto-upload-deployment.md` — social-auto-upload 多平台自动分发部署记录 (抖音/B站/小红书/快手)
- `references/openmontage-fastpath-test.md` — **无 GPU/无 PyTorch 环境下 fast path 端到端实测记录** (direct_clip_search + video_compose)
- `references/openmontage-tool-patterns.md` — OpenMontage 核心工具调用模式、RPA→Workflow→Agent 架构映射、关键参数速查
- `references/mimo-tts-api.md` — MiMo TTS API 实测记录 (chat/completions 格式、base64 响应、~1s 时长限制、voice 参数)
- `references/piper-tts-setup.md` — Piper TTS 本地部署方案 (离线无限时长、中文模型、SRT 生成、双引擎切换)
- `references/pipeline_runbook.md` — 监控流水线运行记录、关键设计决策、常见问题排查
- `references/cron-job-environment.md` — **Cron 任务环境依赖管理** (缺失 feedparser 等包导致定时任务失败、修复记录、关键路径速查)