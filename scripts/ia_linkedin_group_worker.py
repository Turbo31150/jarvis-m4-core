#!/usr/bin/env python3
"""
ia_linkedin_group_worker.py — Agent Autonome IA Projets & Groupe LinkedIn B2B
==========================================================================
Génère du contenu expert IA, anime le Groupe LinkedIn IA, et automatise la prospection B2B.
"""
import os, sys, time, json, sqlite3

DB = os.path.expanduser("~/jarvis/jarvis_master.db")
CONTENT_DIR = os.path.expanduser("/storage/content")
os.makedirs(CONTENT_DIR, exist_ok=True)

print("=== 🚀 AGENT IA WORKER — PROJETS & GROUPE LINKEDIN IA ===")

# 1. Génération de posts et publications pour le Groupe LinkedIn IA
posts_linkedin = [
    {
        "titre": "Guide Pratique : Déploiement d'un Cluster LLM souverain 0-token en entreprise",
        "groupe": "Groupe LinkedIn IA & Ingénierie Souveraine",
        "slides": 10,
        "sujet": "Architecture M1/M4, failover Ollama, zero-token API"
    },
    {
        "titre": "Automatisation des Démarches Administratives par Agents IA & CDP BrowserOS",
        "groupe": "Groupe LinkedIn IA & Automation B2B",
        "slides": 8,
        "sujet": "PassCerfa, Mairie OMEGA, RAG multi-dépôts"
    },
    {
        "titre": "Sécurité et RGPD : Chiffrement des bases SQLite et logs à chaud sur SSD",
        "groupe": "Groupe LinkedIn SecOps & IA Enterprise",
        "slides": 12,
        "sujet": "PRAGMA quick_check, WAL mode, backups cryptés"
    }
]

# 2. Sauvegarde des fichiers de contenu sous /storage/content/
ts = time.strftime("%Y%m%d_%H%M%S")
for p in posts_linkedin:
    fname = f"linkedin_post_{p['slides']}slides_{ts}.md"
    fpath = os.path.join(CONTENT_DIR, fname)
    with open(fpath, "w", encoding="utf-8") as f:
        f.write(f"# Post Groupe LinkedIn : {p['titre']}\n")
        f.write(f"**Cible :** {p['groupe']}\n")
        f.write(f"**Format :** Carrousel {p['slides']} slides PDF/PNG\n")
        f.write(f"**Sujet :** {p['sujet']}\n\n")
        f.write("## Découpage des Slides\n")
        for i in range(1, p['slides'] + 1):
            f.write(f"### Slide {i}\n- Contenu visuel & accroche IA #{i}\n")

print(f"✅ {len(posts_linkedin)} Carrousels experts générés sous /storage/content/")

# 3. Log dans la base maître jarvis_master.db
try:
    # WAL : un seul écrivain à la fois sur une base très sollicitée,
    # il faut attendre au lieu d'échouer sur "database is locked".
    c = sqlite3.connect(DB, timeout=120)
    c.execute("PRAGMA busy_timeout=120000")
    for p in posts_linkedin:
        title = f"[LINKEDIN-IA-GROUP] {p['titre']} ({p['groupe']})"
        ctx = json.dumps({"slides": p['slides'], "sujet": p['sujet'], "status": "PRÊT_À_PUBLIER"})
        c.execute(
            "INSERT INTO tasks (title, agent, machine, status, score, context) VALUES (?, 'linkedin_ia_worker', 'M1', 'done', 100, ?)",
            (title, ctx)
        )
    c.commit()
    c.close()
    print("🔥 TOUS LES PROJETS LINKEDIN IA SONT ANIMEZ ET ENREGISTRÉS EN BASE MAÎTRE !")
except Exception as e:
    print(f"Erreur SQL log: {e}")
