#!/usr/bin/env bash
# Veilleur lien direct M4<->M6 : detecte carrier sans IP, configure le /24 direct, sonde M6.
set -uo pipefail
LOG=~/jarvis/logs/m6-link-watch.log
mkdir -p "$(dirname "$LOG")"
SELF_IP=10.42.0.1/24
PEER=10.42.0.230

log(){ printf '%s %s\n' "$(date '+%F %T')" "$*" | tee -a "$LOG"; }

log "demarrage veilleur (uid=$(id -u) $(id -un))"
while :; do
  for ifc in $(ls /sys/class/net | grep -E '^(enx|enp|eth)'); do
    carrier=$(cat "/sys/class/net/$ifc/carrier" 2>/dev/null || echo 0)
    [ "$carrier" = 1 ] || continue
    # Le lien direct passe par l'adaptateur USB-C (enx*), JAMAIS par le RJ45
    # natif enp47s0, qui est cable sur la box. Au reveil, ce dernier a un
    # carrier AVANT d'avoir son bail DHCP : il cochait donc « carrier UP sans
    # IPv4 » et recevait 10.42.0.1/24 — constate 2 fois. NetworkManager a
    # corrige ensuite, mais la fenetre suffisait a casser l'acces box.
    case "$ifc" in enx*) ;; *) continue ;; esac
    # Une interface pilotee par un profil NM nomme n'est pas un lien direct nu.
    # `nmcli` traduit STATE selon la locale (« connected » / « connecté ») :
    # tester la chaine exacte d'une seule langue rend le garde inoperant ailleurs.
    if nmcli -t -f DEVICE,STATE device status 2>/dev/null \
         | grep -E "^$ifc:(connected|connecté)" -q; then
      continue
    fi
    # interface avec lien mais sans adresse IPv4 => candidat lien direct
    if ! ip -4 addr show dev "$ifc" | grep -q 'inet '; then
      log "lien direct candidat: $ifc (carrier UP, sans IPv4)"
      if sudo -n ip addr add "$SELF_IP" dev "$ifc" 2>>"$LOG"; then
        log "adresse $SELF_IP posee sur $ifc"
      else
        log "ECHEC pose IP sur $ifc (sudo non disponible sans mot de passe)"
      fi
    fi
  done
  if ping -c1 -W2 "$PEER" >/dev/null 2>&1; then
    rtt=$(ping -c3 -W2 "$PEER" | tail -1 | cut -d= -f2)
    lms=$(curl -s -m 3 -o /dev/null -w '%{http_code}' "http://$PEER:1234/v1/models" || echo 000)
    log "M6 JOIGNABLE rtt=$rtt LMStudio_http=$lms"
  fi
  sleep 15
done
