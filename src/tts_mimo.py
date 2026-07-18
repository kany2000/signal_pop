#!/usr/bin/env python3
"""
Signal Pop — MiMo TTS 语音合成
支持男女声切换，基于 Xiaomi MiMo v2.5 TTS API
"""
import os
import sys
import base64
import wave
import json
import requests
import shutil
from datetime import datetime
import math

# ========== 配置 ==========
API_KEY = os.environ.get("MIMO_API_KEY", "sk-c6iihcqs7cldniegn6zkhi4rv5ea6balu913wbrrddeo5odm")
API_URL = "https://api.xiaomimimo.com/v1/chat/completions"

# Owl Meeting / MiMo 音色 ID（通过 voice_id 参数指定）
# 女声：xiaoxiao（晓晓）| 男声：yunyang（云扬）
VOICE_FEMALE = "xiaoxiao"
VOICE_MALE   = "yunyang"

# 文字风格描述（备用，仅voice_id不生效时使用）
MALE_STYLE   = "低沉稳重的男声，播报新闻，语速适中，咬字清晰"
FEMALE_STYLE = "温柔专业的女声，播报新闻，语速适中，咬字清晰"

OUTPUT_DIR = "/home/kan/signal_pop/output"
# ========== 配置 ==========


# 中文语速估算：约 4-5 字/秒（含标点停顿）
CHARS_PER_SEC = 4.5


def estimate_segment_duration(text: str) -> float:
    """估算文本段的朗读时长（秒）"""
    # 字符数 / 语速，加上标点停顿
    char_count = len(text)
    base_duration = char_count / CHARS_PER_SEC
    # 句号/逗号额外停顿
    pauses = text.count('。') * 0.4 + text.count('，') * 0.2 + text.count('、') * 0.15
    return base_duration + pauses


def generate_srt_from_segments(segments: list, srt_path: str):
    """根据文本段生成 SRT 字幕文件"""
    lines = []
    current_time = 0.0
    
    for i, seg in enumerate(segments, 1):
        duration = estimate_segment_duration(seg)
        start = current_time
        end = current_time + duration
        
        def fmt(t):
            h = int(t // 3600)
            m = int((t % 3600) // 60)
            s = int(t % 60)
            ms = int((t - int(t)) * 1000)
            return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
        
        lines.append(str(i))
        lines.append(f"{fmt(start)} --> {fmt(end)}")
        lines.append(seg)
        lines.append("")  # 空行分隔
        
        current_time = end
    
    with open(srt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    
    print(f"[MiMo TTS] 📝 SRT 生成: {srt_path} ({len(segments)} 段)")
    return srt_path


def generate_srt_from_segments_real(segments: list, durations: list, srt_path: str):
    """用实际音频时长生成精准 SRT 字幕"""
    lines = []
    current_time = 0.0

    for i, (seg, dur) in enumerate(zip(segments, durations), 1):
        start = current_time
        end = current_time + dur

        def fmt(t):
            h = int(t // 3600)
            m = int((t % 3600) // 60)
            s = int(t % 60)
            ms = int((t - int(t)) * 1000)
            return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

        lines.append(str(i))
        lines.append(f"{fmt(start)} --> {fmt(end)}")
        lines.append(seg)
        lines.append("")
        current_time = end

    with open(srt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"[MiMo TTS] ✅ 精准 SRT 生成: {srt_path} ({len(segments)} 段)")
    return srt_path


def synthesize(text: str, voice_gender: str = "female", output_path: str = None) -> str:
    """
    调用 MiMo TTS API 合成语音。
    voice_gender: "male" 或 "female"
    voice_id 优先用 Owl Meeting 音色 ID，fallback 到文字描述
    返回: WAV 文件路径
    """
    voice_id = VOICE_MALE if voice_gender == "male" else VOICE_FEMALE
    style = MALE_STYLE if voice_gender == "male" else FEMALE_STYLE

    payload = {
        "model": "mimo-v2.5-tts",
        "messages": [
            {"role": "user", "content": style},
            {"role": "assistant", "content": text}
        ],
        "voice_id": voice_id   # Owl Meeting 音色ID: xiaoxiao=女, yunyang=男
    }

    headers = {
        "api-key": API_KEY,
        "Content-Type": "application/json"
    }

    print(f"[MiMo TTS] {'👨' if voice_gender == 'male' else '👩'} {voice_gender} voice (voice_id={voice_id})")
    print(f"[MiMo TTS] Text length: {len(text)} chars")

    resp = requests.post(API_URL, json=payload, headers=headers, timeout=60)
    if resp.status_code != 200:
        print(f"[MiMo TTS] HTTP {resp.status_code}: {resp.text[:500]}", file=sys.stderr)
        resp.raise_for_status()

    data = resp.json()
    audio_b64 = data["choices"][0]["message"]["audio"]["data"]

    # 解码 base64 → PCM bytes
    audio_bytes = base64.b64decode(audio_b64)

    if output_path is None:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        gender_tag = "male" if voice_gender == "male" else "female"
        output_path = f"{OUTPUT_DIR}/mimo_tts_{gender_tag}_{ts}.wav"

    # 写入 WAV (PCM16, 24kHz, mono)
    with wave.open(output_path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(24000)
        w.writeframes(audio_bytes)

    print(f"[MiMo TTS] ✅ Saved: {output_path} ({len(audio_bytes)} bytes)")
    return output_path


def text_to_segments(text: str, max_chars: int = 500) -> list:
    """
    将长文本分段，避免超过 API 单次上限。
    优先按新闻条目分段（第1条、第2条...），超长条目再按句子切分。
    """
    import re
    
    # 先尝试按新闻条目分割：第1条、第2条、第3条...
    # 匹配 "第X条" 或 "第X条，"
    item_pattern = r'(第[一二三四五六七八九十\d]+条[，、。])'
    
    # 找到所有条目分隔符
    matches = list(re.finditer(item_pattern, text))
    
    if matches:
        # 按条目分割
        segments = []
        for i, match in enumerate(matches):
            start = match.start()
            end = matches[i+1].start() if i+1 < len(matches) else len(text)
            segment = text[start:end].strip()
            if segment:
                # 如果单条超过 max_chars，按句子再切分
                if len(segment) > max_chars:
                    sentences = re.split(r'(?<=[。！？；\n])', segment)
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
                else:
                    segments.append(segment)
        
        # 检查开头部分（"这里是隔天信号弹..." 开头到第一条之前）
        if matches[0].start() > 0:
            intro = text[:matches[0].start()].strip()
            if intro:
                segments.insert(0, intro)
        
        return segments
    
    # 回退：按句子分割
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

    return segments


def synthesize_long_text(text: str, voice_gender: str = "female", output_path: str = None, srt_path: str = None) -> tuple:
    """
    合成长文本，分段调用后合并为一个 WAV 文件。
    返回: (wav_path, segments_list, durations_list)
    """
    segments = text_to_segments(text, max_chars=500)
    print(f"[MiMo TTS] Split into {len(segments)} segments")

    if output_path is None:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        gender_tag = "male" if voice_gender == "male" else "female"
        output_path = f"{OUTPUT_DIR}/mimo_tts_{gender_tag}_{ts}.wav"
    elif not output_path.endswith('.wav'):
        output_path += '.wav'

    # 合并所有段的 PCM 数据，同时记录每段实际时长
    combined_frames = b""
    durations = []
    for i, seg in enumerate(segments):
        print(f"[MiMo TTS] Segment {i+1}/{len(segments)}: {len(seg)} chars")
        seg_path = f"/tmp/mimo_seg_{i}.wav"
        try:
            synthesize(seg, voice_gender, seg_path)
            with wave.open(seg_path, "rb") as w:
                frames = w.readframes(w.getnframes())
                dur = w.getnframes() / w.getframerate()
                combined_frames += frames
                durations.append(dur)
            os.unlink(seg_path)
        except Exception as e:
            print(f"[MiMo TTS] ⚠️ Segment {i+1} failed: {e}")
            # Retry once after 2s delay
            import time
            print(f"[MiMo TTS] 🔄 Retrying segment {i+1} in 2s...")
            time.sleep(2)
            try:
                synthesize(seg, voice_gender, seg_path)
                with wave.open(seg_path, "rb") as w:
                    frames = w.readframes(w.getnframes())
                    dur = w.getnframes() / w.getframerate()
                    combined_frames += frames
                    durations.append(dur)
                os.unlink(seg_path)
                print(f"[MiMo TTS] ✅ Segment {i+1} succeeded on retry")
            except Exception as e2:
                print(f"[MiMo TTS] ❌ Segment {i+1} failed after retry: {e2}")
                continue

    if not combined_frames:
        raise ValueError("No audio segments generated")

    # 写入合并后的 WAV
    with wave.open(output_path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(24000)
        w.writeframes(combined_frames)

    print(f"[MiMo TTS] ✅ Combined audio saved: {output_path}")
    for i, d in enumerate(durations):
        print(f"  Seg {i}: {d:.2f}s")

    # 保存实际时长 JSON 用于视频精准对齐
    if output_path:
        dur_path = output_path.replace('.wav', '_segments.json')
        with open(dur_path, 'w') as f:
            json.dump(durations, f)
        print(f"[MiMo TTS] ✅ Segment durations saved: {dur_path}")

    # 用实际时长生成 SRT
    if srt_path:
        generate_srt_from_segments_real(segments, durations, srt_path)

    return output_path, segments, durations


def get_ffmpeg_path():
    """获取 ffmpeg 路径（优先用 venv 里的）"""
    venv_ffmpeg = "/home/kan/.hermes/hermes-agent/venv/lib/python3.11/site-packages/imageio_ffmpeg/binaries/ffmpeg-linux-x86_64-v7.0.2"
    if os.path.exists(venv_ffmpeg):
        return venv_ffmpeg
    return "ffmpeg"


def convert_to_mp3(wav_path: str) -> str:
    """将 WAV 转换为 MP3（使用 ffmpeg 封装为 RIFF/WAVE 容器以提高兼容性）"""
    mp3_path = wav_path.replace(".wav", ".mp3")
    ffmpeg_path = get_ffmpeg_path()
    try:
        import subprocess
        # 使用 ffmpeg 转换为标准 MP3 裸流
        tmp_mp3 = mp3_path + ".tmp.mp3"
        result = subprocess.run(
            [ffmpeg_path, "-y", "-i", wav_path,
             "-codec:a", "libmp3lame", "-b:a", "192k",
             "-write_id3v1", "1",
             tmp_mp3],
            capture_output=True, text=True, timeout=120
        )
        if result.returncode != 0:
            print(f"[MiMo TTS] ⚠️ ffmpeg failed: {result.stderr[:200]}")
            return wav_path

        # 将裸 MP3 封装为 RIFF/WAVE 容器（兼容旧版 QuickTime/WMP/macOS）
        result2 = subprocess.run(
            [ffmpeg_path, "-y", "-i", tmp_mp3,
             "-codec:a", "copy",
             "-f", "wav",
             mp3_path],
            capture_output=True, text=True, timeout=120
        )
        os.unlink(tmp_mp3)

        if result2.returncode == 0:
            print(f"[MiMo TTS] ✅ Converted to MP3: {mp3_path}")
            return mp3_path
        else:
            # fallback: 保留原始裸流 MP3
            print(f"[MiMo TTS] ⚠️ WAVE wrapper failed, keeping raw MP3")
            result3 = subprocess.run(
                [ffmpeg_path, "-y", "-i", wav_path,
                 "-codec:a", "libmp3lame", "-b:a", "192k",
                 mp3_path],
                capture_output=True, text=True, timeout=120
            )
            return mp3_path if result3.returncode == 0 else wav_path
    except FileNotFoundError:
        print(f"[MiMo TTS] ⚠️ ffmpeg not found, keeping WAV")
        return wav_path
    except Exception as e:
        print(f"[MiMo TTS] ⚠️ MP3 conversion failed: {e}")
        return wav_path


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python tts_mimo.py <text> [--male|--female] [--output FILE]")
        sys.exit(1)

    text = sys.argv[1]
    gender = "female"
    output = None

    if "--male" in sys.argv:
        gender = "male"
    elif "--female" in sys.argv:
        gender = "female"

    if "--output" in sys.argv:
        idx = sys.argv.index("--output")
        output = sys.argv[idx + 1]

    srt_path = None
    if "--srt" in sys.argv:
        idx = sys.argv.index("--srt")
        srt_path = sys.argv[idx + 1]

    wav_path, segments, durations = synthesize_long_text(text, voice_gender=gender, output_path=output, srt_path=srt_path)
    mp3_path = convert_to_mp3(wav_path)
    print(f"\n🎙️ Output: {mp3_path}")
