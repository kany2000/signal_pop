---
name: signal-pop-pipeline
description: Signal Pop (隔天信号弹) 新闻管道维护技能。覆盖 RSS 抓取 → 过滤 → 脚本生成 → TTS → 发布的全流程常见问题修复与最佳实践。
tags:
  - signal-pop
  - news-pipeline
  - rss
  - content-filtering
  - chinese-nlp
category: devops
---

# Signal Pop 新闻管道维护

## 管道架构

```
fetch_news.py → filter_news.py → generate_script.py → tts_mimo.py → 发布
     ↓              ↓                ↓               ↓
  RSS源抓取      去重/分类/清洗    播报文本生成      MiMo TTS音频
```

## 常见问题与修复

### 1. HTML 实体未解码 (`&nbsp;`, `&amp;`, `&lt;` 等)

**症状**：生成脚本中出现 `作者&nbsp;|&nbsp;王晗玉`

**修复** (`fetch_news.py`)：
```python
import html
summary = html.unescape(summary)  # 在 re.sub 之后调用
```

### 2. 摘要硬截断导致半句残缺

**症状**：`"此次融资将.."`、`"过..."`

**修复** (`fetch_news.py`) - 智能截断在句号处：
```python
if len(summary) > 300:
    match = re.search(r'[。！？.!?]', summary[:300])
    if match:
        summary = summary[:match.end()]
    else:
        summary = summary[:300]
```

### 3. 垃圾内容混入（体育/娱乐/财经行情/博彩/英文标题）

**症状**：FIFA 世界杯、电影票房、美元指数/期铜价格、博彩广告、未翻译英文标题

**修复** (`filter_news.py`) - 多层过滤：

```python
SPAM_KEYWORDS = [
    # 体育赛事
    "世界杯", "FIFA", "欧冠", "英超", "NBA", "裁判", "进球", "比分", "赛程",
    # 娱乐八卦
    "票房", "电影", "上映", "玩具总动员", "漫威", "迪士尼",
    # 财经行情（非新闻类）
    "美元指数", "期铜", "收盘", "涨停", "北向资金", "LME", "WTI",
    # 博彩/广告
    "点击浏览", "即时更新", "精彩进球", "万勿错过", "竞猜", "赔率",
]

def is_spam(title, summary):
    text = (title + " " + summary).lower()
    for kw in SPAM_KEYWORDS:
        if kw.lower() in text:
            return True
    # 检测全英文/高英文比例标题
    if re.match(r'^[A-Za-z\s\.\,\-\'\?]+$', title.strip()) and len(title) > 5:
        return True
    words = title.split()
    english_words = sum(1 for w in words if re.match(r'^[A-Za-z\.\,\-]+$', w))
    if len(words) >= 4 and english_words / len(words) > 0.7 and not re.search(r'[\u4e00-\u9fff]', title):
        return True
    return False
```

### 4. 繁体中文未转简体（BBC 中文 RSS）

**修复** (`filter_news.py`) - 使用 OpenCC：
```bash
pip install opencc-python-reimplemented
```
```python
from opencc import OpenCC
cc = OpenCC('t2s')
title = cc.convert(title)
summary = cc.convert(summary)
```

## 运行顺序

```bash
cd /home/kan/signal_pop
python3 src/fetch_news.py      # 抓取 → data/raw_feed.json
python3 src/filter_news.py --mode daily --top 10  # 过滤 → data/filtered_news.json
python3 src/generate_script.py daily              # 生成 → archive/signal_pop_daily_YYYYMMDD.txt
```

## 视频生产流水线（完整流程）

### 新闻稿格式：视觉提示词行

**2026-07-12 起新增格式**：每条新闻后新增 `视觉提示词：...` 行，包含英文逗号分隔的场景描述。

处理规则：
- **TTS前必须剥离** — 视觉提示词不能出现在语音播报中。用 `re.sub(r'^.*视觉提示词.*\n?', '', text, flags=re.MULTILINE)` 去除。
- **配图可直接使用** — 英文翻译版prompt可直接用于Pollinations文生图，比`keyword_map`自动匹配更精准。
- 脚本`gen_news_images.py`仍可用，但手动配图应优先使用视觉提示词中的英文prompt。

### 日期铁律

**新闻周日做 → 周一发布 → 视频标注周一日期**
- `DATE` (新闻稿日期、配图目录、TTS文件) = 制作日
- `PUB_DATE` (视频叠文字、封面) = 制作日 + 1天 = 发布日
- Build脚本自动计算 `PUB_DATE = DATE + 1`，无需手动改

### 生产步骤

```bash
cd /home/kan/signal_pop

# 1. 新闻稿确认 → 检查时政人物头衔（当前2026: 特朗普是现任总统，非"前总统"）
less /home/kan/shared/signal_pop/archive/signal_pop_daily_YYYYMMDD.txt

# 2. 配图 — 两条路径
#    路径A（默认/自动）: Pollinations cron → 10张新闻配图
#       cron job "signal-pop-daily-images" (09:30 周日/二/四/五)
#       脚本: /home/kan/shared/signal_pop/scripts/gen_news_images.py
#       输出: archive/img_YYYYMMDD/01.jpg … 10.jpg
#
#    路径B（定制prompt, 手动）: gen_custom_images.py — 硬编码了today日期
#       使用前先改脚本内 today 变量
#       python3 /home/kan/shared/signal_pop/scripts/gen_custom_images.py
#       输出: archive/img_YYYYMMDD/01.jpg … 10.jpg
#
#    opening_bg.jpg 需单独生成（cron不生成开场图）:
#       品牌硬规则（2026-07-09 用户确认）：
#         - 必须显示 "Sign-POP News" 台标
#         - 如有人物，形态必须自然、不得扭曲
#         - "Sign-POP News" 用 PIL 精确叠加（AI 直出文字必糊）
#       每期必须全新开场图（2026-07-12 用户重申）：
#         - 不可复用历史期 opening_bg！用户明确批评"已经用过了"
#         - 场景轮换池：控制室夜景 / 新闻演播室 / 城市天台 / 数据大厅 / 外滩夜景
#       直接用封装脚本：
#       python3 /home/kan/.hermes/skills/devops/signal-pop-pipeline/scripts/gen_opening_bg.py YYYYMMDD
#       # → archive/img_YYYYMMDD/opening_bg.jpg
#       改完 opening_bg 后必须重跑 build_daily_video.py 并重新上传

# 3. TTS — 必须先剥离视觉提示词行！用剥离后的文本
python3 -c "
import re
text = open('/home/kan/shared/signal_pop/archive/signal_pop_daily_YYYYMMDD.txt').read()
clean = re.sub(r'^.*视觉提示词.*\n?', '', text, flags=re.MULTILINE)
open('/tmp/signal_pop_daily_YYYYMMDD_tts.txt', 'w').write(clean)
"
python3 src/tts_mimo.py "$(cat /tmp/signal_pop_daily_YYYYMMDD_tts.txt)" \
  --female \
  --output output/daily/signal_pop_daily_YYYYMMDD.wav \
  --srt output/daily/signal_pop_daily_YYYYMMDD.srt

# 4. 修改 build_daily_video.py 中的 DATE 变量为当天日期，然后构建视频
#    编辑 scripts/build_daily_video.py 第6行 DATE = "YYYYMMDD"
#    build_daily_video.py 写封面为 cover_{DATE}.png → 需手动 cp 为 video_{DATE}.png
#       或先修脚本 HER2HOME_COVER 路径
python3 scripts/build_daily_video.py
# 输出: output/daily/signal_pop_daily_YYYYMMDD_v4.mp4
# 自动复制到: /home/kan/shared/her2home/video_YYYYMMDD.mp4 + cover_YYYYMMDD.png
# cover_YYYYMMDD.png 仅为开场帧截图，不能做视频封面

# 5. 生成模板封面（强制 — 非视频帧截图）
#    封面设计：深蓝渐变背景 + 标题「隔天信号弹」+ 右上日期 + 10条编号新闻列表
#    参考 skill 内「封面生成流程」模板规则。用 NotoSansCJK 字体。
#    输出 /home/kan/shared/her2home/video_YYYYMMDD.png（1920×1080 PNG）
#    文件名必须 video_YYYYMMDD.png（auto_publish.py 按 video_ 同名查找）
#    封面可以且应该和开场图不同

# 6. 生成元数据 JSON
#    /home/kan/shared/her2home/video_YYYYMMDD.json

# 7. 手动运行自动分发（一次性，不要设cron）
cd /home/kan/shared/social-auto-upload && python3 auto_publish.py
# 只跑一次 — 不要设周期性 cron！用户明确要求不要多次触发。
# 分发前必须清理：移走 her2home/ 旧视频文件 + 清理 .publish_state.json
# 抖音在无头服务器需设置环境变量：
export DOUYIN_COOKIE_AUTH_HEADLESS=true
# 如果报 Playwright 浏览器缺失，先查看 sau 用哪个包再装：
#    pip list | grep -iE "playwright|patchright"
#    若用 patchright → python3 -m patchright install chromium
#    若用 playwright  → python3 -m playwright install chromium
```

### 关键坑点表

| 问题 | 根因 | 修复 |
|------|------|------|
| TTS输出文件覆盖 | `--output`没传`.wav`后缀 → JSON覆盖了WAV | 必须 `--output xxx.wav` |
| 渐变画成纯黑 | `draw.rectangle(fill=(0,0,0,α))`画在RGB图上，α被忽略 | 改用 `Image.alpha_composite(RGBA层)` |
| 文字可读性差 | 浅色背景上白色文字看不清 | 9点阴影 `[(±1,0),(0,±1),(±1,±1),(0,2)]` |
| 开场图半黑 | 底部渐变遮住背景 | 渐变仅覆盖左半区域(0-960px) |
| 音画不同步 | proportional估算不准 | TTS返回每段`nframes/framerate`实际时长 |
| 日期标错 | 写了制作日而非发布日 | `PUB_DATE = DATE + 1` 自动计算 |
| 时政头衔错误 | 未核实人物现状 | **必须核查**：当前2026年特朗普是现任总统 |
| auto_publish 扫到旧视频而非新视频 | `.publish_state.json` 中旧视频标记了部分平台失败 → 脚本认为未完成 | 清理状态文件，只保留新 video_YYYYMMDD.mp4 的记录，或清空 `.publish_state.json` 的 `published` 字段重跑 |
| 新闻配图重复 | `keyword_map` 关键词跨条匹配 + URL 无 `seed` 参数 → Pollinations 返回相同图 | 已修：`seed={n*37}` + prompt 追加标题差异化剩余部分 |
| 封面用开场帧截图 | build_daily_video.py 复制开场帧到 `cover_*.png`，用户要求模板封面 | 新增 step 5：独立生成模板封面，不能用开场帧替代 |
| 新闻稿改正文后日期回退 | 编辑新闻稿时可能不小心把已修的「发布日」改回「制作日」 | 每次修改新闻稿后必须复查第1行日期是否对应发布日(DATE+1) |
| 开场图每期重复 | 复用历史期 opening_bg，被用户指出 | 每期全新生成，prompt轮换（控制室/演播室/城市天台/数据大厅/外滩夜景等） |
| 时政地理配图不准确 | 霍尔木兹海峡等地理图用了错误关键词prompt | 国家/地理类配图必须用卫星鸟瞰+强调准确性的prompt，用户会验证 |

### 新闻配图重复问题

**症状**：`gen_news_images.py` 生成的 05.jpg 和 08.jpg 是同一张图
**根因**：
1. `keyword_map` 中 "AI" 同时匹配了第5条(GPT-5)和第8条(欧盟AI调查)，返回相同prompt模板
2. Pollinations URL 没加 `seed` 参数 → 相同prompt返回相同图片
**修复**（已应用至 `gen_news_images.py`）：
- `build_prompt(title)` → `build_prompt(title, index)`，每条prompt追加标题中去除关键词后的剩余部分做差异化
- URL 追加 `&seed={n*37}`，确保相同prompt在不同seed下出不同图
- 脚本已检测已存在文件跳过，可删 `rm 05.jpg 08.jpg` 后重跑

### 封面生成流程（强制）

**封面 = 模板生成，非视频帧截图。** `build_daily_video.py` 复制开场帧到 `cover_*.png` 仅作为内嵌封面，**不能替代**视频封面。

```bash
# 正确封面生成步骤：
# 1. 先配齐 archive/img_YYYYMMDD/ 下 10张配图 + opening_bg.jpg
# 2. 运行 build_daily_video.py → 输出 video_YYYYMMDD.mp4 + cover_YYYYMMDD.png
# 3. 运行 gen_cover.py 生成模板封面（深蓝渐变+标题+10条新闻列表）
#    gen_cover.py 路径: （skill 内 scripts/gen_cover.py）
#    或手动写一个临时脚本，用 NotoSansCJK font 生成
# 4. 通过 cp/write 输出到 /home/kan/shared/her2home/video_YYYYMMDD.png
#    文件名必须是 video_YYYYMMDD.png（auto_publish.py 按 video_ 同名查找）
#    build_daily_video.py 输出 cover_YYYYMMDD.png 不符合要求，需要手动重命名或复制
```

**封面模板规则**（`gen_cover.py` 或手写脚本遵守）：
- 1920×1080 16:9
- 背景：深蓝渐变 (`#0A1628` 起)
- 装饰：右上光晕、左下一角装饰线条
- 主标题：「隔天信号弹」白色粗体 + 蓝色描边
- 副标题：「Signal Pop · 每日硬核资讯」青色
- 右上角：日期 `YYYY.MM.DD` + 星期 + 期数
- 中部：10条新闻编号列表（蓝色圆圈编号 + 白色标题文字）
- 底部品牌行 + 发布信息
- 字体：NotoSansCJK-Bold / NotoSansCJK-Regular（`/usr/share/fonts/opentype/noto/`）

**封面 4:3 铁律**：4:3 封面（1440×1080）**绝不能用 `Image.crop()` 截取 16:9 封面**。用户连续三次纠正「这是截图不是完整的图片」「文字显示不全」「图不完整」。必须用**三区拼接**：从 16:9 网格海报母版 crop(0,0,500,1080)文字区 + crop(500,0,670,1080)网格过渡 + crop(1150,0,1920,1080)人物区，拼到 1440×1080 网格画布。详见 skill `signal-pop-cover` 的「4:3 唯一正确方法」。

### 人脸/身体变形规避 + 场景类型差异化

配图prompt策略：
- **优先选无人物场景**（技术/经济/国内新闻都可做纯场景/设备/图表）
- 必须有人物时：避免正面人脸、避免全身站立（AI画下半身常上下半身错位）
- 人物prompt强制加 `, no people` 反向不够强 → 直接设计为无人物场景
- 外交/政治→建筑外景、会议室内景（无人）
- 社会新闻→场景环境（城市街景、医院、实验室，无人）
- 经济新闻→数据图表、工厂仓库、店面（无人）
- 科技新闻→实验设备、芯片微距、数据中心走廊（无人）
- 体育新闻→球场俯拍全景（小人物可接受，但vision检查变形）
- **10张配图必须有各自不同的场景类型** — 不能多用「赛博隧道/数据中心走廊」风格
  - 反例：#4 AI素养教育、#7 仿生皮肤量产、#10 日元剧震 → 都用了蓝紫隧道风，被用户指出
  - 正例：教室·学校 · 工厂·机械臂 · 日元硬币·金融街天际线 · 球场俯拍 · 芯片微距 · 光伏农场
  - 人为分配：保证每张配图的「场景类别」不同（室内/室外/自然/城市/微距/图表...）
- `vision_analyze` **全量检查所有10张**确认：
  - ❌ 无人脸扭曲、五官错位
  - ❌ 无身体变形（上下半身移位、四肢比例失衡）
  - ❌ 无重复配图（关键词跨条命中+缺seed导致）
  - ❌ 无场景类型雷同（至少每张主场景不同）
  - 发现问题 → 删对应图，换无人物+不同场景的prompt重生成

### 开场/新闻背景图每期多样性规则（2026-07-12 用户明确）

**所有视频背景图每期必须全新，不可复用历史期**。包括：

- **opening_bg.jpg**（开场/结束卡底图）— 用户明确批评"已经用过了"。场景轮换池：控制室夜景 / 新闻演播室 / 城市天台 / 数据大厅 / 外滩夜景
- **新闻播报段背景图** — 主场景始终是"新闻直播间"，但**格调/光影/视角/风格每期不同**，不可复用。至少从以下维度每期变化：
  - 格调：科技蓝光 / 暖色晨光 / 赛博夜景 / 极简白 / 金色落日
  - 光影：顶光 / 侧逆光 / 漫射光 / 霓虹光
  - 视角：广角全景 / 近景主播台 / 俯拍控制室 / 长焦压缩
  - 季相/天气：春秋午后 / 夏日暴雨 / 冬夜飘雪
- 封面图（16:9 海报式）**也每期全新**，不可复用历史期封面

**实现方式**：生成 opening_bg/新闻背景图时，prompt 必须附加随机化的风格参数。示例：
```python
import random, hashlib
date = "20260712"
seed = int(hashlib.md5(date.encode()).hexdigest()[:8], 16)
random.seed(seed)  # 日期不同→seed不同→风格不同

styles = ["cinematic blue neon", "warm golden hour", "cyberpunk night", "minimalist white", "dramatic sunset"]
style = random.choice(styles)
prompt = f"news broadcast studio, {style}, wide angle, ..."
```

### 开场/结束卡规则

- **开场图**：prompt `新闻播报直播间`，绿幕演播室实景，不与其他新闻图重复
- **结束卡**：**共用开场背景图**（opening_bg.jpg），压暗 + 标题 + 日期
- 开场/结束共用同一张「新闻播报直播间」背景，风格统一
- 开场首次生成存放到 `archive/img_YYYYMMDD/opening_bg.jpg`
- **结束卡标题文字固定为「下期见」**（非「明天见」—— 发布频率为周一/三/五，非每日，所以用「下期见」）
- 永久约束：`build_daily_video.py` 中 `draw.text((960, 580), "下期见", ...)` 已固化
- **opening_bg 品牌铁律（2026-07-09）**：必须显示 **"Sign-POP News"** 台标；如含人物，形态不得扭曲。
  用 `scripts/gen_opening_bg.py YYYYMMDD`（PIL 叠加台标，非 prompt 出字）。生成后用 `vision_analyze` 复核：台标可读 + 人物比例自然 + 确为直播间。

### 重生成开场图后必须重渲染

opening_bg 是开场/结束卡底图，已烘焙进 mp4。改 opening_bg.jpg 后：
1. 重跑 `python3 scripts/build_daily_video.py`（DATE 不变，自动读新 opening_bg）
2. 重新上传：
   `curl -X POST -F "file=@/home/kan/shared/her2home/video_YYYYMMDD.mp4" http://10.10.10.30:8080/her2home/`
   及同名 cover_YYYYMMDD.png（POST 目标路径 = 服务器目标目录 `/her2home/`）
3. 上传成功返回 `{"ok": true, "path": "/her2home/..."}`；用 `curl -s -o /dev/null -w "%{http_code}"` 验证 200

### 过期路径提醒

`signal-pop-hyperframes-video` SKILL.md 描述的 HyperFrames 流水线（npx hyperframes、/home/kan/signal_pop/hyperframes、/home/kan/signal_pop/daily 目录）**当前不存在**（2026-07-09 核实：无 hyperframes/ 与 daily/ 目录）。当前真实视频合成是 `scripts/build_daily_video.py`（v4，PIL 逐帧 + ffmpeg concat）。不要按 hyperframes skill 操作。视频合成入口：
- 脚本：`/home/kan/signal_pop/scripts/build_daily_video.py`（改第6行 `DATE`，输出 `output/daily/signal_pop_daily_YYYYMMDD_v4.mp4`）
- 配图：`gen_news_images.py`（cron 09:30）或 `scripts/gen_opening_bg.py`（开场图）
- TTS：`src/tts_mimo.py` → wav + `_segments.json`（音画同步用实际时长）

### 排版规则（v4 最终版）

- 1920×1080，全屏铺底
- 左侧渐变遮罩（alpha 255→0 左半960px + 残余60→0 右半960px）
- 文字：分类标签(带底色) + 粗体标题 + 正文(3行) + 页码 + 来源
- 正文：双层阴影（8方向 + 下偏移9点），fill=(0,0,0,100)
- 页码：`2/10` 格式，右下角
- 底部栏：`隔天信号弹 · YYYY.MM.DD` 左下 + `n/10` 右下
- 日期用 `PUB_DATE_SHORT`（发布日）
- emoji不可用（PIL不支持→替代为金色圆环+实心圆）

### Patchright/Playwright 浏览器未安装（前置检查）

**`sau` 用 `patchright`（非 `playwright`）** — 两个包各自的 chromium 版本不同：
- `playwright 1.60.0` → `chromium-1223`
- `patchright 1.58.2` → `chromium-1208`（`sau` 实际使用的版本）

**症状**：`auto_publish.py` 报错：
```
BrowserType.launch: Executable doesn't exist at /home/kan/.cache/ms-playwright/chromium-1208/chrome-linux64/chrome
Looks like Playwright was just installed or updated.
```

**注意**：先查 `sau` 用的是哪个包：
```bash
pip list | grep -iE "playwright|patchright"
# patchright     1.58.2   ← sau 用这个
# playwright     1.60.0   ← 全局装的新版，版本不同
```
→ 新版 `playwright install chromium` 装的是 `chromium-1223`，但 `sau` 需要 `chromium-1208`。

**修复**（只需跑一次）：
```bash
# 1. 查看 sau 用的是 patchright 还是 playwright
pip show patchright | grep Version

# 2. 用对应的包名安装浏览器
#    如果 sau 用 patchright:
python3 -m patchright install chromium
#    如果 sau 用 playwright:
python3 -m playwright install chromium

# 3. 验证
ls -la /home/kan/.cache/ms-playwright/chromium-*/chrome-linux64/chrome
# 应该有文件

# playwright install 装的是新版 chromium（v1223+），
#    但 patchright 1.58.x 需要 v1208。千万别混用！
#    `pip install playwright && python3 -m playwright install chromium`
#    不会修好 patchright 的报错！
```

### 抖音无头服务器 Missing X Server

**症状**：
```
ERROR:ui/ozone/platform/x11/ozone_platform_x11.cc:257] Missing X server or $DISPLAY
The platform failed to initialize.  Exiting.
```

**根因**：抖音 `cookie_auth()` 函数默认**非无头**启动 Chrome（`headless=False`），因为"抖音无头会撞反爬墙→content/upload 跳登录→误判 cookie 失效"。但在无 X Server 的 headless 服务器上，这条策略直接导致 Chrome 无法启动。

**修复**：
```bash
# 设置环境变量让 cookie_auth 走无头模式
export DOUYIN_COOKIE_AUTH_HEADLESS=true

# 然后运行分发
python3 auto_publish.py
```

该环境变量在 douyin_uploader/main.py 中已内置支持：
```python
use_headless = os.environ.get("DOUYIN_COOKIE_AUTH_HEADLESS", "").lower() in ("1", "true", "yes")
```

**折衷**：强制无头后抖音可能误判 cookie 失效（间歇性），但至少不会崩溃。如果 cookie 被判定无效，需在有桌面的机器上跑 `sau douyin login --account her2home` 重新扫码。

### Chrome/Playwright 无头 Missing X Server 最终修法

即使 `export DOUYIN_COOKIE_AUTH_HEADLESS=true`，patchright 1.58.2 仍启动完整 `chrome` 二进制（需 X11）。

**修法**（一次永久有效）：把 chrome 换成 `chromium_headless_shell`（不需 X）：
```bash
rm -f /home/kan/.cache/ms-playwright/chromium-1208/chrome-linux64/chrome
ln -sf /home/kan/.cache/ms-playwright/chromium_headless_shell-1223/chrome-headless-shell-linux64/chrome-headless-shell \
      /home/kan/.cache/ms-playwright/chromium-1208/chrome-linux64/chrome
```
验证：`/home/kan/.cache/ms-playwright/chromium-1208/chrome-linux64/chrome --headless --no-sandbox --dump-dom https://example.com`

### `--schedule` 引号坑

手动 terminal() 调用时：schedule 引号内空格被 shell 拆分。`--schedule "2026-07-14 08:30"` → `--schedule "2026-07-14"` + 剩余 `08:30` 当无参 arg。auto_publish.py 用 Popen 列表传参安全，只有手动 terminal() 背景调用时出此坑。

### Chrome/Playwright 浏览器缺失替代方案（CDN 超时备用）

当 `python3 -m patchright install chromium` 下载 CDN 超时（国内服务器常见）：
```bash
# 方案1：用系统已安装的 Chrome 做 symlink
# 先查系统 Chrome 路径
which google-chrome chromium chromium-browser
# 预期: /opt/google/chrome/chrome

# 创建 patchright 期望的目录结构并 symlink
# 先查正确的版本号目录（从报错或 ls ~/.cache/ms-playwright/）
ls ~/.cache/ms-playwright/
mkdir -p ~/.cache/ms-playwright/chromium-1208/chrome-linux64
ln -sf /opt/google/chrome/chrome ~/.cache/ms-playwright/chromium-1208/chrome-linux64/chrome

# 验证
/opt/google/chrome/chrome --version
```

**注意**：版本号 (`chromium-1208`) 随 `patchright` 版本变化。从报错信息或 `ls ~/.cache/ms-playwright/` 提取即可。

**先确定 `sau` 用哪个包**：
```bash
pip list | grep -iE "playwright|patchright"
# → 用对应的包名叫 `.cache/ms-playwright/chromium-XXXX/`
```

### auto_publish.py YouTube 特殊处理

YouTube CLI 不支持 `--schedule`。`auto_publish.py` 已内置逻辑：
- YouTube → `--visibility private`（私密发布，手动改公开+设定时）
- 其他平台 → `--schedule YYYY-MM-DD HH:MM`

YouTube Cookie 过期处理：
```bash
sau youtube login --account her2home  # 需有桌面环境的机器扫码
```

## 微信视频号（Tencent）专项坑点（2026-07-12 实战验证）

### Headless 服务端扫码代劳

`conf.py` 设了 `LOCAL_CHROME_PATH`（headless-shell），`_build_launch_kwargs()` 用 `executable_path` 跳过 `channel="chrome"`，**不需 X11**。`sau tencent login` 可本机跑（需 Xvfb）：

```bash
# 1. 启动虚拟显示（如未运行）
Xvfb :99 -screen 0 1280x720x24 &

# 2. 导出 DISPLAY 并登录
export DISPLAY=:99
sau tencent login --account her2home

# 3. 日志输出二维码路径：
#   🖼️ 二维码已经准备好啦，已保存到: ..._login_qrcode_20260712_173119.png
#   🧍 请扫码，小人正在耐心等待登录完成
#
# 4. 把该 PNG 发给用户 → 微信扫码 → 手机确认
#    用 vision_analyze("path/to/qr.png") 检查清晰度后 MEDIA 分享
#
# 5. 扫码后自动登录成功 → cookie 保存，验证
sau tencent check --account her2home  # 应返回 "valid"
```

**二维码刷新坑**：二维码约2分钟过期，`_wait_for_tencent_login` 自动刷新并重存二维码。新 PNG 写同名目录，用 `find ... -newer` 找最新文件。

### Cookie 路径不一致坑（必踩）

`sau tencent login` 存到 `cookies/tencent_{account}.json`（CLI路径），但 `tencent_setup` / `TencentVideo` 上传器读 `cookies/tencent_uploader/{account}`（`_resolve_account_file()` 路径）。登录成功后 cookie 已存但 upload 仍报 "missing or expired"。修：

```bash
cp cookies/tencent_{account}.json cookies/tencent_uploader/{account}
```

反过来也一样——`tencent_setup(handle=True)` 登录后存到 `tencent_uploader/`，但 `sau` 下次检查读 `cookies/tencent_{account}.json`。**两边目录都要拷**。

### Headless cookie_auth 超时坑

`cookie_auth()` 的 `page.wait_for_load_state("networkidle", timeout=15000)` 在服务端 headless 模式加载微信页面慢，15s 或 60s 都超时。改 `wait_for_timeout(8000)` 跳过 networkidle 等待。代码位置：`uploader/tencent_uploader/main.py` line 115。

### 定时发布

微信视频号支持 `--schedule "YYYY-MM-DD HH:MM"`。**第一次上传没加 `--schedule` 会立即发布**，无法事后补定时。必须一开始就带 `--schedule`。

## 关键文件位置

- 源码：`/home/kan/signal_pop/src/`
- 数据：`/home/kan/signal_pop/data/`
- 输出：`/home/kan/signal_pop/output/daily/`, `output/weekly/`
- 配置：环境变量 `MINIMAX_API_KEY`, `MINIMAX_BASE_URL`

## 多平台自动分发组件

- **部署位置**：`/home/kan/shared/social-auto-upload/`
- **核心脚本**：`scripts/auto_publish.py` — 扫描 `/home/kan/shared/her2home/`，读取同名 `.json` 元数据，**顺序分发**到已认证平台，去重记录 `.publish_state.json`
- **登录脚本**：`login_all_platforms.sh` — 一键登录 4 平台 (首次扫码，cookie 持久化)
- **CLI 方式**：`sau douyin upload --account her2home --file <video> --title <title>` 等

### 实战状态 (2026-07-01 实测)
  - **B站** ✅ — 定时发布正常，tid=249 (科技/数码)
  - **快手** ✅ — 需 `--headless` 参数，定时发布正常
  - **YouTube** ❌ — Cookie 过期，需有桌面环境的机器扫码更新
  - **抖音** ✅ — headless-shell symlink + DOUYIN_COOKIE_AUTH_HEADLESS=true
  - **微信视频号** ✅ — 2026-07-12 实战验证，支持定时 `--schedule`
  - **小红书** ❌ — 用户指定不发布
- **Cron 状态**：暂停 (人工触发)，视频生成后手动跑 `python auto_publish.py`

## Signal Pop 配图规则 (强制)

1. **所有配图必须 16:9 横图** (1920×1080 或等比) — BlazeAPI 生成时必须指定 `aspect_ratio=16:9`，禁止 1:1
2. **每期必须不同** — 禁止复用旧封面/配图，每次生成新图
3. **成品保存至共享文件夹** `/home/kan/shared/` (对应 http://10.10.10.30:8080/) 按项目分目录
4. **封面命名规范**：`video_YYYYMMDD.png` (auto_publish.py 按 video 同名查找，`cover_*.png` 会被跳过)
5. **Watermark/logo**：150×150 严格放右下角

### 配图优先级策略（2026-07-14 用户确认 & 实战验证）

**三层降级路径**：

```
Sensenova-u1-fast (2752×1536, 16:9) → Pollinations (1280×720) → image_generate (FLUX, 需 FAL_KEY)
```

已封装在 `/home/kan/shared/signal_pop/scripts/sensenova_client.py` 的 `gen_image()` 中自动降级。
也整合在 `gen_news_images.py` 的 `gen_image()` 中。

### ⚠️ Sensenova API 直接 curl 调用坑

**症状**：`curl -X POST https://token.sensenova.cn/v1/images/generations ...` 返回 `{"error":{"message":"invalid arguments","type":"invalid_request_error","code":"3"}}`

**根因**：shell 中 JSON 的参数转义问题（双引号嵌套、特殊字符等），以及间歇性 `SSL UNEXPECTED_EOF_WHILE_READING`。

**修法**：必须用 Python 脚本（`urllib.request`）调用，**不要用 shell curl 直发**。已封装：
- 单张：`python3 -c "from sensenova_client import gen_image_file; gen_image_file(prompt, out_path, seed=N)"`
- 批量：`gen_news_images.py`（含降级逻辑）

**Sensenova 响应格式**：`{"data": [{"url": "https://..."}]}` → 下载 PNG 转 JPEG

### ⚠️ gen_news_images.py 不匹配新版新闻稿格式

**症状**：运行 `gen_news_images.py` 后 `extract_titles()` 返回 0 条，所有配图跳过。

**根因**：`extract_titles()` 的正则 `r'第\d+条[，,]\s*[^。]+[。，]\s*(.+?)\s*[。，]?\s*$'` 匹配 **旧版单行标题**。新版新闻稿每条含：
- `第N条...标题：XXX。详情：XXX。`（标题在 `标题：` 字段内，不在行首句号后）
- 额外行：`主播观点：...`、`视觉提示词：...`

**修法**：要么更新 `extract_titles()` 正则解析 `标题：(.+?)。`，要么跳过该脚本，直接从视觉提示词手动生图（当前做法）。`build_daily_video.py` 的 `parse_news()` 按 `第N条` 分割工作正常，配图不依赖该函数。

### ⚠️ MiMo TTS 段静默丢失 + SSL 间歇性超时（2026-07-14 关键坑）

**症状**：TTS 运行时部分 segment 报 `SSL: UNEXPECTED_EOF_WHILE_READING` 或 `Read timed out (timeout=60)`。更严重：视频播报**没有开场白**，一开口就是"第1条..."。

**诊断**：用户说"没有开场白" → **不要修视频时长/文字**，先查 TTS 段数：
```bash
python3 -c "import json; s=json.load(open('output/daily/signal_pop_daily_YYYYMMDD_segments.json')); print(f'{len(s)} segments (预期 11)')"
```
预期 11 段(1开场白+10新闻)，实际少 → 开场白段被静默跳过。

**根因**：`synthesize_long_text()` 逐段调 MiMo API，旧代码某段失败时 `except: continue` 静默跳过，不重试、不告警。

**修复**：`tts_mimo.py` 已加自动重试（失败等 2s 重试一次）。重跑 TTS 即可。

**旧代码行为**（已修复）：旧代码某段失败后静默跳过，不重试。结果 WAV 段落数 < 预期，开场白或最后几条新闻丢失。

### 新闻配图生成（Pollinations AI，免费无Key）

- **脚本**：`/home/kan/shared/signal_pop/scripts/gen_news_images.py` — 读取 `archive/signal_pop_daily_YYYYMMDD.txt`，解析10条新闻标题，为每条生成1280×720配图，保存到 `archive/img_YYYYMMDD/`
- **Cron**：`signal-pop-daily-images` (09:00 周一三五，新闻稿出后一小时)
- **技术细节**：必须带 `User-Agent` + `Referer` 头，否则403
- **重复图坑**：相同 prompt 不加 `seed` → Pollinations 返回同图。`keyword_map` 关键词可能跨条命中致多条同prompt。**修**：URL 加 `&seed={n*37}` + `build_prompt(title, index)` 每条追加标题差异化部分
- **免费替代方案**：Bing Image Creator (~15次/天)、Playground AI (500张/天)、Leonardo.ai (150 tokens/天)、Hugging Face Spaces

## 视频命名规范 (自动分发要求)

- 视频：`video_YYYYMMDD.mp4`
- 封面：`video_YYYYMMDD.png`
- 元数据：`video_YYYYMMDD.json` (含 title、tags、description、schedule_time)
- 放入 `/home/kan/shared/her2home/` 目录
- 运行 `python auto_publish.py` 自动分发

## 多平台自动分发 (social-auto-upload)

### 架构
```
马小v出片 → /home/kan/shared/her2home/video_xxx.mp4 + .png + .json
                ↓
         cron (10:30/16:30) 扫描
                ↓
         auto_publish.py 并行分发
                ↓
    ┌─────┬─────┬─────────┬────────┐
    ↓     ↓     ↓         ↓
  抖音   B站   小红书     快手
  定时发布
```

### 部署路径
- 仓库：`/home/kan/shared/social-auto-upload/` (13k⭐ dreammis/social-auto-upload)
- CLI：`sau douyin|bilibili|xiaohongshu|kuaishou ...`
- 登录脚本：`/home/kan/shared/social-auto-upload/login_all_platforms.sh` (首次扫码，cookie 持久化)
- 分发脚本：`/home/kan/shared/social-auto-upload/auto_publish.py`

### 分发脚本逻辑 (auto_publish.py)
1. 扫描 `/home/kan/shared/her2home/*.mp4`
2. 匹配同名 `.png/.jpg` (封面) + `.json` (元数据)
3. 读取 `.publish_state.json` 去重 — **同一文件名绝不重复上传**
4. 并行 `sau` 上传 4 平台 (含 `--schedule "次日 08:30"`)
5. 成功写入状态文件，失败下轮重试

### 元数据 JSON 模板
```json
{
  "title": "隔天信号弹 6.28｜标题",
  "desc": "简介内容...",
  "tags": "隔天信号弹,AI,科技",
  "schedule": "2026-06-29 08:30"
}
```

### auto_publish.py 旧视频污染问题

**症状**：`auto_publish.py` 总是重试旧的 `test_video_*.mp4` 或 `video_20260627.mp4`，不处理当前期视频

**根因**：`.publish_state.json` 中旧视频有部分平台标记失败（如抖音 `false`），且旧 `.mp4` 文件物理存在于 `her2home/` 目录中 → `find_new_videos()` 认为它们未发布完，优先重试

**修复**（两步缺一不可）：
```bash
# 1. 移走旧视频文件（auto_publish 扫描所有 .mp4）
mkdir -p /home/kan/shared/her2home/archive_old
mv /home/kan/shared/her2home/video_2026*.mp4 /home/kan/shared/her2home/archive_old/
mv /home/kan/shared/her2home/video_2026*.png /home/kan/shared/her2home/archive_old/
mv /home/kan/shared/her2home/video_2026*.json /home/kan/shared/her2home/archive_old/

# 2. 清理 .publish_state.json，只保留本期
#    或直接写入仅含本期 video 的记录
```

**预防**：分发前确认 `her2home/` 目录只有本期文件。旧视频集中移入 `archive_old/` 子目录。

### 分发策略（强制：仅手动一次性触发）

- 虾小图产出新闻稿：08:00-08:30
- 视频生成：配图→TTS→build_daily_video.py
- **手动运行 `python auto_publish.py` 一次性分发**
- **绝对不要设周期性 cron** — 用户明确要求不能多次触发
- 如果上传中途失败（如缺 X Server 或 Playwright 未装），按下方「失败修复」步骤处理

### 分发前准备

**小红书不需要发布（2026-07-12 用户明确）**：从 `auto_publish.py` 的 `PLATFORMS` 列表中移除 `"xiaohongshu"`：
```python
PLATFORMS = ["bilibili", "kuaishou", "douyin", "tencent"]
```
重置或编辑 `auto_publish.py` 后检查 PLATFORMS 是否误加了 xiaohongshu。

**微信视频号（tencent）平台**：`auto_publish.py` 的 `PLATFORMS` 列表**必须包含 `"tencent"`**。
```python
PLATFORMS = ["bilibili", "kuaishou", "douyin", "tencent"]
```
**每次首次搭建或重置时检查是否漏了 tencent**。用户明确指出「我让你配好微信的，你忘了？」——不可遗漏。

`auto_publish.py` **扫描 `her2home/` 下所有 `.mp4` 文件**，不区分新旧。旧视频若状态中标记部分平台失败，会挡住新视频。

**分发前执行（每次）**：

```bash
cd /home/kan/shared/her2home

# 1. 移走所有旧视频/封面/元数据（只留本期 YYYYMMDD）
mkdir -p archive_old
mv video_20260*.mp4 video_20260*.png video_20260*.json cover_*.png cover_*.jpg test_*.mp4 test_*.png test_*.json archive_old/ 2>/dev/null

# 2. 验证只剩本期文件
ls -la *.mp4 *.png *.json
# 应该只有: video_YYYYMMDD.mp4 + .png + .json

# 3. 清理 .publish_state.json，只保留本期记录
```

**失败修复（缺一不可）**：
1. 移走旧文件 → `mkdir -p archive_old && mv old_files archive_old/`
2. 清理 `.publish_state.json` 中除本期外的所有条目
3. 确保 Playwright 浏览器已装（见下方）
4. 抖音设置 `export DOUYIN_COOKIE_AUTH_HEADLESS=true`
5. 重新跑 `python3 auto_publish.py`
6. 多次失败仍不通 → 单独看小节「Playwright 浏览器缺失」+「抖音无头服务 Missing X Server」

---

### OpenMontage 评估参考

OpenMontage (calesthio/OpenMontage, 22k⭐, AGPL-3.0) 是开源 agentic 视频制作系统，与 Signal Pop 高度相关：

- **核心管道**: `documentary-montage` (新闻蒙太奇)、`hybrid` (混合素材+生成，对标 HyperFrames)、`clip-factory` (长切短)、`talking-head` (口播)
- **工具覆盖**: 免费素材直连 (Pexels/Pixabay/Archive.org)、CLIP 语义检索、多渲染引擎 (HyperFrames/Remotion/FFmpeg)、专业级动态字幕、TTS 多提供商
- **架构对齐**: Executive Producer 编排 + checkpoint 审批 + 质量门控 + 预算控制 + 技能复用
- **已 clone 到**: `/home/kan/shared/OpenMontage/`

## NotebookLM 集成

notebooklm-py (teng-lin/notebooklm-py, 17.6k⭐) 已部署，可程序化操控 Google NotebookLM。

**安装**：`uv tool install "notebooklm-py[browser]"`
**登录**：无头VPS需 EditThisCookie JSON → Playwright storage_state 转换
**验证**：`notebooklm auth check --test --json` → `"status": "ok"`

### storage_state.json 同步坑（必踩）

**症状**：`notebooklm auth check` 显示 `✓ pass`，但 `notebooklm generate|download` 报 `Authentication expired or invalid`。

**根因**：notebooklm-py 有两处 cookie 文件：
1. 项目目录：`<project>/storage_state.json`（用户用 EditThisCookie 导出后放的）
2. profile 目录：`~/.notebooklm/profiles/default/storage_state.json`（CLI 默认读取）

用户通常只更新项目目录的（EditThisCookie 导出到项目目录），但 CLI 读 profile 目录，两边版本不同→旧的被销毁的 cookie 被使用。

**修复**：复制最新的 storage_state.json 覆盖 profile 目录的：
```bash
cp /path/to/project/storage_state.json ~/.notebooklm/profiles/default/storage_state.json
notebooklm auth check --test --json
notebooklm list  # 应能列出 notebook
```

### `notebooklm download audio` 首次下载失败重试

**症状**：`notebooklm download audio` 报 `Network error downloading lh3.googleusercontent.com/...`，但 file 检查显示是 HTML document（Google 登录页）。

**根因**：第一次获取下载 URL 时有浏览器级重定向到 accounts.google.com。

**修复**（重试即可）：
```bash
notebooklm download audio --latest --force  # 再试一次通常成功
```
如果持续失败，重新同步 storage_state.json 再试。notebooklm 的 download 工具内部用认证 cookie 下载，首次网络波动后重试通常成功。

### NotebookLM 播客 → 视频管线（通用模式）

适用于任何项目（非 Signal Pop 也可用）：

```
Step 1: notebooklm generate audio --format deep-dive --language zh_Hans --wait --timeout 1200 --json
        → 返回 {"task_id": "...", "status": "completed", "url": "..."}

Step 2: notebooklm download audio --latest --force /path/to/output.mp3

Step 3: notebooklm ask "逐条列出本期播客讨论的话题，按时间顺序，每条一句话概括"
        → 获取话题列表

Step 4: 为每话题 + 片头片尾生成配图（Pollinations / image_generate）

Step 5: FFmpeg 合成视频
        - 构建 concat demuxer：片头(10s) → 话题(各20s) → 片尾(10s)
        - 总幻灯片循环时长 = 10+8*20+10=180s
        - 播客通常 ~16min(990s) → 需 `-stream_loop` 循环幻灯片 5-6 次
        - `ffmpeg -y -stream_loop -1 -i slides.mp4 -i podcast.mp3 -c:v libx264 -c:a aac -shortest output.mp4`
        - 幻灯片需 scale+pad 到1920×1080: `-vf "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2"`

常见问题：
- Pollinations 图可能是 768×768 方形 → FFmpeg 必须加 scale/pad 强制 16:9
- 16.5min 播客需 slides 循环 6 次 → 长时间编码需 `timeout >300`
- slides 生成选 `preset ultrafast` + `crf 26`，最终合成也相同 preset

### 对 Signal Pop 管线的影响

| 能力 | 评价 | 替代方案 |
|------|------|----------|
| 中文播客生成 | ✅ 双人对话，15分钟，自然度远优于TTS | 可替代 tts_mimo 做独立播客栏目 |
| 中文问答+引用 | ✅ 自动摘要，有citation | 可替代 generate_script 做新闻摘要草稿 |
| 视频生成 | ❌ 无法控制配图场景 | 不替代现有管线 |
| 声音控制 | ❌ 不能指定主播声音 | 保留 xiaoxiao 女声 |

**结论**：NotebookLM 播客适合作为独立栏目（双人对话播客），但不替代现有 TTS 管线。