# -*- coding: utf-8 -*-
"""
周末版·播报词标题句静音切割（20260904 期应急）
背景：豆包配额耗尽无法重录，改用静音检测剪掉每条阿信新闻段里
     「接着聊X。{标题}。{内容}」中的 {标题} 句（内容首句已复述标题）。
方法：silencedetect 找句间停顿 -> 第1个停顿=前缀|标题边界，
     第2个停顿=标题|内容边界；用 字数/语速 交叉校验，不符则跳过。
"""
import json, os, re, subprocess, sys

ROOT = "E:/projects/signal_pop"
DATE = "20260904"
TMP = f"{ROOT}/output/weekly/{DATE}/audio/_tmp"
ORIG = os.path.join(TMP, "_orig")
FF = f"{ROOT}/bin/ffmpeg-9.0.1-essentials_build/bin/ffmpeg.exe"
FP = f"{ROOT}/bin/ffmpeg-9.0.1-essentials_build/bin/ffprobe.exe"
RATE = 5.5  # 校验用语速 字/秒（宽容 ±50%）

os.makedirs(ORIG, exist_ok=True)
segs = json.load(open(f"{ROOT}/remotion_poc/src/weekly_segs.json", encoding="utf-8"))


def probe_dur(path):
    r = subprocess.run([FP, "-v", "error", "-show_entries", "format=duration",
                        "-of", "default=noprint_wrappers=1:nokey=1", path],
                       capture_output=True, text=True)
    return float(r.stdout.strip())


def silences(path):
    r = subprocess.run([FF, "-i", path, "-af", "silencedetect=noise=-35dB:d=0.12",
                        "-f", "null", "-"], capture_output=True, text=True)
    txt = r.stderr
    starts = [float(x) for x in re.findall(r"silence_start: ([0-9.]+)", txt)]
    ends = [float(x) for x in re.findall(r"silence_end: ([0-9.]+)", txt)]
    return list(zip(starts, ends[: len(starts)]))


def cut(in_path, out_path, m1, m2):
    af = ("[0:a]asplit=2[a1][a2];"
          f"[a1]atrim=start=0:end={m1:.3f},asetpts=PTS-STARTPTS[p1];"
          f"[a2]atrim=start={m2:.3f},asetpts=PTS-STARTPTS[p2];"
          "[p1][p2]concat=n=2:v=0:a=1[out]")
    r = subprocess.run([FF, "-y", "-v", "error", "-i", in_path,
                        "-filter_complex", af, "-map", "[out]",
                        "-c:a", "libmp3lame", "-q:a", "2", out_path],
                       capture_output=True, text=True)
    return r.returncode == 0


plan = []
for i, s in enumerate(segs):
    bg = s.get("bg") or ""
    if not re.fullmatch(r"news_(0[2-9]|1[0-4])\.jpg", bg):
        continue
    if s["speaker"] != "阿信" or s.get("cta") or s.get("isInteractive"):
        continue
    # 只处理每条新闻的第一段（长播报段，文本含 标题+内容）
    txt = s["text"]
    parts = txt.split("。")
    if len(parts) < 3:
        print(f"[skip] seg{i} {bg} 文本结构异常")
        continue
    prefix, title = parts[0] + "。", parts[1]
    if not prefix.startswith("接着聊"):
        print(f"[skip] seg{i} {bg} 前缀异常: {prefix}")
        continue
    plan.append({"idx": i, "bg": bg, "title": title, "mp3": f"{TMP}/_s{i:03d}.mp3"})

print(f"共 {len(plan)} 段待处理\n")
ok, fail = 0, 0
for p in plan:
    mp3 = p["mp3"]
    if not os.path.exists(mp3):
        print(f"[FAIL] seg{p['idx']} {p['bg']} 无音频")
        fail += 1
        continue
    d0 = probe_dur(mp3)
    allsil = silences(mp3)
    sil = [x for x in allsil if x[1] - x[0] >= 0.12]
    # 句首静音（start≈0）
    lead_end = 0.0
    if sil and sil[0][0] < 0.3:
        lead_end = sil[0][1]
        sil = sil[1:]
    if len(sil) < 2:
        print(f"[FAIL] seg{p['idx']} {p['bg']} 停顿不足({len(sil)})")
        fail += 1
        continue
    # 在停顿对 (i,j) 中选「前缀跨度+标题跨度」与字数语速最吻合的组合
    # （TTS 在数字/引号后有微停顿，标题内可能含停顿，需跨多个停顿取边界）
    pre_exp, tit_exp = len(prefix) / 6.0, len(p["title"]) / RATE
    best, best_score = None, 1e9
    for i in range(min(4, len(sil) - 1)):
        pre_span = sil[i][0] - lead_end
        if not (0.3 * pre_exp <= pre_span <= 2.0 * pre_exp):
            continue
        for j in range(i + 1, min(i + 5, len(sil))):
            tit_span = sil[j][0] - sil[i][1]
            if not (0.5 * tit_exp <= tit_span <= 2.0 * tit_exp):
                continue
            score = abs(pre_span - pre_exp) / pre_exp + abs(tit_span - tit_exp) / tit_exp
            if score < best_score:
                best, best_score = (sil[i], sil[j]), score
    if best is None:
        print(f"[FAIL] seg{p['idx']} {p['bg']} 无吻合停顿对 (标题期望{tit_exp:.2f}s)")
        fail += 1
        continue
    (a1, b1), (a2, b2) = best
    m1, m2 = (a1 + b1) / 2, (a2 + b2) / 2
    bak = os.path.join(ORIG, f"_s{p['idx']:03d}.mp3")
    if not os.path.exists(bak):
        import shutil
        shutil.copy2(mp3, bak)
    tmp_out = mp3 + ".cut.mp3"
    if not cut(bak if os.path.exists(bak) else mp3, tmp_out, m1, m2):
        print(f"[FAIL] seg{p['idx']} {p['bg']} ffmpeg 切割失败")
        fail += 1
        continue
    d1 = probe_dur(tmp_out)
    os.replace(tmp_out, mp3)
    p.update(old=d0, new=d1, delta=round(d0 - d1, 2))
    print(f"[OK] seg{p['idx']:2d} {p['bg']} {p['title'][:22]} | {d0:.2f}s -> {d1:.2f}s (-{d0-d1:.2f}s)")
    ok += 1

json.dump(plan, open(f"{TMP}/_cut_plan.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"\n完成: OK={ok} FAIL={fail} (备份在 {ORIG})")
sys.exit(0 if fail == 0 else 1)
