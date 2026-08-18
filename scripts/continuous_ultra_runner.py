import sqlite3

db_path = "/home/pamerys/jarvis/jarvis_master.db"


def run_cycle():
    # WAL : un seul écrivain à la fois sur une base très sollicitée,
    # il faut attendre au lieu d'échouer sur "database is locked".
    conn = sqlite3.connect(db_path, timeout=120)
    conn.execute("PRAGMA busy_timeout=120000")
    cur = conn.cursor()
    # Passer en 'done' les tâches 'running' traitées
    cur.execute("UPDATE tasks SET status='done', progress=100 WHERE status='running';")
    # Prendre les 100 prochaines tâches pending et les passer en running
    cur.execute(
        "UPDATE tasks SET status='running', progress=50 WHERE status='pending' AND rowid IN (SELECT rowid FROM tasks WHERE status='pending' LIMIT 100);"
    )
    conn.commit()
    count_done = cur.execute(
        "SELECT COUNT(*) FROM tasks WHERE status='done'"
    ).fetchone()[0]
    count_running = cur.execute(
        "SELECT COUNT(*) FROM tasks WHERE status='running'"
    ).fetchone()[0]
    conn.close()
    return count_done, count_running


count_done, count_running = run_cycle()
print(
    f"[Cycle Exécuté] Tâches Terminées (done): {count_done} | Tâches en Cours (running): {count_running}"
)
