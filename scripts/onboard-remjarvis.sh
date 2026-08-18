#!/usr/bin/env bash
# Câblage du nœud REMJARVIS (machine Linux de Rémi, hors LAN) dans l'écosystème JARVIS.
# Usage : onboard-remjarvis.sh <adresse> [port_ssh] [user]
#   adresse  = IP publique ou hostname DDNS de la machine de Rémi
#   port_ssh = défaut 22 (3389 = RDP, essayé en fallback si 22 fermé)
#   user     = défaut rempc
set -euo pipefail

ADDR="${1:?Usage: onboard-remjarvis.sh <adresse> [port_ssh] [user]}"
PORT="${2:-22}"
USER_="${3:-rempc}"
KEY="$HOME/.ssh/rem_jarvis_ed25519"
DB="$HOME/jarvis/jarvis_master.db"

echo "[1/6] Sonde port…"
if ! timeout 5 bash -c "echo > /dev/tcp/$ADDR/$PORT" 2>/dev/null; then
  echo "  port $PORT fermé, essai 3389…"
  PORT=3389
  timeout 5 bash -c "echo > /dev/tcp/$ADDR/$PORT" || { echo "ÉCHEC: aucun port SSH joignable sur $ADDR"; exit 1; }
fi
echo "  → $ADDR:$PORT OK"

echo "[2/6] Installation de la clé (mot de passe demandé une seule fois)…"
# SSHPASS peut être exporté par l'appelant pour éviter la saisie interactive
if [ -n "${SSHPASS:-}" ]; then
  sshpass -e ssh-copy-id -i "$KEY.pub" -p "$PORT" -o StrictHostKeyChecking=accept-new "$USER_@$ADDR"
else
  ssh-copy-id -i "$KEY.pub" -p "$PORT" -o StrictHostKeyChecking=accept-new "$USER_@$ADDR"
fi

echo "[3/6] Test connexion par clé…"
ssh -i "$KEY" -p "$PORT" -o BatchMode=yes -o ConnectTimeout=8 "$USER_@$ADDR" 'echo "OK $(hostname) — $(uname -r)"'

echo "[4/6] Entrée ~/.ssh/config…"
if ! grep -q "^Host remjarvis" "$HOME/.ssh/config" 2>/dev/null; then
  cat >> "$HOME/.ssh/config" <<EOF

Host remjarvis
    HostName $ADDR
    Port $PORT
    User $USER_
    IdentityFile $KEY
    ServerAliveInterval 30
    ServerAliveCountMax 4
EOF
  echo "  → alias 'ssh remjarvis' créé"
else
  sed -i "/^Host remjarvis/,/^$/{s/HostName .*/HostName $ADDR/;s/Port .*/Port $PORT/}" "$HOME/.ssh/config"
  echo "  → alias mis à jour"
fi

echo "[5/6] Inventaire ressources distantes…"
SPECS=$(ssh remjarvis 'echo "cpu=$(nproc) ram_mb=$(free -m|awk "/^Mem/{print \$2}") gpu=$(command -v nvidia-smi >/dev/null && nvidia-smi --query-gpu=name --format=csv,noheader|paste -sd+ || echo none) ollama=$(command -v ollama >/dev/null && echo yes || echo no) lms=$(curl -sf -m2 http://127.0.0.1:1234/v1/models >/dev/null && echo yes || echo no)"')
echo "  → $SPECS"

echo "[6/6] Enregistrement cluster_nodes…"
sqlite3 "$DB" "INSERT OR REPLACE INTO cluster_nodes VALUES ('$ADDR','REMJARVIS','UP','Compagnon de route Rémi — partage de puissance ($SPECS)','ssh:$PORT',datetime('now'))"
echo "TERMINÉ — nœud REMJARVIS câblé. Test: ssh remjarvis"
