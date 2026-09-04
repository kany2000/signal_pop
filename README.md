# Signal Pop 信号弹

> 新闻短视频自动生成管线：**RSS 抓取 → AI 筛选 → 用户审稿 → 配图 → TTS → 视频 → 多平台发布**。

Signal Pop 目前有两条独立产线，面向不同节奏与形态：

| 维度 | 平日版（每周三播出，周二制作） | 周末特别版 · 信蓝组合（每周六播出，周五制作） |
|------|----------------|----------------------|
| 形态 | AI 新闻简报（女主播播报） | 双人对话脱口秀（阿信 + 小蓝） |
| 选题 | 10 条（经济2/文旅1/科技3/民生2/体育1/新质生产力1 + 末条固定「AI 使用指南/电脑 AI 新应用」） | 突发置顶 + 本周要闻(无排名) + 本周之最 + 下周看点 + 双主播观点 + 互动话题 |
| 渲染 | ffmpeg 合成（传统管线） | **Remotion** 程序化渲染（`remotion_poc/`） |
| 声音 | 单女声（豆包 / edge-tts 兜底） | 双人（阿信男声报新闻 + 小蓝女声点评，逐段峰值归一化，阿信峰值 0.95 / 小蓝 0.72） |
| 封面 | AI 女主播封面（背景主题每期轮换：hud/aurora/neon/minimal/retro） | 双人封面七风格自动轮换（见下文） |
| 发布 | 抖音/快手/B站自动 + 其余手动 | 抖音/快手/B站自动 + 其余手动 |

---

## 项目结构

```
signal_pop/
├── config.py                 # 集中配置管理（路径、API 密钥、样式），.env 覆盖
├── logger.py                 # 统一日志与错误处理
├── styles.py                 # 视频样式/配色主题轮换
├── run_pipeline.py           # 每日版统一管线入口（--weekly / --skip-images）
├── requirements.txt          # Python 依赖
├── src/                      # 每日版核心模块
│   ├── fetch_news.py         # RSS 新闻抓取
│   ├── filter_news.py        # AI 新闻筛选（含红线过滤 win_redline_filter.py）
│   ├── generate_script.py    # 脚本生成
│   ├── generate_video.py     # 视频合成
│   ├── tts_mimo.py / tts_google.py  # TTS（中英混排统一用 MiMo）
│   └── parse_xiaoxiaotu.py  # 小红书解析
├── tools/                    # 工具与脚本（每日版 + 周末版）
│   ├── weekend_pipeline.py        # 周末版主驱动（导出分镜→配图→对话稿→TTS→渲染→封面/文案/质检）
│   ├── weekly_images.py           # 周末版配图（真实网图 + AI 图混合来源）
│   ├── build_weekly_dialogue.py   # 周末版新闻→阿信/小蓝对话稿
│   ├── gen_dual_tts.py            # 周末版双人 TTS（逐段峰值归一化，阿信 0.95 / 小蓝 0.72）
│   ├── gen_weekly_talk_cover.py   # 周末版封面（七风格 + auto 每期轮换）
│   ├── gen_weekly_talk_copy.py    # 周末版 8 平台文案
│   ├── gen_weekly_en_srt.py       # 周末版英文外挂字幕（en_US.srt）
│   ├── export_weekly_remotion.py  # 周末版分镜导出 → weekly_segs.json
│   ├── remotion_weekly_build.py   # 周末版 Remotion 渲染 + ffmpeg 合并（CRF26 + loudnorm）
│   ├── render_weekly_segmented.sh # 周末版应急分段渲染（单次渲染被环境回收时续渲染，幂等/可续）
│   ├── export_daily_remotion.py   # 每日版分镜导出 → daily_segs.json + 配图复制到 public/
│   ├── remotion_daily_build.py    # 每日版 Remotion 渲染 + 音频合并（CRF26，支持 --render）
│   ├── gen_daily_en_srt.py        # 每日版英文外挂字幕（en_US.srt，基于音频时长生成）
│   ├── check_publish_ready.py     # 发布前质检（全过才可发布）
│   ├── verify_final_video.py      # 出品自检：视频帧数 vs 分镜期望、音视频时长差校验（PASS 才交审片）
│   ├── publish_weekly_*.py / publish_daily_*.py  # 各平台发布脚本
│   ├── gen_weekly_publish_assets.py  # 周末版发布素材汇总（封面/文案/字幕打包）
│   ├── gen_cloud_tts.py / gen_srt.py / gen_en_srt.py  # TTS / 字幕通用工具
│   ├── gen_cover*.py / gen_hyperframes_html.py      # 封面 / HyperFrames 渲染
│   └── win_*.py              # Windows 管线批处理脚本
├── scripts/                  # 管线脚本（每日版构建、封面、发布、SadTalker 等）
├── remotion_poc/             # 周末版 Remotion 工程（React + TypeScript）
│   ├── src/
│   │   ├── WeeklyTalk.tsx    # 双人对话脱口秀主组件（配图轮换/一键三连/说话高亮）
│   │   ├── DailyNews.tsx     # 每日版主组件（开场/历史/新闻×N/结尾三连，stagger+ken-burns+标题滑入，开场播报日期打屏+结尾日期盖章动画，头像遮水印）
│   │   ├── Root.tsx / NewsSlide.tsx / index.ts
│   │   ├── weekly_segs.json  # Remotion 消费的分镜数据（export_weekly_remotion.py 产出）
│   │   ├── daily_segs.json   # 每日版分镜数据（export_daily_remotion.py 产出）
│   │   └── news.json
│   ├── public/               # 渲染素材（配图/主播头像，例外放行入库）
│   ├── package.json / remotion.config.ts / tsconfig.json
├── hyperframes/              # HyperFrames 独立渲染管线（5 种布局风格按日期轮换）
├── output/                   # 输出产物（video/封面/文案/字幕，按 gitignore 不入库）
│   ├── daily/{制作日}/
│   └── weekly/{制作日}/
├── archive/                  # 历史新闻脚本归档
└── skills/                   # 技能配置
```

---

## 依赖

- **Python** 3.11+
- **Node.js** 18+（仅周末版 Remotion 渲染需要）
- **ffmpeg** 9.0.1（视频合成/合并，`bin/` 下本地副本）
- 第三方服务：商汤 **SenseNova**（配图）/ **豆包 TTS**（默认，配额耗尽自动切 edge-tts 兜底）

```bash
pip install -r requirements.txt

# 开发依赖（可选）
pip install flake8 black pytest pytest-cov
```

---

## 快速开始

### 1. 配置

复制 `.env.example` 为 `.env` 并填入密钥（**密钥只走 .env，禁止硬编码**）：

```bash
cp .env.example .env
```

关键配置项：

| 环境变量 | 说明 | 默认值 |
|---------|------|--------|
| `SIGNAL_POP_PREP_DATE` | 准备日期 (YYYYMMDD) | 昨天 |
| `SENSENOVA_API_KEY` | 商汤 SenseNova 配图密钥 | 必须设置 |
| `SIGNAL_POP_TTS_BACKEND` | TTS 后端：`doubao` / `edge` | doubao |
| `FFMPEG_PATH` | ffmpeg 可执行文件路径 | bin/ffmpeg-9.0.1 |
| `SIGNAL_POP_LOG_LEVEL` | 日志级别 | INFO |

### 2. 平日版（每周三播出，周二制作）

```bash
# 统一管线入口（跨平台，ffmpeg 分屏传统管线，CRF26）
python run_pipeline.py
python run_pipeline.py --skip-images     # 已有图片时跳过配图
SIGNAL_POP_PREP_DATE=20260821 python run_pipeline.py

# Windows 一键管线
python scripts/win_pipeline_run.py
```

#### 每日版 Remotion 动效管线（当前默认管线）

每日版默认走 Remotion 动效管线（`DailyNews.tsx`：stagger / ken-burns / 标题滑入 / 片头片尾日期打屏 / 主播头像遮水印），由 `render_daily_segmented.sh` 一体化驱动（导出分镜 → 分段渲染 → 拼接 → 合并 TTS 音频 → CRF26 重编码），幂等可续：

```bash
# 0) 先跑 TTS 生成 tts.wav + tts_segments.json（gen_cloud_tts.py）
# 1) 导出分镜数据（parsed_news + tts_segments + 配图 → daily_segs.json + daily_meta.json，配图复制到 public/）
python tools/export_daily_remotion.py 20260901

# 2) 分段渲染 + 合并音频（每段 1000 帧，约 31 分钟；中途被环境回收可重跑续渲）
bash tools/render_daily_segmented.sh 20260901 1000

# 3) 成片自检（帧数 / 音视频时长差 / 文件 sanity），PASS 才交审片
python tools/verify_final_video.py daily 20260901
```

> `Root.tsx` 的 `defaultProps` 由 `export_daily_remotion.py` 写入的 `daily_meta.json`（pubDate / weekday / avatar）自动填充，**禁止硬编码旧日期**（2026-09-01 期曾因此踩坑：片头片尾日期错 + 旧主播头像）。

### 3. 周末特别版（信蓝组合）

```bash
# 1) 导出分镜数据（talk_segments.json + 配图映射 → weekly_segs.json）
python tools/export_weekly_remotion.py 20260821

# 2) 在 remotion_poc/ 用 Remotion（Studio 或 CLI）渲染画面轨（静音 mp4）
cd remotion_poc && npm install   # 首次
#    用 Remotion 渲染 WeeklyTalk 画面轨到输出目录

# 3) 合并双人 TTS 音频 + CRF26 压缩 → signal_pop_weekly_20260821.mp4
python tools/remotion_weekly_build.py 20260821
#    可覆盖码率：python tools/remotion_weekly_build.py 20260821 --crf 30
```

> **应急分段渲染（单次渲染被环境回收时）**：本环境后台长任务会被静默回收，单次 `remotion render` 整片（9 分钟+）可能永远落不了盘。此时改用分段脚本，把整片切成 ~33s 的短段分别渲染、最后拼接 + 整体 CRF26 重编码，规避回收。**幂等可续**：已完成的段自动跳过，任务被回收后重跑即从断点继续。
>
> ```bash
> # 先正常导出分镜（export_weekly_remotion.py），再：
> bash tools/render_weekly_segmented.sh 20260821
> #   可选：bash tools/render_weekly_segmented.sh 20260821 1000   # 每段帧数
> #   可选：CRF=26 bash tools/render_weekly_segmented.sh 20260821  # 覆盖码率
> ```
> 约束：拼接用 `-c copy` 保留各段 Remotion 编码，**最后必须用 libx264 CRF26 整体重编码一遍**（抹平接缝/统一码率），不可纯 concat 不重编码。
> **内置帧数校验**（2026-08-30 起）：每段渲染后、幂等跳过时、拼接后、成片复用前均用 ffprobe 校验帧数，残缺段（如渲染中途被回收留下的半截文件）会判失败并删除，**不会再混入成片**（20260828 期末尾 28s 冻结即此根因）。

> **每日版同样适用分段渲染**：`bash tools/render_daily_segmented.sh {制作日} 1000`（每段 1000 帧，11 段 ×1000 帧 + 拼接 + 合并 `tts.wav` + CRF26 整体重编码）。每日版整段 `remotion render` 在本环境同样会被后台任务回收，必须用分段脚本，禁止整段渲染。
>

---

## 管线流程

```
┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐
│ 抓取新闻 │→│ AI 筛选 │→│ 用户审稿 │→│ 图片生成 │→│  TTS   │→│ 视频渲染 │
│ fetch  │  │ filter │  │ review │  │ images │  │  tts   │  │ render │
└────────┘  └────────┘  └────────┘  └────────┘  └────────┘  └────────┘
                                                            │
              ┌────────┐  ┌────────┐  ┌────────┐            │
  发布输出 ←─│ 文案生成 │←│ 封面生成 │←│ 质检放行 │←───────────┘
  publish    │  copy   │  │  cover  │  │  qc     │
              └────────┘  └────────┘  └────────┘
```

> **铁律**：配图 + 视频两级确认（用户审图、审片通过）后才能发布；发布前必须跑质检。

---

## 周末特别版（信蓝组合）详解

双人对话脱口秀，阿信（男声）报新闻、小蓝（女声）点评，Remotion 程序化渲染。

- **选题结构**：【突发置顶】仅真实重大事件才放 →【本周要闻】无排名播报（~14 条）→【本周之最】→【下周看点】→【双主播观点】每条新闻阿信/小蓝各一句 →【互动话题】收尾邀评。题材以民生/科技/经济为主，游戏类配图（如《边缘行者 2》）使用真实官方图，禁止 AI 生成。
- **音量平衡**：`gen_dual_tts.py` 改为**逐段峰值归一化**（阿信峰值 0.95 / 小蓝 0.72，等效相对响度约 +30%）消除忽高忽低与削波；`remotion_weekly_build.py` 的 `merge_audio` 再叠 `ffmpeg loudnorm`（I=-14）统一整片响度。
- **封面七风格 + 每期自动轮换**（`gen_weekly_talk_cover.py`，2026-09-04 扩充）：
  - `split`：经典左右分屏 + 金色中带（兜底）
  - `magazine`：杂志头条风（双人 + 大刊头 TOP3 预告）
  - `neon`：**巨型数字霓虹风**（巨大「15」+ 圆形头像 + 霓虹光晕）
  - `newspaper`：报纸头版风（米白纸纹 + 衬线大标题 + 黑白红三色）
  - `popart`：波普漫画风（三色对角撞色 + 半调网点 + 爆炸星框 + 贴纸卡）
  - `glitch`：赛博故障风（RGB 错位标题 + 扫描线 + 数据网格，标题区有保护带）
  - `variety`：综艺大字报风（渐变底 + 爆炸星 + 超大描边字 + 旋转贴纸标签）
  - **轮换机制**：`STYLE=auto`（默认）按制作日 md5 选风格，记录到 `output/used_cover_styles.json`，自动避开最近 2 期不撞款；每种风格内置 2-3 套配色按日期哈希再轮换。TOP3 头条自动读取本期 `parsed_news.json`（突发优先，缺失时回退占位）。传 SUFFIX 做预览时不写历史记录。
- **一键三连动画**：订阅/关注/转发金色圆钮 stagger 浮现 + 呼吸光晕，从三连段持续到片尾。
- **视频码率**：Remotion 默认 CRF18 过大（3min ≈ 76MB），统一 `libx264 CRF26`（≈ 26MB）压缩。
- **应急分段渲染**：单次整片渲染在本环境会被后台任务回收时，用 `bash tools/render_weekly_segmented.sh {制作日}` 分段渲染（每段 ~33s）+ 拼接 + 整体 CRF26 重编码；脚本幂等可续，总帧数自动从 `remotion_poc/src/weekly_segs.json` 计算，不硬编码。
- **字幕规则**：中文版**不烧字幕**、不生成中文字幕；仅保留英文外挂 `signal_pop_weekly_{date}.en_US.srt`（海外平台 + 质检用）。
- **8 平台发布矩阵**：抖音 / 快手 / B站（自动代发）+ 小红书 / 知乎 / Facebook / YouTube / Twitter（手动）；视频须经用户最终确认后才发布。
- **发布前质检**：`python tools/check_publish_ready.py {制作日}` —— 校验视频大小、封面、8 平台文案非空、标题简介、parsed_news 条目数、英文字幕；全部通过方可发布。

---

## 关键约定（长期规则）

- 选题配额与媒体多样性、地域配比（国内/国际）按各产线既定约束执行。
- 「历史上的今天」只用国内事件（科技/文化/民生），且**日期必须与发布日对齐**（= 制作日 + 1），不是制作日。
- 配图：汽车/电子产品优先真实网络图；OS/科技类突出软件系统主题。
- **配图水印铁律**：SenseNova 配图右下角带「日日新 sensenova」水印，**生成后保留原始带水印原图，由用户用工具自行清除**；管线不在配图阶段做任何水印模糊/inpaint 处理。用户清完并确认后，才进入 TTS/视频渲染；视频中用主播头像遮水印位。
- **🔴 渲染前置硬门禁（2026-09-01 固化）**：配图生成后 AI 必须 `present_files` 交用户审图；**在用户明确回「水印已清、可以渲染」之前，禁止调用任何 render 脚本**。TTS 可先跑，但合成视频必须等确认。本期曾因 AI 提前渲染带水印旧图而触发此门禁。
- **每日版视觉规范（12b，2026-09-01 固化）**：`DailyNews.tsx` 字号/头像——新闻标题 `46px`（固定不动）、新闻内容 `36px`、历史内容 `42px`、主播头像直径 `150px`。再微调只改这几处数值，无需重跑 `export_daily_remotion.py`。
- **opening_bg / ending_bg 复用（4a，2026-09-01 固化）**：每期复用同一张背景图，不重复生成；基准母版 `remotion_poc/public/base_opening_bg.jpg` + `base_ending_bg.jpg`，下期制作第 1 步复制到新期 `images/`，`win_pipeline_images.py` 的 `exists→skip` 逻辑自动跳过生成。**仅当用户要求更换时才重新生成**。
- **TTS 中文日期修复（2026-09-01）**：豆包 seed-tts-2.0 对短数字日期「X月Y日」概率性误读为英文；`gen_cloud_tts.py` 的 `_cn_month_day()` 在拼接正文前把「X月Y日」转汉字（九月一日），年份/数量词不动。重合成后 faster-whisper 复检确认无英文串音。
- **发布三坑位（每日版/周末版通用）**：① 抖音必须 `--headed`（无头卡创作平台弹窗，失败且会误以为已发布）；② B站（`sau bilibili`）**不接受 `--headed`**，该参数只给 douyin，传错会 `exit=2`；B站偶发 `invalid peer certificate: Expired`，重试一次即过；③ **重跑整套会重复预约已成功平台**，失败平台只用 `publish_*_{yyyymmdd}_retry_<平台>.py` 单家重试。抖音/快手/B站自动代发（`sau` CLI，账号 `her2home`），知乎/小红书/Facebook/YouTube/Twitter 手动。
- **视频编码对齐**：每日版与周末版统一 `libx264 CRF26`（-preset fast -pix_fmt yuv420p），1080p 约 275kb/s（10 分钟视频 ≈ 22MB）。
- **出品自检（2026-08-30 起）**：成片交付/发布前必须先跑 `python tools/verify_final_video.py weekly|daily {制作日}` 自检——校验视频帧数 vs 分镜期望（拦截分段渲染残段混入导致的结尾画面缺失）、视频轨 vs 音频轨时长差（拦截定格假播）、文件 sanity；**PASS 才可交用户审片**。
- 密钥只走 `.env`，禁止硬编码；`output/` 产物与 `*.mp4/*.wav/*.png/*.jpg/*.srt` 按 `.gitignore` 不入库（仅 `remotion_poc/public/` 素材例外放行）。
- 代码规范：`black --line-length=120`、`flake8`；改动前先完整重读项目（README/scripts/tools/历史）再动手。

---

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

style = get_style_for_date("20260821")
```

### 周末版 Remotion 渲染

`remotion_poc/` 为 React + TypeScript 工程，`WeeklyTalk.tsx` 消费 `weekly_segs.json`（每段含文本、背景图、时长）。`tools/remotion_weekly_build.py` 负责将 Remotion 渲染出的静音画面轨与双人 TTS 音频合并，并做 CRF26 压缩。

---

## 许可

MIT
