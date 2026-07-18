# Agnes AI API — apihub.agnes-ai.com

## Endpoint

```
Base URL: https://apihub.agnes-ai.com/v1
Auth:    Authorization: Bearer <api_key>
Format:  OpenAI-compatible (chat completions)
```

API key format: `sk-*` (OpenAI-style).

## Available Models (2026-06-05)

| Model | Type | Notes |
|-------|------|-------|
| `agnes-1.5-flash` | Chat | Works with this key |
| `agnes-2.0-flash` | Chat | Works with this key; self-identifies as "Agnes, developed by Sapiens AI" |
| `agnes-video-v2.0` | Video gen | Listed in models but POST endpoints return 401 "无效的令牌" with this key |
| `agnes-image-2.1-flash` | Image gen | Listed but 401 with this key |
| `agnes-image-2.0-flash` | Image gen | Listed but 401 with this key |

## Working Endpoints

### GET /v1/models
Lists all available models. Returns `{"data": [...], "object": "list", "success": true}`.
Requires auth header but may work with limited-scope keys.

### POST /v1/chat/completions
Standard OpenAI chat format. Works with `agnes-1.5-flash` and `agnes-2.0-flash`.

```json
{
  "model": "agnes-2.0-flash",
  "messages": [{"role": "user", "content": "..."}]
}
```

## Non-Working Endpoints (with this key)

All return HTTP 401 `"无效的令牌"`:
- `POST /v1/images/generations` — image gen
- `POST /v1/video/generations` — video gen
- Any `/v1/v1/...` doubled path → 404 `"Invalid URL"`

## URL Quirk

The base URL already includes `/v1`. POST to `apihub.agnes-ai.com/v1/chat/completions` (not `apihub.agnes-ai.com/v1/v1/...`).
If you use the raw domain `apihub.agnes-ai.com` without `/v1`, all requests return 401.

## Discovery Notes

- Chat model doesn't have knowledge of its own API platform — can't self-document available endpoints.
- Video/image gen likely needs a different API key tier or separate permission scope.
- The API proxies to upstream OpenAI (404 errors reveal `OpenAIException`).
- Web frontend at `app.agnes-ai.com` requires Google OAuth login (Cloudflare-protected).
