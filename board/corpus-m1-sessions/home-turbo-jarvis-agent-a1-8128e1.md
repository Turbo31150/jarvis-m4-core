[user] Explore (medium) le pipeline de génération + chargement + consommation de la TODOLIST du système JARVIS, dans /home/turbo/jarvis. Objectif : cartographier le "protocole de chargement de todolist" existant pour un plan d'amélioration. Ne modifie RIEN (lecture seule).

Fichiers/zones à couvrir :
- `bin/planning-mega.py` (moteur canonique d'agrégation todolist unifiée)
- `bin/jarvis-plan.py` (overlay unified_plan.db)
- `bin/planning-autogen.py` / `planning-mega` (scans dynamiques)
- La table `tasks` dans `jarvis_master.db` (racine) + `data/unified_plan.db` (table plan/unified)
- `bin/jarvis-planning-widget.py` (consommation widget :8899 — comment il lit tasks/plan/dominos)
- Le skill `run-planning-autogen` (.claude/skills/run-planning-autogen/)
- Les timers systemd liés (jarvis-planning-autogen, task-autogen, jarvis-producer, jarvis-prod-loop)
- Le préchargement biblio par tâche (bloc.sh, BLOCS-INDEX)

RENDS une carte structurée :
1. Le FLUX actuel : sources → agrégation → DB → widget (avec fichiers:fonctions clés).
2. Les 3 couches (feeder/overlay/widget) et où se fait le dédup.
3. Ce qui existe déjà pour "charger une todolist énorme avec contexte préchargé".
4. Les LIMITES/goulots observables (dédup, double-compte, cadence timers, latence).
5. Points d'extension propres pour un "protocole de chargement" unifié CLI/skill.
Cite les chemins exacts. Ne propose pas de code — juste la carte de l'existant.

[assistant] Je vais explorer le pipeline TODOLIST de JARVIS. Commençons par cartographier les fichiers clés en parallèle.

[assistant] Lisons maintenant l'overlay `jarvis-plan.py`, le widget, `task-autogen.py`, et inspectons les schémas DB + timers.

[assistant] Examinons maintenant le widget (consommation), les timers systemd, les schémas DB et bloc.sh.

[assistant] Lisons le cycle, le refresh, bloc.sh, et cherchons dans le widget comment il lit tasks/plan/dominos.

[assistant] Vérifions qui écrit `source='domino'`/`'report'` dans unified_plan.db (jarvis-plan.py ne les gère pas) et lisons bloc.sh + la section widget tasks.

[assistant] Cherchons le producteur de lignes `source='domino'` dans le plan et le rôle du drainer/reconcile.

[assistant] Vérifions le rôle de jarvis-producer.py vis-à-vis unified_plan.db et confirmons l'absence actuelle de lignes domino/report dans le plan.

[assistant] J'ai une image complète du pipeline. Voici la carte structurée de l'existant.

---

# Carte du protocole de chargement TODOLIST — JARVIS (`/home/turbo/jarvis`)

## 0. Vue d'ensemble : DEUX pipelines parallèles vers DEUX bases

Il existe **deux systèmes de todolist distincts** qui coexistent et se recouvrent partiellement :

- **Pipeline A — "feeder direct"** : scans → écriture directe dans `jarvis_master.db` table `tasks` (status `pending`). Moteurs : `planning-mega.py`, `planning-autogen.py`, `task-autogen.py`.
- **Pipeline B — "overlay unifié"** : sources multiples → agrégation/dédup → `data/unified_plan.db` table `plan` (lecture seule des sources). Moteur : `jarvis-plan.py --sync`.

Les deux se rejoignent via le **drainer** (`jarvis-backlog-drainer.py`) qui pousse l'overlay B vers la file exécutable A, et se referment via le **reconcile**. Le **widget :8899** lit les DEUX bases.

---

## 1. FLUX actuel : sources → agrégation → DB → widget

### Pipeline A (feeder → `jarvis_master.db:tasks`)

Sources brutes (0-token, stdlib) :
- `bin/planning-autogen.py` — brique de scans réutilisable. Fonctions : `scan_incidents()` (health.log `/var/log/jarvis-service-health.log`), `scan_code_todos()` (grep TODO/FIXME/XXX sur `~/jarvis/bin|scripts`, `~/jarvis-linux/scripts`), `scan_bureau_projects()` (dossiers `~/Bureau` + cases `- [ ]`), `scan_git_dirty()` (repos git modifiés). Préchargement : `preload_biblio(title)` → appelle `bin/bloc.sh` → top blocs de `BLOCS-INDEX.tsv`.
- `bin/planning