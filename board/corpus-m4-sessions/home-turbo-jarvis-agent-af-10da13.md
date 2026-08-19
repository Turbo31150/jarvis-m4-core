[user] Contexte : environnement JARVIS fraîchement (re)provisionné — des unit files systemd existent mais les scripts qu'ils référencent (ExecStart=) n'ont jamais été écrits sur cette machine. Base SQLite existante à `/home/turbo/jarvis/jarvis_master.db` avec une table `tasks` (colonnes au moins : id, title, agent, status, score, context, created_at, updated_at — vérifie avec `sqlite3 /home/turbo/jarvis/jarvis_master.db ".schema tasks"` avant d'écrire le code, adapte-toi au schéma réel).

Écris exactement ces fichiers, sûrs et non destructifs :

1. `/home/turbo/jarvis/bin/jarvis-executor.py` — python3, argparse avec `--tick N` (secondes). Boucle infinie : toutes les N secondes, lit jusqu'à 3 tâches `status='plan'` dans `tasks`, les marque `status='in_progress'`, log l'action (pas d'exécution réelle risquée — juste log + passe `status='done'` après log), dans `/home/turbo/jarvis/logs/executor.log`.

2. `/home/turbo/jarvis/bin/jarvis-master-routing-daemon.py` — python3, démon simple qui toutes les 60s vérifie la disponibilité de chaque backend LLM connu (127.0.0.1:1234 LM Studio, 192.168.1.85:1234 M1, 192.168.1.26:1234 M2 — timeout 2s chacun, ne bloque pas si down), écrit un JSON de routing dans `/home/turbo/jarvis/data/routing-index.json` avec le statut de chaque backend. Log dans `/home/turbo/jarvis/logs/master-routing.log`.

3. `/home/turbo/jarvis/scripts/multi_bash_autodetect_daemon.py` — python3, démon léger qui toutes les 30s compte les process bash actifs (`ps aux | grep bash |

[assistant] No leftover foreground processes. The pre-existing systemd timers (`jarvis-executor.timer`, `jarvis-master-routing.timer`, `jarvis-multi-bash.timer`, `jarvis-plan-refresh.timer`, `jarvis-cascade-ingest.timer`) picked up the newly-written scripts and auto-fired them once during my testing — expected since those units were already enabled and just waiting for the missing scripts. I stopped the running instances; the timers remain armed for their normal schedule (untouched, non-destructive).

[assistant] STATUS: DONE

Schéma réel `tasks` : `CREATE TABLE tasks (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, agent TEXT, status TEXT, score REAL, context TEXT, created_at DATETIME, updated_at DATETIME)` — conforme à l'hypothèse, aucune adaptation requise.

Fichiers créés (tous chmod +x) :
1. `/home/turbo/jarvis/bin/jarvis-executor.py`
2. `/home/turbo/jarvis/bin/jarvis-master-routing-daemon.py`
3. `/home/turbo/jarvis/scripts/multi_bash_autodetect_daemon.py`
4. `/home/turbo/jarvis/scripts/cascade-log-ingest.py`
5. `/home/turbo/jarvis/bin/task-feedback-loop.py`
6. `/home/turbo/jarvis/bin/dominos-batch`
7. `/home/turbo/jarvis/bin/jarvis-plan-refresh`

Tests (exécutés en fond avec `timeout` puis arrêt SIGTERM propre) :
- `jarvis-executor.py --tick 2/5` : boucle ok, aucune tâche `status='plan'` trouvée (114 381 tâches, toutes `done`), log OK dans `logs/executor.log`, arrêt propre confirmé.
- `jarvis-master-routing-daemon.py` : sondes 127.0.0.1:1234 (UP), 192.168.1.85:1234 M1 (DOWN), 192.168.1.26:1234 M2 (DOWN), sans blocage ; `data/routing-index.json` généré correctement, arrêt propre confirmé.
- `multi_bash_autodetect_daemon.py` : compte les process bash (8 puis 15), log OK, arrêt propre confirmé.
- `cascade-log-ingest.py` : `data/llm_cascade_log.jsonl` absent → créé vide + warning loggé, table `llm_cascade_log` créée (0 lignes, normal car fichier vide), exit 0.
- `task-feedback-loop.py --threshold 0.5 --max-feedback 10` : aucune tâche `done` avec score < 0.5 trouvée (colonne `score