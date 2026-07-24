---
name: signal-pop-windows-video-pipeline
description: Windows 本地一键新闻视频渲染管线。解析稿件→Sensenova 配图→edge-tts TTS→PIL v4 帧合成→ffmpeg filter_complex 精确编码。
author: Claude Code
version: 1.0.0
tags: [signal-pop, video, pipeline, windows, ffmpeg, tts]
related_skills: [signal-pop-news-video-pipeline, signal-pop-news-pipeline, signal-pop-audio-only-pipeline]
---

# Signal Pop Windows Video Pipeline

Windows 本地运行的全自动新闻视频渲染管线，无需 Linux 服务器。

## 架构

```
archive/signal_pop_*.txt  →  win_pipeline_parse.py   → parsed_news.json
parsed_news.json          →  win_pipeline_images.py  → images/*.jpg (Sensenova/Pollinations)
parsed_news.json          →  win_pipeline_tts.py     → audio/tts.wav + tts_segments.json
items + images + audio    →  win_pipeline_video.py   → signal_pop_*.mp4
```

## 前置条件

- Python 3.11+ with: Pillow, edge-tts, asyncio
- ffmpeg 8.1+ (需要 ffmpeg.exe 和 ffprobe.exe 在同一目录)
- 中文字体: Microsoft YaHei / SimHei / SimSun

## 核心文件

| 脚本 | 功能 |
|------|------|
| `scripts/win_pipeline_parse.py` | 解析新闻稿 → 结构化 JSON |
| `scripts/win_pipeline_images.py` | Sensenova API 配图 + Pollinations 降级 |
| `scripts/win_pipeline_tts.py` | edge-tts 分段 TTS + 静音修剪 + PCM 拼接 |
| `scripts/win_pipeline_video.py` | PIL v4 帧合成 + ffmpeg filter_complex 编码 |
| `scripts/win_pipeline_run.py` | 一键调度全部步骤 |

## 踩坑记录

### 1. AV 同步 — 边缘静音偏移 (CRITICAL)

**根源:** edge-tts 输出 MP3，ffmpeg 解码为 WAV 时引入 ~0.22s encoder delay（前导静音）。若直接用 WAV 时长做帧长，每段 TTS 的语音实际偏移 0.22s，积累到第15条新闻时偏差达 3s+。

**现象:** 画面已切到下一条新闻，上一条的语音还在播。

**修复:** 分段 TTS → MP3 → WAV → trim_silence() 切除前后静音 → 纯 PCM 拼接。

```python
def trim_silence(wav_path, threshold=200):
    # 找到第一个/最后一个 amplitude > threshold 的样本
    # 只保留中间的有效语音段
    # 返回 trimmed WAV 路径和实际语音时长
```

### 2. ffmpeg concat 精度陷阱

**现象:** 即便 TTS 时长精确到 0.001s，ffmpeg concat demuxer 在 25fps 下强制四舍五入到 0.04s，每帧误差 0.02s。

**修复:** 不用 concat demuxer，改用 `-loop 1 -r 100 -t DUR` 逐帧输入 + filter_complex concat + `fps=25` 输出。100fps 精度 0.01s。

```bash
ffmpeg \
  -loop 1 -r 100 -t 10.530 -i opening.png \
  -loop 1 -r 100 -t 26.690 -i slide_001.png \
  ... \
  -loop 1 -r 100 -t 9.720 -i ending.png \
  -i audio.wav \
  -filter_complex "[0:v]...[16:v]concat=n=17:v=1:a=0[outv];[outv]fps=25[out]"
  -map "[out]" -map 17:a -c:v libx264 -preset veryfast -crf 24 -t TOTAL_DUR output.mp4
```

### 3. TTS 分段生成可靠性

**问题:** 逐段顺序调用 edge-tts 时，长段（>200 chars）偶发超时挂死。

**修复:** 3 路并发 asyncio.Semaphore，所有段同时发起请求，总体等待。

```python
sem = asyncio.Semaphore(3)
tasks = [gen_one_segment(i, l, t, VOICE, sem) for i, (l, t) in enumerate(segs)]
results = await asyncio.gather(*tasks)
```

### 4. 配图文字乱码

**问题:** 直接用新闻标题做 prompt → AI 生图包含乱码文字。

**修复:** 每条新闻配独立场景 prompt，末尾加 `no text, no words, no labels, clean image`。

### 5. 板块检测失效

**问题:** `re.match(r'【.+?】', line)` 匹配不到 `**【科技与产业】**`（开头有 `**`）。

**修复:** 改用 `re.search`。

### 6. TTS DNS 解析失败 (Windows)

**问题:** edge-tts 在 Windows 上偶发 `Could not contact DNS servers` 错误。

**修复:** 使用 `aiohttp.TCPConnector(resolver=aiohttp.resolver.ThreadedResolver())` 替代默认 c-ares 解析器。

```python
conn = aiohttp.TCPConnector(
    resolver=aiohttp.resolver.ThreadedResolver(),
)
communicate = edge_tts.Communicate(text, voice, connector=conn, connect_timeout=30, receive_timeout=120)
```

### 7. 主播观点字段前缀 `*` 残留

**问题:** 来源文本 `👉 *[主播观点]*：评论内容` → 解析后 opinion 字段以 `*：` 开头。

**修复:** `win_pipeline_parse.py` 中 `opinion_text.lstrip('*：: ')` 去除标点前缀。

### 8. 封面图女主播面孔重复

**问题:** Unsplash 固定池中照片轮替完会重复出现。

**修复:** 改用 Pollinations AI 实时生成主播头像，每次不同 seed 确保不重复。见 `scripts/gen_weekend_cover.py`。

## 一键运行

```bash
python scripts/win_pipeline_run.py
```

自动执行:
1. 解析 `archive/signal_pop_weekly_special_YYYYMMDD.txt` → 15 条结构化新闻
2. 生成配图（已有则跳过）
3. 17 段 TTS（并发 3 路，切除静音，PCM 拼接）
4. 合成视频（filter_complex, 100fps 精度, AV 同步 0.00s）

## 输出

```
output/weekly_YYYYMMDD/
├── parsed_news.json          # 结构化新闻
├── images/                   # 配图 (opening_bg + 01-15 + ending_bg)
│   └── SRT 字幕
├── audio/
│   ├── tts.wav               # 拼接后的完整音频
│   └── tts_segments.json     # 17 段实际时长
├── frames_exact/             # PIL 生成的帧 PNG
└── signal_pop_weekly_special_YYYYMMDD.mp4  # 最终视频
```