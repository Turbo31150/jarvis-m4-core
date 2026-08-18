#!/usr/bin/env bash
# s9-failover.sh — bascule M1 sur la 4G du Galaxy S9 quand le lien principal perd Internet.
#
# Principe : on ne touche PAS aux profils NetworkManager (réversibilité + zéro reconnexion).
# En mode dégradé on pose une route par défaut manuelle metric 10 via le S9, qui bat la
# route DHCP du lien principal (metric 50). Au retour du principal, on la retire. Rien
# d'autre ne change : DNS globaux (1.1.1.1/8.8.8.8) et Tailscale restent valides.
#
# Hystérésis : 2 échecs consécutifs pour basculer, 3 succès pour revenir (anti-flap).
set -uo pipefail

PRIMARY_IF="${PRIMARY_IF:-enp42s0}"
PROBES=(1.1.1.1 9.9.9.9)
BACKUP_METRIC=10
FAIL_THRESHOLD=2
OK_THRESHOLD=3
IDLE_TETHER_OFF_AFTER=8   # ~3 min de lien principal sain avant de couper la radio
S9_SERIAL="${S9_SERIAL:-4357514238453498}"
ADB="${ADB:-/usr/bin/adb}"
export HOME="${ADB_HOME:-/home/pamerys}"
STATE_DIR=/run/s9-failover
LOG=/var/log/jarvis/s9-failover.log
TETHER_UP=/usr/local/sbin/s9-tether-up.sh

mkdir -p "$STATE_DIR" "$(dirname "$LOG")"
exec 9>"$STATE_DIR/lock"
flock -n 9 || exit 0   # une seule instance : garde anti-prolifération

log() { printf '[%s] %s\n' "$(date '+%F %T')" "$*" >>"$LOG"; logger -t s9-failover -- "$*"; }

read_ctr() { cat "$STATE_DIR/$1" 2>/dev/null || echo 0; }
write_ctr() { echo "$2" >"$STATE_DIR/$1"; }

# Interface de secours = celle pilotée par rndis_host (nom stable s9usb0 via udev,
# mais on retombe sur la détection par driver si la règle n'est pas encore appliquée).
backup_iface() {
  local i drv
  for i in /sys/class/net/*; do
    [ -e "$i/device/driver" ] || continue
    drv=$(basename "$(readlink -f "$i/device/driver")")
    [ "$drv" = "rndis_host" ] && { basename "$i"; return 0; }
  done
  return 1
}

# Internet réellement joignable PAR le lien principal (indépendant de la table de routage :
# -I force l'interface source, donc un test valide même quand la route par défaut est ailleurs).
primary_alive() {
  local p
  ip link show "$PRIMARY_IF" >/dev/null 2>&1 || return 1
  [ "$(cat "/sys/class/net/$PRIMARY_IF/carrier" 2>/dev/null)" = "1" ] || return 1
  for p in "${PROBES[@]}"; do
    ping -c1 -W2 -I "$PRIMARY_IF" "$p" >/dev/null 2>&1 && return 0
  done
  return 1
}

degraded() { ip route show default metric "$BACKUP_METRIC" 2>/dev/null | grep -q default; }

engage_backup() {
  local ifb gw
  # En mode éco le partage est éteint : le S9 retire alors la fonction RNDIS du
  # gadget USB, donc l'interface n'existe plus côté M1. Il faut la faire renaître
  # par adb AVANT de pouvoir router quoi que ce soit dessus.
  if ! ifb=$(backup_iface); then
    [ -x "$TETHER_UP" ] && "$TETHER_UP" >/dev/null 2>&1
    for _ in $(seq 1 20); do
      ifb=$(backup_iface) && break
      sleep 1
    done
  fi
  [ -n "${ifb:-}" ] || { log "BASCULE IMPOSSIBLE : aucune interface rndis (S9 débranché ?)"; return 1; }

  # Chemin rapide : le lien de secours est déjà debout (cas nominal). On ne touche
  # surtout pas au tethering — le relancer renumérote le sous-réseau et casse le bail.
  gw=$(ip route show default dev "$ifb" 2>/dev/null | awk '/default via/{print $3; exit}')

  if [ -z "${gw:-}" ]; then
    # Secours réellement absent : là seulement on réarme le partage côté téléphone.
    [ -x "$TETHER_UP" ] && "$TETHER_UP" >/dev/null 2>&1
    nmcli device connect "$ifb" >/dev/null 2>&1
    for _ in $(seq 1 12); do
      gw=$(ip route show default dev "$ifb" 2>/dev/null | awk '/default via/{print $3; exit}')
      [ -n "${gw:-}" ] && break
      sleep 1
    done
  fi
  [ -n "${gw:-}" ] || { log "BASCULE ÉCHOUÉE : pas de passerelle DHCP sur $ifb"; return 1; }

  ip route replace default via "$gw" dev "$ifb" metric "$BACKUP_METRIC" || return 1
  log "BASCULE 4G : défaut via $gw dev $ifb (metric $BACKUP_METRIC) — $PRIMARY_IF hors service"
  return 0
}

release_backup() {
  ip route del default metric "$BACKUP_METRIC" 2>/dev/null
  log "RETOUR NOMINAL : $PRIMARY_IF a récupéré Internet, route de secours retirée"
}

# Éco-thermique : laisser la radio 4G partager en permanence chauffe le téléphone
# (mesuré : batterie ~42 °C, CPU 68 °C au repos). Le partage n'a d'utilité que
# pendant une bascule, et engage_backup sait le réarmer en ~10 s. On le coupe donc
# dès que le lien principal est stable.
idle_tether_off() {
  local ifb
  ifb=$(backup_iface) || return 0
  ip route show default dev "$ifb" 2>/dev/null | grep -q default || return 0
  "$ADB" -s "$S9_SERIAL" shell service call tethering 3 i32 0 s16 com.android.shell s16 com.android.shell >/dev/null 2>&1 \
    && log "ÉCO : partage 4G mis en veille ($PRIMARY_IF stable) — réarmé automatiquement en cas de panne"
}

if primary_alive; then
  write_ctr fail 0
  ok=$(( $(read_ctr ok) + 1 )); write_ctr ok "$ok"
  if degraded && [ "$ok" -ge "$OK_THRESHOLD" ]; then
    release_backup
    write_ctr ok 0
  elif ! degraded && [ "$ok" -ge "$IDLE_TETHER_OFF_AFTER" ]; then
    idle_tether_off
    write_ctr ok 0
  fi
else
  write_ctr ok 0
  fail=$(( $(read_ctr fail) + 1 )); write_ctr fail "$fail"
  if [ "$fail" -eq "$FAIL_THRESHOLD" ]; then
    log "$PRIMARY_IF : $fail échecs consécutifs → tentative de bascule"
    engage_backup || write_ctr fail $((FAIL_THRESHOLD - 1))   # retentera au tick suivant
  elif [ "$fail" -gt "$FAIL_THRESHOLD" ] && ! degraded; then
    engage_backup || true
  fi
fi
exit 0
