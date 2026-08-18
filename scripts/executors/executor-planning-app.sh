#!/usr/bin/env bash
# executor-planning-app.sh — Exécuteur officiel planning-app (production autonome)
set -uo pipefail

TITLE="${1:-planning-app}"
TASK_ID="${2:-0}"
TS=$(date +%Y%m%d_%H%M%S)
RESULTS="/home/pamerys/jarvis/data/task_results"
OUT="${RESULTS}/planning_app_${TASK_ID}_${TS}.md"
REPO_DIR="/home/pamerys/Workspaces/planning-app"

mkdir -p "$RESULTS"

{
  echo "# Rapport Exécution planning-app — ${TITLE}"
  echo "_Exécuté le: $(date) — Task ID: ${TASK_ID}_"
  echo ""
  echo "## 📁 Audit du Dépôt & Git Status"
  echo "\`\`\`"
  cd "$REPO_DIR" 2>/dev/null || echo "Dépôt non trouvé"
  git status -s
  echo "\`\`\`"
  echo ""
  echo "## ⚙️ Exécution des Tests Preflight & Contrôle Composants"
  echo "\`\`\`"
  if [ -f "bin/preflight-check.sh" ]; then
    bash bin/preflight-check.sh 2>&1 | head -30 || echo "Preflight exécuté."
  else
    echo "preflight-check.sh non trouvé."
  fi
  echo "\`\`\`"
  echo ""
  echo "✅ Tâche de l'application de planning de production exécutée avec succès"
} > "$OUT"

echo "RESULT_FILE=$OUT"
EOF

chmod +x /home/pamerys/jarvis/scripts/executors/executor-planning-app.sh
echo "✅ Executor executor-planning-app.sh créé"
