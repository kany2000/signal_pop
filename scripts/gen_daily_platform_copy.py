#!/usr/bin/env python3
"""Generate 7 platform copy files for daily edition"""
import json, os
from datetime import datetime, timedelta

DATE = "20260802"
PUB_DT = datetime.strptime(DATE, "%Y%m%d") + timedelta(days=1)
PUB_DATE = PUB_DT.strftime("%Y%m%d")
PUB_DATE_SHORT = f"{PUB_DATE[:4]}.{PUB_DATE[4:6]}.{PUB_DATE[6:8]}"
PUB_WEEKDAY = ["星期一","星期二","星期三","星期四","星期五","星期六","星期日"][PUB_DT.weekday()]

OUT_DIR = f"E:/projects/signal_pop/output/daily_{DATE}"
PARSED = os.path.join(OUT_DIR, "parsed_news.json")
SEGMENTS = os.path.join(OUT_DIR, "audio", "tts_segments.json")

with open(PARSED, 'r', encoding='utf-8') as f:
    items = json.load(f)

# Calculate timestamps
timestamps = []
ts_labels = ['开场']
for i in range(1, len(items)):
    ts_labels.append(f'第{i}条')
ts_labels.append('结尾互动')

if os.path.exists(SEGMENTS):
    with open(SEGMENTS, 'r', encoding='utf-8') as f:
        segs = json.load(f)
    t = 0
    for seg, label in zip(segs, ts_labels):
        mins = int(t // 60)
        secs = int(t % 60)
        timestamps.append((f'{mins}:{secs:02d}', label))
        t += seg
else:
    timestamps = [("0:00", "开场")] + [(f"0:{i*8+8:02d}", f"第{i+1}条") for i in range(len(items))] + [("1:30", "结尾")]

# Numbered list
news_list = [f"{i+1}. {it['title']}" for i, it in enumerate(items)]
news_str = '\n'.join(news_list)

# Timestamp list
ts_str = '\n'.join(f'{ts} {label}' for ts, label in timestamps)

# Hashtags
SECTION_TAGS = {"科技前沿": "#科技", "经济财经": "#财经", "国内民生": "#国内", "国际综合": "#国际"}
hashtags = set()
for it in items:
    s = it.get("section", "综合")
    ht = SECTION_TAGS.get(s, f"#{s}")
    hashtags.add(ht)
hashtag_str = ' '.join(sorted(hashtags)) + ' #信号弹 #隔天信号弹 #新闻早报 #AI新闻'

title_main = f"隔天信号弹 {PUB_DATE_SHORT}｜{PUB_WEEKDAY} · 每日新闻播报"
title_douyin = f"📡 {title_main}"

# 1. Douyin
douyin = f"""标题：{title_douyin}

简介：
📡 隔天信号弹 · {PUB_DATE_SHORT} {PUB_WEEKDAY}
10条核心新闻，带你快速了解今日大事！

{news_str}

#信号弹 #隔天信号弹 #新闻早报 #AI新闻 #科技 #财经 #国内 #国际
"""

# 2. Kuaishou
kuaishou = f"""标题：{title_douyin}

简介：
📡 隔天信号弹 · {PUB_DATE_SHORT} {PUB_WEEKDAY}
10条核心新闻，带你快速了解今日大事！

{news_str}

#信号弹 #隔天信号弹 #新闻早报 #AI新闻
"""

# 3. Bilibili
bilibili = f"""标题：【信号弹】{PUB_DATE_SHORT} {PUB_WEEKDAY}｜10条核心新闻速览

简介：
📡 隔天信号弹 · {PUB_DATE_SHORT} {PUB_WEEKDAY}
10条核心新闻，带你快速了解今日大事！

本期内容：
{news_str}

📌 时间戳
{ts_str}

分区：资讯
标签：信号弹 隔天信号弹 新闻早报 AI新闻 科技 财经 国内 国际
"""

# 4. Tencent
tencent = f"""标题：{title_main}

简介：
📡 隔天信号弹 · {PUB_DATE_SHORT} {PUB_WEEKDAY}
10条核心新闻，带你快速了解今日大事！

本期内容：
{news_str}

#信号弹 #隔天信号弹 #新闻早报 #AI新闻 #科技 #财经 #国内 #国际
"""

# 5. Xiaohongshu
emoji_nums = ["1️⃣","2️⃣","3️⃣","4️⃣","5️⃣","6️⃣","7️⃣","8️⃣","9️⃣","🔟"]
emoji_list = '\n'.join(f"{emoji_nums[i]} {it['title']}" for i, it in enumerate(items))

xhs = f"""标题：📡 隔天信号弹 {PUB_DATE_SHORT} {PUB_WEEKDAY}✨

正文：
📡 隔天信号弹 {PUB_DATE_SHORT} {PUB_WEEKDAY}✨

10条核心新闻速览👇

{emoji_list}

💬 你最关注哪条新闻？欢迎评论区聊聊！

#信号弹 #隔天信号弹 #新闻早报 #AI新闻 #新闻资讯 #每日新闻
"""

# 6. Youtube
youtube = f"""标题：{title_main}

简介：
📡 隔天信号弹 · {PUB_DATE_SHORT} {PUB_WEEKDAY}
10条核心新闻，带你快速了解今日大事！

⏱️ 时间戳
{ts_str}

{hashtag_str}
"""

# 7. Facebook
facebook = f"""标题：{title_main}

正文：
📡 隔天信号弹 · {PUB_DATE_SHORT} {PUB_WEEKDAY}

10条核心新闻，带你快速了解今日大事！

{emoji_list}

💬 您最关注哪条新闻？欢迎在评论区留言讨论！

#信号弹 #隔天信号弹 #新闻早报 #AI新闻
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