import os
#!/usr/bin/env python3
"""Signal Pop — Remotion 周末版数据导出（含配图轮换 + 突发现场视频窗）

消费 build_weekly_dialogue 产出的 dialogue_segments.json（含正确 bg 字段）
+ audio/tts_segments.json（时长）+ talk_segments.json（音色），
输出 remotion_poc/src/weekly_segs.json（Remotion 消费格式）。

突发现场视频：扫描 output/weekly/<日>/videos/ 下首个 .mp4，归一化为
breaking_footage.mp4 复制到 remotion_poc/public，并用 ffprobe 探测真实时长
写入每段的 videoDur 字段；WeeklyTalk.tsx 据此把视频窗锚定到首个突发段起点
播一次、末尾淡出消失。无视频文件则静默跳过。

用法: python tools/export_weekly_remotion.py [制作日YYYYMMDD]
"""

import sys, os, json, shutil, subprocess

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_BIN = os.path.join(PROJECT_ROOT, "bin", "ffmpeg-9.0.1-essentials_build", "bin")
FFPROBE = os.path.join(_BIN, "ffprobe.exe")
FFMPEG = os.path.join(_BIN, "ffmpeg.exe")
FRAME_FPS = 30
FRAME_DIR = "breaking_frames"


def probe_duration(path):
    """返回视频真实时长（秒），失败返回 0.0"""
    try:
        out = subprocess.run(
            [
                FFPROBE,
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                path,
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        return float(out.stdout.strip())
    except Exception as e:
        print(f"⚠️ ffprobe 探测时长失败: {e}")
        return 0.0


def probe_dimensions(path):
    """返回视频 (width, height)，失败返回 (0, 0)"""
    try:
        out = subprocess.run(
            [
                FFPROBE,
                "-v",
                "error",
                "-select_streams",
                "v:0",
                "-show_entries",
                "stream=width,height",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                path,
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        lines = [x.strip() for x in out.stdout.strip().splitlines() if x.strip()]
        return int(lines[0]), int(lines[1])
    except Exception as e:
        print(f"⚠️ ffprobe 探测宽高失败: {e}")
        return 0, 0


def build_stable_frames(video_src, pub, trim=None):
    """把突发现场短视频预处理成「确定性 JPEG 帧序列」。

    🔴 2026-11-05 修「画中画严重震动」：源素材是带硬转场 + 末尾黑帧 + B 帧的
    竖屏短视频，Remotion 的 <Video loop> 在 headless Chromium 里逐帧 seek 时
    帧定位不稳定，表现为画面上下抖动 / 循环点闪黑。改为把画面抽成静态 JPEG
    序列，由 WeeklyTalk 用 <Img> 按帧号显示 —— 每帧完全确定，零解码抖动。

    预处理：按 videoTrim 截取稳定段（避开转场与黑帧）→ deshake 去抖 →
    中心裁切 4% 消除边缘黑块 → 统一 30fps → 缩放到画中画窗 372x660。
    返回 (帧数, fps)；失败返回 (0, FRAME_FPS) 由调用方回退 <Video>。
    """
    dst = os.path.join(pub, FRAME_DIR)
    os.makedirs(dst, exist_ok=True)
    for f in os.listdir(dst):
        if f.lower().endswith((".jpg", ".jpeg", ".png")):
            try:
                os.remove(os.path.join(dst, f))
            except OSError:
                pass

    dur = probe_duration(video_src)
    if trim and len(trim) == 2:
        t0, t1 = float(trim[0]), float(trim[1])
    else:
        t0 = min(0.6, dur * 0.12)
        t1 = max(t0 + 1.2, dur - min(0.5, dur * 0.10))
    t0 = max(0.0, min(t0, max(0.0, dur - 0.5)))
    t1 = max(t0 + 0.6, min(t1, dur))

    vf = (f"trim=start={t0:.3f}:end={t1:.3f},setpts=PTS-STARTPTS,"
          f"deshake=rx=32:ry=32:edge=clamp,"
          f"crop=iw*0.94:ih*0.94,scale=372:660:flags=lanczos,"
          f"fps={FRAME_FPS}")
    out_pattern = os.path.join(dst, "f%04d.jpg")
    r = subprocess.run(
        [FFMPEG, "-y", "-v", "error", "-i", video_src, "-vf", vf,
         "-q:v", "3", out_pattern],
        capture_output=True, text=True, timeout=300)
    n = len([f for f in os.listdir(dst) if f.lower().endswith(".jpg")])
    if n == 0:
        print(f"⚠️ 帧序列生成失败，回退 <Video>: {r.stderr[-400:]}")
        return 0, FRAME_FPS
    print(f"✅ 画中画稳定帧序列: {n} 帧 / {FRAME_FPS}fps "
          f"(源 {dur:.2f}s 取 {t0:.2f}~{t1:.2f}s, 去抖+裁边+缩放)")
    return n, FRAME_FPS


def main(date):
    out_dir = os.path.join(PROJECT_ROOT, "output", "weekly", date)
    dlg_path = os.path.join(out_dir, "dialogue_segments.json")
    talk_path = os.path.join(out_dir, "talk_segments.json")
    if not os.path.exists(talk_path):  # gen_dual_tts 将其写到 audio/ 子目录
        alt = os.path.join(out_dir, "audio", "talk_segments.json")
        if os.path.exists(alt):
            talk_path = alt
    dur_path = os.path.join(out_dir, "audio", "tts_segments.json")
    for p in (dlg_path, talk_path, dur_path):
        if not os.path.exists(p):
            print(f"❌ 数据不存在: {p}")
            sys.exit(1)

    dlg = json.load(open(dlg_path, encoding="utf-8"))
    talk = json.load(open(talk_path, encoding="utf-8"))
    durs = json.load(open(dur_path, encoding="utf-8"))
    if not (len(dlg) == len(talk) == len(durs)):
        print(f"❌ 段数不匹配: dlg={len(dlg)} talk={len(talk)} durs={len(durs)}")
        sys.exit(1)

    segs = []
    n = len(dlg)
    opening_bg_path = os.path.join(out_dir, "images", "opening_bg.jpg")
    has_opening_bg = os.path.exists(opening_bg_path)

    # 每期精选网址（片尾「本期精选网址」条 + 发布文案复用）：
    # 优先级：从 parsed_news.json 的 pick 项正文中自动提取 URL
    # > argv[2] 显式传入 > output/weekly/<日>/pick_url.txt > 默认兜底。
    pick_url = None

    # 1) 优先从 parsed_news.json 的 pick 条目正文提取真实网址
    try:
        pn_data = json.load(open(os.path.join(out_dir, "parsed_news.json"), encoding="utf-8"))
        pick_it = next((it for it in pn_data if it.get("type") == "pick"), None)
        if pick_it and pick_it.get("body"):
            import re
            m = re.search(r"(https?://[^\s，。、；]+|[a-zA-Z0-9][-a-zA-Z0-9]*\.(?:net|com|org|cn|io|me|cc|tv|xyz)[^\s，。、；]*)", pick_it["body"])
            if m:
                pick_url = m.group(1).rstrip("，。、；")
                # 规范化：去除协议头便于胶囊卡美观展示（如 https://fmhy.net -> fmhy.net）
                print(f"✅ 从 parsed_news.json pick 提取到本期精选网址: {pick_url}")
    except Exception as e:
        print(f"⚠️ 解析 pick_url 失败: {e}")

    # 2) 命令行参数显式传入
    if not pick_url and len(sys.argv) > 2 and sys.argv[2].strip():
        pick_url = sys.argv[2].strip()

    # 3) pick_url.txt 文件
    pick_txt = os.path.join(out_dir, "pick_url.txt")
    if not pick_url and os.path.exists(pick_txt):
        try:
            pick_url = open(pick_txt, encoding="utf-8").read().strip()
        except Exception:
            pass

    # 4) 兜底
    if not pick_url:
        pick_url = "fmhy.net"

    # 同步写入/更新 pick_url.txt，供后续发布脚本或外部工具复用
    try:
        with open(pick_txt, "w", encoding="utf-8") as pf:
            pf.write(pick_url)
    except Exception:
        pass

    print(f"ℹ️ 本期精选网址最终锁定: {pick_url}")

    for i in range(n):
        d = dlg[i]
        bg = d.get("bg") or ""
        # 开场问候段 bg 为空时，若存在 opening_bg.jpg 则挂上，避免黑屏开场
        if not bg and has_opening_bg and d["speaker"] in ("阿信", "小蓝"):
            bg = "opening_bg.jpg"
        segs.append(
            {
                "speaker": d["speaker"],
                "voice": talk[i].get("voice", ""),
                "text": d["text"],
                "dur": durs[i]["dur"],
                "bg": bg,
                "video": "",
                "videoDur": 0,
                "videoW": 0,
                "videoH": 0,
                "videoClipDur": 0,
                "videoFrames": 0,
                "videoFps": 0,
                "videoFrameDir": "",
                "isBreaking": bg == "breaking.jpg",
                "isInteractive": bg == "interactive.jpg",
                "cta": (i == n - 1),  # 末段触发结尾「一键三连」CTA
                "pickUrl": pick_url,  # 片尾每期精选网址（逐期可配）
                # ② 数字滚动卡 / ③ 下周看点日程卡（build_weekly_dialogue 生成，
                #    Remotion 端仅在非空时渲染对应组件）
                "data": d.get("data") or [],
                "agenda": d.get("agenda") or [],
            }
        )

    # public 目录先建好（视频与配图都要用）
    pub = os.path.join(PROJECT_ROOT, "remotion_poc", "public")
    os.makedirs(pub, exist_ok=True)

    # 特别报道现场视频（用户提供真实素材）：规范目录 output/video/（见约定）
    # 解析优先级：
    #   1) parsed_news.json 中 breaking 项的显式 "video" 字段（绝对路径或文件名）
    #   2) 规范目录 output/video/（按制作日约定文件名或首个 mp4）
    #   3) 回退 output/weekly/<日>/videos/
    # → 归一化为 breaking_footage.mp4 → ffprobe 时长 → 挂到突发段
    # 视频窗由 WeeklyTalk.tsx 条件渲染：仅在突发段且有时长时显示，播一次末尾淡出。
    VIDEO_CANON = os.path.join(PROJECT_ROOT, "output", "video")
    VIDEO_DIR = os.path.join(out_dir, "videos")
    video_src = None

    # 1) parsed_news.json breaking 项显式 video 字段
    try:
        pn = json.load(open(os.path.join(out_dir, "parsed_news.json"), encoding="utf-8"))
        brk = next((it for it in pn if it.get("type") == "breaking"), None)
        if brk and brk.get("video"):
            cand = brk["video"]
            if os.path.isabs(cand) and os.path.exists(cand):
                video_src = cand
            else:
                for base in (VIDEO_CANON, VIDEO_DIR):
                    p = os.path.join(base, cand)
                    if os.path.exists(p):
                        video_src = p
                        break
    except Exception as e:
        print(f"⚠️ 读取 parsed_news.json 视频字段失败: {e}")

    # 2) 规范目录 output/video/（约定文件名优先，再兜底首个 mp4）
    if not video_src and os.path.isdir(VIDEO_CANON):
        prefs = []
        if len(sys.argv) > 2:
            prefs.append(sys.argv[2])
        prefs += [f"{date}_breaking.mp4", "iphone-duo.mp4", "breaking_footage.mp4"]
        for name in prefs:
            p = os.path.join(VIDEO_CANON, name)
            if os.path.exists(p):
                video_src = p
                break
        if not video_src:
            mp4s = sorted(f for f in os.listdir(VIDEO_CANON) if f.lower().endswith(".mp4"))
            if mp4s:
                video_src = os.path.join(VIDEO_CANON, mp4s[0])

    # 3) 回退 output/weekly/<日>/videos/
    if not video_src and os.path.isdir(VIDEO_DIR):
        prefs = []
        if len(sys.argv) > 2:
            prefs.append(sys.argv[2])
        prefs += ["现场视频2.mp4", "breaking_footage.mp4"]
        for name in prefs:
            cand = os.path.join(VIDEO_DIR, name)
            if os.path.exists(cand):
                video_src = cand
                break
        if not video_src:
            mp4s = sorted(f for f in os.listdir(VIDEO_DIR) if f.lower().endswith(".mp4"))
            if mp4s:
                video_src = os.path.join(VIDEO_DIR, mp4s[0])

    if video_src:
        dst_name = "breaking_footage.mp4"
        shutil.copy(video_src, os.path.join(pub, dst_name))
        vdur = probe_duration(video_src)
        vw, vh = probe_dimensions(video_src)
        # 循环次数：稳定段通常只有 2~5s，播一遍在 40~60s 的突发段里太短；
        # videoLoops / videoTrim 由 parsed_news.json breaking 项配置。
        try:
            pn2 = json.load(open(os.path.join(out_dir, "parsed_news.json"), encoding="utf-8"))
            brk2 = next((it for it in pn2 if it.get("type") == "breaking"), None)
            loops = max(1, int(brk2.get("videoLoops", 1))) if brk2 else 1
            trim = brk2.get("videoTrim") if brk2 else None
        except Exception:
            loops, trim = 1, None

        # 2026-11-05：优先输出确定性帧序列（<Img>），失败才回退 <Video>
        n_frames, frame_fps = build_stable_frames(video_src, pub, trim)
        clip_dur = round(n_frames / frame_fps, 3) if n_frames else round(vdur, 3)
        vdur_total = round(clip_dur * loops, 3)
        for s in segs:
            if s["isBreaking"]:
                s["video"] = dst_name
                s["videoDur"] = vdur_total
                s["videoW"] = vw
                s["videoH"] = vh
                s["videoClipDur"] = clip_dur
                s["videoFrames"] = n_frames
                s["videoFps"] = frame_fps
                s["videoFrameDir"] = FRAME_DIR
        orient = "竖屏" if vh > vw else "横屏"
        print(
            f"✅ 特别报道视频窗已挂载: {os.path.basename(video_src)} → {dst_name} "
            f"（{vw}x{vh} {orient}, 单遍 {clip_dur:.2f}s × {loops} = {vdur_total:.2f}s, "
            f"渲染方式={'帧序列 <Img>' if n_frames else '视频 <Video>'}）"
        )
    else:
        print(f"ℹ️ 未找到特别报道视频（output/video/ 与 {VIDEO_DIR}/ 均无 mp4），突发段不挂视频窗。")

    dst = os.path.join(PROJECT_ROOT, "remotion_poc", "src", "weekly_segs.json")
    with open(dst, "w", encoding="utf-8") as f:
        json.dump(segs, f, ensure_ascii=False, indent=1)
    total = sum(s["dur"] for s in segs)
    uniq_bg = sorted(set(s["bg"] for s in segs if s["bg"]))
    print(f"✅ 导出 {len(segs)} 段 / {total:.1f}s -> {dst}")
    print(f"   配图 {len(uniq_bg)} 种: {uniq_bg}")

    # 复制素材到 remotion_poc/public
    # 2026-11-05：配图版本可用环境变量切换（默认 images = 带标原图；
    # images_nomark = 底部裁切无标版）。argv[2] 已被 pick_url 占用，故用环境变量。
    img_sub = os.environ.get("SIGNAL_POP_IMG_SUBDIR", "images")
    imgs = os.path.join(out_dir, img_sub)
    print(f"   配图版本: {img_sub}")
    srcs = [os.path.join(imgs, "anchor_axin.jpg"), os.path.join(imgs, "anchor_xiaolan.jpg")]
    srcs += [os.path.join(imgs, b) for b in uniq_bg]
    copied = []
    for s in srcs:
        if os.path.exists(s):
            shutil.copy(s, os.path.join(pub, os.path.basename(s)))
            copied.append(os.path.basename(s))
    print(f"✅ 素材已复制({len(copied)}): {copied}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "20260821")
