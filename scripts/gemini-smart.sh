#!/bin/bash
# gemini-smart.sh — Wrapper Gemini CLI avec watchdog anti-blocage, logging, profils
#
# Usage:
#   gemini-smart.sh [options] "prompt"
#   echo "prompt" | gemini-smart.sh [options]
#
# Options:
#   --short        Tâche courte (flash, timeout 45s)  [défaut si prompt < 200 chars]
#   --long         Tâche longue (pro, timeout 180s)
#   --pro          Force gemini-2.5-pro
#   --flash        Force gemini-2.5-flash
#   --model ID     Modèle explicite
#   --via NAME     Source (lumen|whisperflow|telegram|cli) pour logs
#   --json         Output JSON wrappé {"output":"...","status":"...","dur_s":...}
#   --no-log       Désactive le logging SQLite
#   --analyze      Affiche stats/scoring des sessions
#   --no-fallback  Pas de fallback lm-ask.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/gemini-session-logger.sh" 2>/dev/null || true

# --- Session registry ---
bash /home/pamerys/.jarvis/session-start.sh gemini-cli $$ 2>/dev/null &

# --- Defaults ---
MODEL=""
VIA="direct"
JSON_OUT=false
DO_LOG=true
FALLBACK=true
TIMEOUT_PRO=180
TIMEOUT_FLASH=45
FORCE_SHORT=false
FORCE_LONG=false
SESSION_ID=""

# --- Parse args ---
while [[ "${1:-}" == --* ]]; do
  case "$1" in
    --short)       FORCE_SHORT=true; shift ;;
    --long)        FORCE_LONG=true; shift ;;
    --pro)         MODEL="gemini-2.5-pro"; shift ;;
    --flash)       MODEL="gemini-2.5-flash"; shift ;;
    --model)       MODEL="$2"; shift 2 ;;
    --via)         VIA="$2"; shift 2 ;;
    --json)        JSON_OUT=true; shift ;;
    --no-log)      DO_LOG=false; shift ;;
    --analyze)     gemini_analyze 2>/dev/null; exit 0 ;;
    --no-fallback) FALLBACK=false; shift ;;
    --timeout)     TIMEOUT_PRO="$2"; TIMEOUT_FLASH="$2"; shift 2 ;;
    *) shift ;;
  esac
done

# --- Prompt ---
PROMPT="${*:-}"
[[ -t 0 ]] || PROMPT="$(cat)${PROMPT:+ }${PROMPT}"
PROMPT="${PROMPT// /}"  # trim leading/trailing
if [[ -z "$PROMPT" ]]; then
  echo "Usage: gemini-smart.sh [--short|--long|--flash|--pro] \"prompt\"" >&2
  exit 1
fi

PROMPT_LEN=${#PROMPT}

# --- Auto-select model / timeout ---
if [[ -z "$MODEL" ]]; then
  if $FORCE_LONG || [[ $PROMPT_LEN -gt 500 ]]; then
    MODEL="gemini-2.5-pro"
    # Dégrader vers flash si l'heure courante a un mauvais historique
    HOUR_QUALITY=$(gemini_best_hours 2>/dev/null || echo "unknown")
    if [[ "$HOUR_QUALITY" == "bad" ]]; then
      MODEL="gemini-2.5-flash"
      echo "[gemini-smart] heure défavorable→flash" >&2
    fi
  else
    MODEL="gemini-2.5-flash"
  fi
fi
$FORCE_LONG && MODEL="gemini-2.5-pro"
$FORCE_SHORT && MODEL="gemini-2.5-flash"

[[ "$MODEL" == *pro* ]] && TIMEOUT=$TIMEOUT_PRO || TIMEOUT=$TIMEOUT_FLASH

# --- Log start ---
if $DO_LOG && command -v gemini_log_start &>/dev/null; then
  SESSION_ID=$(gemini_log_start "$MODEL" "$PROMPT_LEN" "$VIA" 2>/dev/null) || SESSION_ID=""
fi

# --- Watchdog : tue Gemini si aucune sortie pendant TIMEOUT secondes ---
TMPOUT=$(mktemp /tmp/gemini-smart-XXXXXX)
TMPERR=$(mktemp /tmp/gemini-smart-err-XXXXXX)
STATUS="ok"
ERROR_MSG=""

_cleanup() { rm -f "$TMPOUT" "$TMPERR"; }
trap _cleanup EXIT

# Lance Gemini avec timeout strict
set +e
timeout "$TIMEOUT" gemini --prompt "$PROMPT" --yolo --model "$MODEL" \
  >"$TMPOUT" 2>"$TMPERR"
EXIT=$?
set -e

# Filtrer header YOLO
OUT=$(grep -v "^YOLO mode" "$TMPOUT" 2>/dev/null || true)
ERR=$(cat "$TMPERR" 2>/dev/null || true)

# --- Analyser le résultat ---
if [[ $EXIT -eq 124 ]]; then
  STATUS="hung"
  ERROR_MSG="timeout_${TIMEOUT}s"
elif echo "$ERR$OUT" | grep -qiE "QUOTA_EXHAUSTED|exhausted your capacity|capacity.related"; then
  STATUS="quota"
  ERROR_MSG="quota_exhausted"
elif echo "$ERR$OUT" | grep -qiE "^Error:|UNAVAILABLE|503|overloaded"; then
  STATUS="error"
  ERROR_MSG=$(echo "$ERR" | head -1)
elif [[ $EXIT -ne 0 ]]; then
  STATUS="error"
  ERROR_MSG="exit_$EXIT"
fi

# --- Fallback si nécessaire ---
if [[ "$STATUS" != "ok" ]] && $FALLBACK; then
  case "$STATUS" in
    hung|quota)
      # Pro bloqué → essayer flash
      if [[ "$MODEL" == *pro* ]]; then
        echo "[gemini-pro-${STATUS}→flash]" >&2
        set +e
        timeout "$TIMEOUT_FLASH" gemini --prompt "$PROMPT" --yolo --model "gemini-2.5-flash" \
          >"$TMPOUT" 2>"$TMPERR"
        EXIT=$?
        set -e
        OUT=$(grep -v "^YOLO mode" "$TMPOUT" 2>/dev/null || true)
        ERR=$(cat "$TMPERR" 2>/dev/null || true)
        if [[ $EXIT -eq 0 ]] && ! echo "$OUT" | grep -qiE "QUOTA_EXHAUSTED|Error:"; then
          STATUS="ok"
          MODEL="gemini-2.5-flash"
        fi
      fi
      # Flash aussi bloqué → antigravity → lm-ask
      if [[ "$STATUS" != "ok" ]]; then
        echo "[gemini-quota→antigravity]" >&2
        OUT=$(bash "$SCRIPT_DIR/antigravity-ask.sh" "$PROMPT" 2>/dev/null) || OUT=""
        if [[ -n "$OUT" ]]; then
          STATUS="ok"
          MODEL="antigravity"
        else
          echo "[gemini-quota→lm-ask]" >&2
          OUT=$(bash "$SCRIPT_DIR/lm-ask.sh" "$PROMPT" 2>/dev/null) || OUT=""
          [[ -n "$OUT" ]] && STATUS="ok" && MODEL="lm-local"
        fi
      fi
      ;;
  esac
fi

OUT_LEN=${#OUT}

# --- Log end ---
if $DO_LOG && [[ -n "$SESSION_ID" ]] && command -v gemini_log_end &>/dev/null; then
  gemini_log_end "$SESSION_ID" "$STATUS" "$OUT_LEN" "$ERROR_MSG" 2>/dev/null || true
fi

# --- Output ---
if $JSON_OUT; then
  TS_END=$(date +%s%3N)
  printf '{"output":%s,"status":"%s","model":"%s","via":"%s"}\n' \
    "$(echo "$OUT" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read().rstrip()))' 2>/dev/null || echo '"'"$OUT"'"')" \
    "$STATUS" "$MODEL" "$VIA"
else
  echo "$OUT"
fi

[[ "$STATUS" == "ok" ]] && exit 0 || exit 1
