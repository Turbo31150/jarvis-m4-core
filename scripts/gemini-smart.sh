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

# --- Headless : gemini-cli 0.47 bloque (RC=55) hors dossier "trusted" en non-interactif.
# Auth = api-key (~/.gemini/.env GEMINI_API_KEY) ; on lève la barrière trust pour MCP/cron/scripts.
# cf. https://geminicli.com/docs/cli/trusted-folders/#headless-and-automated-environments
export GEMINI_CLI_TRUST_WORKSPACE=true

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
    --pro)         MODEL="gemini-3.1-pro-preview"; shift ;;
    --flash)       MODEL="gemini-3.7-flash"; shift ;;
    --lite)        MODEL="gemini-3.5-flash-lite"; shift ;;
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
PROMPT="${PROMPT#"${PROMPT%%[![:space:]]*}"}"  # trim leading
PROMPT="${PROMPT%"${PROMPT##*[![:space:]]}"}"   # trim trailing (préserve espaces internes)
if [[ -z "$PROMPT" ]]; then
  echo "Usage: gemini-smart.sh [--short|--long|--flash|--pro|--lite] \"prompt\"" >&2
  exit 1
fi

PROMPT_LEN=${#PROMPT}

# --- Auto-select model / timeout ---
if [[ -z "$MODEL" ]]; then
  if $FORCE_LONG || [[ $PROMPT_LEN -gt 800 ]]; then
    MODEL="gemini-3.1-pro-preview"
    # Dégrader vers flash si l'heure courante a un mauvais historique
    HOUR_QUALITY=$(gemini_best_hours 2>/dev/null || echo "unknown")
    if [[ "$HOUR_QUALITY" == "bad" ]]; then
      MODEL="gemini-3.7-flash"
      echo "[gemini-smart] heure défavorable→flash" >&2
    fi
  else
    MODEL="gemini-3.7-flash"
  fi
fi
$FORCE_LONG && MODEL="gemini-3.1-pro-preview"
$FORCE_SHORT && MODEL="gemini-3.5-flash-lite"

[[ "$MODEL" == *pro* ]] && TIMEOUT=$TIMEOUT_PRO || TIMEOUT=$TIMEOUT_FLASH

# --- SÉCURITÉ : --yolo (auto-approve outils) seulement pour prompts de confiance ---
# Les sources réseau (lumen/whisperflow/telegram/linkedin/cli-stdin) sont NON fiables :
# auto-exécuter des outils sur un prompt distant = bypass de permission (escalade).
# Seul l'opérateur local (--via direct|cli) ou GEMINI_TRUSTED_PROMPT=1 active --yolo.
case "$VIA" in
  direct|cli) TRUSTED=1 ;;
  *)          TRUSTED=0 ;;
esac
[[ "${GEMINI_TRUSTED_PROMPT:-0}" == "1" ]] && TRUSTED=1
if [[ "$TRUSTED" == "1" ]]; then
  YOLO_FLAG=(--yolo)
else
  YOLO_FLAG=()
  echo "[gemini-smart] --via=$VIA non fiable → --yolo désactivé (sécurité, pas d'auto-exec d'outils)" >&2
fi

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
timeout --kill-after=10 "$TIMEOUT" gemini --prompt "$PROMPT" "${YOLO_FLAG[@]}" --model "$MODEL" \
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
elif echo "$ERR$OUT" | grep -qiE "QUOTA_EXHAUSTED|RESOURCE_EXHAUSTED|exhausted your capacity|No capacity available|capacity.related|\b429\b"; then
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
    hung|quota|error)
      # Flash bloqué (429 / No capacity) → essayer pro (capacité distincte côté Google)
      if [[ "$MODEL" == *flash* ]]; then
        echo "[gemini-flash-${STATUS}→pro]" >&2
        set +e
        timeout --kill-after=10 "$TIMEOUT_PRO" gemini --prompt "$PROMPT" "${YOLO_FLAG[@]}" --model "gemini-3.1-pro-preview" \
          >"$TMPOUT" 2>"$TMPERR"
        EXIT=$?
        set -e
        OUT=$(grep -v "^YOLO mode" "$TMPOUT" 2>/dev/null || true)
        ERR=$(cat "$TMPERR" 2>/dev/null || true)
        if [[ $EXIT -eq 0 ]] && ! echo "$ERR$OUT" | grep -qiE "QUOTA_EXHAUSTED|No capacity available|Error:"; then
          STATUS="ok"
          MODEL="gemini-3.1-pro-preview"
        fi
      fi
      # Pro bloqué → essayer flash
      if [[ "$STATUS" != "ok" && "$MODEL" == *pro* ]]; then
        echo "[gemini-pro-${STATUS}→flash]" >&2
        set +e
        timeout --kill-after=10 "$TIMEOUT_FLASH" gemini --prompt "$PROMPT" "${YOLO_FLAG[@]}" --model "gemini-3.7-flash" \
          >"$TMPOUT" 2>"$TMPERR"
        EXIT=$?
        set -e
        OUT=$(grep -v "^YOLO mode" "$TMPOUT" 2>/dev/null || true)
        ERR=$(cat "$TMPERR" 2>/dev/null || true)
        if [[ $EXIT -eq 0 ]] && ! echo "$ERR$OUT" | grep -qiE "QUOTA_EXHAUSTED|No capacity available|Error:"; then
          STATUS="ok"
          MODEL="gemini-3.7-flash"
        fi
      fi
      # Tout Gemini bloqué → antigravity → lm-ask (cluster local)
      if [[ "$STATUS" != "ok" ]]; then
        echo "[gemini-${STATUS}→antigravity]" >&2
        OUT=$(bash "$SCRIPT_DIR/antigravity-ask.sh" "$PROMPT" 2>/dev/null) || OUT=""
        if [[ -n "$OUT" ]]; then
          STATUS="ok"
          MODEL="antigravity"
        else
          echo "[gemini-${STATUS}→lm-ask]" >&2
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
