#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Signal Pop — 发布前合规质检（参考 Easel quality-gate / risk-scanner）

在 check_publish_ready.py（完整性/截断）之外，追加「合规风险」扫描：
  1. 截断残留：行尾出现 「…」或「...」→ 高优（内容被截断，必须修）
  2. 广告法绝对化用语：最/第一/国家级/唯一/顶级/100%/绝对/史无前例/全国首家/独家 …
  3. 版权/来源提示：来源：/图源：/via @/版权所有 → 需人工确认素材权属
  4. 自定义词表：--words words.txt 追加扫描

用法：
  python tools/quality_gate.py 20260908
  python tools/quality_gate.py 20260908 --words my_risk_words.txt
  python tools/quality_gate.py --dir output/daily/20260908

退出码：发现任意 HIGH 风险 → 1；否则 0（可接入发布门禁）。
"""
import os
import sys
import re
import argparse

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PLATFORMS = ["douyin", "kuaishou", "bilibili", "xiaohongshu", "zhihu",
             "facebook", "youtube", "twitter"]

# 广告法常见绝对化/极限词（命中即高风险）
ABSOLUTE_TERMS = [
    "最", "第一", "国家级", "国家级", "唯一", "顶级", "极致", "绝无仅有",
    "史无前例", "全国首家", "独家", "100%", "绝对", "万能", "永久", "首选",
    "王牌", "销量第一", "全球首发", "领导品牌", "顶峰", "极品",
]
# 版权/来源提示（需人工确认权属，非阻断）
COPYRIGHT_HINTS = ["来源：", "图源：", "via @", "版权所有", "©", "未经授权", "授权转载"]


def scan_text(text, extra_words=None):
    """返回 findings: list of dict(sev, type, line, detail)"""
    findings = []
    extra = extra_words or []
    lines = text.splitlines()
    for i, line in enumerate(lines, 1):
        s = line.strip()
        # 1. 截断残留
        if s.endswith("…") or s.endswith("..."):
            findings.append({"sev": "HIGH", "type": "truncation",
                             "line": i, "detail": s[-20:]})
        # 2. 绝对化用语
        for term in ABSOLUTE_TERMS:
            if term in s:
                findings.append({"sev": "HIGH", "type": "absolute",
                                 "line": i, "detail": f"含绝对化词「{term}」"})
                break
        # 3. 版权/来源
        for hint in COPYRIGHT_HINTS:
            if hint in s:
                findings.append({"sev": "WARN", "type": "copyright",
                                 "line": i, "detail": f"出现来源/版权提示「{hint}」需确认权属"})
                break
        # 4. 自定义词
        for w in extra:
            if w and w in s:
                findings.append({"sev": "WARN", "type": "custom",
                                 "line": i, "detail": f"命中自定义词「{w}」"})
                break
    return findings


def scan_dir(date_dir, extra_words):
    report = {}
    for plat in PLATFORMS:
        p = os.path.join(date_dir, f"{plat}.md")
        if not os.path.exists(p):
            continue
        with open(p, encoding="utf-8") as f:
            text = f.read()
        fs = scan_text(text, extra_words)
        if fs:
            report[plat] = fs
    return report


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("date", nargs="?", help="制作日 YYYYMMDD")
    ap.add_argument("--dir", help="直接指定期目录")
    ap.add_argument("--kind", default="daily", choices=["daily", "weekly"])
    ap.add_argument("--words", help="自定义风险词表文件（每行一词）")
    args = ap.parse_args()

    if args.dir:
        date_dir = args.dir
    else:
        if not args.date:
            ap.error("需提供 date 或 --dir")
        date_dir = os.path.join(PROJECT_ROOT, "output", args.kind, args.date)
    if not os.path.isdir(date_dir):
        raise SystemExit(f"期目录不存在: {date_dir}")

    extra = []
    if args.words and os.path.exists(args.words):
        with open(args.words, encoding="utf-8") as f:
            extra = [w.strip() for w in f if w.strip()]

    report = scan_dir(date_dir, extra)

    high = sum(1 for fs in report.values() for f in fs if f["sev"] == "HIGH")
    warn = sum(1 for fs in report.values() for f in fs if f["sev"] == "WARN")

    print(f"═══ 合规质检 · {os.path.basename(date_dir)} ═══")
    if not report:
        print("  ✅ 未发现合规风险")
    for plat, fs in report.items():
        print(f"\n  [{plat}.md]")
        for f in fs:
            tag = "❌" if f["sev"] == "HIGH" else "⚠️"
            print(f"    {tag} L{f['line']} {f['type']}: {f['detail']}")

    print(f"\n═══ 结果：{'❌ %d 项高风险，禁止发布前修复' % high if high else '✅ 无高风险'} "
          f"（WARN {warn}）═══")
    sys.exit(1 if high else 0)


if __name__ == "__main__":
    main()
