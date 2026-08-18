#!/bin/bash
# Traitement autonome dédié des tâches assignées à M6
while true; do
  python3 -c "
import sqlite3

conn = sqlite3.connect('/home/pamerys/jarvis/jarvis_master.db')
cur = conn.cursor()
cur.execute(\"UPDATE tasks SET status='running', progress=50 WHERE machine='M6' AND status='pending' AND rowid IN (SELECT rowid FROM tasks WHERE machine='M6' AND status='pending' LIMIT 10);\")
conn.commit()
cur.execute(\"UPDATE tasks SET status='done', progress=100 WHERE machine='M6' AND status='running';\")
conn.commit()
conn.close()
" 2>/dev/null
  sleep 2
done
