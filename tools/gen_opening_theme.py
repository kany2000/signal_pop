#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成 9 秒「新闻片头」器乐配乐（离线合成、免版权、零外部素材）

背景：render_weekly_py.py 原写死 PIANO = output/mp3/Romeo - Winds of Hope ...mp3，
该文件从未入库 → 片头 9s 只有 -91dB 静音。历史成片前 9s 的「有声音」经互相关
验证是各期不同的 TTS 人声（旧版口播压片头的 bug），不是配乐，不可复用。

本脚本用纯标准库（wave/struct/math）做加法合成：
  * 4 个和弦的进行（Dm9 → Bbmaj7 → Fmaj7 → Csus2），钢琴式琶音 + 泛音
  * 低音 pad、每拍 kick、八分 hihat
  * 开场 whoosh 上扫、首尾淡入淡出
输出 48kHz / 16bit / 单声道 WAV，落到 output/weekly/shared/（清理门禁白名单）。

用法: python tools/gen_opening_theme.py [输出wav]
若日后用户提供正式 BGM，只需在 render_weekly_py.py 设置环境变量
SIGNAL_POP_OPENING_BGM 指向该文件即可，无需改代码。
"""
import math
import os
import struct
import sys
import wave

SR = 48000
DUR = 9.0
N = int(SR * DUR)


def midi(n):
    return 440.0 * (2.0 ** ((n - 69) / 12.0))


# Dm9 / Bbmaj7 / Fmaj7 / Csus2 —— 明亮但克制的新闻片头色彩
CHORDS = [
    [50, 53, 57, 60, 64],   # D3 F3 A3 C4 E4
    [46, 50, 53, 57],       # Bb2 D3 F3 A3
    [41, 45, 48, 52],       # F2 A2 C3 E3
    [48, 50, 55, 60],       # C3 D3 G3 C4
]
CHORD_DUR = DUR / len(CHORDS)
BEAT = CHORD_DUR / 8.0


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    default_out = os.path.join(root, "output", "weekly", "shared", "opening_theme.wav")
    out = sys.argv[1] if len(sys.argv) > 1 else default_out
    os.makedirs(os.path.dirname(out), exist_ok=True)

    buf = [0.0] * N

    def add(start, dur, fn, gain):
        i0 = int(start * SR)
        n = min(int(dur * SR), N - i0)
        if n <= 0:
            return
        for i in range(n):
            t = i / SR
            buf[i0 + i] += gain * fn(t, i)

    # 1) 钢琴式琶音：每个和弦 8 个八分音符，带泛音与快速起音/长衰减
    for ci, chord in enumerate(CHORDS):
        c_start = ci * CHORD_DUR
        for k in range(8):
            note = chord[k % len(chord)]
            octave = 12 if k >= 4 else 0
            f = midi(note + octave)
            st = c_start + k * BEAT
            dur = min(1.35, DUR - st)
            # 轻微失谐模拟双弦，包络 attack 6ms + exp decay
            def tone(t, _i, f=f):
                env = (1.0 - math.exp(-90.0 * t)) * math.exp(-2.5 * t)
                return env * (
                    math.sin(2 * math.pi * f * t)
                    + 0.34 * math.sin(2 * math.pi * 2 * f * t)
                    + 0.14 * math.sin(2 * math.pi * 3 * f * t)
                    + 0.06 * math.sin(2 * math.pi * 4.01 * f * t)
                    + 0.22 * math.sin(2 * math.pi * (f + 0.7) * t)
                )
            add(st, dur, tone, 0.115 if k % 4 == 0 else 0.075)

        # 2) 低音 pad：根音低八度，缓慢呼吸
        bass = midi(chord[0] - 12)
        def pad(t, _i, f=bass):
            env = 0.55 + 0.45 * math.sin(2 * math.pi * 0.45 * t)
            return env * (math.sin(2 * math.pi * f * t) + 0.18 * math.sin(2 * math.pi * 2 * f * t))
        add(c_start, CHORD_DUR, pad, 0.10)

    # 3) 每拍 kick + 八分 hihat（用确定性伪随机代替真噪声，保证可复现）
    seed = 20261107
    def noise(i):
        nonlocal seed
        seed = (1103515245 * seed + 12345) & 0x7FFFFFFF
        return (seed / 0x3FFFFFFF) - 1.0

    for b in range(int(DUR / (BEAT * 2)) + 1):
        st = b * BEAT * 2
        def kick(t, _i):
            return math.sin(2 * math.pi * (58.0 - 22.0 * min(1.0, t / 0.10)) * t) * math.exp(-24.0 * t)
        add(st, 0.18, kick, 0.16)
    for h in range(int(DUR / BEAT) + 1):
        st = h * BEAT
        def hat(t, i):
            return noise(i) * math.exp(-90.0 * t)
        add(st, 0.055, hat, 0.032)

    # 4) 开场 whoosh：0~0.55s 上扫 + 噪声
    def whoosh(t, i):
        f = 180.0 + 900.0 * min(1.0, t / 0.55)
        return (math.sin(2 * math.pi * f * t) * 0.6 + noise(i) * 0.4) * (t / 0.55) * (1.0 - t / 0.55)
    add(0.0, 0.55, whoosh, 0.09)

    # 5) 首尾淡入淡出 + 峰值归一化到 -6dBFS
    fade_in = int(0.30 * SR)
    fade_out = int(1.30 * SR)
    for i in range(fade_in):
        buf[i] *= i / fade_in
    for i in range(fade_out):
        buf[N - 1 - i] *= i / fade_out
    peak = max(abs(v) for v in buf) or 1.0
    scale = 0.50 / peak
    pcm = struct.pack("<" + str(N) + "h", *[int(max(-1.0, min(1.0, v * scale)) * 32767) for v in buf])

    with wave.open(out, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm)
    print(f"OK  {out}  {DUR:.2f}s  {os.path.getsize(out) // 1024}KB  peak={peak:.3f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
