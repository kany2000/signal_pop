#!/usr/bin/env python3
"""Generate 7 platform copy files for weekly special"""
import json, os
from datetime import datetime, timedelta

PARSED = "E:/projects/signal_pop/output/parsed_weekly_20260731.json"
SEGMENTS = "E:/projects/signal_pop/output/daily_20260731/audio/tts_segments.json"
OUT_DIR = "E:/projects/signal_pop/output/daily_20260731"

DATE = "20260731"
PUB_DT = datetime.strptime(DATE, "%Y%m%d") + timedelta(days=1)
PUB_DATE = PUB_DT.strftime("%Y%m%d")
PUB_DATE_SHORT = f"{PUB_DATE[:4]}.{PUB_DATE[4:6]}.{PUB_DATE[6:8]}"

with open(PARSED, 'r', encoding='utf-8') as f:
    items = json.load(f)

# Calculate actual timestamps from segment durations
timestamps = []
with open(SEGMENTS, 'r', encoding='utf-8') as f:
    segs = json.load(f)
t = 0
ts_labels = ['开场']
for i in range(1, len(segs)):
    if i == len(segs) - 1:
        ts_labels.append('结尾互动')
    else:
        ts_labels.append(f'第{i}条')
for seg, label in zip(segs, ts_labels):
    mins = int(t // 60)
    secs = int(t % 60)
    timestamps.append((f'{mins}:{secs:02d}', label))
    t += seg

# Create numbered list
news_list = []
for i, item in enumerate(items, 1):
    t = item["title"]
    news_list.append(f"{i}. {t}")

news_str = '\n'.join(news_list)

# Emoji numbered list
emoji_nums = ["1️⃣","2️⃣","3️⃣","4️⃣","5️⃣","6️⃣","7️⃣","8️⃣","9️⃣","🔟","1️⃣1️⃣","1️⃣2️⃣","1️⃣3️⃣","1️⃣4️⃣","1️⃣5️⃣"]
emoji_list = []
for i, item in enumerate(items):
    emoji_list.append(f"{emoji_nums[i]} {item['title']}")
emoji_str = '\n'.join(emoji_list)

# Hashtags
CAT_TAGS = {"科技前沿": "#科技", "国内民生": "#国内", "国际综合": "#国际"}
hashtags = set()
for it in items:
    t = it["section"]
    ht = CAT_TAGS.get(t, f"#{t}")
    hashtags.add(ht)
hashtag_str = ' '.join(sorted(hashtags)) + ' #信号弹 #隔天信号弹 #新闻早报 #AI新闻 #每日新闻'

# Titles
title_main = f"隔天信号弹 {PUB_DATE_SHORT}｜周末特别版 · 本周新闻汇总"
title_douyin = f"📡 {title_main}"
title_bilibili = f"【信号弹】{PUB_DATE_SHORT} 周末特别版｜本周15条核心新闻全汇总"
title_xhs = f"📡 隔天信号弹 {PUB_DATE_SHORT} 周末特别版✨本周新闻一览"

# === 1. Douyin ===
douyin = f"""标题：{title_douyin}

简介：
📡 隔天信号弹 · {PUB_DATE_SHORT} 周末特别版
本周15条核心新闻，带你快速了解国内外大事！

{news_str}

#信号弹 #隔天信号弹 #新闻早报 #本周热点 #AI新闻 #科技 #财经 #国际新闻
"""

# === 2. Kuaishou ===
kuaishou = f"""标题：{title_douyin}

简介：
📡 隔天信号弹 · {PUB_DATE_SHORT} 周末特别版
本周15条核心新闻，带你快速了解国内外大事！

{news_str}

#信号弹 #隔天信号弹 #新闻早报 #本周热点 #AI新闻
"""

# === 3. Bilibili ===
bilibili = f"""标题：{title_bilibili}

简介：
📡 隔天信号弹 · {PUB_DATE_SHORT} 周末特别版
本周15条核心新闻，带你快速了解国内外大事！

本期内容：
{news_str}

📌 时间戳
{chr(10).join(f'{ts} {label}' for ts, label in timestamps)}

分区：资讯
标签：信号弹 隔天信号弹 新闻早报 本周热点 AI新闻 科技 财经 国际新闻
"""

# === 4. Tencent ===
tencent = f"""标题：{title_main}

简介：
📡 隔天信号弹 · {PUB_DATE_SHORT} 周末特别版
本周15条核心新闻，带你快速了解国内外大事！

本期内容：
{news_str}

#信号弹 #隔天信号弹 #新闻早报 #本周热点 #AI新闻 #科技 #财经 #国际新闻
"""

# === 5. Xiaohongshu ===
xhs = f"""标题：{title_xhs}

正文：
📡 隔天信号弹 {PUB_DATE_SHORT} 周末特别版✨

本周15条核心新闻速览👇

{emoji_str}

💬 你最关注哪条新闻？欢迎评论区聊聊！

#信号弹 #隔天信号弹 #新闻早报 #本周热点 #AI新闻 #新闻资讯 #每日新闻
"""

# === 6. Youtube ===
youtube = f"""标题：{title_main}

简介：
📡 隔天信号弹 · {PUB_DATE_SHORT} 周末特别版
本周15条核心新闻，带你快速了解国内外大事！

⏱️ 时间戳
{chr(10).join(f'{ts} {label}' for ts, label in timestamps)}

{hashtag_str}
"""

# === 7. Facebook ===
facebook = f"""标题：{title_main}

正文：
📡 隔天信号弹 · {PUB_DATE_SHORT} 周末特别版

本周15条核心新闻，带你快速了解国内外大事！

{emoji_str}

💬 您最关注哪条新闻？欢迎在评论区留言讨论！

#信号弹 #隔天信号弹 #新闻早报 #本周热点 #AI新闻
"""

files = {
    "douyin.md": douyin,
    "kuaishou.md": kuaishou,
    "bilibili.md": bilibili,
    "tencent.md": tencent,
    "xiaohongshu.md": xhs,
    "youtube.md": youtube,
    "facebook.md": facebook,
}

for fname, content in files.items():
    path = os.path.join(OUT_DIR, fname)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"  {fname}")

print(f"\nAll 7 platform copy files saved to {OUT_DIR}")