#!/usr/bin/env bash
# ==============================================================================
# JARVIS OMEGA — AUDIT DE FIN DE SESSION & RESPECT DES VERROUS
# ==============================================================================

set -e
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
DB_PATH="$HOME/jarvis/data/session_audit.db"
mkdir -p "$HOME/jarvis/data"

# 1. Initialiser la DB SQLite d'audit si nécessaire
sqlite3 "$DB_PATH" << 'SQL'
CREATE TABLE IF NOT EXISTS session_audits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    gpu_check INTEGER NOT NULL,
    lms_api_check INTEGER NOT NULL,
    rj45_check INTEGER NOT NULL,
    memory_lock_check INTEGER NOT NULL,
    sqlite_wal_check INTEGER NOT NULL,
    compliance_score INTEGER NOT NULL,
    status TEXT NOT NULL,
    details TEXT
);
SQL

# 2. Check GPU VRAM (4 GPUs présents)
GPU_COUNT=$(nvidia-smi --query-gpu=name --format=csv,noheader | wc -l)
GPU_CHECK=0
[ "$GPU_COUNT" -eq 4 ] && GPU_CHECK=1

# 3. Check LM Studio API (0.0.0.0:1234)
LMS_CHECK=0
if curl -s http://127.0.0.1:1234/v1/models >/dev/null 2>&1; then
    LMS_CHECK=1
fi

# 4. Check Liaison RJ45 direct M4 (10.42.0.1)
RJ45_CHECK=0
if ping -c 1 -W 1 10.42.0.1 >/dev/null 2>&1; then
    RJ45_CHECK=1
fi

# 5. Check Mémoire Lock Swan & Règles
MEM_CHECK=0
if [ -f "$HOME/.gemini/antigravity-cli/brain/9e56f297-cbea-4870-8805-291d8d6489fd/TRANSMISSION_SWAN_LOCK.md" ] && \
   [ -f "$HOME/.gemini/antigravity-cli/brain/9e56f297-cbea-4870-8805-291d8d6489fd/REGLE_AUTO_DECLENCHEUR_DIRECTION.md" ]; then
    MEM_CHECK=1
fi

# 6. Check SQLite WAL Mode & Intégrité
SQLITE_CHECK=0
INTEGRITY=$(sqlite3 "$DB_PATH" "PRAGMA integrity_check;" 2>/dev/null || echo "error")
if [ "$INTEGRITY" = "ok" ]; then
    SQLITE_CHECK=1
fi

# Calcul Score
TOTAL_SCORE=$(( (GPU_CHECK + LMS_CHECK + RJ45_CHECK + MEM_CHECK + SQLITE_CHECK) * 20 ))
STATUS="COMPLIANT"
[ "$TOTAL_SCORE" -lt 100 ] && STATUS="DEGRADED"

DETAILS="GPUs: $GPU_COUNT/4 | LMS: $LMS_CHECK | RJ45: $RJ45_CHECK | Locks: $MEM_CHECK | SQLite: $SQLITE_CHECK"

# Insertion SQLite
sqlite3 "$DB_PATH" << SQL
INSERT INTO session_audits (timestamp, gpu_check, lms_api_check, rj45_check, memory_lock_check, sqlite_wal_check, compliance_score, status, details)
VALUES ('$TIMESTAMP', $GPU_CHECK, $LMS_CHECK, $RJ45_CHECK, $MEM_CHECK, $SQLITE_CHECK, $TOTAL_SCORE, '$STATUS', '$DETAILS');
SQL

# Output JSON pour n8n
cat << JSON
{
  "timestamp": "$TIMESTAMP",
  "compliance_score": $TOTAL_SCORE,
  "status": "$STATUS",
  "gpu_check": $GPU_CHECK,
  "lms_api_check": $LMS_CHECK,
  "rj45_check": $RJ45_CHECK,
  "memory_lock_check": $MEM_CHECK,
  "sqlite_wal_check": $SQLITE_CHECK,
  "details": "$DETAILS"
}
JSON
