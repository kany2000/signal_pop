#!/usr/bin/env python3
"""
从 script.txt 生成 SRT 字幕 — 固定语速 4.5 字/秒
按 agent 描述的 generate_srt_from_segments 实现
"""
import re, sys, os

CHARS_PER_SEC = 4.5


def fmt_srt_time(seconds):
    """SRT 时间格式: HH:MM:SS,mmm"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

def gen_srt(text_path, srt_path):
    with open(text_path, "r", encoding="utf-8") as f:
        lines = [l.strip() for l in f if l.strip()]

    segments = []

    # 找第一条新闻
    news_start = None
    for i, line in enumerate(lines):
        if re.match(r'^\d+[.、]', line) or re.match(r'^第\d+条', line):
            news_start = i
            break

    if news_start is None:
        print("Error: no news items found")
        return

    # Intro
    if news_start > 0:
        segments.append(("intro", " ".join(lines[:news_start])))

    # News items: 累加多行内容
    i = news_start
    while i < len(lines):
        line = lines[i]
        m = re.match(r'^(\d+)[.、]\s*(.*)', line)
        m2 = re.match(r'^第(\d+)条[，,、]\s*(.*)', line)
        if m or m2:
            num = int(m.group(1)) if m else int(m2.group(1))
            text = m.group(2) if m else m2.group(2)
            i += 1
            while i < len(lines):
                nxt = lines[i]
                if re.match(r'^\d+[.、]', nxt) or re.match(r'^第\d+条', nxt):
                    break
                text += " " + nxt
                i += 1
            segments.append((f"news_{num}", text))
        else:
            i += 1

    # Outro: 最后一条新闻之后的行
    last_news = None
    for i, line in enumerate(lines):
        if re.match(r'^\d+[.、]', line) or re.match(r'^第\d+条', line):
            last_news = i
    if last_news is not None and last_news < len(lines) - 1:
        segments.append(("outro", " ".join(lines[last_news+1:])))

    # 写 SRT
    current_time = 0.0
    seq = 1
    with open(srt_path, "w", encoding="utf-8") as f:
        for seg_id, seg_text in segments:
            duration = len(seg_text) / CHARS_PER_SEC
            start = current_time
            end = current_time + duration
            current_time = end

            f.write(f"{seq}\n")
            f.write(f"{fmt_srt_time(start)} --> {fmt_srt_time(end)}\n")
            f.write(f"{seg_text}\n\n")
            seq += 1

            print(f"  [{seg_id:>8}] {start:7.1f}-{end:7.1f}s ({duration:.1f}s, {len(seg_text)} chars)")

    print(f"\nSRT written: {srt_path}")
    print(f"Total duration: {current_time:.1f}s")

def main():
    if len(sys.argv) < 2:
        date = os.path.basename(sorted(glob("E:/projects/signal_pop/daily/data/script_*.txt"))[-1]).split("_")[1].split(".")[0] if False else "20260705"
    else:
        date = sys.argv[1]

    base = "E:/projects/signal_pop/daily"
    text_path = f"{base}/data/script_{date}.txt"
    srt_path = f"{base}/output/signal_pop_daily_{date}.srt"

    if not os.path.exists(text_path):
        # 试试没日期的
        text_path = f"{base}/data/script.txt"
    if not os.path.exists(text_path):
        print(f"Error: not found {text_path}")
        sys.exit(1)

    print(f"Reading: {text_path}")
    print(f"Output:  {srt_path}\n")
    gen_srt(text_path, srt_path)

if __name__ == "__main__":
    import glob
    main()