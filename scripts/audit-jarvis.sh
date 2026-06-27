#!/bin/bash
# audit-jarvis.sh — Audit complet JARVIS PAMERYS M4
# Usage: audit-jarvis [--json]

set -euo pipefail
JARVIS=/home/pamerys/jarvis
JSON_MODE=0; [[ "${1:-}" == "--json" ]] && JSON_MODE=1

# ── Couleurs ──────────────────────────────────────────────────────────────────
G="\033[32m" R="\033[31m" Y="\033[33m" C="\033[36m" B="\033[1m" Z="\033[0m"
ok()  { echo -e "  ${G}✅${Z} $1"; }
ko()  { echo -e "  ${R}❌${Z} $1"; }
warn(){ echo -e "  ${Y}⚠️ ${Z} $1"; }

SCORE=0; MAX=0
pass() { SCORE=$((SCORE+1)); MAX=$((MAX+1)); ok  "$1"; }
fail() {               MAX=$((MAX+1)); ko  "$1"; }
skip() {               MAX=$((MAX+1)); warn "$1"; }

echo -e "\n${B}${C}╔══════════════════════════════════════════════╗${Z}"
echo -e "${B}${C}║   JARVIS AUDIT — PAMERYS M4   $(date +%H:%M)         ║${Z}"
echo -e "${B}${C}╚══════════════════════════════════════════════╝${Z}\n"

# ── 1. SERVICES SYSTEMD ───────────────────────────────────────────────────────
echo -e "${B}📦 Services systemd${Z}"
for svc in jarvis-webapp jarvis-voice-widget jarvis-thermal-agent; do
  if systemctl --user is-active --quiet "${svc}.service" 2>/dev/null; then
    pass "$svc"
  else
    fail "$svc (inactif)"
  fi
done

# ── 2. CLUSTER LLM ────────────────────────────────────────────────────────────
echo -e "\n${B}🤖 Cluster LLM${Z}"
for name_host in "M1:http://192.168.1.85:1234" "M2:http://192.168.1.26:1234"; do
  name="${name_host%%:*}"
  host="${name_host#*:}"
  start=$(($(date +%s%3N)))
  if curl -sf --max-time 2 "${host}/v1/models" > /dev/null 2>&1; then
    ms=$(( $(date +%s%3N) - start ))
    pass "$name UP (${ms}ms)"
  else
    fail "$name DOWN (${host})"
  fi
done

# ── 3. GPU THERMAL ────────────────────────────────────────────────────────────
echo -e "\n${B}🌡️  GPU Thermal${Z}"
THERMAL_JSON="${JARVIS}/logs/thermal-status.json"
if [[ -f "$THERMAL_JSON" ]]; then
  TEMP=$(python3 -c "import json; d=json.load(open('$THERMAL_JSON')); print(d.get('gpu_temp',0))" 2>/dev/null)
  STATE=$(python3 -c "import json; d=json.load(open('$THERMAL_JSON')); print(d.get('state','?'))" 2>/dev/null)
  if (( TEMP < 90 )); then
    pass "GPU ${TEMP}°C (${STATE})"
  elif (( TEMP < 95 )); then
    skip "GPU ${TEMP}°C (${STATE}) — chaud"
  else
    fail "GPU ${TEMP}°C (${STATE}) — critique!"
  fi
else
  fail "thermal-status.json absent"
fi

# ── 4. ESPACE DISQUE ──────────────────────────────────────────────────────────
echo -e "\n${B}💾 Espace disque${Z}"
while IFS= read -r line; do
  pct=$(echo "$line" | awk '{print $5}' | tr -d '%')
  mnt=$(echo "$line" | awk '{print $6}')
  if (( pct < 80 )); then
    pass "${mnt}: ${pct}% utilisé"
  elif (( pct < 90 )); then
    skip "${mnt}: ${pct}% utilisé"
  else
    fail "${mnt}: ${pct}% utilisé — presque plein!"
  fi
done < <(df -h / /home 2>/dev/null | tail -n +2 | awk '!seen[$6]++')

# ── 5. PORT WEBAPP ────────────────────────────────────────────────────────────
echo -e "\n${B}🌐 Ports réseau${Z}"
if curl -sf --max-time 2 "http://localhost:7777/" > /dev/null 2>&1; then
  pass "Dashboard :7777 accessible"
else
  fail "Dashboard :7777 inaccessible"
fi
if ss -tuln 2>/dev/null | grep -q ":7777"; then
  pass "Port 7777 en écoute"
else
  fail "Port 7777 absent"
fi

# ── 6. SQLITE DBs ─────────────────────────────────────────────────────────────
echo -e "\n${B}🗄️  Bases SQLite${Z}"
declare -A DBS=(
  ["todo"]="${JARVIS}/todo.db"
  ["budget"]="${JARVIS}/budget/budget.db"
  ["notes"]="${JARVIS}/webapp/notes.db"
  ["rdv"]="${JARVIS}/rdv.db"
)
for name in "${!DBS[@]}"; do
  db="${DBS[$name]}"
  if [[ -f "$db" ]]; then
    integrity=$(sqlite3 "$db" "PRAGMA integrity_check;" 2>/dev/null)
    if [[ "$integrity" == "ok" ]]; then
      rows=$(sqlite3 "$db" "SELECT COUNT(*) FROM (SELECT name FROM sqlite_master WHERE type='table');" 2>/dev/null)
      pass "${name}.db (${rows} tables, intégrité OK)"
    else
      fail "${name}.db — intégrité KO"
    fi
  else
    skip "${name}.db absent"
  fi
done

# ── 7. GIT REPOS ──────────────────────────────────────────────────────────────
echo -e "\n${B}📁 Repos Git${Z}"
for repo in "${JARVIS}" "${HOME}/machine-m4-pamerys"; do
  name=$(basename "$repo")
  if [[ -d "${repo}/.git" ]]; then
    uncommitted=$(git -C "$repo" status --porcelain 2>/dev/null | wc -l)
    branch=$(git -C "$repo" branch --show-current 2>/dev/null)
    if (( uncommitted == 0 )); then
      pass "${name} (${branch}) — propre"
    else
      skip "${name} (${branch}) — ${uncommitted} fichiers non commités"
    fi
  else
    skip "${name} — pas de repo git"
  fi
done

# ── 8. MAMS COUNTDOWN ────────────────────────────────────────────────────────
echo -e "\n${B}🎯 MAMS Oral${Z}"
DAYS=$(python3 -c "from datetime import date; print((date(2026,6,2)-date.today()).days)" 2>/dev/null)
if (( DAYS > 0 )); then
  pass "J-${DAYS} avant oral MAMS (2 juin)"
elif (( DAYS == 0 )); then
  warn "C'est le JOUR de l'oral MAMS! 🎯"
else
  pass "Oral MAMS passé (${DAYS} jours)"
fi

# ── SCORE FINAL ───────────────────────────────────────────────────────────────
echo ""
echo -e "${B}${C}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${Z}"
PCT=$(( SCORE * 100 / MAX ))
if (( PCT >= 80 )); then
  echo -e "${B}${G}  SCORE: ${SCORE}/${MAX} (${PCT}%) — JARVIS EN BONNE SANTÉ ✅${Z}"
elif (( PCT >= 60 )); then
  echo -e "${B}${Y}  SCORE: ${SCORE}/${MAX} (${PCT}%) — ATTENTION REQUISE ⚠️${Z}"
else
  echo -e "${B}${R}  SCORE: ${SCORE}/${MAX} (${PCT}%) — ACTION NÉCESSAIRE ❌${Z}"
fi
echo -e "${B}${C}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${Z}\n"

[[ "$JSON_MODE" == "1" ]] && echo "{\"score\":${SCORE},\"max\":${MAX},\"pct\":${PCT}}"
exit 0
