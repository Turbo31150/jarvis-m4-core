[user] Explore (medium) la surface CLI + SKILLS + OUTILS qui alimentent ou consomment la todolist/les dominos de JARVIS, dans /home/turbo/jarvis et ~/.claude/skills. Lecture seule, ne modifie rien. Objectif : savoir quels leviers CLI/skill/tool existent pour un "protocole de chargement de todolist avec CLI, skill, outil".

À couvrir :
- `cli/jarvis_master.py` (CLI orchestration : task add/list/run, domino, cascade, scan, seed, tool registry) — commandes exactes.
- `bin/bloc.sh` (router intention→bloc) + `~/labo/bibliotheque/lib/BLOCS-INDEX.tsv` (préchargement contexte).
- `bin/cascade-bibliotheques.py` (génère PLAN/CAHIER/TODO/PROTOCOLE/CONTEXTE_MAXIMAL) — sorties exactes.
- Les séries `~/labo/bibliotheque/series/*.sh` liées au planning/domino.
- Les skills pertinents : run-planning-autogen, jarvis-planning, audit-mode, remplir-bibliotheque, et tout skill "todolist/planning/domino".
- `orchestrator/` (registry.json, registry_build.py, qc_gate.py) — comment tools/agents/skills sont enregistrés.
- Les 3 dominos widget créés récemment (dominos-compiled/dominos/*.sh) + le runner bin/dominos.

RENDS :
1. Inventaire des commandes CLI + skills + séries qui touchent la todolist/dominos (chemin + rôle).
2. Comment le "préchargement de contexte biblio par tâche" fonctionne aujourd'hui (bloc.sh → context).
3. Ce qui MANQUE pour un protocole unifié (un point d'entrée CLI/skill qui charge une todolist énorme + contexte + la câble au widget/dominos).
4. Doublons/fragmentation entre ces outils (pl

[assistant] I'll explore the JARVIS todolist/domino surface. Let me start with parallel reconnaissance.

[assistant] Let me read the domino runner, planning engines, and the relevant skills in parallel.

[assistant] Let me locate the plugin skills and check the jarvis_master task DB + cascade command internals.

[assistant] The plugin skills aren't under ~/.claude/skills. Let me find them and check the cascade engine + domino-compile.

[assistant] The plugin skills are in `/home/turbo/jarvis/.claude/skills/`. Let me read the key ones.

[assistant] Let me capture the last wiring details: jarvis-planning-cli commands, widget trigger whitelist, and the "singular domino" orchestrator for fragmentation analysis.

[assistant] I have a complete picture. Here is my report.

---

# JARVIS — Surface CLI / SKILL / OUTIL de la todolist & dominos

## 1. Inventaire (chemin + rôle)

### A. CLI d'orchestration des tâches

**`/home/turbo/jarvis/cli/jarvis_master.py`** — argparse stdlib sur `jarvis_master.db`. Sous-commandes exactes (parser lignes 772-846) :
- `task add <text> [--context/-c]` · `task list` · `task run <id>` · `task score <id>`
- `loop {start,debug}`
- `scan` (propose next tasks depuis le contexte) · `seed` (données test)
- `cascade <query…>` → résout + **exécute** la chaîne domino (via `cli/cascade.py` `CascadeEngine`, chargé en lazy-import ligne 476, `CASCADE_PY=/home/turbo/jarvis/cli/cascade.py`)
- `plan <query…>` → **dry-run** de l'avalanche (`engine.avalanche(query, dry_run=True)`), le jumeau sûr de `cascade`
- `tools {list,find <term>,stats}` → registre `tool_map` (peuplé par `/home/turbo/jarvis/cli/seed_tools.py`, table créée avec catégories/keywords/priority)
- `audit {init,scan-local,scan-web,multi-agents,report,todo,cascade,run}` (parser 819-846) — délègue à `~/jarvis/scripts/jarvis-audit.sh`
- Free-text sans sous-commande connue (liste ligne 729) → `cascade.avalanche`

`task run` (260-355) exécute via `subprocess claudelm --no-system`, met à jour status/score, log dans `pipeline_log`. **Ce n'est PAS branché aux dominos** — c'est un dispatcher LLM générique.

### B. Moteurs de todolist (plusieurs, voir §4)

| Fichier | Rôle | Cible |
|---|---|---|
| `bin/planning-mega.py` | **Moteur 