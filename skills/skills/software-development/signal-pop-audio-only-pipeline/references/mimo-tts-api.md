# MiMo TTS API Reference (Signal Pop)

## API Configuration

| Setting | Value |
|---------|-------|
| API Endpoint | `https://api.xiaomimimo.com/v1/chat/completions` |
| API Key | `sk-c6iihcqs7cldniegn6zkhi4rv5ea6balu913wbrrddeo5odm` |
| Model | `mimo-v2.5-tts` |
| Platform | `api.xiaomimimo.com` (Owl Meeting / MiMo) |

## Voice IDs

| voice_id | Gender | Use Case |
|----------|--------|----------|
| `xiaoxiao` | 女声 (晓晓) | Daily news (Mon-Fri) |
| `yunyang` | 男声 (云扬) | Weekly news (Sat) |

## Request Format (Verified Working)

```python
import requests

payload = {
    "model": "mimo-v2.5-tts",
    "messages": [
        {"role": "user", "content": "低沉稳重的男声，播报新闻，语速适中，咬字清晰"},
        {"role": "assistant", "content": text_to_speak}
    ],
    "voice_id": "yunyang"  # or "xiaoxiao"
}

headers = {
    "api-key": "sk-c6iihcqs7cldniegn6zkhi4rv5ea6balu913wbrrddeo5odm",
    "Content-Type": "application/json"
}

response = requests.post(
    "https://api.xiaomimimo.com/v1/chat/completions",
    json=payload,
    headers=headers,
    timeout=60
)
```

## ⚠️ Critical: role Rule

**The text to be spoken MUST be in `role: assistant`.**
- `role: user` = style description (low沉的男声/温柔的女声...)
- `role: assistant` = the actual text to synthesize

Placing text in the wrong role produces no audio.

## Response Format

```python
{
    "choices": [
        {
            "message": {
                "audio": {
                    "data": "<base64-encoded PCM audio>"
                }
            }
        }
    ]
}
```

## Audio Decoding

```python
import base64
import wave

audio_b64 = data["choices"][0]["message"]["audio"]["data"]
audio_bytes = base64.b64decode(audio_b64)

# Write as WAV (PCM16, 24kHz, mono)
with wave.open("output.wav", "wb") as w:
    w.setnchannels(1)
    w.setsampwidth(2)      # 16-bit
    w.setframerate(24000)  # 24kHz
    w.writeframes(audio_bytes)
```

## Long Text Handling

MiMo has token limits. For news scripts > ~500 chars, split into segments:

```python
MAX_CHARS = 500  # conservative limit per segment

segments = []
while len(text) > MAX_CHARS:
    # Split at sentence boundary
    split_idx = text.rfind('。', 0, MAX_CHARS)
    if split_idx == -1:
        split_idx = text.rfind('，', 0, MAX_CHARS)
    if split_idx == -1:
        split_idx = MAX_CHARS
    segments.append(text[:split_idx+1])
    text = text[split_idx+1:]
segments.append(text)

# Synthesize each segment, then concatenate WAV files
```

## File Locations

- **Source**: `/home/kan/signal_pop/src/tts_mimo.py`
- **API key stored**: hardcoded in `tts_mimo.py` (do NOT mask/truncate)
- **Test files**: `/tmp/test_f.wav`, `/tmp/test_m.wav`
