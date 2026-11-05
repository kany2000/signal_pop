# Signal Pop 信号弹

> 新闻短视频自动生成管线：**RSS 抓取 → AI 筛选 → 用户审稿 → 配图 → TTS → 视频 → 多平台发布**。

Signal Pop 目前有两条独立产线，面向不同节奏与形态：

> ⚠️ **产线状态（2026-11-02）**：**平日版暂停制作**（用户决定「等有需要再开」），当前**唯一活跃产线 = 周末特别版·信蓝组合**。平日版的代码与素材完整保留，恢复时按「关键约定 → 平日版改造待办」清单执行即可。

| 维度 | 平日版（每周三播出，周二制作）⏸️ | 周末特别版 · 信蓝组合（每周六播出，周五制作）✅ |
|------|----------------|----------------------|
| 形态 | AI 新闻简报（女主播播报） | 双人对话脱口秀（阿信 + 小蓝） |
| 选题 | 10 条（经济2/文旅1/科技3/民生2/体育1/新质生产力1 + 末条固定「AI 使用指南/电脑 AI 新应用」） | 突发置顶 + 本周要闻(无排名) + 本周之最 + 下周看点 + 双主播观点 + 互动话题 |
| 渲染 | ffmpeg 合成（传统管线） | **Remotion** 程序化渲染（`remotion_poc/`） |
| 声音 | 单女声（豆包 / edge-tts 兜底） | 双人（阿信男声报新闻 + 小蓝女声点评，逐段峰值归一化，阿信峰值 0.95 / 小蓝 0.72） |
| 封面 | AI 女主播封面（背景主题每期轮换：hud/aurora/neon/minimal/retro） | 双人封面六风格自动轮换（见下文） |
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
│   ├── fetch_real_images.py       # 真实网图抓取（urllib 静态页，og:image/img 提取 + 下载 1920 宽落地）
│   ├── fetch_real_images_moli.py  # 真实网图探测 Moli 渲染版（JS/懒加载页专用，产原图 URL 清单，下载交给前者）
│   ├── build_weekly_dialogue.py   # 周末版新闻→阿信/小蓝对话稿
│   ├── gen_dual_tts.py            # 周末版双人 TTS（逐段峰值归一化，阿信 0.95 / 小蓝 0.72）
│   ├── gen_weekly_talk_cover.py   # 周末版封面（六风格 + auto 每期轮换 + all 全套模式 + opening 同开场动画风格）
│   ├── gen_weekly_talk_copy.py    # 周末版 8 平台文案
│   ├── gen_weekly_en_srt.py       # 周末版英文外挂字幕（en_US.srt，--rewrap 离线重排）
│   ├── subtitle_layout.py         # 字幕智能排版（auto line-break：中英分词+行首禁则+安全区，移植自 short-video-factory）
│   ├── export_weekly_remotion.py  # 周末版分镜导出 → weekly_segs.json
│   ├── remotion_weekly_build.py   # 周末版 Remotion 渲染 + ffmpeg 合并（CRF26 + loudnorm）
│   ├── render_weekly_segmented.sh # 周末版应急分段渲染（单次渲染被环境回收时续渲染，幂等/可续）
│   ├── export_daily_remotion.py   # 每日版分镜导出 → daily_segs.json + 配图复制到 public/
│   ├── remotion_daily_build.py    # 每日版 Remotion 渲染 + 音频合并（CRF26，支持 --render）
│   ├── gen_daily_en_srt.py        # 每日版英文外挂字幕（en_US.srt，基于音频时长生成）
│   ├── check_publish_ready.py     # 发布前质检（全过才可发布）
│   ├── verify_final_video.py      # 出品自检：视频帧数 vs 分镜期望、音视频时长差、黑帧(>0.5s)与异常长静音(>2.0s)校验（PASS 才交审片）
│   ├── mix_sidechain_bgm.py       # 侧链闪避混音工具（旁白发声 BGM 自动下潜，停顿平滑回弹，-c:v copy 秒级导出）
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
| `SIGNAL_POP_TTS_BACKEND` | TTS 后端：`qwen` / `volcengine` / `xunfei` / `kokoro` / `voxcpm` / `edge` | qwen |
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

- **选题结构**：【特别报道置顶】仅真实重大事件才放 →【本周要闻】无排名播报（本期 17 条，随选题浮动，封面 ITEM_COUNT 变量化）→【本周之最】→【下周看点】→【双主播观点】每条新闻阿信/小蓝各一句 →【互动话题】收尾邀评。题材以民生/科技/经济为主，游戏类配图（如《边缘行者 2》）使用真实官方图，禁止 AI 生成。
- **音量平衡**：`gen_dual_tts.py` 改为**逐段峰值归一化**（阿信峰值 0.95 / 小蓝 0.72，等效相对响度约 +30%）消除忽高忽低与削波；`remotion_weekly_build.py` 的 `merge_audio` 再叠 `ffmpeg loudnorm`（I=-14）统一整片响度。
- **封面六风格 + 每期自动轮换**（`gen_weekly_talk_cover.py`，2026-09-04 扩充，2026-09-12 增 opening + 移除 split，2026-09-13 移除 glitch）：
  - `magazine`：杂志头条风（双人 + 大刊头 TOP3 预告）
  - `neon`：**巨型数字霓虹风**（巨大「本周N条」数字 + 圆形头像 + 霓虹光晕）
  - `newspaper`：报纸头版风（米白纸纹 + 衬线大标题 + 黑白红三色）
  - `popart`：波普漫画风（三色对角撞色 + 半调网点 + 爆炸星框 + 贴纸卡）
  - `variety`：综艺大字报风（渐变底 + 爆炸星 + 超大描边字 + 旋转贴纸标签）
  - `opening`：**与开场动画同视觉**（深蓝底 `#0a0e27` + 青蓝网格 `#37E1FF` + 紫粉辉光 + 漫画速度线/半调网点 + 12角爆炸星 + 霓虹描边标题「信蓝组合/本周N条」+「SIGNAL POP · WEEKLY」+ 底部「MARK哥的创想引擎·出品」，最贴近正片）
  - > ⚠️ `split` 已于 2026-09-12 永久停用（左右分屏风格弃用，不再出现在轮换池）。
  - **轮换机制**：`STYLE=auto`（默认）按制作日 md5 选风格，记录到 `output/used_cover_styles.json`，自动避开最近 2 期不撞款；每种风格内置 2-3 套配色按日期哈希再轮换。头条/条数自动读取本期数据（突发优先，缺失时回退占位）。传 `SUFFIX` 做预览时不写历史记录。
  - **`all` 全套模式**：`STYLE=all` 一次性生成 `COVER_STYLES` 全部风格（文件名带风格后缀，如 `cover_weekly_20260912_opening_16x9.png`），供用户逐期全部出图对比挑选；不污染正式出品名（无后缀规范名 `cover_weekly_<日>_{16x9,4x3,3x4}.png` + `avatar_weekly_<日>.png` 供 check_publish_ready/publish 使用）。
  - **播出日 `PUB_DT` 取制作日所在周的周六**（2026-09-12 固化）：`PUB_DT = PREP + (5 - PREP.weekday()) % 7`，封面「播出日期/星期」自动对齐正片（周五产→次日周六，周六产→当天）；不再写死 `PREP+1`。封面时间品牌统一为「周末」（原「周六 08:00」字样全量改为「周末」）。
  - **条数变量化**：`ITEM_COUNT`（本期 17）+ `CN_COUNT=本周{ITEM_COUNT}条` 取代全文写死的「本周15条」/neon 巨型数字，与正片/文案一致；后续可改为从 `parsed_news` 自动读取。
- **一键三连动画**：订阅/关注/转发金色圆钮 stagger 浮现 + 呼吸光晕，从三连段持续到片尾。
- **视频码率**：Remotion 默认 CRF18 过大（3min ≈ 76MB），统一 `libx264 CRF26`（≈ 26MB）压缩。
- **应急分段渲染**：单次整片渲染在本环境会被后台任务回收时，用 `bash tools/render_weekly_segmented.sh {制作日}` 分段渲染（每段 ~33s）+ 拼接 + 整体 CRF26 重编码；脚本幂等可续，总帧数自动从 `remotion_poc/src/weekly_segs.json` 计算，不硬编码。
- **字幕规则**：中文版**不烧字幕**、不生成中文字幕；仅保留英文外挂 `signal_pop_weekly_{date}.en_US.srt`（海外平台 + 质检用）。英文字幕行经 `tools/subtitle_layout.py` 智能换行（2026-09-12 接入：固定宽度贪心换行、行首禁则标点、中英混排分词，`don't`/`under-display`/`1:00` 等不被拆散，替代原整段单行写法）。
- **8 平台发布矩阵**：抖音 / 快手 / B站（自动代发）+ 小红书 / 知乎 / Facebook / YouTube / Twitter（手动）；视频须经用户最终确认后才发布。
- **快手标题硬上限 28 字**（2026-09-12 实测）：封面标题输入框限制 28 字以内，创作指南建议 15–30 字；描述（`--desc`）只取文案 md 的「简介」字段（≈75 字，500 字以内不触限）。标题务必压在 28 字内留余量（本期已缩至 22 字）。
- **发布前质检**：`python tools/check_publish_ready.py {制作日}` —— 校验视频大小、封面、8 平台文案非空、标题简介、parsed_news 条目数、英文字幕；全部通过方可发布。

### 「大家一起聊经济」收尾环节（huashu-art-motion 代码动画）

周末版正片收尾压轴环节。用户给出经济话题讲义 → AI 浓缩改写为阿信/小蓝双播对话稿（约 600 字 / 2~3 分钟）→ 用户审稿定稿 → 三步产出带动画的成片：

```bash
# 1) 双播音频 + 帧账本
python tools/gen_econ_tts.py {制作日}
# 2) 分镜 spec + huashu 引擎渲染拼接底片
python tools/build_econ_huashu_generic.py {制作日}
# 3) 叠加 V2.1 双主播 HUD + 音轨
python tools/compose_econ_video.py {制作日}
# → output/weekly/{制作日}/econ_talk_{制作日}_huashu.mp4
```

- **配置驱动分镜（2026-11-02 改造）**：分镜不再写死在 Python 里，而是抽到外置 JSON —— `output/weekly/{制作日}/econ_huashu_storyboard.json`（本期专用）或 `tools/econ_huashu_storyboard.template.json`（通用模板）。**稿子段数变了只改配置，不用改代码**。`ratios` 约定：前 N-1 镜写固定比例，末镜写 `0.0` 表示取余量，保证该段帧数总和严格等于 TTS 实测帧数。脚本内置 `lint_y5()` 生成期自检，排版违规直接报错退出。
- ⚠️ `build_econ_huashu.py` 旧版按「固定 11 段」写死，**新期请用 `_generic.py`**。

- **动画引擎**：`huashu-art-motion`（`G:/projects/_dl/huashu/huashu-art-motion-main/scripts/engine`），按真实 TTS 分段帧数拆 5~10s 多镜头，交替 `t1_3b1b`（公式/曲线）、`y3_whiteboard`（白板手绘）、`t3_finance_chart`（财经图表）、`y5_kinetic_type`（动态大字），统一色板 `"theme": "ink"`（深墨底），注入安全边距 `{"top":76,"bottom":128,"left":148,"right":148}`。
- **V2.1 HUD 规格**：左下阿信 / 右下小蓝 `136×136` 贴边圆头像（名牌内嵌在圆头像**下沿**胶囊，严禁放头顶以免遮挡图表来源行），说话者 100% 不透明 + 彩色发光外环，听讲者 45% 半透明暗化；底部中央字幕框单页 ≤25 字，主字号 `42px` 微软雅黑粗体 + `2px` 黑色描边，说话人标签 `36px`。
- **⚠️ `y5_kinetic_type` 排版三铁律**（引擎只告警不报错，须自检）：① 主词 `text` ≤4 汉字（字号固定 300px，5 字以上占满 86% 画宽会撞左上角标签）；② `data.label` ≤3 字（标签固定画在 x=140，是主词的水平避让位）；③ `highlight.data.word` 必须出现在**当前页主词**里（荧光笔只刷主词，辅句词用 `data.key` 着色），否则整下高亮**静默失效**。
- **⚠️ 文稿红线**：① 禁「为什么 XX 集体抛售」式给观众预设概念的设问；② 全稿零操作指引（禁 T+1/逆回购/加减仓/持股/抄底/止盈止损等操作词），只做描述性机制探讨；③ 结尾互动提问纯认知向；④ 必含「不构成任何投资建议，市场有风险，决策需谨慎」合规句。

---

## 平日版改造待办（2026-11-02 调研成型，暂停期间存档）

平日版暂停中，恢复时按此清单执行，无需重新调研：

| # | 改造项 | 现状 → 目标 | 成本 |
|---|--------|--------------|------|
| 1 | **启用 `opinion` 字段** | `parsed_news.json` 每条已预留该字段，`gen_cloud_tts.py:141` 已会播「主播观点：xxx」，但实际条目全为空 → 审稿阶段让 AI 每条填一句「这事跟你有什么关系」，播报从「念新闻」变「有人帮你解读」 | 最低，优先做 |
| 2 | **分档编排破同质** | 15 条全是同一个 `NewsSlide`（约 20s/条）无节奏 → 章节卡（复用周末版 `ChapterOverlay`）+ 头条深挖 1 条（启用闲置的 `EvidenceCard`）+ 快讯 ×10 + 观点金句，总长不变 | 中 |
| 3 | **补 BGM** | 平日版无配乐（周末版有 `mix_sidechain_bgm.py` 侧链闪避），5 分钟干声播报在抖音/小红书掉完播 | 低 |
| 4 | **9:16 竖版常态化** | 仅 20260908 试过一次（`make_vertical.py`/`reframe.py` 现成），抖音/快手/Shorts 主场 | 低 |
| 5 | **历史条改对照式** | 「历史上的今天」改「当年 vs 今天」对照结构（信源零成本，仅改文案结构） | 低 |
| 6 | **数据角标** | 每条标题旁挂 `StatRoll` 滚动数字卡（组件现成），把埋在正文里的数字提出来 | 低 |

---

## 关键约定（长期规则）

- 选题配额与媒体多样性、地域配比（国内/国际）按各产线既定约束执行。
- 「历史上的今天」只用国内事件（科技/文化/民生），且**日期必须与发布日对齐**（= 制作日 + 1），不是制作日。
- 配图：汽车/电子产品优先真实网络图；OS/科技类突出软件系统主题。
- **真实网图探测双工具（2026-10-17 新增）**：静态页用 `python tools/fetch_real_images.py <url> <out.jpg>`（urllib + 正则，自带 CDN 白名单，直接下载 1920 宽落地）；JS 渲染页 / 懒加载页（如百度新闻，urllib 拿不到注入图）用 `python tools/fetch_real_images_moli.py <url>`（Moli 无头浏览器完整渲染，产原图 URL 清单 + 真实尺寸，下载落地交给前者或 curl）。批量：`--input urls.txt` 或 stdin 管道；`--flat --output ...` 合并落盘。反爬挑战页会标记 `challenge_suspected`，选源时排雷。依赖 Moli（`%LOCALAPPDATA%\Moli\bin\moli.exe`）。
- **配图水印铁律**：SenseNova 配图右下角带「日日新 sensenova」水印，**生成后保留原始带水印原图，由用户用工具自行清除**；管线不在配图阶段做任何水印模糊/inpaint 处理。用户清完并确认后，才进入 TTS/视频渲染；视频中用主播头像遮水印位。
- **🔴 渲染前置硬门禁（2026-09-01 固化）**：配图生成后 AI 必须 `present_files` 交用户审图；**在用户明确回「水印已清、可以渲染」之前，禁止调用任何 render 脚本**。TTS 可先跑，但合成视频必须等确认。本期曾因 AI 提前渲染带水印旧图而触发此门禁。
- **每日版视觉规范（12b，2026-09-01 固化）**：`DailyNews.tsx` 字号/头像——新闻标题 `46px`（固定不动）、新闻内容 `36px`、历史内容 `42px`、主播头像直径 `150px`。再微调只改这几处数值，无需重跑 `export_daily_remotion.py`。
- **opening_bg / ending_bg 复用（4a，2026-09-01 固化）**：每期复用同一张背景图，不重复生成；基准母版 `remotion_poc/public/base_opening_bg.jpg` + `base_ending_bg.jpg`，下期制作第 1 步复制到新期 `images/`，`win_pipeline_images.py` 的 `exists→skip` 逻辑自动跳过生成。**仅当用户要求更换时才重新生成**。
- **TTS 中文日期修复（2026-09-01）**：豆包 seed-tts-2.0 对短数字日期「X月Y日」概率性误读为英文；`gen_cloud_tts.py` 的 `_cn_month_day()` 在拼接正文前把「X月Y日」转汉字（九月一日），年份/数量词不动。重合成后 faster-whisper 复检确认无英文串音。
- **发布三坑位（每日版/周末版通用）**：① 抖音必须 `--headed`（无头卡创作平台弹窗，失败且会误以为已发布）；② B站（`sau bilibili`）**不接受 `--headed`**，该参数只给 douyin，传错会 `exit=2`；B站偶发 `invalid peer certificate: Expired`，重试一次即过；③ **重跑整套会重复预约已成功平台**，失败平台只用 `publish_*_{yyyymmdd}_retry_<平台>.py` 单家重试。抖音/快手/B站自动代发（`sau` CLI，账号 `her2home`），知乎/小红书/Facebook/YouTube/Twitter 手动。
- **视频编码对齐**：每日版与周末版统一 `libx264 CRF26`（-preset fast -pix_fmt yuv420p），1080p 约 275kb/s（10 分钟视频 ≈ 22MB）。
- **出品自检（2026-08-30 起，2026-09-21 强化）**：成片交付/发布前必须先跑 `python tools/verify_final_video.py weekly|daily {制作日}` 自检——校验视频帧数 vs 分镜期望（拦截分段渲染残段混入导致的结尾画面缺失）、视频轨 vs 音频轨时长差（拦截定格假播）、文件 sanity；**2026-09-21 借鉴 simontalk 新增黑帧检测（`blackdetect=d=0.5`，>0.5s 异常黑帧）与长静音检测（`silencedetect=n=-45dB:d=2.0`，>2.0s 异常卡死）**；全部 PASS 才可交用户审片。
- **音频侧链闪避混音（2026-09-21 落地）**：通过 `tools/mix_sidechain_bgm.py`（借鉴自 simontalk 商业长片工艺），以人声音轨为 key，说话时 BGM 自动下潜至 0.22，停顿/转场时 350ms 平滑回弹饱满，`alimiter=0.95` 绝不破音；视频轨 `-c:v copy` 保持画面零重编码损耗，秒级完成混音。
- **《大家一起聊经济》证据卡组件（2026-09-21 新增）**：`remotion_poc/src/EvidenceCard.tsx` 原生 React 组件，提供纸张白边内衬、-1.5° 微倾斜、真实深度阴影、Ken-Burns 微缓推镜头与数据来源印章，专用于经济财报图表与分析数据展示。
- **生图后端约定（2026-09-21 最终固化）**：配图及单张/批量生图任务，默认首选 WorkBuddy 内置生图工具（ImageGen / 混元大模型），免外部网络依赖，严格遵守无文字后缀定律与 1536x1024 宽屏（16:9 适配）高画质规格。
- **🧹 发布前清理门禁（2026-09-13 固化）**：每期视频审查通过后、发布各平台前，AI 必须扫描制作留下的系统缓存与不需要文件（渲染中间产物 / remotion_poc/node_modules/.cache / 已发布历史期 output 大视频 / pip·npm 缓存与 %TEMP% / *.bak·*.log 杂散文件），给出「路径+大小+可删理由」清单**经用户确认后才删**，并汇报实际释放空间；当期成片/封面/文案/SRT/分镜 JSON/public 素材/两个指纹 JSON 永不清理。详见发布 skill「第 0 步」。
- 密钥只走 `.env`，禁止硬编码；`output/` 产物与 `*.mp4/*.wav/*.png/*.jpg/*.srt` 按 `.gitignore` 不入库（仅 `remotion_poc/public/` 素材例外放行）。
- **📁 路径动态化铁律（2026-11-02 固化）**：项目已于 2026-11-01 从 `E:/projects/signal_pop` 迁至 `G:/projects/signal_pop`，**所有脚本禁止硬编码盘符**。`tools/` 下统一用 `PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))` 动态推导；`huashu` 引擎等外部依赖用 `os.path.join(dirname(PROJECT_ROOT), "_dl", ...)` 向上回溯定位。**新增脚本一律照此写法**，避免再次迁盘时全线崩溃。
- **🐍 本机 Python 环境（2026-11-02 实测）**：可用解释器为 WorkBuddy 托管 Python 3.13（`C:\Users\Administrator\.workbuddy\binaries\python\versions\3.13.12\python.exe`），已装 `requests` / `Pillow` / `playwright` + Chromium。`external/voxcpm/.venv` 指向已卸载的 Python311（不可用）；`uv` 命令在本机**已不存在**，故 huashu 引擎渲染改为直接用当前解释器跑 `render.py`（只依赖 playwright + 标准库），Chromium 下载走 `PLAYWRIGHT_DOWNLOAD_HOST=https://cdn.npmmirror.com/binaries/playwright`。
- **Windows 子进程 PATH 陷阱（2026-11-02 固化）**：`subprocess` 传 `env={"PATH": ...}` **无效**——Windows 查找可执行文件读的是**进程级**环境块；正解是改 `os.environ["PATH"]`（触发 `SetEnvironmentVariable`）。Git Bash 的 `PATH=xxx:$PATH` 前缀写法会被转成 `G;G:\...` 坏条目，不可用。
- 代码规范：`black --line-length=120`、`flake8`；改动前先完整重读项目（README/scripts/tools/历史）再动手。
- **📦 Skills 沉淀（2026-11-02）**：`~/.workbuddy/skills/` 下三个项目 Skill——
  `signal-pop-weekly-publish`（三平台定时发布 + 清理门禁）、`signal-pop-weekly-render`（周末版渲染→混音→质检→交付全流程）、`signal-pop-econ-huashu`（聊经济动画三步管线 + y5 排版铁律 + 环境坑表）。新增管线能力优先沉淀为 Skill，避免每次重新调研。

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

**渲染环境坑（2026-09-04 期实测，长期有效）**：
- 整片渲染走 `tools/render_weekly_segmented.sh` 分段驱动（500 帧/段）；**并发必须降到 2**，默认 8 会 Out of memory。
- **必须禁用 Chrome 硬件解码**：`--chrome-flags="--disable-accelerated-video-decode --disable-gpu"`。否则渲染到画中画起始帧（如 frame 169）会触发 Chrome 硬解 `PIPELINE_ERROR_DISCONNECTED`，整段渲染静默失败。
- 后台/计划任务方式启动渲染会被宿主回收（实测 54~74s 被杀），**逐段前台渲染**是唯一稳定路径；渲染完成后跑 `verify_final_video.py` 自检 PASS 再交付。
- `tools/_cut_title_audio.py`：豆包配额耗尽时的应急工具——用 silencedetect 定位播报标题与正文重复的静音间隙，直接切割音频去掉重复标题（无需重录 TTS）。

---

## 发布与增长增强工具（Easel 借鉴，2026-09-09）

参考开源社媒 Agent [ZJU-REAL/Easel](https://github.com/ZJU-REAL/Easel) 的技能库，按「不整体迁移、按需借鉴」原则落地以下可离线运行（或待登录态启用）的能力：

### 1. 横竖版转换 `tools/make_vertical.py`
把 16:9 成片转 9:16 竖版喂抖音/快手/视频号（模糊背景填充 + 前景居中，零裁切）。
```bash
python tools/make_vertical.py 20260908                 # fit 模式（默认，零裁切）
python tools/make_vertical.py 20260908 --mode cover    # cover 模式（铺满高度裁左右）
```
输出 `output/daily/{date}/signal_pop_daily_{date}_9x16.mp4`，CRF26 / yuv420p(tv) 与正片一致。

### 2. 合规质检 `tools/quality_gate.py`（参考 Easel quality-gate / risk-scanner）
在 `check_publish_ready.py`（完整性）之外追加**合规风险**扫描：截断残留（行尾「…/...」）、广告法绝对化用语、版权/来源提示。发现 HIGH 风险退出码 1，可接入发布门禁。
```bash
python tools/quality_gate.py 20260908
python tools/quality_gate.py 20260908 --words my_risk_words.txt
```

### 3. 发布通知 `tools/publish_notify.py`（参考 Easel skill-publish-notify）
把发布结果推送到飞书/钉钉/Slack/webhook。未配置 `PUBLISH_NOTIFY_WEBHOOK` 时只打印 payload 不阻塞。
```bash
python tools/publish_notify.py --date 20260908 --dry                 # 预览
python tools/publish_notify.py --date 20260908 --format feishu       # 发送
```

### 4. 多平台自动发布（参考 Easel skill-*-upload，需登录态）
`sau` 已管抖音/快手/B站；补 **小红书 / 知乎 / 微信视频号** 三个 Playwright 发布脚本：
`tools/publish_xhs.py` · `tools/publish_zhihu.py` · `tools/publish_channels.py`，共享基类 `tools/_platform_publisher.py`。
> ⚠️ 强依赖你的平台登录态：先 `playwright install chromium`，再 `python publish_xhs.py --date 20260908 --login` 手动扫码抓状态（存 `cookies/`，已 gitignore），之后方可自动发布。各平台 SELECTORS 为占位实现，站点改版后需实测修正。
> 编排器 `tools/publish_all_daily.py` 串起 sau 三平台 + 三个 Playwright 平台，写 `publish_status.json` 并触发通知。

### 5. 归因复盘 `tools/analytics_postmortem.py`（参考 Easel content-postmortem / data-tracker）
本地可跑：解析 `publish.log` 出各平台成败 + 结合 `parsed_news.json` 做内容盘点 + 复用 `quality_gate` 给出下期改进建议，产出 `postmortem.md`。
真实拉数（`record_snapshot` 从平台后台拉粉丝/播放/互动）为 scaffold，需 Playwright 登录态接入。
```bash
python tools/analytics_postmortem.py 20260908
python tools/analytics_postmortem.py 20260908 --snapshot     # 拉数（需登录）
```

### 6. 片头增强（参考 Easel video-intro-outro，2026-09-24 升级）

开场 `OpeningAnimation.tsx` 现为 **3D 纸张刊头语言**（源自 `EvidenceCard.tsx`）：`perspective(1400px)` + `preserve-3d` 真 3D，纸卡从 `rotateX/rotateY` 倾角与 `translateZ` 纵深「落定」桌面视角，入场后 ±1.6/±2.4° 呼吸浮动；品牌点 `BulletMark` 与背景光环 `BackHalo` 在组件内导出。纸卡语言含纸张白边 / -1.5° 微倾斜 / 真实重投影 / Ken-Burns 微推 / 红色印章 / 来源标头。**突发徽章**已在 `WeeklyTalk.tsx` 改为「热点」。
- **结尾淡出**：开场最后约 0.8s（frames 245→270，`Easing.inOut` 曲线）整体由全亮淡出至黑，平滑接入正片，避免硬切。
- **片尾动画已取消（2026-09-24）**：`EndingCard.tsx` 已删除，最终成片不再含片尾动画；生产管线为 `OpeningAnimation(9s/270帧) + WeeklyTalk(正片)` 顺序拼接（`tools/render_weekly_segmented.sh` 的 `concat_list` 仅含片头 + 各 part）。
- **声音**：开场垫乐取 `output/mp3/Romeo - Winds of Hope - Creative Cut - Piano.mp3` 的 **34–43s 片段（约 9s，纯钢琴）**，由 `render_weekly_segmented.sh` 作为前 9s 头段、TTS 整体延后 270 帧合并。⚠️ 该曲约每 8–12s 有一次强动态涌浪（约 8/20/30/44/56/64/72/80.7s），其中 ~30s 起为带人声/合唱的宽带段——**截取时必须避开，选段后用 `showspectrumpic` 频谱图核验无人声**。独立预览带声用 `remotion_poc/out/opening_romeo.wav` 与预览 mp4 ffmpeg 合并（`-map 0:v:0 -map 1:a:0 -c:a aac -b:a 192k`）。
- **沙箱渲染**：本环境无 Remotion 自带 Chromium，改用系统 Chrome 作 `browserExecutable`，走 `bundle → getCompositions → renderFrames → stitchFramesToVideo`（见 `remotion_poc/render_preview2.mjs`）；`renderMedia()` 在本沙箱会崩，勿用。

### 7. 周末版字幕与交互升级（2026-09-25 升级）
- **短视频滚动翻牌字幕（Paged Flow）**：`WeeklyTalk.tsx` 集成 `PagedDialogue` 智能分句组件，长新闻彻底告别省略号 `……` 截断，按标点语义动态分页并平滑向上推滚翻牌，右上角显示优雅页码胶囊，下方淡显下一句预告。
- **高透毛玻璃气泡**：气泡背景升级为 `rgba(14,20,34,0.68)` + `backdropFilter: blur(14px)`，通透轻盈，配图细节隐隐透出，字幕高对比度清晰可读。
- **换主播接话呼吸停顿**：`gen_dual_tts.py` 合成加入智能间歇机制（换主播接话追加 0.45s 呼吸空停顿、同人句间 0.20s），彻底消除两主播抢话感，对话从容自然。
- **本期精选网址动态注入**：支持从 `parsed_news.json` 自动解析或 `pick_url.txt` 动态配置，彻底告别旧默认网址硬编码，视频内胶囊卡与 8 平台文案动态同步展示（如 `https://fmhy.net`）。

### 8. 视效与深度环节重构（2026-10-02 升级）
- **3D 风格主播全新实装**：阿信与小蓝主播头像全面升级为 3D Pixar 质感三维半身像（圆形无水印裁切），发言外发光与微幅呼吸浮动动效细腻自然，彻底告别旧版平面感。
- **真实突发视频画中画（PiP）动态嵌入**：支持突发大事件本地视频（如 SpaceX 星舰 20s 原生试飞素材）以画中画视频窗形式在画面中景平滑淡入淡出，配合背景大图，打造身临其境的现场感。
- **全片明亮通透画质重构**：
  - `WeeklyTalk.tsx` 配图暗色遮罩透明度由原本厚重的 `0.62` 深度减淡至 `0.15`，彻底释放真实高清配图的纯净色彩与自然层次；
  - 无配图默认背景升级为深蓝渐变科技光晕（`#2a416d` → `#152038`），开场前导段自动挂载 `opening_bg.jpg` 科技演播厅大图底衬。
- **收尾环节「大家一起聊经济」第二期全新落地**：
  - **内容定位**：纯客观机制思辨，严格遵守「不预设概念、无任何操作指引、结尾引导生活」的审稿准则；
  - **1920×1080 满屏清爽科技幻灯**：重构为微透玻璃拟态深蓝卡片，文字图表在 `WeeklyTalk` 中享受 0% 零遮罩纯净透传；
  - **双重黄金安全区**：横向严格收敛在 820px 居中区域（避让左右各 550px 主播 3D 头像呼吸区），纵向上浮留出 270px 空间（避让底部字幕气泡），达成全流程文字零遮挡、零截断。
- **TTS 数字广播口语化更正**：全面建立基数词、百分比、年份与序号的纯汉字口语化规则（如「超过两百种」、「超两千吨」、「四千米」、「一百五十五金」、「七十亿美元」、「十万颗」等），消除阿拉伯数字直读的机械出戏感。

### 9. 2026-10-17 深度重构与工业级演进

#### A. 画中画（PiP）防抖与稳定管线
- **根因终结**：攻克了手机录屏/网络转播源自带的 3:2 Pulldown 恶性跳帧脉冲、手持机位抖动以及 Chromium `objectFit: cover` 亚像素裁切震颤；
- **工业级视频防抖工具 `tools/stabilize_footage.py`**：内置「抽骨去重 (mpdecimate) → 两遍全局运动向量特征追踪与平滑补偿 (vidstab 2-pass, smoothing=30) → 双向光流插值 (minterpolate) 与 16:9 固化」三步法，极端跳变彻底归零；
- **超清连环画轮播相册（方案 A 落地）**：针对极端手抖转播片段，首创将 6 张超清现场定格大图配合 0.5s 高精度 `xfade` 丝滑交叉淡入淡出，物理抖动率绝对为 0%，画面兼具故事丰富度与极度沉稳的高级质感；
- **头像 5Hz 抽搐修复**：将旧版代码中说话者头像高达 5Hz（每秒5次）的高频缩放彻底替换为 0.6Hz、0.012 振幅的平缓微呼吸。

#### B. 广播级口播与时间轴硬对齐
- **体育比分发音纠偏**：在 `build_weekly_dialogue.py` 与 `gen_dual_tts.py` 全链路加入比分正则纠偏，自动将 `7-5、6-4` 替换为汉字口语「7比5、6比4」，彻底消除大模型念成数学减号「七减五」的硬伤；
- **每期开场白不重复（确定性周序号取模）**：候选池由 4 句扩充至 12 句，摒弃随机数轮换，采用 `(周序号 + 主播相角) % 池长` 确定性映射，连续 12 期 100% 零撞车、相邻期零重复；
- **音画与外挂字幕精确卡点**：
  - 最终编码采用 `adelay=9000|9000` 将 TTS 整体延后片头 9 秒，片头铺设优雅钢琴曲（首尾 esin 淡入淡出），彻底解决开场人声提前抢跑；
  - 研发 `tools/offset_srt.py` 专用偏移校准工具，自动将英文外挂字幕整体 +9.0s，首句精准卡点 `00:00:09,000`。

#### C. 「大家一起聊经济」V2.1 代码动画升级
- 全面弃用静态幻灯，采用 `huashu-art-motion` 代码动画引擎动态生成；
- 贴边 136×136 双主播头像（名牌下置防遮挡图表），配合 42px 微软雅黑粗体 + 2px 外描边 HUD 大字幕与 ink 墨黑金绿合规色板；
- 严格落实四条合规红线，末尾标准化免责声明。

#### D. 标准化 Agent Skills 封装（沉淀至 `~/.workbuddy/skills/`）
- **`signal-pop-econ-huashu`**：「大家一起聊经济」全流程工具链（红线校验 → 真实双播 TTS → huashu 代码动画渲染 → V2.1 贴边头像字幕 HUD 合成）；
- **`signal-pop-weekly-render`**：周末版整片自动化装配、分段并发渲染、滤镜时基归一化拼接、双遍 -14 LUFS 响度混音与发布前硬门禁质检全流程管线。

### 10. 本地离线灾备 TTS 引擎（2026-10-22 新增）

云端 API 欠费 / 限流 / 断网时的**零成本本地保底**，与主产线（Gemini 3.8 Flash TTS / 豆包 / Qwen-TTS）并存，互不替代。

| 后端 | 上游 | 许可 | 采样率 | 定位 |
|---|---|---|---|---|
| `kokoro` | hexgrad/kokoro (82M) | Apache-2.0 | 24kHz | 轻量离线灾备 + 英文出海配音 |
| `voxcpm` | OpenBMB/VoxCPM (1.5, 0.6B) | **Apache-2.0（可商用）** | 44.1kHz | 高保真离线灾备 + 声音克隆/音色设计 |

**VoxCPM 接入要点**
- 独立 venv：`external/voxcpm/.venv`（Python 3.11 + torch 2.10.0+cpu），主解释器不装 torch，通过子进程调用 `external/voxcpm/_worker.py`；
- 权重：`external/voxcpm/models/VoxCPM1.5`（1.95GB，已 sha256 校验），来源 ModelScope 直连（13MB/s）；
- 音色走 **Voice Design** 自然语言描述（阿信=沉稳中年男 / 小蓝=明亮年轻女），无需参考音频；
- 比分发音同样走 `7-5 → 7比5` 正则纠偏。

**踩坑与根因（已固化）**
- **Windows access violation 真凶 = 页面文件被固定为 2424MB**：fp32 建模 2B 参数会把提交内存（RAM+pagefile≈28GB）耗尽，分配器拿不到地址空间即报段错误而非 `MemoryError`。修复：`AutomaticManagedPagefile=$true`（系统托管）+ `torch.set_default_dtype(torch.bfloat16)` 建模前切 bf16（内存减半）；
- `optimize=False` 必须传（源码 `torch.compile` 仅支持 CUDA，CPU 上直接抛错）；
- torch 版本对齐上游 `uv.lock` 的 **2.10.0**（pip 默认装到的 2.14.1 未适配）；
- `load_denoiser=False` 跳过降噪器模型下载（省 200MB+ 依赖与一次网络往返）。

**实测性能（本机 i7-8750H / GTX 1050 4GB，CPU 推理）**

| 用例 | 音频 | 耗时 | RTF |
|---|---|---|---|
| 中文新闻句 | 5.60s | 217.7s | 38.87 |
| 中文比分句 | 4.80s | 189.4s | 39.47 |
| 英文句 | 5.92s | 209.1s | 35.33 |

> ⚠️ RTF 35~40 意味着生成整期 12 分钟音频需 7~8 小时，**仅适合应急补条**，不适合整期批量生产。提速路线：换 llama.cpp-omni + GGUF Q8_0，或升级到 12GB+ 显存显卡走 GPU（RTF 可至 0.3）。
>
> 双主播音色区分度客观验证：阿信 vs 小蓝 ZCR 差 45.7%、频谱质心差 17.0%（男声明显更低沉）。

完整部署与踩坑记录见 `docs/voxcpm_local_deploy.md`。

### 11. 2026-11-05 成片硬伤修复（片头静音 / 画中画震动 / 片尾 CTA 消失 → 动画化）

| 问题 | 根因 | 修复 |
|---|---|---|
| 开场 9s 动画无声 | `render_weekly_py.py` 写死 `output/mp3/Romeo...mp3`，该文件从未入库；`opening_anim.mp4` 自带音轨实测 -91dB 静音。历史成片前 9s 的「有声音」经三期互相关验证（corr≈0）是各期不同的 TTS 人声，属旧版口播压片头 bug，不可复用 | `tools/gen_opening_theme.py` 离线合成 9s 新闻片头配乐 → `output/weekly/shared/opening_theme.wav`；可用 `SIGNAL_POP_OPENING_BGM` / `SIGNAL_POP_OPENING_BGM_START` 覆盖为正式 BGM；配乐分支 `volume=1.5` 抵消 `amix` 默认 normalize 的 -6dB |
| 热点画中画严重震动 | 源短视频带硬转场 + 末尾黑帧 + B 帧，Remotion `<Video loop>` 在 headless Chromium 逐帧 seek 时帧定位不稳，叠加循环点闪黑 | `export_weekly_remotion.py` 新增 `build_stable_frames()`：按 `parsed_news.json` 的 `videoTrim` 取稳定段 → `deshake` → 中心裁 4% → 30fps / 372×660 JPEG 序列；`WeeklyTalk.tsx` 改用 `<Img>` 按 `videoLt` 算帧号显示（每帧完全确定），旧期无帧序列自动回退 `<Video>` |
| 片尾「一键三连」消失 → 复审要求动画化 | CTA 只挂在末段，而本期末段落在被 huashu 经济动画整体替换的 577.76~708.92s 区间，Remotion 侧三连图标随画面一起被覆盖；第一版补的静态 PNG 收场卡又被复审指出「没有背景图、不是动画」 | 先在最终编码阶段 `overlay` 收场卡救回画面；再由 `tools/gen_cta_outro.py` 生成 6s / 180 帧动画短片 `cta_outro.mp4`（夜景城市背景缓慢推近 + 三按钮 stagger 弹入点亮 + 点击涟漪 + 三连光波 + 呼吸光晕 + 金粒子 + 文字分层淡入）；`render_weekly_py.py` 优先叠加该短片，`cta_sanlian.png` 仅作兜底，`CTA_DUR` 必须与短片 `DUR` 一致 |

新增配置：`parsed_news.json` 的 breaking 项支持 `videoTrim: [start, end]`（秒）与 `videoLoops`。
新增共享素材（位于清理门禁白名单 `output/weekly/shared/`）：`opening_theme.wav`、`cta_sanlian.png`、`cta_outro.mp4`、`cta_outro_bg.jpg`。

**片尾动画短片**：`python tools/gen_cta_outro.py` → 1920×1080 / 30fps / 6.00s / 无音轨，PIL 逐帧绘制经 rawvideo 管道直喂 ffmpeg（不落 180 张中间 PNG）。背景默认取平日版通用片尾夜景 `remotion_poc/public/base_ending_bg.jpg` 并归档到 `shared/cta_outro_bg.jpg`，可用 `SIGNAL_POP_CTA_BG` 指向任意图覆盖。`render_weekly_py.py` 对视频 CTA 用 `-t CTA_DUR`（**不能** `-loop 1`）+ `format=rgba,setpts` 平移 + 0.45s alpha 淡入。

> 三项均为**导出层 / 后处理层**修复，不动 TTS 与字幕时间轴：换背景图或修画中画只需重渲突发段所在的 part（本期 part00 / part01），片头配乐与 CTA 在最终编码一次生效。

---

## 许可

MIT
