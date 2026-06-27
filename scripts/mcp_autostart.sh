#!/bin/bash
# MCP AutoStart — vérifie et enregistre l'état de tous les serveurs MCP JARVIS
LOG="/tmp/jarvis_logs/mcp_startup.jsonl"
DB="/home/pamerys/jarvis/cowork_engine.db"
TS=$(date -u +%Y-%m-%dT%H:%M:%S)
mkdir -p /tmp/jarvis_logs

declare -A MCP_ENDPOINTS=(
  ["ollama-local"]="http://127.0.0.1:11434/api/tags"
  ["lmstudio-m1"]="http://192.168.1.85:1234/v1/models"
  ["lmstudio-m2"]="http://192.168.1.26:1234/v1/models"
  ["redis-local"]="127.0.0.1:6379"
)

for NAME in "${!MCP_ENDPOINTS[@]}"; do
  URL="${MCP_ENDPOINTS[$NAME]}"
  if [[ "$URL" == http* ]]; then
    STATUS=$(curl -s --max-time 2 "$URL" 2>/dev/null | python3 -c "import json,sys; json.load(sys.stdin); print('up')" 2>/dev/null || echo "down")
  else
    HOST="${URL%%:*}"; PORT="${URL##*:}"
    STATUS=$(nc -z -w1 "$HOST" "$PORT" 2>/dev/null && echo "up" || echo "down")
  fi
  echo "{\"ts\":\"$TS\",\"mcp\":\"$NAME\",\"status\":\"$STATUS\"}" | tee -a "$LOG"
done

echo "---"
echo "MCP Skills disponibles (Claude Code session):"
echo "jarvis-agents, jarvis-cluster, jarvis-memory, jarvis-linux-sqlite"
echo "jarvis-linux-ol1, jarvis-ol1, ia-web-jarvis, requestly-jarvis"
echo "antigravity, claude-in-chrome, plugin_chrome-devtools-mcp"
