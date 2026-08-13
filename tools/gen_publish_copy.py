#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Signal Pop — 统一生成 7 平台发布文案（抖音/快手/B站/小红书/知乎/Facebook/YouTube）
用法：python tools/gen_publish_copy.py [PREP_DATE]  默认 20260809
输出：output/daily_{DATE}/*.md（每个平台一份，风格差异化）
"""
import os
import sys
import json
from datetime import datetime, timedelta

PROJECT_ROOT = "E:/projects/signal_pop"
PREP_DATE = sys.argv[1] if len(sys.argv) > 1 else "20260809"
OUT_DIR = os.path.join(PROJECT_ROOT, "output", "daily", PREP_DATE)
PARSED = os.path.join(PROJECT_ROOT, "output", "daily", PREP_DATE, "parsed_news.json")
SEGMENTS = os.path.join(PROJECT_ROOT, "output", "daily", PREP_DATE, "audio", "tts_segments.json")

PUB_DT = datetime.strptime(PREP_DATE, "%Y%m%d") + timedelta(days=1)
PUB_DATE = PUB_DT.strftime("%Y%m%d")
PUB_DATE_FMT = f"{PUB_DT.year}年{PUB_DT.month:02d}月{PUB_DT.day:02d}日"
PUB_DATE_SHORT = f"{PUB_DT.year}.{PUB_DT.month:02d}.{PUB_DT.day:02d}"
PUB_WEEKDAY = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"][PUB_DT.weekday()]
M_D = f"{PUB_DT.month}月{PUB_DT.day}日"


def load_items():
    with open(PARSED, encoding="utf-8") as f:
        return json.load(f)


def load_durations():
    try:
        with open(SEGMENTS, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def short_of(title):
    """从完整标题提炼短视频短句（去掉来源/引号冗余）。"""
    t = title
    for p in ["：", ":", "｜", "|"]:
        if p in t:
            t = t.split(p, 1)[1]
    t = t.replace("”", "").replace("“", "")
    return t.strip()


def build_short_lines(items):
    """10条一句话短句（各平台共用底料，但话术各不相同）。"""
    lines = []
    for it in items:
        s = short_of(it["title"])
        if len(s) > 30:
            s = s[:29] + "…"
        lines.append(s)
    return lines


def fmt_ts(sec):
    m = int(sec // 60)
    s = int(sec % 60)
    return f"{m:02d}:{s:02d}"


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    items = load_items()
    durs = load_durations()
    # 历史上的今天(num=0) 是口播栏目，不计入"核心新闻"列表（但 B站时间轴保留完整顺序）
    news_items = [it for it in items if it.get("num", 0) != 0]
    history_items = [it for it in items if it.get("num", 0) == 0]
    shorts = build_short_lines(news_items)
    n = len(news_items)
    title_all = "、".join(shorts[:3])
    has_history = bool(history_items)
    history_text = ""
    if has_history:
        h = history_items[0]
        h_body = h.get('full_body', '').strip()
        # 历史上的今天：优先完整保留；超长才按完整句号截断，避免文案半截
        if len(h_body) > 80:
            cut = h_body[:80].rfind('。')
            if cut > 0:
                h_body = h_body[:cut + 1]
        history_text = f"📜 历史上的今天：{h_body}\n\n"

    # ── B站分段时间轴（用真实 TTS 分段时长 + 完整标题，含历史上的今天）──
    timeline_lines = []
    full_titles = [it["title"] for it in items]
    full_n = len(items)
    if durs and len(durs) == full_n + 2:
        t = 0.0
        timeline_lines.append(f"{fmt_ts(t)} 开场")
        acc = durs[0]  # intro
        for i in range(full_n):
            start = acc
            acc += durs[i + 1]
            timeline_lines.append(f"{fmt_ts(start)} {i+1}. {full_titles[i]}")
    else:
        for i in range(full_n):
            timeline_lines.append(f"{i+1}. {full_titles[i]}")

    files = {}

    # 1. 抖音
    files["douyin.md"] = f"""标题：{M_D}信号弹｜{title_all}！{n}条核心新闻

简介：每天3分钟，了解今天发生的{n}件大事！

{history_text}📱 本期看点：
""" + "\n".join(f"{i+1}️⃣ {s}" for i, s in enumerate(shorts)) + f"""

#隔天信号弹 #每日新闻 #今日热点 #新闻播报 #热点新闻 #科技资讯 #AI新闻 #新闻早报 #每日播报 #时政要闻 #民生新闻

正文：
隔天信号弹，每天为你精选{n}条核心新闻。"""

    # 2. 快手
    CIRC = "①②③④⑤⑥⑦⑧⑨⑩"
    files["kuaishou.md"] = f"""标题：{M_D}信号弹｜{n}条核心新闻：{title_all}

简介：每天3分钟，听遍天下事！今天{n}条新闻全在这里👇

🔥 本期热点：
""" + "\n".join(f"{CIRC[i] if i < len(CIRC) else i+1} {s}" for i, s in enumerate(shorts)) + f"""

#隔天信号弹 #新闻早报 #热点 #今日新闻 #每日播报 #科技 #财经 #民生 #社会 #资讯

正文：
隔天信号弹，每天为你精选{n}条核心新闻。"""

    # 3. B站
    files["bilibili.md"] = f"""【{M_D}信号弹】{title_all}｜{n}条核心新闻

📌 本期{n}条新闻：
""" + "\n".join(timeline_lines) + f"""

每天3分钟，纵览天下事。记得三连支持一下~

#隔天信号弹 #每日新闻 #新闻早报 #科技 #财经 #民生 #资讯

（以下为视频文案，供字幕参考）
这里是隔天信号弹，今天是{PUB_DATE_FMT}，{PUB_WEEKDAY}。"""

    # 4. 小红书
    files["xiaohongshu.md"] = f"""今天{n}条新闻，3分钟看完 📺✨

早上好呀宝子们☀️ 今天的信号弹来咯～
每天8点，3分钟带你速览今日大事👇

""" + history_text + "\n".join(f"{CIRC[i] if i < len(CIRC) else i+1}️⃣ {s}" for i, s in enumerate(shorts)) + f"""

你关注哪一条？评论区聊聊呀💬
记得关注不迷路，每天8点见哦～

#新闻早报 #每日新闻 #隔天信号弹 #今日热点 #科技资讯 #民生新闻 #信息差 #认知升级 #早安新闻 #新闻播报 #每日热点 #快讯"""

    # 5. 知乎
    files["zhihu.md"] = f"""隔天信号弹 | {M_D}新闻早报（每日{n}条）

""" + history_text + "\n".join(f"{i+1}. {s}" for i, s in enumerate(shorts)) + """

完整内容见视频。欢迎关注，每天 8 点更新。"""

    # 6. Facebook
    files["facebook.md"] = f"""📡 隔天信号弹 | {M_D} 每日新闻播报

今天{n}条核心新闻：
""" + "\n".join(f"{i+1}. {s}" for i, s in enumerate(shorts)) + """

每天3分钟，看世界动态。欢迎关注、分享！

#SignalPop #DailyNews #ChinaNews #Technology #News"""

    # 7. YouTube
    files["youtube.md"] = f"""📡 Signal Pop Daily | {PUB_DATE_SHORT} - {n} Core News Stories

Today's Top {n}:
""" + "\n".join(f"{i+1}. {s}" for i, s in enumerate(shorts)) + """

Every day in 3 minutes, catch up on the world.
SignalPop,DailyNews,China,Technology,News,DailyNews"""

    # 8. Twitter / X（英文、# 话题、280 字符内紧凑版）
    # 从英文字幕提取前3条英文短标题（去掉 "Article N, Category." 前缀 + 正文只取标题句）
    en_titles = []
    en_srt = os.path.join(PROJECT_ROOT, "output", "daily", PREP_DATE, f"signal_pop_daily_{PREP_DATE}_en.srt")
    if os.path.exists(en_srt):
        import re as _re
        blocks = _re.split(r"\n\n+", open(en_srt, encoding="utf-8").read().strip())
        for b in blocks[1:4]:
            lines = b.strip().split("\n")
            if len(lines) >= 3:
                t = lines[2]
                t = _re.sub(r"^Article\s*\d+\s*,\s*[^.]+\.\s*", "", t)
                # 英文标题以首个句号截断（取标题句）
                t = t.split(". ")[0].strip()
                if not t.endswith("."):
                    t += "."
                if t:
                    if len(t) > 100:
                        t = t[:97].rstrip() + "..."
                    en_titles.append(t)
    if len(en_titles) < 3:
        en_titles = [s[:60] for s in shorts[:3]]

    twitter = f"""📡 Signal Pop Daily | {n} News in 3 min

Today's top stories:
🔹 {en_titles[0]}
🔹 {en_titles[1]}
🔹 {en_titles[2]}
➕ {n-3} more in the video 👇

#SignalPop #DailyNews #China #Technology #News #AI #Weather"""
    # 若超 280 字符，逐步压缩
    if len(twitter) > 280:
        twitter = f"""📡 Signal Pop Daily | {n} News in 3 min

🔹 {en_titles[0]}
🔹 {en_titles[1]}
🔹 {en_titles[2]}
➕ {n-3} more in the video 👇

#SignalPop #DailyNews #China #News #AI"""
    if len(twitter) > 280:
        # 再压：标题截断 48 字符 + 精简标签
        short_t = [t[:48].rstrip() + ("..." if len(t) > 48 else "") for t in en_titles]
        twitter = f"""📡 Signal Pop Daily | {n} News in 3 min

🔹 {short_t[0]}
🔹 {short_t[1]}
🔹 {short_t[2]}
➕ {n-3} more in the video 👇

#SignalPop #DailyNews #China #AI"""
    if len(twitter) > 280:
        # 最后兜底：去掉 emoji 圆点，只留纯文本
        twitter = f"📡 Signal Pop Daily | {n} News in 3 min\n\n{en_titles[0][:55]}\n{en_titles[1][:55]}\n{en_titles[2][:55]}\n+{n-3} more in the video\n\n#SignalPop #DailyNews #China #AI"
    files["twitter.md"] = twitter

    for name, content in files.items():
        with open(os.path.join(OUT_DIR, name), "w", encoding="utf-8") as f:
            f.write(content)
        print(f"  ✓ {name} ({len(content)} chars)")
    print(f"\n全部 {len(files)} 个平台文案已生成到 {OUT_DIR}/")


if __name__ == "__main__":
    main()
