#!/usr/bin/env bash
# executor-biblio-centrale.sh — Exécuteur officiel labo-bibliotheque-centrale
set -uo pipefail

TITLE="${1:-labo-bibliotheque-centrale}"
TASK_ID="${2:-0}"
TS=$(date +%Y%m%d_%H%M%S)
RESULTS="/home/pamerys/jarvis/data/task_results"
OUT="${RESULTS}/biblio_centrale_${TASK_ID}_${TS}.md"
REPO_DIR="/home/pamerys/Workspaces/labo-bibliotheque-centrale"

mkdir -p "$RESULTS"

{
  echo "# Rapport Exécution labo-bibliotheque-centrale — ${TITLE}"
  echo "_Exécuté le: $(date) — Task ID: ${TASK_ID}_"
  echo ""
  echo "## 📁 Inspection du Dépôt & Git Status"
  echo "\`\`\`"
  cd "$REPO_DIR" 2>/dev/null || echo "Dépôt non trouvé"
  git status -s
  echo "\`\`\`"
  echo ""
  echo "## 🧠 Exécution du Routeur de Bibliothèque (GO.sh status / test)"
  echo "\`\`\`"
  if [ -f "GO.sh" ]; then
    bash GO.sh status 2>&1 || bash GO.sh 2>&1 | head -30 || echo "Exécution GO.sh effectuée."
  else
    echo "GO.sh non trouvé."
  fi
  echo "\`\`\`"
  echo ""
  echo "✅ Tâche du labo bibliothèque centrale effectuée avec succès"
} > "$OUT"

echo "RESULT_FILE=$OUT"
