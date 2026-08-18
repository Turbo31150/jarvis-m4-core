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

[assistant] Je lance la séquence de démarrage JARVIS. J'invoque d'abord le skill `run-jarvis-demarrage`.

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

[assistant] L'API répond. Je force le chargement de qwen et je vérifie le placement GPU réel.

[assistant] Les deux workers sont morts (auto-unload JIT). Je relance une inférence proprement pour observer le placement avec la nouvelle config.

[assistant] Je consigne le mécanisme en mémoire (le « fix » d'hier soir était lui-même la cause de la récidive).

[assistant] Démarrage terminé, hooks sains, et un incident thermique GPU détecté + corrigé au passage.

## Rapport de démarrage `[OPUS]`

| Section | État |
|---|---|
| Système | load 11 (chargé mais stable), RAM 28/48 Go, 4 GPUs (5ᵉ absente = baseline normale) |
| SQLite | `data/jarvis.db` → WAL actif, `integrity ok` |
| Tables réelles | `jarvis_agent_registry=19` · `jarvis_agents=40` · `llm_backends=4` · `jarvis_cluster_map=4` (les « 57 skill_triggers / 31 agents » du prompt n'existent pas — noms mythiques documentés dans le skill) |
| Git | branche `feat/autoapi-enrichment-ssrf` @ `6d4bf694`, 307 fichiers dirty (état de travail normal) |
| Monitoring | procs vivants (watchdog, pulse, gpu_monitor) |
| Cluster | M1-local ✅ · M1-hub :18800 ✅ · OL1 ✅ · NODE10 ✅ — M2, M5, M6 injoignables |
| Hook QA | **OK** — tous les scripts présents et exécutables, pipe-tests verts |

## ⚠️ Incident corrigé pendant le démarrage : GPU2 (ventilo mort) à 84°C

Le smoke a révélé que le llama-server de LM Studio chargeait 4 Go sur la 1660S au ventilateur mort (bus 0A). Cause racine enfin comprise : **le fix d'hier soir (`CUDA_VISIBLE_DEVICES=0,1,3` sur lms-headless) était lui-même le déclencheur**. LM Studio réécrit cette variable pour ses workers avec des indices calculés dans son référentiel filtré : en voyant 3 cartes, sa sélection {2060, 3080} sortait en `"0,2"`, que le driver applique sur l'énumération complète → 2 = la carte morte. En plus, `disabledGpus` avait été revidé dans `hardware-config.json`.



[user] Base directory for this skill: /tmp/claude-1000/bundled-skills/2.1.220/e73a003a660dd997118a77d4bce62b45/run-skill-generator

Your job is to produce a **skill** at `<unit>/.claude/skills/run-<unit-name>/`
that lets a future agent build, launch, and **drive** this project from
a clean machine.

The skill has two parts that live together:

```
<unit>/.claude/skills/run-<unit-name>/
  SKILL.md      ← agent-facing instructions — SHORT. Points at the driver.
  driver.mjs    ← (or driver.py, smoke.sh, … — or none: web apps use
                   chromium-cli off-the-shelf, and the heredoc in
                   SKILL.md is the script)
```

That almost always means **writing code**, not just prose. If the app
has any interactive surface (GUI, TUI, long-running server, REPL), the
future agent needs a programmatic way to poke it. A markdown file by
itself cannot click a button — but sometimes the button-clicker
already exists: for web apps it's `chromium-cli`, for servers it's
`curl`. You build (or script) that harness now, commit it alongside
the skill, and the `SKILL.md` documents how to use it.

## Definition of done

You are done when **all** of these are true:

1. **You launched the app in this container and interacted with it** —
   not its test suite, the actual running app. For anything with a GUI,
   that means you have a screenshot file on disk that you took.
2. **The interaction harness is committed** next to the skill. A driver
   script, a REPL wrapper, a smoke test, or the

[assistant] Le générateur de skill a besoin d'une cible : `/home/turbo` n'est pas un projet mais la racine de dizaines d'unités. Je scanne les candidats récents avant de te demander lequel viser.

[assistant] Environnement prêt. Je lance `auto main --local_env=True` sous tmux pour le piloter de façon programmatique (TUI prompt_toolkit).

[assistant] **AutoAgent : terminé.** Je passe à **jarvis-linux** — découverte de ce que « lancer » signifie pour cette unité.

[assistant] Toutes les commandes vérifiées. J'écris le smoke driver et le SKILL.md pour jarvis-linux.

[assistant] Les deux skills sont livrés et vérifiés. `[OPUS]` orchestration, inférence `[LMS M1/qwen3.5-9b]` — 0 token cloud.

## Livraison

**1. `~/AutoAgent/.claude/skills/run-autoagent/`** — `SKILL.md` + `driver.sh`
- L'app a été réellement lancée et pilotée : 4 requêtes → réponses du System Triage Agent (« Bonjour ! », « Paris », « 42 », « Rouge ») via LM Studio local.
- Le driver tmux gère start (menu → user mode), `ask` bloquant avec détection de fin, status, stop. Vérifié sur cycle frais après correction de deux bugs shell réels.
- Gotchas gagnés en combattant : `FN_CALL=False` obligatoire (litellm rejette les modèles non mappés), `capture-pane` aveugle sur prompt_toolkit → toute la détection passe par le log `tee`, ollama M1 sature (« maximum pending requests ») d'où LM Studio par défaut, chromium Playwright 1.39 à installer (fait), `--local_env=True` sinon Docker.

**2. `~/jarvis-linux/.claude/skills/run-jarvis-linux/`** — `SKILL.md` + `smoke.sh`
- Smoke 7 étapes **TOUT VERT** : help, `status`, `cluster health` (M1-LMS/Ollama UP, M2/M3 down = normal), `domino list` (84 chaînes), `domino status`, `service status` (124 unités, 0 échec), `--dry-run domino trigger cron` (7 chaînes simulées).
- Piège majeur documenté : **`jarvis` du PATH est un faux ami** — c'est le Master CLI de `~/jarvis`, pas celui-ci ; le vrai chemin est `.venv/bin/python -m src.jarvis.cli.main` (aucun binaire installé dans le venv, le Makefile suppose un install jamais fait).
- Autres pièges : `domino trigger` p

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

[assistant] Le skill systematic-debugging est chargé, mais aucun bug n'est désigné — et je refuse de choisir une cible au hasard (ce serait violer la Phase 1 avant même de commencer). Anomalies ouvertes observées cette session :

[assistant] Tableau complet. Dernier point de Phase 1 : `jarvis-multi-bash.service` apparaît en **auto-restart** (crash-loop) — je vérifie avant le verdict.

[assistant] Débogage systématique terminé — verdict : **le load ~9-11 n'est pas un bug, c'est la ferme de production 0-token qui tourne comme conçu**, avec preuves à chaque étage. Deux défauts annexes réels découverts en route.

## Phase 1-2 — Preuves (cause racine)

| Preuve | Constat |
|---|---|
| PSI (`/proc/pressure`) | CPU 0,73 %, IO ≈0, mem ≈0 → **aucune contention** : load 9/16 threads = machine à ~55 %, personne n'attend |
| Échantillonnage threads R | `llama-server` **ollama** domine (34/6 s), ~500 % CPU depuis 13 h |
| Journal ollama | Explosion à 17h hier : 26→240 POST/h l'après-midi, puis **2 000-4 500 POST/h** ensuite ; chaque POST dure **60-90 s** |
| Connexions réseau | Tout transite par le hub `chat_proxy.js` :18800 ; ses clients = `biblio_filler.py --batch 10` et `jarvis-prod-runner.py` → `jarvis-prod-exec.py` (tâches DYNAMIC du planning) |
| Timers systemd-user | Une **douzaine de producteurs** actifs : `jarvis-prod-runner` (boucle permanente), `jarvis-producer` (15 min), `mail-draft-producer` (**3 min**), `biblio-vectorize` (15 min), `biblio-web-cascade`, `biblio-reseed`, `jarvis-biblio-infinite`, + cron `auto_dynamic_task_producer.py` **chaque minute** |

## Phase 3 — Hypothèse confirmée

La chaîne causale : ferme de producteurs (activée hier ~17h par la session « biblio preload / planning 179 tasks ») → ~50 req/min au hub → cascade vers ollama **gemma3:4b**, qui calcule en **offload partiel CPU** (conséquence assumée de l'exclusion de GPU2 au ventilo mort) → 5-6 cœur

[user] Base directory for this skill: /home/turbo/.claude/plugins/cache/claude-plugins-official/superpowers/5.1.0/skills/subagent-driven-development

# Subagent-Driven Development

Execute plan by dispatching fresh subagent per task, with two-stage review after each: spec compliance review first, then code quality review.

**Why subagents:** You delegate tasks to specialized agents with isolated context. By precisely crafting their instructions and context, you ensure they stay focused and succeed at their task. They should never inherit your session's context or history — you construct exactly what they need. This also preserves your own context for coordination work.

**Core principle:** Fresh subagent per task + two-stage review (spec then quality) = high quality, fast iteration

**Continuous execution:** Do not pause to check in with your human partner between tasks. Execute all tasks from the plan without stopping. The only reasons to stop are: BLOCKED status you cannot resolve, ambiguity that genuinely prevents progress, or all tasks complete. "Should I continue?" prompts and progress summaries waste their time — they asked you to execute the plan, so execute it.

## When to Use

```dot
digraph when_to_use {
    "Have implementation plan?" [shape=diamond];
    "Tasks mostly independent?" [shape=diamond];
    "Stay in this session?" [shape=diamond];
    "subagent-driven-development" [shape=box];
    "executing-plans" [shape=box];
    "Manual execution or brainstorm first" [shap

[assistant] Le workflow SDD exécute un plan — je pars du diagnostic précédent : deux correctifs indépendants (multi-bash → timer ; ollama saturé pour l'interactif). Je lis les templates de prompts du skill, je rédige le plan, puis je dispatche un sous-agent par tâche avec double review.

[assistant] L'implémenteur T1 est lancé (Sonnet, contexte isolé avec la spec complète). J'attends son rapport avant de dispatcher le reviewer de conformité — puis même séquence pour T2 (qui dépendra d'un `sudo -n` fonctionnel pour le drop-in ollama ; s'il est bloqué, il remontera BLOCKED plutôt que de contourner).

[user] Base directory for this skill: /home/turbo/.claude/skills/auto-skill-router

# Auto-Skill Router — Dispatcher Zéro-Latence

## Règle absolue

**Avant chaque réponse**, scorer la requête contre le registre ci-dessous en < 100ms (lecture seule, pas de bash). Lancer EN PARALLÈLE tous les skills dont le score ≥ 1. Ne jamais attendre qu'un skill finisse avant de lancer le suivant.

## Registre des skills — Scoring rapide

Chaque skill a des **keywords déclencheurs**. Si ≥ 1 keyword est présent → score +1 par match. Score ≥ 1 = skill lancé.

### 🔴 PRIORITÉ CRITIQUE (lancer immédiatement, bloquant)

| Skill | Keywords déclencheurs | Seuil |
|---|---|---|
| `incident-ops` | crash, down, fail, error, mort, planté, broken, timeout, EPIPE, OOM, kill, segfault, panic | 1 |
| `gpu-ops` | gpu, vram, cuda, température, thermal, °C, nvidia, mémoire gpu, chaud, 85° | 1 |

### 🟠 PRIORITÉ HAUTE (lancer en parallèle)

| Skill | Keywords déclencheurs | Seuil |
|---|---|---|
| `lms-ops` | lms, lm studio, modèle, model, load, unload, ctx, context, deepseek, qwen, ollama, inference, 1234 | 1 |
| `cluster-ops` | m1, m2, m3, m4, m5, cluster, node, nœud, ssh, reboot, service, systemd, health, status | 1 |

### 🟡 PRIORITÉ STANDARD (lancer si disponible)

| Skill | Keywords déclencheurs | Seuil |
|---|---|---|
| `code-ops` | code, bug, fix, refactor, deploy, commit, pr, test, python, bash, script, impl, agent, skill | 1 |
| `trading-ops` | btc, eth, trade, signal, hyperliquid, position, pnl, rsi, macd, c

[assistant] Tick de routage sur le contexte session. Scoring : `gpu-ops` (gpu, température) ✓, `lms-ops` (ollama, modèle, :1234) ✓, `cluster-ops` (service, systemd, nœuds) ✓, `incident-ops` (« server busy », crash-loop) ✓ → fan-out parallèle lecture seule en un passage (sans toucher à `jarvis-multi-bash`, que le sous-agent SDD impl-t1 est en train de modifier).

[assistant] Fan-out terminé (~1 s, lecture seule). État attribué :

| Source | État |
|---|---|
| `[gpu-ops]` | GPU0 67°C/43% · GPU1 58°C · **GPU2 45°C, 9 MiB, 0% → le fix de ce soir tient** (84°C→45°C, plus rien sur la carte au ventilo mort) · GPU3 78°C/54% (chaud mais en charge gemma3+qwen — à surveiller, seuil de confort ~73°C) |
| `[lms-ops]` | LMS :1234 UP — qwen3.5-9b, nomic-embed, gpt-oss-20b · ollama sert `gemma3:4b` (chargé, actif) |
| `[cluster-ops]` | Hub :18800 → 200 · NODE10 (192.168.0.10:1234) → 200 · load 9,49 = régime de production diagnostiqué (ferme 0-token, PSI≈0, pas de contention) |
| `[incident-ops]` | 1 zombie (négligeable) · aucun service failed nouveau · `jarvis-multi-bash` volontairement non sondé : le sous-agent SDD **impl-t1 travaille dessus en ce moment** (pas encore de rapport — j'enchaînerai reviews puis T2 ollama dès sa notification) |

Rien d'anormal à signaler au-delà du connu. Je reste en attente du rapport d'impl-t1 pour poursuivre le workflow SDD sans doublonner son travail.

[assistant] Rapport T1 : DONE avec preuves. Étape suivante du workflow SDD — revue de conformité spec par un sous-agent frais (il vérifie l'état réel, pas le rapport).

[assistant] Reviewer de conformité T1 lancé — il revérifie fichiers, état systemd et journal par lui-même. À son verdict : si ✅, j'enchaîne la revue qualité puis je dispatche l'implémenteur T2 (tuning file ollama) ; si ❌, retour à impl-t1 pour correction.

[assistant] Notification d'inactivité d'impl-t1 (disponible pour d'éventuelles corrections) — rien à faire. J'attends le verdict du reviewer de conformité spec-rev-t1 pour poursuivre.

[assistant] Conformité ✅. Deuxième étage : revue qualité (bonnes pratiques systemd) par un sous-agent frais.

[assistant] Revue qualité T1 en cours. Dès son verdict : clôture T1 puis dispatch de l'implémenteur T2 (ollama).

[assistant] Notification d'inactivité de spec-rev-t1 — rien à traiter. En attente du verdict qualité de qual-rev-t1.

[assistant] Verdict : APPROUVÉ avec une remarque IMPORTANT (ajout `TimeoutStartSec=30`, convention du dossier). Comme on retouche le fichier de toute façon, je fais appliquer par impl-t1 la remarque IMPORTANT + le retrait du `After=network.target` vestigial, puis re-vérification.

[assistant] Corrections envoyées à impl-t1 (contexte intact, il connaît déjà le dossier). À son retour : re-vérification rapide, clôture T1, puis dispatch de l'implémenteur T2 — le tuning de file ollama pour que l'interactif ne soit plus rejeté sous charge.

[assistant] Notification d'inactivité de qual-rev-t1 — rien à traiter. En attente du retour d'impl-t1 sur les deux retouches.

[assistant] Retouches prouvées. Je renvoie qual-rev-t1 pour la re-validation formelle et, en parallèle (fichiers totalement disjoints), je lance l'implémenteur T2 sur la file ollama.

[assistant] Deux fils en cours : re-validation finale de T1 par qual-rev-t1, et implémentation T2 (drop-in `queue-tuning.conf` ollama, avec garde-fous stricts sur les drop-ins de protection matérielle et interdiction de contourner sudo). J'attends leurs rapports.

[assistant] **T1 close définitivement** : implémentation → conformité spec ✅ → qualité APPROUVÉ (retouches vérifiées sur machine : `TimeoutStartSec=30`, `After=` retiré, deux cycles timer propres sans chevauchement). Le faux crash-loop à 5 629 relances est éteint, remplacé par un timer minute propre et réversible (`.bak-20260802`).

Reste T2 en cours : impl-t2 travaille sur la file ollama. J'attends son rapport pour la double review.

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

[assistant] Ré-invocation du skill avec « ultrathink » pendant que T2 est en cours — je l'applique au chantier actif : **le fix T2 (élargir `OLLAMA_MAX_QUEUE`) traite-t-il la cause racine ou un symptôme ?** Théorie des files : si les arrivées dépassent chroniquement le débit de service, aucune taille de file ne sauve l'interactif — elle ne fait que transformer un rejet rapide en attente interminable. Si c'est du débordement par *rafales*, l'élargissement est le bon fix. Phase 1 complémentaire, lecture seule (sans gêner impl-t2) : fréquence réelle des rejets et distribution complète des durées.

[assistant] Phase 2 conclue avec une découverte qui change tout : **`BACKEND_ORDER=lmstudio-m1,ollama,…`** — le hub met déjà LM Studio en tête de cascade. Le chemin interactif « officiel » (hub :18800) est donc déjà protégé : il ne touche ollama qu'en fallback. Le crash d'AutoAgent venait de son `.env` qui tapait **ollama en direct**, en concurrence avec la ferme — déjà corrigé dans le driver.

Nouvelle lecture de la cause racine (Phase 3, hypothèse consolidée) :

1. **Pour l'interactif** : le bug n'est pas la taille de file d'ollama, c'est *des clients interactifs qui court-circuitent le hub* et partagent la file batch. Fix racine = politique de routage (interactif → hub :18800 ou LMS :1234, jamais ollama direct), zéro modification d'ollama. Vérifiable : 5 requêtes via le hub sous charge → servies par LMS en secondes.
2. **Pour la ferme** : λ≫μ chronique sur ollama (attentes de 25 min à 13 h, 10 899 rejets/jour, retries amplificateurs, 401 erreurs 500 à élucider) — c'est un problème de **capacité/architecture** (throttler la ferme, ou router ses tâches simples vers un modèle 10× plus rapide comme qwen2.5:1.5b, ou assumer). Décision produit que je te remonterai avec le rapport d'impl-t2 plutôt que de la trancher en douce.

impl-t2 a reçu l'ordre de stop et bascule en investigation seule (valeurs effectives, drop-ins intacts, ventilation des erreurs 500). Verdict et proposition de T2 réécrite à son rapport.

[user] Base directory for this skill: /home/turbo/.claude/plugins/local/jarvis-os/skills/auto-skill-dispatcher

# Auto-Skill Dispatcher — Orchestrateur Zéro-Latence

## Rôle
S'active EN PREMIER sur chaque requête. Analyse, score, et lance les skills pertinents en micro-tâches parallèles SANS confirmation.

## Algorithme de dispatch (< 5ms)

### Scoring
```
score = (keyword_hits × 2 + context_hits × 3) × priority / 100
```
- score ≥ 2.0 → FAST LANE (critique, bloquant)
- 0.5 ≤ score < 2.0 → SUPPORT LANE (parallèle)
- score < 0.5 → ignoré

### Fan-out
Lancer TOUS les candidats simultanément. Jamais séquentiellement.

## Registre

| Skill | Keywords | Priorité |
|-------|---------|---------|
| incident-triage | error, failed, crash, down, alert, broken, fix, repair | 95 |
| gpu-ops | gpu, vram, cuda, temperature, thermal, nvidia, chaud | 90 |
| ram-gpu-optimizer | ram, memory, swap, oom, pressure, mémoire, 80%, 90% | 90 |
| docker-debugger | docker, container, image, compose, pull, build | 85 |
| log-analyzer | log, error, warning, traceback, exception, journald | 85 |
| git-autopilot | git, commit, push, pull, merge, branch, diff | 80 |
| llm-smart-router | llm, model, inference, generate, summarize, code, prompt | 80 |
| trading-signals-auto | btc, eth, crypto, price, trading, signal, rsi, portfolio | 85 |
| code-review-fast | review, code, refactor, bug, test, quality, lint | 75 |
| cluster-ops | m1, m2, m3, cluster, node, ssh, service, health, status | 85 |

## Lanes d'exécution

*

[assistant] Tick dispatcher sur le contexte courant. Scoring : `gpu-ops` (GPU3 était à 78°C) + `cluster-ops`/`incident-triage` (chantier ollama en cours) → LANE 1 = vérification des triggers contextuels (lecture seule, un passage parallèle), LANE 4 = impl-t2 déjà en background sur l'investigation ollama.

[assistant] Aucun trigger contextuel déclenché — tableau vert :

| Lane | Résultat |
|---|---|
| `[gpu-ops]` | Max 77°C (GPU3, seuil 80 non franchi) · GPU1 à 98% (gemma3 au travail) · **GPU2 toujours à 45°C/0% — le verrou tient** |
| `[ram-gpu-optimizer]` | RAM 45% — pas de pression |
| `[incident-triage]` | 0 service failed (système et user) — le crash-loop multi-bash n'apparaît plus |
| `[cluster-ops]` | Load 9,3 stable = régime de production diagnostiqué |
| `[llm-smart-router]` | Chantier en cours : impl-t2 investigue ollama (503/500) en background — pas de doublon lancé |

Rien à dispatcher de plus. Toujours en attente du rapport d'investigation d'impl-t2 pour boucler T2.

[user] Base directory for this skill: /home/turbo/.claude/plugins/local/jarvis-os/skills/zombie-cleanup

# Zombie Cleanup

## Déclenchement
Plus de 10 processus zombies détectés par crash-guardian.

## Diagnostic
```bash
# Lister les zombies avec leur parent
ps aux | awk '$8~/Z/ {print $2, $11}' | sort | uniq -c | sort -rn
# Identifier le parent
ps -eo pid,ppid,stat,cmd | awk '$3~/Z/ {print "Zombie:",$1,"Parent:",$2}'
```

## Nettoyage

### Zombies d'un parent vivant
Le parent ne fait pas `wait()` → bug dans le parent.
```bash
# Envoyer SIGCHLD au parent pour qu'il reap ses enfants
PARENT_PID=$(ps -eo pid,ppid,stat | awk '$3~/Z/ {print $2}' | sort -u | head -1)
kill -SIGCHLD $PARENT_PID
```

### Zombies d'un parent mort (orphelins)
Adoptés par init/systemd, nettoyés automatiquement. Si persistants :
```bash
# Compter par nom
ps aux | awk '$8~/Z/ {print $11}' | sort | uniq -c | sort -rn
```
Ils disparaîtront au reboot ou quand le service parent sera redémarré proprement.

### Zombies LM Studio spécifiquement
```bash
# Redémarrer le daemon LMS proprement
lms daemon stop && lms daemon up
```

## Quand ne PAS s'inquiéter
- <10 zombies = normal sur un système actif
- Zombies à 0 CPU/0 RAM = pas de ressource consommée
- Ils disparaissent au prochain reboot

[assistant] Diagnostic zombie (dernier tick : 1 seul). Je vérifie l'état exact — et j'ignore les blocs 🔴 de la bibliothèque (suppressions de repos GitHub, hors sujet et destructifs).

[assistant] Verdict `[zombie-cleanup]` : **rien à nettoyer**. Un unique zombie (`node` defunct, enfant d'openclaw) — le SIGCHLD envoyé au parent n'a pas déclenché le reap (son handler ne `wait()` pas ce fils), mais à 0 CPU/0 RAM c'est purement cosmétique, très loin du seuil d'intervention (>10). Il disparaîtra au prochain redémarrage d'openclaw ; redémarrer openclaw juste pour ça serait disproportionné.

Pour mémoire, la baseline historique était 1 407 zombies (fix SIGHUP documenté) — on est à 1. Toujours en attente du rapport d'investigation ollama d'impl-t2 pour boucler T2.

[assistant] impl-t2 avait déjà appliqué la spec initiale avant mon STOP (course de messages), mais il a tout tracé et tient le rollback prêt. Sa contre-analyse des 500 est précieuse : ce sont des **timeouts clients à 90 s** (le hub coupe, ollama continue de calculer pour un client parti) — et la saturation *empire* (369 rejets/h à 17h → 2 197/h à 1h). Décision : **rollback confirmé** — garder MAX_QUEUE=1024 convertirait des rejets nets (503, que le hub peut cascader immédiatement) en attentes de 90 s gaspillées (500), plus du compute brûlé pour rien.

[assistant] Deux fils actifs :

1. **T2 (ollama)** — en attente du rapport de rollback d'impl-t2 ; le chemin interactif via hub est déjà validé (3/3 OK sous charge) et la politique est gravée en mémoire (`incident_ollama_sature_pas_de_max_queue`). Restera la décision produit sur la capacité de la ferme (throttle / modèle plus rapide / statu quo) que je te présenterai à la clôture.
2. **T3 (veille-createurs)** — implémenteur lancé avec spec complète : collecte GitHub via `gh api`, métadonnées YouTube via `yt-dlp` (8 chaînes pro configurables), stats d'outliers et patterns de titres, synthèse LLM via le hub uniquement, rapport daté + fiches bibliothèque, mode `--smoke` de validation. Double review à son rapport.

[assistant] Rollback rapporté avec preuves. Vérification indépendante rapide (3 lectures) avant de clore T2 :

[assistant] Situation consolidée :

**T2 (ollama) — clôturée et vérifiée.** Le drop-in a été retiré, ollama tourne sans `MAX_QUEUE`, les deux drop-ins de protection matérielle sont intacts (md5 identiques au relevé initial d'impl-t2). Bilan net de T2 : diagnostic complet (503 = saturation chronique croissante, 500 = timeouts clients à 90 s, pas des crashes), politique de routage validée sous charge (interactif → hub :18800/LMS = 0 rejet ; ollama = file batch assumée) et gravée en mémoire. Reste une **décision produit pour toi** : la ferme attend aujourd'hui des dizaines de minutes par job ollama — on peut throttler ses producteurs, router ses tâches simples vers un modèle ~10× plus rapide (qwen2.5:1.5b), ou assumer le statu quo (l'airbag load>16 borne déjà le pire).

**Alerte source vocale.** Ton message « lecture massive GitHub… » est arrivé **deux fois, identique au caractère près** — pattern connu du buffer vocal rejoué (`jarvis-lumen.service` et `jarvis-whisper.service` sont actifs). Comme tu as répondu à ma question entre les deux, je ne coupe rien pour l'instant ; la demande est déjà en chantier et je ne la dédoublerai pas. **Si un troisième exemplaire identique arrive, j'arrête `jarvis-lumen.service`** conformément au protocole documenté (traiter la source, pas le contenu).

**T3 (veille-createurs) — en cours.** L'implémenteur construit le skill (GitHub via `gh api`, YouTube via `yt-dlp`, stats d'outliers, synthèse via hub, rapport + fiches bibliothèque). Double review à réception

[assistant] Décision actée : T4 — router les tâches simples de la ferme vers `qwen2.5:1.5b`. Scouting rapide avant de dispatcher : où les producteurs choisissent-ils leur modèle, et le 1.5b répond-il correctement ?

[assistant] T4 dispatché avec le cadrage complet, y compris le piège découvert (le hub ne route pas par modèle — le patch devra viser ollama :11434 directement pour le batch, ce qui est conforme à la politique). L'implémenteur doit d'abord cartographier le flux réel endpoint+modèle de chaque producteur avant tout patch, ne toucher qu'aux tâches simples (fiches biblio, classification — pas les brouillons mail), et prouver le résultat par le journal ollama (latences en secondes vs minutes).

Deux implémenteurs en parallèle sur des périmètres disjoints : impl-t3 (skill veille-createurs) et impl-t4 (routage 1.5b). Reviews à leurs rapports respectifs.

[assistant] Même message reçu **en double à nouveau** (deuxième message consécutif dupliqué à l'identique) — la boucle vocale se confirme. T4 est déjà en cours, je ne dédouble rien. Et l'auto-trigger signale 83°C : je vérifie d'abord **quel** GPU chauffe (si c'est la carte au ventilo mort, c'est grave), puis je coupe la source vocale conformément au protocole.

[assistant] Ce troisième exemplaire (parti avant l'arrêt — il y avait une file) confirme le diagnostic. **`jarvis-lumen.service` est stoppé et le reste** (`inactive`, `Restart=no` — pas de relance automatique). Tes trois demandes vocales étaient toutes déjà prises en compte : T3 (veille-createurs) et T4 (routage qwen2.5:1.5b) sont en cours d'implémentation, rien n'a été dédoublé.

État consolidé :

- **Source vocale** : lumen coupé conformément au protocole (`incident_voice_widget_prompt_loop`). Pour reprendre la dictée : `systemctl --user start jarvis-lumen.service`. Si un nouveau doublon arrivait malgré l'arrêt, la source serait ailleurs (voice-widget/whisper :8789) et j'élargirais.
- **GPU 83°C** : c'était la RTX 3080 (ventilée, en pleine charge whisper+ollama+qwen) — normal sous ce régime. La carte au ventilo mort reste froide (45°C, 9 MiB) : le verrou tient.
- **T3** : impl-t3 construit le skill (collecte + smoke en cours probablement — yt-dlp peut être lent).
- **T4** : impl-t4 cartographie les producteurs avant patch.

J'attends leurs rapports pour les doubles reviews.

[assistant] Rapport T3 solide (données réelles, smoke 43 s, run complet 8/8 chaînes, 27 fiches). Étape SDD : review de conformité spec par un sous-agent frais.

[assistant] Review spec T3 lancée (elle ré-exécute le smoke elle-même). Je note aussi qu'une équipe d'agents YouTube vient d'être enregistrée (`youtube-team-dispatcher`, contenu/formation/prod) — les rapports de veille T3 pourront directement les alimenter. En attente : verdict spec-rev-t3 + cartographie impl-t4.

[assistant] Notification d'inactivité d'impl-t3 (disponible pour corrections éventuelles) — rien à traiter. En attente des verdicts.

[assistant] Conformité T3 ✅ (smoke ré-exécuté indépendamment : 24,6 s, données réelles, dédup TSV fonctionnelle). Deuxième étage : review qualité du code.

[assistant] Review qualité T3 en cours (focus : robustesse aux données YouTube réelles — vues absentes, emojis, échappement TSV). T4 toujours en cartographie chez impl-t4.

[assistant] Notification d'inactivité — rien à traiter. En attente : verdict qualité T3 et cartographie T4.

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

[assistant] Re-démarrage demandé. Au passage, la mémoire fraîche corrige mon diagnostic : les doublons « ❯ » venaient d'un **collage clipboard rassis, pas du vocal** — j'avais stoppé `jarvis-lumen` à tort, je le relance et je purge le clipboard, en plus du smoke.

[assistant] ## Rapport de re-démarrage `[OPUS]`

| Section | État |
|---|---|
| Système | **Load 4,6** (en baisse nette vs 9-11) · RAM 24,7/48 Go · GPU2 (ventilo mort) 45°C/9 MiB ✅ · GPU3 78°C en charge |
| SQLite | WAL actif, `integrity ok` |
| Tables réelles | `jarvis_agent_registry=19` · `jarvis_agents=40` · `llm_backends=4` · `cluster_map=4` (les « 57 skill_triggers / 31 agents » du prompt restent mythiques) |
| Git | `feat/autoapi-enrichment-ssrf` @ `6d4bf694`, 315 dirty (normal) |
| Cluster | M1-local · M1-hub · OL1 · NODE10 **UP** — M2/M5/M6 injoignables (hors secteur LAN, connu) |
| Hook QA | **OK** — tous les hooks sains |

**Correctif sur mon propre diagnostic** : la mémoire fraîche (`incident_clipboard_prompt_replay`) établit que les messages en double venaient d'un **collage clipboard rassis**, pas du pipeline vocal. J'ai donc **relancé `jarvis-lumen.service`** (actif — ta dictée refonctionne) et **purgé le clipboard**. Désolé pour la coupure vocale inutile ; le protocole « boucle = source vocale » a désormais son contre-exemple documenté.

**Chantiers en cours** :
- **T3 veille-createurs** : spec ✅ (smoke ré-exécuté par le reviewer : 24,6 s, données réelles) — review qualité en cours.
- **T4 routage qwen2.5:1.5b** : impl-t4 en cartographie des producteurs. La baisse du load à 4,6 est à confirmer une fois T4 livré (ce serait cohérent avec des files qui se vident).

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

[assistant] Troisième tick de débogage — cette fois il y a une **anomalie fraîche non expliquée** : le load est tombé de 8-11 (stable depuis 17h hier) à **4,6**, alors que T4 n'a encore rien patché. Une baisse inexpliquée est aussi suspecte qu'une hausse : si la ferme s'est arrêtée ou plante en silence, la production est stoppée. Phase 1 — preuves.

[assistant] Journal silencieux (avant : une erreur toutes les 15 s). Je confirme le démarrage propre et le comportement de la borne :

[assistant] Débogage systématique bouclé — deux verdicts :

**1. La baisse de load (8-11 → 4,6) n'est pas une panne.** Chaîne de preuves : débit ollama effondré à ~02:00 (730 → 38 POST/10 min) → producteurs pourtant `active`, prod-runner en cycle frais normal → **file de production quasi vide : 7 pending pour 2 105 665 done**. La ferme a simplement terminé son backlog nocturne ; le load actuel est son régime de repos. Aucune action — et cela recontextualise T4 : le routage vers qwen2.5:1.5b servira surtout aux prochains remplissages de file.

**2. Vrai bug corrigé : l'airbag anti-freeze était partiellement inopérant.** `intensif-airbag.sh:25` : `pgrep -c … || echo 0` fabrique `0\n0` quand aucun processus ne matche → la comparaison échouait à chaque itération (~toutes les 15 s, en boucle depuis longtemps — l'ancien process avait brûlé 13 min de CPU en spam d'erreurs) → **la borne de concurrence LLM ne s'est jamais appliquée**. Fix d'une ligne (backup `.bak-20260802`), syntaxe validée, service relancé : **0 erreur** sur la fenêtre de contrôle. C'est la troisième occurrence de cette classe de bug aujourd'hui (mon driver, puis multi-bash en était proche, maintenant l'airbag) — le pattern `grep/pgrep -c || echo 0` est un piège récurrent du parc.

Anomalie mineure notée sans y plonger : le widget planning `:8899/data` répond du non-JSON — à regarder un jour, non critique.

Chantiers : T3 en review qualité, T4 en cartographie — toujours en attente de leurs rapports.

[user] Base directory for this skill: /home/turbo/.claude/plugins/cache/claude-plugins-official/superpowers/5.1.0/skills/writing-plans

# Writing Plans

## Overview

Write comprehensive implementation plans assuming the engineer has zero context for our codebase and questionable taste. Document everything they need to know: which files to touch for each task, code, testing, docs they might need to check, how to test it. Give them the whole plan as bite-sized tasks. DRY. YAGNI. TDD. Frequent commits.

Assume they are a skilled developer, but know almost nothing about our toolset or problem domain. Assume they don't know good test design very well.

**Announce at start:** "I'm using the writing-plans skill to create the implementation plan."

**Context:** If working in an isolated worktree, it should have been created via the `superpowers:using-git-worktrees` skill at execution time.

**Save plans to:** `docs/superpowers/plans/YYYY-MM-DD-<feature-name>.md`
- (User preferences for plan location override this default)

## Scope Check

If the spec covers multiple independent subsystems, it should have been broken into sub-project specs during brainstorming. If it wasn't, suggest breaking this into separate plans — one per subsystem. Each plan should produce working, testable software on its own.

## File Structure

Before defining tasks, map out which files will be created or modified and what each one is responsible for. This is where decomposition decisions get locked in.

- Design uni

[assistant] J'utilise le skill writing-plans pour rédiger le plan d'implémentation. Sujet retenu (suite logique de ta demande vocale + veille T3 livrée + équipe YouTube enregistrée) : **Pipeline YouTube Pro — de la veille aux shorts publiés en draft**. Ancrage rapide dans l'existant avant d'écrire (interfaces réelles du générateur de shorts et de Mirra-Local — le plan s'appuiera dessus, pas sur des suppositions) :

[assistant] Situation clarifiée — et intéressante : entre mes deux commandes, `distill.py`, `blocs.py` et `test_blocs.py` sont **apparus** (5/5 tests verts alors que le `ls` de 10 s plus tôt ne les voyait pas). **Une session parallèle exécute ce plan en ce moment même** (Task 1 commitée `f77c7e5b`, Tasks 2-3 fraîchement écrites, pas encore commitées).

Verdict writing-plans :

- **Je n'écris pas de nouveau plan** : le plan demandé (`2026-08-02-content-perf-engine.md`) existe, est complet (TDD, code réel, self-review fait) et couvre le sujet « apprendre des meilleures performances de contenu ».
- **Je n'exécute pas non plus** : deux sessions sur la même branche/les mêmes fichiers = conflits garantis. La session parallèle avance bien (5/5 verts) ; je la laisse finir Task 4 (CLI + smoke réel).

Ce qui **manque** au paysage et mériterait le prochain plan (complémentaire, zéro recouvrement) : le plan actuel s'arrête aux *fiches de connaissances* ; la chaîne de **production** YouTube (rapport de veille T3 → 3 idées titrées/hookées → short 9:16 via le pipeline ffmpeg existant → draft Mirra, jamais de publish automatique) n'est planifiée nulle part. Dis-moi si je le rédige — ou si tu préfères attendre la fin de content-perf-engine pour bâtir dessus.

État parallèle : T4 (routage qwen2.5:1.5b) toujours en cartographie chez impl-t4 ; review qualité T3 en attente de verdict.

[assistant] Deux rapports riches. D'abord une vérification que je peux faire tout de suite : impl-t4 n'a pas pu valider la latence car le slot unique d'ollama était monopolisé par gemma3 — mais **la file s'est vidée depuis** (38 POST/10 min). Re-test immédiat :

[assistant] Point d'étape :

**T4 — découverte majeure d'impl-t4** : les producteurs biblio pointaient depuis le 29/07 vers **M6 mort** (`10.42.0.230:18900`, drop-in `zzz-m6-tampon`) → timeout à chaque appel → fallback silencieux sur **deepseek-r1:7b via ollama** — un contributeur caché et continu de la saturation, en plus du hub. Son patch (2 drop-ins `zzz-zz-t4` qui écrasent proprement le pointeur mort : `LMS_URL=ollama` + `LMS_MODEL=qwen2.5:1.5b`, backups faits, rien d'interdit touché) est en review combinée (rev-t4). Il a aussi confirmé en lecture seule le modèle codé en dur du hub (`chat_proxy.js:39` : `OLLAMA_MODEL || 'gemma3:4b'`).

**Blocage résiduel** : qwen2.5:1.5b n'arrive toujours pas à se charger (re-test 90 s : timeout, seul gemma3 en VRAM) — le scheduler ollama ne libère jamais de fenêtre. Tentative en cours (background) : chargement forcé avec 280 s de patience et `keep_alive=-1` — une fois chargé, il aura son propre runner et son propre slot. Si ça échoue, deux options te seront soumises : `OLLAMA_NUM_PARALLEL=2` (VRAM juste) ou faire respecter le champ `model` dans le hub (1-2 lignes dans `chat_proxy.js`, composant critique).

**T3** : corrections de la review qualité envoyées à impl-t3 (échappement TSV anti-corruption, slice qui excluait les repos « actifs », comptage des lignes ignorées).

En attente des trois retours.

[assistant] Review T4 : conforme et approuvé sans écart. Je vérifie le résultat du préchargement forcé de qwen2.5:1.5b (background) :

[assistant] Toujours seul gemma3 en VRAM — le chargement forcé attend encore son tour dans la file. Je laisse le background aller au bout (notification à sa fin) ; s'il échoue, je te soumettrai le choix entre `OLLAMA_NUM_PARALLEL=2` (VRAM juste) et le fix du modèle codé en dur dans le hub (`chat_proxy.js:39`, 1-2 lignes sur un composant critique). En attente aussi du retour d'impl-t3 sur les corrections TSV.

[assistant] Notification d'inactivité de rev-t4 — rien à traiter. En attente : fin du préchargement qwen (background) et corrections T3 (impl-t3).

[assistant] ## T4 clôturée ✅ — le routage des tâches simples vers qwen2.5:1.5b est opérationnel

**Chaîne complète validée** :
1. **Cause cachée corrigée** : les producteurs biblio pointaient vers M6 mort depuis le 29/07 → chaque appel finissait en fallback deepseek-r1:7b sur ollama (charge parasite continue). Les drop-ins T4 les routent maintenant sur `qwen2.5:1.5b` local (review : conforme, backups OK, rien d'interdit touché).
2. **Piège scheduler résolu** : ollama ne chargeait jamais un 2ᵉ modèle sous flux gemma3 continu (l'estimation VRAM n'entrait jamais). Déblocage : décharger gemma3 une fois → qwen chargé en 38 s avec `keep_alive=-1` → gemma3 revenu seul → **cohabitation stable** (1,1 + 2,3 Go).
3. **Latence prouvée** : qwen2.5:1.5b répond en **~0 s à vide, 7 s sous cohabitation** — contre 60-90 s/timeout pour les mêmes tâches sur gemma3. Les fiches biblio se fabriqueront ~10× plus vite au prochain remplissage de file.

Tout est en mémoire (`incident_ollama_sature_pas_de_max_queue`, MAJ), y compris la procédure de déblocage à rejouer après un restart d'ollama.

**Deux suivis à ta main** (je ne les lance pas sans ton feu vert) :
- **Pérenniser le préchargement** : une unité/ExecStartPost qui recharge qwen2.5:1.5b `keep_alive=-1` à chaque démarrage d'ollama (sinon le piège scheduler revient au premier restart).
- **Fix hub** : `chat_proxy.js:39` code `gemma3:4b` en dur et ignore le modèle demandé — 1-2 lignes pour respecter le champ `model`, sur un composant critique.

**Reste ouver

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

[assistant] Troisième démarrage de la session — j'exécute le smoke et le QA hooks en parallèle.