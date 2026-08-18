#!/usr/bin/env bash
# mcp-funnel-check.sh — contrôle de la chaîne JARVIS MCP → Funnel → Perplexity.
# 0-token : aucune inférence, uniquement des sondes locales. On-demand ou boot.
# Sortie : une ligne par chaînon (OK/KO), code retour 0 toujours (fail-safe).
set -euo pipefail

LOG="${MCP_CHECK_LOG:-$HOME/jarvis/logs/mcp-funnel-check.log}"
ENV_FILE="$HOME/jarvis-mcp/.env"
FUNNEL_HOST="pamerys-m4.tail1065ac.ts.net"
mkdir -p "$(dirname "$LOG")"

note() { printf '%s\t%s\t%s\n' "$(date -Is)" "$1" "$2" | tee -a "$LOG"; }

check_service() {
  if systemctl --user is-active --quiet jarvis-mcp.service; then
    note OK "service jarvis-mcp actif"
  else
    note KO "service jarvis-mcp inactif — systemctl --user restart jarvis-mcp"
  fi
}

check_garde() {
  local code
  code=$(curl -s -o /dev/null -w '%{http_code}' -m 5 http://127.0.0.1:8901/health || true)
  if [ "$code" = "404" ]; then
    note OK "garde secrète locale (health nu → 404)"
  else
    note KO "garde secrète : health nu → $code (attendu 404)"
  fi
}

check_funnel() {
  local code
  code=$(curl -s -o /dev/null -w '%{http_code}' -m 10 "https://$FUNNEL_HOST/health" || true)
  if [ "$code" = "404" ]; then
    note OK "funnel public répond (et refuse sans secret)"
  else
    note KO "funnel : $code — vérifier 'tailscale funnel status'"
  fi
}

check_secret_path() {
  # Lit le secret sans jamais l'afficher ; teste le health gardé en local.
  local sec code
  sec=$(grep -s '^JARVIS_MCP_PATH=' "$ENV_FILE" | cut -d= -f2 | tr -d '/')
  if [ -z "$sec" ]; then
    note KO "JARVIS_MCP_PATH absent de .env"
    return
  fi
  code=$(curl -s -o /dev/null -w '%{http_code}' -m 5 "http://127.0.0.1:8901/$sec/health" || true)
  if [ "$code" = "200" ]; then
    note OK "chemin secret opérationnel (17 outils derrière)"
  else
    note KO "chemin secret : $code (attendu 200)"
  fi
}

check_service
check_garde
check_secret_path
check_funnel
exit 0
