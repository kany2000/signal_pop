#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Signal Pop · 字级时间戳质检

检查对齐结果是否可用于渲染：单调性、段边界偏差、字时长分布、
插值比例、异常长时间戳。下期正式接入前可直接复用本脚本。
"""
import json
import os
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def main(path=None):
    path = path or os.path.join(HERE, "words.json")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    all_words = []
    print(f"file: {path}")
    for s in data["segments"]:
        ws = s["words"]
        all_words.extend(ws)
        starts = [w["start"] for w in ws]
        mono = all(starts[i] <= starts[i + 1] + 1e-6 for i in range(len(starts) - 1))
        tiny = sum(1 for w in ws if w["end"] - w["start"] < 0.03)
        long = sum(1 for w in ws if w["end"] - w["start"] > 1.0)
        print(
            "seg#%02d %.2f-%.2fs chars=%3d mono=%-5s first=%.3f (Δ%+.3f) "
            "last=%.3f (Δ%+.3f) tiny=%d long=%d"
            % (s["index"], s["start"], s["end"], len(ws), mono,
               ws[0]["start"], ws[0]["start"] - s["start"],
               ws[-1]["end"], ws[-1]["end"] - s["end"], tiny, long)
        )
    durs = [w["end"] - w["start"] for w in all_words if w["end"] > w["start"]]
    aligned = sum(1 for w in all_words if not w["interp"])
    interp = len(all_words) - aligned
    print("-" * 78)
    print("总字符 %d | 模型直接对齐 %d (%.1f%%) | 插值补齐 %d (%.1f%%)"
          % (len(all_words), aligned, aligned / len(all_words) * 100,
             interp, interp / len(all_words) * 100))
    print("字时长 median %.3fs / min %.3fs / max %.3fs"
          % (statistics.median(durs), min(durs), max(durs)))
    print("全局单调:", all(all_words[i]["start"] <= all_words[i + 1]["start"] + 1e-6
                       for i in range(len(all_words) - 1)))
    bad = [w for w in all_words if w["end"] - w["start"] > 1.5]
    if bad:
        print("异常长字 (>1.5s):", [(w["w"], round(w["end"] - w["start"], 2)) for w in bad[:12]])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else None))
