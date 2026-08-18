#!/usr/bin/env bash
# planning-cycle.sh — CYCLE PERMANENT du planning (branché sur jarvis-planning-autogen.timer, 3h).
# Couches séparées : PLANNING (mega) → DRAIN (overlay→file exécutable) → RECONCILE (ferme la boucle).
# L'EXÉCUTION est faite en continu par jarvis-task-auto (5min) + prod-loop (30min) sur la file pending.
# Résultat : les tâches « à faire » de l'overlay descendent, sont exécutées, et le compteur baisse.
set -uo pipefail
BIN="$HOME/jarvis/bin"

echo "## planning-cycle $(date '+%F %T')"

# 1. PLANNING : régénère la file dynamique (scans + reports + business) + préchargement
python3 "$BIN/planning-mega.py" 2>&1 | tail -3

# 2. DRAIN : pont overlay → file exécutable (priorisé P0→P1→P2, cap anti-flood)
# RYTHME ADAPTATIF (pas de --limit) : draine pour maintenir la file ~setpoint
python3 "$BIN/jarvis-backlog-drainer.py" --go 2>&1 | tail -1

# 3. RECONCILE : ferme la boucle (les drainées déjà traitées → overlay done → compteur baisse)
python3 "$BIN/jarvis-backlog-reconcile.py" --go 2>&1 | tail -1

echo "✅ cycle terminé — file exécutable alimentée, boucle fermée"
