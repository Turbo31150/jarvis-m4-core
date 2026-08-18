[assistant] Lecture SQL terminée. Je bascule le démarrage sur M6 — j'invoque le skill dédié.

[user] Base directory for this skill: /home/turbo/.claude/skills/run-m6-share

# run-m6-share — M6 en câble direct comme nœud de compute partagé

M6 est un nœud du cluster raccordé à **M1 par câble Ethernet direct** (partage réseau
GNOME/ICS : M1 = passerelle `enxf8e43b9b67d4` 10.42.0.1/24, M6 = `enp3s0` **10.42.0.230**).
Ce n'est pas une GUI : le « pilotage » = un **driver bash** qui vérifie la connectivité,
les endpoints LLM, l'enregistrement dans le routeur, et fait une inférence réelle.

Chemins relatifs à `/home/turbo/jarvis/`. Le driver vit dans le dossier du skill.

## Piège central (à connaître avant tout)
**L'ICMP est filtré sur M6** → `ping 10.42.0.230` échoue *à tort*. M6 est joignable :
vérifier via **ARP** (`ip neigh`) ou **TCP** (`/dev/tcp/.../22`), jamais via ping.

## Run (chemin agent) — le driver

```bash
cd /home/turbo/jarvis/.claude/skills/run-m6-share
./driver.sh check     # connectivité + endpoints + état config (lecture seule)
./driver.sh smoke     # inférence réelle : Ollama M6 + hub :18800
./driver.sh register  # (ré)enregistre les providers ollama-m6 + lmstudio-m6 (backup auto) + recharge le hub
./driver.sh all       # check + register + smoke
```

`./driver.sh check` attendu (tout vert) :
```
== Lien câble direct → M6 (10.42.0.230)  [ICMP filtré : on teste ARP+TCP, pas ping] ==
  ✓ ARP REACHABLE (44:8a:5b:a2:35:94)
  ✓ SSH ok (alias 'm6' → M6)
== Backends LLM joignables depuis M1 ==
  ✓ port 1234 ouvert   ✓ port 11434 ouvert   ✓ port 22 ouvert
  ✓ LM Studi

[assistant] Lecture terminée. État réel (tout sondé, rien de supposé) :

## SQL — SQLite
| Base | Taille | Tables | Volumétrie clé |
|---|---|---|---|
| `jarvis_master.db` | **2,0 Go** | 73 | `tasks` **2 139 420** · `agent_index` **310** |
| `logs/jarvis_logs.db` | 584 K | 13 | `protocole_runs` **33** |
| `cowork_engine.db` | 39 M | 3 | — |
| `data/etoile.db` | 2,1 M | 13 | — |

⚠️ `protocole_runs` n'existe **que** dans `jarvis_logs.db`, pas dans master.

## SQL — PostgreSQL (2 containers)
| Container | User/DB | Contenu |
|---|---|---|
| `jarvis_prod_postgres` | jarvis/jarvis | **1 411 Mo** (+ `jarvis_backups` 7,6 Mo) |
| `jv-infra-biblio-db` | cmduser/cmdlib | `commands` **23 117** · `holding_index` **40 573** · `library_series` 205 |

## GitHub — Turbo31150
100 repos (89 privés, 1,9 Go). Poussés aujourd'hui : `jarvis-n8n-workflows`, `labo-bibliotheque-centrale`, `transcription-portable`. Local `jarvis-core` : **532 fichiers modifiés non commités**, HEAD `6ab555e4` (04/08).

## n8n — ⚠️ anomalie majeure
La base lue par défaut (`~/.n8n/database.sqlite`, 99 Mo) **date du 23/07 — périmée**. La vraie est le volume Docker (146 Mo, maj 04:56) :

| 24 h | Nombre |
|---|---|
| **error** | **1 029** |
| success | 38 |

72 workflows, 70 actifs. Top erreurs : `Self-Healing Watchdog` ×267, `GPU Monitor & Thermal Alert` ×107, `Trading Watchdog` ×53, `GPU Thermal Guard` ×53. **96 % d'échec** — ces watchdogs bouclent sur l'incident thermique.

## Bibliothèque vivante
55 720 blocs (maj 05:04) — comman

[user] Base directory for this skill: /home/turbo/.claude/plugins/cache/claude-plugins-official/superpowers/5.1.0/skills/verification-before-completion

# Verification Before Completion

## Overview

Claiming work is complete without verification is dishonesty, not efficiency.

**Core principle:** Evidence before claims, always.

**Violating the letter of this rule is violating the spirit of this rule.**

## The Iron Law

```
NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE
```

If you haven't run the verification command in this message, you cannot claim it passes.

## The Gate Function

```
BEFORE claiming any status or expressing satisfaction:

1. IDENTIFY: What command proves this claim?
2. RUN: Execute the FULL command (fresh, complete)
3. READ: Full output, check exit code, count failures
4. VERIFY: Does output confirm the claim?
   - If NO: State actual status with evidence
   - If YES: State claim WITH evidence
5. ONLY THEN: Make the claim

Skip any step = lying, not verifying
```

## Common Failures

| Claim | Requires | Not Sufficient |
|-------|----------|----------------|
| Tests pass | Test command output: 0 failures | Previous run, "should pass" |
| Linter clean | Linter output: 0 errors | Partial check, extrapolation |
| Build succeeds | Build command: exit 0 | Linter passing, logs look good |
| Bug fixed | Test original symptom: passes | Code changed, assumed fixed |
| Regression test works | Red-green cycle verified | Test passes once |
| Agent completed | V

[assistant] Je re-vérifie mes affirmations avec des commandes fraîches, plus l'alerte `FAILED_SVC:1` qui vient d'arriver.

[assistant] Correction nécessaire : **M6 répond** — `HTTP=200` en 29 s. Mon affirmation précédente était fausse. Je qualifie la vraie limite.

[assistant] Vérification faite. Une de mes affirmations était fausse, deux étaient imprécises.

## Corrections

**❌ « M6 : aucune réponse en 90 s »** — faux tel quel. Mesure fraîche :

| Test M6 | Résultat |
|---|---|
| `qwen2.5:1.5b` (déjà chargé) | **HTTP 200**, rc=0, **29,1 s** pour 20 tokens |
| `gemma3:4b` (cold-load) | rc=**28** (timeout) après **275 s**, aucune réponse |

Formulation exacte : **M6 sert les modèles déjà résidents, à ~0,8 token/s en 100 % CPU ; il ne parvient pas à charger un nouveau modèle** (le GPU n'est pas utilisé pour l'inférence — `ollama ps` affiche `100% CPU`).

**⚠️ « hub :18800 ✅ actif »** — incomplet. `/v1/models` renvoie 200, mais l'inférence réelle :

```
/v1/chat/completions → HTTP=000 T=115.0s   (aucune réponse)
```

Le hub est vivant mais **ne produit aucune complétion** — exactement le piège « /health vert qui ment » de la mémoire projet. Je n'aurais pas dû le compter vert.

**⚠️ Service en échec** (alerte `FAILED_SVC:1`, non traitée dans mon rapport) :

```
× jarvis-lms-qwen-warm.service — failed (Result: exit-code, status=1)
  depuis 05:34:39, TriggeredBy jarvis-lms-qwen-warm.timer
  journal: "etat detecte ctx=8192 parallel=4" → "etat incorrect -> rechargement" → unload
```
LM Studio M1 `:1234` répond pourtant **200 en 2,5 ms**. C'est le flap connu (concat TTL + force-reload) : le service tue une instance saine en boucle sur timer.

## Ce qui reste confirmé, avec preuve

| Claim | Preuve |
|---|---|
| SQLite `tasks` 2 139 420 · `agent_index` 310 |

[user] lance toiute les tache sur ap planning d'un coup en attente non effectuer bibliotheque vivante domiçno relance lme roulo compresseur

[assistant] Rouleau compresseur — j'exécute. D'abord débloquer LMS, puis mesurer la file avant de tout lâcher (M1 est à load 17,5 sans refroidissement, je ne lance pas à l'aveugle).

[assistant] Les deux fichiers du Bureau sont du contenu Perplexity halluciné (encodage cassé, `/perf`, `/benchmark`, `/optimize`, `/bg` n'existent pas, modèles `opus-4-8` inventés). Je n'exécute pas `optimize-claude-code.sh.sh`. J'y reviens après — je lance d'abord le rouleau compresseur.

[assistant] Rouleau compresseur passé. Bilan mesuré :

## Services lancés — 8/8 terminés avec succès (`Result=success`, exit 0)

| Service | Effet réel constaté |
|---|---|
| `jarvis-task-auto` | recovery : **stuck→pending=3**, **error→retry=4** |
| `jarvis-domino-autopilot` | **25 séries domino / 125 actions granulaires** accomplies |
| `dominos-batch` | terminé |
| `jarvis-planning-autogen` + `task-autogen` | file régénérée |
| `jarvis-sync-biblio` | réplication biblio vers les nœuds, terminée |
| `biblio-doctor` | terminé |
| `jarvis-executor` | terminé |

## 5 services longs toujours en cours (ils travaillent, ils ne sont pas plantés)

| Service | CPU consommé |
|---|---|
| `jarvis-journee` | **1 299 s** |
| `biblio-rebuild` | **177 s** |
| `jarvis-plan-refresh` | 161 s |
| `biblio-vectorize` | 0,5 s |
| `jarvis-prod-loop` | 0,1 s |

## File de tâches — avant → après

| Statut | Avant | Après |
|---|---|---|
| pending | 180 | **207** |
| to_validate | 164 | 167 |
| running | 6 | 3 |
| error | **4** | **1** |
| done | 2 139 396 | **2 139 524** (+128) |

Les erreurs sont retombées de 4 à 1 et 128 tâches sont passées en `done`. Le `pending` **monte** parce que l'autogen produit plus vite que la file ne se vide — c'est le comportement attendu du cycle, pas un blocage.

## LMS — relance faite, chargement en cours

Timer tueur neutralisé (`jarvis-lms-qwen-warm.timer` stoppé + désactivé, service `reset-failed`). Conséquence immédiate :

```
loading      qwen/qwen3.5-9b      ← se charge enfi

[assistant] Le rapport annonce un sans-faute (faithfulness 1.0, citation 1.0, `passed: True`) — mais **7 ms de latence moyenne**, c'est trop rapide pour une inférence LLM. Je vérifie ce que ce banc mesure réellement.

[assistant] Preuve trouvée. Je la vérifie empiriquement sans toucher aux fichiers du projet.

[assistant] J'ai audité le pack. Le contenu documentaire est solide et honnête, mais **la « priorité n°1 » qu'il déclare résolue ne l'est pas** — et c'est démontrable.

## Le pack (28 fichiers, 512 K)

Structure cohérente : `00-INDEX` → `06-DEPLOIEMENT-ROLLBACK`, plus dossier AI Act, audit client, offre MRR. La règle transverse est saine : « aucun chiffre non prouvé », avec exclusion explicite des `928 agents`, `168 TFLOPS`, `+340 %`. Ça correspond à ce qui est en mémoire projet.

## Le banc qualité — le rapport ment sur ce qu'il mesure

`data/qa_bench_report.json` (31/07) annonce :

```
total_questions: 200 · faithfulness: 1.0 · citation_match: 1.0
avg_latency_ms: 6.99 · passed: True
```

Les 7 ms m'ont alerté. Vérification dans le code :

**1. Aucun LLM n'est jamais appelé.** `rag_engine.py:309` appelle Ollama `/api/generate` avec `timeout=0.5` — une génération LLM ne rend jamais la main en 500 ms. Au premier échec, `_ollama_offline = True` (variable **de classe**) : tout le run bascule définitivement sur le fallback. Confirmé à l'exécution : `Ollama considéré offline par le moteur : True`.

**2. Le fallback copie le chunk.** `rag_engine.py:319-327` : il prend les 3 premières phrases du chunk top-1 et les préfixe de `[chunk_id]`.

**3. Les métriques notent alors la copie contre son original.** `_evaluate_faithfulness` vérifie que les mots de la réponse sont dans le contexte ; `_evaluate_citation_match` vérifie que la réponse contient les mots du chunk top-1. La réponse *étant* le chunk

[assistant] Je fais du TDD : test rouge d'abord, sur le cas `qa_002` que le banc actuel note 1,0.

[assistant] 57 tests passent, 1 échoue — précisément celui qui verrouillait la fausse réussite. Je le corrige pour qu'il teste la cohérence du rapport au lieu d'exiger un succès inatteignable.

[assistant] Correctif n°1 livré. Vérifié : **59/59 tests passent**, banc exécuté sur les 200 questions, code de sortie **1** (FAILED) confirmé hors pipe.

## Ce qui a changé

**`qa_bench_real.py`** — deux fonctions de scoring, plus leur intégration :

| Fonction | Rôle |
|---|---|
| `evaluate_answer_correctness(answer, ground_truth)` | F1 lexical (hors mots-outils, préfixe `[chunk_id]` neutralisé) + rappel des faits clés (codes `E10`/`F04`, quantités) — moyenne des deux |
| `evaluate_retrieval_recall(served, expected)` | le chunk désigné par le gold set est-il dans le top-k servi |

`ground_truth_answer` est désormais lu à chaque question. `passed` inclut les deux nouveaux critères (seuils 0,75 et 0,90).

**`tests/test_answer_correctness.py`** (nouveau, 9 tests) — écrit **avant** l'implémentation, rouge sur `ImportError`, puis vert. Il verrouille notamment que la réponse `F04`/sèche-linge face à la question `E10`/lave-linge score **< 0,5**.

**`tests/test_qa_bench.py`** — `assertTrue(results["passed"])` remplacé. Ce test exigeait un succès inconditionnel : il **verrouillait la fausse réussite**. Il vérifie maintenant que `passed` égale exactement la conjonction des sous-critères, plus un test que `answer_correctness` est strictement entre 0 et 1 (ni ignoré, ni tautologique).

## Avant / après sur les mêmes 200 questions

| Métrique | Avant (31/07) | Après |
|---|---|---|
| faithfulness | 1.0 ✅ | 1.0 ✅ |
| citation_match | 1.0 ✅ | 1.0 ✅ |
| **answer_correctness** | *non mesuré* | **0,7401

[assistant] `os` est déjà importé et `_generate_answer` n'a aucun usage externe. J'implémente.

[assistant] Toujours en repli, mais pour une raison différente — 15,3 s, exactement mon timeout d'embedding. Je vérifie qui bloque.

[assistant] Découverte décisive : la génération **fonctionne** (61,8 s), c'est l'**embedding** qui ne répond pas du tout (HTTP 000 après 85 s). Or un échec d'embedding désactive la génération. Je casse ce couplage.

[assistant] Erreur de ma part : j'ai inséré la property **au milieu de `__init__`**, laissant `self.vector_store = ...` en code mort. Je répare.

[assistant] Le banc tourne en arrière-plan (200 vraies générations, ~25 min). Voici l'état pendant qu'il travaille.

## Correctif n°2 livré — 3 causes racines, pas 1

Je pensais n'avoir qu'un timeout à corriger. Il y en avait trois, chacune suffisante à elle seule pour garantir le repli :

| # | Défaut | Preuve |
|---|---|---|
| 1 | Timeout de génération à **0,5 s** | aucune inférence ne rend la main si vite ; mesuré 61,8 s sur M1 chargé |
| 2 | Modèle par défaut **`qwen3.5` inexistant** | `curl` → `{"error":"model 'qwen3.5' not found"}` HTTP **404** |
| 3 | **Un échec d'embedding désactivait la génération** | `_ollama_offline` unique, en variable de *classe* |

La 3ᵉ était la plus vicieuse. Mesure sur OL1 : l'embedder `nomic-embed-text` **ne répond pas du tout** (HTTP 000 après 85 s) alors que `gemma3:4b` **génère très bien**. Un flag commun faisait tomber un service parfaitement fonctionnel avec celui qui était en panne.

**Corrections** dans `src/rag_engine.py` : timeouts configurables (génération 120 s, embedding 15 s), modèle par défaut `gemma3:4b` surchargeable par `ASSISTANT_LLM_MODEL`, drapeaux `_embed_offline` / `_llm_offline` séparés et par instance, compteurs `llm_calls_ok` / `fallback_count`, et `query()` déclare désormais son `backend`.

Dans `qa_bench_real.py` : `fallback_rate` et `llm_model` au rapport, `llm_backend_pass` en critère bloquant — **tout repli ferme la porte**, quels que soient les autres scores.

## Ce que la vraie inférence révèle

Même question `qa_002`, mê

[assistant] Le banc tourne encore (PID 1029448) — `tail` bufferise, d'où la sortie vide. Je mesure la progression directement dans la table d'audit.

[assistant] Le banc n'a pas fini — mais la mesure confirme qu'il fait de **vraies générations** cette fois.

[assistant] Verdict pas encore disponible — le banc en est à **15 questions sur 200**. Voici pourquoi, mesuré :

## Le run est bien en vraie inférence

| | |
|---|---|
| Questions traitées | **15 / 200** |
| Latence médiane | **6,5 s** |
| Latence max | **79,0 s** |

Ces latences sont la signature d'une génération réelle. Avant les correctifs, c'était **7 ms** — la recopie de chunk. Le repli est bien mort.

## Pourquoi c'est si lent

Le run a démarré vers 06:05, mais la **première question n'est tombée qu'à 06:28** : ~23 minutes consommées par `ingest_gold_set_corpus()`, qui demande un embedding pour chacun des 200 chunks. Or `nomic-embed-text` ne répond pas sur OL1 — chaque appel attend son timeout de 15 s avant de basculer.

Depuis 06:28, le rythme est d'environ **20 s par question**. Reste ~185 questions → **fin estimée vers 07:35**, soit ~1 h.

M1 est à load **18,23** et **76,5 °C** — le refroidissement absent plafonne le débit. Sur une machine saine, gemma3:4b répondrait en 1–2 s, pas 6,5.

## Un détail à corriger que j'ai introduit

Le timeout d'embedding à 15 s est payé **200 fois** à l'ingestion alors que le premier échec suffit à trancher. Un test de disponibilité unique en tête de run éliminerait ces 23 minutes. Je ne touche à rien pendant que le banc tourne.

## L'alerte `FAILED_SVC` — ce n'est pas une régression

`jarvis-lms-qwen-warm.service` est de nouveau `failed` (06:31:34), **alors que j'avais bien neutralisé son timer** :

```
timer enabled: disabled
timer actif:   inac

[assistant] Rafale. Je vérifie d'abord une hypothèse : les 23 min d'ingestion pourraient être **ma régression**.

[assistant] **Verdict : FAILED** — et il est enfin informatif.

| Métrique | Avant correctifs | Maintenant | Seuil |
|---|---|---|---|
| faithfulness | 1.0000 | **0,9775** | 0,95 ✅ |
| citation_match | 1.0000 | **0,9470** | 0,90 ✅ |
| answer_correctness | *non mesuré* | **0,7301** | 0,75 ❌ |
| retrieval_recall | *non mesuré* | **0,7750** | 0,90 ❌ |
| **fallback_rate** | *invisible* | **0,8150** | 0,0 ❌ |
| latence moyenne | 6,99 ms | **1 827 ms** | — |

Faithfulness et citation ne sont **plus à 1,0** : elles ne l'étaient que parce que le repli recopiait les chunks. Dès qu'un vrai LLM répond, elles descendent à leur valeur réelle.

## Le chiffre qui commande la suite : 81,5 % de repli

Seules **37 questions sur 200** ont eu une vraie génération. Cause : `_llm_offline` bascule au **premier** échec et ne se réarme jamais. Sous une charge à 18, un timeout ponctuel suffit à condamner les 163 questions suivantes. C'est un disjoncteur sans réarmement. Je corrige — TDD, comme les précédents.

[assistant] Banc relancé en fond. Bilan de la rafale pendant qu'il tourne.

## Le verdict, et ce qu'il a révélé

Le `fallback_rate` que j'ai ajouté au correctif n°2 a immédiatement payé : il a exposé un défaut que personne ne voyait. **81,5 % des réponses passaient encore par le repli** — seules 37 questions sur 200 avaient une vraie génération. Cause : `_llm_offline` basculait au premier échec et ne se réarmait jamais. Un unique timeout sous charge condamnait tout le reste du run.

Sans cette métrique, le rapport aurait affiché des scores plausibles issus à 81 % de copier-coller de chunks.

## Correctif n°3 — disjoncteur réarmable

`MAX_CONSECUTIVE_LLM_FAILURES = 3`, avec `_note_llm_failure()` / `_note_llm_success()` : le circuit ne s'ouvre qu'après 3 échecs **consécutifs**, et toute réussite efface l'ardoise. J'ai aussi corrigé un trou au passage — une réponse vide ou un statut non-200 tombait dans le silence sans être compté comme échec.

3 tests écrits rouges puis verts. **18/18** sur le moteur et l'honnêteté backend.

## Deux choses à rectifier dans ce que je t'ai dit

**Mon hypothèse sur les 23 minutes d'ingestion était fausse.** J'ai vérifié `ingest_gold_set_corpus()` : il n'instancie qu'**un seul** `RAGEngine` (ligne 2030), donc le premier échec d'embedding suffit à basculer les 199 chunks suivants. Le passage classe→instance n'a pas créé la régression que je soupçonnais. Le temps est ailleurs, je n'ai pas encore la cause.

**Le `mask` du service a échoué**, et c'est normal : `ja

[assistant] Le `fallback_rate` a **empiré** : 0,9950 contre 0,8150. Je vérifie — j'ai peut-être pollué ma propre mesure.

[assistant] Cause trouvée, et elle est nette : **GPU 2 est en `Prohibited`** (ventilo mort) mais son UUID figure quand même dans le `CUDA_VISIBLE_DEVICES` d'Ollama — l'énumération CUDA bute dessus et tout le survey tombe.

[assistant] GPU 2 est **repassé en `Default`** en 30 secondes — quelque chose le bascule dynamiquement (garde thermique, ventilo mort). Je teste si Ollama est rétabli.

[assistant] Ollama est rétabli (HTTP 200 en 8 s) — la panne CUDA était **transitoire**. Ce qui invalide une conclusion que je viens de te donner.

[assistant] Appliqué. Banc de référence relancé, **et je ne touche plus au GPU pendant qu'il tourne** — c'est précisément ce que j'ai mal fait au tour précédent.

## Correction : ma conclusion précédente était fausse

J'ai annoncé que le `fallback_rate` de 0,9950 montrait un problème avec le disjoncteur. **C'est faux, et j'ai deux torts** :

**1. Ollama était en panne pendant la mesure.**
```
CUDA-capable device(s) is/are busy or unavailable   HTTP=500
```
Cause : **GPU 2 en `compute_mode Prohibited`** (ventilo mort). Son UUID figure dans le `CUDA_VISIBLE_DEVICES` d'Ollama, et une carte prohibée dans la liste visible fait échouer toute l'énumération CUDA — pas seulement ce GPU. Le run a donc mesuré une infrastructure morte, pas mon code.

**2. J'ai pollué ma propre mesure.** J'ai lancé un cold-load de `nomic-embed-text` **en parallèle** du banc, sur le même GPU. Erreur de méthode : on ne diagnostique pas sur la ressource qu'on est en train de mesurer.

Le run 0,9950 est archivé sous `qa_bench_report.INVALIDE-panne-cuda.json`. Ollama regénère depuis (HTTP 200 en 8 s), la panne était transitoire — GPU 2 est repassé en `Default` tout seul en 30 secondes, quelque chose le bascule dynamiquement.

## Ce que le diagnostic a quand même rapporté

**L'embedder fonctionne.** Je le croyais mort (HTTP 000). Avec une fenêtre plus large :

```
nomic-embed-text → HTTP 200 en 35 s
```

Il chargeait, simplement — et mon timeout de 15 s raccrochait avant. C'est pour ça que toute la recherche vectorielle to