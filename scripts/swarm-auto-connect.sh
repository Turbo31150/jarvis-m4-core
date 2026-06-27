#!/bin/bash
# JARVIS Swarm Auto-Connect — surveille les nœuds et les joint dès disponibles
NODES=("192.168.1.85:turbo:M1" "192.168.1.26:turbo:M2" "192.168.1.113:turbo:M3" "192.168.1.94:turbo:M5")
MANAGER_IP="192.168.1.62"
JOIN_SCRIPT="$HOME/jarvis/scripts/swarm-join-node.sh"
LOG="$HOME/jarvis/logs/swarm-connect.log"
mkdir -p "$(dirname $LOG)"

log() { echo "[$(date '+%H:%M:%S')] $*" | tee -a "$LOG"; }

log "=== Swarm Auto-Connect démarré (manager: $MANAGER_IP) ==="

while true; do
  CONNECTED=$(docker node ls --format "{{.Hostname}}" 2>/dev/null | wc -l)
  log "Nœuds actifs: $CONNECTED"

  for entry in "${NODES[@]}"; do
    IP="${entry%%:*}"; rest="${entry#*:}"; USER="${rest%%:*}"; NAME="${rest##*:}"
    if nc -z -w2 "$IP" 22 2>/dev/null; then
      # Vérifier si déjà dans le swarm
      if ! docker node ls 2>/dev/null | grep -q "$IP\|$NAME"; then
        log "→ $NAME ($IP) détecté, connexion au swarm..."
        ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 "$USER@$IP" \
          "bash -s" < "$JOIN_SCRIPT" >> "$LOG" 2>&1 && log "✅ $NAME joint" || log "❌ $NAME échec"
      else
        log "✓ $NAME déjà dans le swarm"
      fi
    else
      log "⏳ $NAME ($IP) hors ligne"
    fi
  done

  sleep 30
done
