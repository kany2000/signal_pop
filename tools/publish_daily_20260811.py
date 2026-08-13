#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Signal Pop 定时发布 20260811 → 8/12 08:00 (抖音 + 快手 + B站，sau CLI)
注意：sau 不支持知乎；小红书需单独登录。
"""
import os, re, subprocess, sys, json

if sys.stdout.encoding and sys.stdout.encoding.lower().startswith("gbk"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DATE = "20260811"
OUT_DIR = "E:/projects/signal_pop/output/daily_20260811"   # 文案与封面目录
VIDEO_DIR = "E:/projects/signal_pop/output/daily/20260811"  # 视频目录
SAU = ["sau"]
ACCOUNT = "her2home"
SCHEDULE = "2026-08-12 08:00"
BILI_TID = 249

VIDEO = os.path.join(VIDEO_DIR, f"signal_pop_daily_{DATE}.mp4")
COVER_34 = os.path.join(OUT_DIR, "cover_20260812_3x4.png")
COVER_169 = os.path.join(OUT_DIR, "cover_20260812_16x9.png")


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
    tags = lines[-1]
    return ",".join([t.strip("#") for t in tags.split()])


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

# --- B站 (标题 = 首行，B站限制80字符；desc 用 简介，若缺则用正文) ---
bili_md = read_md("bilibili.md")
bili_title = extract(bili_md, "标题") or bili_md.strip().splitlines()[0].strip()
if len(bili_title) > 78:
    bili_title = bili_title[:78].rstrip() + "…"
bili_desc = extract(bili_md, "简介")
if not bili_desc:
    m = re.search(r"正文[：:]\s*(.+?)(?:\n\n|\Z)", bili_md, re.S | re.M)
    bili_desc = m.group(1).strip() if m else bili_title

print(f"视频: {VIDEO}")
print(f"封面3:4: {COVER_34}")
print()
print(f"[抖音] title={dy_title[:40]}... desc_len={len(dy_desc)} tags={dy_tags}")
print(f"[快手] title={ks_title[:40]}... desc_len={len(ks_desc)} tags={ks_tags}")
print(f"[B站] title={bili_title[:40]}... desc_len={len(bili_desc)}")
print(f"\n⏰ 定时发布: {SCHEDULE}")


def run(label, cmd):
    print(f"\n{'='*60}\n🚀 [{label}] 开始上传...")
    print(f"  命令: {' '.join(cmd)}")
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
        print(f"  exit={r.returncode}")
        out = (r.stdout or "")[-2000:]
        err = (r.stderr or "")[-2000:]
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

# 3. B站 (tid 249, 无封面)
results["bilibili"] = run("bilibili", SAU + [
    "bilibili", "upload-video", "--account", ACCOUNT,
    "--file", VIDEO, "--title", bili_title, "--desc", bili_desc,
    "--tags", "信号弹,隔天信号弹,新闻早报,AI新闻,科技,财经", "--tid", str(BILI_TID),
    "--schedule", SCHEDULE,
])

print(f"\n{'='*60}")
for k, ok in results.items():
    print(f"  {'✅' if ok else '❌'} {k}")
print(f"\n定时发布时间: {SCHEDULE}")
print("📌 知乎：sau 不支持，需手动发布。")
