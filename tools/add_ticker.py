#!/usr/bin/env python3
"""
Signal Pop 分段字幕 — 生成 SRT 软字幕，不重编码视频

用法:
  python3 add_ticker.py input.mp4 [timeline.json] [--output output.mp4]
"""
import json, subprocess, sys
from pathlib import Path

def build_srt(timeline):
    """从 timeline 生成 SRT 字幕"""
    lines = []
    idx = 1
    current = 0.0
    for seg in timeline:
        dur = seg["duration"]
        title = seg.get("title", "信号弹播报")
        title_clean = title.rstrip("。")

        start_s = int(current)
        start_ms = int((current - start_s) * 1000)
        end = current + dur
        end_s = int(end)
        end_ms = int((end - end_s) * 1000)

        lines.append(f"{idx}")
        lines.append(f"{start_s:02d}:{start_ms//10:02d}:{start_s//3600:02d},{start_ms:03d} --> {end_s:02d}:{(end_ms//10):02d}:{end_s//3600:02d},{end_ms:03d}")
        # Hmm, SRT format: hh:mm:ss,mmm --> hh:mm:ss,mmm
        lines.append(f"{title_clean}")
        lines.append("")

        current += dur
        idx += 1
    return "\n".join(lines)

def build_srt_proper(timeline):
    lines = []
    idx = 1
    current = 0.0
    for seg in timeline:
        dur = seg["duration"]
        title = seg.get("title", "信号弹播报")
        title_clean = title.rstrip("。")

        start_h = int(current // 3600)
        start_m = int((current % 3600) // 60)
        start_s = int(current % 60)
        start_ms = int((current - int(current)) * 1000)

        end = current + dur
        end_h = int(end // 3600)
        end_m = int((end % 3600) // 60)
        end_s = int(end % 60)
        end_ms = int((end - int(end)) * 1000)

        lines.append(f"{idx}")
        lines.append(f"{start_h:02d}:{start_m:02d}:{start_s:02d},{start_ms:03d} --> {end_h:02d}:{end_m:02d}:{end_s:02d},{end_ms:03d}")
        lines.append(f"{title_clean}")
        lines.append("")

        current += dur
        idx += 1
    return "\n".join(lines)

def main():
    import argparse
    parser = argparse.ArgumentParser(description="分段字幕（软字幕，不重编码）")
    parser.add_argument("input", help="输入视频")
    parser.add_argument("timeline", nargs="?", default=None)
    parser.add_argument("--output", "-o", default=None)
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"[ERROR] 找不到: {input_path}"); sys.exit(1)

    # 找 timeline
    if args.timeline:
        tl_path = Path(args.timeline)
    else:
        candidates = sorted(Path("/home/kan/signal_pop/daily/data").glob("timeline_*.json"), reverse=True)
        if not candidates:
            print("[ERROR] 无 timeline.json"); sys.exit(1)
        tl_path = candidates[0]
    print(f"[时间线] {tl_path}")

    with open(tl_path) as f:
        timeline = json.load(f)

    # 生成 SRT
    srt_content = build_srt_proper(timeline)
    srt_path = input_path.parent / f"{input_path.stem}_ticker.srt"
    with open(srt_path, "w") as f:
        f.write(srt_content)
    print(f"[SRT] {srt_path} ({len(timeline)} 条)")

    # 嵌入软字幕 — 不重编码视频
    output = args.output or str(input_path.parent / f"{input_path.stem}_ticker_srt.mp4")
    subprocess.run([
        "ffmpeg", "-y",
        "-i", str(input_path),
        "-i", str(srt_path),
        "-c", "copy",
        "-c:s", "mov_text",
        "-metadata:s:s:0", "language=chi",
        str(output)
    ], check=True)

    # 清理 SRT (可选，保留方便调)
    total_dur = sum(s["duration"] for s in timeline)
    print(f"✅ {output} ({total_dur}s)")
    print(f"   软字幕，视频零重编码，画质无损")

if __name__ == "__main__":
    main()
