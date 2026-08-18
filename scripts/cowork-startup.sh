#!/bin/bash
# Attendre que Docker Swarm soit prêt
sleep 15

ENV_FILE=/home/pamerys/jarvis-linux/.env
OPENCLAW_CONF=/home/pamerys/.openclaw/openclaw.json

die() {
    logger -t jarvis-cowork-startup "ERREUR: $* — deploiement annule"
    echo "jarvis-cowork-startup: $*" >&2
    exit 1
}

[ -r "$ENV_FILE" ]      || die "$ENV_FILE illisible"
[ -r "$OPENCLAW_CONF" ] || die "$OPENCLAW_CONF illisible"

# Variables substituées dans docker-compose.swarm.yml. On n'extrait que les deux
# variables nécessaires : sourcer tout le .env dans ce shell exposerait la
# trentaine de secrets qu'il contient aux daemons lancés plus bas.
TELEGRAM_TOKEN=$(. "$ENV_FILE" >/dev/null 2>&1; printf '%s' "$TELEGRAM_TOKEN") || die "lecture de TELEGRAM_TOKEN impossible"
TELEGRAM_CHAT=$(. "$ENV_FILE" >/dev/null 2>&1; printf '%s' "$TELEGRAM_CHAT")   || die "lecture de TELEGRAM_CHAT impossible"

# Token de la gateway OpenClaw (consommé par antigravity-mcp)
OPENCLAW_GATEWAY_TOKEN=$(python3 -c "import json;print(json.load(open('$OPENCLAW_CONF'))['gateway']['auth']['token'])") \
    || die "gateway.auth.token illisible dans $OPENCLAW_CONF"

export TELEGRAM_TOKEN TELEGRAM_CHAT OPENCLAW_GATEWAY_TOKEN

# Une substitution vide réécrirait silencieusement la spec des services concernés
for var in TELEGRAM_TOKEN TELEGRAM_CHAT OPENCLAW_GATEWAY_TOKEN; do
    [ -n "${!var}" ] || die "$var est vide"
done

# Redéployer le stack Swarm
cd /home/pamerys/Workspaces/jarvis-linux
docker stack deploy -c infra/docker/docker-compose.swarm.yml jarvis_prod 2>&1 | logger -t jarvis-cowork-startup

# Démarrer le node_agent monitoring si pas actif
ss -tlnp | grep -q ':8421 ' || nohup python3 /home/pamerys/jarvis/monitoring/node_agent.py --port 8421 >> /tmp/node_agent.log 2>&1 &

# Démarrer le monitoring server si pas actif
ss -tlnp | grep -q ':8422 ' || (cd /home/pamerys/jarvis/monitoring && nohup python3 server.py >> /tmp/monitoring.log 2>&1 &)
