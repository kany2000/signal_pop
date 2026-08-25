#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Signal Pop 定时发布：抖音 + 快手 + B站 (sau CLI)
制作日 20260823 / 发布日 2026-08-24 周一 08:00 定时发布。其余平台手动。
"""
import os, re, subprocess, sys

if sys.stdout.encoding and sys.stdout.encoding.lower().startswith("gbk"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DATE = "20260823"
OUT_DIR = f"E:/projects/signal_pop/output/daily/{DATE}"
SAU = ["sau"]
ACCOUNT = "her2home"
SCHEDULE = "2026-08-24 08:00"
BILI_TID = 249

VIDEO = os.path.join(OUT_DIR, f"signal_pop_daily_{DATE}.mp4")
COVER_34 = os.path.join(OUT_DIR, "cover_20260824_3x4.png")

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
        return "隔天信号弹,AI,科技资讯"
    return ",".join([t.strip("#") for t in lines[-1].split()])

# --- 抖音 ---
douyin_md = read_md("douyin.md")
dy_title = extract(douyin_md, "标题")
dy_desc = extract(douyin_md, "简介")
dy_tags = extract_tags(douyin_md)

# --- 快手 ---
kuaishou_md = read_md("kuaishou.md")
ks_title = extract(kuaishou_md, "标题")
ks_desc = extract(kuaishou_md, "简介")
ks_tags = extract_tags(kuaishou_md)

# --- B站 ---
bili_md = read_md("bilibili.md")
bili_title = extract(bili_md, "标题")
bili_desc = extract(bili_md, "简介")

print(f"视频: {VIDEO}")
print(f"封面3:4: {COVER_34}")
print()
print(f"[抖音] title={dy_title[:40]}... desc_len={len(dy_desc)} tags={dy_tags}")
print(f"[快手] title={ks_title[:40]}... desc_len={len(ks_desc)} tags={ks_tags}")
print(f"[B站] title={bili_title[:40]}... desc_len={len(bili_desc)}")

def run(label, cmd):
    print(f"\n{'='*60}\n🚀 [{label}] 开始上传...")
    print(f"  命令: {' '.join(cmd[:8])} ...")
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
        print(f"  exit={r.returncode}")
        out = (r.stdout or "")[-1500:]
        err = (r.stderr or "")[-1500:]
        if out: print(f"  stdout: {out}")
        if err and r.returncode != 0: print(f"  stderr: {err}")
        return r.returncode == 0
    except Exception as e:
        print(f"  💥 异常: {e}")
        return False

results = {}

# 1. 抖音 (headless + thumbnail 3:4)
results["douyin"] = run("douyin", SAU + [
    "douyin", "upload-video", "--account", ACCOUNT,
    "--file", VIDEO, "--title", dy_title, "--desc", dy_desc, "--tags", dy_tags,
    "--thumbnail", COVER_34, "--schedule", SCHEDULE, "--headless",
])

# 2. 快手 (headed + thumbnail 3:4)
results["kuaishou"] = run("kuaishou", SAU + [
    "kuaishou", "upload-video", "--account", ACCOUNT,
    "--file", VIDEO, "--title", ks_title, "--desc", ks_desc, "--tags", ks_tags,
    "--thumbnail", COVER_34, "--schedule", SCHEDULE, "--headed",
])

# 3. B站 (tid 249, no thumbnail)
results["bilibili"] = run("bilibili", "upload-video", "--account", ACCOUNT,
    "--file", VIDEO, "--title", bili_title, "--desc", bili_desc,
    "--tags", "信号弹,隔天信号弹,新闻早报,AI新闻,科技,财经", "--tid", str(BILI_TID),
    "--schedule", SCHEDULE,
) if False else run("bilibili", SAU + [
    "bilibili", "upload-video", "--account", ACCOUNT,
    "--file", VIDEO, "--title", bili_title, "--desc", bili_desc,
    "--tags", "信号弹,隔天信号弹,新闻早报,AI新闻,科技,财经", "--tid", str(BILI_TID),
    "--schedule", SCHEDULE,
])

print(f"\n{'='*60}")
for k, ok in results.items():
    print(f"  {'✅' if ok else '❌'} {k}")
print(f"\n定时发布时间: {SCHEDULE}")
