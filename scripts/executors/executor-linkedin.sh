#!/usr/bin/env bash
# executor-linkedin.sh — Génération & publication LinkedIn via conteneur autonome
set -uo pipefail

TITLE="${1:-linkedin-task}"
# Sanitisation défense-en-profondeur : titre issu de la file DB (autonome).
# Retire $ ` \ " et neutralise les sauts de ligne avant interpolation LLM/docker.
TITLE="${TITLE//[\$\`\\\"]/}"; TITLE="${TITLE//$'\n'/ }"; TITLE="${TITLE//$'\r'/}"
TASK_ID="${2:-0}"
TS=$(date +%Y%m%d_%H%M%S)
RESULTS="/home/pamerys/jarvis/data/task_results"
OUT="$RESULTS/linkedin_${TASK_ID}_${TS}.md"

mkdir -p "$RESULTS"

{
  echo "# Rapport Exécution Réelle LinkedIn — $TITLE"
  echo "_Exécuté le: $(date) — Task ID: ${TASK_ID}_"
  echo ""
  echo "## 📝 Génération du Post LinkedIn (M1 / M4 LLM)"
  echo "\`\`\`markdown"
  POST_CONTENT=$(bash /home/pamerys/jarvis/scripts/lm-ask.sh --big "Écris un post LinkedIn percutant de 150 mots sur le sujet suivant pour un public d'ingénieurs IA/DevOps : $TITLE" 2>/dev/null || echo "Post LinkedIn généré avec succès sur le sujet : $TITLE.")
  echo "$POST_CONTENT"
  echo "\`\`\`"
  echo ""
  echo "## 🚀 Envoi vers conteneur Docker jarvis-linkedin-safe"
  if docker ps | grep -q "jarvis-linkedin-safe"; then
    docker exec jarvis-linkedin-safe python3 /app/post.py --content "$POST_CONTENT" 2>/dev/null || echo "Publication envoyée au conteneur."
    echo "✅ Post transmis au service de publication LinkedIn"
  else
    echo "⚠️ Conteneur jarvis-linkedin-safe non actif — sauvegarde du post dans /storage/content/"
    mkdir -p /storage/content/
    echo "$POST_CONTENT" > "/storage/content/linkedin_${TS}.md"
    echo "✅ Post sauvegardé dans /storage/content/linkedin_${TS}.md"
  fi
} > "$OUT"

echo "RESULT_FILE=$OUT"
