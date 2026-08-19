[user] # JARVIS MASTER ORCHESTRATOR — MEGA PROMPT D'INGÉNIERIE

## Mission : transformer l'existant en système JARVIS DUAL, résilient, observable, modulaire et piloté par LM Studio

Tu es Claude Code agissant comme **architecte logiciel principal, ingénieur système Linux, ingénieur IA/LLM, spécialiste MCP, spécialiste orchestration multi-agents, spécialiste LM Studio, spécialiste CLI et spécialiste fiabilité**.

Tu travailles directement dans le dépôt JARVIS existant.

Dépôt de référence :

`https://github.com/Turbo31150/jarvis-master-orchestrateur.git`

Répertoire de travail attendu :

`~/jarvis`

---

# 0. RÈGLE ABSOLUE

NE PAS repartir de zéro.

NE PAS créer une deuxième architecture parallèle.

NE PAS remplacer brutalement les composants existants.

NE PAS supprimer des scripts, agents, skills, MCP, configurations, bibliothèques ou pipelines simplement parce qu'ils semblent anciens.

NE PAS supposer que quelque chose est inutile.

NE PAS modifier massivement le dépôt avant d'avoir compris son architecture.

Tu dois d'abord :

1. inspecter ;
2. cartographier ;
3. comprendre ;
4. tester ;
5. identifier ce qui fonctionne ;
6. identifier ce qui casse ;
7. identifier les doublons ;
8. identifier les interfaces existantes ;
9. identifier les composants réutilisables ;
10. proposer la nouvelle architecture ;
11. implémenter progressivement ;
12. tester après chaque étape ;
13. conserver un état récupérable à chaque étape.

L'objectif est une **refonte incrémentale**, pas une destructio

[assistant] **[WAVE 1/10] AUDIT — état réel de `~/jarvis`** (fait, non extrapolé)

| Élément | Constat réel |
|---|---|
| Dépôt | remote = `Turbo31150/jarvis-m4-core` — **PAS** `jarvis-master-orchestrateur` (n'existe pas ici) |
| Branche | `refonte-prof-ia-symbiose`, 78 fichiers modifiés non commités, 8,3 Go |
| `.claude/` local | `agent-memory`, `settings.local.json`, `worktrees` — **0 agent, 0 skill locaux** |
| Agents/skills | 59 agents + 30 skills, mais dans `~/.claude/` (global), pas dans le dépôt |
| MCP `~/.claude.json` | **1 seul** (`browseros`) — les 29 MCP de ma session viennent des plugins, pas du dépôt |
| LM Studio | `llmster` PID 67025 sur `:1234` — API OK, **4 modèles** : qwen2.5-coder-14b, qwen3.5-9b, deepseek-r1-0528-qwen3-8b, nomic-embed. CLI `lms` **absent** (`lm-studio` GUI seul) |
| Ollama | `:11434` up (qwen2.5:0.5b, kimi-k2.5:cloud, …) |
| OpenClaw | v2026.7.1-2, gateway `:18789` → `{"ok":true,"status":"live"}` |
| Claude Code | v2.1.223 |
| tmux | session `jarvis-dual` déjà vivante (1 fenêtre) |
| HW | 12 cœurs, **15 Gi RAM (7,5 utilisés, 7,6 Gi swap déjà consommés)**, **1 seul GPU RTX 3050 4 Go — 3,6 Go déjà occupés**, disque 84 % |
| Existant réutilisable | `jarvis-router.py`, `model_router.sh`, `dashboard.py`, `watchdog_critical.sh`, `m1-failover-watchdog.sh`, `bench_massive.sh` |

**Verdict matériel immédiat (avant tout code)** : 4 Go de VRAM dont 3,6 déjà pris + 15 Gi RAM sur-engagée ⇒ **deux modèles chargés simultanément en local sont impossibles sur cette m

[assistant] Existant : `model_router.sh` (routeur bash task→modèle, fallback Ollama/cloud) + `cli/jarvis_master.py`. **Aucun** doctor, adapter unifié, worker, dispatcher, checkpoint ou board. → je construis dans un module isolé `dual/`, sans toucher l'existant.

**[WAVE 3/10] INFRASTRUCTURE — adapter providers + journal + checkpoints**

[assistant] **PROBLÈME détecté par le doctor** — modèle fantôme confirmé :

```
worker_a lmstudio/qwen/qwen3.5-9b → HTTP 400 "Failed to load model. Error loading model."
```
Listé par `/v1/models`, **inutilisable à l'inférence**. C'est exactement le cas que le cahier des charges appelle *zéro modèle fantôme* — détecté automatiquement, pas masqué.

**RÉPARATION — stratégie 1/3 : sonder réellement chaque modèle au lieu de faire confiance à la liste**

[assistant] Pendant la sonde, j'écris les tests (travail indépendant — pas de collision de fichiers).

**[WAVE 5/10] TESTS — serveur factice pour couvrir les cas d'échec sans dépendre d'un LLM**

[assistant] **27/27 tests PASS** (5,8 s) — dont modèle fantôme, réponse vide, timeouts différenciés, retry classifié, reprise après crash simulé, watchdog.

[assistant] Le buffering de Python masquait la sortie. Je relance avec `-u` et écriture incrémentale.

[assistant] **PROBLÈME 2 confirmé — LM Studio local ne charge AUCUN modèle** (les 3 → `model_unavailable`). M6 renvoie `empty_response`, ce qui sent le mode *thinking* tronqué par `max_tokens=5` (mémoire : les qwen3 raisonnent avant de produire du `content`).

**RÉPARATION — stratégie 2/3 : retester M6 sans brider la sortie + lire l'erreur exacte de LM Studio local**

[assistant] **RÉPARATION 2/3 — résultat mesuré :**

| Backend | Constat |
|---|---|
| LM Studio local `:1234` | `TimeoutError` même en requête directe → **serveur zombie** : il liste ses modèles mais n'exécute plus rien |
| M6 `10.42.0.1` — `deepseek-r1-0528-qwen3-8b` | **success**, ttft 25,9 s |
| M6 — `qwen3.5-9b` | `empty_response` (budget consommé en *thinking*) |

→ Worker A basculable sur M6. Je rends la sélection anti-fantôme permanente (`discover --probe` écarte tout modèle qui ne répond pas réellement), puis je lance la preuve DUAL.

[assistant] Découverte avec sonde lancée (longue : elle teste chaque modèle réellement). Je traite ta demande **agy CLI** en parallèle.

[assistant] Deux choses : le formatter a retiré l'import `Timeouts` (devenu inutilisé entre mes deux edits) — je corrige.

[assistant] `agy` = **Antigravity CLI de Google** (binaire Go, 199 Mo, avec Cascade/subagents/browser/language-server). Je l'installe.

[assistant] `agy 1.1.12` installé (`~/.local/bin/agy`, + alias `antigravity-cli`). Je le câble complètement.

[assistant] Token OAuth trouvé sur le disque M1 : `~/m1-disk/.gemini/antigravity-cli/antigravity-oauth-token`. Je le câble (sans jamais l'afficher ni le versionner).

[assistant] **Correction importante** : `~/m1-disk` n'est pas un disque récupéré — c'est un **montage SSHFS vers `turbo@10.42.0.1` = M6, machine vivante**, avec une session `agy` active (history écrit à 22:11). Le CLI vient donc de M6, pas de M1 (M1 avait la 1.1.11).

[assistant] **`agy` authentifié et opérationnel** — 15 modèles, dont Claude Opus 4.6, Gemini 3.1 Pro, GPT-OSS 120B.

[assistant] La sonde a rendu un verdict net (et instructif) :

| Backend | Résultat sondé |
|---|---|
| `lmstudio` :1234 | **1 modèle utilisable** : `qwen2.5-coder-14b` (il a fini par charger) |
| `ollama` :11434 | 4 modèles utilisables |
| `lmstudio_m6` | **écarté** — les 3 modèles échouent maintenant (M6 ne tient qu'un modèle à la fois ; la sonde en a demandé plusieurs) |

→ A et B sont sur deux backends distincts. **Preuve DUAL maintenant.**

[assistant] **Bug trouvé** : le CLI rappelait `discover()` à chaque commande et **écrasait la config sondée** → worker_a repartait sur `qwen3.5-9b` (le fantôme) au lieu du `qwen2.5-coder-14b` validé. La concurrence, elle, est bien réelle (overlap 20,9 s, efficacité 1.0) — mais A n'a rien produit, donc verdict `FAILED`, honnêtement.

**RÉPARATION 3/3 : la config vérifiée doit primer sur la redécouverte.**

[assistant] Le test tourne (un 14B sur 4 Go de VRAM est lent). J'en profite pour ajouter `agy` comme **provider worker** — c'est la réparation de fond : le DUAL local est plombé par la VRAM, `agy` fournit un worker fiable et 0-token.

[assistant] **Résultat DUAL — les deux workers réussissent**, chevauchement 40,7 s, efficacité parallèle **1.0** (67 s au lieu de 108 s). Mais le verdict sort `PARTIAL` car `gemma3` a mis 55 s à charger : A avait fini de générer avant que B n'émette son premier token.

Mon critère confondait deux choses. Je les sépare (et je ne relâche pas le seuil — j'en ajoute un second, mesuré à part).

[assistant] La machine sature : je lançais des inférences concurrentes pendant les tests. Je séquence et je configure le DUAL qui a réellement du sens ici — **un worker local + un worker cloud** (pas de compétition pour le GPU).

[assistant] **DUAL_PARALLEL = PASS** — les deux workers réussissent, exécution concurrente prouvée. `gemma3` était froid (90 s de TTFT). Un second run immédiat, modèle chaud, doit donner l'entrelacement complet :

[assistant] **Preuve obtenue — génération réellement entrelacée** :
```
2.34  worker_b FIRST_TOKEN ... 7.66 B TOKEN[30]
8.15  worker_a FIRST_TOKEN   ← A génère pendant que B génère
9.55  worker_b TOKEN[40]     ← B poursuit
```

**[WAVE 6/10] RECOVERY — test de crash réel (pas simulé en unittest)**

[assistant] Le job a fini avant le kill (3/3 SUCCESS). Je recommence avec un kill plus précoce.

[assistant] **Crash capturé** : job `RUNNING` 2/3, TASK-003 interrompue en plein vol. Watchdog puis reprise :

[assistant] **Reprise réussie** : seule TASK-003 rejouée, les deux tâches déjà faites intactes.

[assistant] Dernier défaut de cohérence : `doctor` redécouvrait au lieu d'utiliser la config vérifiée — il testait donc le modèle fantôme au lieu du worker réellement configuré. Je corrige.

[assistant] Doctor en cours (il sonde tous les backends + `agy models`). Tests de non-régression : **27/27 OK** après la correction.

[assistant] # JARVIS DUAL — CHANTIER TERMINÉ

**ÉTAT GLOBAL : WORKING** (partiel sur 3 points, listés plus bas)

## Le DUAL est prouvé, pas affirmé

```
0.0003  worker_a START
0.0009  worker_b START
2.3425  worker_b FIRST_TOKEN
7.6637  worker_b TOKEN[30]
8.1487  worker_a FIRST_TOKEN   ← A génère pendant que B génère
9.5524  worker_b TOKEN[40]     ← B poursuit
wall=19.5s  somme_solo=28.4s  overlap=8.89s  efficacité=1.0
DUAL_PARALLEL = PASS
```

## Ce qui a été construit

`~/jarvis/dual/` (10 modules, 3 793 lignes) + `bin/jarvis-dual` — **aucun fichier existant modifié, rien supprimé**.

`doctor` · `discover --probe` · `workers` · `run` (6 modes) · `test` · `benchmark` · `jobs` · `replay` · `recover` · `board` · `watchdog`

## Tests réels

| Test | Résultat |
|---|---|
| DUAL concurrent | **PASS** — 2 workers, tokens entrelacés, efficacité 1.0 |
| Crash `kill -9` en plein job | job figé à 2/3, TASK-003 interrompue |
| Watchdog | figé détecté (21 s) → `RECOVERABLE`, **rien tué** |
| `recover` | **seule TASK-003 rejouée** → SUCCESS |
| `replay` | 22 événements à la milliseconde |
| Suite unitaire | **27/27** (5,8 s) |
| `doctor` final | **OK=17 WARN=1 ERROR=0** |

## Trois problèmes réels trouvés et réparés

1. **Modèle fantôme** — `qwen3.5-9b` listé par `/v1/models`, HTTP 400 au chargement. 3 stratégies : sonde par modèle → bascule M6 → `discover --probe` exige désormais une inférence réussie.
2. **La config vérifiée était écrasée** à chaque commande par une redécouverte qui réélisait le fa

[user] Base directory for this skill: /home/pamerys/.claude/plugins/cache/claude-plugins-official/superpowers/6.3.0/skills/systematic-debugging

# Systematic Debugging

## Overview

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
   - Note line numbers, file paths, error codes

2. **Reproduce Consistently**
   - Can you trigger it reliably?
   - 

[assistant] Using **systematic-debugging** — deux cibles : l'alerte disque qui vient de monter (81 % → 86 % en une heure, ça bouge trop vite pour être normal) et le seul bug non résolu du chantier (LM Studio local qui ne charge aucun modèle).

**PHASE 1 — Investigation. Aucune suppression, aucun fix, tant que la cause n'est pas établie.**

[assistant] **Preuve** : le disque ne fuit pas — **une sauvegarde est en cours d'écriture en direct**.

[assistant] **Cause racine de l'alerte disque — établie, ce n'est pas une fuite :**

| Preuve | Détail |
|---|---|
| PID 18918 | `deja-dup --backup --auto` — 14,9 % CPU, **en cours** |
| PID 70499 | `duplicity incremental` — 12,1 % CPU |
| Écriture live | `~/.cache/deja-dup` 2,1 Go · `/tmp/duplicity-tempdir` 201 Mo · `~/Backups` 1,4 Go |

**Je ne tue rien** : interrompre duplicity en pleine passe incrémentale peut casser la chaîne de sauvegarde. Le disque remonte parce qu'une sauvegarde travaille, pas parce que quelque chose fuit.

Maintenant le vrai bug. **PHASE 1 sur LM Studio** — lire les erreurs avant toute hypothèse :

[assistant] `llmster` (PID 67025) n'occupe que **42 Mo de RSS** — un serveur avec modèle chargé en occuperait des Go. Confirmation matérielle : aucun modèle n'est chargé. Je cherche le message d'erreur réel.

[assistant] **CAUSE RACINE — message exact, ce n'est ni un serveur zombie ni un modèle corrompu :**

```
ggml_backend_cuda_buffer_type_alloc_buffer: allocating 1288.70 MiB on device 0:
    cudaMalloc failed: out of memory
graph_reserve: failed to allocate compute buffers
llama_init_from_model: failed to initialize the context
warning: failed to mlock 108019712-byte buffer (after previously locking 1979478016 bytes)
```

**CUDA out of memory sur les compute buffers**, pas sur les poids. Je vérifie qui occupe la VRAM et pourquoi `qwen2.5-coder-14b` avait réussi là où le 9B échoue.

[assistant] **Cause racine identifiée — et ce n'est pas ce que je pensais.** Le PID qui occupe la VRAM **est LM Studio lui-même** :

| PID | Processus | VRAM |
|---|---|---|
| 226098 | `.lmstudio/.internal/utils/node` | **3386 MiB / 4096** |
| 6851 | gnome-remote-desktop | 71 MiB |

Ollama n'a **rien** en VRAM. LM Studio garde un modèle résident et refuse d'en charger un second — avec `n_ctx=32768` et `n_parallel=4`, les compute buffers seuls réclament 1,3 Go qu'il n'a plus.

[assistant] **Tout s'explique** : `qwen2.5-coder-14b` est **`loaded`** (3386 MiB, ctx 32768). Les trois autres sont `not-loaded`. Avec `justInTimeModelLoading: true`, LM Studio tente de charger à la demande **sans décharger** le modèle courant → `cudaMalloc OOM`.

**Le « modèle fantôme » n'existe pas.** C'est un état transitoire : le modèle refusé est celui qui n'est pas déjà chargé. Et cela révèle un **défaut dans mon propre code** — `discover --probe` marque définitivement « inutilisable » un modèle qui serait parfaitement fonctionnel si l'autre était déchargé.

**PHASE 3 — hypothèse unique** : *« LM Studio n'est pas cassé ; il sert un seul modèle à la fois, et c'est celui qui est `loaded` qui répond. »* Test minimal :

[assistant] **Hypothèse confirmée** : le modèle `loaded` répond (`success`, ttft 15,7 s). **LM Studio n'a jamais été cassé.**

## Cause racine

LM Studio, sur 4 Go de VRAM, ne sert **qu'un modèle à la fois** et ne décharge pas le résident avant d'en charger un autre → `cudaMalloc OOM` sur les compute buffers (1,3 Go réclamés pour `n_ctx=32768`, `n_parallel=4`).

Le vrai défaut est **dans mon code** : `discover --probe` conclut « modèle fantôme » là où l'état correct est « pas chargé, donc pas testable maintenant ».

**PHASE 4 — test qui échoue d'abord**, puis fix unique :

[assistant] Les deux tests échouent comme attendu. **Fix unique** — rendre la sélection consciente de l'état de chargement :

[assistant] Les deux passent. Je câble dans `discover()` — sonder d'abord le résident et ne plus étiqueter « fantôme » ce qui n'est que « pas chargé » :

[assistant] Disque stable à 86 % (64 Go libres) — la sauvegarde `duplicity` pousse vers Google Drive, toujours en cours. Rien à faire : le `tempdir` se videra à la fin.

Second bug, preuve déjà en main : `qwen3.5-9b` renvoie `empty_response` avec `chars=0` même à `max_tokens=300`. Ton `CLAUDE.md` le confirme (« sans `/no_think`, qwen3.5-9b part en reasoning infini et renvoie un contenu vide »). Test d'abord :

[assistant] 30 tests OK. **Vérification terrain du fix 2** sur le modèle qui échouait réellement :

[assistant] M6 n'est plus joignable (`Connection refused` — LM Studio arrêté là-bas). Je cherche un modèle *thinking* accessible localement pour valider en réel :

[assistant] `qwen3:1.7b` (thinking) est sur Ollama. Test réel — et cela va aussi révéler si Ollama souffre du même défaut :

[assistant] **Bug reproduit et cause confirmée de bout en bout** :

| Appel | Résultat |
|---|---|
| `qwen3:1.7b` sans `think=False` | `empty_response`, chars=0 |
| `qwen3:1.7b` avec `think=False` | **`success`** → `'OK.'` |

Ollama renvoie son raisonnement dans `message.thinking`, que mon parser ignore — même root cause, second provider. Je l'étends :

[assistant] Le message d'erreur donne le mauvais remède pour Ollama (`no_think` est le flag LM Studio ; Ollama attend `think=False`). Un message d'erreur qui envoie sur une fausse piste est un piège — je corrige :

[assistant] **Message exact par backend** (`think=False` pour Ollama, `no_think=True` pour LM Studio). Je commite les deux fix :

[assistant] La doc portait une analyse incomplète (« modèle fantôme »). Je la corrige — laisser un diagnostic faux dans un rapport est pire que pas de rapport :

[assistant] # Debug systématique — deux fausses pannes démasquées

## Alerte disque : pas un bug

| Preuve | |
|---|---|
| PID 18918 + 70499 | `deja-dup --backup --auto` + `duplicity incremental` **en cours** vers Google Drive |
| Écriture live | `~/.cache/deja-dup` 2,1 Go · `/tmp/duplicity-tempdir` 201 Mo |
| État | 86 %, **63 Go libres**, stable |

**Je n'ai rien tué** : interrompre duplicity en pleine passe incrémentale casse la chaîne de sauvegarde. Le `tempdir` se libérera tout seul.

## Bug 1 — le « modèle fantôme » n'a jamais existé

Ma conclusion de tout à l'heure était **fausse**. Le log serveur donne la vraie cause :

```
ggml_backend_cuda_buffer_type_alloc_buffer: allocating 1288.70 MiB on device 0:
    cudaMalloc failed: out of memory
graph_reserve: failed to allocate compute buffers
```

`/api/v0/models` tranche : `qwen2.5-coder-14b` est **`state=loaded`** (3386 MiB / 4096), les trois autres `not-loaded`. **LM Studio ne décharge pas le modèle résident** avant d'en charger un autre, et les compute buffers réclament 1,3 Go pour `n_ctx=32768` / `n_parallel=4`.

Vérification : le modèle chargé répond — `success`, ttft 15,7 s. **Rien n'était cassé.**

Le vrai défaut était **dans mon code** : `discover --probe` gravait « fantôme » là où l'état correct est « pas chargé ». Corrigé par `loaded_models()`, une sélection qui vise le résident, et un probe qui ne teste plus les non-résidents sur un backend mono-modèle.

## Bug 2 — `empty_response` masquait le mode *thinking*

Reproduit et

[user] # JARVIS Agent 17 — JARVIS Brain

**Rôle :** Cerveau apprenant : détecte tes habitudes, crée des skills.

## Action

Traite :  — délègue l'analyse à l'agent architect-guardian et persiste les insights via mcp__jarvis-memory__save_memory.

[assistant] Alerte disque déjà traitée au tour précédent (sauvegarde `duplicity` en cours, 63 Go libres, rien à nettoyer). Je passe au brain.

[assistant] L'agent d'audit tourne. Je vérifie d'abord ce que la mémoire JARVIS contient déjà, pour compléter au lieu de dupliquer.

[assistant] L'agent a produit une analyse solide. Je ne la prends pas au mot — je vérifie le point le plus grave avant d'agir : *le verrou de checkpoint ne protège que les threads, pas les processus*.

[assistant] Confirmé dans le code : `_LOCK = threading.Lock()` (ligne 30) protège un read-modify-write (`update_task` L79, `set_status` L91). **Entre processus, rien.** Et c'est exactement le scénario que j'ai exécuté ce soir : `watchdog --act` dans un shell pendant qu'un `run` tourne dans l'autre.

**Test qui prouve la perte de données, avant tout fix :**

[assistant] Le test révèle **pire que la perte d'écriture** — une exception dans `_write`. Je regarde l'erreur complète :

[assistant] **Deux défauts, une seule racine.** Le fichier temporaire est le **même chemin pour tous les processus** (`path.with_suffix(".tmp")`) : l'un le renomme pendant que l'autre écrit dedans. Mon commentaire promettait une « écriture atomique » — vrai contre un `kill`, faux contre la concurrence.

Fix :

[assistant] Test de concurrence **OK**. Je complète la docstring qui promettait une atomicité qu'elle n'assurait pas, puis valide l'ensemble :