# MLOps — IA en Production

> Référence `mlops` · 89 €

## Plan

## Module 1 : Architecture de pipeline MLOps
**Objectif mesurable** : Concevoir et implémenter un pipeline CI/CD complet (build, test, validation, déploiement) pour un modèle de classification en moins de 2 h.  
- Gestion du code source avec Git + Git‑flow.  
- Définition d’un pipeline CI/CD dans GitHub Actions (ou GitLab CI).  
- Tests unitaires et d’intégration pour les fonctions de pré‑traitement et de prédiction.  
- Conteneurisation du modèle avec Docker (Dockerfile, image multi‑stage).  
- Publication d’artefacts (modèle, image) dans un registre (Docker Hub ou GitHub Packages).

## Module 2 : Gestion des données et du versionnage
**Objectif mesurable** : Mettre en place un système de suivi des jeux de données et des métadonnées, et reproduire un entraînement à partir d’un snapshot de données.  
- Stockage des données brutes et transformées (S3, Azure Blob, GCS).  
- Versionnage des datasets avec DVC ou Pachyderm.  
- Enregistrement des paramètres d’entraînement (MLflow, Hydra, JSON/YAML).  
- Gestion des schémas et validation (Great Expectations).  
- Automatisation du rafraîchissement des jeux de données via pipelines Airflow ou Prefect.

## Module 3 : Entraînement scalable et suivi d’expérimentation
**Objectif mesurable** : Exécuter un entraînement distribué sur un cluster Kubernetes et consigner les métriques dans un tableau de bord exploitable.  
- Utilisation de frameworks distribués (Horovod, PyTorch Distributed, TensorFlow Strategy).  
- Orchestration de jobs d’entraînement avec Kubeflow Pipelines ou Argo Workflows.  
- Tracking des expériences avec MLflow Tracking Server ou Weights & Biases.  
- Gestion des artefacts de modèle (pickle, ONNX, TorchScript).  
- Analyse des courbes de perte et des métriques via Grafana/Prometheus.

## Module 4 : Déploiement et orchestration en production
**Objectif mesurable** : Déployer le modèle en service RESTful sur un cluster Kubernetes et valider le SLA de latence (< 100 ms) sur un jeu de requêtes synthétique.  
- Création d’une API inference avec FastAPI ou Flask.  
- Containerisation et déploiement via Helm charts.  
- Mise en place de l’autoscaling (HPA) basé sur les métriques de CPU/mémoire et de latence.  
- Gestion du trafic avec un Ingress controller (NGINX, Traefik).  
- Monitoring des endpoints (Prometheus exporter, OpenTelemetry).

## Module 5 : Surveillance, gouvernance et mise à jour continue
**Objectif mesurable** : Configurer une chaîne de monitoring qui déclenche automatiquement le retrait d’un modèle en cas de dérive de données supérieure à un seuil défini.  
- Collecte de métriques de performance (accuracy, drift) via Evidently AI ou NannyML.  
- Alerting avec Alertmanager et Slack/Teams.  
- Gestion du cycle de vie du modèle (model registry, versioning, canary release).  
- Mise à jour continue (blue‑green, canary) avec Argo Rollouts.  
- Conformité RGPD et traçabilité des décisions (audit logs, Data Lineage

---

## Module 1 — contenu

## Module 1 : Architecture de pipeline MLOps  

### 1. Gestion du code source avec Git + Git‑flow  

| Branch | Rôle | Convention de nommage |
|--------|------|------------------------|
| `main` | version stable, déployable | `main` |
| `develop` | branche d’intégration continue | `develop` |
| `feature/<ticket>` | développement d’une fonctionnalité | `feature/issue‑12‑preprocess` |
| `release/<vX.Y>` | stabilisation avant mise en prod | `release/1.0` |
| `hotfix/<vX.Y.Z>` | correctif urgent sur `main` | `hotfix/1.0.1` |

**Workflow typique**  

```bash
# création d’une feature
git checkout develop
git pull
git checkout -b feature/issue-12-preprocess

# travail, commits fréquents
git add src/preprocess.py
git commit -m "feat: ajout du pré‑traitement des dates"

# mise à jour de develop et résolution de conflits éventuels
git checkout develop
git pull
git merge --no-ff feature/issue-12-preprocess

# suppression de la branche locale
git branch -d feature/issue-12-preprocess
git push origin develop
```

*Piège* : ne jamais pousser directement sur `main`. Un merge accidentel sur `main` déclenche le pipeline de production et peut bloquer le déploiement.

---

### 2. Pipeline CI/CD avec GitHub Actions  

Fichier **`.github/workflows/ci-cd.yml`** (YAML) :

```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [ develop, main ]
  pull_request:
    branches: [ develop ]

jobs:
  # ---------- Lint & tests ----------
  test:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Python 3.11
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Cache pip dependencies
        uses: actions/cache@v4
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('requirements.txt') }}
          restore-keys: ${{ runner.os }}-pip-

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install -r requirements-dev.txt   # pytest, flake8, mypy

      - name: Lint (flake8)
        run: flake8 src tests

      - name: Type check (mypy)
        run: mypy src

      - name: Run unit & integration tests
        run: pytest -v --cov=src

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v4
        with:
          token: ${{ secrets.CODECOV_TOKEN }}

  # ---------- Build Docker image ----------
  build:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'   # ne builder que sur main
    steps:
      - uses: actions/checkout@v4

      - name: Log in to Docker Hub
        uses: docker/login-action@v3
        with:
          username: ${{ secrets.DH_USERNAME }}
          password: ${{ secrets.DH_PASSWORD }}

      - name: Build multi‑stage image
        run: |
          docker build \
            --target runtime \
            -t ${{ secrets.DH_USERNAME }}/mlops-demo:${{ github.sha }} \
            .

      - name: Push image
        run: |
          docker push ${{ secrets.DH_USERNAME }}/mlops-demo:${{ github.sha }}
```

**Points clés**  

* `needs: test` garantit que le build ne démarre que si les tests passent.  
* `if: github.ref == 'refs/heads/main'` empêche la construction d’images sur les branches de feature.  
* Les secrets (`DH_USERNAME`, `DH_PASSWORD`, `CODECOV_TOKEN`) sont stockés dans **Settings → Secrets** du repo.  

*Piège* : le cache pip peut devenir obsolète après une mise à jour majeure de dépendance. Supprimez le cache ou changez la clé (`hashFiles('requirements.txt')`) pour forcer le rafraîchissement.

---

### 3. Tests unitaires et d’intégration  

#### 3.1 Structure du projet  

```
mlops-demo/
├─ src/
│  ├─ __init__.py
│  ├─ preprocess.py
│  └─ model.py
├─ tests/
│  ├─ __init__.py
│  ├─ test_preprocess.py
│  └─ test_inference.py
├─ requirements.txt
└─ pyproject.toml
```

#### 3.2 Exemple de test unitaire (pytest) – `tests/test_preprocess.py`

```python
"""Tests unitaires du module preprocess."""

import pandas as pd
import pytest
from src.preprocess import clean_dates, encode_categorical

@pytest.fixture
def raw_df():
    """DataFrame minimal contenant des valeurs typiques du jeu de données."""
    return pd.DataFrame({
        "date_str": ["2023-01-15", "2023/02/20", None],
        "category": ["A", "B", "A"]
    })

def test_clean_dates_handles_various_formats(raw_df):
    """Vérifie que clean_dates convertit les formats mixtes en datetime UTC."""
    df = clean_dates(raw_df.copy(), column="date_str")
    # les valeurs valides deviennent Timestamp, les NaN restent NaT
    assert pd.api.types.is_datetime64_any_dtype(df["date_str"])
    assert df["date_str"].isna().sum() == 1
    # vérification du fuseau UTC
    assert df["date

---

## Module 2 — contenu

## Module 2 : Gestion des données et du versionnage  

### 2.1 Stockage des données brutes et transformées  

| Niveau | Service | Points clés | Exemple de configuration |
|--------|---------|-------------|--------------------------|
| **Objets** | Amazon S3, Azure Blob Storage, Google Cloud Storage | • Accès via API REST ou SDK (boto3, azure‑storage‑blob, google‑cloud‑storage). <br>• Séparer les buckets : `raw/`, `processed/`. <br>• Activer le versionnage côté bucket pour garder chaque modification. | ```bash\n# création d’un bucket S3 avec versionnage\naws s3api create-bucket --bucket my-ml-data --region us-east-1\naws s3api put-bucket-versioning --bucket my-ml-data \\\n    --versioning-configuration Status=Enabled\n``` |
| **Montage** | Fuse‑S3, gcsfuse, Azure Blob Fuse | Permet d’accéder aux objets comme à un système de fichiers local, pratique pour les scripts qui attendent des chemins POSIX. | ```bash\n# monter le bucket S3 en local (Linux)\nsudo apt-get install s3fs\necho "$AWS_ACCESS_KEY_ID:$AWS_SECRET_ACCESS_KEY" > ~/.passwd-s3fs\nchmod 600 ~/.passwd-s3fs\ns3fs my-ml-data /mnt/ml-data -o allow_other -o iam_role=auto\n``` |

**Piège :** le “eventual consistency” de S3 peut entraîner la lecture d’une version antérieure immédiatement après un `PUT`. Utiliser `s3.wait_until_exists` ou attendre quelques secondes dans les pipelines critiques.

---

### 2.2 Versionnage des datasets avec DVC  

#### 2.2.1 Principes  

* DVC crée un fichier `.dvc` qui stocke le hash du fichier de données (SHA‑256) et les métadonnées (size, path).  
* Le fichier `.dvc` est versionné dans Git, les gros fichiers restent dans le remote (S3, Azure, GCS, ou un serveur SSH).  
* Chaque commit Git → snapshot complet du code **et** du jeu de données.

#### 2.2.2 Installation & configuration  

```bash
# pip install dvc[s3]  # ajoute le support S3
git init
dvc init
git commit -m "Initialisation DVC"
```

Remote S3 :

```bash
dvc remote add -d myremote s3://my-ml-data/dvc
dvc remote modify myremote access_key_id $AWS_ACCESS_KEY_ID
dvc remote modify myremote secret_access_key $AWS_SECRET_ACCESS_KEY
dvc remote modify myremote region us-east-1
```

#### 2.2.3 Exemple complet (commenté)  

```python
# file: data/download_raw.py
"""
Script de téléchargement des données brutes depuis une API publique,
stockage dans le répertoire `data/raw/` et versionnage DVC.
"""

import os
import requests
import hashlib
import subprocess
from pathlib import Path

RAW_DIR = Path("data/raw")
RAW_DIR.mkdir(parents=True, exist_ok=True)

URL = "https://archive.ics.uci.edu/ml/machine-learning-databases/iris/iris.data"
TARGET = RAW_DIR / "iris.csv"

def download():
    """Télécharge le fichier si absent ou si le hash a changé."""
    resp = requests.get(URL, timeout=10)
    resp.raise_for_status()
    data = resp.text.encode("utf-8")
    # calcul du hash pour détecter les changements
    new_hash = hashlib.sha256(data).hexdigest()

    if TARGET.exists():
        old_hash = hashlib.sha256(TARGET.read_bytes()).hexdigest()
        if old_hash == new_hash:
            print("Fichier déjà à jour.")
            return
    TARGET.write_bytes(data)
    print(f"Téléchargé → {TARGET}")

def dvc_add():
    """Ajoute le fichier dans DVC et commit Git."""
    subprocess.run(["dvc", "add", str(TARGET)], check=True)
    subprocess.run(["git", "add", f"{TARGET}.dvc", ".gitignore"], check=True)
    subprocess.run(
        ["git", "commit", "-m", "Add raw iris dataset (versioned with DVC)"],
        check=True,
    )
    # push vers le remote DVC (S3)
    subprocess.run(["dvc", "push"], check=True)

if __name__ == "__main__":
    download()
    dvc_add()
```

*Le script* :  
1. Télécharge le CSV uniquement s’il a changé (détection via SHA‑256).  
2. `dvc add` crée `iris.csv.dvc`.  
3. Le commit Git inclut le fichier `.dvc` et la mise à jour de `.gitignore`.  
4. `dvc push` transfère le fichier vers le remote S3.

#### 2.2.4 Récupérer un snapshot  

```bash
git checkout <commit_sha>          # positionner le repo sur le commit désiré
dvc pull                           # télécharge les artefacts manquants
```

**Piège :** si le remote DVC n’est pas configuré sur la machine de checkout, `dvc pull` échoue silencieusement. Toujours vérifier `dvc remote list` avant de récupérer.

---

### 2.3 Enregistrement des paramètres d’entraînement  

| Outil | Format | Avantages | Exemple |
|------|--------|-----------|---------|
| **MLflow** | JSON dans le `run` | UI web, recherche par tag, versionnage du modèle intégré | `mlflow.log_params({"lr":0.01,"batch_size":64})` |
| **Hydra** | YAML (configurable via CLI) | Héritage de configurations, composition dynamique | `python train.py model=resnet50 optimizer=adam` |
| **JSON/YAML** manuel | Aucun runtime | Simplicité, portable | `params.yaml` |

#### 2.3.

---

## Module 3 — contenu

## 3.1 Entraînement distribué – concepts fondamentaux  

| Concept | Description | Référence (vérifiable) |
|--------|-------------|------------------------|
| **Data‑parallelism** | Chaque réplique du modèle reçoit une portion du batch et calcule les gradients localement. Les gradients sont agrégés (All‑Reduce) avant la mise à jour du modèle. | Horovod (https://github.com/horovod/horovod) |
| **Model‑parallelism** | Le modèle est découpé en sous‑parties qui s’exécutent sur différents GPU/CPU. Utilisé rarement pour les modèles de classification classiques. | TensorFlow Strategy (https://www.tensorflow.org/guide/distributed_training) |
| **All‑Reduce** | Opération collective qui somme les gradients de chaque worker et redistribue le résultat à tous. Implémentations courantes : NCCL (GPU), Gloo (CPU). | NCCL (https://developer.nvidia.com/nccl) |
| **Job scheduler** | Orchestrateur qui crée les pods, alloue les ressources et injecte les variables d’environnement (RANK, WORLD_SIZE, …). | Kubernetes + Kubeflow Pipelines (https://www.kubeflow.org/docs/pipelines/) |
| **Checkpoint partagé** | Stockage persistant (ex. S3, GCS, PVC) où chaque worker écrit le même checkpoint afin de pouvoir reprendre l’entraînement. | DVC (https://dvc.org) |

> **Règle de base** : le code d’entraînement doit être *déterministe* à l’échelle du processus (seed fixe, synchronisation explicite) pour que les expériences soient reproductibles.

---

## 3.2 Implémentation d’un entraînement distribué avec PyTorch DDP et MLflow  

### 3.2.1 Architecture du conteneur  

```
.
├── Dockerfile                # multi‑stage, image finale = python:3.11‑slim
├── requirements.txt          # torch, torchvision, mlflow, boto3, gunicorn
├── src/
│   ├── train.py              # script d’entraînement (DDP)
│   └── utils.py              # fonctions de chargement de données, seed, logger
└── entrypoint.sh             # lance le script avec torchrun
```

### 3.2.2 Dockerfile (extrait)

```dockerfile
# ---------- build stage ----------
FROM python:3.11-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ---------- runtime stage ----------
FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY src/ src/
COPY entrypoint.sh .
ENV PYTHONPATH=/app/src
ENTRYPOINT ["./entrypoint.sh"]
```

### 3.2.3 `train.py` – entraînement DDP avec suivi MLflow  

```python
# src/train.py
import os
import argparse
import random
import numpy as np
import torch
import torch.nn as nn
import torch.distributed as dist
import torch.multiprocessing as mp
import torch.nn.functional as F
import torchvision
import torchvision.transforms as T
import mlflow
import mlflow.pytorch

# -------------------------------------------------
# 1️⃣  Fonctions utilitaires
# -------------------------------------------------
def set_seed(seed: int = 42):
    """Fixe les seeds dans tous les frameworks utilisés."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)

def get_data_loaders(batch_size: int, world_size: int, rank: int):
    """Dataset CIFAR‑10, partitionné par rang."""
    transform = T.Compose([
        T.RandomHorizontalFlip(),
        T.RandomCrop(32, padding=4),
        T.ToTensor(),
        T.Normalize((0.4914, 0.4822, 0.4465),
                    (0.2470, 0.2435, 0.2616)),
    ])
    train_set = torchvision.datasets.CIFAR10(
        root="/data", train=True, download=True, transform=transform
    )
    # Sampler distribué assure que chaque worker voit un sous‑ensemble exclusif
    sampler = torch.utils.data.distributed.DistributedSampler(
        train_set, num_replicas=world_size, rank=rank, shuffle=True
    )
    train_loader = torch.utils.data.DataLoader(
        train_set, batch_size=batch_size, sampler=sampler, num_workers=2, pin_memory=True
    )
    return train_loader

# -------------------------------------------------
# 2️⃣  Modèle simple (ResNet‑18 adapté)
# -------------------------------------------------
def build_model():
    model = torchvision.models.resnet18(pretrained=False, num_classes=10)
    return model

# -------------------------------------------------
# 3️⃣  Boucle d’entraînement
# -------------------------------------------------
def train_one_epoch(model, loader, optimizer, device, epoch, log_interval=100):
    model.train()
    running_loss = 0.0
    for batch_idx, (data, target) in enumerate(loader):
        data, target = data.to(device), target.to(device)

        optimizer.zero_grad()
        output = model(data)
        loss = F.cross_entropy(output, target)
        loss.backward()
        optimizer.step()

        running_loss += loss.item()
        if batch_idx % log_interval == 0:
            avg = running_loss / (batch_idx + 1)
            print(f"[Rank {dist.get_rank()}] Epoch {epoch} "
                  f"Batch {batch_idx}/{

---

## Module 4 — contenu

## 4.1 Architecture du service d’inférence  

| composant | rôle | technologie recommandée |
|-----------|------|--------------------------|
| **API** | point d’entrée HTTP/HTTPS, sérialisation JSON, validation Pydantic | **FastAPI** (Python 3.9+) |
| **Conteneur** | isolation, reproductibilité | Docker (multi‑stage) |
| **Orchestrateur** | planification, scaling, mise à jour | **Kubernetes** (v1.26+) |
| **Déploiement** | description déclarative, versionning | **Helm chart** |
| **Autoscaling** | adaptation dynamique à la charge | **Horizontal Pod Autoscaler (HPA)** basé sur CPU, mémoire et latence custom |
| **Ingress** | routage externe, TLS termination | **NGINX Ingress Controller** ou **Traefik** |
| **Monitoring** | métriques d’inférence, traces, alertes | **Prometheus exporter** + **OpenTelemetry SDK** + **Grafana** |
| **Observabilité du modèle** | version, hash, paramètres | **MLflow Model Registry** (optionnel) |

---

## 4.2 Implémentation d’une API d’inférence avec FastAPI  

```python
# file: app/main.py
import json
import os
from pathlib import Path
from typing import List

import joblib  # ou torch, tensorflow selon le modèle
import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, validator
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

# -------------------------------------------------
# 1️⃣  Modèle de requête / réponse (Pydantic)
# -------------------------------------------------
class Sample(BaseModel):
    """Une observation à scorer."""
    features: List[float] = Field(..., description="Vecteur de features numériques")
    
    @validator("features")
    def check_dim(cls, v):
        if len(v) != 4:  # ex. modèle entraîné sur 4 colonnes
            raise ValueError("Le vecteur doit contenir exactement 4 valeurs")
        return v

class Prediction(BaseModel):
    """Résultat de l’inférence."""
    label: int
    probability: float
    model_version: str

# -------------------------------------------------
# 2️⃣  Métriques Prometheus
# -------------------------------------------------
REQUEST_COUNT = Counter(
    "inference_requests_total",
    "Nombre total de requêtes d’inférence",
    ["endpoint"]
)
REQUEST_LATENCY = Histogram(
    "inference_request_duration_seconds",
    "Latence d’une requête d’inférence",
    ["endpoint"]
)

# -------------------------------------------------
# 3️⃣  Chargement du modèle (singleton)
# -------------------------------------------------
MODEL_PATH = Path(os.getenv("MODEL_PATH", "/app/model/model.joblib"))
if not MODEL_PATH.is_file():
    raise FileNotFoundError(f"Modèle introuvable : {MODEL_PATH}")

model = joblib.load(MODEL_PATH)               # ou torch.load, tf.keras.models.load_model
model_version = os.getenv("MODEL_VERSION", "unknown")

# -------------------------------------------------
# 4️⃣  Création de l’application FastAPI
# -------------------------------------------------
app = FastAPI(
    title="Inference Service",
    version="1.0.0",
    description="API RESTful pour scorer des observations"
)

# -------------------------------------------------
# 5️⃣  End‑point d’inférence
# -------------------------------------------------
@app.post("/predict", response_model=Prediction, tags=["inference"])
def predict(sample: Sample):
    REQUEST_COUNT.labels(endpoint="/predict").inc()
    with REQUEST_LATENCY.labels(endpoint="/predict").time():
        # 5.1 Pré‑traitement minimal (exemple : reshape)
        X = np.array(sample.features).reshape(1, -1)

        # 5.2 Prédiction
        try:
            proba = model.predict_proba(X)[0, 1]          # probabilité classe 1
            label = int(proba >= 0.5)
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc))

        return Prediction(
            label=label,
            probability=round(float(proba), 4),
            model_version=model_version,
        )

# -------------------------------------------------
# 6️⃣  Endpoint métriques Prometheus
# -------------------------------------------------
@app.get("/metrics", include_in_schema=False)
def metrics():
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )
```

**Points clés du code**  

* `Sample` valide la dimension du vecteur d’entrée ; la validation s’effectue avant l’appel à la fonction de prédiction.  
* Les métriques `REQUEST_COUNT` et `REQUEST_LATENCY` sont exposées via `/metrics` ; Prometheus scrappe ce endpoint.  
* Le modèle est chargé **une seule fois** au démarrage du conteneur (singleton) ; éviter le re‑chargement à chaque requête.  
* `MODEL_PATH` et `MODEL_VERSION` sont injectés par variables d’environnement ; ils seront définis dans le Helm chart.  

---

## 4.3 Dockerfile multi‑stage  

```dockerfile
# ---------- Stage 1 : Build ----------
FROM python:3.11-slim AS builder

# 1️⃣ Installation des dépendances de build
RUN apt-get update && apt-get install -y --no-install-recommends gcc && \
    rm -rf /var/lib/apt/lists/*

# 2️⃣ Copie du fichier de dépendances
COPY requirements.txt /tmp/
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r /tmp/requirements.txt && \
    pip install --no-cache-dir gunicorn  # serveur d’application

# ---------- Stage 2 : Runtime ----------
FROM python:3.11-slim AS runtime

# 3️⃣ Copie des paquets Python depuis le builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr

---

## Module 5 — contenu

## Module 5 – Surveillance, gouvernance et mise à jour continue  

### 5.1 Collecte de métriques de performance et de dérive  

| Métrique | Source | Outil recommandé | Commentaire |
|----------|--------|------------------|-------------|
| **Précision / Recall / F1** | API inference (payload → prédiction) | **Evidently AI** – `Report` ou `Dashboard` | Calculé sur un *sample* de requêtes réelles (ex. 10 % du trafic) pour éviter la surcharge. |
| **Distribution des features** | Data lake (S3, GCS) ou base de features | **Evidently AI** – `DataDrift` | Compare la distribution du jeu de production (`current`) à la distribution du jeu d’entraînement (`reference`). |
| **Score de dérive (KS, PSI)** | Calculé sur les features clés | **NannyML** – `DriftCalculator` | PSI < 0,1 : stable, 0,1‑0,25 : attention, > 0,25 : alerte. |
| **Latency / Throughput** | Exporter les métriques de l’API (Prometheus) | **Prometheus** + **Grafana** | Histogrammes `http_request_duration_seconds` et `http_requests_total`. |
| **Erreur d’inférence (exceptions, time‑outs)** | Middleware d’API | **OpenTelemetry** – traces + **Prometheus** counter | Un taux d’erreur > 1 % déclenche une alerte. |

#### 5.1.1 Exemple de pipeline de surveillance avec Evidently AI  

```python
# fichier: monitor/evidently_report.py
import pandas as pd
from evidently.dashboard import Dashboard
from evidently.tabs import DataDriftTab, ClassificationPerformanceTab
import joblib
import os
import json
from datetime import datetime

# -------------------------------------------------------------------------
# 1. Chargement du jeu de référence (les features d'entraînement)
# -------------------------------------------------------------------------
REF_PATH = os.getenv("EVIDENTLY_REF_PATH", "/data/reference.parquet")
reference_df = pd.read_parquet(REF_PATH)

# 2. Chargement du jeu de production (extrait quotidien depuis le data lake)
CURR_PATH = os.getenv("EVIDENTLY_CURR_PATH", "/data/current.parquet")
current_df = pd.read_parquet(CURR_PATH)

# 3. Colonnes cibles et prédictions (déjà présentes dans les deux jeux)
TARGET_COL = "label"
PRED_COL   = "prediction"

# -------------------------------------------------------------------------
# 4. Construction du tableau de bord
# -------------------------------------------------------------------------
dashboard = Dashboard(tabs=[
    DataDriftTab(),
    ClassificationPerformanceTab()
])

dashboard.calculate(reference_df, current_df,
                    column_mapping={
                        "target": TARGET_COL,
                        "prediction": PRED_COL,
                        # on peut préciser les colonnes catégorielles si besoin
                    })

# 5. Export du rapport HTML (pour visualisation manuelle)
out_html = f"/reports/evidently_{datetime.utcnow().isoformat()}.html"
dashboard.save(out_html)

# 6. Export JSON des métriques critiques (pour alerting automatisé)
metrics = dashboard.get_summary()
summary_path = "/metrics/evidently_summary.json"
with open(summary_path, "w") as f:
    json.dump(metrics, f, indent=2)

print(f"✅ Evidently report généré : {out_html}")
print(f"🔎 Métriques résumées écrites dans {summary_path}")
```

*Points de vérification*  

- Les deux DataFrames doivent contenir **exactement** les mêmes colonnes (ou un sous‑ensemble).  
- `target` et `prediction` doivent être de type **int** ou **str** compatible avec le modèle.  
- Le fichier JSON produit contient les clés `data_drift` → `drift_score` et `classification_performance` → `accuracy`.  

---

### 5.2 Alerting avec Alertmanager et Slack  

1. **Exporter les métriques** depuis le job de monitoring (ex. le script précédent) vers Prometheus via le **pushgateway** ou un exporter HTTP.  
2. **Règle d’alerte** dans `alert.rules.yml` :

```yaml
groups:
- name: model_drift
  rules:
  - alert: ModelDataDrift
    expr: evidently_data_drift_drift_score > 0.25
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "Dérive de données détectée sur le modèle {{ $labels.model_name }}"
      description: |
        Le score de dérive (PSI) a dépassé 0.25 pendant 5 minutes.
        Consultez le tableau de bord Evidently : {{ $labels.dashboard_url }}
```

3. **Receiver Slack** dans `alertmanager.yml` :

```yaml
receivers:
- name: slack-notifications
  slack_configs:
  - api_url: https://hooks.slack.com/services/TXXXX/BXXXX/XXXXXXXX
    channel: '#mlops-alerts'
    title: "{{ .CommonAnnotations.summary }}"
    text: "{{ .CommonAnnotations.description }}"
```

4. **Reload** Alertmanager (`curl -X POST http://alertmanager:9093/-/reload`).  

#### Pièges courants  

| Situation | Pourquoi c’est un problème | Solution |
|-----------|----------------------------|----------|
| **Métriques non pushées** | Le job de monitoring ne pousse pas de données → aucune alerte. | Vérifier le statut du pushgateway (`curl http://pushgateway:9091/metrics`). |
| **Labels manquants** | Alertmanager ne trouve pas `model_name` ou `dashboard_url`. | Ajouter les labels dans le job Prometheus (`metric{model_name="my_model",dashboard_url="http://..."} 1`). |
| **Alertes en boucle** | La même alerte se déclenche chaque minute. | Utiliser `for: 5m` (ou plus) et `resolve_timeout` dans Alertmanager. |
| **Slack rate‑limit** | Trop d’alertes en peu de temps → messages bloqués. | Configurer `group_wait`, `