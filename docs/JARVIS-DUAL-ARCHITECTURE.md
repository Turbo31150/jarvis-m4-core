# JARVIS DUAL ORCHESTRATOR — architecture

Architecture **adaptée à la machine réelle** (1 GPU 4 Go, 15 Gi RAM), pas au
schéma théorique. Voir `JARVIS-AUTONOMOUS-AUDIT.md` pour les mesures.

## 1. Chaîne réelle

```
USER
 │
 ▼
bin/jarvis-dual  (CLI, un sous-commande = une responsabilité)
 │
 ▼
DualDispatcher ─── split() ──► micro-tâches TASK-001…N (checkpointées)
 │
 ├─ mode single / parallel / cascade / review / fallback / pipeline
 │
 ├──────────────┬──────────────┐
 ▼              ▼              │
Worker A      Worker B         │  heartbeat, retry classifié, états
 │              │              │
 ▼              ▼              │
LMStudioProvider  OllamaProvider   ← SEULE couche qui connaît une URL
 │              │
 ▼              ▼
:1234 (ou M6)  :11434
 └──────┬───────┘
        ▼
   aggregate()  first | best | merge | consensus
        ▼
   JobStore (checkpoint atomique)  +  Journal (JSONL)
        ▼
   board / replay / watchdog
```

## 2. Pourquoi deux backends et non deux modèles

Mesure : 4096 MiB de VRAM au total. Deux modèles simultanés sur un même
LM Studio ne tiennent pas, et un serveur mono-instance sérialise de toute façon
les requêtes. `config._assign_workers()` affecte donc A et B à des **providers
distincts**. C'est la seule façon d'obtenir un parallélisme mesurable ici — et
le benchmark le vérifie au lieu de l'affirmer.

## 3. Contrats

### Provider (`dual/providers.py`)

```
discover_models()  health()  model_status(m)  chat(...)  stream(...)  cancel(rid)
```

Quatre timeouts **distincts** (jamais un seul global) :

| Timeout | Défaut | Ce qu'il protège |
|---|---|---|
| `connect` | 5 s | serveur mort / port fermé |
| `first_token` | 60 s | modèle qui charge ou qui ne répond jamais |
| `idle` | 30 s | flux qui se tait en cours de route |
| `request` | 300 s | garde-fou global |

Statuts renvoyés, jamais approximés :
`success`, `empty_response`, `model_unavailable`, `server_unavailable`,
`timeout_connect`, `timeout_first_token`, `timeout_idle`, `timeout_request`,
`http_error`, `cancelled`.

### Métriques

`ttft_ms`, `duration_ms`, `prompt_tokens`, `completion_tokens`, `total_tokens`,
`tokens_per_second`. **Toute valeur que l'API ne fournit pas vaut `UNAVAILABLE`**
— jamais 0, jamais une estimation. Quand seuls les chunks SSE sont comptables
(LM Studio sans `usage`), le champ s'appelle `chunks_per_second` et
`tokens_per_second` reste `UNAVAILABLE`.

### Worker (`dual/worker.py`)

États : `STARTING READY RUNNING WAITING COMPLETED FAILED TIMEOUT RECOVERING STOPPED`.

Retry **classifié**, pas aveugle :

| Erreur | Décision |
|---|---|
| `server_unavailable`, `timeout_*`, `empty_response`, `http_error` | retry avec backoff `1.5^n` |
| `model_unavailable`, `cancelled` | **pas de retry** — relancer ne changerait rien |

Heartbeat : `last_activity`, `last_token_at`, `tokens`, `current_task`. Un worker
en `RUNNING` dont `last_activity` dépasse `idle` est classé `TIMEOUT` par le
watchdog — **jamais `OK`**.

### Micro-tâches

`DualDispatcher.split()` ne découpe que sur des marqueurs **explicites** (lignes
numérotées ou à puces, ≥ 2). Sans marqueur : une seule tâche. Un découpage
inventé casse le sens plus souvent qu'il n'aide.

### Checkpoint (`dual/checkpoint.py`)

Écriture atomique (`tmp` + `os.replace`) : un kill au milieu d'un write ne
corrompt pas l'état. Chaque tâche porte `input_hash`, `output_hash`, `attempts`,
`worker`, `status`. `resume=True` ne rejoue que les tâches ≠ `SUCCESS`.

### Journal (`dual/journal.py`)

Un JSONL par job. Horodatage mural **et** monotone (`perf_counter`) — c'est le
temps monotone qui rend la preuve de parallélisme exploitable.

## 4. Modes

| Mode | Comportement | Dégradation si 1 worker |
|---|---|---|
| `single` | un worker | — |
| `parallel` | A et B sur la **même** tâche, simultanément | → `single`, tracé `FALLBACK` |
| `fallback` | A, puis B seulement si A échoue | → `single` |
| `cascade` | A produit → B reprend, checkpoint entre étapes | → `single` |
| `review` | A produit, B critique, A corrige | → `single` |
| `pipeline` | tâches réparties en continu, sans barrière | → `single` |

## 5. Verdict de parallélisme

`benchmark.dual()` calcule :

- `overlap_s` = intersection réelle des deux fenêtres d'exécution ;
- `token_switches` = alternances A↔B dans le flux de tokens ;
- `parallel_efficiency` = `(somme_solo − wall) / (somme_solo − plus_long)`, borné [0,1].

| Verdict | Condition |
|---|---|
| `PASS` | overlap > 0,15 s **et** ≥ 2 alternances de tokens |
| `PARTIAL` | fenêtres chevauchées mais tokens non entrelacés |
| `FAILED` | exécution sérialisée, ou un worker en échec |
| `BLOCKED` | moins de 2 workers |

## 6. Sécurité

- Aucun secret dans le code ni dans les logs ; les prompts journalisés sont
  tronqués à 200 caractères dans le checkpoint.
- `watchdog --act` ne **tue rien** : il marque le job `RECOVERABLE`. La
  destruction n'est jamais automatique.
- Aucun fichier existant du dépôt n'est modifié par ce module.

## 7. Ce que le système sait répondre

| Question | Commande |
|---|---|
| Quel worker travaille ? | `jarvis-dual board` |
| Quel modèle, quel backend ? | `jarvis-dual workers` |
| Quel débit, quel TTFT ? | `jarvis-dual benchmark` |
| Où en est le job, quelle étape ? | `jarvis-dual jobs` |
| Que s'est-il passé exactement ? | `jarvis-dual replay <job_id>` |
| Pourquoi ça bloque ? | `jarvis-dual doctor` (CAUSE/IMPACT/ACTION) |
| Comment reprendre ? | `jarvis-dual recover <job_id>` |
