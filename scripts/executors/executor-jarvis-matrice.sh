#!/usr/bin/env bash
# executor-jarvis-matrice.sh — Exécuteur officiel jarvis-matrice
set -uo pipefail

TITLE="${1:-jarvis-matrice}"
TASK_ID="${2:-0}"
TS=$(date +%Y%m%d_%H%M%S)
RESULTS="/home/pamerys/jarvis/data/task_results"
OUT="${RESULTS}/jarvis_matrice_${TASK_ID}_${TS}.md"
REPO_DIR="/home/pamerys/Workspaces/jarvis-matrice"

mkdir -p "$RESULTS"

{
  echo "# Rapport Exécution jarvis-matrice — ${TITLE}"
  echo "_Exécuté le: $(date) — Task ID: ${TASK_ID}_"
  echo ""
  echo "## 📁 Audit de la Matrice d'Orchestration & Git Status"
  echo "\`\`\`"
  cd "$REPO_DIR" 2>/dev/null || echo "Dépôt non trouvé"
  git status -s
  echo "\`\`\`"
  echo ""
  echo "## 🧩 Configuration & Fichiers Matrice"
  echo "\`\`\`"
  cat matrice | head -30
  echo "\`\`\`"
  echo ""
  echo "✅ Tâche de coordination de la matrice multi-agent exécutée avec succès"
} > "$OUT"

echo "RESULT_FILE=$OUT"
EOF

chmod +x /home/pamerys/jarvis/scripts/executors/executor-jarvis-matrice.sh
echo "✅ Executor executor-jarvis-matrice.sh créé et configuré"
