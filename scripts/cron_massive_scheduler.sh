#!/bin/bash
# Cron scheduler massif JARVIS OS - Exécution haute cadence
DATE=$(date '+%Y-%m-%d %H:%M:%S')
python3 -c "
import sqlite3, os
conn = sqlite3.connect(os.path.expanduser('~/jarvis/jarvis_master.db'))
conn.execute('INSERT INTO tasks (title, context, status, agent, progress) VALUES (?, ?, ?, ?, 100)',
             ('Cron Auto Batch Exec — ' + '$DATE', 'System Automated Cron', 'done', 'cron-worker'))
conn.commit()
"
