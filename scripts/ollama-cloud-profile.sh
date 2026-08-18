#!/usr/bin/env bash
# ollama-cloud-profile.sh — profil unifié Ollama Cloud (modèles GRATUITS, tier sans abonnement)
# source ~/jarvis/scripts/ollama-cloud-profile.sh
# Décisions Turbo 2026-06-25 : router code→qwen3-coder-next, général→glm-4.7, rapide→gemma3:12b.
# ollama.com expose /v1/messages (Anthropic) ET /v1/chat/completions (OpenAI) → pas de signin requis.

# clé (fichier perms 600 ; ne jamais committer)
[ -f "$HOME/.ollama_api_key" ] && export OLLAMA_API_KEY="$(cat "$HOME/.ollama_api_key")"

export OLLAMA_CLOUD_HOST="https://ollama.com"
export OLLAMA_CLOUD_OPENAI="https://ollama.com/v1"               # base OpenAI-compat (OpenClaw, Antigravity, S9, LM tools)
export OLLAMA_CLOUD_ANTHROPIC="https://ollama.com"              # base Anthropic-compat (Claude Code)
export OLLAMA_CLOUD_MODEL_CODE="qwen3-coder-next"
export OLLAMA_CLOUD_MODEL_GEN="glm-4.7"
export OLLAMA_CLOUD_MODEL_FAST="gemma3:12b"

# --- Claude Code branché sur Ollama Cloud gratuit (via ollama.com Anthropic-compat) ---
alias claude-cloud='ANTHROPIC_BASE_URL="$OLLAMA_CLOUD_ANTHROPIC" ANTHROPIC_AUTH_TOKEN="$OLLAMA_API_KEY" ANTHROPIC_API_KEY="" claude --model "$OLLAMA_CLOUD_MODEL_GEN"'
alias claude-cloud-code='ANTHROPIC_BASE_URL="$OLLAMA_CLOUD_ANTHROPIC" ANTHROPIC_AUTH_TOKEN="$OLLAMA_API_KEY" ANTHROPIC_API_KEY="" claude --model "$OLLAMA_CLOUD_MODEL_CODE"'

# --- passerelle wrapper (route auto + fallback) ---
alias oc='~/jarvis/scripts/ollama-cloud.sh'
alias oc-code='~/jarvis/scripts/ollama-cloud.sh --code'
alias oc-fast='~/jarvis/scripts/ollama-cloud.sh --fast'

# helper OpenAI-compat 1-shot (pour scripts/agents)
occ() {  # occ "prompt" [model]
  local m="${2:-$OLLAMA_CLOUD_MODEL_GEN}"
  curl -sS --max-time 60 "$OLLAMA_CLOUD_OPENAI/chat/completions" \
    -H "Authorization: Bearer $OLLAMA_API_KEY" \
    -d "$(python3 -c 'import json,sys;print(json.dumps({"model":sys.argv[1],"messages":[{"role":"user","content":sys.argv[2]}]}))' "$m" "$1")" \
    | python3 -c 'import sys,json;print(json.load(sys.stdin)["choices"][0]["message"]["content"])'
}
