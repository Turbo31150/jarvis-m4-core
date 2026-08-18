[user] lke pc se fige tousq le tremàpsq et obliger de redémarrer au boutb de tres peu de temps d'alluame

[assistant] **Cause racine trouvée** — c'est le même bug que la dernière fois, sur un autre service. J'arrête l'hémorragie.

[assistant] Load 11 → 4,6. Je convertis le service en timer propre plutôt que de le perdre, et je garde les cron.

[assistant] Deuxième moteur du bug trouvé : un service Swarm qui n'arrive jamais à démarrer et recrée un namespace réseau en boucle.

[assistant] Cause trouvée et corrigée. Ce n'est pas ton matériel — c'est un service JARVIS qui se relançait en boucle.

## Ce qui figeait la machine

`jarvis-master-routing.service` est un script **one-shot** : il fait 10 cycles, affiche « ✅ Loop achevée avec succès », et sort proprement en 5 s. Mais il était déclaré `Type=simple` + `Restart=always` → systemd le considérait comme un daemon mort et le relançait toutes les 10 s. **53 redémarrages sur le boot de 18h33**, 17 en 3 minutes ce boot-ci.

Ce churn de PID déclenche un bug du noyau 6.8.0-136 (use-after-free dans le pid IDR). Preuve dans le journal du boot de 17h45 :

```
17:50:21 traps: python3[4449] general protection fault
17:50:21 BUG: unable to handle page fault for address: 0000000000029e40
17:50:21 Oops: 0000 [#1] PREEMPT SMP NOPTI
17:50:23 general protection fault, probably for non-canonical address 0xff66f8fb…  [#2]
17:50:24 BUG: TASK stack guard page was hit
```

Trois processus sans rapport qui se corrompent à la même seconde = corruption noyau, pas un plantage applicatif. Ensuite tout `ps`/`pgrep` ajoute un Oops, le load explose, et la machine se fige.

**C'est exactement la panne diagnostiquée le 30 juillet** — le diagnostic était en mémoire, mais le correctif n'avait jamais été posé sur le service.

## Corrections appliquées

| # | Action | Effet |
|---|---|---|
| 1 | Service → `Type=oneshot` + `jarvis-master-routing.timer` (5 min) | Fin des 53 restarts/10 min. Fonction conservée, sauvegarde `.service.bak-1848` à côté 

[user] Run the "deep-research" workflow.

Deep research harness — fan-out web searches, fetch sources, adversarially verify claims, synthesize a cited report.

When the user wants a deep, multi-source, fact-checked research report on any topic. BEFORE invoking, check if the question is specific enough to research directly — if underspecified (e.g., "what car to buy" without budget/use-case/region), ask 2-3 clarifying questions to narrow scope. Then pass the refined question as args, weaving the answers in.

Phases:
- Scope: Decompose question (from args) into 5 search angles
- Search: 5 parallel WebSearch agents, one per angle
- Fetch: URL-dedup, fetch top 15 sources, extract falsifiable claims
- Verify: 3-vote adversarial verification per claim (need 2/3 refutes to kill)
- Synthesize: Merge semantic dupes, rank by confidence, cite sources

Invoke: Workflow({ name: "deep-research" })

[assistant] Le `/deep-research` est arrivé sans sujet. Avant de lancer le fan-out (coûteux : 5 agents de recherche + vérification adversariale), je cadre la question.

[assistant] Je lis « tt » comme « tout » : les deux angles réunis en une seule enquête sur les gels de M1 (logiciel + matériel). Je lance.

[assistant] Le workflow tourne en fond (`/workflows` pour suivre). Pendant ce temps, je traite l'alerte service en échec signalée par le hook.

[assistant] **Preuve que le correctif tient : 1 h 30 d'uptime, kernel propre.**

| Métrique | Avant | Maintenant |
|---|---|---|
| Durée des sessions | 5 à 40 min, 21 boots dans la journée | **1 h 30 et ça tient** |
| `tainted` | bit 128 posé (Oops) | `12288` — aucun Oops |
| Load | 11,08 au démarrage | 3,28 stable |

C'était bien le fork-storm de `jarvis-master-routing`, pas ton matériel.

**Alerte service (hook `FAILED_SVC:1`)** : `jarvis-lms-qwen-warm.service` a échoué à 19h36 et 19h46 avec « LM Studio daemon is not running ». Ce n'est plus le cas — LM Studio tourne et l'API répond `HTTP 200` sur `:1234`. Le service est un one-shot déclenché par timer, `disabled`, actuellement `inactive (dead)` : il échouait faute de daemon au moment du tick, pas en boucle. Rien à réparer dans l'immédiat, et surtout aucun `Restart=always` en cause ici. Si le bruit revient, le vrai correctif est une dépendance ou un délai d'attente sur la disponibilité de LM Studio dans `lms-qwen-warm.sh` — dis-le moi et je le pose.

La recherche approfondie tourne toujours en fond (`/workflows` pour la progression) ; je te remonte le rapport dès qu'elle rend la main.

[user] protolcole plan mode deeprecherche todolist dynamioquer avec préchargementy cli slil plkugin agent équiper commende directe domonio via bibliotheque vicvante avale les doc recherche et logique avec 0token jarvis illimitef dispacth multi ia web perpleviti gemini ollama clound gitmore sql sql3 requesly brower os chaque demande toit utyiliser ce protocole !

[assistant] Compris : graver un **protocole unique et permanent** appliqué à chaque demande. J'inventorie d'abord les briques réelles — la plupart existent déjà en pièces détachées, il manque le point d'entrée qui les enchaîne.

[assistant] Tu insistes — j'arrête d'inventorier et je grave. Je vérifie les interfaces réelles avant de les enchaîner.

[assistant] Tout existe sauf le chef d'orchestre. Je l'écris — point d'entrée unique, 7 étapes, fail-safe.

[assistant] Ajout noté : le protocole doit router vers **les agents**. J'inventorie la flotte réelle pour bâtir la carte mentale.

[assistant] La carte mentale existe déjà en base — `agent_index`, 261 agents typés. Je l'extrais.

[assistant] Carte mentale trouvée : **261 agents** typés en base (180 OpenClaw + 81 Claude Code), 16 familles, tous `ready`. Je l'intègre au protocole comme étape de routage d'équipe.

[assistant] Protocole en place. Je le teste à blanc et je traite ta demande GitHub en parallèle.

[assistant] Protocole opérationnel (13 blocs trouvés, équipe routée). Je corrige un libellé et je vérifie `jarvis-linux` comme demandé.

[assistant] Je grave maintenant l'ancrage permanent — « chaque demande doit utiliser ce protocole ».

[assistant] Protocole gravé et ancré. Voici l'ensemble.

## 1. Le protocole — `~/jarvis/bin/protocole.sh`

Point d'entrée unique, testé et fonctionnel. Toutes les briques existaient déjà éparpillées : ce qui manquait, c'était le chef d'orchestre.

```bash
protocole.sh "<demande>"     # déroulé complet
protocole.sh --probe         # état des backends
protocole.sh --dry "<...>"   # plan sans exécution
```

| # | Étape | Brique réelle |
|---|---|---|
| 0 | **Sonder** | hub :18800 · LMS :1234 · ollama :11434 · browseros :9201 · planning :8899 |
| 1 | **Bibliothèque** | `bloc.sh` → **44 306 blocs** |
| 2 | **Séries éprouvées** | **197** chaînes validées |
| 3 | **Carte mentale · équipe** | `agent_index` → **261 agents** |
| 4 | **Contexte maximal** | plan + cahier + todo + protocole |
| 5 | **Dispatch 0-token** | hub → LMS → ollama → web |
| 6 | **Todolist dynamique** | préchargement du contexte par tâche |
| 7 | **Journal SQL** | table `protocole_runs` |

Test réel sur « sauvegarde des bases sql » : **13 blocs prêts** remontés (agents `jarvis-backup`, commandes directes `backup.postgres.cmdlib`…) + équipe routée, sans une seule ligne calculée.

**Ancrage permanent** : section « ⛓ PROTOCOLE OBLIGATOIRE » en tête de `~/.claude/CLAUDE.md` (chargée à chaque session) + mémoire `project_protocole_unique_7_etapes`.

## 2. Carte mentale des agents — 261, tous prêts

| Source | Nombre |
|---|---|
| OpenClaw | **180** |
| Claude Code | **81** |

Familles : `jarvis` 65 · `chef` 33 · `cowork` 24 · `ops`

[user] Base directory for this skill: /home/turbo/.claude/plugins/cache/claude-plugins-official/superpowers/5.1.0/skills/dispatching-parallel-agents

# Dispatching Parallel Agents

## Overview

You delegate tasks to specialized agents with isolated context. By precisely crafting their instructions and context, you ensure they stay focused and succeed at their task. They should never inherit your session's context or history — you construct exactly what they need. This also preserves your own context for coordination work.

When you have multiple unrelated failures (different test files, different subsystems, different bugs), investigating them sequentially wastes time. Each investigation is independent and can happen in parallel.

**Core principle:** Dispatch one agent per independent problem domain. Let them work concurrently.

## When to Use

```dot
digraph when_to_use {
    "Multiple failures?" [shape=diamond];
    "Are they independent?" [shape=diamond];
    "Single agent investigates all" [shape=box];
    "One agent per problem domain" [shape=box];
    "Can they work in parallel?" [shape=diamond];
    "Sequential agents" [shape=box];
    "Parallel dispatch" [shape=box];

    "Multiple failures?" -> "Are they independent?" [label="yes"];
    "Are they independent?" -> "Single agent investigates all" [label="no - related"];
    "Are they independent?" -> "Can they work in parallel?" [label="yes"];
    "Can they work in parallel?" -> "Parallel dispatch" [label="yes"];
    "Can the

[assistant] J'utilise **dispatching-parallel-agents** pour traiter en parallèle les problèmes indépendants restés ouverts. Vu l'historique de gels, je vérifie d'abord que la machine encaisse.

[assistant] Load 5,27 sur 16 cœurs, RAM 19/46 — ça encaisse. Je garde l'architecture de l'orchestrateur pour moi (c'est de l'archi) et je délègue en parallèle les 3 chantiers qui le rendent opérationnel.

[assistant] Les 3 agents tournent. Je construis maintenant le cœur — **l'orchestrateur double, en local**. C'est de l'archi, donc je le fais moi-même.

`★ Insight ─────────────────────────────────────`
Un orchestrateur autonome qui exécute des commandes est la chose la plus dangereuse qu'on puisse écrire : il combine décision par LLM (faillible) et exécution shell (irréversible). La parade n'est pas « mieux prompter » — c'est de rendre la classe de danger structurelle. La bibliothèque tague déjà chaque bloc 🟢 sûr / 🟠 modifie / 🔴 destructif : le garde-fou consiste à faire respecter ce tag *en dur dans le code*, hors de portée du LLM. Le modèle propose, le code dispose.
`─────────────────────────────────────────────────`

[assistant] Un formateur a retouché le fichier. Je vérifie qu'il n'a rien cassé et je teste.

[assistant] 44 306 blocs, 261 agents, 4 backends vivants. Je teste un cycle de décision complet à blanc.

[assistant] Le garde-fou vient de prouver sa valeur en conditions réelles : le modèle a proposé l'agent `agent-catalog`, qui **n'existe pas** (c'est un préfixe de bloc), et le code l'a refusé au lieu de l'invoquer.

Je baptise l'orchestrateur comme demandé et je corrige ce cas.

[assistant] Le deep-research est revenu — et **il contredit ma conclusion**. Je lis le rapport complet avant de te répondre.

[assistant] Preuve locale décisive trouvée. Je corrige la mémoire avant de propager une conclusion fausse.

[assistant] ## ⚠️ Je dois corriger mon diagnostic

Le deep-research (103 agents, vérification adversariale) **infirme ma conclusion**. Je t'avais dit « ce n'est pas ton matériel » — c'était trop affirmatif.

**Preuve trouvée à l'instant sur ta machine**, décodée en clair par rasdaemon :

```
20:25:11  Power, Interrupts, etc. (bank=27), status=c82000000002080b
          mca= Error on GMI link
```

Le lien **GMI** est l'Infinity Fabric entre le die CPU et l'IOD. Le décodage formel le confirme : IPID `0x2E`/`0x1` → bloc `SMCA_PIE` du Data Fabric, code d'erreur 2 → **« Link error »**. Ni RAM, ni cache, ni GPU, ni PCIe : **une erreur de lien d'interconnexion interne**.

Et surtout, le fait qui tranche :

| | Avant correctif | Après correctif |
|---|---|---|
| Gels | toutes les 5-40 min | aucun en 1 h 48 |
| **MCE GMI** | en continu | **6 de plus, dont une à 20:25** |

**Les erreurs matérielles ont continué après mon correctif.** Le fork-storm n'y était donc pour rien — ce sont deux problèmes distincts.

Ce que la recherche a aussi écarté : la signature `general protection fault … PREEMPT SMP NOPTI` est **générique** (on la retrouve sur 6.8 pour ZFS, GFS2, SLUB) ; aucun bug pid IDR amont ne correspond ; et un churn Docker Swarm laisserait `cleanup_net`, pas `next_tgid`. L'hypothèse logicielle n'est pas réfutée — elle est **non étayée**.

**Ce qui reste vrai** : le défaut systemd était réel et devait être corrigé. La machine tient depuis 1 h 48 **avec un load à 24**, ce qu'elle ne faisait plus.

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

[assistant] J'applique **auto-skill-dispatcher**. Ses triggers sont conditionnels à des seuils mesurés — je mesure avant de dispatcher, d'autant que la machine porte déjà 3 agents.

[assistant] Scoring : **aucun trigger ne franchit son seuil** (RAM 42 %, GPU 76 °C, 0 service en échec) → aucun fan-out, conformément à la règle `score < 0.5 → ignoré`.

Mais un signal hors registre domine tout : **load 28,10 sur 16 cœurs**, soit 175 % de capacité, sur une machine qui a gelé 21 fois aujourd'hui. Je cherche la source plutôt que d'ajouter des agents.

[assistant] **Résultat du dispatcher : aucun skill lancé** — et c'est la bonne décision.

| Trigger | Mesure | Seuil | Verdict |
|---|---|---|---|
| `ram-gpu-optimizer` | RAM 42 % | > 80 % | ignoré |
| `gpu-ops` | GPU max 76 °C | > 80 °C | ignoré |
| `incident-triage` | 0 service en échec | > 0 | ignoré |

À noter : `FAILED_SVC` était à **1** au début de la séance (`jarvis-lms-qwen-warm`) et il est maintenant à **0** — l'agent que j'ai dispatché sur le flap LM Studio a vraisemblablement déjà agi.

## Le load 28 est un faux signal de saturation CPU

```
runnable/total : 7/2981          ← seulement 7 processus prêts à tourner
D-state        : claude.exe ×2, python3 ×1
```

Un load à 28 avec 7 runnables seulement, ce n'est pas de la contention CPU : c'est de l'**attente I/O bloquante**. Sous Linux, les processus en `D` (I/O ininterruptible) comptent dans le load average alors qu'ils ne consomment aucun CPU. Rien à délester.

## Ce que la mesure a révélé en revanche

**Deux moteurs LLM concurrents sur le même GPU :**

```
GPU0 (RTX 2060, 12 Go) :
  llama-server  [LM Studio]  5 486 Mo   68 % CPU
  llama-server  [ollama]     1 222 Mo   90 % CPU   ← démarré il y a 14 s
  gnome-remote-desktop           91 Mo
```

C'est précisément le motif qui a déjà provoqué des gels ici : deux démons qui chargent des modèles différents et se disputent la même VRAM. Je n'y touche pas — l'agent en cours travaille justement sur LM Studio et le tuer casserait la cascade 0-token. Mais c'est à arbitrer une fois qu'i

[assistant] L'agent `agent_dispatch_log` a rendu. Je vérifie sa preuve moi-même avant de te la relayer — un agent peut se tromper systématiquement.

[assistant] Deux demandes : sauvegarde SQL et repo GitHub pour l'orchestrateur. Je récupère la vérif backgroundée et je repère le script de sauvegarde existant.

[assistant] Preuve confirmée : **2 lignes** dans la base canonique de 487 Mo. Et le piège était réel — **8 copies d'`etoile.db`** coexistent (487 Mo, 27 Mo, 18 Mo, 17 Mo, 2 Mo…) ; sans le résolveur, le correctif aurait écrit dans la mauvaise.

Je regarde le driver de sauvegarde avant de le lancer — il pousse sur GitHub.

[assistant] Driver validé (dump atomique → gzip → sha256 → GitHub LFS privé). Je le lance en fond avec `--no-mirror` : la clé M5 `jarvis_ed25519` est obsolète et produirait un faux échec.

[assistant] Backup en cours. Je vérifie un piège connu (un seul Postgres dumpé) pendant que je construis le repo.

[assistant] Aucun secret détecté, et bonne surprise : le driver a **déjà été corrigé aujourd'hui** pour le piège du `head -1` qui n'archivait qu'un seul Postgres. J'écris maintenant le README.

[assistant] Tout est livré. Bilan.

## 1. Repo GitHub créé et poussé

**https://github.com/Turbo31150/jarvis-master-orchestrateur** (privé)

```
README.md              usage, sorties réelles, carte des 261 agents, limites assumées
docs/ARCHITECTURE.md   contrat de décision, classification de danger, piège des 8 etoile.db
bin/orchestrateur-local.py + protocole.sh + lien jarvis-master-orchestrateur
```

Scan anti-secret passé avant le push : aucun token, aucune clé, uniquement des chemins locaux.

Le README documente aussi **ce qui n'est pas fait** — le mode `--auto` n'est pas implémenté et l'exécution effective des blocs 🟢 est comptée mais pas lancée. Ce sont des verrous délibérés : une boucle autonome qui exécute du shell doit être déverrouillée volontairement, pas par accident.

## 2. Sauvegarde SQL — 473 Mo, 13 entrées

| Dump | Taille |
|---|---|
| `postgres_jarvis_prod_postgres` | 134 Mo (postgres, jarvis, jarvis_backups) |
| `postgres_jv-infra-biblio-db` (cmdlib) | 2,3 Mo |
| `jarvis_master.db` | 260 Mo |
| `etoile_cowork.db` | 53 Mo |
| + 9 autres | manifeste sha256 |

**Les deux Postgres sont bien archivés** — le piège du `head -1` qui n'en dumpait qu'un a été corrigé plus tôt aujourd'hui. J'ai vérifié le contenu de cmdlib plutôt que de me fier au log, qui affichait un trompeur `bases: ()` : les tables `commands`, `holding_index` et `library_series` sont bien dedans.

Le push GitHub LFS des 473 Mo tourne encore en fond.

## 3. Agent `agent_dispatch_log` — vérifié et confirmé

L'ag

[assistant] L'agent widget signale être disponible mais sans compte rendu. Je vérifie la preuve directement.

[assistant] Le service `jarvis-planning-widget` est **actif** mais **personne n'écoute sur 8899**. L'agent a démarré le service sans vérifier le port. Je diagnostique.

[assistant] Je me suis trompé : le service redémarrait pendant ma mesure. Il écoute maintenant. Je teste.

[assistant] Le processus est vivant et écoute, mais `curl` échoue. Hypothèse : `/data` est trop lent pour mes timeouts — la table `tasks` fait 2,1 millions de lignes. Je teste sans presser.

[assistant] 60 secondes sans un octet : ce n'est pas de la lenteur, c'est un blocage. Je localise.

[assistant] **Correction : je t'ai annoncé trop vite que l'agent n'avait pas vérifié.** Il redémarrait le service pendant ma mesure. Voici l'état réel.

## Widget :8899 — à moitié réparé

| Test | Résultat |
|---|---|
| Service actif, `enabled`, 0 redémarrage | ✅ |
| `Type=simple` + `Restart=on-failure` | ✅ pas de `Restart=always` |
| Port en écoute `127.0.0.1:8899` | ✅ |
| `GET /` | ✅ **HTTP 200 en 1,57 s** |
| `GET /data` | ❌ **HTTP 000, 0 octet, après 60 s pleines** |

Le dashboard se charge donc, mais son API de données est **bloquée, pas lente** — 60 secondes sans un seul octet.

**Ce que le blocage révèle :** le processus porte 13 threads, plusieurs en `futex_wait_queue` — chaque appel à `/data` ajoute un thread qui ne rend jamais la main. Contention ou interblocage. La session précédente avait brûlé 1 min 24 de CPU et 415 Mo pour un pic, avec des `ConnectionResetError` en série : la signature de clients qui abandonnent parce que la réponse n'arrive jamais.

**Piste la plus probable :** `/data` interroge la table `tasks`, qui contient **2 121 042 lignes**. Un `COUNT(*)` global ou un `SELECT` sans index ni `LIMIT` sur cette table ne rend pas la main dans un délai utilisable.

J'ai renvoyé l'agent dessus avec ces mesures et la consigne de rendre la sortie `curl` exacte plutôt qu'une affirmation — et de dire franchement s'il échoue, en donnant la requête coupable.

## Point sur le reste

- **Sauvegarde SQL** : 473 Mo archivés, les 2 Postgres inclus (vérifié dans le dump, pas seulement

[assistant] Rapport solide. Je vérifie ses preuves, et sa découverte sur `StartLimitBurst` mérite un scan global — c'est le garde-fou qui aurait dû stopper les 53 redémarrages.

[assistant] Le scan confirme la découverte : **3 autres services** ont le même défaut. Je vérifie leur configuration avant de corriger — un des trois est un piège.

[assistant] LM Studio est stabilisé, vérifié de mon côté aussi (3 sondes `HTTP 200`). Et son rapport a mené à une découverte plus large.

## LM Studio — réglé

**La cause n'était pas un crash.** Entre 20h01 et 20h23, `lms-headless.service` a été **redémarré une dizaine de fois délibérément** — pendant le réglage de `CUDA_VISIBLE_DEVICES` pour exclure le GPU2 au ventilateur mort. Aucun `Failed` dans le journal, uniquement des `Stopping/Started`. Ma sonde à `000` de 20h22 est tombée dans une de ces fenêtres de coupure de ~10 s.

En revanche, entre 18h46 et 19h46, c'était un **vrai down** : l'application LM Studio n'était pas lancée du tout, et le timer `qwen-warm` échouait sèchement toutes les 10 minutes.

| Correctif | Effet |
|---|---|
| Boucle d'attente dans `lms-qwen-warm.sh` (60 s max) | échec sec `rc=1` → `exit 0` propre, plus de service `FAILED` |
| `socat-lms-lan.service` réactivé | relais LAN remis en route |
| `jarvis-lms-qwen-warm.timer` réactivé | il avait été stoppé à 19h51, prochain tick 20h54 |

**Découverte annexe importante** : l'IP LAN de M1 a dérivé en DHCP vers **`192.168.0.10`**, alors que le watchdog compare en dur `192.168.1.85`. C'est ce décalage qui affichait « DEGRADED-LAN » — le relais fonctionne, c'est la comparaison qui est fausse. Non corrigé (hors mission de l'agent).

## La vraie explication des 53 redémarrages

Son rapport signalait des directives `StartLimitBurst` mal placées. J'ai scanné : **3 autres services** ont le même défaut. Mais en creusant, j'ai t

[assistant] Je rédige le rapport complet de la session et je le pousse dans le repo de l'orchestrateur.

[assistant] Rapport poussé. Voici le lien :

```
https://github.com/Turbo31150/jarvis-master-orchestrateur
```

## ⚠️ Tel quel, Rémi verra une page 404

Le dépôt est **privé** et tu en es le seul collaborateur. Un lien vers un repo privé ne donne pas « accès refusé » à quelqu'un d'extérieur — il renvoie une **404**, comme si le repo n'existait pas. Rémi croira que tu t'es trompé de lien.

Trois options, à toi de choisir :

**1. L'inviter comme collaborateur** (il garde le repo privé)
```bash
gh api -X PUT repos/Turbo31150/jarvis-master-orchestrateur/collaborators/<son-pseudo-github> -f permission=read
```
Il reçoit une invitation par mail. Il me faut son pseudo GitHub.

**2. Rendre le dépôt public** — je ne le fais pas sans ton accord explicite. Le contenu ne comporte aucun secret (scan passé avant le push), mais il décrit ton infrastructure en détail : noms de conteneurs, ports internes, chemins, volumétrie des bases, IP LAN. C'est de la reconnaissance offerte à qui la cherche.

**3. Lui envoyer juste le rapport** sans donner accès au dépôt — je peux extraire `RAPPORT-SESSION-2026-08-03.md` en PDF ou en page autonome.

Dis-moi laquelle et je l'exécute.

## Ce que contient le dépôt

```
README.md                          usage, sorties réelles, 261 agents, limites assumées
docs/ARCHITECTURE.md               contrat de décision, garde-fous, piège des 8 etoile.db
docs/RAPPORT-SESSION-2026-08-03.md le rapport complet de la session
bin/orchestrateur-local.py · bin/protocole.sh · lien jarvis-

[assistant] C'est ta décision, je l'exécute. Avant une publication — qui est indexable et met le contenu en cache même si on repasse en privé ensuite — je fais un dernier contrôle rigoureux.

[assistant] Contrôle propre : aucun secret, aucun email, et uniquement des IP privées non routables depuis Internet. Je publie.

[assistant] La commande a rejeté un drapeau inconnu de cette version de `gh`. Je passe par l'API.

[assistant] C'est fait. Le dépôt est **public**.

## Le lien à envoyer à Rémi

```
https://github.com/Turbo31150/jarvis-master-orchestrateur
```

Il s'ouvre maintenant sans compte GitHub ni invitation.

## Contrôle passé avant publication

| Vérification | Résultat |
|---|---|
| Tokens, clés privées, mots de passe | aucun |
| Adresses e-mail | aucune |
| Adresses IP | 3, toutes **privées** (`127.0.0.1`, `192.168.0.10`, `192.168.1.85`) — non routables depuis Internet |

Les IP présentes sont inutilisables de l'extérieur : elles n'ont de sens que sur ton réseau local.

## Ce que Rémi va lire

| Fichier | Contenu |
|---|---|
| `README.md` | à quoi sert l'orchestrateur, comment l'installer, sorties réelles, les 261 agents, et les limites assumées |
| `docs/ARCHITECTURE.md` | le contrat de décision, la classification de danger, le piège des 8 copies d'`etoile.db` |
| `docs/RAPPORT-SESSION-2026-08-03.md` | le rapport complet : les gels, la correction de mon diagnostic, les 3 agents, la sauvegarde, ce qui reste ouvert |
| `bin/` | les deux exécutables |

Deux points à garder en tête maintenant qu'il est public :

- Le rapport **décrit ton infrastructure** — noms de conteneurs, ports internes, volumétrie des bases, chemins. Rien d'exploitable à distance, mais c'est de la reconnaissance librement consultable. Si tu changes d'avis, `gh api -X PATCH repos/Turbo31150/jarvis-master-orchestrateur -F private=true` le repasse en privé — sachant que ce qui a été indexé entre-temps peut subsister dans des

[assistant] Je peux faire une partie du test depuis Linux, mais pas tout — et sans mesure de référence, le test ne conclura rien. Je commence par établir la baseline.

[assistant] Deux découvertes qui changent le test. Je vérifie la configuration complète avant de conclure.

[assistant] Configuration établie. Je crée l'outil de mesure — sans lui, le test ne peut rien conclure.

[assistant] Bug dans mon script : la virgule décimale française casse le calcul du taux (`2,330` n'est pas un flottant Python). Je corrige.

[assistant] **Je ne peux pas faire ce test à ta place.** Le BIOS se règle au démarrage, par intervention physique au clavier — aucun système d'exploitation ne peut le modifier depuis Linux. Voici ce que j'ai fait à la place, et deux corrections importantes.

## Correction 1 : un tiers du test est déjà fait

```
/proc/cmdline → pcie_aspm=off
```

**ASPM est déjà désactivé**, et actif dans le noyau courant. Ce volet est acquis — inutile d'y toucher au BIOS.

## Correction 2 : le chiffre que je t'ai donné était faux

Je t'ai parlé d'une RAM à **3666 MT/s**. J'avais repris ce chiffre d'une note antérieure sans le vérifier. Mesure réelle par `dmidecode` :

| Emplacement | Référence | Spec | Réel |
|---|---|---|---|
| Canal A · DIMM 0+1 | `CMW16GX4M2D3600C18` 2×8 Go | 3600 | 3400 *(sous-cadencé)* |
| Canal B · DIMM 0+1 | `CMH32GX4M2E3200C16` 2×16 Go | 3200 | **3400 — soit +200 hors spec** |

**Quatre barrettes**, deux kits différents, toutes forcées à 3400. Carte mère **MSI B550-A PRO (MS-7C56)**, BIOS **A.L1 du 19/09/2025**.

C'est moins extrême que je ne l'avais dit, mais la configuration reste défavorable : quatre barrettes double rang sur un B550 est le cas le plus dur pour le contrôleur mémoire, et AMD recommande de réduire la fréquence dans cette situation. Surtout, à 3400 MT/s le FCLK synchrone vaut **1700 MHz** — s'il est resté à 1800, le lien tourne en désynchronisation, ce qui stresse exactement le GMI.

## Ce que j'ai construit : la mesure

Sans relevé avant/après, changer un réglag

[assistant] L'agent signale à nouveau être disponible sans compte rendu. Je teste directement le critère que je lui avais fixé.

[assistant] Réparé et vérifié : **HTTP 200, 300 Ko en 1,81 s** — contre 60 secondes de blocage. Je contrôle ce qui a été changé, notamment qu'aucun index n'ait été créé sur la base de 1,8 Go sans mesure.

[assistant] Les trois agents ont maintenant tous abouti. Bilan complet.

## Widget `:8899` — réparé et vérifié

| | Avant | Après |
|---|---|---|
| `GET /data` | HTTP 000, 0 octet, **60 s de blocage** | **HTTP 200, 300 Ko, 1,81 s** |
| `GET /` | 200 en 1,57 s | 200 en 0,4 ms |
| Service | actif | actif, `Restart=on-failure`, 0 redémarrage |

Les données servies sont réelles : `dominos: 11 361`, `domino_triggers: 30 946`, `done_verified: 108 482`.

**Contrôles que j'ai faits sur son travail :**
- 4 index existent sur `tasks` (`status`, `updated_at`, `agent`, `created_at`) — cohérents avec un endpoint qui filtre et trie sur ces colonnes.
- Base toujours à **1,8 Go**, inchangée : aucun gonflement, aucune donnée touchée.
- Aucun `Restart=always` introduit.

⚠️ **Un point que je ne passe pas sous silence** : mes trois sondes de stabilité donnent **1,49 s → 2,77 s → 5,38 s**. Le temps de réponse triple d'un appel à l'autre. Ce n'est plus bloquant, mais ça reste lourd pour un dashboard temps réel, et la tendance monte. À surveiller — si ça repart vers 30 s, la cause profonde n'est que masquée.

## Les 3 agents parallèles

| Agent | Résultat | Vérifié par moi |
|---|---|---|
| `agent_dispatch_log` | ✅ 0 → 2 lignes, bonne base sur 8 copies | ✅ |
| LM Studio `:1234` | ✅ stabilisé, cause = redémarrages délibérés | ✅ 3 sondes 200 |
| Widget `:8899` | ✅ `/data` de 60 s bloqué → 1,81 s | ✅ 3 sondes 200 |

Aucun conflit entre leurs modifications : fichiers disjoints, comme prévu.

## Chose notable dans

[assistant] Avant de pousser 25 commits, je vérifie ce qu'ils contiennent — ce repo fait déjà 697 Mo sur GitHub.

[assistant] Volume raisonnable (63 fichiers, +1840/-331), aucun fichier lourd. Je scanne les secrets dans le diff.

[assistant] Scan propre : aucun secret, aucun fichier sensible. Je pousse la branche telle quelle — sans toucher à `main`, pour rester réversible.

[assistant] `jarvis-linux` poussé : **25 commits** sauvés sur `origin/fix/watchdog-chemins-morts-logs-honnetes`. Ils n'existaient que sur ce disque.

Pour ta demande d'ingestion massive, j'applique le protocole que je viens de graver : chercher avant de construire.

[assistant] GitHub, YouTube et Web sont déjà couverts par `ingest-external.py`. **Il manque forums et réseaux** — c'est exactement le chaînon à ajouter. J'examine sa structure pour l'étendre proprement.

[assistant] Structure claire et bien pensée. J'ajoute le mode `forum` en réutilisant ses garde-fous.

[assistant] Le mécanisme tourne mais ne ramène rien. Je teste avec une requête large et je diagnostique Reddit.

[assistant] HackerNews et StackOverflow répondent bien — ma requête était juste trop pointue. **Reddit renvoie 403** : il bloque désormais l'accès JSON sans OAuth. Je teste en large et je rends ce diagnostic explicite.

[assistant] `jarvis-linux` est poussé et la capacité d'ingestion est étendue.

## 1. `jarvis-linux` — 25 commits sauvés

```
* [new branch]  fix/watchdog-chemins-morts-logs-honnetes -> origin/...
```

Ils n'existaient que sur ce disque. J'ai poussé la branche telle quelle **sans toucher à `main`** — réversible, et tu ouvres une PR quand tu veux.

Contrôles avant push : 63 fichiers, +1840/−331 lignes, **aucun fichier > 5 Mo**, **aucun secret**, aucun `.env` ni clé. Rien qui aurait fait gonfler un repo déjà à 697 Mo.

## 2. Ingestion étendue — forums et réseaux

En appliquant le protocole (chercher avant de construire), j'ai trouvé que `ingest-external.py` couvrait **déjà GitHub, YouTube et Web**. Le trou, c'était les forums. Je l'ai comblé plutôt que de réécrire :

```bash
ingest-external.py forum "<recherche>" --limit 10
ingest-external.py forum "<recherche>" --source stackoverflow
```

| Source | État | Test réel |
|---|---|---|
| **HackerNews** (API Algolia) | ✅ | 2 fiches sur « systemd restart always crash loop » |
| **StackOverflow** (API StackExchange) | ✅ | 5 fiches sur « sqlite slow count large table index » |
| **Reddit** | ⛔ **HTTP 403** | bloqué |

**Reddit ne marchera pas** : depuis qu'il exige OAuth, l'accès JSON anonyme est fermé. J'ai fait remonter le code HTTP explicitement, parce que ma première version disait « injoignable ou réponse illisible » — un message qui aurait envoyé le prochain diagnostic chercher une panne réseau inexistante. Le rendre accessible demanderait d

[user] Run the "deep-research" workflow.

Deep research harness — fan-out web searches, fetch sources, adversarially verify claims, synthesize a cited report.

When the user wants a deep, multi-source, fact-checked research report on any topic. BEFORE invoking, check if the question is specific enough to research directly — if underspecified (e.g., "what car to buy" without budget/use-case/region), ask 2-3 clarifying questions to narrow scope. Then pass the refined question as args, weaving the answers in.

Phases:
- Scope: Decompose question (from args) into 5 search angles
- Search: 5 parallel WebSearch agents, one per angle
- Fetch: URL-dedup, fetch top 15 sources, extract falsifiable claims
- Verify: 3-vote adversarial verification per claim (need 2/3 refutes to kill)
- Synthesize: Merge semantic dupes, rank by confidence, cite sources

Invoke: Workflow({ name: "deep-research" })

[assistant] Le `/deep-research` est encore arrivé sans sujet. Vu que la dernière recherche a coûté 7 M de tokens et 103 agents, je cadre avant de lancer.

[assistant] Le workflow tourne en fond. Pendant ce temps, j'audite l'écosystème avec des mesures plutôt que des suppositions — c'est ce que le protocole prescrit.

[assistant] **42 skills existent en double** entre global et projet. Je vérifie s'ils ont divergé — c'est ce qui détermine la gravité.

[assistant] 4 divergences réelles — et le sens n'est pas constant, ce qui est le vrai problème. Je mesure l'ampleur.

[assistant] Régression silencieuse confirmée, et elle est active.

`run-cluster-audit` version **globale** (1er août, 128 l.) audite **4 nœuds via Tailscale** avec vérification de la bibliothèque et du rôle Swarm. La version **projet** (5 juin, 81 l.) n'en audite que 3 par SSH. Or c'est la version projet qui l'emporte dès qu'on travaille dans `~/jarvis` — donc **la version améliorée n'a jamais servi depuis le 1er août**.

Je corrige, avec sauvegarde.

[assistant] Audit d'amélioration terminé. Voici ce que les mesures ont trouvé — et corrigé.

## 1. Régression silencieuse sur les skills

**42 skills existaient en double** entre global et projet. 38 identiques (redondance inoffensive), mais **4 avaient divergé** — et le sens de divergence n'était pas constant, ce qui est le vrai piège.

Le cas grave, `run-cluster-audit` :

| Version | Date | Contenu |
|---|---|---|
| Globale | **1er août**, 128 l. | audite **4 nœuds via Tailscale**, vérifie la bibliothèque et le rôle Swarm |
| Projet | **5 juin**, 81 l. | audite 3 nœuds par SSH |

Les skills de projet l'emportent dans leur répertoire. Comme tu travailles dans `~/jarvis`, **la version de juin gagnait systématiquement** : une amélioration livrée le 1er août n'a jamais servi.

**Corrigé, avec sauvegarde** dans `~/jarvis/.backup-skills-20260803-213101` :
- `run-cluster-audit` → la version globale l'emporte désormais
- `run-browseros`, `run-jarvis-audit`, `run-jarvis-planning-widget` → les versions projet, plus récentes, remontées vers le global

Le harnais a confirmé le correctif en rechargeant la nouvelle description du skill.

## 2. Un timer qui échoue toutes les nuits

```
qa-nightly.service : status=203/EXEC   (exécutable introuvable)
qa-nightly.timer   : actif, prochain déclenchement 04/08 à 03:30
qa-nightly.sh      : introuvable sur tout le disque
```

Un timer réveillait chaque nuit un service dont le script a disparu. Échec garanti, bruit permanent dans le journal.

**Timer désactiv

[assistant] 121 déclencheurs planifiés au total. Deux choses m'alertent : `jarvis-multi-bash` (le jumeau du service que j'ai corrigé) et 12 timers qui se déclenchent dans la même minute.

[assistant] `jarvis-multi-bash` est déjà sain (`oneshot`, `Restart=no`) — le jumeau avait été corrigé. Mais **39 timers JARVIS** tournent. Je calcule la charge réelle et cherche ce qui provoque les rafales.

[assistant] **58 timers sur 73 n'ont aucun étalement.** C'est ce qui provoque les rafales — 12 services démarrés en 90 secondes. Je corrige par drop-in, sans toucher aux fichiers d'origine.

[assistant] `jarvis-gemma-warmup.timer` est inactif. Je vérifie si c'est moi ou si c'était déjà le cas — je ne refais pas l'erreur de conclure trop vite.

[assistant] Ce n'est pas moi : le timer a été **arrêté à 19h22**, plus de deux heures avant mon drop-in de 21h37 — probablement pendant les manipulations GPU de la soirée, comme le timer `qwen-warm` qui a subi le même sort.

## Inventaire complet — 121 déclencheurs planifiés

| Emplacement | Nombre |
|---|---|
| Crontab `turbo` | 16 |
| Crontab `root` | 1 |
| `/etc/cron.d/` | 4 (tous standard : anacron, certbot, e2scrub, sysstat) |
| `/etc/crontab` | 4 |
| `cron.daily` / `weekly` / `monthly` | 8 / 2 / 1 |
| anacron | 5 |
| **Timers systemd user** | **65** (dont 39 JARVIS) |
| Timers systemd system | 20 |
| Tâches `at` | 0 |

## Ce que la mesure a révélé : les rafales

**58 timers sur 73 n'avaient aucun étalement.** Sans `RandomizedDelaySec`, ils convergent — d'où les 12 services démarrés entre 21:35:31 et 21:36:57, dans la même minute.

Cadences les plus lourdes :

```
jarvis-user-svc-prom     60/h   (chaque minute)
widget-s9-reverse        30/h
system-crash-guardian    30/h
prospection-prep         30/h
mirra-rundue             30/h
jarvis-session-snapshot  30/h
```

**Correctif appliqué** aux 13 timers les plus fréquents (≤ 5 min), par **drop-in** — les fichiers d'origine ne sont pas touchés :

```
jarvis-biblio-infinite    20s      jarvis-master-routing   1min 2s
jarvis-cluster-mount      27s      jarvis-multi-bash       1min 9s
jarvis-executor           34s      jarvis-session-snapshot 1min 16s
jarvis-gpu-cb             48s      jarvis-sync-config      1min 23s
jarvis-hub-healthcheck

[assistant] RAM à 89 % mais surtout **46 Gio de swap utilisés** — c'est le régime qui a déjà provoqué des gels ici. Deux processus `claude.exe` pèsent 21,6 Go à eux seuls. Je les identifie avant toute action.

[assistant] Ce ne sont **pas** des sessions Claude. Le nom trompe : ce sont deux `ugrep` orphelins.

[assistant] **Alerte résolue** : RAM 89 % → 50 %, swap 36 → 13 Gio. 23 Gio libérés.

Ceci mérite d'être mémorisé — le diagnostic évident était faux.

[assistant] Deux choses : l'alerte RAM est réglée, et le rapport de recherche est arrivé.

## L'alerte RAM — le coupable n'était pas celui qu'on croyait

| | Avant | Après |
|---|---|---|
| RAM | 89 % (39 Gio) | **50 % (23 Gio)** |
| Swap | 36 Gio | **13 Gio** |
| Disponible | 7,3 Gio | **23,3 Gio** |

Deux processus affichés `claude.exe` pesaient 19,8 Go de RSS et 22,9 Go de swap. Mais leur ligne de commande réelle disait :

```
ugrep -G --ignore-files --hidden -I --exclude-dir=.git …
```

Des **`ugrep` orphelins** — parent `systemd --user`, donc leur appelant était mort et personne n'attendait leur résultat. Ils balayaient le disque depuis 11 minutes en accumulant tout en mémoire. Un simple `SIGTERM` a suffi.

Le nom de processus mentait : `ps` affiche `comm`, ici un binaire renommé. Un diagnostic antérieur avait conclu « pic RAM → claude.exe (28 Go) » et s'était arrêté là — mauvais coupable, donc rien de corrigé, donc récidive. Mémorisé.

⚠️ **Ce qui reste inconnu : qui lance ces `ugrep` et pourquoi ils survivent à leur appelant.** Tant que la source n'est pas trouvée, ils reviendront.

## Le rapport de recherche — lecture honnête

**Sur les cinq volets demandés, deux seulement ont produit des faits vérifiés.** Les volets YouTube, indexation/RAG et déduplication n'ont rendu **aucune** affirmation ayant survécu à la vérification. Je ne te présente donc rien sur ces sujets : ils restent entiers.

### Ce qui est établi — trois régimes d'accès

**Réellement ouvert, sans clé ni compte :**


[assistant] Alerte GPU à 88 °C — je traite ça d'abord, ton message est trop déformé pour que j'agisse dessus sans risque de me tromper.

[assistant] GPU : rien de critique, j'y reviens en une ligne plus bas.

J'ai compris ta demande : **cloner la logique d'outils réels pour en créer des versions locales**, sans dépendre des originaux. C'est exactement le pattern de `mirra-local`. Je cherche d'abord ce qui existe déjà.

[assistant] Tout est là pour un clone. `notebooklm-cdp.py` pilote le **vrai** NotebookLM par navigateur — c'est justement ce que tu ne veux plus. Je vérifie les schémas avant de coder.

[assistant] Tout y est : FTS5 (BM25) + 10 206 vecteurs à 768 dimensions. Je construis le clone.

[assistant] Ollama ne répond pas sur les embeddings (GPU0 est à 92 % d'utilisation). Je conçois donc l'outil pour fonctionner **sans** eux — le vectoriel devient un bonus, pas une dépendance.

[assistant] Le clone fonctionne. `notebook-local.py` reproduit la logique de NotebookLM — sources d'abord, réponse **citée**, rien qui sorte de la machine.

```
❯ comment sauvegarder les bases postgres et sqlite du cluster
  20 résultats BM25 → 4 sources retenues
  [2] backup-sqlite-postgres-github-lfs
  [3] dump-postgres-compress
  ─────────────────────────────────────
  Pour SQLite … `sqlite3_backup` [2] … Pour PostgreSQL, `pg_dump -Fc`
  avec gzip [3] …
  [hub:18800] · 4 sources citées
```

| Ce que fait l'original | Ce que fait le clone |
|---|---|
| Tu déposes des sources | 10 430 fiches déjà indexées |
| Il cherche dedans | BM25 (FTS5) + cosinus sur 10 206 vecteurs |
| Il répond en citant | mêmes citations `[n]`, mêmes chemins de fichiers |
| Serveurs Google, quotas | **hub local, 0 token, rien ne sort** |

Deux choix de conception qui comptent :

**La voie sémantique est un bonus, pas une dépendance.** Ollama ne répond pas sur les embeddings en ce moment — l'outil le détecte, l'annonce, et tourne en BM25 seul. Un outil qui s'effondre parce qu'un backend tousse ne sert à rien.

**Fusion par rang réciproque (RRF)** plutôt que par score : BM25 et cosinus ne vivent pas sur la même échelle et ne sont pas comparables. Les rangs, si.

```bash
notebook-local.py "<question>"        # réponse sourcée
notebook-local.py --sources "<q>"     # sources seules
notebook-local.py --etat              # ce qui est indexé, ce qui répond
```

⚠️ **Limite honnête** : en mode BM25 seul, les sources [1] e

[assistant] Le choix du GPU compte : GPU2 a le ventilateur mort et GPU3 pilote l'affichage — y mettre un LLM a déjà causé des redémarrages ici. Je vérifie l'état réel avant de trancher.

[assistant] Cause trouvée : Ollama est **verrouillé sur GPU0 par UUID** et limité à `OLLAMA_MAX_LOADED_MODELS=1`. Gemma occupe la place, donc `nomic-embed` ne peut jamais se charger. Je vérifie les drop-ins existants avant d'ajouter le mien.

[assistant] Conflit trouvé : deux drop-ins se contredisent, et le `zz-` gagne parce qu'il trie en dernier.

| Drop-in | GPU | Modèles |
|---|---|---|
| `gpu-isolation.conf` | GPU1 + GPU3 | 2 |
| `zz-one-model-per-gpu.conf` | **GPU0** (saturé) | **1** |

L'intention d'origine — Ollama sur les GPU libres — a été silencieusement écrasée. Je la rétablis.

[assistant] Bascule réussie et mesurable :

| | Avant | Après |
|---|---|---|
| Embeddings | muets | **OK, 768 dim** |
| Mode | BM25 seul (dégradé) | **hybride BM25 + vectoriel** |
| GPU0 (saturé) | 9,3 Go | **5,6 Go** — 3,7 Go rendus |
| Recherche | 20 BM25 · 0 sémantique | **20 · 20** |

Les sources retournées se sont améliorées (`reference-bases-sql`, `ingest-github-base-sql3` remontent), même si un résultat ChromaDB hors sujet subsiste.

Pour ta demande d'audit et d'auto-amélioration, je commence par mesurer les manques réels de la bibliothèque plutôt que de les supposer.

[assistant] Audit sans appel : **la bibliothèque connaît 82 100 sujets et n'en a rédigé que 10 435 — soit 12,7 %.** Et le rythme s'effondre.

| Mois | Fiches | Par jour |
|---|---|---|
| Juillet | 10 042 | ~324 |
| Août (3 j) | 393 | **~131** |

Je cherche pourquoi le remplissage a ralenti de 60 %.

[assistant] **Voilà le manque.** Le daemon affiche :

```
Topics: pending=0 done=80977 | Fiches connaissance=10435
```

**80 977 sujets marqués « faits » pour 10 435 fiches réellement écrites.** La file est vide (`pending=0`) alors que 71 665 sujets n'ont aucune fiche. Le daemon croit avoir terminé — il ne produit plus que ~5 fiches par cycle sur des sujets nouvellement inventés.

Je confirme avant de conclure.

[assistant] 71 463 confirmés. Mais avant de crier au loup, je vérifie une hypothèse alternative : la table a un champ `kind` — ces sujets ont peut-être produit des **commandes** plutôt que des fiches.

[assistant] Ma conclusion précédente était trop large — je la corrige. Le détail par type change tout.