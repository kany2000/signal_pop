#!/usr/bin/env python3
"""Signal Pop — Remotion 周末版数据导出（含配图轮换）

合并 talk_segments.json + audio/tts_segments.json，
并从 archive 脚本文本解析每段背景图（【第N名】→ rankNN.jpg），
输出 remotion_poc/src/weekly_segs.json（Remotion 消费格式）。

用法: python tools/export_weekly_remotion.py [制作日YYYYMMDD]
"""
import sys, os, json, shutil

PROJECT_ROOT = "E:/projects/signal_pop"

# 段文本 → 背景图 映射（与旧管线 rebuild_weekly_talk.parse_talk_with_bg 一致）
BG_MAP = {"开场": "opening_bg.jpg", "本周之最": "00.jpg", "下周看点": "99.jpg", "结尾": "ending_bg.jpg"}


def parse_bg_rank(text):
    """从 archive 脚本文本解析: 段文本列表 -> [(文本, bg), ...]"""
    segs_bg = []
    cur_group = "开场"
    for line in text.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        if line.startswith("【"):
            tag = line.strip("【】")
            if tag.startswith("第") and "名" in tag:
                try:
                    rank = int(tag.replace("第", "").replace("名", ""))
                    cur_group = f"rank{rank}"
                    BG_MAP[f"rank{rank}"] = f"{rank:02d}.jpg"
                except Exception:
                    cur_group = tag
            else:
                cur_group = tag
            continue
        for name in ("阿信", "小蓝"):
            if line.startswith(f"{name}：") or line.startswith(f"{name}:"):
                content = line.split("：", 1)[1] if "：" in line else line.split(":", 1)[1]
                segs_bg.append((content.strip(), BG_MAP.get(cur_group, "opening_bg.jpg")))
                break
    return segs_bg


def main(date):
    out_dir = os.path.join(PROJECT_ROOT, "output", "weekly", date)
    talk_path = os.path.join(out_dir, "talk_segments.json")
    dur_path = os.path.join(out_dir, "audio", "tts_segments.json")
    if not (os.path.exists(talk_path) and os.path.exists(dur_path)):
        print(f"❌ 数据不存在: {talk_path} / {dur_path}"); sys.exit(1)

    talk = json.load(open(talk_path, encoding="utf-8"))
    durs = json.load(open(dur_path, encoding="utf-8"))
    if len(talk) != len(durs):
        print(f"❌ 段数不匹配: talk={len(talk)} durs={len(durs)}"); sys.exit(1)

    # 从 archive 解析配图
    archive = os.path.join(PROJECT_ROOT, "archive", f"signal_pop_weekly_special_{date}.txt")
    segs_bg = []
    if os.path.exists(archive):
        segs_bg = parse_bg_rank(open(archive, encoding="utf-8").read())
        if len(segs_bg) != len(talk):
            print(f"⚠️ 配图段数({len(segs_bg)}) != 对话段数({len(talk)})，用占位图补齐")
    else:
        print(f"⚠️ archive 不存在: {archive}，全部用 opening_bg.jpg")

    segs = []
    for i, (t, d) in enumerate(zip(talk, durs)):
        bg = segs_bg[i][1] if i < len(segs_bg) else "opening_bg.jpg"
        segs.append({"speaker": t["speaker"], "voice": t["voice"], "text": t["text"],
                     "dur": d["dur"], "bg": bg})
    dst = os.path.join(PROJECT_ROOT, "remotion_poc", "src", "weekly_segs.json")
    with open(dst, "w", encoding="utf-8") as f:
        json.dump(segs, f, ensure_ascii=False, indent=1)
    total = sum(s["dur"] for s in segs)
    uniq_bg = sorted(set(s["bg"] for s in segs))
    print(f"✅ 导出 {len(segs)} 段 / {total:.1f}s -> {dst}")
    print(f"   配图 {len(uniq_bg)} 种: {uniq_bg}")

    # 复制素材
    pub = os.path.join(PROJECT_ROOT, "remotion_poc", "public")
    os.makedirs(pub, exist_ok=True)
    imgs = os.path.join(out_dir, "images")
    srcs = [os.path.join(imgs, "anchor_axin.jpg"), os.path.join(imgs, "anchor_xiaolan.jpg")]
    srcs += [os.path.join(imgs, b) for b in uniq_bg]
    for s in srcs:
        if os.path.exists(s):
            shutil.copy(s, os.path.join(pub, os.path.basename(s)))
    print(f"✅ 素材已复制: {[os.path.basename(s) for s in srcs if os.path.exists(s)]}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "20260821")
