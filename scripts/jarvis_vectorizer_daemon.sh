#!/bin/bash
# JARVIS Vectorizer Daemon Loop
echo "🧬 Démarrage du Démon Permanent de Vectorisation..."
while true; do
    python3 /home/pamerys/jarvis/scripts/jarvis_permanent_vectorizer.py
    echo "Relance automatique du vectoriseur..."
    sleep 5
done
