#!/bin/bash
# JARVIS OS - Script de nettoyage pour ollama-mcp-server

PROCESS_NAME="ollama-mcp-server"

echo "🔍 Recherche des instances de $PROCESS_NAME..."
PIDS=($(pgrep -f "$PROCESS_NAME"))

if [ ${#PIDS[@]} -eq 0 ]; then
    echo "✅ Aucune instance de $PROCESS_NAME trouvée."
    exit 0
fi

echo "⚠️ ${#PIDS[@]} instance(s) trouvée(s). Tentative d'arrêt propre (SIGTERM)..."
pkill -f "$PROCESS_NAME"
sleep 2

REMAINING_PIDS=($(pgrep -f "$PROCESS_NAME"))
if [ ${#REMAINING_PIDS[@]} -gt 0 ]; then
    echo "🚨 ${#REMAINING_PIDS[@]} instance(s) résistent. Arrêt forcé (SIGKILL)..."
    pkill -9 -f "$PROCESS_NAME"
fi

echo "✅ Toutes les instances de $PROCESS_NAME ont été fermées."