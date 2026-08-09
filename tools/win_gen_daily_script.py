#!/usr/bin/env python3
"""Signal Pop — Windows 版每日脚本生成器

读取 output/filtered_news.json（由 win_fetch_news.py + win_filter_news.py 产出），
做基础清理（去重/去垃圾）+ 中文分类，写出 archive/signal_pop_daily_{prod_date}.txt。
发布日 = 制作日 + 1 天（视频开头播报用发布日）。

用法:
    python tools/win_gen_daily_script.py [制作日期YYYYMMDD]
    制作日期缺省 = 今天。发布日期 = 制作日期 + 1。
"""
import os
import sys
import json
from datetime import datetime, timedelta

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEEKDAYS = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]


def classify(text: str) -> str:
    if any(k in text for k in ["AI", "人工智能", "科技", "芯片", "模型", "机器人",
                                "SpaceX", "卫星", "NASA", "Meta", "算力", "大模型"]):
        return "科技"
    if any(k in text for k in ["中国", "国内", "北京", "A股", "华为", "腾讯", "阿里",
                               "比亚迪", "宁德", "京东", "小米", "我国"]):
        return "国内"
    return "国际"


def generate(prod_date: str):
    prod_dt = datetime.strptime(prod_date, "%Y%m%d")
    pub_dt = prod_dt + timedelta(days=1)
    pub_str = pub_dt.strftime("%Y年%m月%d日")
    pub_weekday = WEEKDAYS[pub_dt.weekday()]

    with open(os.path.join(BASE, "output", "filtered_news.json"), encoding="utf-8") as f:
        items = json.load(f)

    # 基础清理：去掉无摘要噪声、标题去重
    seen = set()
    clean = []
    for it in items:
        title = (it.get("title") or "").strip()
        summary = (it.get("summary") or "").strip()
        if len(summary) < 10:
            continue
        key = title[:20]
        if key in seen:
            continue
        seen.add(key)
        clean.append(it)

    header = f"这里是隔天信号弹，今天是{pub_str}，{pub_weekday}。\n以下是今天的主要新闻。\n\n"
    lines = []
    for i, it in enumerate(clean[:10], 1):
        cat = classify(it["title"] + it.get("summary", ""))
        line = f"第{i}条，[{cat}]新闻。{it['title']}。据 {it.get('source', '')} 报道，{it.get('summary', '')[:100]}"
        lines.append(line)
    footer = "\n\n以上是本期的信号弹，我们下期见。"

    txt = header + "\n".join(lines) + footer
    out_path = os.path.join(BASE, "archive", f"signal_pop_daily_{prod_date}.txt")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(txt)
    print(f"[script] ✅ 已生成 {out_path}（{len(clean[:10])} 条，发布日 {pub_str} {pub_weekday}）")
    print("=" * 50)
    print(txt)
    print("=" * 50)


if __name__ == "__main__":
    prod = sys.argv[1] if len(sys.argv) > 1 else datetime.now().strftime("%Y%m%d")
    generate(prod)
