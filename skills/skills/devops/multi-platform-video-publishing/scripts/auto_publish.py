#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Signal Pop 自动分发脚本 (存放在 skill 的 scripts/ 目录)
- 监控 /home/kan/shared/her2home/ 新视频+封面+同名 .json 元数据
- 并行分发到抖音、B站、小红书、快手、YouTube
- 发布成功后记录日志，避免重复发布
"""

import json
import os
import subprocess
import sys
import time
from pathlib import Path

# 配置
HER2HOME = Path("/home/kan/shared/her2home")
STATE_FILE = HER2HOME / ".publish_state.json"
ACCOUNT = "her2home"
SAU = "/home/kan/shared/social-auto-upload/.venv/bin/sau"  # 或用 `sau` 如果已在 PATH

# 支持平台：YouTube 新增（需先登录：sau youtube login --account her2home）
PLATFORMS = [
    {
        "name": "bilibili",
        "cmd": ["upload-video", "--account", ACCOUNT, "--tid", "249"],
        "thumb_args": [],  # CLI 不支持封面
        "headless": False,
    },
    {
        "name": "xiaohongshu",
        "cmd": ["upload-video", "--account", ACCOUNT],
        "thumb_args": [],  # --thumbnail 有 Bug，暂不传封面
        "headless": True,
    },
    {
        "name": "kuaishou",
        "cmd": ["upload-video", "--account", ACCOUNT],
        "thumb_args": ["--thumbnail"],
        "headless": True,
    },
    {
        "name": "douyin",
        "cmd": ["upload-video", "--account", ACCOUNT],
        "thumb_args": ["--thumbnail-portrait"],
        "headless": True,
    },
    {
        "name": "youtube",
        "cmd": ["upload-video", "--account", ACCOUNT, "--visibility", "public"],
        "thumb_args": ["--thumbnail"],
        "headless": True,
    },
]


def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"published": [], "failed": []}


def save_state(state):
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2))


def run_sau(platform, video_path, meta, cover_path):
    cmd = [SAU, platform["name"]] + platform["cmd"]
    cmd += ["--file", str(video_path), "--title", meta["title"], "--desc", meta["desc"]]
    cmd += ["--tags", meta["tags"], "--schedule", meta["schedule"]]
    if platform["thumb_args"] and cover_path:
        cmd += platform["thumb_args"] + [str(cover_path)]
    if platform["headless"]:
        cmd += ["--headless"]

    print(f"[{platform['name']}] 上传: {video_path.name}")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if result.returncode == 0:
        print(f"[{platform['name']}] ✅ 成功")
        return True
    else:
        print(f"[{platform['name']}] ❌ 失败: {result.stderr[:200]}")
        return False


def main():
    state = load_state()
    published = set(state.get("published", []))
    failed = state.get("failed", [])

    video_files = sorted(HER2HOME.glob("*.mp4"))
    if not video_files:
        print("无新视频")
        return

    for video in video_files:
        if video.name in published:
            continue

        cover = video.with_suffix(".png")
        if not cover.exists():
            cover = video.with_suffix(".jpg")
        meta_file = video.with_suffix(".json")

        if not meta_file.exists():
            print(f"⚠️ 缺少元数据: {meta_file}")
            continue

        meta = json.loads(meta_file.read_text())

        # 顺序上传，避免浏览器并发冲突
        all_ok = True
        for platform in PLATFORMS:
            ok = run_sau(platform, video, meta, cover if cover.exists() else None)
            if not ok:
                all_ok = False
            time.sleep(8)  # 平台间隔，避免频率限制

        if all_ok:
            published.add(video.name)
            print(f"✅ {video.name} 全平台发布成功")
        else:
            failed.append({"video": video.name, "time": time.time()})
            print(f"❌ {video.name} 部分平台失败，下轮重试")

        save_state({"published": list(published), "failed": failed})

    print("完成")


if __name__ == "__main__":
    main()