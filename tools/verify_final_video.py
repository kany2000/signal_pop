# -*- coding: utf-8 -*-
"""成品视频出品自检（verify_final_video.py）

用法：
    python tools/verify_final_video.py weekly 20260828
    python tools/verify_final_video.py daily  20260823

用途（2026-08-30 用户要求：出品前必须先自检一遍）：
    交付/发布前对成片做完整性校验，用 ffprobe 数据把关，不靠肉眼：
      1) 视频帧数 vs 分镜期望帧数（weekly_segs.json / daily_segs.json）
         —— 拦截"分段渲染残段被拼入"导致的画面缺失（20260828 期末尾 28s 冻结）
      2) 视频/音频时长差 —— 拦截"画面提前结束、定格帧假播"（视频轨远短于音频轨）
      3) 文件存在性/大小/时长 sanity
    全部通过 exit 0 并打印 PASS；任何 FAIL exit 1。

依赖：仓库本地 ffprobe（bin/ffmpeg-9.0.1-essentials_build/bin/ffprobe.exe）。
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FFPROBE = ROOT / "bin" / "ffmpeg-9.0.1-essentials_build" / "bin" / "ffprobe.exe"
SEGS = {
    "weekly": ROOT / "remotion_poc" / "src" / "weekly_segs.json",
    "daily": ROOT / "remotion_poc" / "src" / "daily_segs.json",
}
FPS = 30
# 容差：帧数允许多出的合并冗余帧；音频可比视频长的拖尾秒数（正常结尾定格）
FRAME_TOLERANCE = 30        # 1s
AUDIO_TAIL_TOLERANCE = 3.0  # 秒


def ffprobe_json(path: Path) -> dict:
    out = subprocess.run(
        [str(FFPROBE), "-v", "error", "-print_format", "json",
         "-select_streams", "v:0", "-count_packets",
         "-show_entries", "stream=nb_read_packets,duration,r_frame_rate",
         "-show_entries", "format=duration,size", str(path)],
        capture_output=True, text=True)
    if out.returncode != 0:
        raise RuntimeError(f"ffprobe 失败: {out.stderr.strip()}")
    return json.loads(out.stdout)


def audio_duration(path: Path) -> float:
    out = subprocess.run(
        [str(FFPROBE), "-v", "error", "-select_streams", "a:0",
         "-show_entries", "stream=duration", "-of", "default=noprint_wrappers=1:nokey=1",
         str(path)], capture_output=True, text=True)
    try:
        return float(out.stdout.strip().splitlines()[0])
    except (ValueError, IndexError):
        return 0.0


def expected_frames(kind: str) -> int | None:
    segs_path = SEGS[kind]
    if not segs_path.exists():
        return None
    data = json.loads(segs_path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        total = sum(float(seg.get("dur", 0)) for seg in data)
        return round(total * FPS)
    return None


def main() -> int:
    if len(sys.argv) < 3 or sys.argv[1] not in SEGS:
        print(__doc__)
        return 2
    kind, date = sys.argv[1], sys.argv[2]
    video = ROOT / "output" / kind / date / f"signal_pop_{kind}_{date}.mp4"

    fails: list[str] = []
    warns: list[str] = []
    lines: list[str] = [f"=== 出品自检 {kind} {date} ==="]

    if not video.exists():
        print(f"FAIL 成片不存在: {video}")
        return 1

    info = ffprobe_json(video)
    vstream = info["streams"][0]
    v_packets = int(vstream["nb_read_packets"])
    v_dur = float(vstream.get("duration") or info["format"]["duration"])
    a_dur = audio_duration(video)
    size_mb = int(info["format"]["size"]) / 1024 / 1024

    lines.append(f"文件: {video.name}  {size_mb:.1f}MB  时长(容器) {float(info['format']['duration']):.1f}s")
    lines.append(f"视频轨: {v_packets} 帧 / {v_dur:.2f}s   音频轨: {a_dur:.2f}s")

    exp = expected_frames(kind)
    if exp is None:
        warns.append(f"找不到分镜数据 {SEGS[kind].name}，跳过帧数比对")
    else:
        lines.append(f"分镜期望: {exp} 帧 / {exp / FPS:.1f}s")
        if v_packets < exp - FRAME_TOLERANCE:
            fails.append(f"视频帧数缺口 {exp - v_packets} 帧（≈{(exp - v_packets) / FPS:.1f}s）："
                         f"结尾画面缺失，疑似残缺段被拼入")
        elif v_packets > exp + FRAME_TOLERANCE:
            warns.append(f"视频帧数多 {v_packets - exp} 帧（合并冗余，一般无害）")

    if a_dur > 0 and v_dur < a_dur - AUDIO_TAIL_TOLERANCE:
        fails.append(f"视频轨比音频轨短 {a_dur - v_dur:.1f}s：结尾会定格假播（卡死观感）")

    if size_mb < 1:
        fails.append(f"文件仅 {size_mb:.2f}MB，疑似损坏")

    for ln in lines:
        print(ln)
    for w in warns:
        print(f"WARN {w}")
    if fails:
        for f in fails:
            print(f"FAIL {f}")
        print("=== 自检未通过 ===")
        return 1
    print("PASS 全部检查通过，可交付用户审片")
    return 0


if __name__ == "__main__":
    sys.exit(main())
