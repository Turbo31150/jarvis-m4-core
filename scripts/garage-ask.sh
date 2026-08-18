#!/usr/bin/env bash
# garage-ask.sh — routeur d'inférence 0-token : M4 produit via le LM Studio
# de la machine en câble direct (M1, 10.42.0.230:1234), en puisant dans la
# « banque/garage » (bibliothèque vivante BLOCS-INDEX).
#
# Cascade (0-token, on-demand, JAMAIS de boucle permanente) :
#   1. cache SQL local   (réponse déjà produite → 0 inférence)
#   2. M1 LM Studio :1234 (qwen2.5-coder-14b = texte propre, 0 reasoning-runaway)
#   3. Ollama local :11434 (gemma3:4b, CPU) si M1 down
# Aucun appel d'IA facturée. Backend répondant affiché sur stderr (transparence).
#
# Usage :
#   garage-ask.sh "ta question"
#   garage-ask.sh --garage "question"   # injecte des blocs de la banque M1 en contexte
#   garage-ask.sh --big    "question"   # qwen2.5-coder-14b (défaut) — modèle propre
#   garage-ask.sh --fresh  "question"   # ignore le cache
#   echo "texte" | garage-ask.sh --garage "résume"
set -uo pipefail

M1_URL="${GARAGE_M1_URL:-http://10.42.0.230:1234}"
M1_MODEL="${GARAGE_M1_MODEL:-qwen/qwen2.5-coder-14b}"   # propre, finish=stop, 0 reasoning
OLLAMA_URL="${GARAGE_OLLAMA_URL:-http://127.0.0.1:11434}"
OLLAMA_MODEL="${GARAGE_OLLAMA_MODEL:-gemma3:4b}"
GARAGE_INDEX="${GARAGE_INDEX:-$HOME/labo/bibliotheque/lib/BLOCS-INDEX.tsv}"
CACHE_DB="${GARAGE_CACHE_DB:-$HOME/.cache/garage-ask/cache.db}"
MAX_TOKENS="${GARAGE_MAX_TOKENS:-900}"

USE_GARAGE=0; USE_CACHE=1
while [[ "${1:-}" == --* ]]; do
  case "$1" in
    --garage) USE_GARAGE=1 ;;
    --big)    M1_MODEL="qwen/qwen2.5-coder-14b" ;;
    --fresh)  USE_CACHE=0 ;;
    *) echo "option inconnue: $1" >&2 ;;
  esac
  shift
done

Q="${*:-}"
# stdin en contexte (pipe)
STDIN=""
if [ ! -t 0 ]; then STDIN="$(cat)"; fi
[ -z "$Q$STDIN" ] && { echo "usage: garage-ask.sh [--garage|--big|--fresh] \"question\"" >&2; exit 2; }

mkdir -p "$(dirname "$CACHE_DB")"
sqlite3 "$CACHE_DB" "CREATE TABLE IF NOT EXISTS ai_cache(key TEXT PRIMARY KEY, question TEXT, answer TEXT, backend TEXT, hits INTEGER DEFAULT 0, ts TEXT DEFAULT (datetime('now')));" 2>/dev/null

# --- banque/garage : injecter les blocs pertinents (recherche pure, 0 IA) ---
CONTEXT=""
if [ "$USE_GARAGE" = 1 ] && [ -f "$GARAGE_INDEX" ]; then
  kw=$(printf '%s' "$Q" | tr 'A-ZÀ-Ÿ' 'a-zà-ÿ' | grep -oE '[a-zà-ÿ0-9_-]{4,}' | head -6 | paste -sd'|')
  if [ -n "$kw" ]; then
    CONTEXT=$(grep -iE "$kw" "$GARAGE_INDEX" 2>/dev/null | head -12 | cut -f1,4 | sed 's/^/- /')
  fi
fi

PROMPT="$Q"
[ -n "$STDIN" ]  && PROMPT="$PROMPT

--- texte ---
$STDIN"
[ -n "$CONTEXT" ] && PROMPT="Contexte issu de la banque JARVIS (blocs éprouvés) :
$CONTEXT

Question : $PROMPT"

# --- 1. cache ---
KEY=$(printf '%s|%s' "$M1_MODEL" "$PROMPT" | sha256sum | cut -c1-32)
if [ "$USE_CACHE" = 1 ]; then
  hit=$(sqlite3 "$CACHE_DB" "SELECT answer FROM ai_cache WHERE key='$KEY';" 2>/dev/null)
  if [ -n "$hit" ]; then
    sqlite3 "$CACHE_DB" "UPDATE ai_cache SET hits=hits+1 WHERE key='$KEY';" 2>/dev/null
    echo "[backend: cache]" >&2
    printf '%s\n' "$hit"
    exit 0
  fi
fi

# helper : appel OpenAI-compat, extrait content (python3, pas de jq)
call() {  # $1=url $2=model
  curl -s -m 120 "$1/v1/chat/completions" -H 'Content-Type: application/json' \
    -d "$(PROMPT="$PROMPT" MODEL="$2" MT="$MAX_TOKENS" python3 -c '
import json,os
print(json.dumps({"model":os.environ["MODEL"],
 "messages":[{"role":"user","content":os.environ["PROMPT"]}],
 "max_tokens":int(os.environ["MT"]),"temperature":0.2}))')" \
  | python3 -c '
import sys,json
try:
  d=json.load(sys.stdin); m=d["choices"][0]["message"]
  c=(m.get("content") or "").strip()
  print(c)
except Exception:
  pass'
}

# --- 2. M1 LM Studio (si joignable) ---
ANS=""; BACKEND=""
if curl -s -m 5 "$M1_URL/v1/models" >/dev/null 2>&1; then
  ANS=$(call "$M1_URL" "$M1_MODEL")
  [ -n "$ANS" ] && BACKEND="M1:${M1_MODEL##*/}"
fi

# --- 3. fallback Ollama local ---
if [ -z "$ANS" ]; then
  if curl -s -m 4 "$OLLAMA_URL/api/tags" >/dev/null 2>&1; then
    ANS=$(call "$OLLAMA_URL" "$OLLAMA_MODEL")
    [ -n "$ANS" ] && BACKEND="ollama:$OLLAMA_MODEL"
  fi
fi

if [ -z "$ANS" ]; then
  echo "[backend: AUCUN — M1 et Ollama injoignables ou vides]" >&2
  exit 3
fi

# écrit au cache (0-token les prochaines fois)
esc=$(printf '%s' "$ANS" | sed "s/'/''/g")
qsc=$(printf '%s' "$Q"   | sed "s/'/''/g")
sqlite3 "$CACHE_DB" "INSERT OR REPLACE INTO ai_cache(key,question,answer,backend) VALUES('$KEY','$qsc','$esc','$BACKEND');" 2>/dev/null

echo "[backend: $BACKEND]" >&2
printf '%s\n' "$ANS"
