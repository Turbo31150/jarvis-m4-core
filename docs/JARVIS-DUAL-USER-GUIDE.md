# JARVIS DUAL — guide d'utilisation

Point d'entrée unique : `./bin/jarvis-dual` (depuis `~/jarvis`).
Aucune dépendance à installer : stdlib Python 3 uniquement.

## Démarrage

```bash
cd ~/jarvis
./bin/jarvis-dual doctor          # diagnostic complet (teste l'inférence réelle)
./bin/jarvis-dual doctor --fast   # sans inférence : rapide, mais les workers sortent en [UNK]
```

Le doctor ne dit jamais `[OK]` sans preuve. Chaque `[WARN]`/`[ERROR]` affiche
**CAUSE / IMPACT / ACTION**. Code retour 1 s'il reste une erreur.

## Découvrir les backends

```bash
./bin/jarvis-dual discover --save   # sonde LM Studio, Ollama, M6… puis écrit dual/config.json
./bin/jarvis-dual models            # modèles réellement exposés par chaque backend
./bin/jarvis-dual workers           # santé de A et B (serveur + modèle)
```

Rien n'est supposé : chaque URL candidate est réellement contactée. Un backend
absent est simplement ignoré.

## Choisir A et B

Automatique après `discover` : A et B sont placés sur des **backends distincts**
(contrainte matérielle, cf. `JARVIS-DUAL-ARCHITECTURE.md`). Pour forcer :

```bash
export JARVIS_WORKER_A="qwen/qwen3.5-9b"
export JARVIS_WORKER_B="gemma3:4b"
export LMSTUDIO_BASE_URL="http://10.42.0.1:1234"   # M6 par câble direct
export OLLAMA_BASE_URL="http://127.0.0.1:11434"
```

Ou éditer `dual/config.json` (`workers.worker_a.model`, etc.).

## Lancer une demande

```bash
./bin/jarvis-dual run "Résume ce texte en 3 points" -m single
./bin/jarvis-dual run "Explique les GIL Python" -m parallel -a merge
./bin/jarvis-dual run "Écris une fonction de tri" -m review
./bin/jarvis-dual run "1. lister les risques
2. proposer des correctifs
3. écrire la conclusion" -m pipeline
```

| Option | Effet |
|---|---|
| `-m` | `single` `parallel` `cascade` `review` `fallback` `pipeline` |
| `-a` | agrégation : `first` `best` `merge` `consensus` |
| `-s` | prompt système |
| `--max-tokens` | plafond de génération (défaut 400) |
| `--json` | sortie machine |

Les listes numérotées ou à puces sont automatiquement découpées en micro-tâches
`TASK-001…N`, chacune checkpointée.

## Vérifier le DUAL

```bash
./bin/jarvis-dual test        # verdict de concurrence, sortie courte
./bin/jarvis-dual benchmark   # A seul, B seul, puis A+B
```

Le verdict s'appuie sur des mesures (`overlap_s`, `token_switches`,
`parallel_efficiency`), pas sur une intention. `FAILED` signifie exécution
sérialisée — et le rapport dit pourquoi.

## Suivre, reprendre, comprendre

```bash
./bin/jarvis-dual board                 # tableau de bord
./bin/jarvis-dual board --watch         # rafraîchi toutes les 2 s
./bin/jarvis-dual jobs                  # tous les jobs et leur avancement
./bin/jarvis-dual replay <job_id>       # chronologie exacte, à la milliseconde
./bin/jarvis-dual recover <job_id>      # rejoue uniquement les tâches non réussies
./bin/jarvis-dual watchdog              # jobs figés (diagnostic seul)
./bin/jarvis-dual watchdog --act        # les marque RECOVERABLE (ne tue rien)
```

## Où sont les fichiers

| Chemin | Contenu |
|---|---|
| `dual/config.json` | configuration vérifiée (généré par `discover --save`) |
| `logs/dual/<job_id>.jsonl` | journal d'événements horodatés |
| `data/dual-jobs/<job_id>.json` | état des tâches et checkpoints |

## Tests

```bash
python3 -m unittest discover -s dual/tests -t . -v
```

27 tests, sans LLM réel : un faux serveur HTTP rejoue les pannes (serveur mort,
modèle fantôme, HTTP 200 vide, silence, retry, reprise après crash).

## Diagnostic des pannes courantes

| Symptôme | Cause probable | Que faire |
|---|---|---|
| `model_unavailable` alors que le modèle est listé | le backend sert **un seul modèle à la fois** : celui demandé n'est pas le résident, et il n'y a plus de VRAM pour les compute buffers | `curl :1234/api/v0/models` pour voir lequel est `loaded` ; viser celui-là, ou décharger l'autre dans l'interface LM Studio |
| `reasoning_only` | modèle en mode *thinking* : tout le budget part en raisonnement | couper le raisonnement (`think=False` sur Ollama, `no_think=True` sur LM Studio) ou augmenter `--max-tokens` |
| `empty_response` | HTTP 200 mais **ni** contenu **ni** raisonnement | vérifier le backend : c'est une vraie anomalie, pas un modèle qui réfléchit |
| `timeout_first_token` | le modèle charge à froid (constaté : 14 s sur `gemma3:4b`) | augmenter `timeouts.first_token` dans `dual/config.json` |
| `DUAL_PARALLEL = BLOCKED` | un seul backend joignable | démarrer Ollama ou un second LM Studio |
| `BLOCKED: aucun worker` | aucun backend ne répond | `jarvis-dual doctor` pour la cause exacte |
