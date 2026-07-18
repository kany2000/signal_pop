# graphify — OpenAI-compatible backends (non-Gemini)

When `GEMINI_API_KEY` is dead/revoked, graphify still runs the semantic layer against
ANY OpenAI-compatible endpoint via the `openai` backend. graphify reads three env vars.

## Sensenova (商汤) — CONFIRMED WORKING 2026-07-09

```bash
export OPENAI_BASE_URL="https://token.sensenova.cn/v1"
export OPENAI_API_KEY="<key>"          # sk-...
export OPENAI_MODEL="glm-5.2"
graphify extract . --backend openai --out <dir>
# --backend openai optional: OPENAI_* is auto-detected by graphify
```

Pre-flight sanity check (text only):
```bash
curl -s --max-time 20 https://token.sensenova.cn/v1/chat/completions \
  -H "Authorization: Bearer $OPENAI_API_KEY" -H "Content-Type: application/json" \
  -d '{"model":"glm-5.2","messages":[{"role":"user","content":"hi"}],"max_tokens":10}'
```
Returns `chat.completion` JSON. NOTE: glm-5.2 streams `reasoning_content` before the
answer; with a tiny `max_tokens` it truncates mid-reasoning and the `content` may be
empty — that's a token-budget artifact, not a failure.

### Result on Signal Pop (8 txt + 46 jpg)
- 12 nodes / 11 edges / 4 communities, ~880 in / 1519 out tokens, ~$0.0028, 37s.
- **Only the 8 txt news files were semantically understood.** The 46 images were
  dropped: glm-5.2 is TEXT-ONLY and rejects `image_url` content blocks with
  `400 messages.content.type 参数非法，取值范围 ['text']` (code 400001).
- Image nodes still appear in the graph (filename only) and image↔image edges are
  INFERRED guesses from filesystem paths — NOT reliable. Use a multimodal endpoint to
  actually parse images, or `--code-only`.

## MiMo (api.xiaomimimo.com) — endpoint works, account had NO balance

```bash
export OPENAI_BASE_URL="https://api.xiaomimimo.com/v1"
export OPENAI_API_KEY="sk-..."        # the Owl/TTS key
export OPENAI_MODEL="mimo-v2.5-pro"
```
`/v1/models` lists chat models (mimo-v2.5, mimo-v2.5-pro, ...). BUT `chat/completions`
returned `402 Insufficient account balance` on 2026-07-09 — valid key, empty wallet.
Works the moment credit is added; same shape as Sensenova otherwise.

## Local llama.cpp / vLLM — free, fully offline

```bash
export OPENAI_BASE_URL="http://localhost:8080/v1"   # or :8000
export OPENAI_API_KEY="not-needed"
export OPENAI_MODEL="<your-local-model>"
```
Best for private corpora and zero cost. Needs the server actually running (none was up
on the test host). Multimodal depends on the local model's capabilities.

## Decision rule
| Need | Backend |
|---|---|
| Code structure only, no key | `graphify extract . --code-only` (0 tokens) |
| Docs/text semantics | any text OR multimodal endpoint |
| Image/PDF/video semantics | MUST be a multimodal-compatible endpoint |
| Fully offline / free | local llama.cpp/vLLM |
| Gemini key present & valid | default `gemini` backend (needs `graphifyy[gemini]`) |
