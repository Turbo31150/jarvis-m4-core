import os
import glob
import sqlite3

repo_dir = "/home/pamerys/Workspaces/bibliotheque-prompts-multi-ia"
db_path = "/home/pamerys/jarvis/jarvis_master.db"

# WAL : un seul écrivain à la fois sur une base très sollicitée,
# il faut attendre au lieu d'échouer sur "database is locked".
conn = sqlite3.connect(db_path, timeout=120)
conn.execute("PRAGMA busy_timeout=120000")
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS system_prompts_library (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rel_path TEXT UNIQUE,
    category TEXT,
    filename TEXT,
    content TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

count = 0
for root, dirs, files in os.walk(repo_dir):
    for file in files:
        if file.endswith(".md") or file.endswith(".json") or file.endswith(".py") or file.endswith(".sh"):
            full_path = os.path.join(root, file)
            rel_path = os.path.relpath(full_path, repo_dir)
            category = rel_path.split('/')[0]
            
            try:
                with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                cur.execute("""
                INSERT INTO system_prompts_library (rel_path, category, filename, content)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(rel_path) DO UPDATE SET
                    content=excluded.content,
                    updated_at=CURRENT_TIMESTAMP
                """, (rel_path, category, file, content))
                count += 1
            except Exception as e:
                pass

conn.commit()
conn.close()
print(f"Ingestion terminée : {count} fichiers indexés dans jarvis_master.db (table system_prompts_library)")
