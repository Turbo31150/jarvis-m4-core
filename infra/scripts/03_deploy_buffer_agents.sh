#!/usr/bin/env bash
# JARVIS — Phase 3 : Déploiement des containers "tampon" devant chaque container sensible
# Un buffer = socat proxy minimaliste, réseau jarvis-net uniquement, pas d'accès direct au target
# Exécuter : bash /home/pamerys/jarvis/infra/scripts/03_deploy_buffer_agents.sh

set -euo pipefail

DB="/home/pamerys/jarvis/data/jarvis.db"

# Format: "container_name:internal_port"
# Port 9742 = jarvis-pipeline standard, ajuster selon container
declare -A SENSITIVE_PORTS=(
  [jarvis-master]="9761"
  [jarvis-omega-bridge]="9742"
  [jarvis-linkedin-safe]="9742"
  [jarvis-trading-sentinel]="9742"
  [jarvis-production]="9742"
  [jarvis-integrity-watchdog]="9742"
  [jarvis-valise-auto]="9742"
  [jarvis-codex-telegram]="9742"
  [jarvis-lumen-token]="3001"
  [jarvis-whatsapp]="9742"
)

# Port d'écoute du buffer (offset +10000)
declare -A BUFFER_LISTEN_PORTS=(
  [jarvis-master]="19761"
  [jarvis-omega-bridge]="19742"
  [jarvis-linkedin-safe]="19743"
  [jarvis-trading-sentinel]="19744"
  [jarvis-production]="19745"
  [jarvis-integrity-watchdog]="19746"
  [jarvis-valise-auto]="19747"
  [jarvis-codex-telegram]="19748"
  [jarvis-lumen-token]="19749"
  [jarvis-whatsapp]="19750"
)

echo "[Phase 3] Déploiement buffers proxy"

for CTR in "${!SENSITIVE_PORTS[@]}"; do
  BUF_NAME="buf-${CTR#jarvis-}"
  TARGET_PORT="${SENSITIVE_PORTS[$CTR]}"
  LISTEN_PORT="${BUFFER_LISTEN_PORTS[$CTR]}"
  ISO_NET="jarvis-iso-${CTR#jarvis-}"

  # Skip si buffer déjà running
  if docker inspect "$BUF_NAME" &>/dev/null; then
    echo "  [=] Buffer déjà présent : $BUF_NAME"
    continue
  fi

  # Le buffer écoute sur jarvis-net, forward vers le container cible via son réseau iso
  docker run -d \
    --name "$BUF_NAME" \
    --network jarvis-net \
    --restart unless-stopped \
    --label jarvis.role=buffer \
    --label jarvis.target="$CTR" \
    --read-only \
    --cap-drop ALL \
    --security-opt no-new-privileges \
    alpine/socat \
    TCP-LISTEN:${LISTEN_PORT},fork,reuseaddr TCP:${CTR}:${TARGET_PORT}

  # Connecter aussi au réseau isolé pour atteindre la cible
  docker network connect "$ISO_NET" "$BUF_NAME"
  docker network connect "$ISO_NET" "$CTR" 2>/dev/null || true

  # Mise à jour SQL
  sqlite3 "$DB" "UPDATE jarvis_endpoints SET has_buffer=1, buffer_container_name='${BUF_NAME}' WHERE id='${CTR}';"
  sqlite3 "$DB" "UPDATE jarvis_endpoints SET status='buffer' WHERE id='${CTR}';" 2>/dev/null || true

  echo "  [+] Buffer déployé : $BUF_NAME → $CTR:$TARGET_PORT (écoute :$LISTEN_PORT)"
done

echo ""
echo "[OK] Buffers déployés. Vérifier avec : docker ps --filter label=jarvis.role=buffer"
