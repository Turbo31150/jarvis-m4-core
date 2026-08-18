# DevOps IA & CI/CD Intelligent

> Référence `ia-devops` · 69 €

## Plan

## Module 1 – Provisionnement d’infrastructures IA avec IaC  
**Objectif d’apprentissage :** Déployer, à l’aide de Terraform ou AWS CloudFormation, une stack reproducible (GPU, stockage d’objets, réseau) et valider que le script s’exécute sans erreur sur deux fournisseurs cloud différents.  
**Notions couvertes**  
- Syntaxe HCL et modules Terraform ; utilisation de `terraform validate` et `terraform plan`.  
- Templates CloudFormation (YAML/JSON) ; fonctions intrinsèques `Fn::GetAtt`, `Fn::Join`.  
- Gestion des variables d’environnement et secrets avec HashiCorp Vault ou AWS Secrets Manager.  
- Provisionnement de nœuds GPU via le provider `aws_instance` ou `google_compute_instance`.  
- Stratégies de state locking (Terraform Cloud, DynamoDB) et de drift detection.

---

## Module 2 – Versionnage et traçabilité des données et modèles  
**Objectif d’apprentissage :** Implémenter un workflow DVC qui lie chaque commit Git à un snapshot de jeu de données et à un artefact de modèle, et démontrer la capacité à reproduire un entraînement à partir d’un tag Git.  
**Notions couvertes**  
- Installation et configuration de DVC ; fichiers `.dvc` et `.dvcignore`.  
- Remote storage (S3, GCS, Azure Blob) et authentification via IAM.  
- Métriques et visualisation avec `dvc metrics` et `dvc plots`.  
- Intégration de MLflow pour le tracking des hyper‑paramètres et des artefacts.  
- Gestion des conflits de version de données (merge, rebase) dans un dépôt Git partagé.

---

## Module 3 – Pipelines CI/CD pour l’entraînement et le déploiement de modèles  
**Objectif d’apprentissage :** Construire un pipeline GitHub Actions (ou Jenkins) qui exécute les étapes suivantes : linting du code Python, tests unitaires, entraînement d’un modèle, création d’une image Docker contenant le modèle, et déploiement automatisé sur un cluster Kubernetes.  
**Notions couvertes**  
- Fichiers de workflow YAML ; déclencheurs `push`, `pull_request`, `workflow_dispatch`.  
- Utilisation de `actions/cache` pour accélérer les étapes d’entraînement.  
- Construction d’images Docker multi‑stage pour réduire la taille finale.  
- Publication d’artefacts dans un registre privé (GitHub Packages, Harbor).  
- Déploiement via `kubectl apply` ou Helm chart, avec variables d’environnement injectées par le pipeline.

---

## Module 4 – Monitoring, observabilité et gouvernance des modèles en production  
**Objectif d’apprentissage :** Configurer la collecte de métriques (latence, taux d

---

## Module 1 — contenu

## 1. Provisionnement d’infrastructures IA avec IaC  

### 1.1 Concepts fondamentaux  

| Concept | Description vérifiable |
|---------|------------------------|
| **Infrastructure as Code (IaC)** | Déclaration de l’infrastructure dans des fichiers versionnés. Terraform utilise le **HashiCorp Configuration Language (HCL)**, CloudFormation utilise **YAML/JSON**. |
| **Provider** | Plugin qui traduit le DSL en appels API du cloud. Ex. `aws`, `google`. |
| **State** | Terraform stocke l’état réel de la stack dans un fichier (`terraform.tfstate`). Il doit être partagé et verrouillé pour éviter les corruptions. |
| **Drift detection** | Comparaison entre l’état déclaré et l’état réel. Terraform : `terraform plan -detailed-exitcode`. CloudFormation : `aws cloudformation detect-stack-drift`. |
| **Secrets** | Ne jamais placer de clés d’accès en clair. Utiliser **Vault** ou **AWS Secrets Manager** et référencer via variables d’environnement ou `data` sources. |

---

### 1.2 Terraform – Déploiement d’une stack GPU sur AWS et GCP  

#### 1.2.1 Structure du répertoire  

```
infra/
├── modules/
│   └── gpu_node/
│       ├── main.tf
│       ├── variables.tf
│       └── outputs.tf
├── env/
│   ├── aws/
│   │   ├── backend.tf
│   │   └── terraform.tfvars
│   └── gcp/
│       ├── backend.tf
│       └── terraform.tfvars
└── main.tf
```

#### 1.2.2 `modules/gpu_node/main.tf` (exemple fonctionnel, commenté)

```hcl
# ---------- Provider ----------
provider "aws" {
  # Le provider est chargé uniquement si le bloc est présent dans le workspace
  region = var.aws_region
}

provider "google" {
  project = var.gcp_project
  region  = var.gcp_region
}

# ---------- Variables ----------
variable "cloud" {
  description = "Target cloud provider: \"aws\" ou \"gcp\""
  type        = string
}

variable "instance_type" {
  description = "Type d'instance GPU"
  type        = string
  default     = "p3.2xlarge"   # AWS
}

variable "gpu_count" {
  description = "Nombre de GPU à attacher"
  type        = number
  default     = 1
}

# ---------- AWS GPU Instance ----------
resource "aws_instance" "gpu" {
  count = var.cloud == "aws" ? 1 : 0

  ami           = data.aws_ami.ubuntu.id
  instance_type = var.instance_type
  subnet_id     = data.aws_subnet_ids.default.ids[0]

  # Attachement du volume SSD NVMe (gp3) pour les datasets
  root_block_device {
    volume_size = 100
    volume_type = "gp3"
    iops        = 3000
  }

  # Tag obligatoire pour le drift detection via CloudWatch
  tags = {
    Name = "ai-gpu-node"
    Env  = var.environment
  }

  # Utilisation du rôle IAM géré
  iam_instance_profile = aws_iam_instance_profile.gpu_profile.name
}

# ---------- GCP GPU Instance ----------
resource "google_compute_instance" "gpu" {
  count = var.cloud == "gcp" ? 1 : 0

  name         = "ai-gpu-node"
  machine_type = "n1-standard-8"
  zone         = var.gcp_zone

  # Ajout d’un GPU NVIDIA Tesla T4
  guest_accelerator {
    type  = "nvidia-tesla-t4"
    count = var.gpu_count
  }

  boot_disk {
    initialize_params {
      image = "projects/ubuntu-os-cloud/global/images/ubuntu-2204-jammy-v20240812"
      size  = 100
      type  = "pd-ssd"
    }
  }

  network_interface {
    network = "default"
    access_config {}
  }

  service_account {
    email  = google_service_account.gpu.email
    scopes = ["cloud-platform"]
  }

  tags = ["ai-gpu-node"]
}

# ---------- Data sources ----------
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical
  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }
}

data "aws_subnet_ids" "default" {
  vpc_id = data.aws_vpc.default.id
}

data "aws_vpc" "default" {
  default = true
}
```

#### 1.2.3 Verrouillage du state avec DynamoDB (AWS)  

`infra/env/aws/backend.tf`

```hcl
terraform {
  backend "s3" {
    bucket         = "ai-terraform-state"
    key            = "aws/gpu-stack/terraform.tfstate"
    region         = "eu-west-1"
    dynamodb_table = "ai-terraform-lock"
    encrypt        = true
  }
}
```

*Création de la table DynamoDB (une fois) :*

```bash
aws dynamodb create-table \
  --table-name ai-terraform-lock \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region eu-west-1
```

#### 1.2.4 Validation et planification  

```bash
cd infra
terraform init          # télécharge les providers, configure le backend
terraform validate      # syntaxe HCL + type checking
terraform fmt -recursive # formatage standard
terraform plan -var 'cloud=aws' -out=tfplan.aws
terraform apply tfplan

---

## Module 2 — contenu

## 2.1. Mise en place du dépôt Git + DVC  

```bash
# 1. Crée le répertoire du projet
mkdir ai-project && cd ai-project

# 2. Initialise le dépôt Git
git init

# 3. Initialise DVC (crée .dvc/ et .dvcignore)
dvc init

# 4. Ajoute le .gitignore généré par DVC
git add .gitignore .dvc .dvcignore
git commit -m "Initialisation Git + DVC"
```

* `dvc init` crée un fichier de configuration `dvc.yaml` (vide) et le répertoire `.dvc/` contenant les métadonnées du cache.  
* Le fichier `.dvcignore` fonctionne comme `.gitignore` : les chemins listés ne seront pas ajoutés au cache DVC.

---

## 2.2. Configuration du remote de stockage  

```yaml
# dvc config - local (défaut) → stockage du cache dans .dvc/cache
dvc remote add -d storage s3://my-dvc-bucket/project
dvc remote modify storage region eu-west-3
dvc remote modify storage profile my-aws-profile   # utilise le profil AWS configuré
dvc remote modify storage credentialpath ~/.aws/credentials
```

* `-d` désigne le remote par défaut.  
* Le remote peut être S3, GCS (`gcs://bucket`) ou Azure Blob (`az://container`).  
* Les identifiants sont récupérés via le SDK du cloud ; ne jamais les coder en dur.

---

## 2.3. Versionner un jeu de données  

```bash
# 1. Télécharge le jeu de données (exemple : CIFAR‑10)
wget -O data/cifar-10.zip https://www.cs.toronto.edu/~kriz/cifar-10-python.tar.gz

# 2. Crée le répertoire de stockage brut
mkdir -p data/raw

# 3. Décompresse dans data/raw
tar -xzf data/cifar-10.zip -C data/raw

# 4. Track le répertoire avec DVC
dvc add data/raw

# 5. Commit les métadonnées (.dvc + .gitignore)
git add data/raw.dvc .gitignore
git commit -m "Track raw CIFAR‑10 dataset with DVC"
```

* `dvc add` calcule le hash SHA‑256 du contenu, crée un fichier `data/raw.dvc` contenant le chemin du cache et le checksum.  
* Le cache réel se trouve dans `.dvc/cache/<first‑2‑chars>/<remaining‑hash>`.

### 2.3.1. Pousser le cache vers le remote  

```bash
dvc push    # envoie uniquement les objets manquants sur le remote
git push    # envoie les commits Git (incluant les .dvc)
```

* `dvc push` utilise le remote configuré.  
* Si plusieurs développeurs travaillent, chaque `push` synchronise le même cache, évitant les duplications.

---

## 2.4. Versionner un modèle entraîné  

```python
# train.py
import argparse
import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score

def main(data_path, model_path, n_estimators):
    # 1. Charge les données pré‑traitées (CSV)
    df = pd.read_csv(data_path)
    X, y = df.drop("label", axis=1), df["label"]

    # 2. Entraîne le modèle
    clf = RandomForestClassifier(n_estimators=n_estimators, random_state=42)
    clf.fit(X, y)

    # 3. Sauvegarde le modèle (binary)
    joblib.dump(clf, model_path)

    # 4. Affiche la précision sur le même jeu (exemple simplifié)
    preds = clf.predict(X)
    print("accuracy:", accuracy_score(y, preds))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True, help="Chemin du CSV d'entraînement")
    parser.add_argument("--model", required=True, help="Chemin de sortie du modèle")
    parser.add_argument("--n_estimators", type=int, default=100)
    args = parser.parse_args()
    main(args.data, args.model, args.n_estimators)
```

```bash
# 1. Prépare les données (exemple simplifié)
python scripts/prepare.py --input data/raw --output data/processed/train.csv

# 2. Track le fichier CSV d'entraînement
dvc add data/processed/train.csv

# 3. Entraîne le modèle et crée le fichier .pkl
python train.py --data data/processed/train.csv --model models/rf.pkl --n_estimators 200

# 4. Track le modèle
dvc add models/rf.pkl

# 5. Commit les métadonnées
git add data/processed/train.csv.dvc models/rf.pkl.dvc dvc.yaml
git commit -m "Add training data and RandomForest model v1"
```

* Le fichier `dvc.yaml` généré contient les étapes du pipeline :

```yaml
stages:
  prepare:
    cmd: python scripts/prepare.py --input data/raw --output data/processed/train.csv
    deps:
      - data/raw
      - scripts/prepare.py
    outs:
      - data/processed/train.csv
  train:
    cmd: python train.py --data data/processed/train.csv --model models/rf.pkl --n_estimators 200
    deps:
      - data/processed/train.csv
      - train.py
    outs:
      - models/rf.pkl
```

---

## 2.5. Reproduire un entraînement à partir d’un tag Git  

```bash

---

## Module 3 — contenu

## 3.1 Architecture du pipeline

| Étape | Action | Artefact produit | Environnement |
|------|--------|-------------------|--------------|
| **Linting** | `ruff` (ou `flake8`) | Aucun | `python:3.11-slim` |
| **Tests unitaires** | `pytest` avec couverture | Rapport `coverage.xml` | `python:3.11-slim` |
| **Entraînement** | Script `train.py` → modèle `model.pkl` | Modèle + métriques (`metrics.json`) | Image Docker **build‑time** (GPU optionnel) |
| **Construction Docker** | Dockerfile multi‑stage → image `myorg/model:sha` | Image Docker | Docker Engine (GitHub Runner) |
| **Push registre** | `docker push` vers GitHub Packages / Harbor | Tag `sha` | Docker login avec secret |
| **Déploiement** | `helm upgrade --install` ou `kubectl apply` | Release Kubernetes | Cluster reachable via `KUBECONFIG` secret |

Le pipeline doit être **déclaratif** (GitHub Actions) et **idempotent** : chaque run part du même état (`git checkout`, `actions/cache`, `terraform init` si infra‑as‑code est impliquée).

---

## 3.2 Fichier de workflow GitHub Actions

```yaml
# .github/workflows/ci-cd.yml
name: CI‑CD modèle IA

on:
  push:
    branches: [ main ]
    tags: [ 'v*.*.*' ]          # déclenche le déploiement en prod
  pull_request:
    branches: [ main ]
  workflow_dispatch: {}        # lancement manuel

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}/model
  # Le tag sera le SHA court du commit ou le tag Git (ex: v1.2.3)
  IMAGE_TAG: ${{ github.sha }}

jobs:
  lint-test:
    name: Lint & tests
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Cache pip
        uses: actions/cache@v3
        with:
          path: ~/.cache/pip
          key: pip-${{ runner.os }}-${{ hashFiles('requirements.txt') }}
          restore-keys: pip-${{ runner.os }}-

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install deps
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install ruff pytest pytest-cov

      - name: Lint code
        run: ruff check src/

      - name: Run unit tests with coverage
        run: |
          pytest -q --cov=src --cov-report=xml
        continue-on-error: false

      - name: Upload coverage report
        uses: actions/upload-artifact@v3
        with:
          name: coverage
          path: coverage.xml

  train-and-build:
    name: Entraînement & image Docker
    needs: lint-test
    runs-on: ubuntu-latest
    # GPU optionnel – décommentez si le runner possède un GPU
    # runs-on: [self-hosted, linux, gpu]
    env:
      MODEL_DIR: model_artifacts
    steps:
      - uses: actions/checkout@v4

      - name: Cache Docker layers
        uses: actions/cache@v3
        with:
          path: /tmp/.buildx-cache
          key: docker-${{ runner.os }}-${{ github.sha }}
          restore-keys: docker-${{ runner.os }}-

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v2

      - name: Login to registry
        uses: docker/login-action@v2
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Build & train (stage 1)
        # Dockerfile utilise un premier stage "builder" qui lance l'entraînement.
        run: |
          docker buildx build \
            --target builder \
            --output type=local,dest=${{ env.MODEL_DIR }} \
            --cache-from type=local,src=/tmp/.buildx-cache \
            --cache-to type=local,dest=/tmp/.buildx-cache,mode=max \
            .

      - name: Verify model artefacts
        run: |
          ls -l ${{ env.MODEL_DIR }}
          test -f ${{ env.MODEL_DIR }}/model.pkl
          test -f ${{ env.MODEL_DIR }}/metrics.json

      - name: Build final image (stage 2)
        run: |
          docker buildx build \
            --target runtime \
            --tag ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ env.IMAGE_TAG }} \
            --push \
            --cache-from type=local,src=/tmp/.buildx-cache \
            .

  deploy:
    name: Déploiement Kubernetes
    needs: train-and-build
    runs-on: ubuntu-latest
    if: github.ref_type == 'tag'   # uniquement sur les tags versionnés
    steps:
      - uses: actions/checkout@v4

      - name: Set up kubectl
        uses: azure/setup-kubectl@v3
        with:
          version: 'v1.27.0'

      - name: Kubeconfig
        run: |
          echo "${{ secrets.KUBECONFIG }}" > $HOME/.kube/config
          chmod 600 $HOME/.kube

---

## Module 4 — contenu

## Module 4 – Monitoring, observabilité et gouvernance des modèles en production  

### 4.1 Principes de monitoring IA  

| Aspect | Métrique typique | Source de données | Niveau |
|--------|------------------|-------------------|--------|
| **Performance** | Latence (ms), débit (req/s) | Service mesh (Istio), Prometheus exporter | Runtime |
| **Qualité du modèle** | Drift de distribution (KS, Wasserstein), précision en ligne, taux d’erreur | Feature store, logs d’inférence, DVC/MLflow tracking | Runtime + post‑déploiement |
| **Ressources** | CPU, GPU utilisation, mémoire, I/O | cAdvisor, node‑exporter | Runtime |
| **Sécurité & conformité** | Accès non‑autorisé, logs d’audit, chiffrement | OPA, auditd, CloudTrail | Ops |
| **Business** | Taux de conversion, churn, revenu / utilisateur | Data warehouse, BI | Business |

> **Règle 1** : chaque métrique doit être *SLA‑compatible* (ex. latence ≤ 200 ms 99 % du temps).  
> **Règle 2** : les métriques de qualité du modèle sont calculées sur des *datasets de référence* versionnés (ex. `data/reference/v1.2/`).

### 4.2 Architecture de collecte  

```
┌─────────────────────┐   scrape   ┌─────────────────────┐
│  Application (API)  │◀──────────▶│  Prometheus Server  │
│  (FastAPI, Flask)   │            │  (scrape /metrics)  │
└─────────┬───────────┘            └───────┬─────────────┘
          │                               │
          ▼                               ▼
   ┌───────────────┐                 ┌───────────────┐
   │  Exporter     │                 │  Alertmanager │
   │ (custom)      │                 │  (alert rules)│
   └───────┬───────┘                 └───────┬───────┘
           │                                 │
           ▼                                 ▼
   ┌─────────────────────┐          ┌─────────────────────┐
   │ Grafana Dashboard   │          │ Slack / PagerDuty   │
   └─────────────────────┘          └─────────────────────┘
```

* **Exporter custom** : expose les métriques spécifiques au modèle (ex. `model_prediction_drift`).  
* **Prometheus** : base temporelle, stockage 15 jours par défaut, `remote_write` vers Cortex/Thanos si besoin de rétention longue.  
* **Alertmanager** : règles d’alerte basées sur seuils SLA ou drift.  

### 4.3 Implémentation d’un exporter Prometheus pour le drift  

```python
# file: exporter/model_drift_exporter.py
"""
Exporter Prometheus qui calcule le drift entre les features d’entrée
actuelles et la distribution de référence stockée dans un bucket S3.
Utilise scipy.stats.ks_2samp pour le test de Kolmogorov‑Smirnov.
"""

from prometheus_client import start_http_server, Gauge
import boto3, json, os, time
from scipy.stats import ks_2samp
import numpy as np

# Métriques exposées
DRIFT_SCORE = Gauge(
    "model_feature_ks_drift",
    "Kolmogorov‑Smirnov distance entre feature distribution en production et référence",
    ["feature"]
)

# Configuration
REF_BUCKET = os.getenv("REF_BUCKET", "ml-reference-data")
REF_KEY    = os.getenv("REF_KEY", "features/reference.json")
EXPORTER_PORT = int(os.getenv("EXPORTER_PORT", 8000))
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", 300))  # seconds

s3 = boto3.client("s3")

def load_reference():
    """Charge le dictionnaire {feature: list(values)} depuis S3."""
    obj = s3.get_object(Bucket=REF_BUCKET, Key=REF_KEY)
    payload = obj["Body"].read()
    return json.loads(payload)

def fetch_live_features():
    """
    Simule la récupération des dernières 10 000 valeurs de chaque feature
    depuis un topic Kafka ou une base de logs. Ici on génère aléatoirement
    pour l’exemple.
    """
    np.random.seed(int(time.time()) // POLL_INTERVAL)  # variation chaque poll
    return {
        "age":   np.random.normal(35, 10, size=10000).tolist(),
        "income": np.random.lognormal(10, 2, size=10000).tolist(),
    }

def compute_and_report(ref, live):
    """Calcule le KS‑statistic et met à jour la gauge."""
    for feat, ref_vals in ref.items():
        live_vals = live.get(feat, [])
        if not live_vals:
            continue
        ks_stat, _ = ks_2samp(ref_vals, live_vals)
        DRIFT_SCORE.labels(feature=feat).set(ks_stat)

def main():
    start_http_server(EXPORTER_PORT)
    while True:
        try:
            reference = load_reference()
            live = fetch_live_features()
            compute_and_report(reference, live)
        except Exception as exc:
            # En production, pousser l’erreur vers un logger central
            print(f"[ERROR] {exc}")
        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    main()
```

**Explications du code**  

| Ligne | Pourquoi |
|------|----------|
| `Gauge` | Choix d’une métrique monotone (0 ≤ KS ≤ 1). |
| `load_reference` | Utilise le même format que le pipeline d’entraînement : JSON sérialisé depuis S3, versionné via le tag Git du modèle. |
| `fetch_live_features` | En production remplacer par une requête à un data lake (ex. Athena) ou à un topic Kafka. |
| `ks_2samp` | Test

---

## Module 5 — contenu

## Module 5 – Déploiement canary, rollback automatisé et gouvernance des modèles en production  

### 5.1 Principes de déploiement progressif  

| Type | Description | Outils courants | Points de contrôle |
|------|-------------|-----------------|---------------------|
| **Blue‑Green** | Deux environnements (blue = production, green = nouvelle version). Le basculement se fait en une seule opération `kubectl apply` sur le service. | Kubernetes Service, Helm, Seldon Core | Temps d’arrêt = 0, test de santé complet avant bascule. |
| **Canary** | Le trafic est réparti progressivement (ex. 5 % → 100 %) entre la version courante et la version candidate. Le monitoring décide du passage à l’étape suivante. | Argo Rollouts, Istio VirtualService, Flagger, Seldon Core | Métriques de latence, taux d’erreur, KPI métier. |
| **A/B testing** | Deux versions co‑existent, chaque groupe d’utilisateurs reçoit un traitement différent. Les résultats sont agrégés pour comparaison statistique. | Feature flags (LaunchDarkly, Unleash), Istio, Seldon Core | Taille d’échantillon, intervalle de confiance, plan d’expérience. |

#### 5.1.1 Pourquoi le canary est privilégié en MLOps  

* **Risque limité** : une mauvaise prédiction n’affecte qu’une fraction du trafic.  
* **Détection précoce du drift** : les métriques de performance (ex. RMSE, précision) sont observées en temps réel.  
* **Rollback instantané** : la configuration Istio/Argo permet de revenir à 100 % de la version stable en une seconde.  

### 5.2 Architecture de référence  

```mermaid
graph LR
    subgraph K8s Cluster
        A[Ingress (Istio Gateway)] --> B[VirtualService]
        B -->|50 %| C[Deployment v1 (Seldon Model)]
        B -->|50 %| D[Deployment v2 (Seldon Model)]
        C --> E[Prometheus Exporter]
        D --> E
    end
    E --> F[Prometheus]
    F --> G[Grafana]
    F --> H[Argo Rollout Controller]
    H -->|rollback| C
```

* **Istio** gère le routage du trafic (`VirtualService`).  
* **Seldon Core** expose chaque version comme un micro‑service compatible le protocole Seldon.  
* **Prometheus** scrappe les métriques `seldon_core_request_duration_seconds`, `seldon_core_success_total`.  
* **Argo Rollout** orchestre les étapes canary en lisant les métriques via l’API Prometheus.  

### 5.3 Exemple complet : Canary avec Seldon + Istio + Argo Rollouts  

#### 5.3.1 Déploiement Seldon (v1) – modèle stable  

```yaml
# file: seldon-model-v1.yaml
apiVersion: machinelearning.seldon.io/v1
kind: SeldonDeployment
metadata:
  name: sentiment-analyzer
spec:
  name: sentiment-analyzer
  predictors:
  - name: default
    replicas: 2
    graph:
      name: classifier
      implementation: SKLEARN_SERVER
      modelUri: "gs://my-bucket/models/v1/"
    traffic: 100  # % du trafic initial
```

* `modelUri` pointe vers un bucket GCS (ou S3) contenant le modèle pickled.  
* `traffic: 100` indique que la version v1 reçoit tout le trafic tant qu’aucune version canary n’est déclarée.  

#### 5.3.2 Déploiement Seldon (v2) – modèle candidate  

```yaml
# file: seldon-model-v2.yaml
apiVersion: machinelearning.seldon.io/v1
kind: SeldonDeployment
metadata:
  name: sentiment-analyzer-canary
spec:
  name: sentiment-analyzer
  predictors:
  - name: canary
    replicas: 1
    graph:
      name: classifier
      implementation: SKLEARN_SERVER
      modelUri: "gs://my-bucket/models/v2/"
    traffic: 0   # initialement 0 % (géré par Argo)
```

#### 5.3.3 VirtualService Istio – routage initial  

```yaml
# file: sentiment-virtualservice.yaml
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: sentiment-analyzer
spec:
  hosts:
  - sentiment-analyzer.default.svc.cluster.local
  http:
  - route:
    - destination:
        host: sentiment-analyzer-default
        subset: v1
      weight: 100
    - destination:
        host: sentiment-analyzer-canary
        subset: v2