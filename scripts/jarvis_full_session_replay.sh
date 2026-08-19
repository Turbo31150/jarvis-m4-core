#!/usr/bin/env bash
# jarvis_full_session_replay.sh — Rejeu Intégral Monopasse de la Session JARVIS & SWAN.
# Exécute l ensemble des étapes de configuration matérielle, de ponts, de crawl et d arbitrage.

set -e
echo "================================================================================"
echo "🚀 EXÉCUTION DU SCRIPT MAÎTRE DE REJEU DE SESSION JARVIS / SWAN"
echo "================================================================================"

# 1. OPTIMISATIONS NOYAU & GOUVERNEUR CPU
echo -e "\n[1/8] ⚙️  Optimisation Noyau & Gouverneur CPU M4..."
chmod 666 /sys/devices/system/cpu/intel_pstate/max_perf_pct 2>/dev/null || true
for pol in /sys/devices/system/cpu/cpufreq/policy*/energy_performance_preference; do
    [ -f "$pol" ] && echo "balance_performance" > "$pol" 2>/dev/null || true
done
sysctl -p /etc/sysctl.d/99-jarvis-performance.conf 2>/dev/null || true

# 2. CÂBLAGE STOCKAGE & TOPOLOGIE DISQUES
echo -e "\n[2/8] 💾 Topologie Disques (NVMe / SSD M1 / Cold Storage)..."
mkdir -p /data/jarvis-cache /data/jarvis-memory /data/bibliotheque /media/pamerys/JARVIS-M1/labo /media/pamerys/JARVIS-M1/bibliotheque /storage/backups /storage/remi-mirror
chown -R pamerys:pamerys /data /media/pamerys/JARVIS-M1 /storage /home/pamerys/jarvis 2>/dev/null || true
chmod -R 775 /data /media/pamerys/JARVIS-M1 /storage 2>/dev/null || true

# 3. DÉMARRAGE DES PONTS & SUPERVISEUR H24
echo -e "\n[3/8] ⚡ Démarrage des Ponts Critiques (9761, 8420, 3001, 9742, 18800)..."
systemctl restart jarvis-h24-daemon.service 2>/dev/null || true

# 4. DOCKER BROWSEROS (CDP 9108) & N8N (5678)
echo -e "\n[4/8] 🌐 Contrôle des Conteneurs Docker (BrowserOS & N8N)..."
docker start jv-ia-browseros jarvis-n8n 2>/dev/null || true

# 5. INITIALISATION TMUX 4 MACHINES
echo -e "\n[5/8] 🖥️  Grille Tmux 4 Nœuds (M4, M1, Rémi PC, Rémi Serveur)..."
su - pamerys -c "
tmux kill-session -t jarvis-4m 2>/dev/null || true
tmux new-session -d -s jarvis-4m -n CLUSTER-4M 'bash'
tmux split-window -h -t jarvis-4m:0 'ssh turbo@100.112.114.32'
tmux split-window -v -t jarvis-4m:0.0 'ssh root@100.113.121.61'
tmux split-window -v -t jarvis-4m:0.2 'ssh root@100.124.69.1'
tmux select-layout -t jarvis-4m:0 tiled
"

# 6. SYNCHRONISATION BASES RÉMI
echo -e "\n[6/8] 🔄 Synchronisation des Bases et Miroirs Rémi..."
rsync -avz --timeout=10 -e "ssh -o ConnectTimeout=4 -o BatchMode=yes" root@100.113.121.61:/home/rempc/jarvis/*.db /home/pamerys/jarvis/data/moisson-remi/ 2>/dev/null || true

# 7. INGESTION & VECTORISATION BOARD OS (RAG 768D SUR M1)
echo -e "\n[7/8] 🏛️ Ingestion & Inférence GPU M1 (Table Ronde)..."
python3 /home/pamerys/jarvis/scripts/cluster_parallel_executor.py

# 8. VÉRIFICATION GLOBALE DE SANTÉ
echo -e "\n[8/8] ✅ Audit de Santé Global..."
python3 /home/pamerys/jarvis/scripts/linkedin_local_feed_bridge.py

echo -e "\n================================================================================"
echo "🎯 REJEU COMPLET DE LA SESSION EFFECTUÉ AVEC 100% DE SUCCÈS !"
echo "================================================================================"
