#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Signal Pop 周末特别版 · 英文外挂字幕生成（无中文字幕版）

规则 #7（2026-08-21）：周末版不生成中文字幕 SRT，只保留英文外挂
signal_pop_weekly_{DATE}.en_US.srt（海外平台文案提取 + 质检用）。

本工具不同于 daily 版 gen_en_srt.py（它读中文 srt 翻译），这里直接读
talk_segments.json 的口语文本，用音频 wav 实际时长推算时间轴，再用
MyMemory 免费 API 逐段翻译成英文，写出与视频对齐的 en_US.srt。

2026-09-12：接入 subtitle_layout 智能换行（移植自 short-video-factory 的
line-break 算法）——每条字幕最多 2 行、行首禁则标点、中英混排自适应，
替代原先「整段译文单行」的写法。新增 --rewrap 离线模式：对已生成的
SRT 直接重排换行，不重跑网络翻译。

用法：python tools/gen_weekly_en_srt.py [PREP_DATE]
      python tools/gen_weekly_en_srt.py [PREP_DATE] --rewrap   # 仅重排换行
依赖：Python 标准库 json（读 TTS 时长账本）+ urllib（MyMemory，无需 key）；
      换行度量优先 Pillow+jieba（缺失自动退化，不阻塞）
"""
import os
import re
import sys
import time
import json
import urllib.parse
import urllib.request

_TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
if _TOOLS_DIR not in sys.path:
    sys.path.insert(0, _TOOLS_DIR)

from subtitle_layout import wrap_srt_text  # noqa: E402

PROJECT_ROOT = "E:/projects/signal_pop"
PREP_DATE = sys.argv[1] if len(sys.argv) > 1 else "20260821"
OUT_DIR = os.path.join(PROJECT_ROOT, "output", "weekly", PREP_DATE)
SEG_JSON = os.path.join(OUT_DIR, "talk_segments.json")
# ⚠️ 时长必须读这个文件，不能自己去 audio/ 里探测分片 wav。
#    tts_segments.json 是 TTS 阶段落的**权威时长账本**（下游
#    gen_daily_en_srt / gen_weekly_publish_assets / export_*_remotion
#    都只认它），是唯一的单一数据源。
DUR_JSON = os.path.join(OUT_DIR, "audio", "tts_segments.json")
SRT_EN = os.path.join(OUT_DIR, f"signal_pop_weekly_{PREP_DATE}.en_US.srt")


def load_durations():
    """读 tts_segments.json 的真实时长，并硬校验段数。

    ⚠️ 本函数替换掉旧实现 `seg_duration(idx)`（2026-10-12 修正）。
    旧实现去audio/_sNNN.wav 探测时长、读不到就 `except: return 3.0`，
    而 gen_dual_tts.py:117 早就把分片挪进了 audio/_tmp/ 子目录 →
    路径失效 → 每段都掉进兜底 → **37 条字幕全部被压成 3.000s，
    全片字幕从 549.7s塌缩到 111.0s（覆盖率仅 20.2%）**，
    而且 `except Exception` 把「路径写错」这种编程错误伪装成
    「时长恰好 3 秒」的正常数据，无日志、无告警、一路过了质检。

    教训：静默兜底常量是把编程错误伪装成数据的经典手法。
    时长这种**有权威账本**的数据，只读账本，读不到就报错退出，
    绝不猜一个「看起来合理」的值。
    """
    if not os.path.exists(DUR_JSON):
        print(f"ERROR: 找不到时长账本 {DUR_JSON}")
        print("       请先跑完 TTS 阶段（tools/gen_dual_tts.py），再生成字幕。")
        sys.exit(1)
    with open(DUR_JSON, encoding="utf-8") as f:
        rows = json.load(f)
    durs = [float(r["dur"]) for r in rows]
    bad = [d for d in durs if d <= 0]
    if bad:
        print(f"ERROR: tts_segments.json 有 {len(bad)} 段时长非正（{bad[:5]}...）")
        sys.exit(1)
    return durs


def seg_duration(idx, durs=None):
    """兼容旧调用签名；durs 由 load_durations() 一次性载入。"""
    if durs is None:
        durs = load_durations()
    return durs[idx]


def translate(text):
    """MyMemory 免费翻译 zh-CN -> en（带重试）。"""
    for attempt in range(3):
        try:
            q = urllib.parse.quote(text[:450])
            url = f"https://api.mymemory.translated.net/get?q={q}&langpair=zh-CN|en"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=30) as r:
                d = json.loads(r.read().decode("utf-8"))
            if d.get("responseStatus") == 200:
                t = d["responseData"]["translatedText"].strip()
                if t and "MYMEMORY WARNING" not in t:
                    return t
            return text
        except Exception:
            time.sleep(2)
    return text


def fmt(sec):
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = int(sec % 60)
    ms = int((sec - int(sec)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


TIMING_RE = re.compile(r"\d{1,2}:\d{2}:\d{2}[,.]\d{3}\s*-->\s*\d{1,2}:\d{2}:\d{2}[,.]\d{3}")


def parse_srt_cues(raw):
    """解析 SRT 为 cue 列表 [{idx, timing, text:[原始行]}]。

    兼容两种写法：标准「空行分隔」与 gen_weekly_publish_assets 产出的
    「单换行紧凑」格式——统一按「序号行 + 时间轴行」扫描，不按空行 split。
    注意：cue 内「序号行」和「时间轴行」是同一个 cue 的两段，不能
    在时间轴处重复开新 cue（首版曾因此把 58 条解析成 116 条）。
    """
    lines = raw.strip().splitlines()
    TIM = TIMING_RE
    cues = []
    cur = None  # dict(idx, timing, text)
    n = len(lines)
    for i, line in enumerate(lines):
        s = line.strip()
        nxt = lines[i + 1].strip() if i + 1 < n else ""
        if cur is not None and not cur["timing"] and TIM.search(s):
            cur["timing"] = s  # 当前 cue 还没时间轴：此行就是它的时间轴
        elif TIM.search(s):
            if cur:
                cues.append(cur)
            cur = {"idx": "", "timing": s, "text": []}
        elif cur is None:
            if s:
                cur = {"idx": s, "timing": "", "text": []}
        elif s.isdigit() and TIM.search(nxt):
            cues.append(cur)  # 新 cue 起点：纯数字行且下一行是时间轴
            cur = {"idx": s, "timing": "", "text": []}
        else:
            cur["text"].append(line)
    if cur:
        cues.append(cur)
    return cues


def rewrap_srt():
    """离线重排：读已有 SRT，解开旧行再按智能换行重排（不重跑翻译）。"""
    if not os.path.exists(SRT_EN):
        print(f"ERROR: 找不到 {SRT_EN}")
        sys.exit(1)
    raw = open(SRT_EN, encoding="utf-8").read()
    cues = parse_srt_cues(raw)
    out_blocks = []
    changed = 0
    for i, cue in enumerate(cues):
        idx = cue["idx"] or str(i + 1)
        if not cue["timing"]:  # 异常 cue：原样回写
            out_blocks.append("\n".join([idx] + cue["text"]))
            continue
        text = " ".join(t.strip() for t in cue["text"] if t.strip())
        new_text = wrap_srt_text(text) if text else ""
        if new_text != text:
            changed += 1
        block = [idx, cue["timing"]] + ([new_text] if new_text else [])
        out_blocks.append("\n".join(block))
    with open(SRT_EN, "w", encoding="utf-8") as f:
        f.write("\n\n".join(out_blocks) + "\n")
    print(f"✅ 智能换行重排完成: {SRT_EN}（{changed}/{len(cues)} 条变更，已标准化为空行分隔）")


def main():
    if not os.path.exists(SEG_JSON):
        print(f"ERROR: 找不到 {SEG_JSON}")
        sys.exit(1)
    segs = json.load(open(SEG_JSON, encoding="utf-8"))
    durs = load_durations()

    # ⚠️ 段数必须一致：段数不符说明对话稿与 TTS 不同步，
    #    继续跑只会产出整体错位的字幕（无告警）。
    if len(durs) != len(segs):
        print(f"ERROR: 段数不匹配 —— 对话稿 {len(segs)} 段 vs TTS {len(durs)} 段")
        print("       请重跑 TTS（tools/gen_dual_tts.py），或检查对话稿是否被改动。")
        sys.exit(1)

    out = []
    t = 0.0
    for i, seg in enumerate(segs):
        text = seg.get("text", "").strip()
        dur = durs[i]
        start = t
        end = t + dur
        if text:
            en = translate(text)
            print(f"  [{i + 1}] {text[:28]}... -> {en[:46]}")
            out.append(f"{i + 1}\n{fmt(start)} --> {fmt(end)}\n{wrap_srt_text(en)}\n")
        else:
            out.append(f"{i + 1}\n{fmt(start)} --> {fmt(end)}\n\n")
        t = end
        time.sleep(0.6)  # 限速，避免 MyMemory 频率限制

    # ⚠️ 落盘前自检：字幕总跨度必须等于 TTS 总时长。
    #    这条断言专门拦「静默兜底」类 bug —— 只要跨度对不上就拒绝写文件，
    #    绝不让一个时间轴错误的SRT 落到 output/ 里再流到质检和平台。
    total = sum(durs)
    if t < total * 0.98:
        print(f"ERROR: 字幕总跨度 {t:.2f}s 与 TTS 总时长 {total:.2f}s 不符（偏差 {abs(t-total):.2f}s）")
        print("       拒绝写入，宁可无字幕也不能产出时间轴错误的字幕。")
        sys.exit(1)

    with open(SRT_EN, "w", encoding="utf-8") as f:
        f.write("\n".join(out))
    print(f"\n✅ 英文字幕已生成: {SRT_EN}（{len(segs)} 段，总长 {t:.1f}s / TTS {total:.1f}s ✅）")


def retime_srt():
    """离线重建时间轴：复用现有英文译文，只按TTS 时长账本重算时间轴。

    ⚠️ 2026-10-12 新增。起因：20261002 的字幕**只有时间轴坏了**（37 条全被
    压成 3.0s），但英文译文本身完全正确（37 段全英文化、段数与对话稿一致）。
    走main() 重生成要联网跑 37 次 MyMemory 翻译（限速 0.6s/次 + 退避重试），
    实测跑 15 分钟还没完——**为了修一个时间轴问题去重译全部文案，纯属浪费**。

    用法：python tools/gen_weekly_en_srt.py 20261002 --retime
    """
    if not os.path.exists(SRT_EN):
        print(f"ERROR: 找不到 {SRT_EN}")
        sys.exit(1)
    raw = open(SRT_EN, encoding="utf-8").read()
    cues = parse_srt_cues(raw)
    texts = [" ".join(t.strip() for t in c["text"] if t.strip()) for c in cues]
    durs = load_durations()

    if len(texts) != len(durs):
        print(f"ERROR: 现有 SRT {len(texts)} 段vs TTS {len(durs)} 段，无法按序对时")
        print("       段数变了说明对话稿改过，必须重跑完整生成（不加 --retime）。")
        sys.exit(1)

    zh = [i + 1 for i, t in enumerate(texts) if re.search(r"[\u4e00-\u9fff]", t)]
    if zh:
        print(f"ERROR: 现有 SRT 有 {len(zh)} 段仍是中文（段 {zh[:8]}），译文不完整")
        print("       请跑完整生成（不加 --retime）。")
        sys.exit(1)

    out, t = [], 0.0
    for i, (txt, dur) in enumerate(zip(texts, durs)):
        start, end = t, t + dur
        out.append(f"{i + 1}\n{fmt(start)} --> {fmt(end)}\n{wrap_srt_text(txt)}\n")
        t = end

    total = sum(durs)
    if t < total * 0.98:
        print(f"ERROR: 重建后跨度 {t:.2f}s 与 TTS {total:.2f}s 不符 → 拒绝写入")
        sys.exit(1)

    with open(SRT_EN, "w", encoding="utf-8") as f:
        f.write("\n".join(out))
    print(f"✅ 时间轴已重建: {SRT_EN}（{len(texts)} 段，总长 {t:.1f}s / TTS {total:.1f}s ✅）")


if __name__ == "__main__":
    if "--retime" in sys.argv:
        retime_srt()
    elif "--rewrap" in sys.argv:
        rewrap_srt()
    else:
        main()
