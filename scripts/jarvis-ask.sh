#!/bin/bash
# jarvis-ask.sh — routeur unifié de la cascade CLI JARVIS (cf CAHIER_CHARGES_CASCADE_CLI.md §3)
# Analyse la tâche → route vers le backend le moins coûteux → fallback en cascade.
# Usage : jarvis-ask.sh [--auto|--code|--reason|--web|--fast] "question"
#         echo "..." | jarvis-ask.sh --auto
# Sortie : réponse + attribution [backend] sur stderr. 0 token API Anthropic.

set -uo pipefail
SELF="$(readlink -f "${BASH_SOURCE[0]}")"   # résout le symlink ~/.local/bin/jarvis-ask
DIR="$(cd "$(dirname "$SELF")" && pwd)"
LM="$DIR/lm-ask.sh"
GEM="$DIR/gemini-ask.sh"

MODE="auto"
case "${1:-}" in
  --auto)   MODE="auto";   shift ;;
  --code)   MODE="code";   shift ;;
  --reason) MODE="reason"; shift ;;
  --web)    MODE="web";    shift ;;
  --fast)   MODE="fast";   shift ;;
esac

PROMPT="${*:-}"
[[ -t 0 ]] || PROMPT="$(cat)${PROMPT:+ }$PROMPT"
[[ -z "${PROMPT// }" ]] && { echo "Usage: jarvis-ask.sh [--auto|--code|--reason|--web|--fast] \"question\"" >&2; exit 1; }

# --- Auto-classification par mots-clés (insensible casse) ---
if [[ "$MODE" == "auto" ]]; then
  low="${PROMPT,,}"
  if   echo "$low" | grep -qE "recherche|cherche.+(web|internet|en ligne)|actualit|derni[èe]re version|news|sur internet|google"; then MODE="web"
  elif echo "$low" | grep -qE "refactor|impl[ée]ment|écris? (une|un|le|la)? ?(fonction|classe|script|code)|debug|corrige le code|\bcode\b|python|bash|typescript|sql\b"; then MODE="code"
  elif echo "$low" | grep -qE "pourquoi|analyse|raisonn|compare|explique|logique|d[ée]montre|stratégie|architecture"; then MODE="reason"
  elif [[ ${#PROMPT} -gt 500 ]]; then MODE="web"
  else MODE="fast"; fi
fi

run_local() {  # $1 = flag lm-ask ("" | --big | --reason)
  timeout 120 bash "$LM" $1 "$PROMPT" 2>/dev/null
}

OUT=""; BACKEND=""
case "$MODE" in
  fast)   OUT="$(run_local "")";        BACKEND="cluster/fast" ;;
  code)   OUT="$(run_local --big)";     BACKEND="cluster/big" ;;
  reason) OUT="$(run_local --reason)";  BACKEND="cluster/reason" ;;
  web)    OUT="$(timeout 180 bash "$GEM" "$PROMPT" 2>/dev/null)"; BACKEND="gemini" ;;
esac

# --- Cascade de fallback si vide ---
if [[ -z "${OUT// }" ]]; then
  if [[ "$MODE" == "web" ]]; then
    echo "[fallback web→cluster]" >&2
    OUT="$(run_local "")"; BACKEND="cluster/fallback"
  else
    echo "[fallback cluster→gemini]" >&2
    OUT="$(timeout 180 bash "$GEM" "$PROMPT" 2>/dev/null)"; BACKEND="gemini/fallback"
  fi
fi

if [[ -z "${OUT// }" ]]; then
  echo "[XX] Tous les backends locaux/web vides — escalade Opus requise (manuel)" >&2
  exit 1
fi

echo "[$BACKEND]" >&2
echo "$OUT"
