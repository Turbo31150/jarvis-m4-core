# CLAUDE.md — Profil `jarvis` (INFRA)

Orchestrateur, cluster, adapters LLM, board, audit. **Aucune donnée
personnelle ici** : ni élève, ni famille, ni prospect.

## Ce que contient cet espace
| Chemin | Rôle |
|---|---|
| `dual/` | JARVIS DUAL ORCHESTRATOR — providers, workers, dispatcher, checkpoints |
| `board/` | Conseil d'experts local (`bin/jarvis-board`) — réponse sans citation rejetée |
| `audit/` | Moteur d'audit deep research (`jarvis-audit`) |
| `scripts/`, `multiagent/`, `cli/` | Historique : routeurs, watchdogs, dashboards |
| `webapp/` | **Profil `ecole` — ne pas travailler ici depuis ce profil** |

## Règles
- **Preuve avant affirmation.** Aucun statut `OK` par défaut : un composant est
  `WORKING` seulement si une commande l'a démontré. Sinon `PARTIAL`, `BLOCKED`,
  `UNTESTED`.
- **Une métrique non fournie par l'API vaut `UNAVAILABLE`**, jamais 0 ni une
  estimation.
- **Ne pas créer un énième routeur de backends.** Il en existe déjà trois
  (`scripts/model_router.sh`, `multiagent/jarvis-router.py`, `dual/config.py`).
  Consolider sur `dual/config.py`, le seul qui exige une inférence réussie.
- **Secrets** : `certs/*.key` et `.env` restent hors git (déjà gitignorés). Une
  clé privée sur le disque d'un serveur est normale — vérifier `git ls-files`
  avant de crier à la fuite.

## Contraintes matérielles à ne pas réapprendre
- GPU unique **4 Go** : LM Studio ne sert **qu'un modèle à la fois** et ne
  décharge pas le résident → tout autre modèle échoue en `cudaMalloc OOM`.
  Vérifier avec `curl :1234/api/v0/models` (champ `state`).
- Le DUAL réel = **deux backends distincts**, jamais deux modèles locaux.
- Modèles `qwen3*` : sans `think=False` (Ollama) ou `/no_think` (LM Studio),
  tout le budget part en raisonnement → statut `reasoning_only`.
- Garde thermique **82 °C**, coupure à 86 °C.

## Commandes
```bash
./bin/jarvis-dual doctor          # diagnostic CAUSE/IMPACT/ACTION
./bin/jarvis-dual test            # preuve de parallélisme mesurée
./bin/jarvis-board status         # état du corpus et des experts
jarvis-audit run --target . --mode deep --profile full
requestly-ask --list              # liste des endpoints IA Requestly (ChatGPT, Gemini, Perplexity)
requestly-ask gemini "<prompt>"   # délégation rapide Gemini 2.0 via Requestly
requestly-ask chatgpt "<prompt>"  # délégation rapide ChatGPT via Requestly
requestly-ask perplexity "<p>"    # recherche web / deep search Perplexity Sonar
```

## Connecteurs & Boosters Disponibles
- **`requestly-ask`** (`~/.local/bin/requestly-ask`) : Connecteur direct CLI
- **`requestly-jarvis`** (MCP) : Pilotage et exécution des collections API Requestly
- **`ia-web-jarvis`** (MCP) : Routage direct LLM Web (ChatGPT, Gemini, Perplexity) + navigation CDP
- **`jarvis-board-mcp`** (MCP) : Requêtes Board OS, consensus et Bibliothèque Vivante

## Workflow
Écrire le résultat dans `REPORT.md`, tenir `TODO.md` à jour, ne jamais déclarer
terminé sans preuve.
