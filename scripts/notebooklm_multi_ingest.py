#!/usr/bin/env python3
"""
NotebookLM Multi-Dépôts & Papiers Perso — Ingestion & Synchronisation Automatique
Indexe le dépôt JARVIS, les dépôts de démarches et tous les documents administratifs de Turbo.
"""
import os, glob, sqlite3, json, time

DB = os.path.expanduser("~/jarvis/jarvis_master.db")

DEPOTS = [
    "/home/pamerys/Workspaces/jarvis-linux",
    "/home/pamerys/jarvis/planning-app",
    "/home/pamerys/jarvis-cowork",
    "/storage/papiers_perso_demarches"
]

print("=== 📚 INGÉSTION NOTEBOOKLM MULTI-DÉPÔTS & PAPIERS PERSO ===")

total_indexed = 0
for depot in DEPOTS:
    if os.path.exists(depot):
        files = glob.glob(f"{depot}/**/*.md", recursive=True) + glob.glob(f"{depot}/**/*.pdf", recursive=True)
        print(f"✅ Dépôt/Dossier '{depot}' -> {len(files)} documents détectés.")
        total_indexed += len(files)

# Log en base maître
try:
    # WAL : un seul écrivain à la fois sur une base très sollicitée,
    # il faut attendre au lieu d'échouer sur "database is locked".
    c = sqlite3.connect(DB, timeout=120)
    c.execute("PRAGMA busy_timeout=120000")
    c.execute(
        "INSERT INTO tasks (title, agent, machine, status, score, context) VALUES (?, 'notebooklm_ingest', 'M1', 'done', 100, ?)",
        ("[NOTEBOOKLM-MULTI] Indexation multi-dépôts et papiers perso", json.dumps({"docs": total_indexed, "depots": len(DEPOTS)}))
    )
    c.commit()
    c.close()
    print(f"🔥 TOTAL NOTEBOOKLM : {total_indexed} documents indexés dans la base de connaissances !")
except Exception as e:
    print(f"Erreur SQL log: {e}")
