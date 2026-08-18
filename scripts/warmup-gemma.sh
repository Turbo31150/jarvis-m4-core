#!/usr/bin/env bash
# warmup-gemma.sh — maintient gemma3:4b chaud en VRAM (anti cold-start du hub LLM 18800).
# Envoie une requête minimale à Ollama avec keep_alive long. Silencieux, exit 0 toujours.
set -u

OLLAMA_URL="${OLLAMA_URL:-http://127.0.0.1:11434}"
MODEL="${WARMUP_MODEL:-gemma3:4b}"
KEEP_ALIVE="${WARMUP_KEEP_ALIVE:-30m}"

payload=$(printf '{"model":"%s","messages":[{"role":"user","content":"hi"}],"stream":false,"keep_alive":"%s"}' \
  "$MODEL" "$KEEP_ALIVE")

if curl -s --max-time 60 "${OLLAMA_URL}/api/chat" -d "$payload" >/dev/null 2>&1; then
  echo "warmup-gemma: ${MODEL} pingé (keep_alive=${KEEP_ALIVE})"
else
  # Ne jamais échouer bruyamment : Ollama peut être down, on log court et on sort 0.
  echo "warmup-gemma: ping ${MODEL} échoué (Ollama ${OLLAMA_URL} injoignable?) — ignoré" >&2
fi

exit 0
