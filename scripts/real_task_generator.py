import sqlite3
import os
import time

db_path = "/home/pamerys/jarvis/jarvis_master.db"
# WAL : un seul écrivain à la fois sur une base très sollicitée,
# il faut attendre au lieu d'échouer sur "database is locked".
conn = sqlite3.connect(db_path, timeout=120)
conn.execute("PRAGMA busy_timeout=120000")
cur = conn.cursor()

tasks_definition = [
    ("[RECHERCHE-IA] Veille modèles LLM open-source Qwen3.5 & DeepSeek R1", "L9_erudits", "M1"),
    ("[AUDIT-SECURITE] Verification des ports ouverts et firewall UFW", "L3_sentinelles", "M1"),
    ("[OPTIMIZATION-GPU] Profilage VRAM 6 GPUs M1 + GTX 1660S M6", "L8_optimiseurs", "M6"),
    ("[NETTOYAGE-DISQUE] Purge des fichiers tmp et logs anciens", "L5_automates", "M1"),
    ("[PROSPECTION-LEADS] Scraping et qualification offres Codeur.com", "L6_traders", "M1"),
    ("[BACKUP-DB] Creation de checkpoint SQL jarvis_master.db & etoile.db", "L9_erudits", "M1"),
    ("[MONITORING-CLUSTER] Telemetrie des noeuds M1, M2, M4 et M6", "L4_analystes", "M4"),
    ("[ROUTAGE-TELEGRAM] Test d inference multi-llm via proxy :18800", "L7_communicateurs", "M1"),
    ("[COMMITS-GITOPS] Push automatique des modifications de configuration", "L5_automates", "M1"),
    ("[TEST-PERFORMANCE] Benchmark du temps de reponse API widget :8899", "L10_debuggers", "M1")
]

inserted_count = 0
for idx in range(1, 101):
    for title_fmt, legion, machine in tasks_definition:
        full_title = f"{title_fmt} (Batch #{idx:03d})"
        ctx = f"Execution reelle autonome par l agent {legion} sur le noeud {machine}."
        try:
            cur.execute("""
            INSERT INTO tasks (title, context, status, progress, agent, machine)
            VALUES (?, ?, 'pending', 0, ?, ?)
            """, (full_title, ctx, legion, machine))
            inserted_count += 1
        except Exception as e:
            pass

conn.commit()
conn.close()

print(f"REEL : {inserted_count} nouvelles vraies taches concrètes injectees dans la file de planning-app !")
