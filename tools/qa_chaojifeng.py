#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Signal Pop — 周末版 chaojifeng 质检总控（check_publish_ready 之前运行）

用法：python tools/qa_chaojifeng.py YYYYMMDD

三步：
  1. talk_segments.json → plan.json（chaojifeng-video-design 计划合同）
  2. validate_plan.py 结构校验（errors>0 即 FAIL）
  3. 成片已存在时 film_probe.py 实测：实际时长 vs 计划时长（容差 ±2s）、必须含音轨

依赖：G:/projects/chaojifeng-video-design（可用环境变量 CJF_VIDEO_SKILL 覆盖）；
      film_probe 需要 ffprobe（管线已具备）。本脚本只测结构与时长，
      画面、听感、事实仍由人工审稿与 check_publish_ready 把关。
"""
import json
import os
import subprocess
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL_ROOT = os.environ.get("CJF_VIDEO_SKILL") or os.path.join(
    os.path.dirname(PROJECT_ROOT), "chaojifeng-video-design")
DURATION_TOLERANCE_S = 2.0


def _with_ffmpeg_env():
    """信号弹自带 ffmpeg（bin/ffmpeg-*/bin），确保子进程能用 ffprobe"""
    env = os.environ.copy()
    bin_root = os.path.join(PROJECT_ROOT, "bin")
    if os.path.isdir(bin_root):
        for name in sorted(os.listdir(bin_root)):
            cand = os.path.join(bin_root, name, "bin")
            if os.path.isfile(os.path.join(cand, "ffprobe.exe")):
                env["PATH"] = cand + os.pathsep + env.get("PATH", "")
                break
    return env


def _ffprobe_exe():
    bin_root = os.path.join(PROJECT_ROOT, "bin")
    if os.path.isdir(bin_root):
        for name in sorted(os.listdir(bin_root)):
            cand = os.path.join(bin_root, name, "bin", "ffprobe.exe")
            if os.path.isfile(cand):
                return cand
    return "ffprobe"


def _probe_duration(path):
    r = subprocess.run([_ffprobe_exe(), "-v", "quiet", "-print_format", "json",
                        "-show_format", path], capture_output=True, text=True)
    try:
        return float(json.loads(r.stdout)["format"]["duration"])
    except (json.JSONDecodeError, KeyError, ValueError):
        return None


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                          env=_with_ffmpeg_env(), **kw)


def main():
    if len(sys.argv) < 2:
        print("用法: python tools/qa_chaojifeng.py YYYYMMDD")
        return 2
    date = sys.argv[1]
    out_dir = os.path.join(PROJECT_ROOT, "output", "weekly", date)
    if not os.path.isdir(out_dir):
        print(f"FAIL: 目录不存在 {out_dir}")
        return 2

    # 1. 生成 plan.json（分段：talk_segments.json；实测时长：audio/tts_segments.json）
    segs = os.path.join(out_dir, "talk_segments.json")
    if not os.path.exists(segs):
        segs = os.path.join(PROJECT_ROOT, "remotion_poc", "src", "weekly_segs.json")
        print(f"⚠ 未找到 talk_segments.json，回退 {segs}")
    audio_dir = os.path.join(out_dir, "audio")
    tts_segs = os.path.join(audio_dir, "tts_segments.json") if os.path.isdir(audio_dir) else None
    audio_arg = ["--audio-dir", audio_dir] if tts_segs else []
    if tts_segs:
        audio_arg += ["--dur-from", tts_segs]
    # 开场动画：成片 = opening_anim.mp4 + 正片，计划必须覆盖全片时长
    opening_file = os.path.join(out_dir, "opening_anim.mp4")
    if os.path.exists(opening_file):
        odur = _probe_duration(opening_file)
        if odur:
            audio_arg += ["--opening-dur", str(odur), "--opening-asset", opening_file]
            print(f"ℹ 开场动画实测 {odur:.3f}s，计入 wk-s00-opening")
    plan_path = os.path.join(out_dir, "plan.json")

    r = run([sys.executable, os.path.join(PROJECT_ROOT, "tools", "convert_weekly_plan.py"),
             "--segs", segs, "--out", plan_path] + audio_arg)
    print(r.stdout.strip())
    if r.returncode != 0:
        print(r.stderr.strip())
        print("❌ FAIL: plan 生成失败（缺素材或分段异常）")
        return 1
    plan = json.load(open(plan_path, encoding="utf-8"))

    # 2. 结构校验
    if not os.path.isdir(SKILL_ROOT):
        print(f"❌ FAIL: 找不到 skill 目录 {SKILL_ROOT}（设 CJF_VIDEO_SKILL 环境变量）")
        return 2
    r = run([sys.executable, os.path.join(SKILL_ROOT, "scripts", "validate_plan.py"), plan_path])
    report = {}
    try:
        report = json.loads(r.stdout)
    except json.JSONDecodeError:
        print(r.stdout[-800:], r.stderr[-400:])
        print("❌ FAIL: validate_plan 输出无法解析")
        return 1
    errs, warns = report.get("errors", []), report.get("warnings", [])
    print(f"📋 结构校验: errors={len(errs)} warnings={len(warns)}")
    for e in errs[:8]:
        print(f"   ✗ {e['code']}: {e['message']} @ {e['path']}")
    for w in warns[:3]:
        print(f"   ⚠ {w['code']}: {w['message']}")
    if errs:
        with open(os.path.join(out_dir, "plan_validate.json"), "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=1)
        print("❌ FAIL: 计划结构未过（详见 plan_validate.json），先修排程再继续")
        return 1

    # 3. 成片实测（可选：成片不存在时跳过，不视为失败）
    video = os.path.join(out_dir, f"signal_pop_weekly_{date}.mp4")
    if not os.path.exists(video):
        print(f"ℹ 成片尚未渲染（{os.path.basename(video)}），跳过实测；结构校验通过")
        return 0
    probe_path = os.path.join(out_dir, "plan_probe.json")
    r = run([sys.executable, os.path.join(SKILL_ROOT, "scripts", "film_probe.py"),
             video, "--out", probe_path, "--no-palette", "--no-audio"])
    if r.returncode != 0 or not os.path.exists(probe_path):
        print(r.stdout[-600:], r.stderr[-400:])
        print("❌ FAIL: film_probe 实测失败")
        return 1
    probe = json.load(open(probe_path, encoding="utf-8"))
    actual = float(probe.get("container", {}).get("duration_s") or 0)
    has_audio = bool(probe.get("audio", {}).get("codec"))
    vinfo = probe.get("video", {})
    cuts = len(probe.get("cuts", []))
    planned = float(plan["output"]["duration_seconds"])
    print(f"🎬 实测: {vinfo.get('width')}x{vinfo.get('height')}@{vinfo.get('fps')} | "
          f"时长 {actual:.2f}s（计划 {planned:.2f}s）| 音轨={'有' if has_audio else '无'} | 检出切换 {cuts} 处")

    ok = True
    if abs(actual - planned) > DURATION_TOLERANCE_S:
        print(f"❌ FAIL: 实际时长偏差 {abs(actual - planned):.2f}s 超容差 {DURATION_TOLERANCE_S}s（成片与排程不一致，"
              f"检查开场/片尾是否未计入计划，或旁白时长过期）")
        ok = False
    if not has_audio:
        print("❌ FAIL: 成片无音轨（计划 audio=required）")
        ok = False
    for key, want, got in (("宽", plan["output"]["width"], vinfo.get("width")),
                           ("高", plan["output"]["height"], vinfo.get("height")),
                           ("帧率", plan["output"]["fps"], vinfo.get("fps"))):
        if got and float(want) != float(got):
            print(f"⚠ 警告: {key}不一致 计划{want} vs 实际{got}")
    if ok:
        print(f"✅ chaojifeng 质检通过：plan.json / plan_probe.json 已存 {out_dir}")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
