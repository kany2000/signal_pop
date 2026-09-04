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
    # 断点复用：现有 SRT 全英文且句数一致时按序复用译文，仅含中文的行才重翻（避免限流拖慢整轮）
    # 注意：本脚本写出的 SRT 块间为单换行，必须按「序号行」扫描分块，不能按空行 split
    old_srt = os.path.join(OUT, f"signal_pop_weekly_{PREP_DATE}.en_US.srt")
    if os.path.exists(old_srt):
        raw = open(old_srt, encoding="utf-8").read().splitlines()
        old_en, i = [], 0
        while i < len(raw):
            if raw[i].strip().isdigit():
                i += 1
                if i < len(raw) and "-->" in raw[i]:
                    i += 1
                txt = []
                while i < len(raw) and not raw[i].strip().isdigit() and raw[i].strip() != "":
                    txt.append(raw[i])
                    i += 1
                if txt:
                    old_en.append("\n".join(txt))
            else:
                i += 1
        if len(old_en) == len(pend):
            for p, en in zip(pend, old_en):
                if en and not re.search(r"[\u4e00-\u9fff]", en):
                    p["en"] = en
            reused = sum(1 for p in pend if p["en"] is not None)
            print(f"  [srt] 复用现有译文 {reused}/{len(pend)} 句", flush=True)
    # 逐段翻译；成功缓存，失败退避重试（限流解除后自动补齐）
    delays = [15, 30, 60, 120, 240, 300]
    round_n = 0
    while True:
        failed = []
        for p in pend:
            if p["en"] is not None:
                continue
            print(f"  [srt] 翻译段 {p['i']}: {p['text'][:20]}…", flush=True)
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
# label 动态从 parsed_news.json 构建（img -> 标题），避免每期硬编码漏更
BG_LABEL_STATIC = {
    "breaking.jpg": "特别报道",
    "summary.jpg": "本周之最",
    "watch.jpg": "下周看点",
    "interactive.jpg": "互动话题",
    "pick.jpg": "每期精选",
}


def build_timeline():
    bg2label = dict(BG_LABEL_STATIC)
    news_no = 0
    for it in parsed:
        img = it.get("img", "")
        if it.get("type") == "news" and img:
            news_no += 1
            bg2label[img] = f"要闻{news_no} {it['title'][:18]}"
        elif it.get("type") == "breaking" and img:
            bg2label[img] = f"特别报道 {it['title'][:18]}"
    lines = []
    acc = 0.0
    seen = {}
    for d, du in zip(dlg, tts):
        bg = d.get("bg", "")
        if bg not in seen:
            label = bg2label.get(bg, bg)
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

    # 6/7/8. 海外三平台（全英文铁律：把新闻标题逐条翻译，失败重试，仍失败才告警）
    en_cache = {}
    cache_path = os.path.join(OUT, "_en_title_cache.json")
    if os.path.exists(cache_path):
        try:
            en_cache = json.load(open(cache_path, encoding="utf-8"))
        except Exception:
            en_cache = {}

    def tr_title(s):
        if s in en_cache:
            return en_cache[s]
        t = None
        for _ in range(3):
            t = translate_one(s)
            if t:
                break
            time.sleep(2)
        t = (t or s).strip()
        if not t.endswith("."):
            t += "."
        if t != s:  # 仅缓存真实译文，中文 fallback 不入缓存
            en_cache[s] = t
            json.dump(en_cache, open(cache_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        return t

    en_titles = [tr_title(s) for s in shorts]
    bad = [s for s, t in zip(shorts, en_titles) if re.search(r"[\u4e00-\u9fff]", t)]
    if bad:
        print(f"  ⚠️ 海外平台标题仍有中文（翻译失败）: {bad}")

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
    if len(twitter) > 280:
        # 第三级兜底：标题各自截短到 80 字符（禁硬截断整条文案）
        short3 = [t[:80].rstrip() + ("…" if len(t) > 80 else "") for t in en_titles[:3]]
        twitter = f"""📡 Signal Pop Weekly | {n} News in 9 min

🔹 {short3[0]}
🔹 {short3[1]}
🔹 {short3[2]}
➕ {n-3} more 👇

#SignalPop #News"""
    assert len(twitter) <= 280, f"twitter 文案超长: {len(twitter)}"
    files["twitter.md"] = twitter

    return files


def main():
    os.makedirs(OUT, exist_ok=True)
    print("[main] build_en_srt ...", flush=True)
    build_en_srt()
    print("[main] build_files ...", flush=True)
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

