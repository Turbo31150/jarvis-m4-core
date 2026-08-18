[assistant] `/home/turbo/jarvis-linux` existe encore — je vérifie ce qu'il contient et je localise chaque script référencé.

[assistant] `scripts/` existe bel et bien. Je vérifie son contenu réel, fichier par fichier.

[assistant] Le premier constat corrige la prémisse : `scripts/` existe toujours. J'élargis l'audit à **tous** les chemins de scripts référencés, pas seulement les 4 motifs.

[assistant] Audit terminé, aucun fichier modifié.

## Correction de la prémisse

Trois des quatre chemins annoncés comme morts **existent encore** :
- `/home/turbo/jarvis-linux` → symlink vivant vers `Workspaces/jarvis-linux`
- `/home/turbo/Workspaces/jarvis-linux/scripts/` → répertoire vivant, ~40 fichiers (dont `jarvis-tts.sh`, `lm-ask.sh`, `jarvis-planning-widget.py`)
- `jarvis-linux-repo` → confirmé inexistant, mais **zéro référence** dans le corpus audité

La réorganisation a été **partielle** : `scripts/` a gardé une partie de son contenu, et 8 scripts d'infra en sont partis vers `infra/scripts/{boot,tools,maintenance,monitoring}/`. C'est pour ça que le grep sur le préfixe donne des faux positifs — j'ai donc audité **tous** les chemins de scripts référencés (183 refs uniques) plutôt que les 4 motifs.

## Réparables — cible retrouvée (26 lignes)

| fichier:ligne | chemin mort | chemin correct |
|---|---|---|
| `plugins/local/jarvis-os/agents/incident-responder.md:14,37`<br>`agents/incident-responder.md:14,37`<br>`plugins/local/jarvis-os/agents/system-health-monitor.md:14`<br>`agents/system-health-monitor.md:14`<br>`plugins/local/jarvis-os/agents/jarvis-flow-dispatcher.md:41`<br>`plugins/local/jarvis-turbo/agents/jarvis-flow-dispatcher.md:41` | `~/Workspaces/jarvis-linux/scripts/jarvis-flow-check.sh` | `…/infra/scripts/monitoring/jarvis-flow-check.sh` |
| `plugins/local/jarvis-os/skills/jarvis-flow-controller/SKILL.md:159`<br>`plugins/local/jarvis-os/skills/task-distributor/SKILL.md:

[assistant] # Rapport final — chemins morts dans skills/plugins/agents/commands

Chemins relatifs à `/home/turbo/.claude/`.

## RÉPARABLES (28 lignes, 12 fichiers)

| fichier:ligne | chemin mort | statut | chemin correct proposé |
|---|---|---|---|
| `plugins/local/jarvis-os/agents/incident-responder.md:14` | `~/Workspaces/jarvis-linux/scripts/jarvis-flow-check.sh` | RÉPARABLE | `~/Workspaces/jarvis-linux/infra/scripts/monitoring/jarvis-flow-check.sh` |
| `plugins/local/jarvis-os/agents/incident-responder.md:37` | idem | RÉPARABLE | idem |
| `agents/incident-responder.md:14` | idem | RÉPARABLE | idem |
| `agents/incident-responder.md:37` | idem | RÉPARABLE | idem |
| `plugins/local/jarvis-os/agents/system-health-monitor.md:14` | idem | RÉPARABLE | idem |
| `agents/system-health-monitor.md:14` | idem | RÉPARABLE | idem |
| `plugins/local/jarvis-os/agents/jarvis-flow-dispatcher.md:41` | idem | RÉPARABLE | idem |
| `plugins/local/jarvis-turbo/agents/jarvis-flow-dispatcher.md:41` | idem | RÉPARABLE | idem |
| `plugins/local/jarvis-os/skills/jarvis-flow-controller/SKILL.md:159` | `~/Workspaces/jarvis-linux/infra/scripts/tools/jarvis-flow-check.sh` | RÉPARABLE | `…/infra/scripts/monitoring/jarvis-flow-check.sh` |
| `plugins/local/jarvis-os/skills/task-distributor/SKILL.md:73` | idem | RÉPARABLE | idem |
| `plugins/local/jarvis-os/agents/incident-responder.md:32` | `~/Workspaces/jarvis-linux/scripts/jarvis-domino-engine.sh` | RÉPARABLE | `~/Workspaces/jarvis-linux/infra/scripts/tools/jarvis-dom