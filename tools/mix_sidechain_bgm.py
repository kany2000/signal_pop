# -*- coding: utf-8 -*-
"""侧链闪避混音工具（mix_sidechain_bgm.py）

借鉴自开源项目 simontalk-investigation 的核心音频工艺：
    - 旁白人声说话时，背景音乐通过 sidechaincompress 滤镜毫秒级自动压低（ducking）；
    - 人声停顿/转场/呼吸气口时，BGM 在 350ms 内自然平滑回弹饱满；
    - 混音后经过 alimiter 峰值限幅（0.95），绝不破音；
    - 视频轨使用 -c:v copy，完全不重编码，极速导出。

2026-10-12 增补（自 signal-motion/cognition/mix_final.py 移植，遵循外科手术式迁移）：
    - **两遍 loudnorm 响度归一**。起因：实测 20261002 成片 I=-19.9 LUFS，比抖音推荐
      的 -14 偏轻 5.9dB，播放时「像没推音量」。信号弹认知版同样是 -20.8 LUFS。
    - **`--segments start:end` 分段铺底**（补 OpenMontage audio_mixer._segmented_music 的能力）。
    - **`--check` / `--stems` 两个数据门禁**：不改片子就能读响度，并把人声与 ducked
      配乐分轨导出，量化「配乐相对人声差几 dB」。
      **为什么要 stems**：sidechaincompress 的实际衰减量取决于输入电平，参数写
      -12dB 只是上限意图、不是实测结果，只能靠分轨测出来。

  ⚠️ **实测数据推翻了一个假设**：`--segments` 对本项目两个片子都用不上。
  信号弹认知版语音覆盖 **100%**（9 段首尾相接，xfade 只是视觉交叉溶解）；
  周末版 20261002覆盖 **98.4%**（37 段对话，同样首尾相接）——
  两片都**没有一秒钟空隙**，所以「配乐只塞空隙」退化为「全程铺底 + ducking」。
  工具现在会自动算这个比例并提示，别再凭印象以为有空隙可用。

用法示例：
    python tools/mix_sidechain_bgm.py input_video.mp4 bgm.mp3 -o output_video.mp4
    python tools/mix_sidechain_bgm.py input_video.mp4 bgm.mp3 --bgm-vol 0.20
    python tools/mix_sidechain_bgm.py input_video.mp4 bgm.mp3 --lufs -14   # 响度归一到 -14
    python tools/mix_sidechain_bgm.py input_video.mp4 --check# 只读响度，零改动
    python tools/mix_sidechain_bgm.py input_video.mp4 bgm.mp3 --stems     # 导出分轨核对配乐电平
    python tools/mix_sidechain_bgm.py input_video.mp4 bgm.mp3 --segments 0:30 120:150
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FFMPEG = ROOT / "bin" / "ffmpeg-9.0.1-essentials_build" / "bin" / "ffmpeg.exe"
FFPROBE = ROOT / "bin" / "ffmpeg-9.0.1-essentials_build" / "bin" / "ffprobe.exe"

TARGET_LUFS = -14.0
TARGET_TP = -1.5
TARGET_LRA = 11.0


def _run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, errors="replace")


def parse_loudness(media_path: Path) -> dict:
    """ebur128 汇总值（I / LRA / True Peak）。

    **必须锚定 Summary 块**：ebur128 每 0.1s 往 stderr 打一行进度
    （`t: 94.9 ... I: -70.0 LUFS LRA: 0.0`）。若在全量 stderr 上直接
    re.search('I:')，命中的是**第一帧瞬时值**而非综合响度 —— 实测会得到
    I=-70.0 / LRA=0.0，与真实值差 50dB，让验收门禁彻底失效（本项目已踩）。
    """
    res = _run([str(FFMPEG), "-hide_banner", "-i", str(media_path),
                "-af", "ebur128=peak=true", "-f", "null", "NUL"])
    out = res.stderr
    idx = out.rfind("Summary:")
    tail = out[idx:] if idx >= 0 else out

    def grab(label: str):
        m = re.search(rf"^\s*{re.escape(label)}\s*(-?\d+(?:\.\d+)?)", tail, re.M)
        return float(m.group(1)) if m else None

    return {"I": grab("I:"), "LRA": grab("LRA:"), "TP": grab("Peak:")}


def speech_seconds(segments_json: Path | None) -> float | None:
    """从音频分段 json累加净语音时长（用于算覆盖率，判断有没有空隙可用）。"""
    if not segments_json or not segments_json.exists():
        return None
    try:
        data = json.loads(segments_json.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    durs = data if isinstance(data, list) else list(data.values())
    try:
        return sum(float(d["dur"]) for d in durs)
    except (KeyError, TypeError, ValueError):
        return None


def get_duration(media_path: Path) -> float:
    cmd = [
        str(FFPROBE), "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(media_path)
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    try:
        return float(res.stdout.strip())
    except (ValueError, IndexError):
        raise RuntimeError(f"无法读取媒体时长: {media_path} ({res.stderr})")


def build_volume_expr(segments: list[tuple[float, float]], total: float, vol: float,
                      fade: float = 1.5) -> str:
    """分段配乐音量表达式（语义同 OpenMontage audio_mixer._segmented_music）。

    配乐只在 segments 区间内响，区间外返回 0；每段首尾各留 fade 秒渐变。
    多区间用覆盖式 if/lt 串联（命中即定值），不是相加 —— 重叠时不会叠加超过 vol。
    """
    parts = []
    for s, e in sorted(segments):
        s = max(0.0, min(s, total))
        e = max(0.0, min(e, total))
        if e - s < 0.05:
            continue
        parts.append(
            f"if(lt(t,{s:.3f}),0,"
            f"if(lt(t,{s + fade:.3f}),{vol}*(t-{s:.3f})/{fade},"
            f"if(lt(t,{e - fade:.3f}),{vol},"
            f"if(lt(t,{e:.3f}),{vol}*({e:.3f}-t)/{fade},0))))"
        )
    if not parts:
        return "0"
    if len(parts) == 1:
        return parts[0]
    return "+".join(f"({p})" for p in parts)


def parse_segments(raw) -> list[tuple[float, float]]:
    """'0:30 120:150' → [(0.0, 30.0), (120.0, 150.0)]"""
    out = []
    for tok in (raw or []):
        m = re.fullmatch(r"([\d.]+)\s*:\s*([\d.]+)", str(tok).strip())
        if not m:
            print(f"[-] 错误: --segments 语法错: {tok!r}（应形如 0:30 120:150，单位秒）")
            raise SystemExit(1)
        out.append((float(m.group(1)), float(m.group(2))))
    return out


def mix_sidechain(
    video_path: Path,
    bgm_path: Path | None,
    output_path: Path,
    bgm_vol: float = 0.22,
    threshold: float = 0.008,
    ratio: float = 6.0,
    attack_ms: int = 20,
    release_ms: int = 350,
    segments: list[tuple[float, float]] | None = None,
    lufs: float | None = None,
    tp: float = TARGET_TP,
    lra: float = TARGET_LRA,
    stems_dir: Path | None = None,
) -> bool:
    if not video_path.exists():
        print(f"[-] 错误: 视频文件不存在: {video_path}")
        return False
    if bgm_path is not None and not bgm_path.exists():
        print(f"[-] 错误: 背景音乐文件不存在: {bgm_path}")
        return False

    dur = get_duration(video_path)
    fadeout_st = max(0.0, dur - 3.5)
    do_music = bgm_path is not None

    print(f"[*] 开始侧链闪避混音: {video_path.name} (时长: {dur:.2f}s)")
    if do_music:
        print(f"[*] BGM: {bgm_path.name} (音量: {bgm_vol}, 压缩比: {ratio}, 阈值: {threshold})")
    else:
        print("[*] 未提供 BGM → 仅做响度归一")
    if lufs is not None:
        print(f"[*] 响度归一目标: I={lufs} LUFS / TP={tp} / LRA={lra}")

    # 滤镜链：
    # [1:a] BGM 音量（可选分段表达式）-> 循环覆盖视频时长 -> 采样率对齐 -> 淡入淡出 -> [bg]
    # [0:a] 原视频人声拆分 -> 一路保留 [nar]，一路作为侧链触发器 [key]
    # [bg][key] sidechaincompress 侧链压制 -> [duck]
    # [nar][duck] amix（normalize=0 保证人声不被二次衰减）-> alimiter 防破音 -> [mix]
    #
    # ⚠️ afade 必须在音量/循环**之前**（这里顺序已正确）。afade=t=out 的 st 默认 0，
    # 若排在adelay 之后会淡出「延迟产生的静音」，导致延迟轨一开播就已是静音。
    if do_music:
        if segments:
            vol_expr = build_volume_expr(segments, dur, bgm_vol)
            print(f"[*] 分段铺底: {len(segments)} 段，覆盖 {sum(e - s for s, e in segments):.1f}s / {dur:.1f}s")
        else:
            vol_expr = str(bgm_vol)
        chain = [
            f"[1:a]volume='{vol_expr}':eval=frame,aresample=48000,"
            f"afade=t=in:st=0:d=1.5,afade=t=out:st={fadeout_st:.2f}:d=3.5[bg];",
            "[0:a]asplit=2[nar][key];",
            f"[bg][key]sidechaincompress=threshold={threshold}:ratio={ratio}"
            f":attack={attack_ms}:release={release_ms}[duck];",
        ]
        if stems_dir is not None:
            # 分轨导出：把 ducked 后的配乐单独落盘，才能量化「实际退让了几 dB」。
            # sidechaincompress 的衰减取决于输入电平，无法靠参数值反推，只能测。
            stems_dir.mkdir(parents=True, exist_ok=True)
        tail = "[nar][duck]amix=inputs=2:duration=first:dropout_transition=0:normalize=0"
        if lufs is None:
            tail += ",alimiter=limit=0.95[mix]"
        else:
            # lufs 模式也要落 [mix] 标签 —— 落标签后再用 "[mix]loudnorm...[mix2]" 续接。
            # 实测三种写法（ffmpeg 9.0.1，20261012）：
            #   A "[0:a]anull;loudnorm[o]"                ✗ Cannot find an unused audio input stream
            #   B "[0:a]anull[m];[m]loudnorm[o]"           ✅ 唯一正确
            #   C "[0:a]anull[m]loudnorm[o]"（无分号）     ✗ Trailing garbage after a filter
            tail += "[mix]"
        chain.append(tail + ";")
    else:
        # 无 BGM 时也要按 B 写法落标签，lufs 分支才能续接。
        chain = ["[0:a]anull[nar];", "[nar]anull[mix];"]

    cmd = [str(FFMPEG), "-nostdin", "-y", "-v", "error", "-i", str(video_path)]
    if do_music:
        cmd += ["-stream_loop", "-1", "-t", str(dur), "-i", str(bgm_path)]
    cmd += ["-filter_complex", "".join(chain)]

    # ── 两遍 loudnorm ─────────────────────────────────────
    # 顺序上loudnorm 必须在 alimiter **之后** 或替代它。
    # 这里用「替代」方案：loudnorm 自带 TP 上限（TP=-1.5），比固定 alimiter=0.95
    # 更准；alimiter 0.95 相当于 -0.45dBFS，留给平台转码的余量偏小。
    if lufs is not None:
        ln_probe = f"loudnorm=I={lufs}:TP={tp}:LRA={lra}:print_format=json"
        # 第一遍：动态模式测量（拿 input_i/input_tp/input_lra）。
        # 必须把 loudnorm 接进 filter_complex 链里（用 -af 会与 -filter_complex 冲突，
        # 且 -af 只作用最后一个流）；这里在链尾追加一个测量分支。
        # chain 以 "[nar]anull[mix];" 收尾，按实测写法 B 用"[mix]loudnorm"续接。
        #
        # ⚠️ 关键：测量遍必须用 -v info（不能用继承来的 -v error）。
        # loudnorm的 print_format=json 输出走 **info 级**，被 error 级别过滤掉后
        # res.stderr 里根本没有 JSON，于是 meas={} → 永远退回单遍动态模式，
        # 结果恒定差 1.3dB（实测：目标 -14 出 -15.3，目标 -12.7 出 -15.0/-12.5）。
        # 这个 bug 表现为"数据看似正常只是差一点点"，最难靠肉眼发现。
        meas_cmd = [str(FFMPEG), "-nostdin", "-y", "-v", "info", "-i", str(video_path)]
        if do_music:
            meas_cmd += ["-stream_loop", "-1", "-t", str(dur), "-i", str(bgm_path)]
        # ⚠️ 必须**重建** cmd 而不能在 cmd 上 append：cmd 里已含一个 -filter_complex，
        # 再追加第二个会报 "Option filtergraph 1 was specified twice" 并直接退出
        # （returncode≠0，stderr 里根本没有 loudnorm 的 JSON），
        # 于是 meas={} → 永远退回单遍动态模式 → 结果恒定差 1.3dB。
        # 这个 bug 表现为"数据看似正常只差一点点"，肉眼绝对发现不了。
        meas_cmd += ["-filter_complex", "".join(chain) + f"[mix]{ln_probe}[probe]",
                     "-map", "[probe]", "-ar", "48000", "-ac", "2",
                     "-f", "null", "NUL"]
        res = _run(meas_cmd)
        m = re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", res.stderr, re.S)
        meas = {}
        if m:
            try:
                meas = json.loads(m.group(0))
            except json.JSONDecodeError:
                meas = {}
        # 只保留**有效数值**字段：把None 拼进滤镜串会报
        # "failed to convert ... None" 或直接 Trailing garbage（实测踩过）。
        meas = {k: v for k, v in meas.items() if v not in (None, "", "inf", "-inf")}
        if meas.get("input_i") not in (None, ""):
            print(f"[*] 第一遍实测: I={meas.get('input_i')} TP={meas.get('input_tp')} LRA={meas.get('input_lra')}")
        else:
            print("[!] 警告: 未取到 loudnorm 测量值，退回单遍动态模式（不带 measured_* 参数）")
            meas = {}
        ln = f"loudnorm=I={lufs}:TP={tp}:LRA={lra}"
        if meas:
            # 第二遍线性模式：用第一遍的实测值做精确归一，比单遍动态模式准。
            # 键名映射：input_i → measured_I，input_thresh → measured_thresh 等。
            for src, dst in (("input_i", "measured_I"), ("input_tp", "measured_TP"),
                             ("input_lra", "measured_LRA"), ("input_thresh", "measured_thresh"),
                             ("target_offset", "offset")):
                if meas.get(src) not in (None, ""):
                    ln += f":{dst}={meas[src]}"
            ln += ":linear=true"
        cmd = [str(FFMPEG), "-nostdin", "-y", "-v", "error", "-i", str(video_path)]
        if do_music:
            cmd += ["-stream_loop", "-1", "-t", str(dur), "-i", str(bgm_path)]
        # 按实测写法 B续接：chain 已落 [mix] 标签并以分号结尾。
        cmd += ["-filter_complex", "".join(chain) + f"[mix]{ln}[mix2]",
                "-map", "0:v", "-map", "[mix2]"]
    else:
        cmd += ["-map", "0:v", "-map", "[mix]"]

    cmd += [
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
        "-shortest", "-movflags", "+faststart",
        str(output_path),
    ]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    res = _run(cmd)
    if res.returncode != 0:
        print(f"[-] 混音失败: {res.stderr}")
        return False

    print(f"[+] 混音成功，成片已导出至: {output_path}")

    # ── 分轨导出 + 配乐/人声电平核对（--stems） ──────────────
    if stems_dir is not None and do_music:
        # WAV muxer 不支持「一个文件两路音频」（报wav muxer does not support more
        # than one stream of type audio），所以拆成两次调用各出一轨。
        sp = stems_dir / "stem_speech.wav"
        mu = stems_dir / "stem_music_ducked.wav"
        stem_base = [
            "[1:a]volume='%s':eval=frame,aresample=48000[bg];" % vol_expr,
            "[0:a]asplit=2[nar][key];",
            f"[bg][key]sidechaincompress=threshold={threshold}:ratio={ratio}"
            f":attack={attack_ms}:release={release_ms}[duck];",
        ]
        r1 = _run([str(FFMPEG), "-nostdin", "-y", "-v", "error", "-i", str(video_path),
                   "-stream_loop", "-1", "-t", str(dur), "-i", str(bgm_path),
                   "-filter_complex", "".join(stem_base) + "[duck]anull[o]",
                   "-map", "[o]", "-ar", "48000", "-ac", "2", str(mu)])
        r2 = _run([str(FFMPEG), "-nostdin", "-y", "-v", "error", "-i", str(video_path),
                   "-filter_complex", "[0:a]anull[o]", "-map", "[o]",
                   "-ar", "48000", "-ac", "2", str(sp)])
        if r1.returncode == 0 and r2.returncode == 0:
            a, b = parse_loudness(sp), parse_loudness(mu)
            print(f"[*] 分轨: 人声 I={a['I']} LUFS / ducked 配乐 I={b['I']} LUFS")
            if a["I"] is not None and b["I"] is not None:
                gap = b["I"] - a["I"]
                # -14dB 是口播类常用下限：可感但不压人声
                verdict = "OK" if gap <= -14 else ("偏近" if gap <= -10 else "压人声")
                print(f"[*] 配乐相对人声 {gap:+.1f} dB → {verdict}（建议 ≤ -14dB）")
                if gap > -10:
                    print(f"[!] 建议降低 --bgm-vol（当前 {bgm_vol}，可试 {bgm_vol * 0.55:.3f}）")
        else:
            print(f"[!] 分轨导出失败: {(r1.stderr or r2.stderr)[-500:]}")

    # ── 验收门禁 ─────────────────────────────────────────
    if lufs is not None:
        fin = parse_loudness(output_path)
        print(f"[*] 响度验收: I={fin['I']} LUFS（目标 {lufs}） TP={fin['TP']} dBFS（上限 {tp}）")
        ok = True
        if fin["I"] is not None and abs(fin["I"] - lufs) > 1.0:
            print("[-] FAIL: 响度未达标"); ok = False
        if fin["TP"] is not None and fin["TP"] > tp + 0.3:
            print("[-] FAIL: 真峰超标"); ok = False
        if ok:
            print("[+] 响度门禁通过")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(
        description="FFmpeg 侧链闪避混音工具（旁白说话时 BGM 自动下潜）")
    parser.add_argument("video", type=Path, help="输入的视频文件 (含人声音轨)")
    parser.add_argument("bgm", type=Path, nargs="?", default=None,
                        help="背景音乐音频文件 (mp3/wav)；省略则只做响度归一")
    parser.add_argument("-o", "--output", type=Path, default=None,
                        help="输出视频路径，默认覆盖或加 _duck 后缀")
    parser.add_argument("--bgm-vol", type=float, default=0.22, help="BGM 基础音量比例 (默认 0.22)")
    parser.add_argument("--threshold", type=float, default=0.008, help="人声感应触发阈值 (默认 0.008)")
    parser.add_argument("--ratio", type=float, default=6.0, help="侧链压缩比 (默认 6.0)")
    parser.add_argument("--attack", type=int, default=20, help="侧链 attack (毫秒)")
    parser.add_argument("--release", type=int, default=350, help="侧链 release (毫秒)")
    parser.add_argument("--segments", nargs="+", metavar="S:E",
                        help="分段铺底：配乐只在这些区间响，如 0:30 120:150（秒）")
    parser.add_argument("--lufs", type=float, default=None,
                        help=f"响度归一目标 (如 -14)；不给则只混音不归一")
    parser.add_argument("--tp", type=float, default=TARGET_TP, help="真峰上限 (默认 -1.5)")
    parser.add_argument("--lra", type=float, default=TARGET_LRA, help="响度范围目标 (默认 11)")
    parser.add_argument("--check", action="store_true",
                        help="只读响度与语音覆盖率，零改动")
    parser.add_argument("--segments-json", type=Path, default=None,
                        help="音频分段 json（tts_segments.json 等），用于算语音覆盖率")
    parser.add_argument("--stems", action="store_true",
                        help="导出人声/ducked 配乐分轨，量化配乐相对人声的电平差")

    args = parser.parse_args()

    if not args.video.exists():
        print(f"[-] 错误: 视频文件不存在: {args.video}")
        return 1

    # ── --check：数据门禁的只读入口 ──────────────────────
    if args.check:
        dur = get_duration(args.video)
        lod = parse_loudness(args.video)
        print(f"[*] {args.video.name}  时长 {dur:.2f}s")
        print(f"[*] I={lod['I']} LUFS  LRA={lod['LRA']}  TP={lod['TP']} dBFS")
        print(f"[*] 目标 I={args.lufs if args.lufs is not None else TARGET_LUFS} / "
              f"TP={args.tp} / LRA={args.lra}")
        if lod["I"] is not None:
            tgt = args.lufs if args.lufs is not None else TARGET_LUFS
            print(f"[*] 差值: 需要提升 {tgt - lod['I']:+.1f} dB")
        sp = speech_seconds(args.segments_json)
        if sp is not None:
            ratio = sp / dur if dur else 0
            print(f"[*] 语音覆盖 {sp:.1f}s / {dur:.1f}s = {ratio*100:.1f}%")
            if ratio > 0.95:
                print("[!] 语音几乎占满全片 → --segments 会退化为「全程铺底 + ducking」")
            elif ratio > 0.8:
                print("[*] 有少量空隙，--segments 才有意义")
        else:
            print("[*] 未提供 --segments-json，跳过语音覆盖率检查")
        return 0

    out_path = args.output
    if out_path is None:
        out_path = args.video.with_name(f"{args.video.stem}_ducked.mp4")

    segs = parse_segments(args.segments) if args.segments else None

    ok = mix_sidechain(
        args.video, args.bgm, out_path,
        bgm_vol=args.bgm_vol, threshold=args.threshold, ratio=args.ratio,
        attack_ms=args.attack, release_ms=args.release,
        segments=segs,
        lufs=args.lufs, tp=args.tp, lra=args.lra,
        stems_dir=(args.video.parent / "_qa_stems") if args.stems else None,
    )
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
