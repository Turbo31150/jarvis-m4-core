#!/bin/bash
# Script d'exécution continue et d'activation complète des Agents et Dominos
echo "[1/3] Activation et Recompilation de tous les Dominos..."
/home/pamerys/jarvis/bin/dominos recompile >/dev/null 2>&1

echo "[2/3] Exécution de la patrouille Master OpenClaw..."
# Garde anti-prolifération : ne relancer QUE si aucune instance ne tourne déjà.
# Sans ça, ce cron */5 empilait 68 orphelins (load 40+, freeze) — root cause 2026-07-29.
if ! pgrep -f 'openclaw-master\.py patrol' >/dev/null 2>&1; then
  python3 /home/pamerys/Workspaces/jarvis-linux/infra/scripts/deployment/openclaw-master.py patrol >/dev/null 2>&1 &
fi

echo "[3/3] Exécution autonome Domino Engine..."
if ! pgrep -f 'domino_autogen_engine\.py' >/dev/null 2>&1; then
  python3 /home/pamerys/jarvis/scripts/domino_autogen_engine.py >/dev/null 2>&1 &
fi

echo "Tous les agents et dominos sont engagés en production."
