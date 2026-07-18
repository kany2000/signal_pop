# Signal Pop 每日视频 — 命令配方（2026-07 验证）

## 0. 数据准备：两套新闻稿入口

### 入口 A：虾小图格式（parse_xiaoxiaotu.py）

虾小图原始稿带有 emoji 编号（`1️⃣`）和日期行。`parse_xiaoxiaotu.py` 接收制作日参数，内部把日期改为发布日（DATE+1）：

```bash
PROD_DATE=20260710
python3 /home/kan/signal_pop/src/parse_xiaoxiaotu.py "$PROD_DATE" > archive/signal_pop_daily_$PROD_DATE.txt
```

虾小图日期行格式为 `🗓 2026年7月9日 星期三`，脚本把年月日 + 星期同时改为发布日。

### 入口 B：手动整理稿

直接写 `archive/signal_pop_daily_YYYYMMDD.txt`，格式必须用 `第N条` 开头。

### 入口 C：周末特别版（Markdown 格式）

15 条，含分类和主播观点。需两次转换：Markdown → 标准 `第N条` 格式 → 清洗残留。

## 1. 配图（pollinations.ai 文本生图）
核心（urllib，seed 固定可复现）：
```python
import urllib.request, urllib.parse
url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(prompt)}?width=1280&height=720&nologo=true&seed={n}"
headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
           "Referer": "https://pollinations.ai/"}
# urllib.request.urlopen(Request(url, headers=headers), timeout=120) -> 写 jpg
```
- 每条新闻独立场景 prompt，禁止重复赛博隧道/数据中心风。
- 换稿先 `rm /home/kan/shared/signal_pop/archive/img_YYYYMMDD/0*.jpg` 再跑生成脚本（脚本跳过已存在文件）。
- 15条稿分批策略：先跑前 7 张，再补后 8 张 + opening_bg，每批独立脚本。遇超时检查已生成数量再补。

## 2. opening_bg（新闻直播间 + 可读台标）
生图 prompt 含 `news broadcast studio ... no text`；生成后用 PIL 叠加台标（AI 出字会糊）：
```python
from PIL import Image, ImageDraw, ImageFont
img = Image.open("opening_bg_raw.jpg").convert("RGBA")
d = ImageDraw.Draw(img)
f = ImageFont.truetype("/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc", 64)
d.text((W//2, by+th//2), "Sign-POP News", fill=(255,215,0,255), font=f, anchor="mm")
img.convert("RGB").save("opening_bg.jpg", "JPEG", quality=92)
```

## 3. TTS（MiMo）
```bash
export MIMO_API_KEY="$(cat /home/kan/shared/OpenMontage/signal_pop_test/.mimo_key)"
cd /home/kan/signal_pop
python3 src/tts_mimo.py "$(cat /home/kan/shared/signal_pop/archive/signal_pop_daily_YYYYMMDD.txt)" \
  --female --output output/daily/signal_pop_daily_YYYYMMDD \
  --srt output/daily/signal_pop_daily_YYYYMMDD.srt
```
产出：.wav / _segments.json / .srt / .mp3（女声 voice_id=xiaoxiao，男声 yunyang）

**坑**：tts_mimo.py 的 segments 输出存为 `_raw_segments.json`，`build_daily_video.py` 读 `_segments.json`。渲染前需：
```bash
cp output/daily/signal_pop_daily_YYYYMMDD_raw_segments.json output/daily/signal_pop_daily_YYYYMMDD_segments.json
```

## 4. 渲染
```bash
# 先改 scripts/build_daily_video.py 顶部: DATE = "YYYYMMDD"
cd /home/kan/signal_pop && python3 scripts/build_daily_video.py
```
自动拷贝 video_YYYYMMDD.mp4 + cover_YYYYMMDD.png 到 /home/kan/shared/her2home/

## 5. 上传 HTTP
```bash
curl -X POST -F "file=@/home/kan/shared/her2home/video_YYYYMMDD.mp4" http://10.10.10.30:8080/her2home/
curl -X POST -F "file=@/home/kan/shared/her2home/cover_YYYYMMDD.png" http://10.10.10.30:8080/her2home/
# 校验
curl -s -o /dev/null -w "%{http_code} %{size_download}\n" http://10.10.10.30:8080/her2home/video_YYYYMMDD.mp4
```

## 6. 校验视频
```bash
ffprobe -v error -show_entries format=duration,size \
  -show_entries stream=codec_type -of default=noprint_wrappers=1 \
  /home/kan/shared/her2home/video_YYYYMMDD.mp4
```

## 7. 封面模板（PIL，非 AI 出图文字）
封面按 `video_20260701.png` 模板：左 60% 暗灰网格文字面板 + 右 40% 主播竖图 +
四角青色 L 角标 + 标题青色辉光。**模板脚本** `scripts/gen_cover_template.py`
（复制后改 DATE/文案/seed）。人像用 pollinations 出 768×1080 竖图（prompt 加
`natural realistic body proportions, no distortion`）；文字一律 PIL 叠加，绝不靠 AI。

## 8. 多平台分发（auto_publish.py）
```bash
# 先修封面名匹配（脚本找 video_YYYYMMDD.png，封面实为 cover_YYYYMMDD.png）
ln -sf cover_YYYYMMDD.png /home/kan/shared/her2home/video_YYYYMMDD.png
# 写元数据
cat > /home/kan/shared/her2home/video_YYYYMMDD.json <<'JSON'
{"title":"隔天信号弹 | 2026.07.10 每日新闻播报",
 "desc":"每日硬核资讯，十条直达核心。",
 "tags":"隔天信号弹,新闻播报,每日资讯,AI,科技"}
JSON
# 一次性手动发布（不挂 cron）
cd /home/kan/shared/social-auto-upload && python3 auto_publish.py
```
- state 文件：`/home/kan/shared/her2home/.publish_state.json`。旧稿若只想排除，把其
  platforms 四项标 `true` 即可跳过；不要让它每次被重试发错稿。
- 无头机仅 bilibili 成功（系统 chrome）；kuaishou/xhs/douyin 需 playwright chromium + X，
  失败则换机补发。默认定时次日 08:30（符合 PUB_DATE）。
