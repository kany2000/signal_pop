#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Signal Pop — 周末版排程转换：weekly_segs.json → chaojifeng-video-design plan.json

把 Remotion 周末版分段数据转换为「超级峰视频设计方法论」的计划合同格式
（schema_version 1），供 validate_plan.py 结构校验，接入 QA 链。

用法：
  python tools/convert_weekly_plan.py --date 20261031
  python tools/convert_weekly_plan.py --date 20261031 --style dark-tech --strict-assets

规则：
  - 每个 seg → 一个 scene（稳定 ID：wk-s01…），按 dur 累计绝对秒，0 起点无空洞
  - TTS 实测 dur → narration timing=measured；未量时字段一律不写 measured
  - 背景图/视频 → assets（绝对路径，存在性实测，missing 会标出）
  - 计划只记录排程事实，不把结构通过当成画面/声音/理解验收通过
"""
import argparse
import json
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_SEGS = os.path.join(PROJECT_ROOT, "remotion_poc", "src", "weekly_segs.json")
PUBLIC_DIR = os.path.join(PROJECT_ROOT, "remotion_poc", "public")
FPS = 30
W, H = 1920, 1080
# Remotion WeeklyTalk 合成实测规格（Root.tsx：fps=30, 1920x1080）


def load_segs(path, dur_from=None):
    with open(path, encoding="utf-8") as f:
        segs = json.load(f)
    if not isinstance(segs, list) or not segs:
        raise SystemExit(f"ERROR: {path} 不是非空 JSON 数组")
    if dur_from:
        # 用 TTS 实测时长文件（tts_segments.json）按序号补齐 dur
        with open(dur_from, encoding="utf-8") as f:
            durs = json.load(f)
        if not isinstance(durs, list) or len(durs) != len(segs):
            raise SystemExit(f"ERROR: {dur_from} 段数({len(durs) if isinstance(durs, list) else '?'})"
                             f"与 {path} 段数({len(segs)})不一致，拒绝错位合并")
        for seg, d in zip(segs, durs):
            if not seg.get("dur") and d.get("dur"):
                seg["dur"] = d["dur"]
    return segs


def seg_purpose(seg, idx):
    if seg.get("isBreaking"):
        return "突发头条：完整交代事件、依据与反差细节"
    if seg.get("cta"):
        return "结尾互动：引导评论、关注与下周预告"
    if seg.get("isInteractive"):
        return "互动提问：抛出问题并等待观众回应"
    speaker = seg.get("speaker", "")
    if speaker == "阿信":
        return "主讲：交代新闻事实、数据与机制解释"
    if speaker == "小蓝":
        return "搭话：观众视角追问与共情，维持对话节奏"
    return f"段落{idx}"


def build_plan(segs, segs_path, style_id, audio_dir=None, opening=None):
    assets = {}
    asset_index = {}
    scenes = []
    cursor = 0.0
    total_round = 0.0
    audio_missing = []

    # 开场动画作为独立镜头（无旁白），时长以 ffprobe 实测为准传入
    if opening and opening.get("dur"):
        odur = round(float(opening["dur"]), 3)
        elements = []
        apath = opening.get("asset")
        if apath:
            aid = "asset-opening"
            assets[aid] = {
                "id": aid,
                "kind": "video",
                "path": os.path.abspath(apath),
                "source": "procedural",
                "rights": "pipeline-generated",
                "status": "ready" if os.path.exists(apath) else "missing",
            }
            elements.append({"id": "wk-s00-opening", "role": "footage",
                             "content": os.path.basename(apath), "asset_id": aid})
        scenes.append({
            "id": "wk-s00-opening",
            "purpose": "开场动画：品牌记忆点与情绪启动",
            "start": 0.0,
            "end": odur,
            "layout": "title-card",
            "elements": elements or [{"id": "wk-s00-opening", "role": "footage",
                                      "content": "opening animation"}],
            "narration": [],
            "hold_seconds": odur,
        })
        cursor = odur
        total_round = odur

    for i, seg in enumerate(segs, 1):
        dur = float(seg.get("dur") or 0.0)
        if dur <= 0:
            raise SystemExit(f"ERROR: 第{i}段 dur 无效（{dur!r}），无法排程")
        start = round(cursor, 3)
        end = round(cursor + dur, 3)
        sid = f"wk-s{i:02d}"

        # 素材登记（同一文件复用同一 asset id）
        elements = [{
            "id": f"{sid}-host",
            "role": "speaker",
            "content": f"{seg.get('speaker', '')}（{seg.get('voice', '')}）",
        }]
        for key, kind in (("bg", "image"), ("video", "video")):
            name = seg.get(key) or ""
            if not name:
                continue
            if name not in asset_index:
                p = os.path.join(PUBLIC_DIR, name)
                aid = f"asset-{len(asset_index) + 1:02d}-{kind}"
                assets[aid] = {
                    "id": aid,
                    "kind": kind,
                    "path": os.path.abspath(p),
                    "source": "project-local",
                    "rights": "pipeline-cleared",
                    "status": "ready" if os.path.exists(p) else "missing",
                }
                asset_index[name] = aid
            aid = asset_index[name]
            elements.append({
                "id": f"{sid}-{key}",
                "role": "background" if key == "bg" else "footage",
                "content": name,
                "asset_id": aid,
            })

        # 旁白音频：--audio-dir 提供逐段 TTS 文件时登记为 measured，
        # 否则按合同只能标 estimated（有音频后必须重新量时）
        narration = [{
            "id": f"{sid}-nar",
            "display": seg.get("text", ""),
            "spoken": seg.get("text", ""),
            "start": start,
            "duration_seconds": round(end - start, 3),
            "timing": "estimated",
        }]
        if audio_dir:
            for ext in (".mp3", ".wav", ".m4a"):
                # 兼容两种命名：wk-s01.mp3（本脚本约定）/ _s001.mp3（gen_dual_tts 约定）
                cands = [
                    os.path.join(audio_dir, f"{sid}{ext}"),
                    os.path.join(audio_dir, f"_s{i:03d}{ext}"),
                ]
                cand = next((c for c in cands if os.path.exists(c)), None)
                if cand:
                    aid = f"asset-nar-{i:02d}"
                    assets[aid] = {
                        "id": aid,
                        "kind": "audio",
                        "path": os.path.abspath(cand),
                        "source": "pipeline-tts",
                        "rights": "pipeline-generated",
                        "status": "ready",
                    }
                    narration[0]["timing"] = "measured"
                    narration[0]["asset_id"] = aid
                    break
            else:
                audio_missing.append(sid)

        scene = {
            "id": sid,
            "purpose": seg_purpose(seg, i),
            "start": start,
            "end": end,
            "layout": "breaking-news" if seg.get("isBreaking") else ("call-to-action" if seg.get("cta") else "brief-list"),
            "elements": elements,
            "narration": narration,
            "hold_seconds": 0.0,
        }
        scenes.append(scene)
        cursor = end
        total_round = round(cursor, 3)

    plan = {
        "schema_version": 1,
        "project_id": "signal-pop-weekly",
        "revision": 1,
        "goal": "观众看完能复述本周重点新闻各讲了什么、依据是什么，并明确哪些信息尚未确认。",
        "audience": "关注国内新闻的广州地区短视频观众（抖音/B站等竖横屏通吃）",
        "scenario_id": "news-brief",
        "mode": "recipe",
        "output": {
            "width": W,
            "height": H,
            "fps": FPS,
            "duration_seconds": total_round,
            "language": "zh-CN",
            "audio": "required",
        },
        "design": {
            "style_id": style_id,
            "rationale": "双主播对话资讯简报：暗色科技底色承载新闻条目，突发条目红系强调，CTA 收尾；视觉服从事实可读性。",
            "preserve": ["稳定对象ID", "双主播对话结构", "TTS 实测时长驱动排程"],
        },
        "runtime": {
            "adapter": "signal-pop-remotion",
            "status": "unresolved",
            "capabilities": ["color", "opacity", "position", "time-control", "media-composite"],
        },
        "assets": list(assets.values()),
        "scenes": scenes,
    }
    return plan


def main():
    ap = argparse.ArgumentParser(description="weekly_segs.json → plan.json（chaojifeng 计划合同）")
    ap.add_argument("--segs", default=DEFAULT_SEGS, help="weekly_segs.json 路径")
    ap.add_argument("--date", help="制作日 YYYYMMDD，决定输出目录 output/weekly/<date>/")
    ap.add_argument("--out", help="输出 plan.json 路径（优先于 --date）")
    ap.add_argument("--style", default="dark-tech", help="design.style_id（默认 dark-tech）")
    ap.add_argument("--audio-dir", help="逐段 TTS 音频目录（文件名 wk-s01.mp3/wav），提供后旁白标 measured")
    ap.add_argument("--dur-from", help="TTS 实测时长文件（tts_segments.json），按序号补齐缺失 dur")
    ap.add_argument("--opening-dur", type=float, help="开场动画实测时长（秒），写入 wk-s00-opening 场景")
    ap.add_argument("--opening-asset", help="开场动画文件路径")
    args = ap.parse_args()

    segs = load_segs(args.segs, dur_from=args.dur_from)
    opening = None
    if args.opening_dur:
        opening = {"dur": args.opening_dur, "asset": args.opening_asset}
    plan = build_plan(segs, args.segs, args.style, audio_dir=args.audio_dir, opening=opening)

    if args.out:
        out_path = args.out
    elif args.date:
        out_dir = os.path.join(PROJECT_ROOT, "output", "weekly", args.date)
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, "plan.json")
    else:
        out_path = os.path.join(os.path.dirname(os.path.abspath(args.segs)), "weekly_plan.json")

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(plan, f, ensure_ascii=False, indent=1)

    missing = [a["path"] for a in plan["assets"] if a["status"] == "missing"]
    print(f"OK plan → {out_path}")
    print(f"   scenes={len(plan['scenes'])} assets={len(plan['assets'])} "
          f"duration={plan['output']['duration_seconds']}s style={args.style}")
    if missing:
        print(f"   ⚠ missing assets: {len(missing)}")
        for m in missing[:5]:
            print(f"     - {m}")
        sys.exit(1)
    audio_missing = [s["id"] for s in plan["scenes"]
                     if s["narration"] and s["narration"][0].get("timing") == "estimated"]
    if audio_missing:
        print(f"   ℹ {len(audio_missing)} 段无 TTS 音频文件，旁白按 estimated 记录；"
              f"周五 TTS 生成后用 --audio-dir 重新转换")


if __name__ == "__main__":
    main()
