# Sensenova backend (OpenAI-compatible) — graphify semantic layer

Tested working endpoint for graphify's `--backend openai` semantic extraction
(text-only; cannot read images — see quirk below).

## Config (export before `graphify extract`)
```bash
export OPENAI_BASE_URL="https://token.sensenova.cn/v1"
export OPENAI_API_KEY="sk-uYIUXv8NlePvFVJJisGjSPvQABMfg9Us"
export OPENAI_MODEL="glm-5.2"
graphify extract . --backend openai --out /home/kan/shared/<proj>
```
Always pass `--backend openai` explicitly — if `GEMINI_API_KEY` is also set in the
env, graphify auto-selects gemini and fails (see SKILL.md pitfall #5).

## Model behavior
- `glm-5.2` is a **text-only** chat model. It returns reasoning_content + content
  (reasoning tokens count against `max_tokens`; give it headroom).
- Cost observed: ~880 in / 1519 out tokens ≈ **$0.0028** for a small repo
  (8 text docs). Cheap.

## Quirk: images rejected (reproduction recipe)
When the corpus contains images, graphify packages them as multimodal chunks.
glm-5.2 rejects `image_url`:
```
[graphify] chunk N failed: Error code: 400 -
  {'error': {'message': "messages.content.type 参数非法，取值范围 ['text']",
             'type': 'invalid_request_error', 'code': '400001'}}
```
Effect: image nodes become empty shells; any image→image edges are model-guessed
(INFERRED, low confidence ~0.38) and are NOT reliable. The text/docs part of the
graph is still real.

Fix options:
1. Use a **vision-capable** OpenAI-compatible model (supports `image_url`) → re-run
   `graphify extract .` to actually understand images.
2. Run `--code-only` (no LLM) to skip images entirely and get a clean code graph.
3. Accept现状: treat image nodes as placeholders; don't present image relations as facts.

## Verify endpoint is live (before a big run)
```bash
curl -s https://token.sensenova.cn/v1/chat/completions \
  -H "Authorization: Bearer $OPENAI_API_KEY" -H "Content-Type: application/json" \
  -d '{"model":"glm-5.2","messages":[{"role":"user","content":"say OK"}],"max_tokens":10}'
```
