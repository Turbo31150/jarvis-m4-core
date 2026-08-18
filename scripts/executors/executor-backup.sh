#!/usr/bin/env bash
# executor-backup.sh — Backup rotatif SQLite + Docker volumes en production réelle
# Cible: /storage/backups/ (Samsung 870 EVO)
set -uo pipefail

TITLE="${1:-backup-rotate}"
TASK_ID="${2:-0}"
JARVIS_DIR="/home/pamerys/jarvis"
STORAGE="/storage/backups"
RESULTS="$JARVIS_DIR/data/task_results"
LOG="$JARVIS_DIR/logs/executor-backup.log"
TS=$(date +"%Y-%m-%dT%H:%M:%S")
DATE=$(date +"%Y%m%d_%H%M%S")

mkdir -p "$RESULTS" "$(dirname "$LOG")"
log() { echo "[$TS][backup] $*" | tee -a "$LOG"; }

# Fallback si /storage non monté
[ -d "$STORAGE" ] || STORAGE="/home/pamerys/jarvis/backups"
mkdir -p "$STORAGE"

OUT="$RESULTS/backup_${TASK_ID}_$(date +%s).md"

{
echo "# Rapport Backup — $TITLE"
echo "_Exécuté: ${TS} — JARVIS Production_"
echo ""

echo "## 💾 Backup SQLite"
echo "\`\`\`"
DBS=(
  "$JARVIS_DIR/jarvis_master.db"
  "$JARVIS_DIR/jarvis_logs.db"
  "$JARVIS_DIR/cowork_engine.db"
)
for db in "${DBS[@]}"; do
  if [ -f "$db" ]; then
    name=$(basename "$db" .db)
    dest="$STORAGE/${name}_${DATE}.db.gz"
    sqlite3 "$db" ".dump" 2>/dev/null | gzip -9 > "$dest" && \
      printf "✅ %-30s → %s (%s)\n" "$name" "$dest" "$(du -h "$dest" | cut -f1)" || \
      printf "❌ %-30s ÉCHEC\n" "$name"
  else
    printf "⏭️  %-30s non trouvé\n" "$(basename "$db")"
  fi
done
echo "\`\`\`"
echo ""

echo "## 🔄 Rotation (garde 7 jours)"
echo "\`\`\`"
find "$STORAGE" -name "*.db.gz" -mtime +7 -delete -print 2>/dev/null | head -10 || echo "Aucun fichier expiré"
echo "\`\`\`"
echo ""

echo "## 🐳 Docker Volumes Critiques"
echo "\`\`\`"
VOL_DIR="$STORAGE/docker_${DATE}"
mkdir -p "$VOL_DIR"
VOLUMES_TO_BACKUP=(jarvis_postgres_data jarvis_redis_data jarvis_n8n_data)
for vol in "${VOLUMES_TO_BACKUP[@]}"; do
  if docker volume inspect "$vol" &>/dev/null; then
    dest="$VOL_DIR/${vol}.tar.gz"
    docker run --rm -v "$vol":/data -v "$VOL_DIR":/backup \
      alpine tar czf "/backup/${vol}.tar.gz" -C /data . 2>/dev/null && \
      printf "✅ %s → %s\n" "$vol" "$dest" || \
      printf "❌ %s ÉCHEC\n" "$vol"
  else
    printf "⏭️  %s non trouvé\n" "$vol"
  fi
done
echo "\`\`\`"
echo ""

echo "## 📊 Espace Backup"
echo "\`\`\`"
du -sh "$STORAGE" 2>/dev/null
df -h "$STORAGE" 2>/dev/null | tail -1
echo "\`\`\`"

echo "---"
echo "_Rapport backup généré par executor-backup.sh_"
} | tee "$OUT"

log "✅ Rapport backup → $OUT"
echo "RESULT_FILE=$OUT"
exit 0
