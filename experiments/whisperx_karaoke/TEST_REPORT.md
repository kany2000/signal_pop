# Signal Pop · whisperX 逐字高亮字幕 测试报告

> 测试日期：2026-11-05　｜　样本：`20261106` 期主片音轨 `audio/tts.wav`
> 结论定位：**只做测试，不改 20261106 成片、不改正式产线**；正式接入留到下一期。

## 1. 测试目标

验证「用 whisperX 给周末版做真实逐字高亮字幕」是否可行，并跑通一条最小完整链路：
真实 TTS 音频 → 字级时间戳 → 可播放的逐字高亮 demo。

**与常规 whisperX 用法的关键差别**：本项目 TTS 文稿是 100% 已知真值，
所以**不跑 ASR 猜字**，只借 whisperX 的 wav2vec2 强制对齐（forced alignment）
把已知文稿的每个字钉到时间轴上。好处是字幕文字零错字，数字/专名不会被识别错。

## 2. 环境实测（本机）

| 项 | 实测结果 |
| --- | --- |
| Python | 3.13.14（托管版），隔离 venv `G:\temp\signal_pop_whisperx_venv` |
| whisperX | 3.8.6（PyPI 直装成功，全套依赖在 3.13 上均有 wheel） |
| torch / torchaudio | 2.8.0+cpu / 2.8.0+cpu（**PyPI 版是 CPU-only**） |
| GPU | GTX 1660 Ti 6GB 存在，但当前 torch 检测 `cuda_available=False` |
| 模型通道 | huggingface.co 直连不通；10808 代理可用但单连接仅 ~370KB/s；hf-mirror ~95KB/s |
| 模型 | `jonatasgrosman/wav2vec2-large-xlsr-53-chinese-zh-cn`，`pytorch_model.bin` 1217.2MB |
| 下载方案 | 自写 24 线程 Range 分片 + 断点续传，聚合 ~1MB/s，落 `G:\temp\signal_pop_models\wav2vec2-zh-cn` |
| ffmpeg | `bin/ffmpeg-9.0.1-essentials_build/bin/`，libass 可用，微软雅黑渲染正常 |
| NLTK | `punkt_tab` 必须预下载；代理环境要加 `NLTK_ALLOW_PROXIED_URLOPEN=1`（NLTK 默认拒绝代理下载） |

## 3. 测试设计

- 样本：`tts.wav` 的 `0.000–41.693s`，含 3 段（阿信开场 / 小蓝开场 / 厄尔尼诺长报道），
  16kHz 单声道 PCM，由 `prep_sample.py` 切出。
- 对齐输入：`sample_segments.json`（每段带 `start/end/text/speaker`，时间来自
  `audio/tts_segments.json` 累计时长，与主片时间轴严格一致）。
- 对齐：`whisperx.load_align_model(language_code="zh", model_name=<本地模型目录>)` +
  `whisperx.align(..., return_char_alignments=True)`，`HF_HUB_OFFLINE=1` 全程离线。
- 回贴：`align_test.py:reconcile()` 用 `SequenceMatcher` 把模型字级时间贴回**原始文稿**，
  词表外的标点、数字、拉丁字母保留原文并插值补时间；字幕文字不采纳模型识别结果。
- 可视化：`make_demo.py` 产 HTML 交互预览 + ASS 卡拉OK字幕；`burn_demo.py` 烧录 MP4。

## 4. 词表覆盖预估（对正式接入很重要）

对齐模型 `vocab.json` 共 3503 token。对 **20261106 全片 41 段文稿**：

- 总字符 3627，其中汉字 2841、非汉字（标点/数字/拉丁）786
- 733 个不同汉字中，词表外仅 10 个：`慎掐昇窃筛罄赁阈陌颈`
- 样本 41.693s 内 124 个不同汉字 **100% 命中**

→ 绝大多数汉字可直接拿到模型时间戳；词表外字与 786 个非汉字靠插值补齐，
字幕文字仍保持 TTS 原稿不变。

## 5. 实测结果 ✅ 可行

| 指标 | 实测 |
| --- | --- |
| 样本 | 41.693s / 3 段 / 214 字（含 181 字长新闻段） |
| 模型加载 | 47.8s（一次性，本地离线加载） |
| 对齐耗时 | **22.0s，实时率 0.53×**（CPU-only） |
| 字级输出 | 模型给出 214 字级时间戳，与原文字数 1:1 |
| 直接命中 | 189 字（**88.3%**），score 多在 0.85–1.00 |
| 插值补齐 | 25 字（11.7%，主要是标点、数字、℃、拉丁字母） |
| 时间戳质量 | 全局单调递增 True；字时长中位数 0.160s（≈6 字/秒），min 0.020s / max 0.664s，无 >1s 异常 |
| 段边界偏差 | 段首 +0.02～+0.06s，段尾 −0.04～−0.44s（段尾静音，正常） |
| 外推全片 | 708.9s × 0.53 ≈ **约 6.3 分钟**（CPU 即可，无需等 GPU） |

### 产物

| 文件 | 说明 |
| --- | --- |
| `words.json` | 逐字时间戳（下期接入直接消费的数据格式） |
| `align_raw.json` | whisperX 原始对齐结果（排查用） |
| `karaoke_demo.html` | **交互预览**：真实人声 + 逐字三态高亮 + 整句对照切换 + 当前字时间戳 |
| `karaoke_stage_demo.mp4` | 41.693s 真实人声 + ASS 卡拉OK逐字高亮（1920×1080/30fps） |
| `karaoke_raw.ass` / `karaoke.ass` | 样本时间轴 / +9s 片头偏移的 ASS 字幕 |
| `prep_sample.py` / `align_test.py` / `make_demo.py` / `burn_demo.py` / `analyze_words.py` / `fetch_align_model.py` | 可复跑的完整测试脚本 |

### 关键发现（影响正式接入）

1. **不用 ASR 是对的**：已知 TTS 文稿直接喂 align，字幕文字零错字；
   模型只负责把字钉到时间上，词表外的标点/数字由插值补齐且保留原文。
2. **长段必须分页**：181 字长段若整行烧录会溢出画面；ASS 与 HTML 都按
   ≤16 字 / 标点断行，实测 20s 处字幕正常单行显示。
3. **不能叠加在现有气泡上**：把 ASS 字幕直接盖到成片片段上会出现
   「原 PagedDialogue 整句 + 逐字字幕」双层文字。正式接入必须**替换**
   `WeeklyTalk.tsx:958` 的气泡文字渲染，而不是叠一层。
4. **CPU 够用**：实时率 0.53×，全片 6 分钟级别，不必先装 CUDA 版 torch。

## 6. 下期正式接入方案（建议）

1. **数据层**：新增 `tools/gen_word_timestamps.py`，输入 `audio/tts.wav` +
   `audio/tts_segments.json`，输出 `audio/word_timestamps.json`（41 段、每段 `words[]`）。
2. **导出层**：`tools/export_weekly_remotion.py:202` 的 `segs.append()` 增加 `words` 字段，
   写进 `remotion_poc/src/weekly_segs.json`。
3. **渲染层**：`remotion_poc/src/WeeklyTalk.tsx:958` 的 `PagedDialogue` 换成
   `KaraokeDialogue`：按 `localT` 比较 `words[].start/end` 渲染三态
   （已读 / 当前放大发光 / 未读），保留现有分页、安全区、双主播头像。
4. **时间轴**：`words` 用**段内相对时间**（对齐 `localT`），无需 +9s；
   只有烧录 ASS/SRT 到成片时才 +9s 片头偏移。
5. **不要叠加**：现有气泡已显示整句，逐字高亮必须**替换**气泡内文字渲染，
   不能在成片上再叠一层字幕（冒烟测试已验证会出现双层字幕）。

## 7. 风险与成本

- **CPU 对齐全片**：实测 0.53× 实时，全片约 6.3 分钟 + 模型加载 48s，
  可接受；CUDA 版 torch 只是可选加速（GTX 1660 Ti 6GB 够跑，但 PyPI 装的
  是 CPU-only，换 CUDA 需从 `download.pytorch.org` 另装约 2GB）。
- **模型缓存**：1.2GB 模型在 `G:\temp\signal_pop_models\wav2vec2-zh-cn`（离线可用），
  另有约 1.2GB 下载分片缓存 `_parts/`，不进仓库；换机需重新拉取或冷备。
  本次清理分片时被沙箱批量删除保护（≥50 文件）拦下，可手动清理。
- **词表外字 / 数字**：插值时间精度低于对齐字，新闻稿里数字密集段（如「3.2℃」）
  需抽查高亮节奏。
- **中文版不烧字幕**的项目约定不变：逐字高亮是画面内**字幕气泡**的升级，
  英文外挂 SRT 照旧。
