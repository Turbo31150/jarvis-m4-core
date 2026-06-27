#!/bin/bash
# Attendre que Docker Swarm soit prêt
sleep 15

# Redéployer le stack Swarm
cd /home/pamerys/Workspaces/jarvis-linux
docker stack deploy -c infra/docker/docker-compose.swarm.yml jarvis_prod 2>&1 | logger -t jarvis-cowork-startup

# Démarrer le node_agent monitoring si pas actif
ss -tlnp | grep -q ':8421 ' || nohup python3 /home/pamerys/jarvis/monitoring/node_agent.py --port 8421 >> /tmp/node_agent.log 2>&1 &

# Démarrer le monitoring server si pas actif
ss -tlnp | grep -q ':8420 ' || (cd /home/pamerys/jarvis/monitoring && nohup python3 server.py >> /tmp/monitoring.log 2>&1 &)
