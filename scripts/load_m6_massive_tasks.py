import sqlite3
import os
import time

db_path = "/home/pamerys/jarvis/jarvis_master.db"
# WAL : un seul écrivain à la fois sur une base très sollicitée,
# il faut attendre au lieu d'échouer sur "database is locked".
conn = sqlite3.connect(db_path, timeout=120)
conn.execute("PRAGMA busy_timeout=120000")
cur = conn.cursor()

m6_task_templates = [
    ("[M6-CABLE-DIRECT] Inférence & Délestage LLM Gemma3:4b (GTX 1660S)", "m6-ollama", "M6"),
    ("[M6-GPU-COMPUTE] Traitement parallèle & Calcul matriciel VRAM 6Go", "m6-gpu-worker", "M6"),
    ("[M6-DEEPSEEK-R1] Analyse logique & Raisonnement local zéro-token", "m6-deepseek", "M6"),
    ("[M6-NETWORK-LINK] Inspection débit câble direct 10.42.0.230 interface enxf8e43b9b67d4", "m6-sentinel", "M6"),
    ("[M6-CACHE-OPT] Maintenance & Flush VRAM instantané Ollama M6", "m6-optimizer", "M6")
]

inserted_m6 = 0
for idx in range(1, 301):
    for title_fmt, agent, machine in m6_task_templates:
        full_title = f"{title_fmt} - Slot #{idx:03d}"
        ctx = "Charge de travail lourde assignée au nœud M6 connecté en câble direct 10.42.0.230."
        try:
            cur.execute("""
            INSERT INTO tasks (title, context, status, progress, agent, machine)
            VALUES (?, ?, 'pending', 0, ?, ?)
            """, (full_title, ctx, agent, machine))
            inserted_m6 += 1
        except Exception:
            pass

conn.commit()
conn.close()

print(f"M6 CHARGÉ : {inserted_m6} nouvelles tâches de charge dédiées insérées pour le nœud M6 (GTX 1660S) !")
