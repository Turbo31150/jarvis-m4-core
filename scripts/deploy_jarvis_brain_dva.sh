#!/bin/bash
# ==============================================================================
# Script de Déploiement Identique de JARVIS Brain sur jarvis-dva (Portable Rémi)
# Target Tailscale IP: 100.113.121.61
# ==============================================================================

set -euo pipefail

TARGET_IP="100.113.121.61"
TARGET_USER="turbo"

echo "=== Déploiement IDENTIQUE de JARVIS Brain vers ${TARGET_USER}@${TARGET_IP} ==="

# 1. Transfert de la base de données maître et du catalogue d'actions (64 actions)
echo "[1/4] Synchronisation des bases de données et schémas SQL..."
rsync -avz /home/pamerys/jarvis/jarvis_master.db ${TARGET_USER}@${TARGET_IP}:/home/pamerys/jarvis/jarvis_master.db

# 2. Transfert des scripts et exécutables de l'application JARVIS Brain
echo "[2/4] Synchronisation des scripts JARVIS Brain..."
rsync -avz \
  /home/pamerys/jarvis/scripts/jarvis_voice_hud.py \
  /home/pamerys/jarvis/scripts/jarvis_brain_intent.py \
  /home/pamerys/jarvis/scripts/jarvis_action.py \
  /home/pamerys/jarvis/scripts/jarvis-brain-launch.sh \
  ${TARGET_USER}@${TARGET_IP}:/home/pamerys/jarvis/scripts/

# 3. Transfert des répertoires de configuration et de logs
echo "[3/4] Synchronisation des configurations utilisateur (Voice HUD & Hotkeys)..."
rsync -avz /home/pamerys/.config/jarvis/ ${TARGET_USER}@${TARGET_IP}:/home/pamerys/.config/jarvis/

# 4. Exécution du launcher idempotent sur jarvis-dva
echo "[4/4] Activation et lancement de l'application JARVIS Brain sur ${TARGET_IP}..."
ssh ${TARGET_USER}@${TARGET_IP} "bash /home/pamerys/jarvis/scripts/jarvis-brain-launch.sh"

echo "=== Déploiement IDENTIQUE complété avec succès sur jarvis-dva ! ==="
