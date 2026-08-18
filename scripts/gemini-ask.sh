#!/usr/bin/env bash
# gemini-ask.sh — appel non interactif à Gemini CLI (OAuth Google One, 0 token facturé).
#
# Corrigé le 2026-08-14. Trois défauts réparés :
#   1. le binaire était codé en dur sur /home/pamerys/... — chemin mort depuis la migration
#      vers /home/pamerys. Il est maintenant RÉSOLU dynamiquement.
#   2. un « || echo "Inférence exécutée avec succès" » transformait tout échec en faux
#      succès : l'appelant croyait avoir une réponse alors qu'il n'avait rien. Supprimé.
#      En cas d'échec on écrit sur stderr et on sort en code non nul.
#   3. --yolo est refusé quand ~/.gemini/settings.json porte un defaultApprovalMode
#      invalide. La config a été corrigée ('yolo' -> 'auto_edit').
#
# Usage : gemini-ask.sh "question"          → modèle par défaut
#         gemini-ask.sh --flash "question"  → modèle rapide
set -uo pipefail

GEMINI_BIN="${GEMINI_BIN:-}"
if [ -z "$GEMINI_BIN" ]; then
  GEMINI_BIN="$(command -v gemini 2>/dev/null || true)"
fi
if [ -z "$GEMINI_BIN" ] || [ ! -x "$GEMINI_BIN" ]; then
  for c in "$HOME/.local/bin/gemini" /usr/local/bin/gemini; do
    [ -x "$c" ] && GEMINI_BIN="$c" && break
  done
fi
if [ -z "$GEMINI_BIN" ] || [ ! -x "$GEMINI_BIN" ]; then
  echo "gemini-ask: binaire gemini introuvable (PATH, ~/.local/bin, /usr/local/bin)" >&2
  exit 127
fi

MODELE=(-m gemini-3.7-flash)
if [ "${1:-}" = "--flash" ] || [ "${1:-}" = "--3.7" ]; then
  MODELE=(-m gemini-3.7-flash)
  shift
elif [ "${1:-}" = "--lite" ] || [ "${1:-}" = "--3.5" ]; then
  MODELE=(-m gemini-3.5-flash-lite)
  shift
elif [ "${1:-}" = "--pro" ] || [ "${1:-}" = "--3.1" ]; then
  MODELE=(-m gemini-3.1-pro-preview)
  shift
fi

PROMPT="${1:-}"
if [ -z "$PROMPT" ]; then
  echo "gemini-ask: prompt vide" >&2
  exit 2
fi

SORTIE=$("$GEMINI_BIN" -p "$PROMPT" "${MODELE[@]}" -o text 2>&1)
CODE=$?

# Une sortie vide ou un code non nul est un ÉCHEC — on ne le maquille pas en succès.
if [ $CODE -ne 0 ] || [ -z "${SORTIE//[[:space:]]/}" ]; then
  echo "gemini-ask: échec (code=$CODE)" >&2
  [ -n "$SORTIE" ] && echo "$SORTIE" >&2
  exit 1
fi

printf '%s\n' "$SORTIE"
