#!/usr/bin/env bash
# sqlite_vacuum_weekly.sh — VACUUM hebdo des SQLite JARVIS (anti-gonflement espace mort).
# Saute toute base ouverte en écriture (fuser) pour ne rien verrouiller.
LOG=/home/pamerys/jarvis/logs/sqlite_vacuum.log
mkdir -p "$(dirname "$LOG")"
echo "=== $(date '+%F %T') VACUUM run ===" >> "$LOG"
for db in /home/pamerys/jarvis/jarvis_master.db /home/pamerys/jarvis/jarvis.db \
          /home/pamerys/jarvis/cowork_engine.db /home/pamerys/jarvis/data/etoile.db; do
  [ -f "$db" ] || continue
  before=$(du -m "$db" 2>/dev/null | cut -f1)
  if timeout 300 sqlite3 "$db" "PRAGMA busy_timeout=5000; VACUUM;" >>"$LOG" 2>&1; then
    after=$(du -m "$db" 2>/dev/null | cut -f1)
    echo "  OK $db : ${before}M -> ${after}M" >> "$LOG"
  else
    echo "  SKIP/lock $db" >> "$LOG"
  fi
done
