[user] Exécute la séquence de démarrage complète JARVIS :

1. Vérifie l'état système (CPU/RAM/GPU/Load)
2. Active le mode WAL SQLite + pragmas performance
3. Charge la table `skill_triggers` (57 patterns de détection par mots-clés)
4. Vérifie les 31 agents enregistrés dans `agent_registry`
5. Synchronise avec GitHub (git status + log)
6. Lance les agents de monitoring en parallèle
7. Affiche le rapport de démarrage compact

Utilise le skill `demarrage` pour exécuter cette séquence.

## Audit QA des hooks (anti hook mort)

Avant de conclure le démarrage, vérifier l'intégrité des hooks `settings.json` (aucun script manquant ou non exécutable, contrat JSON respecté) en exécutant le point d'entrée QA et en relayant son verdict :

```bash
bash /home/turbo/.claude/hooks/qa/hook-qa-demarrage.sh
```

Si le verdict est `HOOK QA: ECHEC` (exit 1), corriger les scripts manquants/non-exécutables listés avant de router vers ces hooks (remplace la détection manuelle de hooks morts, ex: jarvis-tts.sh absent).

[user] Base directory for this skill: /home/turbo/.claude/skills/run-jarvis-demarrage

# run-jarvis-demarrage

One bash driver that runs the verified JARVIS startup smoke: system snapshot →
SQLite WAL warm-up → agent counts → git → monitoring procs → cluster ping. It's
the reproducible core of the heavier `jarvis-turbo:demarrage` plugin skill, with
the **correct SQL table names** baked in (the plugin's prose references tables
that don't exist — see Gotchas). Paths relative to repo root `/home/turbo/jarvis`.

Driver: **`.claude/skills/run-jarvis-demarrage/demarrage.sh`**.

## Run (agent path)
```bash
cd /home/turbo/jarvis
bash .claude/skills/run-jarvis-demarrage/demarrage.sh
# or target another DB:
DB=data/jarvis.db bash .claude/skills/run-jarvis-demarrage/demarrage.sh
```
Read-only except `PRAGMA journal_mode=WAL` (persistent + idempotent). Prints a
7-section report; last line is `### démarrage smoke done`.

## What each section checks
| # | Section | Source |
|---|---|---|
| 1 | CPU load / RAM / per-GPU temp+VRAM | `uptime`, `free`, `nvidia-smi` |
| 2 | SQLite WAL + synchronous/cache/temp pragmas + `quick_check` | `sqlite3 data/jarvis.db` |
| 3-4 | Row counts: `jarvis_agent_registry`, `jarvis_agents`, `llm_backends`, `jarvis_cluster_map` | same DB |
| 5 | Branch / HEAD / dirty count / last 3 commits | `git` |
| 6 | Live monitoring PIDs (watchdog, guardian, pulse, gpu_monitor) | `pgrep` |
| 7 | M1/M2 LM Studio `:1234` reachability + M5 ping | `curl`, `ping` |

## Verified output (th

[assistant] ## Rapport de démarrage JARVIS ✅

| Axe | État |
|---|---|
| **Système** | Load 5,16 (nominal prod) · RAM 19,5/48 Go · 4 GPU — max 81°C (RTX 3080, plage connue ~82°C) |
| **SQLite** | `data/jarvis.db` → WAL actif, `integrity: ok` |
| **Tables réelles** | `jarvis_agent_registry`=19 · `jarvis_agents`=40 · `llm_backends`=4 · `jarvis_cluster_map`=4 |
| **Git** | `feat/content-perf-engine` @ `18d2bdab` · 357 fichiers dirty (état de travail normal du repo) |
| **Monitoring** | Procs vivants (watchdog, pulse, moniteurs python) |
| **Cluster** | ✅ M1 LMS :1234 · M1-hub :18800 · OL1 :11434 · nœud .0.10 — ❌ M2, M5, M6 (offline depuis le 29/07, connu, reroutage qwen2.5:1.5b déjà en place) |
| **Hook QA** | **OK** (05:59 UTC) — tous les scripts présents et exécutables, contrat JSON respecté |

Points d'attention :
- M1 LMS était signalé DOWN par la sonde de session (warmup post-reboot) — il répond maintenant. Le faux négatif est le comportement documenté après un reboot (uptime 59 min).
- Les tables `skill_triggers` (57) et `agent_registry` (31) citées dans la checklist n'existent pas — ce sont `jarvis_agent_registry` et `jarvis_agents` qui font foi (gotcha documenté dans le skill).

`★ Insight ─────────────────────────────────────`
Le driver du skill encode les *vrais* noms de tables plutôt que ceux du prompt de la commande : c'est un exemple de « skill comme source de vérité » — la doc prose dérive, le script exécutable testé ne ment pas.
`──────────────────────────────────────────────

[user] Exécute la séquence de démarrage complète JARVIS :

1. Vérifie l'état système (CPU/RAM/GPU/Load)
2. Active le mode WAL SQLite + pragmas performance
3. Charge la table `skill_triggers` (57 patterns de détection par mots-clés)
4. Vérifie les 31 agents enregistrés dans `agent_registry`
5. Synchronise avec GitHub (git status + log)
6. Lance les agents de monitoring en parallèle
7. Affiche le rapport de démarrage compact

Utilise le skill `demarrage` pour exécuter cette séquence.

## Audit QA des hooks (anti hook mort)

Avant de conclure le démarrage, vérifier l'intégrité des hooks `settings.json` (aucun script manquant ou non exécutable, contrat JSON respecté) en exécutant le point d'entrée QA et en relayant son verdict :

```bash
bash /home/turbo/.claude/hooks/qa/hook-qa-demarrage.sh
```

Si le verdict est `HOOK QA: ECHEC` (exit 1), corriger les scripts manquants/non-exécutables listés avant de router vers ces hooks (remplace la détection manuelle de hooks morts, ex: jarvis-tts.sh absent).

[assistant] Relance de la séquence de démarrage (skill déjà chargé — j'exécute directement le driver et l'audit QA).

[assistant] ## Rapport de démarrage JARVIS (rejeu 08:20) ✅

| Axe | État |
|---|---|
| **Système** | Load **12,77** (en hausse vs 5,16 à 08:00 — voir note) · RAM 15,6/48 Go · 4 GPU — max 74°C (RTX 3080, en baisse vs 81°C) |
| **SQLite** | WAL actif, `integrity: ok` |
| **Tables réelles** | `jarvis_agent_registry`=19 · `jarvis_agents`=40 · `llm_backends`=4 · `jarvis_cluster_map`=4 |
| **Git** | `feat/content-perf-engine` @ `18d2bdab` · 364 dirty (normal) |
| **Monitoring** | Procs vivants (watchdog, pulse, moniteurs python) |
| **Cluster** | ✅ M1 LMS · M1-hub :18800 · OL1 · nœud .0.10 — ❌ M2, M5, M6 (offline connu depuis le 29/07) |
| **Hook QA** | **OK** (06:20 UTC) — hooks settings.json sains |

Seul changement notable depuis le démarrage de 08:00 : le **load est passé de 5,2 à 12,8**. Le diagnostic précédent avait établi qu'un load 9–11 est nominal quand la prod 0-token tourne à plein ; 12,8 est juste au-dessus de cette plage. La RAM a baissé (19,5→15,6 Go) et le GPU 3 a refroidi, donc c'est de la charge CPU (probablement les inférences locales qwen2.5:1.5b reroutées depuis M6). À surveiller : si le load dépasse durablement ~15, un passage de `jarvis-backpressure` sera justifié.

Système opérationnel, rien à corriger.