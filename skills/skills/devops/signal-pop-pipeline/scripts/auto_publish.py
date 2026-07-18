#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Signal Pop 自动分发脚本
- 监控 /home/kan/shared/her2home/ 新视频+封面
- 读取同名 .json 元数据（标题、简介、标签、定时时间）
- 并行分发到抖音、B站、小红书、快手
- 发布成功后记录日志，避免重复发布
"""

import json
import os
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# 配置
WATCH_DIR = Path("/home/kan/shared/her2home")
STATE_FILE = WATCH_DIR / ".publish_state.json"
ACCOUNT = "her2home"
# 已认证平台 (tencent 需先 login 获取 cookie)
# 去掉 xiaohongshu — 用户明确要求不发布
PLATFORMS = ["bilibili", "kuaishou", "douyin", "tencent"]

# B站无封面参数, 小红书/快手/抖音用 --thumbnail
THUMBNAIL_ARGS = {
    "bilibili": [],
    "xiaohongshu": ["--thumbnail"],
    "kuaishou": ["--thumbnail"],
    "douyin": ["--thumbnail"],
}

# B站分区 tid: 249 = 科技/数码
BILIBILI_TID = 249

def load_state():
    if STATE_FILE.exists():
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"published": {}}

def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

def find_new_videos(state):
    """扫描目录，返回未完全发布的视频文件列表"""
    published = state.get("published", {})
    new_videos = []
    for video_file in WATCH_DIR.glob("*.mp4"):
        video_state = published.get(video_file.name, {})
        platform_states = video_state.get("platforms", {})
        # 跳过所有平台都已成功的视频
        all_done = all(platform_states.get(p) is True for p in PLATFORMS)
        if all_done:
            continue
        # 检查是否有同名封面
        cover_file = video_file.with_suffix(".png")
        if not cover_file.exists():
            cover_file = video_file.with_suffix(".jpg")
        if not cover_file.exists():
            print(f"⚠️ 缺少封面: {video_file.name}")
            continue
        # 检查元数据文件
        meta_file = video_file.with_suffix(".json")
        meta = {}
        if meta_file.exists():
            with open(meta_file, "r", encoding="utf-8") as f:
                meta = json.load(f)
        new_videos.append({
            "video": video_file,
            "cover": cover_file,
            "meta": meta,
            "platform_states": platform_states,
        })
    return new_videos

def build_upload_cmd(platform, video_path, cover_path, meta):
    """构建 sau 上传命令"""
    title = meta.get("title", f"隔天信号弹 {datetime.now().strftime('%m.%d')}")
    desc = meta.get("desc", "每日硬核资讯，十条直达核心。")
    tags = meta.get("tags", "隔天信号弹,科技资讯,AI,新闻")
    if isinstance(tags, list):
        tags = ",".join(tags)
    schedule = meta.get("schedule")  # 格式: "2026-06-28 08:30"

    cmd = [
        "sau", platform, "upload-video",
        "--account", ACCOUNT,
        "--file", str(video_path),
        "--title", title,
        "--desc", desc,
        "--tags", tags,
    ]

    # 平台特定参数
    if platform == "bilibili":
        cmd.extend(["--tid", str(BILIBILI_TID)])
    if platform in THUMBNAIL_ARGS and THUMBNAIL_ARGS[platform]:
        cmd.extend(THUMBNAIL_ARGS[platform])
        cmd.append(str(cover_path))
    # kuaishou/xiaohongshu/douyin 需要 --headless 避免浏览器 UI 阻塞
    if platform in ("kuaishou", "xiaohongshu", "douyin"):
        cmd.extend(["--headless"])

    # 定时发布 (YouTube CLI 不支持 --schedule, 但此处无 YouTube)
    if schedule:
        cmd.extend(["--schedule", schedule])
    else:
        # 默认次日早 8:30
        tomorrow = datetime.now().replace(hour=8, minute=30, second=0, microsecond=0)
        if tomorrow <= datetime.now():
            tomorrow += timedelta(days=1)
        cmd.extend(["--schedule", tomorrow.strftime("%Y-%m-%d %H:%M")])

    return cmd

def upload_one(platform, video_path, cover_path, meta):
    """上传单个平台"""
    cmd = build_upload_cmd(platform, video_path, cover_path, meta)
    print(f"🚀 [{platform}] 上传: {video_path.name}")
    print(f"   命令: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        if result.returncode == 0:
            print(f"✅ [{platform}] 成功")
            return True, result.stdout
        else:
            print(f"❌ [{platform}] 失败: {result.stderr}")
            return False, result.stderr
    except subprocess.TimeoutExpired:
        print(f"⏱️ [{platform}] 超时")
        return False, "timeout"
    except Exception as e:
        print(f"💥 [{platform}] 异常: {e}")
        return False, str(e)

def publish_video(video_info):
    """顺序发布到所有平台（避免并行导致的浏览器冲突）
    每个平台成功立即记录，避免重复发布"""
    video_path = video_info["video"]
    cover_path = video_info["cover"]
    meta = video_info["meta"]
    platform_states = video_info.get("platform_states", {})

    print(f"\n{'='*60}")
    print(f"📤 处理视频: {video_path.name}")
    print(f"📋 元数据: {json.dumps(meta, ensure_ascii=False)}")
    print(f"{'='*60}")

    state = load_state()
    results = {}
    for p in PLATFORMS:
        # 跳过已成功的平台
        if platform_states.get(p) is True:
            print(f"⏭️ [{p}] 已发布过，跳过")
            results[p] = {"success": True, "output": "skipped"}
            continue

        print(f"🚀 [{p}] 开始上传...")
        success, output = upload_one(p, video_path, cover_path, meta)
        print(f"📥 [{p}] 结果: success={success}")
        results[p] = {"success": success, "output": output}

        # 每个平台成功后立即保存状态
        if success:
            state.setdefault("published", {}).setdefault(video_path.name, {})
            state["published"][video_path.name].setdefault("platforms", {})[p] = True
            state["published"][video_path.name]["time"] = datetime.now().isoformat()
            save_state(state)

    # 汇总
    success_count = sum(1 for r in results.values() if r["success"])
    total = len(PLATFORMS)
    if success_count == total:
        status = "✅ 全部成功"
    elif success_count > 0:
        status = f"⚠️ 部分成功 ({success_count}/{total})"
    else:
        status = "❌ 全部失败"
    print(f"\n📊 发布结果: {status}")
    for p, r in results.items():
        mark = "✅" if r["success"] else "❌"
        reason = " (已跳过)" if r.get("output") == "skipped" else ""
        print(f"   {mark} {p}{reason}")

    return video_path.name, success_count == total, results

def main():
    print(f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} 开始扫描...")

    state = load_state()
    new_videos = find_new_videos(state)

    if not new_videos:
        print("📭 无新视频待发布")
        return

    print(f"📥 发现 {len(new_videos)} 个新视频")

    for video_info in new_videos:
        video_name, all_ok, results = publish_video(video_info)
        if all_ok:
            state["published"][video_name] = {
                "time": datetime.now().isoformat(),
                "platforms": {p: r["success"] for p, r in results.items()},
            }
            save_state(state)
        else:
            print(f"⚠️ {video_name} 发布不完全，下次重试")

    print(f"\n🏁 完成")

if __name__ == "__main__":
    main()
