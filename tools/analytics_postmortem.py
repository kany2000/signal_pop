#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Signal Pop — 归因复盘（参考 Easel content-postmortem / data-tracker）

本地可跑部分（无需登录）：
  - 解析 publish.log 得到各平台发布成败
  - 结合 parsed_news.json 做内容盘点（新闻条数 / 选题配比）
  - 复用 quality_gate 的发现，给出「下期改进建议」
  - 产出 output/<kind>/<date>/postmortem.md

需登录态的部分（scaffold，待接入）：
  - record_snapshot()：从各平台创作者后台拉取 粉丝/播放/互动 快照
    （Easel 用 skill-my-account / skill-data-tracker，需 Playwright 登录态）
  - 数据回填后再跑 postmortem 可追加「表现归因」段落

用法：
  python tools/analytics_postmortem.py 20260908
  python tools/analytics_postmortem.py 20260908 --kind weekly
  python tools/analytics_postmortem.py 20260908 --snapshot   # 拉数（需登录，未配则跳过）
"""
import os
import sys
import json
import argparse

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLATFORMS = ["douyin", "kuaishou", "bilibili", "xiaohongshu", "zhihu",
             "channels", "facebook", "youtube", "twitter"]


def parse_publish_log(path):
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8", errors="replace") as f:
        txt = f.read()
    res = {}
    for plat in PLATFORMS:
        if f"✅ {plat}" in txt:
            res[plat] = True
        elif f"❌ {plat}" in txt:
            res[plat] = False
    return res


def content_inventory(date_dir):
    pj = os.path.join(date_dir, "parsed_news.json")
    if not os.path.exists(pj):
        return None
    with open(pj, encoding="utf-8") as f:
        items = json.load(f)
    # 选题配比（按 category 字段，若存在）
    cats = {}
    for it in items:
        c = it.get("category") or it.get("cat") or "未分类"
        cats[c] = cats.get(c, 0) + 1
    return {"count": len(items), "cats": cats}


def improvements_from_quality_gate(date_dir):
    """复用 quality_gate 的扫描（避免重复实现）"""
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from quality_gate import PLATFORMS as QP, scan_text
    except Exception:
        return []
    notes = []
    for plat in QP:
        p = os.path.join(date_dir, f"{plat}.md")
        if not os.path.exists(p):
            continue
        with open(p, encoding="utf-8") as f:
            txt = f.read()
        for fnd in scan_text(txt):
            if fnd["sev"] == "HIGH" and fnd["type"] == "truncation":
                notes.append(f"{plat}.md 第{fnd['line']}行存在截断残留「…」，下期需在生成阶段防截断")
                break
    return notes


def record_snapshot(date, kind):
    """⚠️ 需登录态：从平台后台拉 粉丝/播放/互动 快照。当前为 scaffold。"""
    print("  ⚠️ record_snapshot 需要平台登录态（Playwright），本期未接入，跳过。")
    print("     接入方式：复用 publish_xhs/zhihu/channels 的 storage_state，"
          "调用各平台创作者 API 或页面抓取后写回 output/<kind>/<date>/metrics.json")
    return None


def build_postmortem(date, kind, do_snapshot=False):
    date_dir = os.path.join(PROJECT_ROOT, "output", kind, date)
    if not os.path.isdir(date_dir):
        raise SystemExit(f"期目录不存在: {date_dir}")

    pub = parse_publish_log(os.path.join(date_dir, "publish.log"))
    inv = content_inventory(date_dir)
    notes = improvements_from_quality_gate(date_dir)
    snap = record_snapshot(date, kind) if do_snapshot else None

    lines = []
    lines.append(f"# 发布复盘 · {date}（{kind}）\n")
    lines.append("## 一、发布概况")
    if pub:
        for plat, ok in pub.items():
            lines.append(f"- {'✅' if ok else '❌'} {plat}")
    else:
        lines.append("- （无 publish.log，未解析到发布结果）")
    lines.append("")

    lines.append("## 二、内容盘点")
    if inv:
        lines.append(f"- 新闻条数：{inv['count']}")
        if inv["cats"]:
            lines.append("- 选题配比：" + "、".join(f"{k}×{v}" for k, v in inv["cats"].items()))
    else:
        lines.append("- （无 parsed_news.json）")
    lines.append("")

    lines.append("## 三、下期改进建议")
    if notes:
        for n in notes:
            lines.append(f"- {n}")
    else:
        lines.append("- 本期质检无高风险项，保持。")
    lines.append("")

    if snap:
        lines.append("## 四、表现归因（来自平台数据）")
        lines.append(json.dumps(snap, ensure_ascii=False, indent=2))
        lines.append("")

    out = os.path.join(date_dir, "postmortem.md")
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"✅ 复盘已写: {out}")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("date")
    ap.add_argument("--kind", default="daily")
    ap.add_argument("--snapshot", action="store_true", help="拉平台数据（需登录，未配则跳过）")
    args = ap.parse_args()
    build_postmortem(args.date, args.kind, args.snapshot)


if __name__ == "__main__":
    main()
