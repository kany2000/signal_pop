#!/usr/bin/env python3
"""从播报脚本 + visual_prompts 自动生成时间线 JSON"""
import json, re, sys
from pathlib import Path

def main():
    script_path = sys.argv[1] if len(sys.argv) > 1 else "/home/kan/signal_pop/daily/data/script_20260620.txt"
    prompts_path = sys.argv[2] if len(sys.argv) > 2 else "/home/kan/signal_pop/daily/data/visual_prompts_20260620.json"

    with open(script_path) as f:
        content = f.read()
    with open(prompts_path) as f:
        prompts = json.load(f)

    # 按编号分段
    segments = re.split(r'\n(?=\d+\.)', content.strip())
    timeline = []

    # intro
    intro = segments[0] if segments else ""
    intro_chars = len(intro.replace('\n',''))
    timeline.append({
        "id": "anchor_bg",
        "title": "开场",
        "duration": max(8, intro_chars // 5)
    })

    for i, seg in enumerate(segments[1:] if segments else []):
        m = re.match(r'(\d+)\.\s*(.*?)(?:。|$)', seg)
        idx = int(m.group(1)) if m else i+1
        title = m.group(2)[:80] if m else f"新闻{idx}"

        chars = len(seg.replace('\n',''))
        dur = max(12, chars // 5)

        timeline.append({
            "index": idx,
            "title": title,
            "duration": dur
        })

    # 收尾
    timeline.append({"id": "outro", "title": "收播", "duration": 5})

    total = sum(s["duration"] for s in timeline)
    print(f"时间线: {len(timeline)} 段, 预估总长 {total}s")

    out = Path(script_path).parent / f"timeline_{Path(script_path).stem.split('_')[1]}.json"
    with open(out, "w") as f:
        json.dump(timeline, f, ensure_ascii=False, indent=2)
    print(f"写入: {out}")

if __name__ == "__main__":
    main()
