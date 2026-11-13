#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""共享新闻片头配置（2026-11-13 用户定：以后每期统一使用）

用户重新制作了两份品牌开场动画，横版 / 竖版各一：

  output/weekly/shared/signal-news-intro-16x9-1080p.mp4  1920x1080 / 24fps / 10.000s
  output/weekly/shared/signal-news-intro-9x16-1080p.mp4  1080x1920 / 24fps / 10.000s

两者均自带 AAC 配乐（mean -19.7 / -18.9 dB），画面无日期、无期号，可每期复用。
用户 2026-11-13 拍板：片头音轨用动画自带的配乐，停用合成 opening_theme.wav；
两份素材经 .gitignore 例外放行后纳入版本控制。

🔴 片头时长不再硬编码：由 ffprobe 从共享文件实时读取，OPENING_DUR / OPEN_FRAMES
   全链路唯一真源。换片头只需替换文件（或用环境变量指向新文件），
   不要再把 9s / 270 帧之类的常量写回各脚本。

环境变量：
  SIGNAL_POP_INTRO_16X9   覆盖横版片头路径
  SIGNAL_POP_INTRO_9X16   覆盖竖版片头路径
  SIGNAL_POP_INTRO_GAIN   片头音轨增益（默认 1.5，抵消 amix 归一化的衰减）
"""
import os
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHARED = os.path.join(ROOT, "output", "weekly", "shared")
FFPROBE = os.path.join(ROOT, "bin", "ffmpeg-9.0.1-essentials_build", "bin", "ffprobe.exe")

INTRO_16X9 = os.environ.get(
    "SIGNAL_POP_INTRO_16X9",
    os.path.join(SHARED, "signal-news-intro-16x9-1080p.mp4"))
INTRO_9X16 = os.environ.get(
    "SIGNAL_POP_INTRO_9X16",
    os.path.join(SHARED, "signal-news-intro-9x16-1080p.mp4"))

# 共享片头缺失/探测失败时的兜底：等于用户素材的实测时长，避免时间轴归零。
FALLBACK_DUR = 10.0
INTRO_GAIN = float(os.environ.get("SIGNAL_POP_INTRO_GAIN", "1.5"))


def probe_duration(path):
    """ffprobe 读容器时长；文件缺失或探测失败时返回兜底值。"""
    if not path or not os.path.exists(path) or not os.path.exists(FFPROBE):
        return FALLBACK_DUR
    try:
        out = subprocess.check_output(
            [FFPROBE, "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", path],
            text=True, timeout=30, stderr=subprocess.DEVNULL)
        val = float(out.strip().splitlines()[0])
        return round(val, 3) if val > 0 else FALLBACK_DUR
    except Exception:
        return FALLBACK_DUR


def opening_duration():
    """横版共享片头时长（秒）—— 全链路唯一的片头时长真源。"""
    return probe_duration(INTRO_16X9)


def opening_frames(fps=30):
    """片头折算到目标帧率后的帧数（concat 滤镜会把 24fps 统一成 30fps）。"""
    return int(round(opening_duration() * fps))


def require_intro(path=None):
    """共享片头缺失时尽早报错，避免渲染到一半才发现。"""
    p = path or INTRO_16X9
    if not os.path.exists(p):
        raise SystemExit(f"共享新闻片头缺失: {p}")
    return p


if __name__ == "__main__":
    print(f"16x9   : {INTRO_16X9}")
    print(f"9x16   : {INTRO_9X16}")
    print(f"duration: {opening_duration():.3f}s   frames@30: {opening_frames()}   gain: {INTRO_GAIN}")
