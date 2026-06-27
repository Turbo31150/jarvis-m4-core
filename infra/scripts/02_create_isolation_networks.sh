#!/usr/bin/env bash
# JARVIS — Phase 2 : Création des réseaux d'isolation pour containers sensibles
# Exécuter : bash /home/pamerys/jarvis/infra/scripts/02_create_isolation_networks.sh

set -euo pipefail

DB="/home/pamerys/jarvis/data/jarvis.db"

SENSITIVE_CONTAINERS=(
  jarvis-master
  jarvis-omega-bridge
  jarvis-linkedin-safe
  jarvis-trading-sentinel
  jarvis-production
  jarvis-integrity-watchdog
  jarvis-valise-auto
  jarvis-codex-telegram
  jarvis-lumen-token
  jarvis-whatsapp
)

echo "[Phase 2] Création réseaux d'isolation + mise à jour SQL"

for CTR in "${SENSITIVE_CONTAINERS[@]}"; do
  NET_NAME="jarvis-iso-${CTR#jarvis-}"

  # Créer le réseau isolé s'il n'existe pas
  if ! docker network inspect "$NET_NAME" &>/dev/null; then
    docker network create \
      --driver bridge \
      --internal \
      --opt com.docker.network.bridge.enable_icc=false \
      --label jarvis.role=isolation \
      --label jarvis.target="$CTR" \
      "$NET_NAME"
    echo "  [+] Réseau créé : $NET_NAME (--internal, ICC désactivé)"
  else
    echo "  [=] Réseau existant : $NET_NAME"
  fi

  # Mise à jour SQL
  sqlite3 "$DB" "UPDATE jarvis_endpoints SET isolation_network='${NET_NAME}' WHERE id='${CTR}';"
done

echo ""
echo "[OK] Réseaux d'isolation créés. Prochaine étape : connecter les containers isolés (script 04)"
echo "[!] IMPORTANT : ne pas déconnecter jarvis-net avant d'avoir déployé les buffers (script 03)"
