#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Signal Pop — 每日版 Remotion 数据导出器

把每日版产线中间产物（parsed_news.json + audio/tts_segments.json + images/*.jpg）
导出为 Remotion 可用的：
  1. remotion_poc/public/ 下的配图（带 daily_{date}_ 前缀，避免与周末版冲突）
  2. remotion_poc/src/daily_segs.json（段数据契约：type/num/section/title/body/image/dur）

用法：python tools/export_daily_remotion.py [PREP_DATE]
随后：node remotion-cli.js render DailyNews out/DailyNews_silent.mp4 --codec=h264
"""
import os
import sys
import json
import shutil
import re

PROJECT_ROOT = "E:/projects/signal_pop"
REMOTION_PUBLIC = os.path.join(PROJECT_ROOT, "remotion_poc", "public")
REMOTION_SRC = os.path.join(PROJECT_ROOT, "remotion_poc", "src")

PREP_DATE = sys.argv[1] if len(sys.argv) > 1 else "20260823"
OUT_DIR = os.path.join(PROJECT_ROOT, "output", "daily", PREP_DATE)
PARSED = os.path.join(OUT_DIR, "parsed_news.json")
SEGMENTS = os.path.join(OUT_DIR, "audio", "tts_segments.json")
IMAGES_DIR = os.path.join(OUT_DIR, "images")

PREFIX = f"daily_{PREP_DATE}_"

# 开场/结尾背景（复用配图目录里的 opening_bg/ending_bg，若无则用 01.jpg 兜底）


def build_segs(items, durations, images_map):
    """构造 Remotion 段数据：intro + history(num=0) + news(1..10) + outro。
    durations 顺序 = [intro, item0, item1..item10, outro]（与 win_pipeline_tts.build_segments 一致）。
    """
    # 确定开场/结尾背景
    opening = "opening_bg.jpg" if os.path.exists(os.path.join(IMAGES_DIR, "opening_bg.jpg")) else "01.jpg"
    ending = "ending_bg.jpg" if os.path.exists(os.path.join(IMAGES_DIR, "ending_bg.jpg")) else "10.jpg"

    segs = []
    # intro（段 0）
    segs.append({
        "type": "intro", "num": 0, "section": "开场", "title": "隔天信号弹",
        "body": "这里是隔天信号弹，欢迎收看本期信号弹，以下是本期精选的核心新闻。",
        "image": images_map.get("opening", opening), "dur": durations[0],
    })
    # 新闻段（durations[1..N] 对应 items 顺序：num=0 历史在前）
    for i, item in enumerate(items):
        n = item.get("num", 0)
        dur = durations[1 + i] if (1 + i) < len(durations) else 8.0
        if n == 0:
            segs.append({
                "type": "history", "num": 0, "section": "历史",
                "title": "历史上的今天",
                "body": item.get("full_body", item.get("body", "")),
                "image": images_map.get(0, "00.jpg"), "dur": dur,
            })
        else:
            segs.append({
                "type": "news", "num": n, "section": item.get("section", "综合"),
                "title": item.get("title", ""),
                "body": item.get("full_body", item.get("body", "")),
                "image": images_map.get(n, f"{n:02d}.jpg"), "dur": dur,
            })
    # outro（最后一段）
    segs.append({
        "type": "outro", "num": 99, "section": "结尾", "title": "一键三连",
        "body": "喜欢本期内容？一键三连支持我们！互动话题：您最关注哪条新闻？欢迎在评论区留言讨论！",
        "image": images_map.get("ending", ending), "dur": durations[-1] if durations else 12.0,
    })
    return segs


def main():
    if not os.path.exists(PARSED) or not os.path.exists(SEGMENTS):
        print(f"❌ 缺少 parsed_news.json 或 tts_segments.json: {OUT_DIR}")
        sys.exit(1)
    items = json.load(open(PARSED, encoding="utf-8"))
    durations = json.load(open(SEGMENTS, encoding="utf-8"))
    expect = len(items) + 2  # intro + items + outro
    if len(durations) != expect:
        print(f"❌ durations({len(durations)}) != items({len(items)})+2")
        sys.exit(1)

    os.makedirs(REMOTION_PUBLIC, exist_ok=True)
    os.makedirs(REMOTION_SRC, exist_ok=True)

    # 复制配图到 public/（带前缀）
    images_map = {}
    for fname in sorted(os.listdir(IMAGES_DIR)) if os.path.isdir(IMAGES_DIR) else []:
        if not fname.endswith(".jpg"):
            continue
        # 跳过 opening_bg/ending_bg 之外的临时文件，只复制 00-NN + opening/ending
        key = None
        if re.fullmatch(r"\d{2}\.jpg", fname):
            key = int(fname[:2])
        elif fname == "opening_bg.jpg":
            key = "opening"
        elif fname == "ending_bg.jpg":
            key = "ending"
        else:
            continue
        dst = os.path.join(REMOTION_PUBLIC, PREFIX + fname)
        if not os.path.exists(dst) or os.path.getmtime(os.path.join(IMAGES_DIR, fname)) > os.path.getmtime(dst):
            shutil.copy2(os.path.join(IMAGES_DIR, fname), dst)
        images_map[key] = PREFIX + fname

    # 复制头像到 public/（avatar_<发布日>.png）
    avatar_src = None
    from datetime import datetime, timedelta
    pub = (datetime.strptime(PREP_DATE, "%Y%m%d") + timedelta(days=1)).strftime("%Y%m%d")
    av_path = os.path.join(OUT_DIR, f"avatar_{pub}.png")
    if os.path.exists(av_path):
        avatar_src = f"avatar_daily_{PREP_DATE}.png"
        shutil.copy2(av_path, os.path.join(REMOTION_PUBLIC, avatar_src))
        print(f"  avatar -> public/{avatar_src}")

    # 写 daily_meta.json（发布日期/星期/头像），供 Root.tsx defaultProps 读取，
    # 避免硬编码过期（20260901 教训：defaultProps 停留在 8/23 POC，片头片尾日期与头像全错）
    pub_dt = datetime.strptime(PREP_DATE, "%Y%m%d") + timedelta(days=1)
    weekday = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"][pub_dt.weekday()]
    pub_date_fmt = f"{pub_dt.year}年{pub_dt.month:02d}月{pub_dt.day:02d}日"
    meta = {"pubDate": pub_date_fmt, "weekday": weekday, "avatar": avatar_src or ""}
    with open(os.path.join(REMOTION_SRC, "daily_meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)

    segs = build_segs(items, durations, images_map)
    out = os.path.join(REMOTION_SRC, "daily_segs.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(segs, f, ensure_ascii=False, indent=1)
    total = sum(s["dur"] for s in segs)
    print(f"✅ daily_segs.json 已导出: {len(segs)} 段, 总长 {total:.2f}s")
    for s in segs:
        print(f"  [{s['type']:7}] #{s['num']:02d} {s['title'][:26]:28} {s['dur']:.2f}s  img={s['image']}")
    print(f"  avatar={avatar_src or '无'}")


if __name__ == "__main__":
    main()
