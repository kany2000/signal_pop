---
name: pollinations-image-generation
description: Free, no-API-key text-to-image generation via Pollinations AI. Zero setup, HTTP-only. For batch image generation, rapid prototyping, or embedding in automation pipelines.
---

# Pollinations AI Text-to-Image

Free image generation, zero API key, zero registration. HTTP GET only.

## Endpoint

```\nhttps://image.pollinations.ai/prompt/{encoded_prompt}?width={W}&height={H}&nologo=true&model=flux\n```\n\n- `encoded_prompt`: URL-encoded English prompt (use `urllib.parse.quote()` or equivalent)\n- `width` / `height`: default 1024x1024, max ~1280x720 for speed\n- `nologo=true`: removes watermark\n- `model=flux`: use Flux model (better quality, default: FLUX.1-dev)\n- `nofeed=true`: skip feed indexing, faster generation\n- `seed={int}`: deterministic output for same prompt

## Required Headers (PITFALL)

**Without these → 403 Forbidden:**

```python
headers = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
    "Referer": "https://pollinations.ai/"
}
```

## Python Usage

```python
import urllib.request, urllib.parse

prompt = "cyberpunk cityscape, neon lights, cinematic"
q = urllib.parse.quote(prompt)
url = f"https://image.pollinations.ai/prompt/{q}?width=1280&height=720&nologo=true"
req = urllib.request.Request(url, headers={
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
    "Referer": "https://pollinations.ai/"
})
with urllib.request.urlopen(req, timeout=120) as r:
    data = r.read()  # JPEG bytes
```

## Pitfalls

1. **No User-Agent → 403**. Always include both `User-Agent` and `Referer`.\n2. **Spaces in prompt break URL**. Use `urllib.parse.quote()` on the full prompt string.\n3. **Prompts should be English**. Chinese keywords fail — translate first or use generic prompts.\n4. **Timeout should be generous** (120s). Generation takes 5-30s per image.\n5. **Rate limits exist**. Don't hammer; 10-20 concurrent requests is safe.\n6. **Output is always JPEG** regardless of file extension used.\n7. **`nofeed=true` reduces latency** — without it, the server waits for feed indexing before responding. Always add this for batch automation.\n8. **`model=flux` is recommended** — `flux` model gives best quality for English prompts. Default may use a different model depending on prompt language.\n9. **Face distortion** — Pollinations often produces warped faces. Mitigate by avoiding close-up portraits: prefer compositions with "no people" or distant figures.