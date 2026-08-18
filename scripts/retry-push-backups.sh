#!/usr/bin/env bash
# Retry-loop des push GitHub des backups (réseau 4G instable) — n8n + SQL.
# Attend la fin du job SQL en cours, puis retente chaque push jusqu'à succès (cap 8, backoff croissant).
set -u
cd /home/pamerys/jarvis
LOG=data/retry_push.log
echo "[$(date +%H:%M:%S)] retry-loop démarré" | tee -a "$LOG"

# 1. attendre que le driver SQL en cours se termine (évite conflit sur le repo cloné)
while pgrep -f 'run-jarvis-sql-backup/driver' >/dev/null 2>&1; do sleep 15; done

retry() {  # $1=nom  $2=GH_REPO  $3=driver relatif
  local n=0
  until [ "$n" -ge 8 ]; do
    if GH_REPO="$2" ./"$3" --no-mirror >> "$LOG" 2>&1; then
      echo "[$(date +%H:%M:%S)] ✅ $1 push OK (essai $((n+1)))" | tee -a "$LOG"; return 0
    fi
    n=$((n+1))
    local wait=$((60*n))
    echo "[$(date +%H:%M:%S)] ⚠️ $1 essai $n échec — backoff ${wait}s" | tee -a "$LOG"
    sleep "$wait"
  done
  echo "[$(date +%H:%M:%S)] ❌ $1 abandon après 8 essais (réseau)" | tee -a "$LOG"; return 1
}

retry SQL  Turbo31150/jarvis-sql-backups     ".claude/skills/run-jarvis-sql-backup/driver.sh"
retry n8n  Turbo31150/jarvis-n8n-workflows   ".claude/skills/run-jarvis-n8n-backup/driver.sh"
echo "[$(date +%H:%M:%S)] retry-loop terminé" | tee -a "$LOG"
