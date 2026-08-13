#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Signal Pop — 发布前质检（每期交付前必须通过，防止截断/缺失/损坏）

用法：python tools/check_publish_ready.py [PREP_DATE]
检查项：
  1. 视频存在且 > 5MB
  2. 封面 3:4 / 16:9 存在
  3. 8 个平台文案存在且非空
  4. 文案「标题/简介」字段非空
  5. 「历史上的今天」不截断（以完整句号/感叹号结尾）
  6. parsed_news.json 存在且新闻数 >= 10
  7. 中英文 SRT 存在
任一项 FAIL 则返回非 0，禁止发布。
"""
import os
import sys
import re

PROJECT_ROOT = "E:/projects/signal_pop"
PREP_DATE = sys.argv[1] if len(sys.argv) > 1 else None
if not PREP_DATE:
    print("用法: python tools/check_publish_ready.py YYYYMMDD")
    sys.exit(2)

OUT = os.path.join(PROJECT_ROOT, "output", "daily", PREP_DATE)
PLATFORMS = ["douyin", "kuaishou", "bilibili", "xiaohongshu", "zhihu", "facebook", "youtube", "twitter"]

fails = []
warns = []


def chk(ok, item, detail=""):
    tag = "✅" if ok else "❌"
    print(f"  {tag} {item}" + (f" — {detail}" if detail else ""))
    if not ok:
        fails.append(item)


def read_md(name):
    p = os.path.join(OUT, f"{name}.md")
    if not os.path.exists(p):
        return ""
    with open(p, encoding="utf-8") as f:
        return f.read()


def extract(md_text, key):
    m = re.search(rf"^{key}[：:]\s*(.+?)(?:\n\n|\Z)", md_text, re.S | re.M)
    m = m or re.search(rf"^{key}[：:]\s*(.+)$", md_text, re.S | re.M)
    return m.group(1).strip() if m else ""


print(f"═══ 发布前质检 · {PREP_DATE} ═══")

# 1. 视频
video = os.path.join(OUT, f"signal_pop_daily_{PREP_DATE}.mp4")
v_ok = os.path.exists(video) and os.path.getsize(video) > 5 * 1024 * 1024
chk(v_ok, "视频文件存在且 >5MB",
    f"{os.path.getsize(video)//1024//1024}MB" if os.path.exists(video) else "缺失")

# 2. 封面
for c in ["cover_3x4", "cover_16x9"]:
    # 封面按发布日命名：发布日 = 制作日 + 1
    from datetime import datetime, timedelta
    pub = (datetime.strptime(PREP_DATE, "%Y%m%d") + timedelta(days=1)).strftime("%Y%m%d")
    # 支持两种命名：cover_{pub}_{ratio}.png 或 cover_{PREP}_{ratio}.png
    found = False
    for base in [pub, PREP_DATE]:
        p = os.path.join(OUT, f"cover_{base}_{c.split('_')[1]}.png")
        if os.path.exists(p):
            found = True
            break
    chk(found, f"封面 {c}")

# 3. 平台文案
for plat in PLATFORMS:
    md = read_md(plat)
    chk(bool(md.strip()), f"{plat}.md 非空")

# 4. 标题/简介（与实际发布脚本提取逻辑一致：
#    有"标题："字段用之，否则取首行；简介字段缺失的平台（小红书/知乎）不强制）
for plat in ["douyin", "kuaishou", "bilibili", "xiaohongshu", "zhihu"]:
    md = read_md(plat)
    if not md.strip():
        continue
    t = extract(md, "标题") or md.strip().splitlines()[0].strip()
    d = extract(md, "简介")
    chk(bool(t), f"{plat}.md 标题", t[:40] + "..." if t else "空")
    # 发布脚本对 douyin/kuaishou 强制简介；bilibili 有"正文/标题"兜底
    if plat in ("douyin", "kuaishou"):
        chk(bool(d), f"{plat}.md 简介", d[:30] + "..." if d else "空")

# 5. 历史上的今天不截断（仅检查含"📜 历史上的今天："正文的平台；
#    bilibili 分段时间轴"00:11 1. 历史上的今天"不算正文）
for plat in PLATFORMS:
    md = read_md(plat)
    m = re.search(r"📜 历史上的今天：(.+?)(?:\n|$)", md)
    if m:
        line = m.group(1).strip()
        ok = line.endswith("。") or line.endswith("！") or line.endswith(".")
        chk(ok, f"{plat}.md 历史上的今天完整",
            f"结尾: ...{line[-12:]}" if ok else f"疑似截断: ...{line[-12:]}")

# 6. parsed_news.json
pj = os.path.join(OUT, "parsed_news.json")
if os.path.exists(pj):
    import json
    with open(pj, encoding="utf-8") as f:
        items = json.load(f)
    chk(len(items) >= 11, "parsed_news.json 条目数", f"{len(items)} 条")
else:
    chk(False, "parsed_news.json 存在")

# 7. SRT（命名规则：signal_pop_daily/weekly_yyyymmdd.en_US.srt）
zh_daily = os.path.join(OUT, f"signal_pop_daily_{PREP_DATE}.srt")
zh_weekly = os.path.join(OUT, f"signal_pop_weekly_{PREP_DATE}.srt")
zh_srt = zh_daily if os.path.exists(zh_daily) else zh_weekly
kind = "daily" if os.path.exists(zh_daily) else "weekly"
en_srt = os.path.join(OUT, f"signal_pop_{kind}_{PREP_DATE}.en_US.srt")
chk(os.path.exists(zh_srt), "中文字幕 SRT")
chk(os.path.exists(en_srt), "英文字幕 SRT (.en_US)")

# 结果
print(f"\n═══ 结果：{'✅ 全部通过，可以发布' if not fails else '❌ %d 项未通过，禁止发布' % len(fails)} ═══")
if fails:
    for f in fails:
        print(f"  ❌ {f}")
if warns:
    for w in warns:
        print(f"  ⚠️ {w}")
sys.exit(0 if not fails else 1)
