#!/usr/bin/env python3
"""Step 3: TTS — per-segment edge-tts with timeout, trim silence, real durations"""
import sys, os, json, asyncio, subprocess, wave, struct, time

VOICE = "zh-CN-YunyangNeural"
FFMPEG = "C:/Users/Administrator/AppData/Local/Microsoft/WinGet/Packages/Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-8.1.2-full_build/bin/ffmpeg.exe"


def build_segments(items, pub_date_fmt, pub_weekday):
    segs = []
    segs.append(("intro", f"这里是隔天信号弹，今天是{pub_date_fmt}，{pub_weekday}。欢迎收看本期周末特别版，以下是本周精选的{len(items)}条核心新闻。"))
    for i, item in enumerate(items, 1):
        txt = f"第{i}条，{item['section']}。{item['title']}。{item['full_body']}"
        if item["opinion"]:
            txt += f".主播观点：{item['opinion']}"
        segs.append((f"item{i}", txt))
    segs.append(("outro", "今天主播：图图。互动话题：您最关注哪条新闻？欢迎在评论区留言讨论！感谢您的关注，我们下期见~"))
    return segs


async def gen_one_segment(idx, label, text, voice, sem, audio_dir):
    """Generate one segment with semaphore control."""
    import edge_tts, aiohttp
    async with sem:
        print(f"  [{label}] {len(text)}c...", end="", flush=True)
        mp3 = os.path.join(audio_dir, f'_s{idx:03d}.mp3')
        conn = aiohttp.TCPConnector(
            resolver=aiohttp.resolver.ThreadedResolver(),
        )
        communicate = edge_tts.Communicate(text, voice, connector=conn, connect_timeout=30, receive_timeout=120)
        await communicate.save(mp3)
        return (idx, label, mp3)


async def gen_tts(items_path, output_wav, pub_date_fmt="2026年07月25日", pub_weekday="星期六"):
    with open(items_path, 'r', encoding='utf-8') as f:
        items = json.load(f)

    segs = build_segments(items, pub_date_fmt, pub_weekday)
    print(f"Per-segment TTS: {len(segs)} segments")

    audio_dir = os.path.dirname(output_wav)
    os.makedirs(audio_dir, exist_ok=True)

    # Run all segments concurrently with semaphore (max 3 concurrent)
    sem = asyncio.Semaphore(3)
    tasks = [gen_one_segment(i, l, t, VOICE, sem, audio_dir) for i, (l, t) in enumerate(segs)]
    results = await asyncio.gather(*tasks)

    # Sort by index, convert to WAV, trim silence
    results.sort(key=lambda x: x[0])
    durations = []
    all_pcm = bytearray()

    for idx, label, mp3 in results:
        # MP3 to WAV
        wav = mp3.replace('.mp3', '.wav')
        subprocess.run([FFMPEG, '-y', '-i', mp3, '-acodec', 'pcm_s16le', '-ar', '24000', '-ac', '1', wav],
                       check=True, capture_output=True, timeout=60)
        os.remove(mp3)

        # Read WAV, trim silence
        with wave.open(wav, 'rb') as w:
            rate = w.getframerate()
            raw = w.readframes(w.getnframes())

        # Trim leading silence
        threshold = 200
        samples = [int.from_bytes(raw[i:i+2], 'little', signed=True) for i in range(0, len(raw), 2)]
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
        dur = len(trimmed) / rate

        # Build trimmed PCM
        for s in trimmed:
            all_pcm.extend(struct.pack('<h', s))

        print(f" {dur:.2f}s (trimmed {start/rate:.2f}s lead)")
        durations.append(dur)
        os.remove(wav)

    # Write combined WAV
    with wave.open(output_wav, 'wb') as out:
        out.setnchannels(1)
        out.setsampwidth(2)
        out.setframerate(24000)
        out.writeframes(bytes(all_pcm))

    total = len(all_pcm) / 48000
    print(f"  Combined: {total:.2f}s")

    # Save segments
    seg_path = output_wav.replace('.wav', '_segments.json')
    with open(seg_path, 'w') as f:
        json.dump(durations, f)

    print(f"  Saved: {len(durations)} segments")
    return output_wav, durations


if __name__ == "__main__":
    items_path = sys.argv[1] if len(sys.argv) > 1 else "E:/projects/signal_pop/output/weekly_20260717/parsed_news.json"
    out = sys.argv[2] if len(sys.argv) > 2 else "E:/projects/signal_pop/output/weekly_20260717/audio/tts.wav"
    asyncio.run(gen_tts(items_path, out))