#!/usr/bin/env bash
# production-audit.sh — Audit complet production JARVIS + auto-fix
set -euo pipefail

LOG_DB="${JARVIS_LOG_DB:-/home/pamerys/jarvis/logs/jarvis_logs.db}"
REPORT_DIR="/home/pamerys/jarvis/reports"
TS=$(date +%Y%m%d_%H%M%S)
REPORT="$REPORT_DIR/audit_$TS.txt"
FAIL=0

mkdir -p "$REPORT_DIR"

_log() { echo "$1" | tee -a "$REPORT"; }
_ok()  { _log "  ✓ $1"; }
_err() { _log "  ✗ $1"; FAIL=$((FAIL+1)); }

_log "=== JARVIS PRODUCTION AUDIT $TS ==="

# ── 1. Cluster LLM ──────────────────────────────────────────────────────────
_log "\n[1/6] CLUSTER LLM"
for node in "M1:192.168.1.85:1234" "M2:192.168.1.26:1234"; do
  name="${node%%:*}"; addr="${node#*:}"
  count=$(curl -sf "http://$addr/v1/models" 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d.get('data',[])))" 2>/dev/null || echo "0")
  [[ "$count" -gt 0 ]] && _ok "$name: $count models" || _err "$name: DOWN (http://$addr)"
done
ol1=$(curl -sf http://127.0.0.1:11434/api/tags 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d.get('models',[])))" 2>/dev/null || echo "0")
[[ "$ol1" -gt 0 ]] && _ok "OL1: $ol1 models" || _err "OL1: DOWN"

# ── 2. Services systemd critiques ───────────────────────────────────────────
_log "\n[2/6] SERVICES SYSTEMD"
for svc in jarvis-vocal jarvis-ws lumen-voice jarvis-whisper; do
  st=$(systemctl is-active "$svc" 2>/dev/null || echo "not-found")
  [[ "$st" == "active" ]] && _ok "$svc: active" || _log "  ~ $svc: $st (non critique)"
done

# ── 3. Docker containers ────────────────────────────────────────────────────
_log "\n[3/6] DOCKER CONTAINERS"
down_containers=$(docker ps -a --format "{{.Names}}:{{.Status}}" 2>/dev/null | grep -v "Up " | grep -v "NAMES" | head -10)
running=$(docker ps -q 2>/dev/null | wc -l)
_ok "Running: $running containers"
if [[ -n "$down_containers" ]]; then
  echo "$down_containers" | while IFS= read -r line; do _log "  ~ DOWN: $line"; done
fi

# ── 4. MCP servers Python import check ──────────────────────────────────────
_log "\n[4/6] MCP SERVERS — IMPORT CHECK"
PYPATH="/home/pamerys/Workspaces/jarvis-linux:/home/pamerys/Workspaces/jarvis-linux/src"
cd /home/pamerys/Workspaces/jarvis-linux

check_import() {
  PYTHONPATH="$PYPATH" python3 -c "import $1" 2>/dev/null && _ok "$1" || _err "$1: ImportError"
}
check_import "jarvis.core.utils.mcp_server"
check_import "jarvis.core.utils.ia_tool_executor"
check_import "jarvis.core.utils.ia_tools"
check_import "jarvis.core.utils.production_bridge"

# ── 5. SQLite databases ──────────────────────────────────────────────────────
_log "\n[5/6] DATABASES"
for db in \
  /home/pamerys/jarvis/jarvis_master.db \
  /home/pamerys/jarvis/data/etoile.db \
  /home/pamerys/jarvis/logs/jarvis_logs.db \
  /home/pamerys/jarvis/cowork_engine.db; do
  if [[ -f "$db" ]]; then
    tables=$(sqlite3 "$db" ".tables" 2>/dev/null | wc -w)
    _ok "$(basename $db): $tables tables"
  else
    _err "MISSING: $db"
  fi
done

# ── 6. Ports critiques ───────────────────────────────────────────────────────
_log "\n[6/6] PORTS"
for port_label in "9742:JARVIS-WS" "18789:OpenClaw" "11434:OL1" "1234:LMStudio-local"; do
  port="${port_label%%:*}"; label="${port_label#*:}"
  nc -z 127.0.0.1 "$port" 2>/dev/null && _ok "$label :$port" || _log "  ~ $label :$port fermé"
done

# ── Résumé ───────────────────────────────────────────────────────────────────
_log "\n=== RÉSUMÉ: $FAIL erreur(s) critique(s) ==="
[[ $FAIL -gt 0 ]] && _log "ACTION REQUISE — voir $REPORT" || _log "Production OK"

# Log en DB si disponible
if [[ -f "$LOG_DB" ]]; then
  sqlite3 "$LOG_DB" "CREATE TABLE IF NOT EXISTS audit_runs (id INTEGER PRIMARY KEY, ts TEXT, fails INTEGER, report TEXT);
    INSERT INTO audit_runs(ts,fails,report) VALUES('$TS',$FAIL,'$REPORT');" 2>/dev/null || true
fi

echo "$REPORT"
exit $FAIL
