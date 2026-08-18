#!/usr/bin/env bash
# mcp-audit — Validation sockets + MCP + cluster nodes

set -uo pipefail

declare -A targets=(
  [LMStudio_M1]="http://127.0.0.1:1234/v1/models"
  [LMStudio_M2]="http://127.0.0.1:18800/v1/models"
  [Ollama_OL1]="http://127.0.0.1:11434/api/tags"
  [Ollama_M3]="http://127.0.0.1:18800/api/tags"
  [Chrome_CDP_9222]="http://localhost:9222/json/version"
  [JARVIS_CDP_9108]="http://127.0.0.1:9108/"
  [JARVIS_MCP_18901]="http://127.0.0.1:18901/"
  [JARVIS_WS_19742]="http://127.0.0.1:19742/"
  [Antigravity_9001]="http://127.0.0.1:9001/mcp"
)

echo "═══ MCP / SOCKET AUDIT — $(date +%H:%M:%S) ═══"
printf "%-22s %-10s %-10s\n" "TARGET" "STATUS" "LATENCY"
echo "──────────────────────────────────────────────"
for name in "${!targets[@]}"; do
  url="${targets[$name]}"
  start=$(date +%s%N)
  code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 3 "$url" 2>/dev/null || echo "000")
  end=$(date +%s%N)
  ms=$(( (end - start) / 1000000 ))
  if [ "$code" = "000" ]; then
    printf "  %-20s \033[31m%-6s\033[0m %sms\n" "$name" "DOWN" "$ms"
  elif [ "$code" -ge 200 ] && [ "$code" -lt 400 ]; then
    printf "  %-20s \033[32m%-6s\033[0m %sms\n" "$name" "$code" "$ms"
  else
    printf "  %-20s \033[33m%-6s\033[0m %sms\n" "$name" "$code" "$ms"
  fi
done

echo ""
echo "═══ MCP servers (claude mcp list) ═══"
total=$(claude mcp list 2>/dev/null | grep -cE "Connected|✗" || echo 0)
ok=$(claude mcp list 2>/dev/null | grep -c "Connected" || echo 0)
echo "  Total: $total · Connected: $ok"
