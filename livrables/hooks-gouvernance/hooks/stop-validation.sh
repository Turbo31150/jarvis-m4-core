#!/usr/bin/env bash
# stop-validation.sh — hook Stop : validation LÉGÈRE et NON BLOQUANTE de fin de tâche.
# Rôle : rappeler (sans jamais bloquer) s'il reste des TODO ouverts ou des fichiers
# modifiés récemment sans test associé. Écrit un journal, puis rend la main.
#
# ═══ CONTRAT FAIL-SAFE (règle dure de ce poste) ═══
#   - Ne renvoie JAMAIS {"decision":"block"} → aucune boucle « Operation stopped by hook ».
#   - Sort TOUJOURS en exit 0, même sur erreur, DB absente, jq manquant, timeout.
#   - Anti-réentrance : si le hook a déjà tourné il y a < GARDE_S secondes, il se tait.
#   - Respecte stop_hook_active : si Claude continue déjà à cause d'un Stop hook, on sort net.
#   - 0-token : pur bash, aucune inférence LLM facturée.
# Sortie possible : '{}' (silencieux) OU {"systemMessage":"…"} (rappel visible, non bloquant).
set -uo pipefail

LOG="${HOME}/.claude/hooks/stop-validation.log"
STATE="${HOME}/.claude/hooks/.stop-validation-state"
GARDE_S=8          # fenêtre anti-réentrance (secondes)
MAX_LOG=500        # lignes de log conservées (rotation douce)

# Émet '{}' et sort proprement — voie de sortie par défaut, toujours sûre.
emit_empty() { echo '{}'; exit 0; }

# Toute erreur non gérée = laisser passer (jamais bloquer).
trap 'emit_empty' ERR

mkdir -p "$(dirname "$LOG")" 2>/dev/null || true

# 1. Lire l'entrée JSON du harnais (best-effort).
INPUT="$(cat 2>/dev/null || true)"

# 2. ANTI-LOOP #1 — si on est déjà relancé par un Stop hook, ne rien faire.
if command -v jq >/dev/null 2>&1; then
  ACTIVE="$(printf '%s' "$INPUT" | jq -r '.stop_hook_active // false' 2>/dev/null || echo false)"
  [ "$ACTIVE" = "true" ] && emit_empty
fi

# 3. ANTI-LOOP #2 — anti-réentrance temporelle (évite le martèlement).
NOW=$(date +%s 2>/dev/null || echo 0)
if [ -f "$STATE" ]; then
  LAST=$(cat "$STATE" 2>/dev/null || echo 0)
  case "$LAST" in (*[!0-9]*|'') LAST=0 ;; esac
  if [ "$NOW" -gt 0 ] && [ $((NOW - LAST)) -lt "$GARDE_S" ] 2>/dev/null; then
    emit_empty
  fi
fi
echo "$NOW" > "$STATE" 2>/dev/null || true

# 4. Vérifications LÉGÈRES (déterministes, bornées, best-effort).
RAPPELS=""

# 4a. TODO ouverts dans la todolist synchronisée (si présente).
TODO_FILE="${HOME}/.claude/JARVIS_TASKS.md"
if [ -r "$TODO_FILE" ]; then
  NB_TODO=$(grep -cE '^- \[ \]' "$TODO_FILE" 2>/dev/null || echo 0)
  case "$NB_TODO" in (*[!0-9]*|'') NB_TODO=0 ;; esac
  [ "$NB_TODO" -gt 0 ] && RAPPELS="${RAPPELS}${NB_TODO} TODO ouvert(s) dans JARVIS_TASKS.md. "
fi

# 4b. Fichiers Python modifiés < 10 min dans le cwd, sans test évident.
#     Recherche bornée (profondeur 3, exclusions), silencieuse, jamais fatale.
CWD="$(printf '%s' "$INPUT" | (command -v jq >/dev/null 2>&1 && jq -r '.cwd // empty' 2>/dev/null || true))"
[ -n "${CWD:-}" ] && [ -d "$CWD" ] || CWD="$PWD"
if [ -d "$CWD" ]; then
  MODIFS=$(find "$CWD" -maxdepth 3 -type f -name '*.py' -mmin -10 \
             -not -path '*/.git/*' -not -path '*/node_modules/*' \
             -not -path '*/__pycache__/*' -not -name 'test_*' -not -name '*_test.py' \
             2>/dev/null | head -20 || true)
  if [ -n "$MODIFS" ]; then
    SANS_TEST=0
    while IFS= read -r f; do
      [ -n "$f" ] || continue
      base="$(basename "$f" .py)"
      dir="$(dirname "$f")"
      # Un test « évident » = test_<base>.py ou <base>_test.py à proximité (cwd, dir, tests/).
      if ! find "$CWD" -maxdepth 3 -type f \
             \( -name "test_${base}.py" -o -name "${base}_test.py" \) 2>/dev/null | grep -q . ; then
        SANS_TEST=$((SANS_TEST + 1))
      fi
    done <<< "$MODIFS"
    [ "$SANS_TEST" -gt 0 ] && RAPPELS="${RAPPELS}${SANS_TEST} fichier(s) .py modifié(s) sans test associé. "
  fi
fi

# 5. Journaliser (rotation douce), puis rendre la main SANS bloquer.
TS="$(date -Is 2>/dev/null || echo '?')"
if [ -n "$RAPPELS" ]; then
  echo "${TS}	RAPPEL	${RAPPELS}" >> "$LOG" 2>/dev/null || true
else
  echo "${TS}	OK	rien à signaler" >> "$LOG" 2>/dev/null || true
fi
# Rotation : garder au plus MAX_LOG lignes.
if [ -f "$LOG" ]; then
  LINES=$(wc -l < "$LOG" 2>/dev/null || echo 0)
  case "$LINES" in (*[!0-9]*|'') LINES=0 ;; esac
  if [ "$LINES" -gt "$MAX_LOG" ] 2>/dev/null; then
    tail -n "$MAX_LOG" "$LOG" > "${LOG}.tmp" 2>/dev/null && mv "${LOG}.tmp" "$LOG" 2>/dev/null || true
  fi
fi

# 6. Rappel VISIBLE mais NON bloquant (systemMessage) — ou silence.
#    On n'émet JAMAIS decision:block. Claude peut s'arrêter normalement.
if [ -n "$RAPPELS" ] && command -v jq >/dev/null 2>&1; then
  MSG="Validation fin de tâche (non bloquant) : ${RAPPELS}"
  jq -cn --arg m "$MSG" '{systemMessage:$m}' 2>/dev/null || emit_empty
  exit 0
fi
emit_empty
