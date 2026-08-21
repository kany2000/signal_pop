#!/usr/bin/env python3
"""Signal Pop — 周末版音频后处理：阿信段音量 +10%

按 talk_segments.json 的 speaker 标记切分 tts.wav，
对阿信段乘以 1.1 增益，再重拼为新 tts.wav。
PoC 阶段使用；本期新生成时 gen_dual_tts.py 已自带 +10%。

用法: python tools/boost_axin_volume.py [制作日YYYYMMDD]
"""
import sys, os, json, subprocess, wave, struct, shutil

PROJECT_ROOT = "E:/projects/signal_pop"
FFMPEG = "E:/projects/signal_pop/bin/ffmpeg-9.0.1-essentials_build/bin/ffmpeg.exe"
GAIN = 1.30  # 阿信 +30%（2026-08-21 用户反馈；接近小蓝音量）


def main(date):
    out_dir = os.path.join(PROJECT_ROOT, "output", "weekly", date)
    talk_path = os.path.join(out_dir, "talk_segments.json")
    dur_path = os.path.join(out_dir, "audio", "tts_segments.json")
    audio_path = os.path.join(out_dir, "audio", "tts.wav")
    if not os.path.exists(audio_path):
        print(f"❌ 不存在: {audio_path}"); sys.exit(1)

    talk = json.load(open(talk_path, encoding="utf-8"))
    durs = json.load(open(dur_path, encoding="utf-8"))

    # 读全部 PCM
    w = wave.open(audio_path, "rb")
    rate = w.getframerate()
    raw = w.readframes(w.getnframes())
    w.close()
    samples = list(struct.unpack(f"<{len(raw)//2}h", raw))
    print(f"加载音频: {len(samples)} 采样 @ {rate}Hz, {len(samples)/rate:.2f}s")

    # 按段切，axin 段 ×1.1
    out_pcm = []
    pos = 0
    boosted = 0
    for i, (t, d) in enumerate(zip(talk, durs)):
        n = int(d["dur"] * rate)
        seg = samples[pos:pos + n]
        if t["speaker"] == "阿信":
            seg = [max(-32768, min(32767, int(s * GAIN))) for s in seg]
            boosted += 1
        out_pcm.extend(seg)
        pos += n
    if pos != len(samples):
        print(f"⚠️ 段累加 {pos} != 音频 {len(samples)}，可能有空段被跳过")

    # 备份原音频并写新音频
    bak = audio_path + ".bak"
    if not os.path.exists(bak):
        shutil.copy(audio_path, bak)
    new = audio_path + ".new"
    with wave.open(new, "wb") as o:
        o.setnchannels(1); o.setsampwidth(2); o.setframerate(rate)
        o.writeframes(b"".join(struct.pack("<h", s) for s in out_pcm))
    os.replace(new, audio_path)
    print(f"✅ 阿信段 × {len(talk)} 段中 {boosted} 段已 +10% 提升, 备份: {bak}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "20260814")
