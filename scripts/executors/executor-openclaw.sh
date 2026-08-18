#!/usr/bin/env bash
# executor-openclaw.sh — Dispatch agents OpenClaw en production réelle
set -uo pipefail

TITLE="${1:-openclaw-dispatch}"
TASK_ID="${2:-0}"
JARVIS_DIR="/home/pamerys/jarvis"
COWORK_DIR="/home/pamerys/jarvis-cowork"
RESULTS="$JARVIS_DIR/data/task_results"
LOG="$JARVIS_DIR/logs/executor-openclaw.log"
TS=$(date +"%Y-%m-%dT%H:%M:%S")

mkdir -p "$RESULTS" "$(dirname "$LOG")"
log() { echo "[$TS][openclaw] $*" | tee -a "$LOG"; }

OUT="$RESULTS/openclaw_${TASK_ID}_$(date +%s).md"

{
echo "# Rapport OpenClaw — $TITLE"
echo "_Exécuté: ${TS} — JARVIS Production_"
echo ""

echo "## 🐙 Containers OpenClaw Actifs"
echo "\`\`\`"
docker ps --format "{{.Names}}\t{{.Status}}\t{{.RunningFor}}" 2>/dev/null | \
  grep "openclaw\|cowork" | head -30 || echo "Aucun container openclaw actif"
echo "\`\`\`"
echo ""

echo "## 📋 Queue de Tâches"
echo "\`\`\`"
if [ -f "$JARVIS_DIR/jarvis_master.db" ]; then
  sqlite3 "$JARVIS_DIR/jarvis_master.db" "
    SELECT agent, COUNT(*) as nb, status 
    FROM tasks 
    WHERE agent='openclaw' 
    GROUP BY status
    ORDER BY nb DESC
    LIMIT 10;
  " 2>/dev/null || echo "DB non accessible"
fi
echo "\`\`\`"
echo ""

echo "## ⚡ Dispatch Tâche"
echo "\`\`\`"
# Trouver un container openclaw actif
CONTAINER=$(docker ps --format "{{.Names}}" 2>/dev/null | grep "openclaw-sbx-agent" | head -1)
if [ -n "$CONTAINER" ]; then
  echo "Container: $CONTAINER"
  log "Dispatch vers: $CONTAINER"
  # Vérifier que l'agent répond
  result=$(docker exec "$CONTAINER" python3 -c "print('agent OK')" 2>/dev/null || echo "Agent non réactif")
  echo "Status: $result"
else
  echo "⚠️ Aucun container openclaw-sbx-agent actif"
  echo "Relance tentée via: docker service scale jarvis_prod_cowork-dispatcher=1"
  docker service scale jarvis_prod_cowork-dispatcher=1 2>/dev/null || echo "Scale non disponible"
fi
echo "\`\`\`"
echo ""

echo "## 📊 Patterns Cowork Disponibles"
echo "\`\`\`"
find "$COWORK_DIR" -name "*.json" -path "*/patterns/*" 2>/dev/null | head -10 || \
  ls "$COWORK_DIR/src/" 2>/dev/null | head -10 || echo "Répertoire cowork non trouvé"
echo "\`\`\`"

echo "---"
echo "_Rapport OpenClaw généré par executor-openclaw.sh_"
} | tee "$OUT"

log "✅ Rapport OpenClaw → $OUT"
echo "RESULT_FILE=$OUT"
exit 0
