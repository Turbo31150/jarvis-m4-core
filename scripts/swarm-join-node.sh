#!/bin/bash
# JARVIS Docker Swarm — Auto-join worker depuis n'importe quel nœud
# Usage: bash swarm-join-node.sh
# Ou depuis M4: ssh turbo@<IP> "bash -s" < swarm-join-node.sh

set -e
SWARM_MANAGER="192.168.1.62:2377"
WORKER_TOKEN="SWMTKN-1-21h25e7llcmpqzwjrnk1yonue4dwydr1wyaokxpscyjam30mvl-9co8jd8fy1a6mv1aqj25bluvq"

echo "[SWARM] Rejoindre le cluster JARVIS (manager: $SWARM_MANAGER)"

# Installer Docker si absent
if ! command -v docker &>/dev/null; then
  echo "[SWARM] Installation Docker..."
  curl -fsSL https://get.docker.com | sh
  usermod -aG docker $(whoami)
fi

# Quitter tout swarm existant
docker swarm leave --force 2>/dev/null || true

# Rejoindre
docker swarm join --token $WORKER_TOKEN $SWARM_MANAGER
echo "[SWARM] ✅ Nœud connecté"
