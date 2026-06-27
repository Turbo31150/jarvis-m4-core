#!/bin/bash
# Failover internet via Bluetooth PAN — Samsung Galaxy S9 (4G)
# S9 MAC: E0:D0:83:BC:4E:E6

S9_MAC="E0:D0:83:BC:4E:E6"
INET_OK=$(curl -sf --max-time 3 http://1.1.1.1 > /dev/null 2>&1 && echo 1 || echo 0)

log() { echo "[$(date +%H:%M:%S)] [BT-FAILOVER] $*"; }

if [ "$INET_OK" = "1" ]; then
  # Internet dispo via Ethernet — couper BT si actif
  if ip link show bnep0 > /dev/null 2>&1; then
    log "Internet Ethernet OK — désactivation BT-PAN"
    dhclient -r bnep0 2>/dev/null
    ip link set bnep0 down 2>/dev/null
  fi
  exit 0
fi

log "Internet Ethernet KO — activation S9 Bluetooth 4G..."

# Vérifier si bnep0 déjà actif
if ip link show bnep0 > /dev/null 2>&1 && ip route | grep -q bnep0; then
  log "bnep0 déjà actif"
  exit 0
fi

# Connecter S9 via BT-PAN
if ! bluetoothctl info "$S9_MAC" 2>/dev/null | grep -q "Connected: yes"; then
  bluetoothctl connect "$S9_MAC" 2>/dev/null &
  sleep 3
fi

# Activer NAP/PAN
bt-pan client "$S9_MAC" 2>/dev/null || rfcomm connect 0 "$S9_MAC" 2>/dev/null &
sleep 2

if ip link show bnep0 > /dev/null 2>&1; then
  dhclient bnep0 2>/dev/null
  GW=$(ip route show dev bnep0 | grep default | awk '{print $3}')
  [ -n "$GW" ] && ip route add default via "$GW" metric 200 2>/dev/null
  log "bnep0 UP — 4G S9 actif (GW: $GW)"
  
  # Ajouter NAT pour les containers Docker
  iptables -t nat -A POSTROUTING -s 172.17.0.0/16 -o bnep0 -j MASQUERADE 2>/dev/null
  iptables -t nat -A POSTROUTING -s 172.19.0.0/16 -o bnep0 -j MASQUERADE 2>/dev/null
  log "NAT Docker via bnep0 activé"
else
  log "ERREUR: bnep0 non disponible — S9 non connecté?"
  exit 1
fi
