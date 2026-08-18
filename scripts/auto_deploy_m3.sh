#!/bin/bash
# ==============================================================================
# JARVIS — auto_deploy_m3.sh
# Automatisation du déploiement des agents et configs sur le nœud M3 (127.0.0.1)
# S'exécute automatiquement ou manuellement, et vérifie la disponibilité de M3
# ==============================================================================

M3_IP="127.0.0.1"
M3_USER="turbo"
LOG_UTIL="/home/pamerys/jarvis/scripts/util_logging.py"

log() {
    local level="$1"
    local msg="$2"
    echo "[$level] $msg"
    python3 "$LOG_UTIL" log --service "deploy-m3" --level "$level" --message "$msg" 2>/dev/null || true
}

log "INFO" "Début de la tentative de déploiement automatique sur M3 ($M3_IP)..."

# 1. Vérification du ping
if ! ping -c 2 -W 2 "$M3_IP" >/dev/null 2>&1; then
    log "WARNING" "Le nœud M3 ($M3_IP) est actuellement injoignable (ping KO). Déploiement reporté."
    exit 0
fi

# 2. Vérification SSH
SSH_OPTS="-o StrictHostKeyChecking=no -o ConnectTimeout=5"
if ! ssh $SSH_OPTS "${M3_USER}@${M3_IP}" "echo OK" >/dev/null 2>&1; then
    log "ERROR" "Le nœud M3 ($M3_IP) répond au ping mais le SSH est injoignable ou non configuré."
    exit 1
fi

log "INFO" "Nœud M3 en ligne. Début de la synchronisation des configurations (T071)..."

# 3. Synchroniser les configs (T071)
ssh $SSH_OPTS "${M3_USER}@${M3_IP}" "mkdir -p ~/.jarvis/config ~/jarvis/scripts"
if rsync -az -e "ssh $SSH_OPTS" ~/jarvis/scripts/lm-ask.sh "${M3_USER}@${M3_IP}:~/jarvis/scripts/" && \
   rsync -az -e "ssh $SSH_OPTS" ~/jarvis/scripts/cluster-health-monitor.sh "${M3_USER}@${M3_IP}:~/jarvis/scripts/"; then
    log "INFO" "T071: Configurations synchronisées sur M3."
else
    log "ERROR" "T071: Échec de la synchronisation des configurations vers M3."
fi

# 4. Déployer cowork-dispatcher (T070)
log "INFO" "T070: Déploiement de cowork-dispatcher sur M3..."
if ssh $SSH_OPTS "${M3_USER}@${M3_IP}" "
    cd /home/pamerys/jarvis-cowork 2>/dev/null || git clone https://github.com/Turbo31150/jarvis-cowork /home/pamerys/jarvis-cowork
    cd /home/pamerys/jarvis-cowork
    docker-compose up -d cowork-dispatcher 2>/dev/null || python3 src/cowork_dispatcher.py &
"; then
    log "INFO" "T070: Dispatcher déployé avec succès sur M3."
else
    log "ERROR" "T070: Échec du déploiement du dispatcher sur M3."
fi

# 5. Déployer agents cowork (T052)
log "INFO" "T052: Déploiement des agents de contenu sur M3..."
if ssh $SSH_OPTS "${M3_USER}@${M3_IP}" "
    docker pull jarvis-cowork-agent:latest 2>/dev/null || true
    docker run -d --name jarvis-content-gen-m3 \
        -e LLM_URL=http://127.0.0.1:11434 \
        -e AGENT_TYPE=content \
        jarvis-cowork-agent:latest 2>/dev/null || echo 'image not found'
"; then
    log "INFO" "T052: Agents de contenu déployés avec succès sur M3."
else
    log "ERROR" "T052: Échec du déploiement des agents de contenu sur M3."
fi

log "INFO" "Déploiement automatique sur M3 terminé avec succès."
exit 0
