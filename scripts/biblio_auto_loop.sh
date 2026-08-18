#!/bin/bash
# Boucle autonome 0-API / 0-Frais d'enrichissement perpétuel de la Bibliothèque Vivante JARVIS OS
# Interroge HuggingFace, GitHub, Reddit RSS, HackerNews et ArXiv
# Synthèse via http://127.0.0.1:1234 (qwen/qwen3.5-9b)

LOG_FILE="/home/pamerys/jarvis/logs/biblio_perp_loop.log"
echo "[$(date)] Démarrage du cycle d'enrichissement 0-API..." >> "$LOG_FILE"

while true; do
    echo "[$(date)] Exécution de la vague d'enrichissement 0-API..." >> "$LOG_FILE"
    python3 /home/pamerys/jarvis/scripts/jarvis_community_scraper.py >> "$LOG_FILE" 2>&1
    
    # Auto-commit Git de la base mise à jour
    cd /home/pamerys/Workspaces/jarvis-linux
    git add -A && git commit -m "chore(biblio): auto-enrichment 0-api $(date +%Y-%m-%d_%H:%M)" 2>/dev/null && git push origin main 2>/dev/null || true
    
    echo "[$(date)] Vague terminée. Pause de 15 minutes avant la prochaine vague..." >> "$LOG_FILE"
    sleep 900
done
