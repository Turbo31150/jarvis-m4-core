[user] Contexte urgent : ~/.claude/CLAUDE.md vient d'être dégraissé de 2676 à 533 mots. Le contenu retiré référence désormais des skills QUI N'EXISTENT PAS — il est donc inaccessible. Tu dois en créer deux.

La source du contenu retiré est la sauvegarde : ~/.claude/CLAUDE.md.bak-avant-degraissage-20260814-133452 — lis-la en entier d'abord.

Crée DEUX skills dans ~/.claude/skills/ :

1. **jarvis-protocole** — récupère de la sauvegarde : le protocole obligatoire en 7 étapes, le journal SQL protocole_runs, le contexte maximal, la todolist dynamique, le widget planning :8899.
2. **jarvis-agents** — récupère : les familles d'agents, le dispatch parallèle, OpenClaw, les subagents, l'agent_index.

ATTENTION — CORRECTIONS OBLIGATOIRES, la sauvegarde contient des informations FAUSSES vérifiées aujourd'hui :
- ~/jarvis/bin/protocole.sh N'EXISTE PAS, alors que la sauvegarde le présente comme « point d'entrée unique ». Cherche le vrai (piste : ~/labo/bibliotheque/series/protocole.sh) et vérifie-le. Si aucun n'existe, dis-le franchement dans la skill au lieu de prescrire une commande morte.
- ~/jarvis/bin/bloc.sh et ~/jarvis-orchestration/SYSTEM/STARTUP.md N'EXISTENT PAS non plus.
- Les machines M1, M2, M5 et OL1 N'EXISTENT PLUS. Parc réel : M4 local, M6 sur 10.42.0.230:1234 (LM Studio, en panne actuellement), Rémi sur 100.113.121.61:11434 (Ollama, Tailscale). Toute adresse 192.168.1.x est morte.
- Vérifie le nombre réel d'agents dans agent_index de ~/jarvis/logs/jarvis_logs.db ou jarvis_master.

[assistant] I'll start by reading the backup file and verifying the environment claims in parallel.

[assistant] Thermal guard blocked the second batch (CPU 91°C). Let me read a sibling skill for format while retrying.

[assistant] Bash is thermally locked (95°C). Let me verify what I can via file tools meanwhile.

[assistant] Waiting on verification. Let me check the OpenClaw reality on M4 (docker vs CLI) — not covered by the running agent.

[assistant] Bash keeps hitting the thermal guard. Reading `/proc/net/tcp` directly instead (no shell).

[assistant] Ports decoded from `/proc/net/tcp` (LISTEN = state 0A): **8899 absent → widget planning DOWN**; 18800 (`0x4970`), 7777, 5678, 9222, 18789/18799, 8788 present; 9201 absent. M6 `10.42.0.230:1234` has ESTABLISHED connections. Writing `jarvis-protocole` now.

[assistant] Report received. Two corrections needed. Verifying the squad count discrepancy first.

[assistant] Confirmed: 49 squads, 215 agents, `jarvis_logs.db` has only 3 tables, and `contexte-maximal/` **does** exist. Correcting `jarvis-protocole`.

[assistant] Confirmed: 15 families × 3 roles + `pilotage`'s 4 = 49. Writing the families reference.

[assistant] Deux skills créées, toutes deux enregistrées et visibles au routage.

## Créé

| Skill | Fichiers |
|---|---|
| `~/.claude/skills/jarvis-protocole/` | `SKILL.md` + `references/briques-mortes.md` |
| `~/.claude/skills/jarvis-agents/` | `SKILL.md` + `references/familles.md`, `openclaw.md`, `boucles-thermiques.md` |

Format conforme aux skills sœurs (`jarvis-backends`, `jarvis-bibliotheque`, `jarvis-mcp-web`) : frontmatter `name`/`description`/`version`, déclencheurs français entre guillemets, corps en tableaux, détail volumineux en `references/`.

## Corrections faites — la sauvegarde était fausse sur 9 points

| Affirmation de la sauvegarde | Réalité vérifiée |
|---|---|
| `~/jarvis/bin/protocole.sh` = « point d'entrée unique » | **N'existe pas.** Aucun script n'enchaîne les 7 étapes → la skill dit franchement qu'on les déroule à la main. Le vrai `series/protocole.sh` existe mais c'est **autre chose** (doctrine anti-blocage) |
| `~/jarvis/bin/bloc.sh`, `~/jarvis/bin/cascade-bibliotheques.py` | N'existent pas → `labo/bibliotheque/series/bloc.sh` et `labo/moisson_remi_forge/bin/cascade-bibliotheques.py` |
| `~/jarvis-orchestration/SYSTEM/STARTUP.md` | Le dossier entier n'existe pas |
| **261 agents** (180 OpenClaw + 81 Claude Code) | **319** lignes dans `agent_index`. 261 = seulement les lignes portant une étiquette `container`; les 49 `skillmp-squads` + 9 `skill-logique` étaient oubliés. Sur disque : 215 `.md` + 192 dossiers OpenClaw — l'index est en retard |
| Table `protocole