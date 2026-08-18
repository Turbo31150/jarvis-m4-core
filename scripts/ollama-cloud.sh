#!/usr/bin/env bash
# ollama-cloud.sh — passerelle unifiée vers les modèles Ollama Cloud GRATUITS.
# Router par usage (décision Turbo 2026-06-25) :
#   code    → qwen3-coder-next
#   général → glm-4.7
#   rapide  → gemma3:12b
# Double voie (décision « les deux ») :
#   1. daemon local :11434 avec modèle :cloud  (transparent, SI `ollama signin` fait)
#   2. fallback API directe https://ollama.com + Bearer OLLAMA_API_KEY  (marche sans signin)
#
# Usage :
#   ollama-cloud.sh "prompt"                  # route auto (général par défaut)
#   ollama-cloud.sh --code "prompt"           # force le modèle code
#   ollama-cloud.sh --fast "prompt"           # force le modèle rapide
#   ollama-cloud.sh --model glm-4.7 "prompt"  # modèle explicite
#   echo "gros contexte" | ollama-cloud.sh --code -
set -euo pipefail

LOCAL_URL="http://127.0.0.1:11434"
CLOUD_URL="https://ollama.com"
KEY="${OLLAMA_API_KEY:-}"

# clé depuis l'env utilisateur si absente (session non-login)
if [ -z "$KEY" ] && [ -f "$HOME/.ollama_api_key" ]; then KEY="$(cat "$HOME/.ollama_api_key")"; fi

MODEL=""; LANE="general"
args=()
while [ $# -gt 0 ]; do
  case "$1" in
    --code)  MODEL="qwen3-coder-next"; shift ;;
    --fast)  MODEL="gemma3:12b";       shift ;;
    --gen|--general) MODEL="glm-4.7";  shift ;;
    --model) MODEL="$2"; shift 2 ;;
    *) args+=("$1"); shift ;;
  esac
done
PROMPT="${args[*]:-}"
[ "$PROMPT" = "-" ] && PROMPT="$(cat)"
[ -z "$PROMPT" ] && { echo "usage: ollama-cloud.sh [--code|--fast|--gen|--model M] \"prompt\"" >&2; exit 2; }

# routage auto par mots-clés si aucun modèle forcé
if [ -z "$MODEL" ]; then
  low="$(printf '%s' "$PROMPT" | tr 'A-Z' 'a-z')"
  if printf '%s' "$low" | grep -qE 'code|function|bug|refactor|python|bash|script|api|sql|regex|compile|stack trace|class |def |import '; then
    MODEL="qwen3-coder-next"
  else
    MODEL="glm-4.7"
  fi
fi

payload() { python3 -c '
import json,sys
print(json.dumps({"model":sys.argv[1],
  "messages":[{"role":"user","content":sys.argv[2]}],"stream":False}))' "$1" "$2"; }

extract() { python3 -c '
import sys,json
try:
  d=json.load(sys.stdin); m=d.get("message")
  if m: print(m["content"]); sys.exit(0)
  print("ERR:"+str(d.get("error","?")),file=sys.stderr); sys.exit(1)
except Exception as e:
  print("ERR:parse "+str(e),file=sys.stderr); sys.exit(1)'; }

# Voie 1 : daemon local (modèle :cloud) — transparent si signin
if curl -sS --max-time 30 "$LOCAL_URL/api/chat" -d "$(payload "${MODEL}:cloud" "$PROMPT")" 2>/dev/null \
     | extract 2>/dev/null; then
  exit 0
fi

# Voie 2 : fallback API directe ollama.com (Bearer) — sans signin
[ -z "$KEY" ] && { echo "ERR: ni signin local, ni OLLAMA_API_KEY pour le fallback" >&2; exit 1; }
curl -sS --max-time 60 "$CLOUD_URL/api/chat" -H "Authorization: Bearer $KEY" \
  -d "$(payload "$MODEL" "$PROMPT")" 2>/dev/null | extract
