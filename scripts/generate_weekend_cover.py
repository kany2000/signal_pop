#!/usr/bin/env python3
"""
Signal Pop 封面生成器 — 按 video_20260701.png 模板。
左 60% 暗灰网格文字栏 + 右 40% 主播竖图 + 四角青色 L 角标 + 标题青色辉光。
文字一律 PIL 叠加（AI 出图文字必糊）。复制后改 DATE / 文案 / seed。
依赖: PIL, 联网(pollinations 出人像)。
"""
import urllib.request, urllib.parse, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# ===== 改这里 =====
# 从视频文件名中提取日期
import re
video_file = "/home/kan/signal_pop/output/daily/signal_pop_daily_20260716_v4.mp4"
match = re.search(r'(\d{8})', video_file)
if match:
    prep_date = match.group(1)  # 20260716
    # 计算出版日期 (准备日期 + 1天)
    from datetime import datetime, timedelta
    prep_dt = datetime.strptime(prep_date, '%Y%m%d')
    pub_dt = prep_dt + timedelta(days=1)
    pub_date_str = pub_dt.strftime('%Y.%m.%d')  # 2026.07.17
else:
    prep_date = "20260716"
    pub_date_str = "2026.07.17"

DATE = prep_date  # 用于文件名
PUB = pub_date_str  # 用于显示在封面上
TITLE = "隔天信号弹"
SUB = "Signal Pop · 每日新闻播报"
TAG = "新闻 • 时事 • 资讯"
# =================

W, H = 1920, 1080
LEFT_W = int(W * 0.6)
RIGHT_W = W - LEFT_W
COVER = f"/home/kan/shared/her2home/cover_{DATE}.png"
FONT    = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
FONT_B  = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
CYAN = (0, 229, 255)

def fnt(sz, bold=False):
    try: return ImageFont.truetype(FONT_B if bold else FONT, sz)
    except: return ImageFont.load_default()

# 1. 右侧人像竖图（约束不扭曲）
anchor = f"/tmp/cover_anchor_{DATE}.jpg"
prompt = ("professional Chinese female news anchor, head and shoulders portrait, "
          "natural realistic body proportions, neutral studio background, "
          "professional broadcast look, soft lighting, no text, no distortion")
q = urllib.parse.quote(prompt)
url = f"https://image.pollinations.ai/prompt/{q}?width=768&height=1080&nologo=true&seed=11"
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
req = urllib.request.Request(url, headers={"User-Agent": UA, "Referer": "https://pollinations.ai/"})
open(anchor, "wb").write(urllib.request.urlopen(req, timeout=120).read())

# 2. 底图：左暗灰网格 + 右紫蓝渐变
canvas = Image.new("RGB", (W, H), (51, 51, 51))
dl = ImageDraw.Draw(canvas)
for x in range(0, LEFT_W, 40):
    dl.line([(x, 0), (x, H)], fill=(42, 42, 42), width=1)
for y in range(0, H, 40):
    dl.line([(0, y), (LEFT_W, y)], fill=(42, 42, 42), width=1)
right = Image.new("RGB", (RIGHT_W, H)); rd = ImageDraw.Draw(right)
top_c, bot_c = (201, 184, 232), (168, 200, 240)
for y in range(H):
    t = y / (H - 1)
    c = tuple(int(top_c[i] + (bot_c[i] - top_c[i]) * t) for i in range(3))
    rd.line([(0, y), (RIGHT_W, y)], fill=c)
canvas.paste(right, (LEFT_W, 0))
a = Image.open(anchor).convert("RGB"); aw, ah = a.size
s = max(RIGHT_W / aw, H / ah); a = a.resize((int(aw*s), int(ah*s)), Image.LANCZOS)
lx = (a.width - RIGHT_W) // 2; a = a.crop((lx, 0, lx + RIGHT_W, H))
canvas.paste(a, (LEFT_W, 0))

# 3. 文字层
draw = ImageDraw.Draw(canvas)
PAD = 90
draw.text((PAD, 120), TAG, fill=(235, 235, 235), font=fnt(30))
ty = 430; tb = fnt(104, True)
glow = Image.new("RGBA", (W, H)); ImageDraw.Draw(glow).text((PAD, ty), TITLE, font=tb, fill=CYAN + (255,))
glow = glow.filter(ImageFilter.GaussianBlur(10))
canvas = canvas.convert("RGBA"); canvas.alpha_composite(glow)
draw = ImageDraw.Draw(canvas)
draw.text((PAD, ty), TITLE, fill=(255, 255, 255), font=tb)
sy = ty + 130
draw.text((PAD, sy), SUB, fill=(225, 225, 225), font=fnt(38))
draw.line([(PAD, sy + 56), (PAD + 520, sy + 56)], fill=(90, 90, 90), width=2)
draw.text((PAD, H - 150), PUB, fill=(225, 225, 225), font=fnt(36))

# 4. 四角青色 L 角标
L, B = 64, 5
def bracket(cx, cy, dx, dy):
    draw.line([(cx, cy), (cx + dx*L, cy)], fill=CYAN, width=B)
    draw.line([(cx, cy), (cx, cy + dy*L)], fill=CYAN, width=B)
bracket(20, 20, 1, 1); bracket(20, H-20, 1, -1)
bracket(W-20, 20, -1, 1); bracket(W-20, H-20, -1, -1)

canvas.convert("RGB").save(COVER, "JPEG", quality=92)
print(f"✅ {COVER}")