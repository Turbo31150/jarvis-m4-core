#!/usr/bin/env bash
# Tunnel Manus « permanent » : récepteur + cloudflared, et surtout ré-enregistrement
# automatique du webhook chez Manus à chaque démarrage (l'URL quick-tunnel change).
#
# Requestly ne peut pas tenir ce rôle : il intercepte des requêtes sortantes,
# il n'expose pas un service local sur Internet.
set -euo pipefail

PORT="${MANUS_WH_PORT:-8791}"
RECV=/home/pamerys/jarvis/mcp/manus_webhook_receiver.py
MCP=/home/pamerys/jarvis/mcp/manus_mcp.py
CFD=/home/pamerys/bin/cloudflared
STATE=/home/pamerys/.config/jarvis
LOG="${MANUS_WH_LOG:-$STATE/manus-tunnel.log}"
mkdir -p "$STATE"

log() { echo "[$(date '+%F %T')] $*" | tee -a "$LOG"; }

mcp_call() {  # mcp_call <endpoint> <params-json>
  printf '%s\n' \
    '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' \
    "{\"jsonrpc\":\"2.0\",\"id\":2,\"method\":\"tools/call\",\"params\":{\"name\":\"manus_call\",\"arguments\":{\"endpoint\":\"$1\",\"params\":$2}}}" \
    | timeout 60 python3 "$MCP" \
    | python3 -c 'import json,sys
for l in sys.stdin:
    r = json.loads(l).get("result", {})
    if "content" in r: print(r["content"][0]["text"])'
}

cleanup() { kill "${CF_PID:-0}" "${RX_PID:-0}" 2>/dev/null || true; }
trap cleanup EXIT

# 1. tunnel d'abord : on a besoin de l'URL pour vérifier les signatures
log "démarrage cloudflared sur :$PORT"
CF_OUT="$STATE/cloudflared.out"; : > "$CF_OUT"
"$CFD" tunnel --url "http://127.0.0.1:$PORT" >"$CF_OUT" 2>&1 &
CF_PID=$!

URL=""
for _ in $(seq 1 30); do
  URL=$(grep -oE 'https://[a-z0-9-]+\.trycloudflare\.com' "$CF_OUT" | head -1) && [ -n "$URL" ] && break
  sleep 2
done
[ -n "$URL" ] || { log "ÉCHEC : pas d'URL de tunnel"; exit 1; }
log "tunnel = $URL"
echo "$URL" > "$STATE/manus-tunnel.url"

# 2. récepteur, avec l'URL publique (elle entre dans la signature RSA)
python3 "$RECV" --port "$PORT" --public-url "$URL/manus" >>"$LOG" 2>&1 &
RX_PID=$!
for _ in $(seq 1 15); do
  curl -sf -m 3 "http://127.0.0.1:$PORT/" >/dev/null && break; sleep 1
done

# 3. purge des anciens webhooks (URLs mortes) puis enregistrement de la nouvelle
OLD=$(mcp_call webhook.list '{}' | python3 -c 'import json,sys
try:
    d = json.load(sys.stdin)
except Exception:
    raise SystemExit
for w in d.get("data") or []:
    print(w["id"])' || true)
for id in $OLD; do
  mcp_call webhook.delete "{\"id\":\"$id\"}" >/dev/null && log "webhook obsolète supprimé : $id"
done

NEW=$(mcp_call webhook.create "{\"url\":\"$URL/manus\",\"name\":\"jarvis-m4\"}")
echo "$NEW" | grep -q '"ok": *true' \
  && log "webhook enregistré → $URL/manus" \
  || { log "ÉCHEC enregistrement : $NEW"; exit 1; }

log "opérationnel — Ctrl-C ou stop du service pour arrêter"
wait "$CF_PID"
