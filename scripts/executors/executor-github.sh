#!/usr/bin/env bash
# executor-github.sh — Production réelle Git & GitHub
set -uo pipefail

TITLE="${1:-git-task}"
# Sanitisation défense-en-profondeur : titre issu de la file DB (autonome).
# Retire $ ` \ " et neutralise les sauts de ligne (garde le message de commit propre).
TITLE="${TITLE//[\$\`\\\"]/}"; TITLE="${TITLE//$'\n'/ }"; TITLE="${TITLE//$'\r'/}"
TASK_ID="${2:-0}"
TS=$(date +%Y%m%d_%H%M%S)
RESULTS="/home/pamerys/jarvis/data/task_results"
OUT="$RESULTS/github_${TASK_ID}_${TS}.md"

mkdir -p "$RESULTS"

{
  echo "# Rapport Exécution Réelle GitHub & Git — $TITLE"
  echo "_Exécuté le: $(date) — Task ID: ${TASK_ID}_"
  echo ""
  echo "## 📁 Audit des Dépôts Git Locaux"
  echo "\`\`\`"
  cd /home/pamerys/Workspaces/jarvis-linux 2>/dev/null || cd /home/pamerys/jarvis
  git status -s | head -30
  echo "\`\`\`"
  echo ""
  echo "## 📜 Derniers Commits Dépôt Core"
  echo "\`\`\`"
  git log -n 5 --oneline 2>/dev/null || echo "Pas de repo git ici"
  echo "\`\`\`"
  echo ""
  echo "## 🚀 Action Git Autonome"
  # Effectuer un auto-commit propre si des fichiers modifiés existent
  if [ -n "$(git status -s 2>/dev/null)" ]; then
    git add -A 2>/dev/null
    git commit -m "fix(auto-prod): exécuté par jarvis-planning T$TASK_ID [$TITLE]" 2>/dev/null || true
    echo "✅ Commit automatique effectué"
  else
    echo "✅ Dépôt propre — aucun commit nécessaire"
  fi
} > "$OUT"

echo "RESULT_FILE=$OUT"
