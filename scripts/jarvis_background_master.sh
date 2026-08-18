#!/bin/bash
# Master Loop autonome d'arrière-plan pour JARVIS OS

echo "[$(date)] Démarrage de la boucle master en arrière-plan..." >> ~/jarvis/logs/master_background.log

# 1. Scraping & Enrichissement de la bibliothèque vivante 0-API
python3 ~/jarvis/scripts/jarvis_community_scraper.py >> ~/jarvis/logs/community_scraper.log 2>&1

# 2. Moteur autonome LinkedIn & Mail Triage
python3 ~/jarvis/scripts/jarvis_linkedin_mail_autonomous_engine.py --mode linkedin >> ~/jarvis/logs/linkedin_mail.log 2>&1

# 3. Expansion de la bibliothèque
python3 ~/jarvis/scripts/biblio_massive_expansion.py >> ~/jarvis/logs/biblio_expansion.log 2>&1

# 4. Check santé cluster
bash ~/jarvis/scripts/cluster-health-monitor.sh >> ~/jarvis/logs/health.log 2>&1

# 5. Git Auto-sync
cd /home/pamerys/Workspaces/jarvis-linux && git add -A && git commit -m "chore(auto-loop): sync background tasks $(date +%Y-%m-%d_%H:%M)" 2>/dev/null && git push origin main 2>/dev/null || true

echo "[$(date)] Fin du cycle d'arrière-plan." >> ~/jarvis/logs/master_background.log
