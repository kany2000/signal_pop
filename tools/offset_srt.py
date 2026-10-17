#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""给 SRT 整体加时间偏移（用于对齐片头）

背景：成片结构是「片头 9s + 正文」，而 `gen_weekly_en_srt.py` / `gen_en_srt.py`
生成的时间轴是**从 0 开始**的正文相对时间（0 = 第一句台词）。
于是字幕会压在片头动画上 —— 与 TTS 音频同一个毛病。

用法：python tools/offset_srt.py <srt 文件> [偏移秒数] [输出路径]
      不给输出路径则原地修改（先写 .bak 备份）
"""
import os
import re
import sys

TC = re.compile(r"(\d{2}):(\d{2}):(\d{2}),(\d{3})")


def to_sec(h, m, s, ms):
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000.0


def to_tc(sec):
    if sec < 0:
        sec = 0.0
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = int(sec % 60)
    ms = int(round((sec - int(sec)) * 1000))
    if ms >= 1000:          # 四舍五入进位
        ms = 0
        s += 1
        if s >= 60:
            s = 0
            m += 1
        if m >= 60:
            m = 0
            h += 1
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def shift(path, offset, out_path=None):
    raw = open(path, encoding="utf-8-sig").read()
    if out_path is None:
        out_path = path
        if not os.path.exists(path + ".bak"):
            os.replace(path, path + ".bak")

    def repl(m):
        return to_tc(to_sec(*m.groups()) + offset)

    new = TC.sub(repl, raw)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(new)
    return raw, new


def main():
    if len(sys.argv) < 2:
        print("用法: python tools/offset_srt.py <srt 文件> [偏移秒数] [输出路径]")
        return 1
    path = sys.argv[1]
    offset = float(sys.argv[2]) if len(sys.argv) > 2 else 9.0
    out = sys.argv[3] if len(sys.argv) > 3 else None
    if not os.path.exists(path):
        print(f"❌ 找不到 {path}")
        return 1

    old, new = shift(path, offset, out)
    o_first = TC.search(old).group(0)
    n_first = TC.search(new).group(0)
    print(f"✅ 已整体偏移 {offset}s")
    print(f"   首条: {o_first} -> {n_first}")
    dst = out or path
    print(f"   输出: {dst}" + ("（原文件已备份为 .bak）" if out is None else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
