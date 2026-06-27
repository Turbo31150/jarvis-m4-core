#!/bin/bash
# PID Monitor JARVIS — enregistre les PIDs clés et met à jour last_seen
LOG="/tmp/jarvis_logs/M1_pids.jsonl"
DB="/home/pamerys/jarvis/data/etoile.db"
TS=$(date -u +%Y-%m-%dT%H:%M:%S)
mkdir -p /tmp/jarvis_logs

declare -A SVCS=(
  ["ollama"]="ollama"
  ["cowork-loop"]="jarvis-cowork"
  ["domino"]="jarvis-domino"
  ["redis"]="redis-server"
)

for SVC in "${!SVCS[@]}"; do
  PATTERN="${SVCS[$SVC]}"
  PID=$(pgrep -f "$PATTERN" 2>/dev/null | head -1)
  STATUS="up"
  RAM_MB=0
  if [ -z "$PID" ]; then
    STATUS="down"
  else
    RAM_MB=$(ps -o rss= -p "$PID" 2>/dev/null | awk '{printf "%d", $1/1024}')
  fi
  echo "{\"ts\":\"$TS\",\"machine\":\"M1\",\"svc\":\"$SVC\",\"pid\":${PID:-0},\"ram_mb\":$RAM_MB,\"status\":\"$STATUS\"}" >> "$LOG"
done

# Update last_seen M1 dans etoile.db
python3 -c "
import sqlite3
conn = sqlite3.connect('$DB')
conn.execute(\"UPDATE jarvis_cluster_nodes SET last_seen=datetime('now'), status='up' WHERE alias='M1'\")
conn.commit()
conn.close()
" 2>/dev/null

tail -4 "$LOG"
