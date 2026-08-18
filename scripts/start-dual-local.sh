#!/bin/bash
# start-dual-local.sh : Lancement simultané de Claude Code (RTX 3080 / Qwen 9B) et OpenClaw (RTX 2060 / Hermes 7B)

set -e
export PATH="$HOME/.local/bin:$HOME/.lmstudio/bin:$PATH"

PROXY_URL="http://127.0.0.1:9765"

# Verification et relance du proxy si besoin
if ! curl -fsS --max-time 2 "$PROXY_URL/health" >/dev/null 2>&1; then
    systemctl --user restart jarvis-proxy-dispatcher.service || true
    sleep 1
fi

MODEL_POWER="qwen/qwen3.5-9b"         # RTX 3080 (GPU 4)
MODEL_FAST="hermes-2-pro-mistral-7b"  # RTX 2060 (GPU 0)

export ANTHROPIC_BASE_URL="$PROXY_URL"
export ANTHROPIC_AUTH_TOKEN="local"
export ANTHROPIC_API_KEY="local"
export OPENAI_BASE_URL="$PROXY_URL/v1"
export OPENAI_API_KEY="local"

echo -e '\033[1;36m╔══════════════════════════════════════════════════════════════════╗\033[0m'
echo -e '\033[1;36m║     J . A . R . V . I . S   — DOUBLE SESSION DUAL GPU LOCAL      ║\033[0m'
echo -e '\033[1;36m╚══════════════════════════════════════════════════════════════════╝\033[0m'
echo "⚡ RTX 3080 (GPU 4) -> Claude Code avec $MODEL_POWER"
echo "⚡ RTX 2060 (GPU 0) -> OpenClaw avec $MODEL_FAST"
echo "──────────────────────────────────────────────────────────────────"

if command -v tmux >/dev/null 2>&1; then
    echo "🚀 Lancement de la session simultanée sous Tmux (Écran Scindé)..."
    tmux kill-session -t jarvis-dual 2>/dev/null || true
    tmux new-session -d -s jarvis-dual -n "Dual-GPU" "export ANTHROPIC_BASE_URL=$PROXY_URL ANTHROPIC_AUTH_TOKEN=local ANTHROPIC_API_KEY=local; claude --model '$MODEL_POWER'"
    tmux split-window -h -t jarvis-dual:0 "export OPENAI_BASE_URL=$PROXY_URL/v1 OPENAI_API_KEY=local; openclaw agent --local --agent main --model '$MODEL_FAST'"
    exec tmux attach-session -t jarvis-dual
else
    echo "🚀 Lancement direct de Claude Code (RTX 3080)..."
    exec claude --model "$MODEL_POWER"
fi
