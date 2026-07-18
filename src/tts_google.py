#!/usr/bin/env python3
"""
Signal Pop — Google Gemini TTS (AI Studio)
使用 gemini-3.1-flash-tts-preview 生成语音
"""
import os
import sys
import base64
import wave
import requests
from datetime import datetime

# ========== 配置 ==========
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")  # 在 .env 设置
MODEL = "gemini-3.1-flash-tts-preview"
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"

# 可用音色（部分常用）
VOICES = {
    "female_news": "Kore",       # 专业女声
    "male_news": "Puck",         # 专业男声
    "female_warm": "Zephyr",     # 温暖女声
    "male_deep": "Orus",         # 低沉男声
    "female_calm": "Aoede",      # 冷静女声
    "male_calm": "Fenrir",       # 冷静男声
}

OUTPUT_DIR = "/home/kan/signal_pop/output"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def synthesize(text: str, voice_name: str = "Kore", output_path: str = None) -> str:
    """
    调用 Gemini TTS 生成语音
    voice_name: 见 VOICES 字典
    返回: WAV 文件路径
    """
    if not GEMINI_API_KEY:
        raise ValueError("请设置 GEMINI_API_KEY 环境变量")

    voice_id = VOICES.get(voice_name, voice_name)

    payload = {
        "contents": [{"parts": [{"text": text}]}],
        "generationConfig": {
            "responseModalities": ["AUDIO"],
            "speechConfig": {
                "voiceConfig": {
                    "prebuiltVoiceConfig": {"voiceName": voice_id}
                }
            }
        }
    }

    headers = {
        "x-goog-api-key": GEMINI_API_KEY,
        "Content-Type": "application/json"
    }

    print(f"[Google TTS] 🎙️ voice={voice_id}, text_len={len(text)}")

    resp = requests.post(API_URL, json=payload, headers=headers, timeout=60)
    if resp.status_code != 200:
        print(f"[Google TTS] HTTP {resp.status_code}: {resp.text[:500]}", file=sys.stderr)
        resp.raise_for_status()

    data = resp.json()
    audio_b64 = data["candidates"][0]["content"]["parts"][0]["inlineData"]["data"]
    audio_bytes = base64.b64decode(audio_b64)

    if output_path is None:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"{OUTPUT_DIR}/google_tts_{voice_name}_{ts}.wav"

    # Gemini 返回 24kHz PCM16 mono
    with wave.open(output_path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(24000)
        w.writeframes(audio_bytes)

    print(f"[Google TTS] ✅ Saved: {output_path} ({len(audio_bytes)} bytes)")
    return output_path


def synthesize_long(text: str, voice_name: str = "Kore", max_chars: int = 3000, output_path: str = None) -> str:
    """长文本分段合成并拼接"""
    import re
    sentences = re.split(r'(?<=[。！？；\n])', text)
    segments = []
    current = ""
    for s in sentences:
        s = s.strip()
        if not s:
            continue
        if len(current) + len(s) <= max_chars:
            current += s
        else:
            if current:
                segments.append(current)
            current = s
    if current:
        segments.append(current)

    print(f"[Google TTS] Split into {len(segments)} segments")

    if output_path is None:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"{OUTPUT_DIR}/google_tts_{voice_name}_{ts}.wav"

    combined = b""
    for i, seg in enumerate(segments):
        print(f"[Google TTS] Segment {i+1}/{len(segments)}")
        seg_path = f"/tmp/google_seg_{i}.wav"
        synthesize(seg, voice_name, seg_path)
        with wave.open(seg_path, "rb") as w:
            combined += w.readframes(w.getnframes())
        os.unlink(seg_path)

    with wave.open(output_path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(24000)
        w.writeframes(combined)

    print(f"[Google TTS] ✅ Combined: {output_path}")
    return output_path


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python tts_google.py <text> [--voice VOICE] [--output FILE]")
        print(f"Voices: {', '.join(VOICES.keys())}")
        sys.exit(1)

    text = sys.argv[1]
    voice = "female_news"
    output = None

    if "--voice" in sys.argv:
        idx = sys.argv.index("--voice")
        voice = sys.argv[idx + 1]
    if "--output" in sys.argv:
        idx = sys.argv.index("--output")
        output = sys.argv[idx + 1]

    wav_path = synthesize_long(text, voice_name=voice, output_path=output)
    print(f"\n🎙️ Output: {wav_path}")