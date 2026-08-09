#!/usr/bin/env python3
"""Signal Pop — 红线过滤（政治敏感黑名单 + 时效闸门）
输出候选池 pass_news.json 供人工审阅，不直接定稿。
"""
import os, sys, json, html, re
from datetime import datetime, timedelta

OUTPUT_DIR = "E:/projects/signal_pop/output"

# ============ 政治敏感硬黑名单（命中即丢，保守优先） ============
POLITICAL_BLOCKLIST = [
    # 涉台
    "台湾", "台灣", "陆委会", "民进党", "国民党", "汉光", "两岸", "台海",
    "台湾海峡", "台独", "台北", "高雄",
    # 涉疆藏
    "新疆", "西藏", "藏独", "疆独",
    # 涉港敏感
    "港独", "反送中", "国安法",
    # 东海南海 / 军事
    "东海", "南海", "钓鱼岛", "印太", "解放军", "国防部", "军演", "演习",
    "导弹", "航母", "核武", "军事基地", "战机",
    # 中美及大国政治
    "中美", "对华", "涉华", "制裁中国", "关税战", "贸易战", "特朗普政府",
    "拜登政府", "特朗普", "拜登", "普京", "泽连斯基",
    # 政体/外交
    "政治局", "两会", "人大", "政协", "总书记", "外交部", "使领馆",
    "外交部长", "国台办", "港澳办",
    # 国际冲突
    "俄乌", "乌克兰", "俄罗斯", "以色列", "伊朗", "巴勒斯坦", "哈马斯",
    "加沙", "战争", "冲突", "袭击", "爆炸", "空袭",
    # 社会动荡
    "抗议", "示威", "游行", "罢工", "骚乱", "维权",
    # 其他红线
    "法轮功", "邪教", "天安门",
]

# ============ 时效闸门（小时） ============
FRESH_HOURS = 48

def is_political(title, summary):
    text = title + " " + summary
    for kw in POLITICAL_BLOCKLIST:
        if kw in text:
            return True, kw
    return False, None

def parse_iso(s):
    try:
        return datetime.strptime(s[:19], "%Y-%m-%dT%H:%M:%S")
    except Exception:
        return None

def main():
    raw = json.load(open(os.path.join(OUTPUT_DIR, "raw_feed.json"), encoding="utf-8"))
    print(f"[redline] 原始 {len(raw)} 条")
    cutoff = datetime.now() - timedelta(hours=FRESH_HOURS)

    seen = set()
    passed = []
    dropped_pol = []
    dropped_old = []
    for e in raw:
        title = html.unescape(e["title"]).strip()
        summary = html.unescape(e.get("summary", "")).strip()
        if len(title) < 5:
            continue
        # 政治
        is_pol, kw = is_political(title, summary)
        if is_pol:
            dropped_pol.append((kw, e["source"], title[:45]))
            continue
        # 时效
        dt = parse_iso(e.get("published_iso", ""))
        if dt is None:
            dropped_old.append(("无时间", e["source"], title[:45]))
            continue
        if dt < cutoff:
            dropped_old.append((dt.strftime("%m-%d"), e["source"], title[:45]))
            continue
        # 去重
        key = title[:30]
        if key in seen:
            continue
        seen.add(key)
        e["title"] = title
        e["summary"] = summary
        e["published_iso"] = dt.strftime("%Y-%m-%d %H:%M")
        passed.append(e)

    # 按时间倒序
    passed.sort(key=lambda x: x["published_iso"], reverse=True)

    out = os.path.join(OUTPUT_DIR, "pass_news.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(passed, f, ensure_ascii=False, indent=2)

    print(f"[redline] 政治命中 {len(dropped_pol)} 条")
    for kw, src, t in dropped_pol:
        print(f"  [POL] ({kw}) {src} | {t}")
    print(f"[redline] 时效/无时间淘汰 {len(dropped_old)} 条（仅列前8）")
    for d, src, t in dropped_old[:8]:
        print(f"  [OLD] ({d}) {src} | {t}")
    print(f"[redline] 红线通过候选 {len(passed)} 条 -> {out}")
    print("\n===== 候选池（按时间倒序） =====")
    for i, e in enumerate(passed, 1):
        print(f"{i:2d}. [{e['published_iso'][5:]}] {e['source']} | {e['title'][:52]}")

if __name__ == "__main__":
    main()
