#!/usr/bin/env bash
# start-dual-local-m4.sh — Double session Claude Code + OpenClaw en tmux (adapté M4)
# Différence M6 : le Smart Router Bi-GPU est distant (M6 via RJ45 direct 10.42.0.230:9765).
set -euo pipefail
export PATH="$HOME/.local/bin:$HOME/.lmstudio/bin:$PATH"

ROUTER_HOST="${JARVIS_ROUTER_HOST:-10.42.0.230}"
PROXY_URL="http://${ROUTER_HOST}:9765"
LMS_URL="http://${ROUTER_HOST}:1234"
OLLAMA_URL="http://127.0.0.1:11434"

MODEL_POWER="qwen/qwen3.5-9b"          # M6 · RTX 3080
MODEL_FAST="hermes-2-pro-mistral-7b"   # M6 · RTX 2060

# --- Cascade de repli (LOI 2) ---
if curl -fsS --max-time 2 "$PROXY_URL/health" >/dev/null 2>&1; then
    BACKEND="M6 Smart Router Bi-GPU"; BASE="$PROXY_URL"
elif curl -fsS --max-time 2 "$LMS_URL/v1/models" >/dev/null 2>&1; then
    BACKEND="M6 LM Studio (direct)"; BASE="$LMS_URL"
elif curl -fsS --max-time 2 "$OLLAMA_URL/api/tags" >/dev/null 2>&1; then
    BACKEND="Ollama local M4 (repli)"; BASE="$OLLAMA_URL"; MODEL_POWER="gemma3:4b"; MODEL_FAST="gemma3:4b"
else
    echo "❌ Aucun backend 0-token joignable." >&2; exit 1
fi

export ANTHROPIC_BASE_URL="$BASE"
export ANTHROPIC_AUTH_TOKEN="local"
export ANTHROPIC_API_KEY="local"
export OPENAI_BASE_URL="$BASE/v1"
export OPENAI_API_KEY="local"

echo -e '\033[1;36m╔══════════════════════════════════════════════════════════════════╗\033[0m'
echo -e '\033[1;36m║   J . A . R . V . I . S   — DOUBLE SESSION M4 → M6 (0-token)     ║\033[0m'
echo -e '\033[1;36m╚══════════════════════════════════════════════════════════════════╝\033[0m'
printf '  Backend : \033[1;32m%s\033[0m  (%s)\n  Power   : %s\n  Fast    : %s\n\n' "$BACKEND" "$BASE" "$MODEL_POWER" "$MODEL_FAST"

SESSION="jarvis-dual-m4"
tmux has-session -t "$SESSION" 2>/dev/null && exec tmux attach -t "$SESSION"

tmux new-session  -d -s "$SESSION" -n dual \
    "ANTHROPIC_BASE_URL=$BASE ANTHROPIC_AUTH_TOKEN=local ANTHROPIC_API_KEY=local claude --model '$MODEL_POWER'; exec bash"
tmux split-window -h -t "$SESSION:dual" \
    "OPENAI_BASE_URL=$BASE/v1 OPENAI_API_KEY=local openclaw; exec bash"
tmux select-layout -t "$SESSION:dual" even-horizontal
exec tmux attach -t "$SESSION"
