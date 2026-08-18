[user] Explore (medium) les aspects PERFORMANCE de "l'application" JARVIS (widget bureau :8899 + planning + dominos + boucles de production), dans /home/turbo/jarvis. Lecture seule. Objectif : identifier concrètement comment la rendre PLUS PERFORMANTE, pour un plan d'amélioration.

À investiguer :
- `bin/jarvis-planning-widget.py` : coût des refresh, requêtes SQLite par tick, /data endpoint, ce qui est recalculé à chaque appel (unified_plan, dominos_state, chronologie…), throttle/latence.
- Les bases : tailles + WAL de jarvis_master.db (tasks 10k+), unified_plan.db (9980), domino_runs.db ; requêtes lourdes, index manquants (PRAGMA index_list sur tasks/plan).
- Les boucles de prod (jarvis-producer, jarvis-prod-loop, task-autogen, planning-autogen) : fréquence des timers, redondance, charge CPU/GPU induite (LLM local).
- Latence LLM local (LM Studio :1234, bug qwen empty déjà corrigé via /v1/completions) : impact sur les dominos/génération.
- Contention GPU (GPU2 ventilo mort, clock-capé) : impact sur les tâches LLM.
- Dédup / double-compte planning (3 couches) : coût.

RENDS :
1. Les goulots de performance concrets (fichier:ligne/fonction + pourquoi).
2. Requêtes SQLite améliorables (index, cache, requêtes recalculées à chaque tick).
3. Cadence des timers : redondances / sur-sollicitation.
4. 5-8 optimisations concrètes classées par impact/effort (sans les implémenter).
Cite les chemins exacts. Pas de code.

[assistant] I'll investigate the JARVIS performance aspects. Let me start by locating the key files.

[assistant] Now let me examine the widget backend, the loops, and the systemd timers in parallel.

[assistant] Let me examine the caching layer, the /data endpoint composition, and the HTML auto-refresh cadence.

[assistant] Let me examine the `dominos` script, the prod-loop/producer/planning-autogen service commands, and LLM/GPU references.

[assistant] Let me check the gpu()/timers() functions (subprocess cost per tick) and the producer's LLM production path.

[assistant] I have a complete picture. Let me record the plan file, then give you the findings.

[assistant] I have everything needed. Here are my findings on JARVIS performance.

## Contexte mesuré (état réel, pas les chiffres supposés)

- `~/jarvis/jarvis_master.db` = **262 Mo** mais **freelist_count = 0** → ce n'est PAS du bloat de pages libres. Le poids vient de tables lourdes **co-localisées** dans le même fichier : `disk_index` 77 Mo, `ai_cache` 34 Mo, `biblio_knowledge` 29 Mo, `cli_history` 24 Mo, `biblio_vectors` 24 Mo. La table `tasks` est petite (**6715 lignes** : done 6222 / pending 460 / to_validate 33) et **bien indexée** (`idx_tasks_status`, `idx_tasks_updated`, `idx_tasks_agent`).
- `data/unified_plan.db` = 14 Mo, table `plan` **2642 lignes**, **5 index** présents (source, prio, statut, norm, autoindex) — correctement indexée.
- `data/domino_runs.db` = 3 Mo, table `runs` = **54 604 lignes créées sur la seule journée du 23/07 (05:24→22:07, ~17 h)** = ~3200 insertions/heure. **Aucun index** (que la PK), **aucune purge/rotation** nulle part.
- Le widget lit bien le **fichier 262 Mo** (`DB = ~/jarvis/jarvis_master.db`, ligne 42) — pas la copie légère `data/jarvis_master.db` (4,8 Mo).

---

## 1. Goulots de performance concrets

**A. Le `/data` n'est PAS caché et recalcule TOUT à chaque tick (5 s)** — `bin/jarvis-planning-widget.py:875` `data()` et `:1550` `do_GET`. Le dict retourné appelle en direct, sans `cached()` : `dominos_state()`, `timers()`, `gpu()`, `agents()`, `routing()`, `n8n()`, `jarvis_linux()`, `strategie()`, `omega_mairie()`, `omega_todolist()`, `unified_pl