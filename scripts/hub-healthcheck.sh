#!/usr/bin/env bash
#
# hub-healthcheck.sh — watchdog externe du hub LLM unifié (jarvis-chat-proxy)
#
# Détecte le cas (b) : process node vivant mais hub gelé / ne répond plus
# sur /health (que Restart=always ne couvre pas). Si /health ne répond pas
# après 3 tentatives (tolère un reload SIGHUP en cours), libère le port et
# relance le service.
#
# JAMAIS de `pkill -f chat_proxy` (tuerait le shell appelant). On utilise
# `fuser -k 18800/tcp` qui ne cible que le détenteur du port.
#
set -u

PORT=18800
URL="http://127.0.0.1:${PORT}/health"
SERVICE="jarvis-chat-proxy.service"
LOG="/home/pamerys/jarvis/data/hub-watchdog.log"
ATTEMPTS=3
SLEEP_BETWEEN=2

log() {
    printf '%s %s\n' "$(date '+%Y-%m-%dT%H:%M:%S%z')" "$1" >> "$LOG"
}

mkdir -p "$(dirname "$LOG")"

# 3 tentatives espacées de 2s pour éviter les faux positifs (reload/SIGHUP).
for i in $(seq 1 "$ATTEMPTS"); do
    if curl -sf --max-time 5 "$URL" >/dev/null 2>&1; then
        # Hub sain : ne RIEN faire (surtout pas de restart).
        exit 0
    fi
    [ "$i" -lt "$ATTEMPTS" ] && sleep "$SLEEP_BETWEEN"
done

# Hub gelé/injoignable après toutes les tentatives -> récupération.
log "INCIDENT hub injoignable sur ${URL} apres ${ATTEMPTS} tentatives -> liberation port + restart"

# Libère le port (cible uniquement le détenteur du port, pas pkill).
fuser -k "${PORT}/tcp" >/dev/null 2>&1 || true
sleep 2

systemctl --user restart "$SERVICE"
RC=$?
log "RESTART ${SERVICE} rc=${RC}"

exit 0
