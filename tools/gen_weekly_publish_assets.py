#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Signal Pop · 周末版（信蓝组合）发布资产生成器
产出：
  1. signal_pop_weekly_{DATE}.en_US.srt  —— 英文外挂字幕（从双人对话稿翻译，含时间轴）
  2. 8 平台文案 .md —— 抖音/快手/B站/小红书/知乎/Facebook/YouTube/Twitter
源数据：dialogue_segments.json（台词）+ audio/tts_segments.json（时间轴）+ parsed_news.json（标题）
用法：python tools/gen_weekly_publish_assets.py [PREP_DATE]
"""
import os
import re
import sys
import time
import json
import urllib.parse
import urllib.request
from datetime import datetime, timedelta

PROJECT_ROOT = "E:/projects/signal_pop"
PREP_DATE = sys.argv[1] if len(sys.argv) > 1 else "20260828"
OUT = os.path.join(PROJECT_ROOT, "output", "weekly", PREP_DATE)

PUB_DT = datetime.strptime(PREP_DATE, "%Y%m%d") + timedelta(days=1)
PUB_DATE = PUB_DT.strftime("%Y%m%d")
PUB_DATE_FMT = f"{PUB_DT.year}年{PUB_DT.month:02d}月{PUB_DT.day:02d}日"
PUB_DATE_SHORT = f"{PUB_DT.year}.{PUB_DT.month:02d}.{PUB_DT.day:02d}"
PUB_WEEKDAY = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"][PUB_DT.weekday()]
M_D = f"{PUB_DT.month}月{PUB_DT.day}日"


def load_json(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


dlg = load_json(os.path.join(OUT, "dialogue_segments.json"))
tts = load_json(os.path.join(OUT, "audio", "tts_segments.json"))
parsed = load_json(os.path.join(OUT, "parsed_news.json"))


def _http_get_json(url, data=None, headers=None):
    req = urllib.request.Request(url, data=data, headers=headers or {"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode("utf-8"))


def translate_one(text):
    """返回英文翻译；任一接口成功即返回，失败返回 None（由调用方决定重试）。"""
    q = urllib.parse.quote(text[:500])
    # 1) MyMemory（免费，当前可用，优先）
    try:
        d = _http_get_json(f"https://api.mymemory.translated.net/get?q={q}&langpair=zh-CN|en")
        if d.get("responseStatus") == 200:
            t = d["responseData"]["translatedText"].strip()
            if t and not t.startswith("MYMEMORY WARNING"):
                return t
    except Exception:
        pass
    # 2) Google gtx（免费非官方端点，质量较好，偶发可用）
    try:
        d = _http_get_json(
            f"https://translate.googleapis.com/translate_a/single?client=gtx&q={q}&sl=zh-CN&tl=en"
        )
        t = d[0][0][0]
        if t and t != text:
            return t
    except Exception:
        pass
    # 3) LibreTranslate 公网实例（无密钥，SSL 不稳）
    try:
        data = json.dumps({"q": text[:500], "source": "zh", "target": "en", "format": "text"}).encode()
        d = _http_get_json(
            "https://translate.astian.org/translate",
            data=data,
            headers={"Content-Type": "application/json"},
        )
        t = d.get("translatedText")
        if t:
            return t
    except Exception:
        pass
    return None


# ── 1. 英文 SRT（含时间轴）──
def srt_ts(sec):
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = int(sec % 60)
    ms = int((sec - int(sec)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def build_en_srt():
    acc = 0.0
    pend = []
    for i, (d, du) in enumerate(zip(dlg, tts), 1):
        start = acc
        end = acc + du["dur"]
        acc = end
        spk = "Axin" if d["speaker"] == "阿信" else "Xiaolan"
        pend.append({"i": i, "spk": spk, "text": d["text"], "start": start, "end": end, "en": None})
    # 逐段翻译；成功缓存，失败退避重试（限流解除后自动补齐）
    delays = [15, 30, 60, 120, 240, 300]
    round_n = 0
    while True:
        failed = []
        for p in pend:
            if p["en"] is not None:
                continue
            t = translate_one(f'{p["spk"]}: {p["text"]}')
            if t:
                p["en"] = t
            else:
                failed.append(p)
            time.sleep(1.0)
        if not failed:
            break
        round_n += 1
        if round_n > len(delays):
            for p in failed:
                p["en"] = f'{p["spk"]}: {p["text"]}'  # 最终兜底：原文占位
            break
        print(f"  [retry {round_n}] {len(failed)} 段未翻出，{delays[round_n-1]}s 后重试…")
        time.sleep(delays[round_n - 1])
    blocks = [f'{p["i"]}\n{srt_ts(p["start"])} --> {srt_ts(p["end"])}\n{p["en"]}' for p in pend]
    out = os.path.join(OUT, f"signal_pop_weekly_{PREP_DATE}.en_US.srt")
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(blocks))
    print(f"  ✓ 英文 SRT: {out} ({len(blocks)} 段)")


# ── 2. 8 平台文案 ──
def short_of(title):
    t = title
    for p in ["：", ":", "｜", "|", "“", "”", '"']:
        t = t.replace(p, "")
    return t.strip()


# 核心新闻标题（突发 + 14 条要闻）
core = []
for it in parsed:
    if it["type"] in ("breaking", "news"):
        core.append(it)
summ = next((x for x in parsed if x["type"] == "summary"), None)
watch = next((x for x in parsed if x["type"] == "watch"), None)
inter = next((x for x in parsed if x["type"] == "interactive"), None)

shorts = [short_of(c["title"]) for c in core]
n = len(core)
breaking_title = core[0]["title"] if core else ""
title_top3 = "、".join(shorts[:3])
CIRC = "①②③④⑤⑥⑦⑧⑨⑩⓫⓬⓭⓮⓯"


def fmt_ts(sec):
    m = int(sec // 60)
    s = int(sec % 60)
    return f"{m:02d}:{s:02d}"


# B站分段时间轴（按 dialogue 段 bg 分组取起始时间）
def build_timeline():
    lines = []
    acc = 0.0
    seen = {}
    for d, du in zip(dlg, tts):
        bg = d.get("bg", "")
        if bg not in seen:
            label = {
                "breaking.jpg": "突发消息",
                "news_01.jpg": "要闻1 英伟达×SpaceX",
                "news_02.jpg": "要闻2 常州应届生劝退",
                "news_03.jpg": "要闻3 孙宇晨长文",
                "news_04.jpg": "要闻4 三台风袭沿海",
                "news_05.jpg": "要闻5 OpenAI芯片",
                "news_06.jpg": "要闻6 中消协AI客服",
                "news_07.jpg": "要闻7 苹果M6",
                "news_08.jpg": "要闻8 小鹏机器人",
                "news_09.jpg": "要闻9 欧洲热浪",
                "news_10.jpg": "要闻10 上海沪八条",
                "news_11.jpg": "要闻11 育儿补贴",
                "news_12.jpg": "要闻12 民生新规",
                "news_13.jpg": "要闻13 章子怡套现",
                "news_14.jpg": "要闻14 金鹰奖",
                "summary.jpg": "本周之最",
                "watch.jpg": "下周看点",
                "interactive.jpg": "互动话题",
            }.get(bg, bg)
            lines.append(f"{fmt_ts(acc)} {label}")
            seen[bg] = True
        acc += du["dur"]
    return lines


timeline = build_timeline()


def build_files():
    files = {}

    # 1. 抖音
    files["douyin.md"] = f"""标题：{M_D}信号弹｜信蓝组合周末版：{title_top3}！{n}条本周大事

简介：每周六8点，阿信和小蓝陪你聊透本周{n}件大事！

🔥 本期看点：
""" + "\n".join(f"{i+1}️⃣ {s}" for i, s in enumerate(shorts)) + f"""

#隔天信号弹 #信蓝组合 #周末新闻 #今日热点 #新闻播报 #科技资讯 #AI新闻 #热点新闻 #每周播报

正文：
隔天信号弹·周末特别版，阿信和小蓝每周六为你精选{n}条核心新闻。"""

    # 2. 快手
    files["kuaishou.md"] = f"""标题：{M_D}信号弹｜信蓝组合：{n}条本周大事：{title_top3}

简介：每周六8点，听阿信小蓝唠透天下事！本周{n}条新闻全在这里👇

🔥 本期热点：
""" + "\n".join(f"{CIRC[i] if i < len(CIRC) else i+1} {s}" for i, s in enumerate(shorts)) + f"""

#隔天信号弹 #信蓝组合 #新闻早报 #热点 #每周播报 #科技 #财经 #民生 #资讯

正文：
隔天信号弹·周末特别版，阿信和小蓝每周六为你精选{n}条核心新闻。"""

    # 3. B站
    files["bilibili.md"] = f"""【{M_D}信号弹·信蓝组合】{title_top3}｜本周{n}条大事

📌 本期时间轴：
""" + "\n".join(timeline) + f"""

每周六8点，阿信和小蓝陪你聊透本周大事。记得三连支持一下~

#隔天信号弹 #信蓝组合 #周末新闻 #新闻早报 #科技 #财经 #民生 #资讯

（以下为视频文案，供字幕参考）
这里是隔天信号弹周末特别版，{PUB_DATE_FMT}，{PUB_WEEKDAY}，我是阿信，我是小蓝。"""

    # 4. 小红书
    files["xiaohongshu.md"] = f"""本周{n}条大事，阿信小蓝陪你聊透 📺✨

宝子们周六好呀☀️ 信号弹周末特别版来咯～
阿信和小蓝每周六8点，陪你速览本周大事👇

""" + "\n".join(f"{CIRC[i] if i < len(CIRC) else i+1}️⃣ {s}" for i, s in enumerate(shorts)) + f"""

你最关注哪一条？评论区聊聊呀💬
记得关注不迷路，每周六8点见哦～

#周末新闻 #隔天信号弹 #信蓝组合 #今日热点 #科技资讯 #民生新闻 #信息差 #认知升级 #每周热点 #快讯"""

    # 5. 知乎
    files["zhihu.md"] = f"""隔天信号弹 · 信蓝组合 | {M_D}周末新闻（本周{n}条）

""" + "\n".join(f"{i+1}. {s}" for i, s in enumerate(shorts)) + """

完整内容见视频。欢迎关注，每周六 8 点更新。"""

    # 6/7/8. 海外三平台（英文，从英文 SRT 提取标题句）
    en_srt = os.path.join(OUT, f"signal_pop_weekly_{PREP_DATE}.en_US.srt")
    en_titles = []
    if os.path.exists(en_srt):
        blocks = re.split(r"\n\n+", open(en_srt, encoding="utf-8").read().strip())
        for b in blocks:
            lines = b.strip().split("\n")
            if len(lines) >= 3:
                t = lines[2]
                t = re.sub(r"^(Axin|Xiaolan):\s*", "", t)
                t = t.split(". ")[0].strip()
                if not t.endswith("."):
                    t += "."
                if t:
                    en_titles.append(t)
    # 英文标题一般 > n 条（含开场/收尾），取要闻部分前 n 条
    if len(en_titles) < n:
        en_titles = [s[:60] for s in shorts[:n]]
    en_titles = en_titles[:n]

    files["facebook.md"] = f"""📡 Signal Pop Weekly | {PUB_DATE_SHORT} Weekend News Briefing

Top {n} stories this week (by Axin & Xiaolan):
""" + "\n".join(f"{i+1}. {t}" for i, t in enumerate(en_titles)) + """

Every Saturday in 9 minutes, catch up on what's happening in the world. Follow & share!

#SignalPop #WeeklyNews #ChinaNews #Technology #News"""

    files["youtube.md"] = f"""📡 Signal Pop Weekly | {PUB_DATE_SHORT} - {n} Core News Stories

This Week's Top {n}:
""" + "\n".join(f"{i+1}. {t}" for i, t in enumerate(en_titles)) + """

Every Saturday on Signal Pop. Subscribe for weekly China & tech news.
SignalPop,WeeklyNews,China,Technology,News,AI"""

    twitter = f"""📡 Signal Pop Weekly | {n} News in 9 min

This week's top stories:
🔹 {en_titles[0]}
🔹 {en_titles[1]}
🔹 {en_titles[2]}
➕ {n-3} more in the video 👇

#SignalPop #WeeklyNews #China #Technology #News #AI #Weather"""
    if len(twitter) > 280:
        twitter = f"""📡 Signal Pop Weekly | {n} News in 9 min

🔹 {en_titles[0]}
🔹 {en_titles[1]}
🔹 {en_titles[2]}
➕ {n-3} more in the video 👇

#SignalPop #WeeklyNews #China #News #AI"""
    files["twitter.md"] = twitter

    return files


def main():
    os.makedirs(OUT, exist_ok=True)
    build_en_srt()
    files = build_files()
    for name, content in files.items():
        with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
            f.write(content)
        print(f"  ✓ {name} ({len(content)} chars)")
    print(f"\n全部 {len(files)} 个平台文案 + 英文 SRT 已生成到 {OUT}/")


if __name__ == "__main__":
    import sys, traceback
    LOG = os.path.join(OUT, "_asset_run.log")
    with open(LOG, "w", encoding="utf-8") as lf:
        lf.write("START\n")
    # 将 stdout/stderr 重定向到日志文件，避免控制台输出捕获异常导致进程被杀
    _lf = open(LOG, "a", encoding="utf-8")
    sys.stdout = _lf
    sys.stderr = _lf
    try:
        main()
        _lf.write("DONE\n")
    except Exception:
        _lf.write("ERROR\n")
        traceback.print_exc(file=_lf)
    finally:
        _lf.flush()
        _lf.close()

