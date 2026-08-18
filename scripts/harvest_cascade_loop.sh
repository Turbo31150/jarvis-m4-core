#!/usr/bin/env bash
# HARVEST CASCADE LOOP — Moisson massive SkillsMP + Sessions Claude
# Boucle infinie contrôlée avec checkpoint, backoff, et injection Board OS

set -uo pipefail
LOGFILE="/home/pamerys/jarvis/logs/harvest_cascade_$(date +%Y%m%d).log"
LOCK="/tmp/jarvis_harvest.lock"
SCRIPTS="/home/pamerys/Workspaces/jarvis-linux/skills-library/scripts"
JARVIS_SCRIPTS="/home/pamerys/jarvis/scripts"

if [ "${1:-}" = "--once" ] || [ "${1:-}" = "-1" ]; then
    ONCE=1
else
    ONCE=0
    exec >> "$LOGFILE" 2>&1
fi

# Lock unique
[ -f "$LOCK" ] && kill -0 "$(cat $LOCK)" 2>/dev/null && echo "[SKIP] Déjà en cours (PID=$(cat $LOCK))" && exit 0
echo $$ > "$LOCK"
trap "rm -f $LOCK" EXIT

echo "=== [CASCADE LOOP] Démarrage $(date) ==="

ONCE=0
if [ "${1:-}" = "--once" ] || [ "${1:-}" = "-1" ]; then
    ONCE=1
fi

CYCLE=0
while true; do
    CYCLE=$((CYCLE + 1))
    echo ""
    echo "--- [CYCLE $CYCLE] $(date) ---"

    # VAGUE 1 — Sessions Claude Code
    echo "[VAGUE 1] Moisson sessions Claude..."
    python3 "$SCRIPTS/harvest_claude_sessions.py" && echo "[OK] Sessions Claude" || echo "[WARN] Sessions Claude partiel"

    # VAGUE 2 — SkillsMP API (mots-clés nouveaux en priorité)
    echo "[VAGUE 2] Moisson SkillsMP API v4..."
    python3 "$SCRIPTS/harvest_skillsmp_api_v4.py" && echo "[OK] SkillsMP API" || echo "[WARN] SkillsMP partiel"

    # VAGUE 3 — Rebuild index
    echo "[VAGUE 3] Rebuild MANIFEST + index..."
    python3 "$SCRIPTS/build_index.py" && echo "[OK] Index rebuilt" || echo "[WARN] Index partiel"

    # VAGUE 4 — Injection Board OS
    echo "[VAGUE 4] Injection Board OS..."
    python3 "$JARVIS_SCRIPTS/inject_skills_to_board.py" 2>/dev/null && echo "[OK] Board OS alimenté" || echo "[WARN] Board OS partiel"

    # VAGUE 5 — Git commit
    echo "[VAGUE 5] Commit git..."
    cd /home/pamerys/Workspaces/jarvis-linux && \
    git add -A && \
    git commit -m "feat(harvest): cascade loop cycle $CYCLE — $(date +%Y-%m-%d_%H%M)" 2>/dev/null && \
    git push origin main 2>/dev/null || true

    # Stats
    TOTAL=$(python3 -c "import sqlite3; c=sqlite3.connect('/home/pamerys/Workspaces/jarvis-linux/skills-library/skills_library.db'); print(c.execute('SELECT COUNT(*) FROM skills').fetchone()[0])" 2>/dev/null || echo "?")
    BOARD_SRC=$(python3 -c "import sqlite3; c=sqlite3.connect('/home/pamerys/jarvis/board/board.db'); print(c.execute('SELECT COUNT(*) FROM sources').fetchone()[0])" 2>/dev/null || echo "?")
    echo "[STATS] Skills: $TOTAL | Board sources: $BOARD_SRC | Cycle: $CYCLE"

    if [ "$ONCE" -eq 1 ]; then
        echo "[ONCE] Cycle unique terminé avec succès."
        exit 0
    fi

    # Pause politesse (30 min entre cycles complets)
    echo "[SLEEP] Pause 1800s avant prochain cycle..."
    sleep 1800
done
