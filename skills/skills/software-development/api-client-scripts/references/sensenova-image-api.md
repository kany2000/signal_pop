# Sensenova u1-fast Image Generation API

Base URL: `https://token.sensenova.cn/v1`
Endpoint: `POST /images/generations` (NOT `/v1/images/generations` — base URL already includes `/v1`)
Auth: `Authorization: Bearer <key>`
Key: `sk-Ork...zWIQ` (stored in memory)

## Valid Sizes (probed via error message)

1664×2496, 2496×1664, 1760×2368, 2368×1760, 1824×2272, 2272×1824, 2048×2048, 2752×1536, 1536×2752, 3072×1376, 1344×3136, 2560×720, 3072×864

## Model

`sensenova-u1-fast` — fast image generation. Response typically ~30s.

## Example

```bash
curl -s https://token.sensenova.cn/v1/images/generations \
  -H "Authorization: Bearer sk-Orks5KCFxdjhRSm7EEFY57UdykEWzWIQ" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "sensenova-u1-fast",
    "prompt": "your Chinese or English prompt",
    "size": "2752x1536",
    "n": 1
  }'
```

## Response Shape

```json
{
  "created": 1783859378,
  "data": [{"url": "https://aoss.cn-sh-01.sensecoreapi-oss.cn/..."}],
  "output_format": "png",
  "usage": {"input_tokens": 173, "output_tokens": 16512, "total_tokens": 16685}
}
```

- `output_format`: always `png`
- `usage`: includes token counts (non-standard OpenAI but useful for cost tracking)
- URL expires after ~1 hour (S3 signed URL with 3600s expiry)

## Chinese Prompt Support

Unlike Pollinations.ai, **Chinese prompts work natively**. The model renders Chinese text in images accurately.

## Key Scope

This key also works for chat models (glm-5.2, glm-5.1) at the same base URL. The key supports both chat completions and image generation.