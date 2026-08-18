#!/usr/bin/env bash
# phone-mouse-autocable-watch.sh — boucle de surveillance FIABLE du câblage USB S9.
# Tourne DANS la session user (accès adb + DISPLAY), lancée par le service systemd USER
# phone-mouse-autocable.service (Type=simple, restart auto). Poll léger 5s.
#
# Pourquoi cette boucle plutôt que le RUN+= udev en su :
#   - udev/systemd-udevd exécute RUN+= dans un contexte SANS session (pas de DISPLAY,
#     pas de XDG_RUNTIME_DIR user, PrivateTmp/kill-on-timeout) -> adb/xdotool échouent
#     ou sont tués (udev tue les process >quelques s). Le `su turbo -c` hérite mal de
#     l'env graphique et de la socket adb-server de l'utilisateur.
#   - Au branchement, adb n'a pas encore AUTORISÉ le device (dialogue RSA sur le tel) :
#     udev part trop tôt, la fenêtre unique est ratée. Ici on POLL jusqu'à autorisation.
#   - Idempotent : ne recâble QUE sur transition absent->device (front montant),
#     se calme quand débranché (aucun spam).
set -uo pipefail
AUTOCABLE="/home/pamerys/jarvis/scripts/phone-mouse-autocable.sh"
LOG="/tmp/phone-mouse-autocable.log"
POLL="${PM_POLL:-5}"
log(){ echo "[$(date '+%F %T')] [watch] $*" >> "$LOG"; }

export ANDROID_ADB_SERVER_PORT="${ANDROID_ADB_SERVER_PORT:-5037}"
adb start-server >/dev/null 2>&1 || true

prev="none"
log "watcher démarré (poll ${POLL}s)"
while :; do
  state="$(adb get-state 2>/dev/null || echo none)"
  [ -z "$state" ] && state="none"
  if [ "$state" = "device" ] && [ "$prev" != "device" ]; then
    log "front montant: device autorisé -> câblage"
    "$AUTOCABLE"
  elif [ "$state" != "device" ] && [ "$prev" = "device" ]; then
    log "S9 débranché/déconnecté (state=$state) -> repos"
  fi
  prev="$state"
  sleep "$POLL"
done
