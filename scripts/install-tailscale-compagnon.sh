#!/usr/bin/env bash
# Installe Tailscale sur la machine compagnon et la rattache au tailnet de Franck.
# Usage depuis la machine compagnon :
#   ssh -p 52222 turbo@81.64.100.212 'cat ~/jarvis/scripts/install-tailscale-compagnon.sh' | sudo bash
# Avec clé d'auth (aucune URL à valider) :
#   ... | sudo TS_AUTHKEY=tskey-auth-xxxx bash
set -euo pipefail

echo "[1/4] Installation de Tailscale…"
if command -v tailscale >/dev/null 2>&1; then
  echo "  déjà installé ($(tailscale version | head -1))"
else
  curl -fsSL https://tailscale.com/install.sh | sh
fi

echo "[2/4] Démarrage du démon…"
systemctl enable --now tailscaled

echo "[3/4] Rattachement au tailnet…"
if [ -n "${TS_AUTHKEY:-}" ]; then
  tailscale up --authkey="$TS_AUTHKEY" --accept-routes --hostname=rempc-compagnon
else
  echo "  >>> Une URL va s'afficher : ouvre-la et connecte-toi au tailnet"
  echo "  >>> remten341@gmail.com (celui de Franck), ou via le lien d'invitation"
  echo "  >>> qu'il t'a transmis (login.tailscale.com/uinv/...)."
  tailscale up --accept-routes --hostname=rempc-compagnon
fi

echo "[4/4] Vérification…"
MYIP=$(tailscale ip -4 | head -1)
echo "  IP Tailscale de cette machine : $MYIP"
echo -n "  Test vers M1 (100.112.114.32) : "
if tailscale ping -c 2 100.112.114.32 >/dev/null 2>&1; then
  echo "OK"
  echo
  echo "TERMINÉ. Accès direct chiffré, sans passer par la box :"
  echo "  ssh turbo@100.112.114.32"
  echo "  RDP  100.112.114.32:3389   (user rem / RemJarvis-2026!)"
  echo "  LLM  http://100.112.114.32:1234/v1   ·   hub http://100.112.114.32:18800"
else
  echo "pas encore joignable (autorisation du nœud en attente côté admin Tailscale)"
fi
echo
echo "Renvoie cette ligne à Franck :  IP Tailscale = $MYIP"
