#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""抖音单平台无封面直接发布重试 (20261002期)"""
import os, re, subprocess, sys

if sys.stdout.encoding and sys.stdout.encoding.lower().startswith("gbk"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DATE = "20261002"
OUT_DIR = f"E:/projects/signal_pop/output/weekly/{DATE}"
SAU = ["sau"]
ACCOUNT = "her2home"
SCHEDULE = "2026-10-03 08:00"

VIDEO = os.path.join(OUT_DIR, f"signal_pop_weekly_{DATE}.mp4")

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

print("🚀 [douyin] 开始重试上传（不带 --thumbnail，使用视频首帧）...")
dy = read_md("douyin.md")
cmd = SAU + ["douyin", "upload-video", "--account", ACCOUNT,
    "--file", VIDEO, "--title", extract(dy, "标题"), "--desc", extract(dy, "简介"),
    "--tags", extract_tags(dy), "--schedule", SCHEDULE, "--headed"]

r = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
print(f"exit={r.returncode}")
if r.stdout: print("stdout:/n" + r.stdout[-2000:])
if r.stderr: print("stderr:/n" + r.stderr[-1000:])
if r.returncode == 0:
    print("✅ 抖音无封面模式发布成功！")
else:
    print("❌ 抖音无封面模式失败")
