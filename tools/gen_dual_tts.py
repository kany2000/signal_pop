#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Signal Pop 周末特别版 · 双人对话 TTS 合成器
解析对话稿（阿信/小蓝）→ 逐段合成（阿信=云舟男声 / 小蓝=爽快思思女声，豆包语音 2.0）→ 合并 WAV + 分段时长。
用法：python tools/gen_dual_tts.py [PREP_DATE]
后端：默认豆包语音（volcengine）；环境变量 SIGNAL_POP_TTS_BACKEND=edge 可回退 edge-tts。
"""
import os
import sys
import json
import asyncio
import subprocess
import wave
import struct

PROJECT_ROOT = "E:/projects/signal_pop"
PREP_DATE = sys.argv[1] if len(sys.argv) > 1 else "20260814"
SCRIPT_FILE = os.path.join(PROJECT_ROOT, "archive", f"signal_pop_weekly_special_{PREP_DATE}.txt")
OUT_DIR = os.path.join(PROJECT_ROOT, "output", "weekly", PREP_DATE)
AUDIO_DIR = os.path.join(OUT_DIR, "audio")
AUDIO_PATH = os.path.join(AUDIO_DIR, "tts.wav")
SEGMENTS_PATH = os.path.join(AUDIO_DIR, "tts_segments.json")
TALK_PATH = os.path.join(OUT_DIR, "talk_segments.json")
FFMPEG = "E:/projects/signal_pop/bin/ffmpeg-9.0.1-essentials_build/bin/ffmpeg.exe"
sys.path.insert(0, os.path.join(PROJECT_ROOT, "tools"))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "scripts"))

# 读取 .env 到环境变量（无 python-dotenv 时手动解析）
def _load_env():
    env_path = os.path.join(PROJECT_ROOT, ".env")
    if os.path.exists(env_path):
        for line in open(env_path, encoding="utf-8"):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

_load_env()
BACKEND = os.environ.get("SIGNAL_POP_TTS_BACKEND", "volcengine")

# 豆包语音双人音色（2026-08-16 用户认可）：阿信=云舟男 / 小蓝=爽快思思女；edge 兜底保留
VOICES = {
    "阿信": ("zh_male_m191_uranus_bigtts", "zh-CN-YunyangNeural"),    # 云舟 2.0 男声 / edge 男
    "小蓝": ("zh_female_shuangkuaisisi_uranus_bigtts", "zh-CN-XiaoxiaoNeural"),  # 爽快思思 2.0 女声 / edge 女
}


def parse_talk(text):
    """解析对话稿：识别 阿信：/小蓝： 行，返回 [{speaker, voice, text}]"""
    segs = []
    for line in text.strip().split("\n"):
        line = line.strip()
        if not line or line.startswith("【"):
            continue
        for name, voices in VOICES.items():
            if line.startswith(f"{name}：") or line.startswith(f"{name}:"):
                content = line.split("：", 1)[1] if "：" in line else line.split(":", 1)[1]
                voice = voices[0] if BACKEND == "volcengine" else voices[1]
                segs.append({"speaker": name, "voice": voice, "text": content.strip()})
                break
    return segs


async def gen_one(idx, seg, sem, audio_dir):
    """单句合成（豆包语音 volc_synthesize，带重试；edge 兜底）。返回 mp3 路径。"""
    from gen_cloud_tts import volc_synthesize
    import edge_tts, aiohttp
    async with sem:
        mp3 = os.path.join(audio_dir, f"_s{idx:03d}.mp3")
        last_err = None
        for attempt in range(4):
            try:
                if BACKEND == "volcengine":
                    volc_synthesize(seg["text"], seg["voice"], mp3)
                else:
                    conn = aiohttp.TCPConnector(resolver=aiohttp.resolver.ThreadedResolver())
                    comm = edge_tts.Communicate(seg["text"], seg["voice"], connector=conn,
                                                connect_timeout=30, receive_timeout=120)
                    await comm.save(mp3)
                if os.path.getsize(mp3) > 1000:
                    return mp3
                last_err = "empty audio"
            except Exception as e:
                last_err = str(e)[:60]
            await asyncio.sleep(3)
        print(f"  ⚠️ [{seg['speaker']}] 失败: {last_err}")
        return None


async def gen_tts_all(segs):
    os.makedirs(AUDIO_DIR, exist_ok=True)
    sem = asyncio.Semaphore(3)
    tasks = [gen_one(i, s, sem, AUDIO_DIR) for i, s in enumerate(segs)]
    mp3s = await asyncio.gather(*tasks)

    durations = []
    all_pcm = bytearray()
    for idx, (seg, mp3) in enumerate(zip(segs, mp3s)):
        if not mp3 or not os.path.exists(mp3):
            print(f"  ❌ 段{idx} 无音频，跳过")
            durations.append({"dur": 1.0, "speaker": seg["speaker"], "text": seg["text"]})
            continue
        wav = mp3.replace(".mp3", ".wav")
        subprocess.run([FFMPEG, "-y", "-i", mp3, "-acodec", "pcm_s16le", "-ar", "24000", "-ac", "1", wav],
                       check=True, capture_output=True, timeout=60)
        try:
            os.remove(mp3)
        except OSError:
            pass  # 临时 mp3 清理失败不影响 TTS 主流程（sandbox 回收站不可用时）
        with wave.open(wav, "rb") as w:
            rate = w.getframerate()
            raw = w.readframes(w.getnframes())
        # trim 静音（前后 0.5/0.3 秒阈值）
        threshold = 200
        samples = [int.from_bytes(raw[i:i+2], "little", signed=True) for i in range(0, len(raw), 2)]
        start = 0
        for i in range(min(len(samples), int(rate * 0.5))):
            if abs(samples[i]) > threshold:
                start = i
                break
        end = len(samples)
        for i in range(len(samples) - 1, max(0, len(samples) - int(rate * 0.3)) - 1, -1):
            if abs(samples[i]) > threshold:
                end = i + 1
                break
        trimmed = samples[start:end]
        # 男主播音量 +30%（2026-08-21 用户反馈阿信声音偏小；原 +10% 不够，提升到 +30% 让阿信接近小蓝音量）
        if seg["speaker"] == "阿信":
            trimmed = [max(-32768, min(32767, int(s * 1.3))) for s in trimmed]
        dur = len(trimmed) / rate
        for s in trimmed:
            all_pcm.extend(struct.pack("<h", s))
        durations.append({"dur": dur, "speaker": seg["speaker"], "text": seg["text"]})
        try:
            os.remove(wav)
        except OSError:
            pass  # 临时 wav 清理失败不影响主流程
        print(f"  [{idx+1}/{len(segs)}] {seg['speaker']} {dur:.2f}s: {seg['text'][:26]}...")

    with wave.open(AUDIO_PATH, "wb") as out:
        out.setnchannels(1)
        out.setsampwidth(2)
        out.setframerate(24000)
        out.writeframes(bytes(all_pcm))
    json.dump(durations, open(SEGMENTS_PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    json.dump(segs, open(TALK_PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    total = len(all_pcm) / 48000
    print(f"\n✅ 合并音频: {total:.2f}s, {len(durations)} 段")
    print(f"  -> {AUDIO_PATH}")
    print(f"  -> {SEGMENTS_PATH}")
    return durations


if __name__ == "__main__":
    text = open(SCRIPT_FILE, encoding="utf-8").read()
    segs = parse_talk(text)
    print(f"解析 {len(segs)} 句对话")
    asyncio.run(gen_tts_all(segs))
