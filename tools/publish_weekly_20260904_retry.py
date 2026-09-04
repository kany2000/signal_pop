#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Signal Pop 周末版定时发布 20260904 重试脚本：仅抖音+B站（快手已成功，勿重复预约）"""
import os, re, subprocess, sys

if sys.stdout.encoding and sys.stdout.encoding.lower().startswith("gbk"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DATE = "20260904"
OUT_DIR = f"E:/projects/signal_pop/output/weekly/{DATE}"
SAU = ["sau"]
ACCOUNT = "her2home"
SCHEDULE = "2026-09-05 08:00"   # 播报日（周六）08:00
BILI_TID = 249                  # B站科技分区

VIDEO = os.path.join(OUT_DIR, f"signal_pop_weekly_{DATE}.mp4")
COVER_34 = os.path.join(OUT_DIR, f"cover_weekly_{DATE}_3x4.png")

def read_md(fname):
    return open(os.path.join(OUT_DIR, fname), encoding="utf-8").read()

def extract(md_text, key):
    m = re.search(rf"^{key}[：:]\s*(.+?)(?:\n\n|\Z)", md_text, re.S | re.M)
    if not m:
        m = re.search(rf"^{key}[：:]\s*(.+)$", md_text, re.S | re.M)
    return m.group(1).strip() if m else ""

def extract_tags(md_text):
    lines = [l for l in md_text.splitlines() if l.startswith("#")]
    return ",".join([t.strip("#") for t in lines[-1].split()]) if lines else "隔天信号弹,周末特别版,新闻脱口秀"

def run(label, cmd):
    print(f"\n🚀 [{label}] 开始上传...")
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
        print(f"  exit={r.returncode}")
        if r.stdout: print(f"  stdout: {(r.stdout or '')[-1500:]}")
        if r.stderr and r.returncode != 0: print(f"  stderr: {(r.stderr or '')[-1500:]}")
        return r.returncode == 0
    except Exception as e:
        print(f"  💥 异常: {e}")
        return False

results = {}
# 抖音：必须 --headed
dy = read_md("douyin.md")
results["douyin"] = run("douyin", SAU + ["douyin", "upload-video", "--account", ACCOUNT,
    "--file", VIDEO, "--title", extract(dy, "标题"), "--desc", extract(dy, "简介"),
    "--tags", extract_tags(dy), "--thumbnail", COVER_34, "--schedule", SCHEDULE, "--headed"])
# B站
bili = read_md("bilibili.md")
bt = extract(bili, "标题") or bili.strip().splitlines()[0].strip()
bt = (bt[:78].rstrip() + "…") if len(bt) > 78 else bt
results["bilibili"] = run("bilibili", SAU + ["bilibili", "upload-video", "--account", ACCOUNT,
    "--file", VIDEO, "--title", bt, "--desc", extract(bili, "简介") or bt,
    "--tags", "信号弹,隔天信号弹,周末特别版,新闻脱口秀,信蓝组合,科技,财经",
    "--tid", str(BILI_TID), "--schedule", SCHEDULE])

print("\n" + "=" * 60)
for k, ok in results.items():
    print(f"  {'✅' if ok else '❌'} {k}")
print(f"\n定时发布时间: {SCHEDULE}")
