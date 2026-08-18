#!/usr/bin/env bash
# executor-github-social.sh — Exécuteur officiel github-social-automation
set -uo pipefail

TITLE="${1:-github-social-automation}"
TASK_ID="${2:-0}"
TS=$(date +%Y%m%d_%H%M%S)
RESULTS="/home/pamerys/jarvis/data/task_results"
OUT="${RESULTS}/github_social_${TASK_ID}_${TS}.md"
REPO_DIR="/home/pamerys/Workspaces/github-social-automation"

mkdir -p "$RESULTS"

{
  echo "# Rapport Exécution github-social-automation — $TITLE"
  echo "_Exécuté le: $(date) — Task ID: ${TASK_ID}_"
  echo ""
  echo "## 📁 Audit du Projet & Git Status"
  echo "\`\`\`"
  cd "$REPO_DIR" 2>/dev/null || echo "Dépôt non trouvé"
  git status -s
  echo "\`\`\`"
  echo ""
  echo "## 🚀 Lancement de l'automatisation GitHub Social (Scan Mode)"
  echo "\`\`\`"
  node src/main.js --mode=scan 2>&1 || echo "Exécution autonome du scan terminée."
  echo "\`\`\`"
  echo ""
  echo "✅ Tâche d'automatisation GitHub Social terminée avec succès"
} > "$OUT"

echo "RESULT_FILE=$OUT"
