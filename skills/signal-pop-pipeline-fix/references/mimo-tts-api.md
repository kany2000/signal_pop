# MiMo TTS API 实测记录 (2026-06-26)

## 端点与认证
- **Base URL**: `https://api.xiaomimimo.com`
- **Endpoint**: `POST /v1/chat/completions` (OpenAI 兼容格式)
- **Auth**: `Authorization: Bearer <API_KEY>`
- **Model**: `mimo-v2.5-tts`

## 请求格式
```json
{
  "model": "mimo-v2.5-tts",
  "messages": [
    {"role": "user", "content": "要合成的文本"},
    {"role": "assistant", "content": ""}
  ]
}
```
**关键点**: 必须包含 `assistant` role 且 `content` 为空字符串，否则返回 400 "messages must contain an assistant role for TTS model"

## 响应格式
```json
{
  "id": "xxx",
  "choices": [{
    "finish_reason": "stop",
    "index": 0,
    "message": {
      "content": "",
      "role": "assistant",
      "audio": {
        "id": "xxx",
        "data": "<base64_encoded_wav>"
      }
    }
  }]
}
```
- 音频以 base64 编码 WAV 返回 (非流式)
- 需 base64 解码后写文件
- Sample rate: 24000 Hz, mono, pcm_s16le

## Voice 参数
- 通过 `voice` 字段在请求体中指定 (非 messages 内)
- `xiaoxiao` - 女声 (默认)
- `yunyang` - 男声
- 实测: `voice` 参数可选，默认 xiaoxiao

```json
{
  "model": "mimo-v2.5-tts",
  "messages": [...],
  "voice": "yunyang"
}
```

## 实测限制
| 指标 | 实测值 | 说明 |
|------|--------|------|
| 单次最大音频时长 | ~1.12s | 无论输入文本长短，输出固定 ~1s |
| 文本长度影响 | 无 | 短文本/长文本输出时长一致 |
| 并发 | 未测 | 单请求阻塞 |
| 失败重试 | 建议 | 偶发 401/网络错误 |

## 代码示例
```python
import requests, base64

API_KEY = "sk-..."
URL = "https://api.xiaomimimo.com/v1/chat/completions"

def mimo_tts(text, voice="xiaoxiao", output_path="out.wav"):
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    data = {
        "model": "mimo-v2.5-tts",
        "messages": [
            {"role": "user", "content": text},
            {"role": "assistant", "content": ""}
        ],
        "voice": voice
    }
    r = requests.post(URL, headers=headers, json=data, timeout=60)
    if r.status_code == 200:
        audio_b64 = r.json()["choices"][0]["message"]["audio"]["data"]
        with open(output_path, "wb") as f:
            f.write(base64.b64decode(audio_b64))
        return output_path
    raise Exception(f"TTS failed: {r.status_code} {r.text}")
```

## 备选 TTS 方案 (长文本)
| 方案 | 类型 | 优点 | 缺点 |
|------|------|------|------|
| **Piper TTS** | 本地离线 | 免费、无限时长、中文支持好、速度快 | 需下载模型 (~50MB)、无云端管理 |
| **ElevenLabs** | 云端 | 高质量、长文本、SSML、声音克隆 | 付费、配额限制 |
| **OpenAI TTS** | 云端 | 稳定、长文本、多语言 | 付费、延迟较高 |
| **Edge TTS** | 本地/免费 | 免费、微软声音、长文本 | 需 Python 包、非标准 API |

**推荐**: Signal Pop Daily (10 条新闻 ~3-5 分钟) 改用 **Piper TTS** 本地合成，彻底解决时长限制。