---
name: signal-pop-daily-video
description: Signal Pop 每日新闻视频生产流水线（2026-07 现行可用）— 新闻稿txt → 配图(Pollinations AI) → TTS(MiMo) → build_daily_video.py 渲染(PIL/FFmpeg) → HTTP上传 → (分发)。
tags: [signal-pop, video-pipeline, daily-video, video-generation, image-generation, tts, ffmpeg, OpenMontage]
trigger: 用户说 "做视频" / "渲染" / "发片" / "视频出错" / "修复视频" / "配图" 等
---

# Signal Pop 每日新闻视频生产流水线 (2026-07 现行)

**状态**：✅ 2026-07-09 验证定型，涵盖配图、TTS、渲染、上传及 Playwright 浏览器兼容问题；✅ 2026-07-10 修复发布日期：脚本生成/TTS 阶段已改为「制作日+1天」作为视频开头播报日期（news 制作于周日/二/四/五，视频标注发布日=制作日+1）。✅ 2026-07-12 新增「视觉提示词」格式支持、开场图每期换新规则、风格轮盘主题切换、地理配图准确性要求。

## 核心铁律（2026-07-12 新增/重申）

### 1. 视觉提示词「视觉提示词」行
新闻稿可能含 `视觉提示词：` 行（中文关键词供文生图用）。
- **TTS 输入必须剥掉**这些行（`re.sub(r'^.*视觉提示词.*\n?', '', text, flags=re.MULTILINE)`）
- **配图直接用**这些关键词翻译成英文完整prompt（比 keyword_map 匹配更准）
- 新闻稿改动后**必须重新检查**日期是否正确（见下方）

### 2. 开场图每期必换
- **opening_bg.jpg 绝对不可复用历史期**。用户明确批评「已经用过了，需要重新做一个」
- 场景轮换池：控制室夜景 / 新闻演播室 / 城市天台 / 数据大厅 / 外滩夜景等
- 先用 Pollinations 出底图，再跑 `gen_opening_bg.py` 叠加 Sign-POP News 台标

### 3. 地理配图必须准确（用户严厉要求）
- 霍尔木兹海峡、国家地图等地理类场景**不能用模糊关键词**
- prompt **必须包含**具体地理方位：`Strait of Hormuz, Persian Gulf to Gulf of Oman, narrow strategic waterway between Iran and Oman, Arabian Peninsula coastline, deep blue sea, desert coastlines, satellite aerial view`
- 反例：只写 `Strait of Hormuz, military conflict`（不准确，用户发现后批评「做新闻要认真，特别是时政新闻，不能马虎」）
- 生成后 `vision_analyze` 验证配图是否匹配实际地理位置
- 用户会验证，出错会被批评。不要等用户指出来才改。

### 4. 风格轮盘（每期自动变化）
详见下方「每日视频风格轮盘」节。2026-07-12 落地。

### 5. 日期验证
- 新闻稿开头日期 = **制作日+1（发布日）**，格式 `「YYYY年MM月DD日，星期X」`
- 用户编辑新闻稿正文后，日期可能被改回制作日，**必须重新检查并修正**

## 概述

本流程负责将每日新闻稿（TXT）转换为一个完整的视频，包括以下核心步骤：

1.  **新闻稿输入**: `/home/kan/shared/signal_pop/archive/signal_pop_daily_YYYYMMDD.txt`
  - 新闻稿可能含 `视觉提示词：...` 行——**TTS输入必须裸strip**（re.sub + re.MULTILINE），配图则直接用翻译的英文prompt
  - **播报日期铁律**：日期 = 制作日+1（发布日）。格式 `「今天是YYYY年MM月DD日，星期X。」`
    - 新闻稿开头日期可能错误（如写作"制作日"而非"发布日"），发现即修。
    - 用户编辑新闻稿后，必须重新检查日期是否被改回。上一轮修正确认过，新一轮改正文可能覆盖。
  - 改动过新闻正文 → 必须重跑 TTS + 重配图（相关条）+ 重渲染 + 重上传
2.  **配图生成**: 使用 `Pollinations AI` 生成每条新闻的场景图 (`img_YYYYMMDD/{01-10}.jpg`) 和片头背景图 (`opening_bg.jpg`)。
3.  **TTS 语音合成**: 使用 `MiMo TTS API` 将新闻稿合成为 WAV 音频，并生成精准的 `_segments.json` 时间轴文件 (`output/daily/signal_pop_daily_YYYYMMDD.wav` / `_segments.json` / `.srt` / `.mp3`)。
4.  **视频渲染**: 使用 `build_daily_video.py` 脚本 (Python/PIL/FFmpeg) 结合配图和音频时间轴，渲染出 MP4 视频和封面图。
5.  **文件上传与留档**: 将成品视频和封面拷贝到 LAN 共享目录 (`/home/kan/shared/her2home/`)，并通过 HTTP POST 上传到 LAN Web 服务器。
6.  **多平台分发 (可选)**: 通过 `social-auto-upload` 项目的 `auto_publish.py` 脚本，将视频定时发布到 Bilibili, Kuaishou, Xiaohongshu, Douyin 等平台。

## 新闻计数与模板差异

| 模板类型 | 新闻条数 | 配图数量 | 说明 |
|---------|---------|---------|------|
| 日常版 | 10条 | 10 + opening | 标准流程，文件命名 `signal_pop_daily_*` |
| 周末特别版 | 15条 | 15 + opening | 新闻稿在 `archive/` 带 `_weekly_special_` 后缀，需先转换 |

### 周末特别版入口

特别版新闻稿是 Markdown 格式（非 `第N条` 格式），到可用的 TTS 脚本需要转换：

1. 读取 `signal_pop_weekly_special_YYYYMMDD.txt`
2. 运行转换脚本（一次性写入 `/tmp/convert_weekly_special.py`）
3. 随后的 TTS → 配图 → 渲染流程与日常版一致

转换脚本规律见 `references/weekend-special-conversion.md`。

### `parse_news` 解析坑

`build_daily_video.py` 的 `parse_news()` 按 `第N条` 分割，不依赖空行分隔。如果在渲染时报 `Parsed 0 news items`，说明新闻稿内新闻未用 `第N条` 开头。修法：补 `第N条` 前缀，或更新 parse_news regex。

开场卡模板 `「{PUB_DATE_FMT} · {len(news_items)}条新闻」` 已是动态版（2026-07-10 从硬编码 `10条` 改为动态）。

## 详细步骤

### 1. 检查新闻稿

确保新闻稿文件存在且内容正确。注意：新闻稿可能包含**视觉提示词行**（`视觉提示词：...`），这些行**必须从TTS输入中剥离**，但可作为配图prompt使用。

**处理视觉提示词**（每次必做）：
```bash
python3 -c "
import re
text = open('/home/kan/shared/signal_pop/archive/signal_pop_daily_YYYYMMDD.txt').read()
clean = re.sub(r'^.*视觉提示词.*\n?', '', text, flags=re.MULTILINE)
open('/tmp/signal_pop_daily_YYYYMMDD_tts.txt', 'w').write(clean)
"
```

**日期验证**（必做）：检查新闻稿第一行日期是否为「制作日+1」（发布日）。不是则修。

**用户编辑新闻稿后的处理流程**（2026-07-12 新增，本轮实战验证）：
1. 读取新新闻稿
2. 检查日期是否正确（可能被改回制作日），修
3. 找出被改动的新闻条（用户说"第7条改了"）
4. 重新生成被改动的配图（用新视觉提示词翻译英文prompt）
5. 也换掉用户不满意的配图（如"第8张也不合适"）
6. 重新剥离视觉提示词 → 重跑 TTS
7. 重跑 build_daily_video.py → 重新上传
8. 每一步改动后都通知用户进度

```bash
read_file(path="/home/kan/shared/signal_pop/archive/signal_pop_daily_YYYYMMDD.txt")
```

### 2. 生成配图

根据新闻标题生成专属场景图，片头背景图需包含 "Sign-POP News" 台标且人物无变形。避免重复场景。

**prompt策略**（2026-07-12 新增）：
- 新闻稿含 `视觉提示词：` 行 → 翻译中文关键词为英文完整prompt，直接作为配图prompt（比 keyword_map 更准）
- **地理类配图必须强调地理准确性**：用"卫星鸟瞰"/"真实海岸线"/"波斯湾至阿曼湾"/"准确地理路径"等词
- 视觉提示词的中文关键词可直接翻译并扩写为完整英文场景描述，每条配图场景类型不同

**单条配图替换**（用户要求换某条新闻的图时）：
1. 删 `img_YYYYMMDD/{N:02d}.jpg`
2. 用视觉提示词为那条新闻写新英文prompt（不同场景类型）
3. 直接 `urllib` 下载单张到同名文件（不需跑 gen_news_images.py 全量）
4. 如用户说"第8张也不合适"，一并换掉
5. 重跑 TTS（如新闻正文也改了）+ 重渲染 + 重新上传

**脚本**: `/tmp/gen_img_YYYYMMDD.py` (一次性写入，可基于 `signal-pop-image-generation` skill 提供的 `gen_news_images.py` 模板定制)

**执行**: `python3 /tmp/gen_img_YYYYMMDD.py`

**输出**: `/home/kan/shared/signal_pop/archive/img_YYYYMMDD/{01..10,opening_bg}.jpg`

**常见坑点**:
- AI 生成人物肢体极易变形。⚠️ **用户对变形零容忍**。遇到变形图**必须立即换掉**（不能保留等待下次），策略：改为无人物的 prompt（产品微距、远景建筑、纯场景构图），不可以留"等下次重新生成"。
- **非人物物体变形同样零容忍** — 汽车外形扭曲、栏杆变形、品牌标志错误（如宝马车标成VinFast），用户一样会指出。策略：加 `negative_prompt=deformed,distorted,disfigured`；prompt 避开具体品牌名称（"汽车维修车间引擎盖检修"而非"宝马汽车"）；图生得太复杂就精简prompt。
- **Pollinations 无法可靠生成文字** — 需要文字（如 "Signpop-News"）时，**不要靠 Pollinations prompt 生成**。策略：用一张干净无字底图（可取历史期类似场景或 Pollinations 出无文字版本），再用 PIL 叠文字 overlay。
- **opening_bg 文字替换策略**：用户要求把原图中的"VIRSUNNY"替换为"Signpop-News"，不是盖黑块再加。正确做法：用干净底图（或历史期同类 opening_bg），PIL 覆写目标文字区域（半透明遮罩→金色大字）。不用黑块遮盖后再写——用户要的是"替换"不是"覆盖"。
- **开图每期必全新**，不可复用历史期。场景轮换：控制室夜景/新闻演播室/城市天台/数据大厅/外滩夜景等。用户明确指出的。
- **地理配图必须地理准确** — 霍尔木兹海峡、国家地图等必须包含具体方位（卫星鸟瞰、真实海岸线、地理坐标）。用户会验证，出错会被批评。
- **prompt 精简原则**：用户要求"精简提示词，抓取重点来做"。复杂 prompt 出杂乱图。`集装箱码头、繁忙港口` 优于长段描述。最少的词表达核心场景。
- Pollinations 每张约 20-60s，10 条分批超时。先 5 张再 5 张，opening_bg 最后。
- 用 `urllib` 非 `requests`。`User-Agent` + `Referer` 头必须带，否则 403。

### 每日视频风格轮盘（2026-07-12 新增）

为每期提供视觉新鲜感，`build_daily_video.py` 内置了风格轮盘机制：

**机制**：4套配色主题，根据 DATE 的 MD5 哈希自动选择，每期不同：
  - #0 蓝白经典 — 标签深蓝 + 金色点缀（20260712 本期命中）
  - #1 橙黑科技 — 标签橙红 + 橙色点缀
  - #2 墨绿财经 — 标签墨绿 + 青绿点缀
  - #3 紫金国际 — 标签深紫 + 淡紫点缀

**影响范围**：开场/结束卡的线条、徽章圆环、标题颜色；新闻帧的标签胶囊底色。不影响配图本身。

**扩展方向**（用户已同意落地但未实现）：开场图场景类型轮换（控制室/演播室/城市天台/数据大厅/外滩夜景）、字体组合轮换、布局微调。

**对应代码**：`build_daily_video.py` 中的 `STYLE_THEMES` 数组和 `STYLE` 字典。`hashlib.md5(DATE).hexdigest()[:8] % 4` 选主题。

### 3. TTS 语音合成

将新闻稿文本转为音频，生成精准时间轴。

**脚本**: `/home/kan/signal_pop/src/tts_mimo.py`

**执行**: export MIMO_API_KEY="<your_key>"; python3 src/tts_mimo.py "$(cat /tmp/signal_pop_daily_YYYYMMDD_tts.txt)" --female --output output/daily/signal_pop_daily_YYYYMMDD.wav --srt output/daily/signal_pop_daily_YYYYMMDD.srt

⚠️ 必须用剥离视觉提示词后的文本（/tmp/signal_pop_daily_YYYYMMDD_tts.txt），不能用原新闻稿。

**输出**: `/home/kan/signal_pop/output/daily/signal_pop_daily_YYYYMMDD.wav` (MP3, SRT, JSON segments)

### ⚠️ TTS 段静默丢失诊断（2026-07-14 关键坑）

**错误现象**：视频播报没有开场白，一开口就是"第1条..."。开场卡修时长/文字大小没用——音频本身就没有开场白。

**诊断步骤**（2026-07-14 花了几轮才定位到，以后先查这个）：
1. 用户说"没有开场白" → **不要修视频时长/文字大小**，先查 TTS 段数
2. `cat output/daily/signal_pop_daily_YYYYMMDD_segments.json` 看有几段
3. 预期 = 1(开场白) + N(新闻条数) = 11段。实际 9 段 → 开场白段被静默丢弃
4. SRT 文件可能有开场白文本（来自 estimated duration），但实际 WAV 无对应音频

**根因**：`synthesize_long_text()` 逐段调 MiMo API，某段失败时 `except: continue` 静默跳过，不重试、不告警。20260714 开场白段(55字) API 调用失败，仅 9 段合成成功。

**修复**：`tts_mimo.py` 已加自动重试（失败等 2s 重试一次）。重跑 TTS 即可。

**验证**：
```bash
python3 -c "
import json, wave
with open('output/daily/signal_pop_daily_YYYYMMDD_segments.json') as f:
    segs = json.load(f)
with wave.open('output/daily/signal_pop_daily_YYYYMMDD.wav') as w:
    dur = w.getnframes() / w.getframerate()
print(f'{len(segs)} segments, {dur:.1f}s total — 预期 11')
```

### 4. 视频渲染

整合图片、音频、时间轴，生成视频和封面。

**脚本**: `/home/kan/signal_pop/scripts/build_daily_video.py` (DATE 变量已内置)

**执行**: `python3 /home/kan/signal_pop/scripts/build_daily_video.py`

**输出**: `/home/kan/signal_pop/output/daily/signal_pop_daily_YYYYMMDD_v4.mp4`, 自动拷贝到 her2home

### 5. 文件上传与留档

成品视频和封面拷贝至 LAN 共享目录，并上传至 HTTP 服务器。

**留档**: 
- `/home/kan/shared/her2home/video_YYYYMMDD.mp4`
- `/home/kan/shared/her2home/cover_YYYYMMDD.png`

**上传**: `curl -X POST -F "file=@/path/to/video.mp4" http://10.10.10.30:8080/her2home/`

**封面文件名坑**: 封面文件名需与视频基名匹配（例如 `video_YYYYMMDD.png`），否则 `auto_publish.py` 会误报「缺少封面」。若封面名为 `cover_YYYYMMDD.png`，可通过创建软链接解决：`ln -sf cover_YYYYMMDD.png video_YYYYMMDD.png`。`gen_cover.py` 会自动输出 `cover_{DATE}.png`(4:3) 和 `cover_{DATE}_16x9.png`(16:9)。\n\n**4:3 封面铁律**：4:3 封面（1440×1080）**绝不能用 `Image.crop()` 截取 16:9 封面**。用户明确指出「这是截图不是完整的图片」。必须全量 re-render。脚本 `scripts/gen_cover_4x3.py` 已封装：缩减右外边距（新闻列表 max_w=1200px）、缩短底部品牌文字避免右侧裁切。调用：`python3 /home/kan/.hermes/skills/media/signal-pop-daily-video/scripts/gen_cover_4x3.py`。

### 6. 多平台分发 (auto_publish.py)

`auto_publish.py` 脚本位于 `/home/kan/shared/social-auto-upload/`，负责将视频发布到多个平台。

**原则**: **只允许一次性手动运行，严禁挂载 cron！** 用户明确要求，避免平台重复发布。

**⚠️ 微信视频号（tencent）平台缺失坑**：`auto_publish.py` 的 `PLATFORMS` 列表默认只有 `["bilibili", "xiaohongshu", "kuaishou", "douyin"]`，**不包含 `"tencent"`**。每次首次搭建或重置配置文件后，必须检查 PLATFORMS 是否包含 `"tencent"`：
```python
PLATFORMS = ["bilibili", "xiaohongshu", "kuaishou", "douyin", "tencent"]
```
用户指出"我让你配好微信的，你忘了？"——不可遗漏。

**微信视频号 cookie 过期**：`sau tencent check --account her2home` → `invalid` → 服务器可代劳扫码（见 `signal-pop-pipeline`  skill 的「微信视频号 cookie 过期处理」节，不需要用户本地桌面）。成功后必须 `cp cookies/tencent_her2home.json cookies/tencent_uploader/her2home` 同步 cookie。

**坑**: `playwright` (或其 fork `patchright`) 在无头机环境下可能存在浏览器安装/版本冲突问题。见 `signal-pop-pipeline` skill。 
