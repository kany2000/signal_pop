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

PROJECT_ROOT = "E:/projects/signal_pop"
FFPROBE = os.path.join(
    PROJECT_ROOT, "bin", "ffmpeg-9.0.1-essentials_build", "bin", "ffprobe.exe"
)


def probe_duration(path):
    """返回视频真实时长（秒），失败返回 0.0"""
    try:
        out = subprocess.run(
            [FFPROBE, "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", path],
            capture_output=True, text=True, timeout=30,
        )
        return float(out.stdout.strip())
    except Exception as e:
        print(f"⚠️ ffprobe 探测时长失败: {e}")
        return 0.0


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
            print(f"❌ 数据不存在: {p}"); sys.exit(1)

    dlg = json.load(open(dlg_path, encoding="utf-8"))
    talk = json.load(open(talk_path, encoding="utf-8"))
    durs = json.load(open(dur_path, encoding="utf-8"))
    if not (len(dlg) == len(talk) == len(durs)):
        print(f"❌ 段数不匹配: dlg={len(dlg)} talk={len(talk)} durs={len(durs)}"); sys.exit(1)

    segs = []
    n = len(dlg)
    opening_bg_path = os.path.join(out_dir, "images", "opening_bg.jpg")
    has_opening_bg = os.path.exists(opening_bg_path)
    for i in range(n):
        d = dlg[i]
        bg = d.get("bg") or ""
        # 开场问候段 bg 为空时，若存在 opening_bg.jpg 则挂上，避免黑屏开场
        if not bg and has_opening_bg and d["speaker"] in ("阿信", "小蓝"):
            bg = "opening_bg.jpg"
        segs.append({
            "speaker": d["speaker"],
            "voice": talk[i].get("voice", ""),
            "text": d["text"],
            "dur": durs[i]["dur"],
            "bg": bg,
            "video": "",
            "videoDur": 0,
            "isBreaking": bg == "breaking.jpg",
            "isInteractive": bg == "interactive.jpg",
            "cta": (i == n - 1),  # 末段触发结尾「一键三连」CTA
        })

    # public 目录先建好（视频与配图都要用）
    pub = os.path.join(PROJECT_ROOT, "remotion_poc", "public")
    os.makedirs(pub, exist_ok=True)

    # 突发消息现场视频（用户提供真实素材）：优先用用户指定/约定文件名
    # → 归一化为 breaking_footage.mp4 → ffprobe 时长 → 挂到突发段
    # 视频窗由 WeeklyTalk.tsx 条件渲染：仅在突发段且有时长时显示，播一次末尾淡出。
    VIDEO_DIR = os.path.join(out_dir, "videos")
    video_src = None
    if os.path.isdir(VIDEO_DIR):
        prefs = []
        if len(sys.argv) > 2:  # 可选第 2 参数指定视频文件名
            prefs.append(sys.argv[2])
        prefs += ["现场视频2.mp4", "breaking_footage.mp4"]
        for name in prefs:
            cand = os.path.join(VIDEO_DIR, name)
            if os.path.exists(cand):
                video_src = cand
                break
        if not video_src:  # 兜底：目录里仅一个 mp4 时直接用
            mp4s = sorted(f for f in os.listdir(VIDEO_DIR) if f.lower().endswith(".mp4"))
            if mp4s:
                video_src = os.path.join(VIDEO_DIR, mp4s[0])
    if video_src:
        dst_name = "breaking_footage.mp4"
        shutil.copy(video_src, os.path.join(pub, dst_name))
        vdur = probe_duration(video_src)
        for s in segs:
            if s["isBreaking"]:
                s["video"] = dst_name
                s["videoDur"] = round(vdur, 3)
        print(f"✅ 突发视频窗已挂载: {os.path.basename(video_src)} → {dst_name} "
              f"（{os.path.getsize(video_src)} bytes, 时长 {vdur:.2f}s）")
    else:
        print(f"ℹ️ 未找到 {VIDEO_DIR}/*.mp4，突发段不挂视频窗。")

    dst = os.path.join(PROJECT_ROOT, "remotion_poc", "src", "weekly_segs.json")
    with open(dst, "w", encoding="utf-8") as f:
        json.dump(segs, f, ensure_ascii=False, indent=1)
    total = sum(s["dur"] for s in segs)
    uniq_bg = sorted(set(s["bg"] for s in segs if s["bg"]))
    print(f"✅ 导出 {len(segs)} 段 / {total:.1f}s -> {dst}")
    print(f"   配图 {len(uniq_bg)} 种: {uniq_bg}")

    # 复制素材到 remotion_poc/public
    imgs = os.path.join(out_dir, "images")
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
