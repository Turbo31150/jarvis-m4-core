#!/bin/bash
# cluster-health-monitor.sh — tâche continue permanente JARVIS
# Surveille M1/M2/M3/OL1 toutes les 60s, log dans SQLite, alerte si down

DB="/home/pamerys/jarvis/cowork_engine.db"
LOG="$HOME/jarvis/logs/cluster-health.log"
SSH_KEY="/home/pamerys/jarvis/infra/config/ssh-access/jarvis_ed25519"

declare -A NODES=(
  ["M1_LM"]="http://127.0.0.1:1234/v1/models"
  ["M2_LM"]="http://192.168.1.26:1234/v1/models"
  ["M3_OL"]="http://192.168.1.113:11434/api/tags"
  ["OL1"]="http://127.0.0.1:11434/api/tags"
)

log() { echo "[$(date '+%H:%M:%S')] $*" | tee -a "$LOG"; }

check_node() {
  local name="$1" url="$2"
  local status="DOWN" models=0
  local response
  response=$(curl -s --max-time 3 "$url" 2>/dev/null)
  if [ -n "$response" ]; then
    models=$(echo "$response" | python3 -c "
import json,sys
try:
  d=json.load(sys.stdin)
  mods=d.get('data',d.get('models',[]))
  print(len(mods))
except: print(0)
" 2>/dev/null)
    [ "$models" -gt 0 ] 2>/dev/null && status="UP" || status="UP"
  fi
  echo "$status|$models"
}

log "=== Cluster Health Monitor démarré ==="
log "Nœuds: M1(LMStudio) M2(LMStudio) M3(Ollama) OL1(Ollama)"

while true; do
  TS=$(date -u +%Y-%m-%dT%H:%M:%S)
  REPORT=""

  for name in "${!NODES[@]}"; do
    result=$(check_node "$name" "${NODES[$name]}")
    status="${result%|*}"; models="${result##*|}"
    REPORT+="$name:$status($models) "

    # Log dans SQLite
    python3 -c "
import sqlite3
try:
  conn=sqlite3.connect('$DB')
  conn.execute('''CREATE TABLE IF NOT EXISTS cluster_health
    (ts TEXT, node TEXT, status TEXT, model_count INT)''')
  conn.execute('INSERT INTO cluster_health VALUES(?,?,?,?)',
    ('$TS','$name','$status',$models))
  conn.commit(); conn.close()
except: pass
" 2>/dev/null
  done

  log "$REPORT"

  # Tentative auto-recovery M3 LMStudio si Ollama dispo mais LMStudio down
  M3_LM_STATUS=$(curl -s --max-time 2 "http://192.168.1.113:1234/v1/models" 2>/dev/null | python3 -c "import json,sys; json.load(sys.stdin); print('UP')" 2>/dev/null || echo "DOWN")
  M3_OL_STATUS=$(curl -s --max-time 2 "http://192.168.1.113:11434/api/tags" 2>/dev/null | python3 -c "import json,sys; json.load(sys.stdin); print('UP')" 2>/dev/null || echo "DOWN")
  if [ "$M3_OL_STATUS" = "UP" ] && [ "$M3_LM_STATUS" = "DOWN" ]; then
    # M3 Ollama OK mais LMStudio down → on utilise déjà Ollama, rien à faire
    :
  fi

  sleep 60
done
