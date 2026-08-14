#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Signal Pop 周末特别版 · 8 平台发布文案（双人对话版）
输出到 output/weekly/{PREP_DATE}/
用法：python tools/gen_weekly_talk_copy.py [PREP_DATE]
"""
import os
import sys
import json
import re

PROJECT_ROOT = "E:/projects/signal_pop"
PREP_DATE = sys.argv[1] if len(sys.argv) > 1 else "20260814"
OUT_DIR = os.path.join(PROJECT_ROOT, "output", "weekly", PREP_DATE)

from datetime import datetime, timedelta
PUB_DT = datetime.strptime(PREP_DATE, "%Y%m%d") + timedelta(days=1)
PUB_FMT = f"{PUB_DT.month}月{PUB_DT.day}日"

# 10 条新闻（第10→第1名）
NEWS = [
    "小米净水器沸腾版开售",
    "火狐和Brave继续支持广告拦截",
    "华硕Armoury Crate高危漏洞",
    "DOTA2国际邀请赛开打",
    "张雪机车获红杉投资",
    "影石开发可换镜头相机",
    "零跑越过最难熬节点",
    "Manus恢复独立运营",
    "惠州贞观天下大唐特展",
    "平陆运河9月通航",
]

TITLE = f"【周末特别版】阿信+小蓝聊本周｜{NEWS[9]}、{NEWS[8]}……10件大事"
DESC = "本周10件大事，阿信小蓝（信蓝组合）边聊边盘！一报一评，有梗有观点～"


def write(name, content):
    with open(os.path.join(OUT_DIR, name), "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  ✓ {name} ({len(content)} chars)")


def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    # 抖音
    dy = f"""标题：{TITLE}

简介：{DESC}

🎙️ 本周10件大事，信蓝组合开聊！
1️⃣ 小米净水器沸腾版（100℃真开水）
2️⃣ 火狐Brave守住广告拦截
3️⃣ 华硕高危漏洞请更新
4️⃣ DOTA2国际邀请赛开打
5️⃣ 张雪机车获红杉投资
6️⃣ 影石发力可换镜头相机
7️⃣ 零跑越过最难熬节点
8️⃣ Manus恢复独立运营
9️⃣ 惠州贞观天下大唐特展
🔟 平陆运河9月通航

#隔天信号弹 #周末特别版 #信蓝组合 #新闻脱口秀 #科技 #民生 #财经 #文化 #AI #平陆运河
"""
    write("douyin.md", dy)

    # 快手
    ks = f"""标题：【周末特别版】信蓝组合聊本周10件大事

简介：阿信+小蓝，一报一评，陪你看遍本周！

🔥 本周10条：
① 平陆运河9月通航
② 惠州贞观天下大唐特展
③ Manus恢复独立运营
④ 零跑越过最难熬节点
⑤ 影石可换镜头相机
⑥ 张雪机车获红杉投资
⑦ DOTA2国际邀请赛
⑧ 华硕高危漏洞
⑨ 火狐Brave广告拦截
⑩ 小米净水器沸腾版

#隔天信号弹 #周末特别版 #信蓝组合 #新闻盘点 #科技 #民生
"""
    write("kuaishou.md", ks)

    # B站（时间轴）
    srt = os.path.join(OUT_DIR, "signal_pop_weekly_20260814.srt")
    timeline = []
    if os.path.exists(srt):
        for block in open(srt, encoding="utf-8").read().strip().split("\n\n"):
            lines = block.split("\n")
            if len(lines) >= 3:
                m = re.match(r"(\d+):(\d+):(\d+)", lines[1])
                if m:
                    mm = int(m.group(1)) * 60 + int(m.group(2))
                    tl = f"{mm:02d}:{int(m.group(3)):02d}"
                    timeline.append(f"{tl} {lines[2][:30]}")
    timeline_text = "\n".join(timeline[:14]) if timeline else ""
    bili = f"""{TITLE}

📌 分段时间轴：
{timeline_text}

💬 阿信报新闻，小蓝唠重点——信蓝组合首秀，有梗有观点！

#隔天信号弹 #周末特别版 #信蓝组合 #新闻脱口秀 #科技 #文化 #财经
"""
    write("bilibili.md", bili)

    # 小红书
    xhs = f"""宝子们！周末特别版来啦📺✨

阿信+小蓝（信蓝组合）首次合体！
10件本周大事，边聊边盘，有梗有观点👇

📜 本期精选：
1️⃣ 平陆运河9月通航（世纪工程！）
2️⃣ 惠州贞观天下大唐特展（白陶舞马yyds）
3️⃣ Manus恢复独立运营（创业反转剧）
4️⃣ 零跑"越过最难熬节点"（造车人真心话）
5️⃣ 影石可换镜头相机（国产影像发力）
6️⃣ 张雪机车获红杉投资
7️⃣ DOTA2国际邀请赛开打
8️⃣ 华硕高危漏洞（快更新！）
9️⃣ 火狐Brave守住广告拦截
🔟 小米净水器沸腾版

你最喜欢哪条？评论区聊聊呀💬
记得关注不迷路，每周六8点见～

#隔天信号弹 #周末特别版 #信蓝组合 #新闻盘点 #大唐 #平陆运河 #科技新闻 #民生新闻 #文化 #财经 #AI
"""
    write("xiaohongshu.md", xhs)

    # 知乎
    zh = f"""隔天信号弹 | 周末特别版：阿信+小蓝聊本周（{PUB_FMT}）

本周 10 件大事，信蓝组合一报一评：

1. 平陆运河 9 月正式通航——西南出海缩短几百公里
2. 惠州"贞观天下"大唐特展——27 件国家一级文物
3. Manus 恢复独立运营——AI 创业反转剧
4. 零跑创始人：已越过最难熬的节点
5. 影石确认开发可换镜头相机
6. 张雪机车获红杉中国独家投资
7. DOTA2 国际邀请赛小组赛开打
8. 华硕 Armoury Crate 高危漏洞（请更新）
9. 火狐和 Brave 继续支持广告拦截插件
10. 小米净水器沸腾版开售

关注「隔天信号弹」，每周六 8 点，信蓝组合陪你看遍本周大事。
"""
    write("zhihu.md", zh)

    # 英文平台
    en_title = f"Weekend Special | Xin & Lan Talk This Week | {NEWS[9]}, {NEWS[8]}... 10 Big Stories"
    fb = f"""Weekend Special: Xin & Lan Talk This Week 🎙️

Two anchors (Xin + Lan = "XinLan Combo") chat about the TOP 10 stories of the week — one reports, one reacts!

🔹 Pinglu Canal opens in September
🔹 "Zhenguan Era" Tang Dynasty exhibition in Huizhou
🔹 Manus back to independent operation
🔹 Lynk & Co's founder: "past the hardest part"
🔹 Insta360 developing interchangeable-lens cameras
🔹 Zhangxue Motorcycle gets Sequoia China funding
🔹 DOTA2 International kicks off
🔹 ASUS Armoury Crate high-risk vulnerability
🔹 Firefox & Brave keep ad-blocking support
🔹 Xiaomi water purifier boiling version

#SignalPop #WeekendSpecial #XinLanCombo #NewsTalk #China #Tech
"""
    write("facebook.md", fb)

    yt = f"""Weekend Special | Xin & Lan Talk This Week | TOP 10 Stories of the Week

Two anchors (Xin + Lan) chat about this week's 10 biggest stories — one reports the news, the other drops hot takes. A news talk show, weekend edition!

Highlights: Pinglu Canal shipping opens in September, "Zhenguan Era" Tang Dynasty exhibition in Huizhou, Manus returns to independent operation, and more.

Subscribe for the weekly Saturday 08:00 edition!

#SignalPop, #WeekendSpecial, #NewsTalk, #China, #Tech, #Culture, #XinLanCombo, #Top10
"""
    write("youtube.md", yt)

    tw = f"""🎙️ Xin & Lan Talk This Week — Weekend Special!

TOP 10 stories, one reports, one reacts:
🔹 Pinglu Canal opens in September
🔹 Tang Dynasty exhibit in Huizhou
🔹 Manus back to independent
🔹 Insta360 new cameras
🔹 DOTA2 International kicks off

Watch the full talk ▶️
#SignalPop #WeekendSpecial #NewsTalk #China
"""
    write("twitter.md", tw)

    print(f"\n全部 8 平台文案已生成到 {OUT_DIR}/")


if __name__ == "__main__":
    main()
