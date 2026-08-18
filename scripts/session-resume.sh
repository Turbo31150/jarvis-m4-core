#!/usr/bin/env bash
# session-resume.sh — Reprise de session JARVIS multi-scénario
# Axes : (1) reprise travail via logs  (2) lecture sauvegarde SQLite  (3) snapshot Timeshift
# Garde-fou anti-boucle inclus. Zéro API — 100% local.
set -uo pipefail

REM="/home/pamerys/.remember"
LOGDIR="/var/log"
PROJ="/home/pamerys/.claude/projects/-home-turbo"
STATE="$REM/tmp/resume-state"
FLAG="$REM/tmp/resume.lock"
TS_DIR="/timeshift/snapshots"
LOOP_WINDOW=30       # fenêtre anti-boucle (s)
LOOP_MAX=3           # nb max de reprises dans la fenêtre avant STOP
NOW_TS=$(date +%s)

mkdir -p "$REM/tmp"

log(){ printf '%s\n' "$*"; }
hr(){ printf '%.0s─' {1..50}; echo; }

MODE="${1:-auto}"   # auto | log | backup | snapshot | stop | reset

# ── COMMANDES DE CONTRÔLE (court-circuitent le garde-fou) ──────
case "$MODE" in
  stop)   : > "$FLAG"; log "🛑 Reprise désactivée (flag posé : $FLAG)."; exit 0 ;;
  reset)  rm -f "$STATE" "$FLAG"; log "♻️  Compteur + flag réinitialisés."; exit 0 ;;
esac
[ -f "$FLAG" ] && { log "⏸️  Reprise gelée (flag présent). 'session-resume.sh reset' pour réactiver."; exit 0; }

# ── GARDE-FOU ANTI-BOUCLE (scénario 3) ────────────────────────
# Compte les reprises récentes ; au-delà du seuil → arrêt net.
PREV=$(cat "$STATE" 2>/dev/null || echo "0 0")          # "count last_ts"
PC=$(echo "$PREV" | awk '{print $1}'); PT=$(echo "$PREV" | awk '{print $2}')
if [ $((NOW_TS - PT)) -lt "$LOOP_WINDOW" ]; then PC=$((PC + 1)); else PC=1; fi
echo "$PC $NOW_TS" > "$STATE"
if [ "$PC" -ge "$LOOP_MAX" ]; then
  log "🛑 STOP — $PC reprises en <${LOOP_WINDOW}s : boucle détectée."
  log "   Reset : session-resume.sh reset  puis relance."
  exit 42
fi

# ── AXE 1 : LECTURE LOGS / TRAVAIL EN COURS ───────────────────
axe_log(){
  hr; log "📜 AXE 1 — LOGS & TRAVAIL EN COURS"; hr
  if [ -s "$REM/remember.md" ]; then
    log "▸ Handoff (remember.md) :"; sed 's/^/   /' "$REM/remember.md"
  else
    log "▸ Handoff VIDE — fallback buffer now.md :"
    tail -25 "$REM/now.md" 2>/dev/null | sed 's/^/   /'
  fi
  TODAY="$REM/today-$(date +%F).md"
  [ -f "$TODAY" ] && { log "▸ Journal du jour ($(basename "$TODAY")) :"; tail -15 "$TODAY" | sed 's/^/   /'; }
  log "▸ Derniers transcripts actifs :"
  ls -lt "$PROJ"/*.jsonl 2>/dev/null | head -3 | awk '{print "   "$NF" ("$5"o)"}'
  log "▸ Incidents récents (var/log) :"
  grep -ihE "error|fail|crash|oom" "$LOGDIR"/jarvis-*.log 2>/dev/null | tail -5 | sed 's/^/   /'
}

# ── AXE 2 : LECTURE SAUVEGARDE SQLITE ─────────────────────────
axe_backup(){
  hr; log "💾 AXE 2 — SAUVEGARDES SQLite"; hr
  for d in /home/pamerys/jarvis/backups /home/pamerys/jarvis/data/backups /home/pamerys/jarvis-sql-backups; do
    [ -d "$d" ] || continue
    LAST=$(ls -t "$d"/*.db "$d"/*.sqlite* "$d"/*.bak* 2>/dev/null | head -1)
    [ -n "$LAST" ] && log "▸ $d → $(basename "$LAST") ($(date -r "$LAST" '+%F %H:%M'), $(du -h "$LAST"|cut -f1))"
  done
  log "▸ Intégrité base vive (jarvis.db) :"
  for db in /home/pamerys/jarvis/data/*.db; do
    [ -f "$db" ] || continue
    R=$(sqlite3 "$db" "PRAGMA integrity_check;" 2>/dev/null | head -1)
    log "   $(basename "$db") : ${R:-illisible}"
  done
}

# ── AXE 3 : SNAPSHOT TIMESHIFT ────────────────────────────────
axe_snapshot(){
  hr; log "📸 AXE 3 — SNAPSHOTS Timeshift"; hr
  LAST_SNAP=$(ls -1 "$TS_DIR" 2>/dev/null | sort | tail -1)
  if [ -n "$LAST_SNAP" ]; then
    SNAP_DATE="${LAST_SNAP%%_*}"; SNAP_TIME="${LAST_SNAP#*_}"; SNAP_TIME="${SNAP_TIME//-/:}"
    SNAP_TS=$(date -d "$SNAP_DATE $SNAP_TIME" +%s 2>/dev/null || echo 0)
    AGE_D=$(( (NOW_TS - SNAP_TS) / 86400 ))
    log "▸ Dernier snapshot : $LAST_SNAP (il y a ${AGE_D}j)"
    [ "$AGE_D" -gt 7 ] && log "   ⚠️  >7j : créer un snapshot frais → sudo timeshift --create --comments 'pre-resume'"
  else
    log "▸ Aucun snapshot accessible (droits root ?). sudo timeshift --list"
  fi
}

# ── DISPATCH MULTI-SCÉNARIO ───────────────────────────────────
case "$MODE" in
  log)      axe_log ;;
  backup)   axe_backup ;;
  snapshot) axe_snapshot ;;
  auto|*)   axe_log; axe_backup; axe_snapshot
            hr; log "✅ Reprise complète ($PC/$LOOP_MAX dans la fenêtre). Travail prêt à continuer." ;;
esac
