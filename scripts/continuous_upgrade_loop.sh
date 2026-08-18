#!/bin/bash
# Boucle de mise à jour continue JARVIS OS (Loop ininterrompue)

echo "=== Démarrage de la boucle de mise à jour continue JARVIS OS ==="

for repo in /home/pamerys/Workspaces/jarvis-linux /home/pamerys/Workspaces/planning-app /home/pamerys/Workspaces/bibliotheque-prompts-multi-ia; do
  if [ -d "$repo/.git" ]; then
    echo "[Git Update] $repo..."
    cd "$repo" && git pull origin main --quiet 2>/dev/null || true
  fi
done

echo "[APT Update] Vérification des mises à jour paquets..."
sudo apt-get update -qq && sudo apt-get --only-upgrade install -y conky-all wkhtmltopdf xvfb 2>/dev/null || true

echo "[SQLite Maintenance] Optimisation des bases..."
sqlite3 /home/pamerys/jarvis/jarvis_master.db "PRAGMA optimize;" 2>/dev/null || true
sqlite3 /home/pamerys/jarvis/logs/jarvis_logs.db "PRAGMA optimize;" 2>/dev/null || true

echo "[Domino Recompile] Recompilation continue..."
/home/pamerys/jarvis/bin/dominos recompile >/dev/null 2>&1

echo "[OpenClaw Patrol] Exécution patrouille..."
# Garde anti-prolifération : ne relancer QUE si aucune instance ne tourne déjà.
# Ce script est en cron `* * * * *` : sans garde, il empilait un patrol
# orphelin (ppid=1) PAR MINUTE — 73 accumulés en 1h10 le 2026-07-29.
# Même root cause que le cron */5 de run_all_dominos_agents.sh (freeze M1).
if ! pgrep -f 'openclaw-master\.py patrol' >/dev/null 2>&1; then
  python3 /home/pamerys/Workspaces/jarvis-linux/infra/scripts/deployment/openclaw-master.py patrol >/dev/null 2>&1 &
fi

echo "[Done] Boucle terminée, prêt pour le cycle suivant."
