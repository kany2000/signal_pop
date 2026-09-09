#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成原创轻开场乐 v2（更柔/更低/更干净）：舒缓上扬短句 + 暖低音垫，无高频微光，整体压低。
采样率 24000 与正片 TTS 对齐，输出 16-bit WAV，供 ffmpeg 编码为 aac。
设计：C 大调中低音区；钟琴式柔音（慢起音、长衰减）；低八度叠加增暖；轻混响；峰值归一 -6 dBFS。"""
import numpy as np
import wave
import os

FS = 24000
DUR = 10.0
N = int(FS * DUR)
OUT = "E:/projects/signal_pop/remotion_poc/out/opening_music.wav"

t = np.linspace(0, DUR, N, endpoint=False)
buf = np.zeros(N, dtype=np.float64)

def add_bell(freq, start, length, amp, harm=(1.0, 0.25, 0.10), attack=0.09, release=0.6):
    s = int(start * FS)
    e = min(N, int((start + length) * FS))
    if e <= s:
        return
    dur = e - s
    tt = np.linspace(0, length, dur, endpoint=False)
    a = int(attack * FS)
    r = int(release * FS)
    env = np.ones(dur)
    if a > 0:
        env[:a] = np.linspace(0, 1, a)
    rel_start = max(a, dur - r)
    if r > 0 and rel_start < dur:
        env[rel_start:] = np.linspace(1, 0, dur - rel_start)
    sig = np.zeros(dur)
    for i, h in enumerate(harm):
        sig += h * np.sin(2 * np.pi * freq * (i + 1) * tt)
    sig /= sum(harm)
    buf[s:e] += amp * env * sig

# ---- 暖低音垫（C2/G2/C3），极轻、缓慢渐入，全程托底 ----
for freq, amp in [(65.41, 0.05), (98.00, 0.04), (130.81, 0.045)]:
    tt = t
    swell = np.clip(tt / 1.6, 0, 1) * 0.7 + 0.3
    sig = np.sin(2 * np.pi * freq * tt) + 0.2 * np.sin(2 * np.pi * freq * 2 * tt)
    sig /= 1.2
    buf += amp * swell * sig

# ---- 舒缓上扬短句（C4 E4 G4 A4 G4），钟琴柔音，低八度叠加增暖 ----
motif = [
    (261.63, 0.40, 1.2),   # C4
    (329.63, 1.55, 1.2),   # E4
    (392.00, 2.70, 1.2),   # G4
    (440.00, 3.85, 1.2),   # A4
    (392.00, 5.00, 1.6),   # G4（收束）
]
low_oct = {261.63: 130.81, 329.63: 164.81, 392.00: 196.00, 440.00: 220.00}
for f, st, ln in motif:
    add_bell(f, st, ln, 0.16)
    add_bell(low_oct[f], st, ln, 0.07)  # 低八度暖音

# ---- 结尾柔化和弦（C4 E4 G4）淡入，随主总线淡出 ----
for f, amp in [(261.63, 0.05), (329.63, 0.045), (392.00, 0.045)]:
    s = int(8.0 * FS)
    e = N
    dur = e - s
    tt = np.linspace(0, (DUR - 8.0), dur, endpoint=False)
    env = np.clip(tt / 0.8, 0, 1)
    sig = np.sin(2 * np.pi * f * tt) + 0.2 * np.sin(2 * np.pi * f * 2 * tt)
    sig /= 1.2
    buf[s:e] += amp * env * sig

# ---- 主总线：淡入淡出 + 轻混响 + 压低归一 ----
buf *= np.clip(t / 0.20, 0, 1)
buf *= np.clip((DUR - t) / 0.8, 0, 1)

ir_len = int(0.22 * FS)
ir = np.exp(-np.linspace(0, 6, ir_len)) * (np.random.rand(ir_len) * 2 - 1)
ir /= np.max(np.abs(ir))
B = 1 << 18
X = np.fft.rfft(buf, B)
H = np.fft.rfft(ir, B)
wet = np.fft.irfft(X * H, B)[:N]
buf = buf * 0.88 + wet * 0.12

peak = np.max(np.abs(buf)) + 1e-9
buf = buf / peak * 0.50  # -6 dBFS，整体更柔更轻
buf = np.tanh(buf)

pcm = (buf * 32767).astype(np.int16)
os.makedirs(os.path.dirname(OUT), exist_ok=True)
with wave.open(OUT, "w") as w:
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(FS)
    w.writeframes(pcm.tobytes())
print(f"OK music v2: {OUT} ({os.path.getsize(OUT)//1024} KB, peak {peak:.3f})")
