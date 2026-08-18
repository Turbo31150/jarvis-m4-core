#!/usr/bin/env bash
# antigravity-ask.sh — Fallback antigravity → cluster lm-ask.
SCRIPTS="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROMPT="${*}"

# Tenter Antigravity CLI en mode --print (one-shot non-interactif, sans TTY).
# PIÈGE : `agy ask` est un TUI bubbletea qui exige /dev/tty et plante en non-interactif
# (et écrit son erreur sur stdout) ; `agy -p` / `--print` est le mode one-shot correct.
AGY="$(command -v agy || command -v antigravity-cli || true)"
if [ -n "$AGY" ]; then
  OUT=$(timeout "${AGY_TIMEOUT:-300}" "$AGY" -p "$PROMPT" --print-timeout "${AGY_PRINT_TIMEOUT:-280s}" 2>/dev/null)
  # rejeter les sorties d'erreur du TUI (sinon traitées à tort comme une réponse)
  if [ -n "$OUT" ] && ! printf '%s' "$OUT" | grep -qiE 'CLI error|bubbletea|could not open TTY|/dev/tty'; then
    echo "$OUT"; exit 0
  fi
fi

# Fallback cluster (hub LLM unifié via lm-ask.sh)
exec bash "$SCRIPTS/lm-ask.sh" "$PROMPT"
