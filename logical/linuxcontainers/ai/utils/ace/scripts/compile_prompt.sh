#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
SYSTEM_PROMPT_FILE="$SCRIPT_DIR/gemma4_system_prompt.txt"

GEMMA_ENDPOINT="${GEMMA_ENDPOINT:-http://core-gpu.home.lan:8000/v1/chat/completions}"
GEMMA_MODEL="${GEMMA_MODEL:-Gemma4-31b-it}"
GEMMA_TEMPERATURE="${GEMMA_TEMPERATURE:-0.2}"
GEMMA_MAX_TOKENS="${GEMMA_MAX_TOKENS:-4096}"
GEMMA_THINKING_BUDGET="${GEMMA_THINKING_BUDGET:-8192}"

if [[ ! -f "$SYSTEM_PROMPT_FILE" ]]; then
  echo "Missing system prompt file: $SYSTEM_PROMPT_FILE" >&2
  exit 1
fi

if [[ $# -gt 0 ]]; then
  USER_PROMPT="$*"
else
  USER_PROMPT="$(cat)"
fi

if [[ -z "${USER_PROMPT//[[:space:]]/}" ]]; then
  echo "Usage: $0 \"your music request\"" >&2
  echo "   or: echo \"your music request\" | $0" >&2
  exit 1
fi

SYSTEM_PROMPT="$(cat "$SYSTEM_PROMPT_FILE")"

if command -v jq >/dev/null 2>&1; then
  REQUEST_BODY="$(jq -n \
    --arg model "$GEMMA_MODEL" \
    --arg system "$SYSTEM_PROMPT" \
    --arg user "$USER_PROMPT" \
    --argjson temperature "$GEMMA_TEMPERATURE" \
    --argjson max_tokens "$GEMMA_MAX_TOKENS" \
    --argjson thinking_budget "$GEMMA_THINKING_BUDGET" \
    '{
      model: $model,
      messages: [
        {role: "system", content: $system},
        {role: "user", content: $user}
      ],
      temperature: $temperature,
      max_tokens: $max_tokens,
      stream: false,
      chat_template_kwargs: {
        enable_thinking: true,
        thinking_budget: $thinking_budget
      }
    }')"
else
  REQUEST_BODY="$(python3 - <<'PY' "$GEMMA_MODEL" "$SYSTEM_PROMPT_FILE" "$USER_PROMPT" "$GEMMA_TEMPERATURE" "$GEMMA_MAX_TOKENS" "$GEMMA_THINKING_BUDGET"
import json
import pathlib
import sys

model = sys.argv[1]
system_prompt = pathlib.Path(sys.argv[2]).read_text()
user_prompt = sys.argv[3]
temperature = float(sys.argv[4])
max_tokens = int(sys.argv[5])
thinking_budget = int(sys.argv[6])

payload = {
    "model": model,
    "messages": [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ],
    "temperature": temperature,
    "max_tokens": max_tokens,
    "stream": False,
    "chat_template_kwargs": {
        "enable_thinking": True,
        "thinking_budget": thinking_budget,
    },
}

print(json.dumps(payload))
PY
  )"
fi

RESPONSE="$(curl -fsS "$GEMMA_ENDPOINT" \
  -H 'Content-Type: application/json' \
  -d "$REQUEST_BODY")"

if command -v jq >/dev/null 2>&1; then
  CONTENT="$(printf '%s' "$RESPONSE" | jq -r '.choices[0].message.content')"
else
  CONTENT="$(python3 - <<'PY' "$RESPONSE"
import json
import sys

response = json.loads(sys.argv[1])
print(response["choices"][0]["message"]["content"])
PY
  )"
fi

printf '%s\n' "$CONTENT"