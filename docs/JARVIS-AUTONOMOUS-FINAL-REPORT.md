# JARVIS DUAL — rapport de chantier

**Date** : 13/08/2026 · **Dépôt** : `~/jarvis` (`jarvis-m4-core`) ·
**Branche** : `refonte-prof-ia-symbiose` · **8 commits locaux, aucun push.**

Règle appliquée partout : un état n'est déclaré `WORKING` que si une commande
réelle l'a démontré. Sinon `PARTIAL`, `BLOCKED` ou `NOT_AVAILABLE`.

---

## 1. Tableau d'état final

| Fonction | État | Testé | Preuve |
|---|---|---|---|
| LM Studio (adapter) | WORKING | oui | `discover` → 4 modèles listés, 1 seul chargeable |
| Ollama (adapter) | WORKING | oui | `gemma3:4b` 5,8 tok/s, ttft 2,3 s à chaud |
| agy / Antigravity CLI | WORKING | oui | `agy -p` → réponse en 7,9 s, 15 modèles |
| Modèle A (`gemini-3.7-flash-low` via agy) | WORKING | oui | ttft 8,15 s, 596 car. |
| Modèle B (`gemma3:4b` via Ollama) | WORKING | oui | ttft 2,34 s, 5,8 tok/s, 501 car. |
| Worker A | WORKING | oui | heartbeat + `WORKER_COMPLETED` au journal |
| Worker B | WORKING | oui | idem |
| **DUAL réel** | **WORKING** | **oui** | wall 19,5 s vs somme solo 28,4 s ; overlap 8,89 s ; efficacité **1.0** ; 2 alternances de tokens |
| Streaming | WORKING | oui | `TOKEN[10..100]` horodatés dans la timeline |
| Métriques | WORKING | oui | ttft/durée/tok-s réels ; `UNAVAILABLE` quand l'API ne les fournit pas |
| Dispatcher (6 modes) | PARTIAL | `single`, `parallel` testés en réel ; `cascade`/`review`/`fallback`/`pipeline` couverts par les tests unitaires seulement |
| Micro-tâches | WORKING | oui | 3 tâches découpées, `TASK-001…003` |
| Checkpoints | WORKING | oui | état sur disque après `kill -9` : 2/3 SUCCESS, 1 RUNNING |
| Recovery | WORKING | oui | `recover` rejoue **uniquement** TASK-003 → SUCCESS |
| Watchdog | WORKING | oui | job figé détecté (age 21 s) → marqué RECOVERABLE |
| Fallback | PARTIAL | tests unitaires (dégradation `parallel`→`single` vérifiée en réel) |
| Board | WORKING | oui | rendu alimenté par le journal, sans saisie |
| Replay | WORKING | oui | 22 événements reconstitués à la milliseconde |
| Diagnostic (`doctor`) | WORKING | oui | a trouvé le modèle fantôme avant tout le reste ; état final **OK=17 WARN=1 ERROR=0** (le WARN est la VRAM, contrainte physique) |
| Tests | WORKING | oui | 27/27 en 5,8 s |
| Documentation | WORKING | — | audit, architecture, guide, agy, ce rapport |
| Worker OpenClaw | BLOCKED | non | gateway vivant (`:18789` → `{"ok":true}`), protocole d'inférence non validé |
| Worker Claude Code | NOT_AVAILABLE | non | volontaire : facturerait des tokens à chaque tâche |
| MCP dans le dépôt | NOT_AVAILABLE | — | 1 seul MCP en global (`browseros`), aucun `.mcp.json` ici |
| GPU 0 → A / GPU 1 → B | NOT_AVAILABLE | — | **un seul GPU** de 4 Go |

---

## 2. Preuve de parallélisme (mesure brute)

```
    0.0003  worker_a  START
    0.0009  worker_b  START
    2.3425  worker_b  FIRST_TOKEN
    3.8621  worker_b  TOKEN[10]
    6.0117  worker_b  TOKEN[20]
    7.6637  worker_b  TOKEN[30]
    8.1487  worker_a  FIRST_TOKEN     ← A génère pendant que B génère
    8.8894  worker_a  END
    9.5524  worker_b  TOKEN[40]       ← B poursuit
   19.5370  worker_b  END
  wall=19.537s  somme_solo=28.425s  overlap=8.889s  efficacité=1.0
  DUAL_PARALLEL = PASS
```

Ce n'est pas `A START / A END / B START / B END` : les deux fenêtres se
recouvrent et les tokens alternent. Le mur (19,5 s) est inférieur à la somme
des solos (28,4 s) de la durée exacte du plus court — efficacité 1.0.

---

## 3. Problèmes rencontrés et réparés

### P1 — Modèle fantôme (critique)

`qwen/qwen3.5-9b` figure dans `/v1/models` et échoue au chargement
(`HTTP 400 — Error loading model`). Trouvé par `doctor` dès le premier
diagnostic.

**Trois stratégies, dans l'ordre :**
1. sonder chaque modèle individuellement → LM Studio local n'en chargeait
   aucun (`TimeoutError` même en requête directe : serveur zombie) ;
2. basculer sur M6 (`10.42.0.1`) → `deepseek-r1` a répondu (ttft 25,9 s), mais
   au test suivant M6 échouait à son tour : il ne tient **qu'un modèle à la
   fois** et la sonde en avait demandé plusieurs ;
3. rendre la sélection anti-fantôme permanente : `discover --probe` exige une
   **inférence réussie** pour retenir un modèle, et `resolve()` fait primer la
   config vérifiée sur toute redécouverte.

**Résolu.** Effet de bord corrigé au passage : le CLI resondait à chaque
commande et réélisait le modèle fantôme par simple préférence de nom, annulant
le travail de vérification.

### P2 — Verdict de parallélisme trop grossier

Premier critère : `overlap > 0,15 s ET tokens entrelacés`. Il classait `FAILED`
un dual pourtant fonctionnel — overlap 40,7 s, efficacité 1.0, mais zéro token
entrelacé parce que `gemma3` mettait 55 s à charger pendant que A générait.

**Correction** : deux propriétés mesurées séparément —
*exécution concurrente* (overlap + efficacité, la définition du dual) et
*génération simultanée* (tokens entrelacés, cas particulier). Le seuil n'a pas
été relâché : un second critère a été ajouté, et les deux sont rapportés.

### P3 — Saturation machine par mes propres tests

Lancer plusieurs inférences en parallèle sur 12 cœurs / 15 Gi faisait échouer
`agy models` (timeout 120 s) et `gemma3` (`timeout_first_token`). Séquencer les
tests a suffi. Le système a correctement rapporté ces échecs plutôt que de les
masquer — c'était le comportement attendu.

---

## 4. Contrainte matérielle, et l'architecture qui en découle

| Ressource | Mesure |
|---|---|
| GPU | 1× RTX 3050 Laptop, **4096 MiB** |
| RAM | 15 Gi, 7,6 Gi de swap déjà consommés |
| CPU | 12 cœurs |

Deux modèles locaux simultanés sont impossibles. Le dual retenu est donc
**cloud + local** :

```
worker_a → agy → gemini-3.7-flash-low   (aucune VRAM, aucun CPU local)
worker_b → ollama → gemma3:4b            (le seul modèle local fiable)
```

Performances comparées, mesurées :

| Worker | TTFT | Débit | Durée (100 tokens) |
|---|---|---|---|
| `agy/gemini-3.7-flash-low` | 6,3–8,2 s | non fourni par le CLI | ~8 s |
| `ollama/gemma3:4b` (chaud) | 2,3 s | 5,8 tok/s | 19,5 s |
| `ollama/gemma3:4b` (froid) | 90,9 s | 5,0 tok/s | 111 s |
| `lmstudio/qwen2.5-coder-14b` | 13,9 s | 3,0 tok/s | 40,7 s |

---

## 5. Ce qui a été conservé, ajouté, et jamais touché

**Conservé, aucune modification** : `multiagent/jarvis-router.py`,
`scripts/model_router.sh`, `scripts/dashboard.py`, `watchdog_critical.sh`,
`m1-failover-watchdog.sh`, `bench_massive.sh`, `cli/*`, `bin/j`, ainsi que les
78 fichiers déjà modifiés sur la branche.

**Ajouté** : `dual/` (10 modules), `bin/jarvis-dual`, `dual/tests/`, `docs/`.

**Supprimé** : rien.

---

## 6. Ce qui reste bloqué

| Sujet | État | Pourquoi |
|---|---|---|
| Worker OpenClaw | BLOCKED | gateway vivant mais protocole d'inférence non validé ; coder à l'aveugle produirait un worker qui ment sur son état |
| Optimisation des agents | NON FAIT | les 59 agents sont dans `~/.claude/agents/`, hors dépôt — les modifier depuis un chantier de dépôt sort du périmètre |
| MCP versionnés | NON FAIT | aucun `.mcp.json` ici ; en créer un déciderait à ta place quels serveurs le dépôt exige |
| LM Studio local | INSTABLE | a alterné entre « aucun modèle chargeable », `TimeoutError` et un `qwen2.5-coder-14b` fonctionnel. Un redémarrage du serveur LM Studio est recommandé |
| M6 (`10.42.0.1`) | ÉCARTÉ | ne tient qu'un modèle à la fois ; utilisable en fixant explicitement le modèle chargé |

---

## 7. Commits

```
a4af388 feat(dual): worker agy (Antigravity CLI) + verdict de parallélisme dédoublé
c5477a7 docs: architecture dual, guide utilisateur et câblage agy 1.1.12
5afb5bb fix(dual): la config vérifiée prime sur la redécouverte + sonde anti-fantôme
de7e8ea test(dual): 27 tests sur faux serveur HTTP (pannes réelles, sans LLM)
7164a9a feat(dual): doctor, benchmark de parallélisme, board, watchdog et CLI
78967d3 feat(dual): workers, dispatcher 6 modes, checkpoints et journal
1c48ec6 feat(dual): adapter providers unique + découverte des backends
1ca904a audit: cartographie mesurée de JARVIS
```

Aucun `push`, aucun `push --force`, aucune suppression.

---

## 8. Prochaines étapes utiles

1. Redémarrer le serveur LM Studio local, puis `jarvis-dual discover --probe --save`
   pour récupérer un troisième worker local fiable.
2. Valider le protocole d'inférence d'OpenClaw pour en faire un worker
   (`OpenClawProvider` viendrait se brancher comme `AgyProvider`).
3. Tester en réel `cascade`, `review` et `pipeline` sur une tâche utile —
   ils ne sont couverts que par les tests unitaires.
4. Brancher `jarvis-dual watchdog` sur un timer systemd pour la surveillance
   continue.
