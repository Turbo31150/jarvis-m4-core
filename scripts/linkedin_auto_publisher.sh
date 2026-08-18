#!/usr/bin/env bash
# linkedin_auto_publisher.sh — Tâche Planifiée Autonome LinkedIn complète
# Publie automatiquement les posts basés sur la recherche du jour, les carrousels, commente, et agrandit le réseau B2B.

echo "=== 🚀 LANCEMENT TÂCHE PLANIFIÉE LINKEDIN RECHERCHE DU JOUR & NETWORK GROWTH ==="
date

# 1. Publication des posts synthétiques issus des recherches de la journée + ajout de contacts
python3 /home/pamerys/jarvis/scripts/linkedin_daily_research_autopilot.py

# 2. Publication autonome des carrousels PDF
python3 /home/pamerys/jarvis/scripts/linkedin_carousel_publisher.py

# 3. Publication autonome des commentaires sur-mesure via BrowserOS CDP
python3 /home/pamerys/jarvis/scripts/auto_post_linkedin_comments.py

# 4. Growth & Agrandissement du réseau (Likes & Contacts B2B)
python3 /home/pamerys/jarvis/scripts/linkedin_growth_network.py

echo "✅ TÂCHE PLANIFIÉE RECHERCHE & NETWORK GROWTH LINKEDIN EXÉCUTÉE !"
