import sqlite3
import os

db_path = "/home/pamerys/jarvis/jarvis_master.db"
# WAL : un seul écrivain à la fois sur une base très sollicitée,
# il faut attendre au lieu d'échouer sur "database is locked".
conn = sqlite3.connect(db_path, timeout=120)
conn.execute("PRAGMA busy_timeout=120000")
cur = conn.cursor()

# Ingestion de 500 tâches de production massive autonome
categories = [
    "AUDIT_SECURITE_RSE", "OPTIMISATION_GPU_VRAM", "BENCHMARK_LLM_LOCAL", 
    "PROSPECTION_AUTO_LEADS", "CODEUR_SCRAPER_AUTONOMOUS", "INDEXATION_RAG_FULL",
    "DELEGUATION_NOEUDS_M1_M6", "CONSOLIDATION_LOGS_SQLITE"
]

tasks_count = 0
for idx in range(1, 501):
    cat = categories[idx % len(categories)]
    title = f"[PRODUCTION-MASSIVE-{idx:04d}] Execution autonome pipeline {cat}"
    context = f"Tâche de production haute priorité générée pour utilisation continue des 928 agents et 697 dominos."
    try:
        cur.execute("""
        INSERT INTO tasks (title, context, status, progress, agent, machine)
        VALUES (?, ?, 'pending', 0, 'JARVIS-OMEGA', 'M1')
        """, (title, context))
        tasks_count += 1
    except Exception:
        pass

conn.commit()
conn.close()
print(f"PRODUCTION MASSIVE : {tasks_count} nouvelles tâches autonomes insérées dans jarvis_master.db !")
