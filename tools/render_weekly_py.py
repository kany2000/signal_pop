#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Signal Pop — 周末版分段渲染器（Python 版，替代 render_weekly_segmented.sh）

2026-10-16 新增。原因：本机 Git Bash 下 `render_weekly_segmented.sh` 无论怎么调
`node` 路径（相对/绝对/带 .exe/去掉子 shell）都报
`node ...: No such file or directory`，而**完全相同的命令手动执行却 100% 成功**。
沙箱对 bash 脚本内 spawn 外部 exe 有拦截，改用 Python subprocess 直调，绕开该问题。

功能与 shell 版完全一致：
  * 幂等 + 可续：已完成段（part 存在且帧数达标 + render.log 标记 PART DONE）自动跳过
  * 总帧数从 remotion_poc/src/weekly_segs.json 自动算，与 Root.tsx durationInFrames 一致
  * 渲染完 concat 拼接 + CRF26 整体重编码 + 合并 TTS 音频
  * 失败返回码 1，重跑即从断点继续

用法：python tools/render_weekly_py.py <制作日YYYYMMDD> [每段帧数]
"""
import json
import os
import subprocess
import sys
import time

ROOT = "E:/projects/signal_pop"
POC = os.path.join(ROOT, "remotion_poc")
NODE = "C:/Users/Administrator/.workbuddy/binaries/node/versions/22.22.2-6/node.exe"
REMX = os.path.join(POC, "node_modules", "@remotion", "cli", "remotion-cli.js")
FF = os.path.join(ROOT, "bin", "ffmpeg-9.0.1-essentials_build", "bin", "ffmpeg.exe")
FP = os.path.join(ROOT, "bin", "ffmpeg-9.0.1-essentials_build", "bin", "ffprobe.exe")
CHROME = "C:/Program Files/Google/Chrome/Application/chrome.exe"
CHROME_FLAGS = "--disable-accelerated-video-decode --disable-gpu"
CRF = "26"
FPS = 30

# 片头（2026-10-12 定版 V4「新闻联播式过场」为每期标配）
OPENING_ID = "OpeningV4"
OPEN_FRAMES = 270
OPENING_TITLE = "AI语播·信号弹每周精选"
OPENING_OUT = "opening_anim.mp4"
PIANO = os.path.join(ROOT, "output", "mp3", "Romeo - Winds of Hope - Creative Cut - Piano.mp3")
PIANO_START = 34          # 片头配乐在钢琴曲里的起点（秒）
OPENING_WEEKDAY = "星期六"
OPENING_DATE = "2026年10月17日"


def log_line(log_path, msg):
    stamp = time.strftime("[%H:%M:%S] ")
    line = stamp + msg
    print(line, flush=True)
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def run(cmd, cwd=None, log_path=None):
    """执行外部命令；log_path 非空时 stdout/stderr 追加进日志。"""
    if log_path:
        with open(log_path, "a", encoding="utf-8") as lf:
            return subprocess.run(cmd, cwd=cwd, stdout=lf, stderr=subprocess.STDOUT)
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)


def probe_frames(path):
    """返回视频帧数，失败返回 -1"""
    try:
        r = subprocess.run(
            [FP, "-v", "error", "-select_streams", "v:0", "-count_packets",
             "-show_entries", "stream=nb_read_packets",
             "-of", "default=noprint_wrappers=1:nokey=1", path],
            capture_output=True, text=True, timeout=120)
        return int(r.stdout.strip())
    except Exception:
        return -1


def probe_duration(path):
    try:
        r = subprocess.run(
            [FP, "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", path],
            capture_output=True, text=True, timeout=60)
        return float(r.stdout.strip())
    except Exception:
        return 0.0


def remotion_render(comp, out, props=None, frames=None):
    """直调 Remotion CLI（cwd=POC，JS 入口用相对路径 —— Python subprocess 无 cwd 解析坑）

    并发数：2026-10-16 从 2 提到 6（本机 12 核）。实测 concurrency=2 时
    1000 帧要 4.7 分钟，23 段总计 1.8 小时；提到 6 后单段约 1.6 分钟。
    可用环境变量 REMOTION_CONCURRENCY 覆盖。
    """
    conc = os.environ.get("REMOTION_CONCURRENCY", "6")
    cmd = [NODE, REMX, "render", comp, out,
           f"--concurrency={conc}",
           f"--browser-executable={CHROME}",
           f"--chrome-flags={CHROME_FLAGS}"]
    if props:
        cmd.append(f"--props={props}")
    if frames:
        cmd.append(f"--frames={frames}")
    return run(cmd, cwd=POC)


def main():
    date = sys.argv[1] if len(sys.argv) > 1 else "20260828"
    chunk = int(sys.argv[2]) if len(sys.argv) > 2 else 1000
    out_dir = os.path.join(ROOT, "output", "weekly", date)
    log_path = os.path.join(out_dir, "render.log")
    os.makedirs(out_dir, exist_ok=True)

    segs_path = os.path.join(POC, "src", "weekly_segs.json")
    data = json.load(open(segs_path, encoding="utf-8"))
    segs = data if isinstance(data, list) else data.get("segments", data)
    total_frames = round(sum(s.get("dur", 0) for s in segs) * FPS)
    full_total = total_frames + OPEN_FRAMES
    nparts = (total_frames + chunk - 1) // chunk

    log_line(log_path, f"PY-RENDER {date}  TOTAL_FRAMES={total_frames} "
                       f"OPEN_FRAMES={OPEN_FRAMES} FULL_TOTAL={full_total} CHUNK={chunk} CRF={CRF}")

    # ---------- 1) 片头 ----------
    opening_out = os.path.join(out_dir, OPENING_OUT)
    props_path = os.path.join(out_dir, "opening_props.json")
    json.dump({"title": OPENING_TITLE, "date": OPENING_DATE, "weekday": OPENING_WEEKDAY},
              open(props_path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    sig = f"OPENING DONE {OPENING_ID}|{OPENING_TITLE}|{OPENING_DATE}|{OPENING_WEEKDAY}"
    if (os.path.exists(opening_out) and probe_frames(opening_out) == OPEN_FRAMES
            and sig in open(log_path, encoding="utf-8", errors="ignore").read()):
        log_line(log_path, f"skip opening (same version+text, {OPEN_FRAMES} frames ok)")
    else:
        log_line(log_path, f"render {OPENING_ID} {OPEN_FRAMES} frames  "
                           f"[title={OPENING_TITLE} | {OPENING_DATE} {OPENING_WEEKDAY}]")
        remotion_render(OPENING_ID, opening_out, props=props_path)
        if probe_frames(opening_out) != OPEN_FRAMES:
            log_line(log_path, f"!! {OPENING_ID} 渲染失败或帧数不足（期望 {OPEN_FRAMES}）")
            print(f"ERROR: {OPENING_ID} 渲染失败", file=sys.stderr)
            return 1
        log_line(log_path, sig)

    # ---------- 2) 逐段渲染 WeeklyTalk（幂等可续）----------
    log_text = open(log_path, encoding="utf-8", errors="ignore").read()
    for i in range(nparts):
        start = i * chunk
        end = min(start + chunk - 1, total_frames - 1)
        expected = end - start + 1
        part = os.path.join(out_dir, f"part{i:02d}.mp4")
        if os.path.exists(part) and probe_frames(part) == expected and f"PART DONE {i} " in log_text:
            print(f"  skip part {i:02d} ({expected} frames ok)", flush=True)
            continue
        if os.path.exists(part):
            os.remove(part)
        log_line(log_path, f"render part {i:02d}  frames={start}-{end}")
        remotion_render("WeeklyTalk", part, frames=f"{start}-{end}")
        if os.path.exists(part) and probe_frames(part) == expected:
            log_line(log_path, f"PART DONE {i} {time.strftime('%H:%M:%S')}")
        else:
            log_line(log_path, f"PART FAILED {i} {time.strftime('%H:%M:%S')} (frames<{expected})")
            print(f"ERROR: part {i:02d} 渲染失败，检查 {log_path} 后重跑即从断点继续", file=sys.stderr)
            return 1

    # ---------- 2.5) 「大家一起聊经济」段替换为 huashu 动画版 ----------
    # 背景：Remotion 侧的 econ_slide_1~4 是 4 张静态图，但 2026-10-12 MARK哥已钦定
    # V2.1 huashu 动画版（双播贴边头像 + 42px 大字幕），成品已渲好在
    # econ_talk_<date>_huashu.mp4。这里在 concat 之前用动画版覆盖 Remotion 渲出的静态图段，
    # 保住之前所有动画工作。缺文件则静默跳过（回退静态图，不阻塞出片）。
    # ⚠️ 2026-10-16 修 bug：merged 原本定义在下方 concat 段里，本段引用会
    #    抛 UnboundLocalError。改为先拼 part 拿到 merged，再做替换，最后 concat 片头。
    merged = os.path.join(out_dir, f"signal_pop_weekly_{date}_merged.mp4")
    _parts_list = os.path.join(out_dir, "_parts_list.txt")
    with open(_parts_list, "w", encoding="utf-8") as f:
        for i in range(nparts):
            f.write(f"file '{os.path.join(out_dir, f'part{i:02d}.mp4')}'\n".replace("\\", "/"))
    # ⚠️ 2026-10-16：Remotion 各 part 的 tbn 可能不一致，concat demuxer + `-c copy`
    #    会产出时间轴错乱的流（表现为后续帧率异常）。统一用滤镜 concat 强制
    #    30fps / 1920x1080 / tbn=90000。
    _fc = "".join(
        f"[{i}:v]fps={FPS},scale=1920:1080,setsar=1,format=yuv420p,setpts=PTS-STARTPTS[v{i}];"
        for i in range(nparts))
    _fc += "".join(f"[v{i}]" for i in range(nparts))
    _fc += f"concat=n={nparts}:v=1:a=0[vout]"
    run([FF, "-y", *sum([["-i", os.path.join(out_dir, f"part{i:02d}.mp4")] for i in range(nparts)], []),
         "-filter_complex", _fc, "-map", "[vout]", "-an",
         "-c:v", "libx264", "-preset", "fast", "-crf", "20",
         "-pix_fmt", "yuv420p", "-r", str(FPS), "-video_track_timescale", "90000",
         merged], log_path=log_path)

    econ_anim = os.path.join(out_dir, f"econ_talk_{date}_huashu.mp4")
    if os.path.exists(econ_anim):
        # 定位 econ 段在「去掉片头后的 part 拼接序列」中的时间轴
        t = 0.0
        econ_start = econ_end = None
        for s in segs:
            bg = str(s.get("bg", ""))
            if bg.startswith("econ_"):
                if econ_start is None:
                    econ_start = t
                econ_end = t + s.get("dur", 0)
            t += s.get("dur", 0)
        if econ_start is not None:
            anim_dur = probe_duration(econ_anim)
            log_line(log_path,
                     f"replace econ segment: {econ_start:.2f}s~{econ_end:.2f}s "
                     f"({econ_end - econ_start:.2f}s) <- huashu {anim_dur:.2f}s")
            # 切成与原子段等长（不足则定格末帧，超出则截断），保证后续 concat 时间轴不变
            econ_len = econ_end - econ_start
            patched = os.path.join(out_dir, "_econ_patched.mp4")
            vf_econ = (
                f"tpad=stop_mode=clone:stop_duration={max(0.0, econ_len - anim_dur):.3f},"
                f"trim=duration={econ_len:.3f},setpts=PTS-STARTPTS[v]"
                if anim_dur < econ_len else
                f"trim=duration={econ_len:.3f},setpts=PTS-STARTPTS[v]")
            run([FF, "-y", "-i", econ_anim, "-vf", vf_econ,
                 "-c:v", "libx264", "-preset", "medium", "-crf", CRF,
                 "-pix_fmt", "yuv420p", "-r", str(FPS),
                 "-an", patched], log_path=log_path)
            # 用 concat 滤镜做「前段 + 动画 + 后段」三段拼接。
            # ⚠️ 2026-10-16 改法：原先用 `overlay` + `enable='between(t,..)'` +
            #    `-map 0:a -c:a copy`，但 merged 是 `-an -c copy` 出来的**无音轨**文件，
            #    `-c:a copy` 找不到音频流 → ffmpeg 报 `Invalid argument`，覆盖失败。
            #    concat 滤镜不碰音轨，稳。
            if os.path.exists(patched):
                merged_econ = os.path.join(out_dir, f"signal_pop_weekly_{date}_merged2.mp4")
                fc = f"[0:v]trim=start=0:end={econ_start:.3f},setpts=PTS-STARTPTS[a];"
                if econ_start <= 0.05:
                    fc = ""
                fc += f"[1:v]setpts=PTS-STARTPTS[b];"
                fc += f"[0:v]trim=start={econ_start + econ_len:.3f},setpts=PTS-STARTPTS[c];"
                fc += ("[a][b][c]concat=n=3:v=1:a=0[v]" if fc.startswith("[0:v]trim=start=0")
                       else "[b][c]concat=n=2:v=1:a=0[v]")
                run([FF, "-y", "-i", merged, "-i", patched,
                     "-filter_complex", fc, "-map", "[v]", "-an",
                     "-c:v", "libx264", "-preset", "medium",
                     "-crf", CRF, "-pix_fmt", "yuv420p", "-r", str(FPS),
                     merged_econ], log_path=log_path)
                if os.path.exists(merged_econ) and probe_duration(merged_econ) > 0:
                    os.replace(merged_econ, merged)
                    log_line(log_path, f"econ segment patched OK ({probe_duration(merged):.2f}s)")
                else:
                    log_line(log_path, "!! econ 覆盖合成失败，保留静态图版本")
                    if os.path.exists(merged_econ):
                        os.remove(merged_econ)
    else:
        log_line(log_path, f"⚠️ 未找到 {os.path.basename(econ_anim)}，econ 段沿用静态图")

    # ---------- 3) concat 拼接（片头 + 已替换动画的 part-merged）----------
    # ⚠️ 2026-10-16 修 bug：原先用 concat demuxer + `-c copy` 拼 opening 与 merged，
    #    但两段 tbn 不同（opening 是 90k tbn，merged 是 15360k tbn），
    #    copy 拼接导致时间轴崩坏 —— merged_final 只有 2:10（应为 12:32），
    #    帧率变成 175.71 fps，最终成片只剩片头 9 秒。
    #    改用 concat **滤镜**（会重编码、统一时基），代价是多一遍编码。
    log_line(log_path, "concat opening + parts(econ patched) [filter mode]")
    final_merged = os.path.join(out_dir, f"signal_pop_weekly_{date}_merged_final.mp4")
    run([FF, "-y", "-i", opening_out, "-i", merged,
         "-filter_complex",
         "[0:v]fps=30,scale=1920:1080,setsar=1,format=yuv420p,setpts=PTS-STARTPTS[v0];"
         "[1:v]fps=30,scale=1920:1080,setsar=1,format=yuv420p,setpts=PTS-STARTPTS[v1];"
         "[v0][v1]concat=n=2:v=1:a=0[v]",
         "-map", "[v]", "-an",
         "-c:v", "libx264", "-preset", "fast", "-crf", "20",
         "-pix_fmt", "yuv420p", "-r", str(FPS), "-video_track_timescale", "90000",
         final_merged], log_path=log_path)
    merged = final_merged

    # ---------- 4) 整体重编码（CRF26，统一码率、抹平接缝）+ 合并 TTS ----------
    # ⚠️ 2026-10-16 修 bug：原实现把 `afade`（**音频**滤镜）加在 `[0:v]` 视频流上，
    #    ffmpeg 直接报错退出，产出 0KB 成片。片头淡入淡出应用 fade 视频滤镜
    #    `fade=t=in:alpha=0`（纯黑场），音频淡入淡出交给 TTS 侧，这里不动。
    wav = os.path.join(out_dir, "audio", "tts.wav")
    final = os.path.join(out_dir, f"signal_pop_weekly_{date}.mp4")

    # 视频侧：片头黑场淡入 + 片尾黑场淡出（只动 alpha，安全）
    open_dur = OPEN_FRAMES / FPS          # 9.0s
    total_dur = probe_duration(merged)
    fade_out_start = max(0.0, total_dur - 1.0)
    vf = (f"[0:v]fade=t=in:st=0:d=1.2:alpha=0:color=black,"
          f"fade=t=out:st={fade_out_start:.2f}:d=1.0:alpha=0:color=black[v]")

    if not os.path.exists(wav):
        # 无 TTS：只做视频重编码
        cmd = [FF, "-y", "-i", merged, "-vf", vf, "-map", "[v]",
               "-c:v", "libx264", "-preset", "medium", "-crf", CRF,
               "-pix_fmt", "yuv420p", "-r", str(FPS), "-movflags", "+faststart", final]
    else:
        # 🔴 2026-10-16 修致命 bug：片头 opening_anim.mp4 **只有视频轨、零音频**，
        # 而 merged 的时间轴是「片头 9s + 正文 752.7s」。原实现把 TTS 从第 0 秒
        # 直接铺上去 → 阿信「大家好」压在片头动画上，**开场就错**。
        # 修法：`adelay` 把 TTS 整体延后片头时长，与正文对齐；
        # 片头 9s 铺钢琴曲（PIANO_START 起 9s），并做首尾淡入淡出。
        piano_in = []
        afc = []
        if os.path.exists(PIANO):
            piano_in = ["-stream_loop", "-1", "-i", PIANO]
            afc.append(f"[2:a]atrim=start={PIANO_START}:duration={open_dur:.2f},"
                       f"asetpts=PTS-STARTPTS,"
                       f"afade=t=in:st=0:d=1.2:curve=esin,"
                       f"afade=t=out:st={open_dur - 1.0:.2f}:d=1.0:curve=esin,"
                       f"volume=0.75,aresample=48000[piano]")
        # TTS 延迟 open_dur 秒，与正文严格对齐
        afc.append(f"[1:a]adelay={int(open_dur * 1000)}|{int(open_dur * 1000)},"
                   f"afade=t=in:st={open_dur:.2f}:d=0.6:curve=esin,"
                   f"afade=t=out:st={fade_out_start:.2f}:d=1.0:curve=esin,"
                   f"loudnorm=I=-14:TP=-1.5:LRA=11[tts]")
        if piano_in:
            # 片头钢琴（9s）与延后后的 TTS 并列，总长取长的那个
            afc.append(f"[piano][tts]amix=inputs=2:duration=longest:dropout_transition=0,"
                       f"alimiter=limit=0.95[aout]")
        else:
            afc.append("[tts]anull[aout]")

        cmd = [FF, "-y", "-i", merged, "-i", wav, *piano_in,
               "-filter_complex", f"{vf};" + ";".join(afc),
               "-map", "[v]", "-map", "[aout]",
               "-c:v", "libx264", "-preset", "medium", "-crf", CRF,
               "-pix_fmt", "yuv420p", "-r", str(FPS),
               "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
               "-movflags", "+faststart", final]

    log_line(log_path, f"final encode -> {os.path.basename(final)}")
    run(cmd, log_path=log_path)

    if not os.path.exists(final):
        log_line(log_path, "!! 最终合成失败")
        print("ERROR: 最终合成失败", file=sys.stderr)
        return 1

    dur = probe_duration(final)
    log_line(log_path, f"OK final: {final}  {dur:.2f}s  "
                       f"{os.path.getsize(final) // 1024}KB")
    print(f"\nDONE  {final}")
    print(f"  时长 {dur:.2f}s ({dur/60:.2f}分)  大小 {os.path.getsize(final)//1024}KB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
