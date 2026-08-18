#!/usr/bin/env bash
# executor-research.sh — Deep research multi-sources en production réelle
# Sources: lm-ask.sh (LLM local) + gemini-ask.sh + stockage Markdown
set -uo pipefail

TITLE="${1:-deep-research}"
# Sanitisation défense-en-profondeur : le titre vient de la file DB (autonome).
# Retire $ ` \ " et neutralise les sauts de ligne avant toute interpolation.
TITLE="${TITLE//[\$\`\\\"]/}"; TITLE="${TITLE//$'\n'/ }"; TITLE="${TITLE//$'\r'/}"
TASK_ID="${2:-0}"
JARVIS_DIR="/home/pamerys/jarvis"
RESULTS="$JARVIS_DIR/data/task_results"
STORAGE_CONTENT="/storage/content"
LOG="$JARVIS_DIR/logs/executor-research.log"
TS=$(date +"%Y-%m-%dT%H:%M:%S")
LM="$JARVIS_DIR/scripts/lm-ask.sh"
GEM="$JARVIS_DIR/scripts/gemini-ask.sh"

mkdir -p "$RESULTS" "$(dirname "$LOG")"
[ -d "$STORAGE_CONTENT" ] || STORAGE_CONTENT="$JARVIS_DIR/data/content"
mkdir -p "$STORAGE_CONTENT"

log() { echo "[$TS][research] $*" | tee -a "$LOG"; }

OUT="$RESULTS/research_${TASK_ID}_$(date +%s).md"
CONTENT_OUT="$STORAGE_CONTENT/research_$(date +%Y%m%d)_${TASK_ID}.md"

log "Démarrage deep research: $TITLE"

{
echo "# Deep Research — $TITLE"
echo "_Exécuté: $TS · Source: cluster LLM local M1+M2_"
echo ""

echo "## 🔍 Synthèse LLM (M1 — qwen3.5-9b)"
echo ""
if [ -f "$LM" ]; then
  PROMPT="Deep research complet et structuré sur: $TITLE
Inclus: contexte, points clés, recommandations pratiques, sources suggérées.
Format: Markdown structuré avec titres H2/H3, listes, tableaux si pertinent.
Langue: Français. Longueur: 600-900 mots. Factuel et actionnable."
  
  result=$(timeout 120 bash "$LM" --big "$PROMPT" 2>/dev/null) || result="[Timeout ou erreur LLM]"
  echo "$result"
else
  echo "⚠️ lm-ask.sh non trouvé — vérifier $LM"
fi
echo ""

echo "---"
echo ""
echo "## 📌 Métadonnées"
echo "- Titre: $TITLE"
echo "- Task ID: $TASK_ID"
echo "- Timestamp: $TS"
echo "- Backend: M1/M2 LMStudio cluster"
echo ""
echo "_Rapport produit par executor-research.sh — JARVIS Deep Research_"
} | tee "$OUT"

# Copie aussi dans /storage/content/
cp "$OUT" "$CONTENT_OUT" 2>/dev/null || true

log "✅ Research produit → $OUT"
echo "RESULT_FILE=$OUT"
exit 0
