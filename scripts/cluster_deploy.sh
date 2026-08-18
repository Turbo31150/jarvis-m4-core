#!/usr/bin/env bash
# ==============================================================================
# JARVIS — cluster_deploy.sh v1.0
# Déploiement et exécution de scripts en parallèle sur les nœuds du cluster (M1, M3)
# ==============================================================================

set -uo pipefail

# Configuration SSH
SSH_KEY="/home/pamerys/jarvis/infra/config/ssh-access/jarvis_ed25519"
SSH_OPTS="-o StrictHostKeyChecking=no -o ConnectTimeout=5"
[ -f "${SSH_KEY}" ] && SSH_OPTS="${SSH_OPTS} -i ${SSH_KEY}"

# Nœuds du cluster
declare -A NODES=(
    [M1]="turbo@192.168.0.10"
    [M3]="turbo@127.0.0.1"
)

usage() {
    echo "Usage: $0 <chemin_vers_script_local>"
    echo "Exemple: $0 ~/jarvis/scripts/watchdog_critical.sh"
    exit 1
}

[ $# -lt 1 ] && usage

LOCAL_SCRIPT="$1"
[ ! -f "${LOCAL_SCRIPT}" ] && {
    echo "❌ Le script local '${LOCAL_SCRIPT}' n'existe pas."
    exit 2
}

SCRIPT_NAME=$(basename "${LOCAL_SCRIPT}")
REMOTE_PATH="/tmp/${SCRIPT_NAME}"

echo "=== Déploiement du script: ${SCRIPT_NAME} ==="

run_on_node() {
    local node="$1"
    local target="${NODES[$node]}"
    
    echo "  [${node}] Connexion à ${target}..."
    
    # 1. Copier le script
    if scp ${SSH_OPTS} "${LOCAL_SCRIPT}" "${target}:${REMOTE_PATH}" >/dev/null 2>&1; then
        echo "  [${node}] ✓ Script copié."
        
        # 2. Rendre exécutable et lancer
        echo "  [${node}] Exécution en cours..."
        if out=$(ssh ${SSH_OPTS} "${target}" "chmod +x ${REMOTE_PATH} && sudo ${REMOTE_PATH} 2>&1"); then
            echo -e "  [${node}] {GREEN}✓ Succès !{RESET}\n--- Output ${node} ---\n${out}\n---------------------"
        else
            echo -e "  [${node}] {RED}❌ Échec de l'exécution.{RESET}\n--- Output ${node} (erreur) ---\n${out}\n---------------------"
        fi
        
        # 3. Nettoyer
        ssh ${SSH_OPTS} "${target}" "rm -f ${REMOTE_PATH}" >/dev/null 2>&1
    else
        echo "  [${node}] ❌ Impossible de copier le script (nœud hors ligne ou SSH bloqué)."
    fi
}

# Remplacement couleurs pour l'affichage console
GREEN="\033[92m"
RED="\033[91m"
RESET="\033[0m"

# Lancement en parallèle
PID_M1=0
PID_M3=0

# Exécution en tâche de fond pour M1
(run_on_node "M1" | sed "s/{GREEN}/${GREEN}/g; s/{RED}/${RED}/g; s/{RESET}/${RESET}/g") &
PID_M1=$!

# Exécution en tâche de fond pour M3
(run_on_node "M3" | sed "s/{GREEN}/${GREEN}/g; s/{RED}/${RED}/g; s/{RESET}/${RESET}/g") &
PID_M3=$!

# Attendre la fin des deux processus
wait ${PID_M1} ${PID_M3}

echo "=== Déploiement cluster terminé ==="
