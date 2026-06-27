#!/usr/bin/env bash
# massive-scrape.sh — Orchestrateur 4 workers: codeur×2 + github + linkedin
# Usage: ./massive-scrape.sh [--dry-run] [--no-linkedin]

set -euo pipefail

DRY_RUN=""
NO_LINKEDIN=0
for arg in "$@"; do
    [[ "$arg" == "--dry-run" ]] && DRY_RUN="--dry-run"
    [[ "$arg" == "--no-linkedin" ]] && NO_LINKEDIN=1
done

JARVIS="/home/pamerys/jarvis"
GH_AUTO="/home/pamerys/github-social-automation"
LOG_DIR="$JARVIS/logs/scrape"
DATA_DIR="$JARVIS/data/scrape"
PIDS=()

mkdir -p "$LOG_DIR" "$DATA_DIR"

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
log() { echo -e "${GREEN}[$(date +%H:%M:%S)]${NC} $*"; }
warn() { echo -e "${YELLOW}[$(date +%H:%M:%S)]${NC} $*"; }

# ── WORKER 1: codeur.com pages 1-7 ──────────────────────────────────────────
worker_codeur_a() {
    log "Worker 1 → codeur.com pages 1-7"
    python3 "$JARVIS/scripts/codeur-scraper-worker.py" \
        --pages 1-7 \
        --output "$DATA_DIR/codeur_a.json" \
        $DRY_RUN \
        > "$LOG_DIR/codeur_a.log" 2>&1
    log "Worker 1 ✓ ($(wc -l < "$LOG_DIR/codeur_a.log") lignes log)"
}

# ── WORKER 2: codeur.com pages 8-15 ─────────────────────────────────────────
worker_codeur_b() {
    log "Worker 2 → codeur.com pages 8-15"
    python3 "$JARVIS/scripts/codeur-scraper-worker.py" \
        --pages 8-15 \
        --output "$DATA_DIR/codeur_b.json" \
        $DRY_RUN \
        > "$LOG_DIR/codeur_b.log" 2>&1
    log "Worker 2 ✓"
}

# ── WORKER 3: GitHub social automation ──────────────────────────────────────
worker_github() {
    log "Worker 3 → GitHub scan + profile"
    cd "$GH_AUTO"
    timeout 120 node src/main.js --mode=profile \
        > "$LOG_DIR/github.log" 2>&1 || true
    timeout 120 node src/main.js --mode=scan \
        >> "$LOG_DIR/github.log" 2>&1 || true
    # If AUTO_PUBLISH=true, also publish
    if [[ "${AUTO_PUBLISH:-false}" == "true" ]]; then
        timeout 120 node src/main.js --mode=publish \
            >> "$LOG_DIR/github.log" 2>&1 || true
    fi
    log "Worker 3 ✓ GitHub"
}

# ── WORKER 4: LinkedIn publish batch ────────────────────────────────────────
worker_linkedin() {
    if [[ $NO_LINKEDIN -eq 1 ]]; then
        log "Worker 4 → LinkedIn ignoré (--no-linkedin)"
        return
    fi
    log "Worker 4 → LinkedIn publish batch"
    python3 "$JARVIS/scripts/linkedin-worker.py" \
        > "$LOG_DIR/linkedin.log" 2>&1 || {
        warn "Worker 4 LinkedIn: erreur (voir $LOG_DIR/linkedin.log)"
    }
    log "Worker 4 ✓ LinkedIn"
}

# ── LAUNCH ALL WORKERS IN PARALLEL ──────────────────────────────────────────
log "=== LANCEMENT 4 WORKERS PARALLÈLES ==="
log "DRY_RUN=${DRY_RUN:-non} | NO_LINKEDIN=$NO_LINKEDIN"

worker_codeur_a &  PIDS+=($!)
worker_codeur_b &  PIDS+=($!)
worker_github   &  PIDS+=($!)
worker_linkedin &  PIDS+=($!)

# ── WAIT + STATUS ────────────────────────────────────────────────────────────
FAILED=0
for pid in "${PIDS[@]}"; do
    if wait "$pid"; then
        : # ok
    else
        warn "Worker PID $pid a échoué (code $?)"
        FAILED=$((FAILED+1))
    fi
done

log "=== MERGE RÉSULTATS ==="
python3 "$JARVIS/scripts/scrape-merger.py" \
    "$DATA_DIR/codeur_a.json" \
    "$DATA_DIR/codeur_b.json" \
    --output "$DATA_DIR/codeur_merged.json" \
    --telegram \
    2>&1 | tee "$LOG_DIR/merge.log"

if [[ $FAILED -eq 0 ]]; then
    log "=== TERMINÉ ✓ (4/4 workers OK) ==="
else
    warn "=== TERMINÉ avec $FAILED échec(s) ==="
fi

echo ""
echo "Logs : $LOG_DIR/"
echo "Data : $DATA_DIR/"
