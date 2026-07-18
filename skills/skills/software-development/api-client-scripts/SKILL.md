---
name: api-client-scripts
skill: api-client-scripts
description: Create reusable CLI scripts wrapping OpenAI-compatible APIs, for consumption by other agents in the fleet.
---

# Agent API Client Scripts

Create reusable shell scripts that wrap OpenAI-compatible API endpoints so any agent (@her2home_bot, @opclwtg_one_bot, @rysx_vps_bot, etc.) can call them via `bash /path/to/script.sh "question"`.

## Trigger

- User says "写个调用脚本" / "write a call script for other agents"
- You need to expose an API as a shell-accessible tool for other agents
- Creating a script in `/home/kan/scripts/` meant for multi-agent reuse

## Pattern

### 1. Key Management

```
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
KEY_FILE="${SCRIPT_DIR}/.api-name-key"   # e.g. .agnes-key
```

Support three sources with fallback (assign to `API_KEY`):
1. Key file (`.api-name-key`) — `chmod 600`:
   ```bash
   API_KEY=$(cat "$KEY_FILE" | tr -d '\n\r')
   ```
2. Env var:
   ```bash
   API_KEY="$AGNES_API_KEY"   # or SERVICE_API_KEY
   ```
3. Exit with error message if neither found

### 2. Input Handling

Accept both:
- CLI args: `if [ $# -ge 1 ]; then PROMPT="$*"`
- stdin pipe: `elif [ ! -t 0 ]; then PROMPT=$(cat)`

### 3. JSON Construction (Critical!)

**Do NOT use bash heredocs with string interpolation for JSON** — special chars, quotes, and newlines in user input will break it. Always use Python for correct escaping:

```bash
ESCAPED=$(python3 -c "
import json, sys
sys.stdout.write(json.dumps({'role': 'user', 'content': sys.stdin.read().strip()}))
" <<< "$PROMPT")
```

Then build the JSON body with heredocs using the already-escaped variable:

```bash
JSON=$(cat <<EOF
{
  "model": "${MODEL}",
  "messages": [${ESCAPED}],
  "temperature": 0.7,
  "max_tokens": 4096
}
EOF
)
```

### 4. API Call

```bash
RESPONSE=$(curl -s --max-time 120 "$API_URL" \
    -H "Authorization: Bearer *** \
    -H "Content-Type: application/json" \
    -d "$JSON")
```

Note: `${KEY}` was renamed to `${API_KEY}` in Section 1 — use that variable here.

### 5. Response Parsing

Use Python to parse JSON and extract content:

```bash
python3 -c "
import json, sys
try:
    d = json.loads(sys.stdin.read())
    if 'error' in d:
        print(f'ERROR: {d[\"error\"].get(\"message\", d[\"error\"])}', file=sys.stderr)
        sys.exit(1)
    print(d['choices'][0]['message']['content'])
except (json.JSONDecodeError, KeyError, IndexError) as e:
    print(f'PARSE_ERROR: {e}', file=sys.stderr)
    sys.exit(1)
" <<< "$RESPONSE"
```

### 6. Placement & Permissions

**Primary** — local `/home/kan/scripts/` for this agent:
```
/home/kan/scripts/agname.sh          # script — chmod +x
/home/kan/scripts/.agname-key        # key  — chmod 600
```

**Also sync to shared folder** so fleet agents can discover and reuse:
```
/home/kan/shared/<your-bot-dir>/agname.sh   # copy script (no key!)
```

The shared copy lets other bots find and use the script without needing the local path. Document the usage in a `README.md` alongside the script.

Always put `.api-name-key` in the local `$(dirname "$0")` — the script uses relative dir discovery so it works from any cwd even if the key stays local.

## API Endpoint Discovery Pattern

When testing a new/unknown OpenAI-compatible API:

1. `GET /v1/models` — verifies auth + lists available models
2. `POST /v1/chat/completions` — confirms chat works
3. `POST /v1/images/generations` — tests image generation (if the API supports it)
4. **Determine correct base URL**: Some APIs serve everything under a `/v1` prefix, others expect it in the base URL already.
   - If the error says `"Invalid URL (POST /v1/v1/images/generations)"`, the base URL you called already includes `/v1` — drop the `/v1` from paths (use `/images/generations` not `/v1/images/generations`)
   - If `base_url/v1/chat/completions` returns 404 but `base_url/chat/completions` works, the base URL already has `/v1` embedded
5. Base URL variants to try:
   - `https://host.com/v1` (with /v1) — then paths like `/chat/completions`
   - `https://host.com` (without /v1) — then paths like `/v1/chat/completions`
6. **Same key, different scope**: Some API keys only work for certain models/endpoints. One key may list models but return 401 on image/video generation endpoints. Document which models each key can access.
7. **Chat model as API doc proxy**: The chat model often knows nothing about the platform's own API endpoints. Don't rely on it for documentation — probe endpoints directly.

## Image Generation Endpoints (OpenAI-compatible)

The standard OpenAI image generation API shape (`POST /v1/images/generations`) works across many providers. Key differences to probe:

| Parameter | Variants |
|-----------|----------|
| `model` | `dall-e-3`, `sensenova-u1-fast`, provider-specific |
| `size` | Usually `1024x1024`. Send a deliberately bad size to get the full list in the error message |
| `n` | Number of images (default 1, some cap at 4) |
| `response_format` | `url` (default) or `b64_json` |
| `quality` | `standard` or `hd` (most models ignore this) |

**Response shape**:
```json
{
  "created": 1234567890,
  "data": [{"url": "https://...", "revised_prompt": "..."}],
  "usage": {"input_tokens": N, "output_tokens": N}
}
```

`usage` is non-standard but present on some providers. Download the URL promptly — some expire after 1 hour.

### Sensenova u1-fast (tested working)
See `references/sensenova-image-api.md` for full details.

## Pitfalls

- **Bash quoting hell**: User input with quotes, $, backticks, or newlines will break `curl -d "..."`. Always use Python for JSON construction.
- **Auto-redaction in write_file**: The system auto-redacts API keys. When writing a script that references `${API_KEY}` from a file, the literal text may appear as `***` in output — check the actual file bytes with `od -c` to verify.
- **Key file truncation**: Writing `echo "key" > file` where the key string contains `...` from auto-redaction writes literally truncated text. Use Python to reconstruct if write_file redaction interferes. Alternative: use `printf '%s' "$actual_key" > file` and verify byte count with `wc -c`.
- **Stdin detection**: `[ ! -t 0 ]` correctly detects piped input. Without this, an empty argument list with no pipe silently exits with usage error.
- **Timeout**: Always set `--max-time` on curl. Default curl timeout is indefinite.
- **Heredoc backgrounding fails**: Using `&` in a foreground `terminal()` call is rejected. Use `terminal(background=true)` for long-lived processes.

## Reference

- Working example: `/home/kan/scripts/agnes-ask.sh`
- Key file: `/home/kan/scripts/.agnes-key`
- Memory entry: `Agnes AI API` in memory store
