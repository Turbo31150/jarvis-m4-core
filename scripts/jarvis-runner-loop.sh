#!/usr/bin/env bash
# Wrapper de relance permanente du runner
LOG="/home/pamerys/jarvis/logs/prod-runner.log"
PID_FILE="/home/pamerys/jarvis/logs/prod-runner.pid"
RUNNER="/home/pamerys/jarvis/scripts/jarvis-prod-runner.py"

echo "[$(date +%H:%M:%S)] ♾️  JARVIS PROD RUNNER — boucle permanente démarrée" | tee -a "$LOG"

while true; do
  # Compter les pending
  PENDING=$(sqlite3 /home/pamerys/jarvis/jarvis_master.db "SELECT COUNT(*) FROM tasks WHERE status='pending';" 2>/dev/null || echo 0)
  
  if [ "$PENDING" -gt 0 ]; then
    echo "[$(date +%H:%M:%S)] ⚡ $PENDING tâches pending → lancement passe" | tee -a "$LOG"
    python3 "$RUNNER" --once --limit 50 >> "$LOG" 2>&1
  else
    echo "[$(date +%H:%M:%S)] ✅ 0 pending — pause 5s" | tee -a "$LOG"
    sleep 5
    continue
  fi
  
  echo "[$(date +%H:%M:%S)] ⏳ Pause 3s avant prochaine passe..." | tee -a "$LOG"
  sleep 3
done
