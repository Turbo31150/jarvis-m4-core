#!/usr/bin/env bash
# jarvis-daily-harvest.sh — Moisson quotidienne autonome du web, GitHub & actualité IA
set -uo pipefail

LOG="/home/pamerys/jarvis/logs/daily_harvest.log"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Démarrage de la moisson quotidienne..." >> "$LOG"

# 1. Scan GitHub Trending
if [ -f /home/pamerys/jarvis/scripts/github-trending-scan.sh ]; then
  bash /home/pamerys/jarvis/scripts/github-trending-scan.sh >> "$LOG" 2>&1 || true
fi

# 2. Batch de remplissage de la bibliothèque vivante
export LMS_URL="http://127.0.0.1:11434/v1/chat/completions"
export LMS_MODEL="qwen2.5:7b"
python3 /home/pamerys/jarvis/cli/biblio_filler.py --once --batch 3 >> "$LOG" 2>&1 || true

# 3. Optimisation des bases SQLite
for db in /home/pamerys/jarvis/jarvis_master.db /home/pamerys/jarvis/board/board.db /home/pamerys/.claude/bibliotheque/bibliotheque.db; do
  [ -f "$db" ] && sqlite3 "$db" "PRAGMA optimize; PRAGMA wal_checkpoint(TRUNCATE);" >> "$LOG" 2>&1 || true
done

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Moisson quotidienne terminée avec succès." >> "$LOG"
