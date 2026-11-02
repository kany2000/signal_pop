#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""「大家一起聊经济」huashu-art-motion 动画管线 —— 通用版（配置驱动）

与旧的写死版 `build_econ_huashu.py` 的区别：
  旧版：分镜按「固定 11 段」逐段写死在 Python 里，稿子段数一变就要重写整个脚本
  本版：分镜抽到外置 JSON 配置，脚本是通用引擎 —— 改稿只改配置，不改代码

用法：
    python tools/build_econ_huashu_generic.py {制作日} [--specs-only]
    python tools/build_econ_huashu_generic.py {制作日} --config {自定义配置.json}

配置文件查找顺序（制作日目录下）：
    1. output/weekly/{制作日}/econ_huashu_storyboard.json      ← 本期专用
    2. tools/econ_huashu_storyboard.template.json               ← 通用模板（11 段 / 19 镜）

配置格式：
    {
      "version": 1,
      "segments": {
        "0": {                              ← TTS 第 0 段（0 起）
          "ratios": [0.52],                ← 该段拆成几镜 + 每镜占比（末镜自动补齐）
          "shots": [
            {"part": 0, "id": "shot_01", "grammar": "y5_kinetic_type", "cues": [...]},
            ...
          ]
        },
        ...
      }
    }

产出：
    output/weekly/{制作日}/econ_huashu/specs/shot_XX.json    分镜 spec
    output/weekly/{制作日}/econ_huashu/clips/shot_XX.mp4     渲染片段
    output/weekly/{制作日}/econ_huashu/econ_huashu_bg.mp4    拼接底片（静音）
"""
import os
import sys
import json
import subprocess

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# huashu 引擎在项目同级目录 G:/projects/_dl/huashu/...，向上回溯一级定位 _dl
_PROJECTS_DIR = os.path.dirname(PROJECT_ROOT)
HUASHU_ENGINE = os.path.join(_PROJECTS_DIR, "_dl", "huashu", "huashu-art-motion-main", "scripts", "engine")
FFMPEG_BIN = os.path.join(PROJECT_ROOT, "bin", "ffmpeg-9.0.1-essentials_build", "bin")
FFMPEG = os.path.join(FFMPEG_BIN, "ffmpeg.exe")

TEMPLATE_CONFIG = os.path.join(PROJECT_ROOT, "tools", "econ_huashu_storyboard.template.json")

FPS = 30
SAFE = {"top": 76, "bottom": 128, "left": 148, "right": 148}
THEME = "ink"

# y5_kinetic_type 排版三铁律（引擎只告警不报错，必须生成期自检）
Y5_MAX_WORD = 4      # 主词汉字数上限
Y5_MAX_LABEL = 3     # 左上角标签字数上限


def load_config(prep_date, custom=None):
    """查找并加载分镜配置。"""
    if custom:
        path = custom
    else:
        period_cfg = os.path.join(PROJECT_ROOT, "output", "weekly", prep_date, "econ_huashu_storyboard.json")
        path = period_cfg if os.path.exists(period_cfg) else TEMPLATE_CONFIG
    with open(path, encoding="utf-8") as f:
        cfg = json.load(f)
    print(f"[config] {path}")
    return cfg, path


def lint_y5(shots):
    """y5_kinetic_type 排版自检（引擎静默失效，必须自己查）。

    ① 主词 ≤4 汉字（字号固定 300px，5 字以上占满 86% 画宽撞左上角标签）
    ② data.label ≤3 字（标签固定画在 x=140，是主词的水平避让位）
    ③ highlight.data.word 必须在「当前页主词」里（荧光笔只刷主词，辅句词要用 data.key 着色）
    """
    errors = []
    for sh in shots:
        if sh["grammar"] != "y5_kinetic_type":
            continue
        pages = sorted(
            [c for c in sh["cues"] if c.get("kind") in ("point", "title", "number")],
            key=lambda c: c["at"],
        )
        for c in sh["cues"]:
            if c.get("kind") in ("point", "title"):
                txt = c.get("text", "")
                label = (c.get("data") or {}).get("label", "")
                if len(txt) > Y5_MAX_WORD:
                    errors.append(f"{sh['id']}: 主词过长({len(txt)}字)「{txt}」")
                if len(label) > Y5_MAX_LABEL:
                    errors.append(f"{sh['id']}: label过长({len(label)}字)「{label}」")
            if c.get("kind") == "highlight":
                word = (c.get("data") or {}).get("word")
                if not word:
                    continue
                cur = [q for q in pages if q["at"] <= c["at"] + 1e-6]
                cur_text = cur[-1].get("text", "") if cur else ""
                if word not in cur_text:
                    errors.append(f"{sh['id']}: highlight词「{word}」不在当前页主词「{cur_text}」")
    return errors


def build_specs(prep_date, cfg):
    """按配置 + 真实 TTS 帧数生成各镜头 spec。"""
    out_dir = os.path.join(PROJECT_ROOT, "output", "weekly", prep_date)
    audio_json = os.path.join(out_dir, "econ_audio", "tts_segments.json")
    specs_dir = os.path.join(out_dir, "econ_huashu", "specs")
    clips_dir = os.path.join(out_dir, "econ_huashu", "clips")

    with open(audio_json, encoding="utf-8") as f:
        segs = json.load(f)

    # 每段精确秒数 → 整数帧（累计帧与累计时间严丝合缝）
    cum_t = 0.0
    seg_frames = []
    prev_f = 0
    for s in segs:
        cum_t += s["dur"]
        cur_f = round(cum_t * FPS)
        seg_frames.append(cur_f - prev_f)
        prev_f = cur_f
    durs = [f / FPS for f in seg_frames]
    print(f"[audio] {len(segs)} 段，总时长 {sum(durs):.3f}s，帧数 {sum(seg_frames)}")

    seg_cfg = cfg.get("segments", {})
    used_segs = sorted(int(k) for k in seg_cfg)
    missing = [i for i in range(len(segs)) if i not in used_segs]
    if missing:
        print(f"[warn] 配置缺少段落索引 {missing}（这些段不会出现在动画里）")
    over = [i for i in used_segs if i >= len(segs)]
    if over:
        raise SystemExit(f"[error] 配置段索引 {over} 超出 TTS 实际段数 {len(segs)}")

    shots = []
    for seg_idx in used_segs:
        sc = seg_cfg[str(seg_idx)]
        ratios = sc.get("ratios") or [1.0]
        shot_list = sorted(sc.get("shots", []), key=lambda s: s.get("part", 0))
        total_f = seg_frames[seg_idx]
        n = len(shot_list)
        # 比例数与镜头数对齐：不足则末镜补齐，超出则截断（保证帧数总和严格 = 该段帧数）
        r = list(ratios)[:n]
        while len(r) < n:
            r.append(0.0)
        frames = []
        acc = 0
        for ratio in r[:-1]:
            f = round(total_f * ratio) if ratio else 0
            frames.append(f)
            acc += f
        frames.append(total_f - acc)
        for idx, sh in enumerate(shot_list):
            f = frames[idx]
            shots.append({
                "id": sh["id"],
                "grammar": sh["grammar"],
                "duration": f / FPS,
                "cues": sh["cues"],
                **({"data": sh["data"]} if "data" in sh else {}),
            })

    errors = lint_y5(shots)
    if errors:
        print("[lint] ❌ y5 排版违规：")
        for e in errors:
            print("   -", e)
        raise SystemExit("[error] 分镜排版自检未通过，请修正配置后重跑")
    print(f"[lint] ✅ y5 排版自检通过（{len(shots)} 镜）")

    os.makedirs(specs_dir, exist_ok=True)
    os.makedirs(clips_dir, exist_ok=True)

    tot_frames = sum(round(sh["duration"] * FPS) for sh in shots)
    expect = sum(seg_frames[i] for i in used_segs)
    print(f"[spec] {len(shots)} 镜，总帧数 {tot_frames} ({tot_frames/FPS:.3f}s)，期望 {expect}")
    assert tot_frames == expect, f"帧数不一致: {tot_frames} != {expect}"

    spec_files = []
    for sh in shots:
        spec = {
            "grammar": sh["grammar"],
            "duration": sh["duration"],
            "fps": FPS,
            "width": 1920,
            "height": 1080,
            "theme": THEME,
            "safe": SAFE,
            "cues": sh["cues"],
        }
        if "data" in sh:
            spec["data"] = sh["data"]
        sp_path = os.path.join(specs_dir, f"{sh['id']}.json")
        with open(sp_path, "w", encoding="utf-8") as f:
            json.dump(spec, f, ensure_ascii=False, indent=2)
        spec_files.append((sh["id"], sp_path, sh["duration"]))
    return spec_files, clips_dir


def render_all(spec_files, clips_dir):
    # ⚠️ Windows 子进程 PATH 陷阱（2026-11-02 实测）：传 env={"PATH": ...} 无效，
    #    进程查找可执行文件读的是**进程级**环境块 → 必须改 os.environ。
    os.environ["PATH"] = FFMPEG_BIN + os.pathsep + os.environ.get("PATH", "")
    env = os.environ.copy()
    env.setdefault("HTTPS_PROXY", "http://127.0.0.1:10808")
    env.setdefault("HTTP_PROXY", "http://127.0.0.1:10808")
    render_py = os.path.join(HUASHU_ENGINE, "render.py")

    clip_paths = []
    for idx, (sid, sp_path, dur) in enumerate(spec_files, 1):
        out_mp4 = os.path.join(clips_dir, f"{sid}.mp4")
        clip_paths.append(out_mp4)
        if os.path.exists(out_mp4) and os.path.getsize(out_mp4) > 5000:
            print(f"  [{idx}/{len(spec_files)}] 复用已存在 {sid}.mp4 ({dur:.2f}s)", flush=True)
            continue
        print(f"  [{idx}/{len(spec_files)}] 渲染 {sid} ({dur:.2f}s) ...", flush=True)
        # ⚠️ 本机 uv 已不存在（2026-11-02 实测），改为直接用当前解释器跑引擎 render.py
        #    引擎只依赖 playwright + 标准库，无需 uv 环境
        cmd = [sys.executable, render_py, "--spec", sp_path, "--out", out_mp4]
        subprocess.run(cmd, cwd=HUASHU_ENGINE, env=env, check=True)
    return clip_paths


def concat_clips(clip_paths, prep_date):
    """拼接所有镜头为静音底片。"""
    out_dir = os.path.join(PROJECT_ROOT, "output", "weekly", prep_date)
    final_bg = os.path.join(out_dir, "econ_huashu", "econ_huashu_bg.mp4")
    list_file = os.path.join(out_dir, "econ_huashu", "concat_list.txt")
    with open(list_file, "w", encoding="utf-8") as f:
        for p in clip_paths:
            f.write(f"file '{os.path.abspath(p)}'\n")
    cmd = [
        FFMPEG, "-y", "-v", "error", "-f", "concat", "-safe", "0",
        "-i", list_file,
        "-c:v", "libx264", "-preset", "fast", "-crf", "18",
        "-pix_fmt", "yuv420p", "-r", str(FPS),
        final_bg,
    ]
    subprocess.run(cmd, check=True)
    print(f"[concat] → {final_bg}")
    return final_bg


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags = [a for a in sys.argv[1:] if a.startswith("--")]
    prep_date = args[0] if args else "20261016"
    custom = None
    if "--config" in flags:
        i = flags.index("--config")
        custom = flags[i + 1] if i + 1 < len(flags) else None

    cfg, _ = load_config(prep_date, custom)
    spec_files, clips_dir = build_specs(prep_date, cfg)
    if "--specs-only" in flags:
        print("[done] 仅生成 spec，未渲染")
        return
    clip_paths = render_all(spec_files, clips_dir)
    concat_clips(clip_paths, prep_date)
    print("[done]")


if __name__ == "__main__":
    main()
