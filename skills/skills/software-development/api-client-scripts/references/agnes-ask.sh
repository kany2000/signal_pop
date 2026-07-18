#!/bin/bash
# Agnes AI API CLI — reusable script for any agent
# Usage: bash agnes-ask.sh "your question"
#   or: echo "question" | bash agnes-ask.sh
# Key file: .agnes-key in same directory (chmod 600)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
KEY_FILE="${SCRIPT_DIR}/.agnes-key"
API_URL="https://apihub.agnes-ai.com/v1/chat/completions"
MODEL="agnes-2.0-flash"

# === Key: file > env var > error ===
if [ -f "$KEY_FILE" ] && [ -s "$KEY_FILE" ]; then
    API_KEY=$(cat "$KEY_FILE" | tr -d '\n\r')
elif [ -n "${AGNES_API_KEY:-}" ]; then
    API_KEY="$AGNES_API_KEY"
else
    echo "ERROR: No API key found. Set \$AGNES_API_KEY or create $KEY_FILE" >&2
    exit 1
fi

# === Input: args > stdin ===
if [ $# -ge 1 ]; then
    PROMPT="$*"
elif [ ! -t 0 ]; then
    PROMPT=$(cat)
else
    echo "Usage: bash agnes-ask.sh \"your question\" or pipe input" >&2
    exit 1
fi

# === JSON construction via Python (avoid bash quoting hell) ===
ESCAPED=$(python3 -c "
import json, sys
sys.stdout.write(json.dumps({'role': 'user', 'content': sys.stdin.read().strip()}))
" <<< "$PROMPT")

JSON=$(cat <<EOF
{
  "model": "${MODEL}",
  "messages": [${ESCAPED}],
  "temperature": 0.7,
  "max_tokens": 4096
}
EOF
)

# === API call ===
RESPONSE=$(curl -s --max-time 120 "$API_URL" \
    -H "Authorization: Bearer ${API_KEY}" \
    -H "Content-Type: application/json" \
    -d "$JSON")

# === Response parsing ===
python3 -c "
import json, sys
try:
    d = json.loads(sys.stdin.read())
    if 'error' in d:
        print(f\"ERROR: {d['error'].get('message', d['error'])}\", file=sys.stderr)
        sys.exit(1)
    print(d['choices'][0]['message']['content'])
except (json.JSONDecodeError, KeyError, IndexError) as e:
    print(f\"PARSE_ERROR: {e}\", file=sys.stderr)
    sys.exit(1)
" <<< "$RESPONSE"
