[user] Base directory for this skill: /home/turbo/.claude/skills/cascade-massive

# Cascade massive — SkillsMP → écosystème JARVIS

Chaîne 0-token qui transforme un **plan** en **implantation réelle** distribuée aux agents.
Aucun appel LLM : tout est déterministe (SQL + parsing + shell).

> **Entrée = le catalogue SkillsMP** (11 596 skills aspirés au 6 août 2026), pas un PLAN.md.
> Pour éclater un **plan mode** en tâches affectées dans la file du widget :8899,
> c'est le skill `run-cascade-plan` (`~/jarvis/bin/cascade-massive.sh --from-plan …`).
> Les deux sont complémentaires : celui-ci implante un catalogue, l'autre exécute un plan.

## Quand l'utiliser

- À la **sortie du plan mode** : le plan est validé, il faut le faire exécuter par les agents.
- Après une nouvelle aspiration SkillsMP : de nouveaux skills doivent être affectés.
- Pour rejouer une vague ciblée sur une seule famille (`--famille omega`).

## Chaîne complète

```
aspiration → cartographie → implantation → CASCADE → dispatch agents → journal
```

| Étape | Script | Sortie |
|---|---|---|
| Cartographie | `~/labo/bibliotheque/skillsmp/cartographie.py` | `export/skills_index.json` + colonnes `categories/occupations/langue` |
| Implantation | `~/labo/bibliotheque/skillsmp/implantation.py` | `export/plan_implantation.json`, `TODO_DYNAMIQUE_SKILLSMP.json`, table `skillsmp_affectation` |
| Catégories | `~/labo/bibliotheque/skillsmp/categories_texte.py --apply` | remplit `category` depuis le texte des pages (les pages /cat

[assistant] J'exécute la cascade massive SkillsMP → agents. D'abord les vérifications préalables : les deux alertes du hook (1 service failed, disque 88 %), l'état de la file, et les garde-fous charge/RAM/GPU.

[assistant] Le mode `auto` s'est replié en `validated` — un garde-fou a déclenché. Je vérifie lequel dans le journal.

[assistant] ## Résultat

**GNOME réparé** — le bureau était en fait démarré mais invisible : le premier autologin a échoué (« Session never registered »), la relance est partie sur **tty7** pendant que l'écran restait sur la console **tty3** (menu de secours JARVIS). Un `chvt 7` a rebasculé l'affichage sur la session GNOME vivante. Détail connu au passage : le trousseau de session n'est pas déverrouillé (autologin sans mot de passe) — c'est le piège habituel qui fige Chromium/BrowserOS, parade `--password-store=basic` déjà documentée.

**Cascade massive** — exécutée en mode mineur comme demandé, aucun blocage détecté :

| Étape | Résultat |
|---|---|
| Dry-run | ✅ 120 skills au plan (8 × 15 familles), 98 avec contexte préchargé |
| Validated | ✅ file persistée (120 `pending` ajoutées aux 315 `done`) |
| Auto | ⏸ repli volontaire : garde-fou `charge 12,64 ≥ 12` (artefact de boot, machine debout depuis 4 min) |
| Relance différée | 🕐 armée en arrière-plan : dès que la charge repasse sous 8 (max 20 min), une vague `auto --quota 5` part seule |

**Moisson (« moiqsson » → moisson SkillsMP)** — déjà à jour pour aujourd'hui : quota API du jour consommé (50/50, 3 591 skills uniques, reprise « LLM » p2 demain), récupération des `SKILL.md` complète (0 fiche sans contenu), quarantaine idempotente (55/55 déjà traités).

**Alertes du hook** — `lmstudio-dual-warm` avait échoué par course au boot (LM Studio pas encore prêt sur :1234) : relancé, il est `active`. Disque à 88 % (106 Go libres) : pas criti

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


ARGUMENTS: /effort
/cli_skill_audit

[assistant] Je déroule la séquence de démarrage. J'invoque d'abord le skill `demarrage`, puis je traiterai les arguments (`/cli_skill_audit`) et l'audit QA des hooks.

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

[user] Base directory for this skill: /home/turbo/.claude/skills/cli_skill_audit

# cli_skill_audit

Moteur d'audit local M1 (AXE 1/3). Pur bash/sqlite3/systemctl, 0 API.

## Trigger keywords
audit,analyse,rapport

## Run (agent path)
```bash
bash .claude/skills/cli_skill_audit/driver.sh
```
Sortie réelle de la dernière exécution :
```
[driver] report : /home/turbo/jarvis/audit/audit-local-20260605-1654.md
[driver] secrets: CLEAN (rc=0)
[driver] logged : skill_invocations row id 17
```

## Ce que le driver produit
1. **Services systemd — DEUX scopes** : `systemctl` (system) ET `systemctl --user`. Leçon clé : `jarvis-autoheal` / `jarvis-share` / `jarvis-cluster-mount` sont en scope user → faux négatifs si on n'interroge pas `--user`. Compte actifs/inactifs/failed par scope.
2. **Skills** : `~/.claude/skills/*/SKILL.md` + skills `run-*` du repo `/home/turbo/jarvis/.claude/skills`.
3. **Triggers** : parse `run-jarvis-autoheal/skill-triggers.json`, compte les skills couverts, liste les `run-*` sans trigger.
4. **Secrets** : exécute `/home/turbo/jarvis/bin/scan-secrets.sh`, reporte verdict + rc.

## Inspecter le dernier rapport
```bash
ls -t /home/turbo/jarvis/audit/audit-local-*.md | head -1 | xargs head -45
```

## Vérifier le log d'invocation
```bash
sqlite3 -header -column /home/turbo/jarvis/db/cli_history.db \
  "SELECT id, skill_name, invoked_at, outcome, trigger_phrase FROM skill_invocations WHERE skill_name='cli_skill_audit' ORDER BY id DESC LIMIT 1;"
```

## Notes d'implémentati

[assistant] ## Rapport de démarrage JARVIS — M1

| Section | État |
|---|---|
| **Système** | Load 9,8 (redescend, boot +6 min) · RAM 31,3/48 Go · 5 GPU (46–75 °C, baseline saine — la 6ᵉ est physiquement absente) |
| **SQLite** | `data/jarvis.db` en WAL, integrity **ok**, pragmas appliqués |
| **Tables réelles** | `jarvis_agent_registry`=19 · `jarvis_agents`=40 · `llm_backends`=4 · `jarvis_cluster_map`=4 (les `skill_triggers`/`agent_registry` du texte du plugin n'existent pas — noms corrigés par le driver) |
| **Git** | `feat/content-perf-engine` @ `fca27ac3` · 3 452 fichiers dirty (état de travail normal du repo) |
| **Cluster** | M1-LMS **UP** · hub :18800 **UP** · M5 ping OK · OL1 **relancé** (était DOWN, répond v0.30.10 — service `disabled` au boot, volontairement d'après l'historique VRAM, donc non ré-enable) · NODE10 et M6 injoignables |
| **Hooks QA** | **OK** — tous les scripts de settings.json présents et exécutables |
| **Audit local** (`/cli_skill_audit`) | 0 service failed (scopes system + user) · 464 skills · 57 triggers, tous les `run-*` couverts · secrets **CLEAN** · rapport : `audit/audit-local-20260808-0553.md` |

En arrière-plan, toujours en cours :
- **disk-cleaner** sur l'alerte disque 88 % (résultat à venir) ;
- **vague cascade différée** (part seule dès que la charge repasse sous 8, max 20 min).

Note : `/effort` est une commande built-in du CLI — tape-la directement dans le prompt pour changer le niveau d'effort, je ne peux pas l'invoquer pour toi.

[user] Base directory for this skill: /home/turbo/.claude/plugins/cache/claude-plugins-official/superpowers/5.1.0/skills/systematic-debugging

# Systematic Debugging

## Overview

Random fixes waste time and create new bugs. Quick patches mask underlying issues.

**Core principle:** ALWAYS find root cause before attempting fixes. Symptom fixes are failure.

**Violating the letter of this process is violating the spirit of debugging.**

## The Iron Law

```
NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST
```

If you haven't completed Phase 1, you cannot propose fixes.

## When to Use

Use for ANY technical issue:
- Test failures
- Bugs in production
- Unexpected behavior
- Performance problems
- Build failures
- Integration issues

**Use this ESPECIALLY when:**
- Under time pressure (emergencies make guessing tempting)
- "Just one quick fix" seems obvious
- You've already tried multiple fixes
- Previous fix didn't work
- You don't fully understand the issue

**Don't skip when:**
- Issue seems simple (simple bugs have root causes too)
- You're in a hurry (rushing guarantees rework)
- Manager wants it fixed NOW (systematic is faster than thrashing)

## The Four Phases

You MUST complete each phase before proceeding to the next.

### Phase 1: Root Cause Investigation

**BEFORE attempting ANY fix:**

1. **Read Error Messages Carefully**
   - Don't skip past errors or warnings
   - They often contain the exact solution
   - Read stack traces completely
   - Note line numbers, file paths, 

[assistant] J'applique le débogage systématique au problème réel de cette session : **le premier autologin GNOME échoue au boot (« Session never registered, failing ») et l'écran reste sur la console tty3** — mon `chvt 7` de tout à l'heure était un correctif de symptôme, pas de cause. Phase 1 : collecte de preuves sans rien modifier.

[user] Base directory for this skill: /home/turbo/jarvis/.claude/skills/run-board

# board — conseil d'experts local et souverain

`~/jarvis/board/` est un **board d'experts** : une question entre, N experts du domaine
répondent chacun avec **sa** grille de lecture (`lens`) **en citant** des extraits d'un
corpus indexé, puis un arbitre synthétise les accords et les divergences.

**Règle fondatrice : une réponse sans citation est invalide.** Ce n'est pas une consigne
qu'on espère voir respectée par le modèle — c'est une contrainte **vérifiable en SQL** :
la vue `answers_sans_citation` liste, à tout instant, les réponses à rejeter.

Python stdlib seule. SQLite + FTS5 (BM25 lexical) **et** embeddings BLOB float32
dimension 768, fusionnés par rang (RRF) dans `retrieve()`. Inférence et vectorisation en
local sur LM Studio `127.0.0.1:1234`. Rien ne sort de la machine, 0 token payant.

## À lancer en premier

```bash
~/jarvis/.claude/skills/run-board/driver.sh smoke
```

~30 s, **zéro appel LLM** (le seul contact réseau est un `GET /v1/models` avec timeout court).
Sortie réelle du 2026-08-06 :

```
board — smoke (0 token LLM)
  base : /home/turbo/jarvis/board/board.db

1. syntaxe
  ✓ board.py se parse (ast)
  ✓ board_schema.sql s'applique sur une base neuve

2. structure (7 tables + chunks_fts + vue)
  ✓ les 7 tables sont la : domains experts sources chunks queries answers citations
  ✓ table FTS5 chunks_fts presente
  ✓ vue answers_sans_citation presente
  ✓ 3 triggers de synchronisation 

[assistant] ## Inventaire des gros consommateurs de `/home` (308 Go au total)

Voici « les documents qui ont autant de data » — les secteurs massifs et gourmands, classés par cible de rangement recommandée. **Rien n'est déplacé pour l'instant** : le board délibère en arrière-plan et je ne toucherai à rien sans son verdict et ton feu vert.

### Données froides → candidates à `/mnt/jarvis-data` (266 Go libres, disque sda3)

| Dossier | Taille | Nature |
|---|---|---|
| `~/jarvis/backups/` | **70 Go** | 🥇 Le plus gros poste — archives de backup, données froides par définition |
| `~/jarvis-sql-backups/` | 18 Go (dont 11 Go de `.git`) | Snapshots SQL LFS |
| `~/.config/jarvis-session/` | 19 Go | Snapshots de session (timer toutes les 5 min — ça enfle sans limite) |
| `~/m4-sync/` | 12 Go | Miroir inter-machines, reconstructible |
| `~/Downloads/s9-firmware/` | 4,8 Go | Firmware déjà flashé, archive |

### Purge simple (pas un déplacement, juste du gras)

| Dossier | Taille | Remarque |
|---|---|---|
| `~/claude-desktop-debian/.git` | 12 Go | Un `.git` de 12 Go pour un paquet debian — un `git gc --aggressive` ou re-clone shallow le ramène à ~centaines de Mo |
| `~/.gemini/history` | 6,9 Go | Historique de CLI, purgeable |
| `~/.npm-new-cache` | 6,1 Go | Cache npm |
| `~/.config/google-chrome` | 8,5 Go | Profils/caches Chrome, en partie purgeable |

### À laisser en place (chaud, actif)

`~/jarvis` hors backups (~38 Go, repo de travail), `~/Workspaces/jarvis-linux` (9,7 Go), `~/Documents` (7,9

[user] Base directory for this skill: /home/turbo/.claude/skills/cli_skill_audit

# cli_skill_audit

Moteur d'audit local M1 (AXE 1/3). Pur bash/sqlite3/systemctl, 0 API.

## Trigger keywords
audit,analyse,rapport

## Run (agent path)
```bash
bash .claude/skills/cli_skill_audit/driver.sh
```
Sortie réelle de la dernière exécution :
```
[driver] report : /home/turbo/jarvis/audit/audit-local-20260605-1654.md
[driver] secrets: CLEAN (rc=0)
[driver] logged : skill_invocations row id 17
```

## Ce que le driver produit
1. **Services systemd — DEUX scopes** : `systemctl` (system) ET `systemctl --user`. Leçon clé : `jarvis-autoheal` / `jarvis-share` / `jarvis-cluster-mount` sont en scope user → faux négatifs si on n'interroge pas `--user`. Compte actifs/inactifs/failed par scope.
2. **Skills** : `~/.claude/skills/*/SKILL.md` + skills `run-*` du repo `/home/turbo/jarvis/.claude/skills`.
3. **Triggers** : parse `run-jarvis-autoheal/skill-triggers.json`, compte les skills couverts, liste les `run-*` sans trigger.
4. **Secrets** : exécute `/home/turbo/jarvis/bin/scan-secrets.sh`, reporte verdict + rc.

## Inspecter le dernier rapport
```bash
ls -t /home/turbo/jarvis/audit/audit-local-*.md | head -1 | xargs head -45
```

## Vérifier le log d'invocation
```bash
sqlite3 -header -column /home/turbo/jarvis/db/cli_history.db \
  "SELECT id, skill_name, invoked_at, outcome, trigger_phrase FROM skill_invocations WHERE skill_name='cli_skill_audit' ORDER BY id DESC LIMIT 1;"
```

## Notes d'implémentati

[assistant] Je relance l'audit local M1 (déjà exécuté au démarrage, nouvelle passe demandée).