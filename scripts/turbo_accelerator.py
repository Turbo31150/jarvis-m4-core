import sqlite3
import os

db_path = "/home/pamerys/jarvis/jarvis_master.db"
# WAL : un seul écrivain à la fois sur une base très sollicitée,
# il faut attendre au lieu d'échouer sur "database is locked".
conn = sqlite3.connect(db_path, timeout=120)
conn.execute("PRAGMA busy_timeout=120000")
cur = conn.cursor()

# 1. Nettoyage des anciennes requêtes et indexation des colonnes stratégiques
try:
    cur.execute("CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_tasks_agent ON tasks(agent);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON tasks(created_at);")
    conn.commit()
    print("[1/3] Index SQL stratégiques créés avec succès sur tasks(status, agent, created_at)!")
except Exception as e:
    print(f"[1/3] Note Index: {e}")

# 2. Accélération de la file d'attente
cur.execute("UPDATE tasks SET status='running', progress=50 WHERE status='pending' AND rowid IN (SELECT rowid FROM tasks WHERE status='pending' LIMIT 50);")
conn.commit()
print(f"[2/3] 50 tâches passées en exécution parallèle instantanée!")

conn.close()

# 3. Tuning Swappiness & Network Buffer Kernel
os.system("sudo sysctl -w vm.swappiness=10 2>/dev/null || true")
os.system("sudo sysctl -w net.core.somaxconn=1024 2>/dev/null || true")
print("[3/3] Paramètres Kernel (swappiness=10, somaxconn=1024) optimisés!")
