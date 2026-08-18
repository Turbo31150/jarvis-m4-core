#!/bin/bash
# ==============================================================================
# Script de Déploiement Identique JARVIS Brain via Tailscale
# Target Tailscale Node: jarvis-dva (100.113.121.61)
# ==============================================================================

set -euo pipefail

TAILSCALE_IP="100.113.121.61"
TARGET_USER="turbo"

echo "=== VÉRIFICATION DU RÉSEAU TAILSCALE ==="
STATUS=$(tailscale status 2>&1)
if echo "$STATUS" | grep -q "jarvis-dva"; then
    echo "✅ Nœud Tailscale $TAILSCALE_IP (jarvis-dva) détecté et actif !"
else
    echo "❌ Erreur: Le nœud $TAILSCALE_IP (jarvis-dva) n'est pas accessible sur Tailscale."
    exit 1
fi

echo ""
echo "=== DÉPLOIEMENT IDENTIQUE DE JARVIS BRAIN ==="

# 1. Copie de la base SQLite maître (64 actions)
echo "[1/4] Transfert de la base de données maître jarvis_master.db via Tailscale..."
rsync -avz -e "ssh -o StrictHostKeyChecking=no" /home/pamerys/jarvis/jarvis_master.db ${TARGET_USER}@${TAILSCALE_IP}:/home/pamerys/jarvis/jarvis_master.db

# 2. Copie des composants applicatifs JARVIS Brain
echo "[2/4] Transfert des scripts et exécutables JARVIS Brain..."
rsync -avz -e "ssh -o StrictHostKeyChecking=no" \
  /home/pamerys/jarvis/scripts/jarvis_voice_hud.py \
  /home/pamerys/jarvis/scripts/jarvis_brain_intent.py \
  /home/pamerys/jarvis/scripts/jarvis_action.py \
  /home/pamerys/jarvis/scripts/jarvis-brain-launch.sh \
  ${TARGET_USER}@${TAILSCALE_IP}:/home/pamerys/jarvis/scripts/

# 3. Copie des fichiers de configuration utilisateur (HUD / Hotkeys)
echo "[3/4] Transfert des configurations ~/.config/jarvis/..."
rsync -avz -e "ssh -o StrictHostKeyChecking=no" \
  /home/pamerys/.config/jarvis/ \
  ${TARGET_USER}@${TAILSCALE_IP}:/home/pamerys/.config/jarvis/

# 4. Lancement et activation à distance via Tailscale
echo "[4/4] Activation et lancement idempotent sur jarvis-dva..."
ssh -o StrictHostKeyChecking=no ${TARGET_USER}@${TAILSCALE_IP} "bash /home/pamerys/jarvis/scripts/jarvis-brain-launch.sh"

echo ""
echo "✅ Déploiement identique terminé avec succès via Tailscale !"
