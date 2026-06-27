#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AGENT="$SCRIPT_DIR/node_agent.py"
CONFIG="$SCRIPT_DIR/config.json"

SSH_OPTS="-o StrictHostKeyChecking=no -o ConnectTimeout=5"

# Parse nodes from config.json (requires python3)
NODES=$(python3 -c "
import json, sys
with open('$CONFIG') as f:
    cfg = json.load(f)
for n in cfg['nodes']:
    lm = n.get('lm_studio_port') or ''
    ol = n.get('ollama_port') or ''
    print(f\"{n['name']}|{n['host']}|{n['ssh_user']}|{lm}|{ol}\")
")

echo "==> JARVIS Monitor Deploy"
echo ""

# ── Deploy + start node_agent on each remote node ──────────────────────────
for row in $NODES; do
  IFS='|' read -r name host user lm_port ollama_port <<< "$row"

  # Skip 127.0.0.1 (OL1) — will be started locally below
  if [[ "$host" == "127.0.0.1" || "$host" == "127.0.0.1" ]]; then
    echo "[$name] local node — will start agent locally"
    continue
  fi

  echo "[$name] Copying node_agent.py to $user@$host..."
  scp $SSH_OPTS "$AGENT" "$user@$host:/tmp/jarvis_node_agent.py" 2>/dev/null && echo "[$name] Copy OK" || { echo "[$name] COPY FAILED (skip)"; continue; }

  # Kill previous instance
  ssh $SSH_OPTS "$user@$host" "pkill -f jarvis_node_agent || true" 2>/dev/null

  # Build args
  EXTRA=""
  [[ -n "$lm_port" ]] && EXTRA="$EXTRA --lm-port $lm_port"
  [[ -n "$ollama_port" ]] && EXTRA="$EXTRA --ollama-port $ollama_port"

  echo "[$name] Starting agent on $host:8421..."
  ssh $SSH_OPTS "$user@$host" "nohup python3 /tmp/jarvis_node_agent.py $EXTRA > /tmp/jarvis_agent.log 2>&1 &" 2>/dev/null \
    && echo "[$name] Agent started" \
    || echo "[$name] START FAILED"
done

# ── Start OL1 (127.0.0.1) agent ───────────────────────────────────────────
echo ""
echo "[OL1] Starting local agent on port 8421..."
pkill -f "node_agent.py" 2>/dev/null || true
python3 "$AGENT" --ollama-port 11434 > /tmp/jarvis_agent_ol1.log 2>&1 &
echo "[OL1] Agent PID $! started"

# ── (Re)start central server ──────────────────────────────────────────────
echo ""
echo "[SERVER] Starting central server on port 8420..."
pkill -f "server.py" 2>/dev/null || true
sleep 1
cd "$SCRIPT_DIR"
python3 server.py > /tmp/jarvis_monitor_server.log 2>&1 &
SERVER_PID=$!
echo "[SERVER] PID $SERVER_PID"
sleep 2

if kill -0 $SERVER_PID 2>/dev/null; then
  echo "[SERVER] Running OK"
else
  echo "[SERVER] FAILED — check /tmp/jarvis_monitor_server.log"
  tail -20 /tmp/jarvis_monitor_server.log
  exit 1
fi

# ── Open dashboard ────────────────────────────────────────────────────────
DASHBOARD_URL="http://127.0.0.1:8420"
echo ""
echo "==> Dashboard: $DASHBOARD_URL"

if command -v xdg-open &>/dev/null; then
  xdg-open "$DASHBOARD_URL" 2>/dev/null &
elif command -v gnome-open &>/dev/null; then
  gnome-open "$DASHBOARD_URL" 2>/dev/null &
else
  echo "(open manually in browser)"
fi

echo ""
echo "==> Deploy complete. Logs:"
echo "    Server : /tmp/jarvis_monitor_server.log"
echo "    OL1    : /tmp/jarvis_agent_ol1.log"
