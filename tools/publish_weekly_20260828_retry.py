#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Retry only the 2 failed platforms for 20260828 weekend edition: douyin (headed) + bilibili.
快手 already succeeded & scheduled; do NOT re-run it (avoids duplicate scheduled upload).
"""
import os, re, subprocess, sys

if sys.stdout.encoding and sys.stdout.encoding.lower().startswith("gbk"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DATE = "20260828"
OUT_DIR = "E:/projects/signal_pop/output/weekly/20260828"
VIDEO_DIR = "E:/projects/signal_pop/output/weekly/20260828"
SAU = ["sau"]
ACCOUNT = "her2home"
SCHEDULE = "2026-08-29 08:00"
BILI_TID = 249

VIDEO = os.path.join(VIDEO_DIR, f"signal_pop_weekly_{DATE}.mp4")
COVER_34 = os.path.join(OUT_DIR, f"cover_weekly_{DATE}_3x4.png")


def read_md(fname):
    with open(os.path.join(OUT_DIR, fname), encoding="utf-8") as f:
        return f.read()


def extract(md_text, key):
    m = re.search(rf"^{key}[：:]\s*(.+?)(?:\n\n|\Z)", md_text, re.S | re.M)
    if not m:
        m = re.search(rf"^{key}[：:]\s*(.+)$", md_text, re.S | re.M)
    return m.group(1).strip() if m else ""


def extract_tags(md_text):
    lines = [l for l in md_text.splitlines() if l.startswith("#")]
    if not lines:
        return "隔天信号弹,周末特别版,新闻脱口秀"
    return ",".join([t.strip("#") for t in lines[-1].split()])


douyin_md = read_md("douyin.md")
dy_title = extract(douyin_md, "标题"); dy_desc = extract(douyin_md, "简介"); dy_tags = extract_tags(douyin_md)

bili_md = read_md("bilibili.md")
bili_title = extract(bili_md, "标题") or bili_md.strip().splitlines()[0].strip()
if len(bili_title) > 78:
    bili_title = bili_title[:78].rstrip() + "…"
bili_desc = extract(bili_md, "简介")
if not bili_desc:
    m = re.search(r"正文[：:]\s*(.+?)(?:\n\n|\Z)", bili_md, re.S | re.M)
    bili_desc = m.group(1).strip() if m else bili_title


def run(label, cmd):
    print(f"\n{'='*60}\n🚀 [{label}] 重试上传...")
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
        print(f"  exit={r.returncode}")
        out = (r.stdout or "")[-2000:]; err = (r.stderr or "")[-2000:]
        if out: print(f"  stdout: {out}")
        if err and r.returncode != 0: print(f"  stderr: {err}")
        return r.returncode == 0
    except Exception as e:
        print(f"  💥 异常: {e}")
        return False


results = {}
# douyin: 改用 --headed（本环境 kuaishou --headed 成功；headless 之前卡弹窗）
results["douyin"] = run("douyin", SAU + [
    "douyin", "upload-video", "--account", ACCOUNT,
    "--file", VIDEO, "--title", dy_title, "--desc", dy_desc, "--tags", dy_tags,
    "--thumbnail", COVER_34, "--schedule", SCHEDULE, "--headed",
])
# bilibili: 原样重试
results["bilibili"] = run("bilibili", SAU + [
    "bilibili", "upload-video", "--account", ACCOUNT,
    "--file", VIDEO, "--title", bili_title, "--desc", bili_desc,
    "--tags", "信号弹,隔天信号弹,周末特别版,新闻脱口秀,信蓝组合,科技,财经", "--tid", str(BILI_TID),
    "--schedule", SCHEDULE,
])

print(f"\n{'='*60}")
for k, ok in results.items():
    print(f"  {'✅' if ok else '❌'} {k}")
