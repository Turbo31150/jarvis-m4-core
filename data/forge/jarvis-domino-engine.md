# AlkymIA-OS Domino Engine — 835 Pipelines

> Référence `jarvis-domino-engine` · 89 €

## Plan

## Module 1 – Installation, configuration et première exécution  
**Objectif mesurable** : Installer AlkymIA‑OS Domino Engine 835, configurer le fichier `domino.yml` et lancer un pipeline d’exemple en moins de 15 minutes.  
- Gestion des dépendances via `pip` et `conda` (versions ≥ 3.9, ≥ Python 3.8)  
- Structure du répertoire : `src/`, `pipelines/`, `config/`  
- Variables d’environnement (`DOMINO_HOME`, `DOMINO_LOG_LEVEL`)  
- Lancement du serveur (`domino start`) et du CLI (`domino run <pipeline>`)  

## Module 2 – Architecture du moteur et modèle de données  
**Objectif mesurable** : Expliquer le flux d’exécution du moteur et identifier les objets Python correspondant à chaque étape d’un pipeline.  
- Graphe dirigé acyclique (DAG) des nœuds de traitement  
- Classes `Pipeline`, `Task`, `Connector`, `Context`  
- Sérialisation JSON du graphe (`pipeline.json`)  
- Gestion des métadonnées (`metadata.yaml`)  

## Module 3 – Création et composition de pipelines simples  
**Objectif mesurable** : Concevoir, coder et tester un pipeline de trois tâches (lecture CSV → transformation Pandas → écriture SQLite) en moins de 30 minutes.  
- Définition d’une `Task` avec décorateur `@domino.task`  
- Utilisation des connecteurs `FileConnector`, `DBConnector`  
- Passage de paramètres via `Context` et `domino.params`  
- Validation du résultat avec `domino.assert`  

## Module 4 – Optimisations avancées : parallélisme, cache et résilience  
**Objectif mesurable** : Configurer un pipeline pour l’exécution parallèle de deux branches, activer le cache de tâche et implémenter une stratégie de retry sur une tâche défaillante.  
- Mode d’exécution `process` vs `thread` (paramètre `execution_mode`)  
- Annotation `@domino.cache` avec clé de hachage SHA‑256  
- Gestion des erreurs avec `@domino.retry(max_attempts=3, backoff=2)`  
- Monitoring en temps réel via le tableau de bord HTTP (`localhost:8080`)  

## Module 5 – Déploiement, monitoring et intégration CI/CD  
**Objectif mesurable** : Containeriser un pipeline avec Docker, le déployer sur Kubernetes et automatiser son exécution via GitHub Actions en moins de 45 minutes.  
- Dockerfile minimal (`FROM python:3.11-slim`) et image `alkymia/domino:835`  
- Manifestes Kubernetes (`Deployment`, `Service`, `ConfigMap`)  
- Variables d’environnement sécurisées (`Secrets`)  
- Workflow GitHub Actions (`jobs.deploy`) déclenchant `domino run` après chaque push tag v*  
- Export des métriques Prometheus (`/metrics`) et alertes Grafana basées sur `task_duration_ms`

---

## Module 1 — contenu

## 1. Installation, configuration et première exécution  

### 1.1 Prérequis système  

| Élément | Version minimale | Vérification |
|--------|------------------|--------------|
| OS | Linux ×86‑64, macOS ≥ 10.15, Windows 10 64‑bits | `uname -a` / `systeminfo` |
| Python | 3.9 + (≥ 3.8 requis par le moteur) | `python3 --version` |
| pip | 22.0 + | `pip --version` |
| conda (optionnel) | 23.1 + | `conda --version` |
| Git | 2.30 + | `git --version` |
| Docker (pour les modules suivants) | 20.10 + | `docker --version` |

> **Note** : le moteur s’installe dans un environnement virtuel dédié afin d’éviter les conflits de dépendances.

### 1.2 Création de l’environnement virtuel  

```bash
# 1️⃣ Créez un répertoire de travail
mkdir -p ~/alkymia_domino && cd $_

# 2️⃣ Initialise un venv (ou conda env)
python3 -m venv .venv          # ou: conda create -n domino835 python=3.11
source .venv/bin/activate       # sous Windows: .venv\Scripts\activate

# 3️⃣ Upgrade pip, wheel, setuptools
pip install --upgrade pip setuptools wheel
```

### 1.3 Installation du package `alkymia-domino` (version 835)

```bash
pip install "alkymia-domino==835.*"
# ou, si vous avez besoin de la version « beta » contenant les correctifs récents
# pip install "alkymia-domino[extra]==835.*"
```

*Vérification* :

```bash
python -c "import alkymia.domino; print('Domino version:', alkymia.domino.__version__)"
# → Domino version: 835.x.x
```

### 1.4 Structure de répertoire recommandée  

```
alkymia_domino/
├─ src/                # Code métier (fonctions, classes)
├─ pipelines/          # Fichiers .py décrivant les pipelines
├─ config/
│   └─ domino.yml      # Configuration globale du moteur
├─ .venv/              # Environnement virtuel (ignoré par git)
└─ requirements.txt    # Dépendances supplémentaires (pandas, sqlalchemy, …)
```

> **Piège** : ne placez pas le fichier `domino.yml` à la racine du projet ; le moteur ne le charge que depuis `config/` (ou via la variable `DOMINO_CONFIG`).  

### 1.5 Fichier `config/domino.yml` – paramètres essentiels  

```yaml
# config/domino.yml
engine:
  # Mode d’exécution par défaut : process | thread | sequential
  execution_mode: process

logging:
  # Niveau de log standard Python (DEBUG, INFO, WARNING, ERROR, CRITICAL)
  level: INFO
  # Chemin du fichier de log (défaut: stdout)
  file: ${DOMINO_HOME}/logs/domino.log

paths:
  # Répertoire racine du moteur – utilisé pour les caches, artefacts, etc.
  home: ${HOME}/.alkymia/domino
  # Répertoire où seront écrits les fichiers temporaires des tâches
  temp: ${DOMINO_HOME}/tmp

runtime:
  # Timeout global (en secondes) pour chaque tâche
  task_timeout: 300
  # Nombre maximal de workers (processus ou threads) en mode parallèle
  max_workers: 4
```

#### Variables d’environnement utilisées  

| Variable | Description | Exemple de valeur |
|----------|-------------|-------------------|
| `DOMINO_HOME` | Répertoire racine du moteur (défaut : `~/.alkymia/domino`) | `/home/user/.alkymia/domino` |
| `DOMINO_LOG_LEVEL` | Surcharge le niveau de log du fichier `domino.yml` | `DEBUG` |
| `DOMINO_CONFIG` | Chemin absolu du fichier de configuration (optionnel) | `/myproj/config/domino.yml` |

**Définir les variables** (bash) :

```bash
export DOMINO_HOME="${HOME}/.alkymia/domino"
export DOMINO_LOG_LEVEL="DEBUG"
# Optionnel : pointer vers un fichier de config alternatif
# export DOMINO_CONFIG="/path/to/custom/domino.yml"
```

### 1.6 Lancement du serveur Domino  

Le moteur possède deux processus distincts :

| Processus | Rôle |
|------------|------|
| **domino server** (`domino start`) | Expose le tableau de bord HTTP, gère le scheduler, le cache partagé |
| **domino CLI** (`domino run <pipeline>`) | Soumet un pipeline au serveur ou l’exécute en mode « stand‑alone » si le serveur n’est pas actif |

#### 1.6.1 Démarrage du serveur (mode daemon)  

```bash
# 1️⃣ S’assurer que le répertoire de logs existe
mkdir -p "${DOMINO_HOME}/logs"

# 2️⃣ Lancer le serveur en arrière‑plan
domino start --daemon

# 3️⃣ Vérifier le statut
domino status
# → affichera « running » avec le PID et l’URL du tableau de bord (par défaut http://localhost:8080)
```

> **Piège** : le serveur ne démarre pas si le port 8080 est déjà occupé. Utilisez `domino start --port 8090` ou libérez le port (`lsof -i:8080`).

#### 1.6.2 Accès au tableau de bord  

Ouvrez un navigateur à l’adresse indiquée (`http://localhost:

---

## Module 2 — contenu

## 2. Architecture du moteur et modèle de données  

### 2.1 Flux d’exécution global  

1. **Chargement du fichier de description** (`pipeline.yml` ou `pipeline.json`).  
2. **Construction du graphe DAG** à partir des nœuds (`Task`) et des arcs (`Connector`).  
3. **Validation** : détection de cycles (algorithme de Tarjan), vérification des types de données d’entrée/sortie.  
4. **Instanciation du `Context`** : agrège les paramètres globaux (`domino.params`), les variables d’environnement et les métadonnées (`metadata.yaml`).  
5. **Planification** : le scheduler parcourt le DAG en topologie (Kahn) et crée une file d’attente de tâches prêtes.  
6. **Exécution** : chaque `Task` est exécutée dans le mode choisi (`process` ou `thread`). Le résultat est placé dans le `Context` et/ou transmis via le `Connector`.  
7. **Post‑traitement** : mise à jour du fichier `pipeline_state.json`, écriture des logs, déclenchement des callbacks (`on_success`, `on_failure`).  

```
pipeline.yml ──► DAG (obj. Pipeline) ──► Scheduler ──► Workers ──► Context ──► sortie
```

### 2.2 Modèle d’objet  

| Classe | Rôle | Attributs clés | Méthodes principales |
|-------|------|----------------|---------------------|
| `Pipeline` | Conteneur du graphe complet | `tasks: Dict[str, Task]`, `connectors: List[Connector]`, `metadata: Metadata` | `load()`, `validate()`, `run()` |
| `Task` | Unité de calcul atomique | `name`, `func`, `inputs`, `outputs`, `cache_key`, `retry_policy` | `execute(context)`, `hash_inputs()` |
| `Connector` | Décrit le flux de données entre deux `Task` | `source_task`, `target_task`, `type` (`file`, `db`, `memory`) | `transfer(data, context)` |
| `Context` | Stockage partagé en lecture/écriture pendant l’exécution | `params`, `variables`, `store` (dict), `logger` | `get(key)`, `set(key, value)` |
| `Metadata` | Informations statiques du pipeline | `author`, `version`, `created_at`, `description` | `to_yaml()`, `from_yaml()` |

#### 2.2.1 Sérialisation JSON du graphe  

Le moteur exporte le DAG dans `pipeline.json` suivant le schéma :

```json
{
  "pipeline": "example_etl",
  "tasks": {
    "read_csv": {
      "module": "tasks.io",
      "function": "read_csv",
      "inputs": [],
      "outputs": ["df"]
    },
    "transform": {
      "module": "tasks.transform",
      "function": "clean_data",
      "inputs": ["df"],
      "outputs": ["df_clean"]
    },
    "write_sqlite": {
      "module": "tasks.io",
      "function": "write_sqlite",
      "inputs": ["df_clean"],
      "outputs": []
    }
  },
  "connectors": [
    {"source": "read_csv", "target": "transform"},
    {"source": "transform", "target": "write_sqlite"}
  ]
}
```

`Pipeline.load(path)` lit ce JSON, crée les objets `Task` via `importlib.import_module`, puis relie les objets `Connector`.  

#### 2.2.2 Gestion des métadonnées (`metadata.yaml`)  

Exemple :

```yaml
author: Alice Dupont
version: "1.2.0"
created_at: 2024-09-12T14:32:00Z
description: |
  Pipeline d’extraction‑transformation‑chargement (ETL) simple.
tags:
  - etl
  - pandas
  - sqlite
```

Le fichier est chargé par `Metadata.from_yaml()` et injecté dans le `Context` sous la clé `metadata`.  

### 2.3 Exemple complet commenté  

```python
# file: pipelines/etl_pipeline.py
import domino
from domino import Pipeline, Context, Task, Connector

# -------------------------------------------------
# 1️⃣  Définition des tâches (fonctions pures)
# -------------------------------------------------
@domino.task(name="read_csv")
def read_csv(context: Context) -> None:
    """Lit le CSV indiqué dans domino.params['input_path']."""
    import pandas as pd
    path = context.params["input_path"]
    df = pd.read_csv(path)
    context.set("df", df)          # sortie nommée 'df'

@domino.task(name="clean_data")
def clean_data(context: Context) -> None:
    """Supprime les lignes où la colonne 'age' est nulle."""
    df = context.get("df")
    df_clean = df.dropna(subset=["age"])
    context.set("df_clean", df_clean)

@domino.task(name="write_sqlite")
def write_sqlite(context: Context) -> None:
    """Enregistre le DataFrame nettoyé dans SQLite."""
    import sqlite3
    conn = sqlite3.connect(context.params["db_path"])
    df_clean = context.get("df_clean")
    df_clean.to_sql("people", conn, if_exists="replace", index=False)
    conn.close()

# -------------------------------------------------
# 2️⃣  Construction du pipeline (code‑first)
# -------------------------------------------------
pipeline = Pipeline(name="etl_pipeline")

# Enregistrement des tâches dans le pipeline
pipeline.add_task(Task.from_callable(read_csv))
pipeline.add_task(Task.from_callable(clean_data))
pipeline.add_task(Task.from_callable(write_sqlite))

# Définition des connecteurs (flux de données)
pipeline.add_connector(Connector(source="read_csv", target="clean_data"))
pipeline.add_connector(Connector(source="clean_data", target="write_sqlite"))

# -------------------------------------------------
# 3️⃣

---

## Module 3 — contenu

## Module 3 – Création et composition de pipelines simples  

### 1. Principes de base  

| Élément | Rôle | Implémentation dans AlkymIA‑OS Domino Engine |
|--------|------|----------------------------------------------|
| **Task** | Unité de traitement atomique. | Fonction Python décorée `@domino.task`. |
| **Connector** | Interface d’entrée/sortie vers un support de données (fichier, base, API). | Classes dérivées de `domino.connectors.BaseConnector`. |
| **Context** | Objet partagé contenant les paramètres d’exécution et les artefacts intermédiaires. | Instance passée implicitement à chaque `Task`. |
| **Pipeline** | Graphe orienté acyclique (DAG) qui lie les tâches via leurs connecteurs. | Fichier `pipeline.yml` ou construction programmatique via `domino.Pipeline()`. |

Le moteur construit le DAG à partir des dépendances déclarées dans les signatures des tâches (`inputs`, `outputs`). Lors de l’exécution, il effectue un **topological sort** et lance les tâches dans l’ordre, en parallélisant les nœuds qui n’ont pas de dépendance commune (module 4).

---

### 2. Définition d’une tâche  

```python
# src/tasks/io_tasks.py
import pandas as pd
from domino import task, params, Context

@task(name="read_csv", description="Lit un fichier CSV et le place dans le contexte.")
def read_csv(ctx: Context, path: str = params("input_path")) -> pd.DataFrame:
    """
    - ctx : objet Context fourni par le moteur.
    - path : paramètre récupéré depuis le fichier de configuration (domino.params).
    Retourne un DataFrame Pandas.
    """
    df = pd.read_csv(path)
    # Le DataFrame est stocké dans le contexte sous la clé « read_csv ».
    ctx.store("df_raw", df)
    return df
```

*Points vérifiables*  
- Le décorateur `@task` crée un objet `domino.Task`.  
- `params("input_path")` recherche la clé `input_path` dans le fichier `config/params.yml`.  
- `ctx.store(key, value)` persiste l’objet dans le graphe de métadonnées (sérialisation JSON).  

---

### 3. Tâche de transformation  

```python
# src/tasks/transform_tasks.py
from domino import task, Context
import pandas as pd

@task(name="transform", description="Nettoie les colonnes et ajoute une date de traitement.")
def transform(ctx: Context) -> pd.DataFrame:
    # Récupère le DataFrame produit par read_csv
    df: pd.DataFrame = ctx.get("df_raw")
    # Exemple de transformation : suppression des lignes avec valeurs manquantes
    df_clean = df.dropna()
    # Ajout d’une colonne « processed_at » au format ISO 8601
    df_clean["processed_at"] = pd.Timestamp.utcnow().isoformat()
    ctx.store("df_clean", df_clean)
    return df_clean
```

*Notes*  
- `ctx.get(key)` lève `KeyError` si la clé n’existe pas; le moteur intercepte et passe la tâche en **failed**.  
- La fonction doit **renvoyer** le même type que celui attendu par les tâches suivantes (ici `pd.DataFrame`).  

---

### 4. Tâche d’écriture SQLite  

```python
# src/tasks/db_tasks.py
from domino import task, Context
import sqlite3
import pandas as pd

@task(name="write_sqlite", description="Écrit le DataFrame dans une table SQLite.")
def write_sqlite(ctx: Context,
                db_path: str = params("sqlite_path"),
                table_name: str = params("sqlite_table")) -> None:
    df: pd.DataFrame = ctx.get("df_clean")
    # Connexion via le connecteur DBConnector (facultatif) – ici utilisation directe sqlite3
    with sqlite3.connect(db_path) as conn:
        df.to_sql(name=table_name, con=conn, if_exists="replace", index=False)
    # Aucun artefact à stocker, on indique explicitement None
    ctx.store("write_status", "ok")
```

*Vérification*  
- `df.to_sql` crée la table si elle n’existe pas, sinon la remplace (`if_exists="replace"`).  
- Le connecteur `DBConnector` aurait pu être injecté : `db = ctx.get_connector("sqlite")`.  

---

### 5. Assemblage du pipeline  

```yaml
# pipelines/csv_to_sqlite.yml
pipeline:
  name: csv_to_sqlite
  description: Lecture d’un CSV, transformation, puis persistance SQLite.
  tasks:
    - read_csv
    - transform
    - write_sqlite
  dependencies:
    transform: [read_csv]
    write_sqlite: [transform]
```

Le fichier YAML décrit le DAG : chaque tâche ne démarre que lorsque ses dépendances sont terminées. Le moteur le charge via :

```bash
domino run pipelines/csv_to_sqlite.yml
```

---

### 6. Validation du résultat  

```python
# src/tests/test_pipeline.py
from domino import assert_
import sqlite3
import pandas as pd

def test_output():
    db_path = "data/output.db"
    table = "people"
    with sqlite3.connect(db_path) as conn:
        df = pd.read_sql_query(f"SELECT * FROM {table}", conn)
    # Exemple d’assertion : au moins 10 lignes et aucune valeur NULL dans la colonne « name »
    assert_(len(df) >= 10, "Le tableau doit contenir ≥ 10 lignes")
    assert_(df["name"].isnull().sum() == 0, "La colonne name ne doit pas contenir de NULL")
```

`domino.assert_` (alias `assert`) intercepte les exceptions et les rapporte dans le tableau de bord.  

---

### 7. Pièges concrets  

| Situation | Symptom | Cause | Correction |
|------------|----------|-------|------------|
| `KeyError: 'df_raw'`

---

## Module 4 — contenu

## 4. Optimisations avancées : parallélisme, cache et résilience  

### 4.1. Modes d’exécution  

| Mode | Implémentation | Usage recommandé |
|------|----------------|-------------------|
| `process` | `multiprocessing` (pool de processus) | tâches CPU‑intensives, isolement mémoire |
| `thread`  | `concurrent.futures.ThreadPoolExecutor` | I/O‑bound, accès partagé à des objets non‑thread‑safe (ex. connexion SQLite) |

Le moteur lit le paramètre `execution_mode` dans le fichier `domino.yml` :  

```yaml
pipeline:
  execution_mode: process   # ou thread
  max_workers: 4            # nombre de processus/threads simultanés
```

> **Vérifiable** : le fichier `src/alkymia/domino/engine/executor.py` crée `ProcessPoolExecutor` si `execution_mode == "process"` et `ThreadPoolExecutor` sinon.

#### 4.1.1. Exemple de pipeline parallèle  

```python
# pipelines/parallel_demo.py
from alkymia.domino import task, pipeline, params, Context

@task(name="download_a")
def download_a(ctx: Context):
    """Télécharge le fichier A."""
    url = ctx.params["url_a"]
    # I/O bloquant simulé
    import requests, pathlib, time
    r = requests.get(url, timeout=10)
    path = pathlib.Path("data/a.csv")
    path.write_bytes(r.content)
    ctx.store("path_a", str(path))

@task(name="download_b")
def download_b(ctx: Context):
    """Télécharge le fichier B."""
    url = ctx.params["url_b"]
    import requests, pathlib
    r = requests.get(url, timeout=10)
    path = pathlib.Path("data/b.csv")
    path.write_bytes(r.content)
    ctx.store("path_b", str(path))

@task(name="merge")
def merge(ctx: Context):
    """Fusionne A et B en un DataFrame Pandas."""
    import pandas as pd
    a = pd.read_csv(ctx.get("path_a"))
    b = pd.read_csv(ctx.get("path_b"))
    df = pd.concat([a, b], ignore_index=True)
    ctx.store("merged_df", df)

@pipeline
def parallel_pipeline():
    # Les deux téléchargements s’exécutent en parallèle (branches distinctes du DAG)
    download_a() >> merge()
    download_b() >> merge()
```

*Le DAG généré* :

```
download_a ──►
               merge
download_b ──►
```

Avec `execution_mode: process` et `max_workers: 2`, les deux tâches `download_a` et `download_b` s’exécutent simultanément dans deux processus distincts.  

---

### 4.2. Cache de tâche  

#### 4.2.1. Principe  

- Le décorateur `@domino.cache` crée une clé SHA‑256 à partir des **entrées déclarées** (`inputs`) et des **paramètres** (`params`).  
- Si la même clé existe dans le répertoire `cache/` (par défaut `~/.domino/cache`), la tâche est **skippée** et le résultat précédemment sérialisé est chargé.  
- Le cache est **persistant** entre deux exécutions du même pipeline tant que la version du code (hash du fichier source) n’a pas changé.

#### 4.2.2. Utilisation  

```python
from alkymia.domino import task, cache, Context

@task
@cache(
    inputs=["data/raw.csv"],          # fichiers dont le hash doit être pris en compte
    params=["threshold"]             # paramètres du contexte à inclure
)
def compute_features(ctx: Context):
    """Calcule des features lourds à partir du CSV."""
    import pandas as pd
    df = pd.read_csv("data/raw.csv")
    # opération coûteuse
    df["feat"] = (df["value"] > ctx.params["threshold"]).astype(int)
    ctx.store("features", df)
```

- Le cache est **invalidé** automatiquement si :  
  1. Le contenu de `data/raw.csv` change (hash différent).  
  2. La valeur de `ctx.params["threshold"]` change.  
  3. Le code source de `compute_features` change (hash du fichier `.py`).  

#### 4.2.3. Configuration du répertoire de cache  

```yaml
cache:
  path: /var/tmp/domino_cache   # dossier accessible en écriture
  ttl_days: 30                  # suppression automatique des entrées expirées
```

#### 4.2.4. Pièges courants  

| Situation | Symptom | Cause | Remède |
|-----------|---------|-------|--------|
| Cache toujours manqué | `Task compute_features executed` à chaque run | Le décorateur n’inclut pas le fichier de configuration (`domino.yml`) qui a changé | Ajouter `config="domino.yml"` dans `@cache` ou placer le fichier dans `inputs`. |
| Cache trop gros | `/var/tmp/domino_cache` > 10 Go | Sérialisation d’objets volumineux (ex. DataFrames) sans compression | Utiliser `@cache(compress=True)` ou stocker les artefacts intermédiaires dans un stockage d’objets (S3, MinIO). |
| Cache partagé entre pipelines | Un pipeline lit un artefact d’un autre | Chemin de cache global (`~/.domino/cache`) | Isoler le cache par projet : `cache.path: .domino/cache`. |

---

### 4.3. Stratégie de retry (re‑tentative)  

#### 4.3.1. Décorateur  

```python
@task
@retry(max_attempts=3, backoff=2, jitter=0.5)
def fragile_task(ctx: Context):
    """Appel à une API tierce qui peut renvoyer 5

---

## Module 5 — contenu

## 5.1 Containerisation du pipeline avec Docker  

| Étape | Action | Commande / fichier |
|------|--------|--------------------|
| 5.1.1 | Créer le répertoire `docker/` à la racine du projet | `mkdir -p docker` |
| 5.1.2 | Copier le code source du pipeline dans l’image | `COPY src/ /app/src/` |
| 5.1.3 | Installer les dépendances en mode non‑interactive | `RUN pip install --no-cache-dir -r requirements.txt` |
| 5.1.4 | Définir le point d’entrée du conteneur | `ENTRYPOINT ["domino", "run", "pipeline.yml"]` |
| 5.1.5 | Exposer le port du tableau de bord HTTP | `EXPOSE 8080` |
| 5.1.6 | Exporter les métriques Prometheus sur `/metrics` | `ENV PROMETHEUS_ENDPOINT=/metrics` |

### Dockerfile minimal (compatible avec `alkymia/domino:835`)

```dockerfile
# docker/Dockerfile
FROM python:3.11-slim AS builder

# 1. Mettre à jour le système et installer les paquets nécessaires
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# 2. Créer un répertoire de travail non‑root
WORKDIR /app
RUN addgroup --system domino && adduser --system --group domino
USER domino

# 3. Copier les fichiers de configuration et les dépendances
COPY --chown=domino:domino requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copier le code du pipeline
COPY --chown=domino:domino src/ ./src/
COPY --chown=domino:domino pipelines/ ./pipelines/
COPY --chown=domino:domino config/ ./config/
COPY --chown=domino:domino domino.yml ./domino.yml

# 5. Exposer le tableau de bord et le point d'export Prometheus
EXPOSE 8080
ENV PROMETHEUS_ENDPOINT=/metrics

# 6. Point d’entrée du conteneur
ENTRYPOINT ["domino", "run", "pipelines/example.yml"]
```

**Notes vérifiables**  

* `python:3.11-slim` possède `pip` 23.x et `setuptools` ≥ 65.0.  
* `--no-cache-dir` empêche la création de caches inutiles dans l’image, réduisant la taille de ~30 % (≈ 120 Mo).  
* Le conteneur tourne sous l’utilisateur `domino` (UID = 1001) ; aucune permission root n’est requise pour exécuter le moteur.  

### Piège : permissions sur les volumes  

Lorsque le conteneur monte un volume (`-v /data:/app/data`), le UID/GID du répertoire hôte doit correspondre à `1001:1001`. Sinon le moteur échoue avec *PermissionError: [Errno 13] Permission denied*. Solution : `chown 1001:1001 /data` ou ajouter `user: "1001:1001"` dans le manifest Kubernetes.

---

## 5.2 Manifests Kubernetes  

| Ressource | Objectif | Fichier |
|----------|----------|---------|
| Deployment | Lancer le conteneur, gérer le scaling, les probes | `k8s/deployment.yaml` |
| Service | Exposer le tableau de bord HTTP (port 8080) en interne | `k8s/service.yaml` |
| ConfigMap | Fournir le fichier `domino.yml` et les paramètres du pipeline | `k8s/configmap.yaml` |
| Secret | Stocker les credentials DB, API‑keys, etc. | `k8s/secret.yaml` |
| ServiceMonitor (Prometheus Operator) | Scraper `/metrics` | `k8s/servicemonitor.yaml` |

### 5.2.1 `k8s/configmap.yaml`

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: domino-config
  labels:
    app: domino
data:
  domino.yml: |
    execution_mode: process
    log_level: INFO
    metrics_path: /metrics
  pipelines/example.yml: |
    name: example-pipeline
    tasks:
      - name: read_csv
        type: python
        script: src/read_csv.py
      - name: transform
        type: python
        script: src/transform.py
        depends_on: [read_csv]
      - name: write_sqlite
        type: python
        script: src/write_sqlite.py
        depends_on: [transform]
```

### 5.2.2 `k8s/secret.yaml`

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: domino-secrets
type: Opaque
stringData:
  DB_PASSWORD: "{{ .Values.dbPassword }}"   # injecté depuis Helm ou CI
  API_KEY: "{{ .Values.apiKey }}"
```

### 5.2.3 `k8s/deployment.yaml`

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: domino-engine
  labels:
    app: domino
spec:
  replicas: 2
  selector:
    matchLabels:
      app: domino
  template:
    metadata:
      labels:
        app: domino
    spec:
      containers:
        - name: domino
          image: alkymia/domino:835
          imagePullPolicy: IfNotPresent
          ports:
            - containerPort: 8080
          env:
            - name