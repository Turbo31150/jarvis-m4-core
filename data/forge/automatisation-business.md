# Automatisation Business IA

> Référence `automatisation-business` · 69 €

## Plan

# Automatisation Business IA (réf. automatisation-business, 69 €)

## Module 1 – Architecture d’une solution d’automatisation IA pour les processus métier  
**Objectif mesurable** : Concevoir, documenter et valider l’architecture technique d’une solution d’automatisation IA répondant à un cas d’usage métier, avec diagrammes (BPMN, C4) et spécifications d’interfaçage d’ici la fin de la session.  

- Analyse fonction

---

## Module 1 — contenu

## 1. Analyse fonctionnelle du cas d’usage  

| Élément | Description | Livrable attendu |
|--------|-------------|------------------|
| **Processus métier** | Exemple : traitement automatisé des demandes de remboursement de frais de déplacement. | Modèle BPMN du flux “Demande de remboursement”. |
| **Acteurs** | - Employé (initiateur)<br>- Système comptable (ERP)<br>- Service RH (validation)<br>- IA de classification (extraction de pièces justificatives) | Diagramme de séquence ou tableau RACI. |
| **Entrées** | Formulaire web (JSON), pièces jointes (PDF, images). | Spécifications d’API d’entrée (REST POST `/remboursement`). |
| **Sorties** | - Enregistrement dans l’ERP (transaction comptable).<br>- Notification par mail.<br>- Tableau de bord de suivi. | Spécifications d’API de sortie (REST PUT `/erp/transaction`, SMTP). |
| **Contraintes** | - Confidentialité (RGPD) : chiffrement des pièces jointes.<br>- Temps de traitement ≤ 5 min.<br>- Traçabilité (audit log). | Matrice de conformité. |

> **Livrable de la phase d’analyse** : Document *Functional‑Spec.pdf* contenant le tableau ci‑dessus, le diagramme BPMN (Mermaid) et les exigences non fonctionnelles.

```mermaid
flowchart TD
    A[Employé] -->|Soumet formulaire| B[API Front (REST)]
    B --> C{IA Extraction}
    C -->|Texte brut| D[Service OCR (Tesseract)]
    C -->|Métadonnées| E[Classifieur ML (sklearn)]
    D --> F[Stockage S3 (chiffré)]
    E --> G[Base de données PostgreSQL]
    F --> H[Trigger Lambda → Validation RH]
    G --> H
    H -->|Validé| I[Appel ERP (REST PUT)]
    H -->|Rejeté| J[Mail de refus]
    I --> K[Notification employé]
```

---

## 2. Architecture technique (C4 – Niveau 1 & 2)

### 2.1 Vue système (C4‑Level 1)

```
+-------------------+          +-------------------+          +-------------------+
|   Front‑end UI    |  HTTPS   |   API Gateway     |  gRPC/   |   ERP (SAP)       |
| (React/Angular)  |<-------> | (AWS API GW)      |<-------> | (Comptabilité)    |
+-------------------+          +-------------------+          +-------------------+
           |                           |
           |  JSON/Multipart           |  Lambda (Node.js)   |
           v                           v
+-------------------+          +-------------------+          +-------------------+
|   Service d’OCR   |  S3 (chiffré)  |   Service ML   |  RDS (PostgreSQL) |
| (Tesseract + λ)  |<------------>| (sklearn + λ)  |<-------------------|
+-------------------+               +-------------------+
```

* **API Gateway** : point d’entrée unique, gestion du throttling, WAF, authentification OAuth 2.0.  
* **Lambda 1 (Ingestion)** : réception du POST, validation du schéma JSON, stockage temporaire S3.  
* **Lambda 2 (OCR)** : déclenché par l’événement S3, invoque Tesseract via container Docker, renvoie le texte brut.  
* **Lambda 3 (Classification)** : charge le modèle `sklearn` (RandomForest) depuis S3, prédit le type de dépense, enrichit les métadonnées.  
* **RDS PostgreSQL** : persistance des métadonnées, audit log (trigger `INSERT` → table `audit`).  
* **Service de validation** : UI interne (React) + API REST, décision manuelle ou règle métier (ex. plafond = 500 €).  
* **ERP** : appel `PUT /remboursement/{id}` via API interne, transaction atomique.  
* **Notification** : SNS → Lambda 4 (Mail) → SES (SMTP).  

### 2.2 Diagramme de conteneur (C4‑Level 2) – Mermaid

```mermaid
graph LR
    subgraph Front
        UI[UI Web] -->|HTTPS| GW[API Gateway]
    end
    subgraph Cloud
        GW -->|REST| L1[Lambda Ingestion]
        L1 --> S3[(S3 Bucket chiffré)]
        S3 -->|Event| L2[Lambda OCR]
        L2 --> OCR[Tesseract (Docker)]
        L2 -->|Texte| L3[Lambda Classification]
        L3 --> ML[Modèle RandomForest]
        L3 --> DB[(PostgreSQL RDS)]
        DB -->|Audit| LOG[Table audit]
        L3 -->|Métadonnées| VAL[Service Validation UI]
        VAL -->|Decision| ERP[ERP SAP]
        ERP -->|Ack| NOTIF[SNS + SES]
    end
```

---

## 3. Spécifications d’interfaçage  

| Interface | Protocole | Payload | Sécurité | Exemple de contrat (OpenAPI) |
|-----------|-----------|---------|----------|------------------------------|
| **Front → API GW** | HTTPS POST | `multipart/form-data` (JSON + files) | OAuth 2.0 Bearer, TLS 1

---

## Module 2 — contenu

## Module 2 – Conception, entraînement et déploiement d’un composant IA dans un workflow d’automatisation  

### 2.1. Cadre fonctionnel d’un composant IA  
| Élément | Description | Référence technique |
|--------|-------------|---------------------|
| **Entrée** | Payload JSON provenant d’un orchestrateur RPA (ex. : texte d’un e‑mail, tableau CSV). | `application/json` – RFC 8259 |
| **Pré‑traitement** | Nettoyage, tokenisation, encodage (TF‑IDF ou embeddings). | `scikit‑learn` 1.3, `sentence‑transformers` 2.2 |
| **Modèle** | Classificateur binaire/multi‑classe ou régression selon le KPI métier. | `LogisticRegression` (solver = `lbfgs`) ou `DistilBERT` fine‑tuned. |
| **Post‑traitement** | Mapping du score à une décision métier, seuil configurable. | Fonction `decision(score, threshold)`. |
| **Sortie** | JSON contenant la décision, le score et les métadonnées (timestamp, version). | `application/json` – RFC 8259 |

### 2.2. Architecture technique recommandée  

```
+----------------+      +-----------------+      +-------------------+
| Orchestrateur  | ---> | API FastAPI     | ---> | Service d’inférence|
| (ex. UiPath)   |      | (REST endpoint) |      | (Docker + GPU)    |
+----------------+      +-----------------+      +-------------------+
       |                         |                         |
       | 1. POST /predict        | 2. Validation JSON      | 3. Chargement du modèle
       |------------------------>|------------------------>|-------------------->
```

* **FastAPI** assure une latence < 50 ms pour des payloads < 5 KB (mesure sur `uvicorn` 0.22).  
* Le service d’inférence tourne dans un conteneur Docker 20.10, version `python:3.11-slim`.  
* Le modèle est sérialisé avec `joblib.dump(..., compress=3)` pour réduire le poids du fichier à < 10 Mo.  

### 2.3. Exemple de code complet (Python 3.11)

```python
# file: app/main.py
# --------------------------------------------------------------
# API FastAPI exposant un endpoint /predict pour classer le texte
# d'un e‑mail en "Facture" vs "Non‑Facture".  Modèle LogisticRegression
# entraîné sur TF‑IDF (scikit‑learn 1.3).  Toutes les fonctions sont
# commentées et testées unitaires (pytest 7.4) dans le répertoire tests/.
# --------------------------------------------------------------

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, validator
from typing import Literal
import joblib
import pathlib
import datetime as dt

# --------------------------------------------------------------
# 1️⃣ Schéma d’entrée – validation stricte (Pydantic)
# --------------------------------------------------------------
class PredictRequest(BaseModel):
    """Payload attendu par l’API."""
    text: str = Field(..., min_length=1, max_length=5000,
                     description="Corps du mail à analyser.")
    threshold: float = Field(0.5, ge=0.0, le=1.0,
                            description="Seuil de décision entre 0 et 1.")

    @validator("text")
    def no_control_chars(cls, v: str) -> str:
        """Interdit les caractères de contrôle qui pourraient casser le tokenizer."""
        if any(ord(ch) < 32 for ch in v):
            raise ValueError("Caractères de contrôle interdits.")
        return v

# --------------------------------------------------------------
# 2️⃣ Schéma de sortie – versionnage et métadonnées
# --------------------------------------------------------------
class PredictResponse(BaseModel):
    decision: Literal["Facture", "Non‑Facture"]
    score: float
    model_version: str
    timestamp: dt.datetime

# --------------------------------------------------------------
# 3️⃣ Chargement du modèle et du vecteur TF‑IDF (singleton)
# --------------------------------------------------------------
APP_ROOT = pathlib.Path(__file__).parent
MODEL_PATH = APP_ROOT / "model" / "logreg_tfidf.joblib"
VEC_PATH   = APP_ROOT / "model" / "tfidf_vectorizer.joblib"

# Le chargement est déclenché à l’import du module, donc une seule fois.
try:
    clf = joblib.load(MODEL_PATH)               # type: ignore[var-annotated]
    vectorizer = joblib.load(VEC_PATH)         # type: ignore[var-annotated]
    MODEL_VERSION = "v2024.07.01"
except Exception as exc:
    raise RuntimeError(f"Impossible de charger le modèle : {exc}") from exc

# --------------------------------------------------------------
# 4️⃣ Application FastAPI
# --------------------------------------------------------------
app = FastAPI(
    title="IA Classification Facture",

---

## Module 3 — contenu

## Module 3 – Déploiement, orchestration et monitoring d’une solution d’automatisation IA  

### 3.1 Architecture de déploiement  

| Composant | Rôle | Technologie typique | Points de contrôle |
|-----------|------|----------------------|---------------------|
| **API d’inférence IA** | Expose le modèle (LLM, classification, OCR) via HTTP | FastAPI + Uvicorn, Flask, ou TorchServe | Temps de réponse < 200 ms, gestion du pool de workers |
| **Moteur RPA** | Exécute les actions sur les applications métier | UiPath Orchestrator, Automation Anywhere, ou script Python + Playwright | Idempotence des tâches, gestion des sessions |
| **Broker de messages** | Découple les appels entre RPA et IA | RabbitMQ, Apache Kafka, ou Azure Service Bus | Persistance, ACK/NACK, dead‑letter queue |
| **Base de données de suivi** | Historise les exécutions, résultats, métriques | PostgreSQL, MySQL, ou Azure Cosmos DB | Indexation sur `run_id`, `timestamp` |
| **Orchestrateur de workflow** | Planifie, relance, et visualise les pipelines | Apache Airflow, Prefect, ou Azure Data Factory | DAG versionné, retries configurés, SLA |
| **Observabilité** | Logs, métriques, alertes | Grafana + Prometheus, ELK stack, ou Azure Monitor | Dashboard temps réel, seuil d’erreur < 1 % |

> **Principe** : chaque composant doit être *stateless* (sauf la DB) pour permettre le scaling horizontal.

### 3.2 Conteneurisation et CI/CD  

1. **Dockerisation**  
   ```dockerfile
   # Dockerfile – API d’inférence IA
   FROM python:3.11-slim

   # Sécurité : n’utilisez jamais USER root en production
   RUN useradd -ms /bin/bash appuser
   USER appuser

   WORKDIR /app
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt

   COPY . .
   EXPOSE 8000
   CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
   ```
   *Vérifiable* : `docker build -t ia-api .` produit une image de < 300 Mo (python‑slim + dépendances).

2. **Pipeline CI/CD (exemple GitHub Actions)**
   ```yaml
   name: CI/CD IA Automation

   on:
     push:
       branches: [ main ]

   jobs:
     build-test-deploy:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v3
         - name: Set up Python
           uses: actions/setup-python@v4
           with:
             python-version: "3.11"
         - name: Install dependencies
           run: pip install -r requirements.txt
         - name: Run unit tests
           run: pytest -q
         - name: Build Docker image
           run: |
             docker build -t ghcr.io/${{ github.repository }}:latest .
         - name: Push to registry
           uses: docker/login-action@v2
           with:
             registry: ghcr.io
             username: ${{ github.actor }}
             password: ${{ secrets.GITHUB_TOKEN }}
         - name: Deploy to Kubernetes
           uses: azure/k8s-deploy@v4
           with:
             manifests: |
               k8s/deployment.yaml
               k8s/service.yaml
   ```
   *Vérifiable* : le job s’arrête dès qu’un test échoue, garantissant la qualité du code livré.

### 3.3 Orchestration avec Apache Airflow  

```python
# dags/automatisation_ia.py
from airflow import DAG
from airflow.providers.http.operators.http import SimpleHttpOperator
from airflow.providers.cncf.kubernetes.operators.kubernetes_pod import KubernetesPodOperator
from airflow.utils.dates import days_ago

default_args = {
    "owner": "ia_team",
    "retries": 2,
    "retry_delay": 300,  # 5 min
}

with DAG(
    dag_id="processus_automatisation_ia",
    default_args=default_args,
    schedule_interval="0 2 * * *",  # quotidien 02:00 UTC
    start_date=days_

---

## Module 4 — contenu

## Module 4 – Mise en production, gouvernance et observabilité d’une solution d’automatisation IA  

### 4.1. Architecture cible en production  

| Composant | Rôle | Technologie typique | Points de contrôle |
|-----------|------|---------------------|--------------------|
| **API d’orchestration** | Point d’entrée des requêtes métier | FastAPI (Python) + Uvicorn | AuthN/AuthZ, quotas, validation schéma |
| **Moteur d’inférence** | Exécution du modèle IA | TensorFlow Serving ou TorchServe (Docker) | Version du modèle, latence, GPU/CPU utilisation |
| **Message broker** | Découplage asynchrone | RabbitMQ ou Kafka | DLQ, rétention, partitions |
| **Worker d’automatisation** | Exécution de tâches RPA / scripts | Celery (Redis) ou Airflow | Retries, timeout, idempotence |
| **Base de données métier** | Persistance des états | PostgreSQL (avec schéma « audit ») | ACID, sauvegarde, chiffrement au repos |
| **Observabilité** | Métriques, logs, traces | Prometheus + Grafana, Loki, OpenTelemetry | SLA, alertes, corrélation |
| **CI/CD** | Livraison continue | GitHub Actions / GitLab CI + ArgoCD | Tests unitaires, tests de charge, promotion d’image |
| **Sécurité & conformité** | Gestion des secrets, audit | HashiCorp Vault, OPA (Open Policy Agent) | Rotation des secrets, policies IaC |

> **Diagramme C4 (Level 2 – Container)**  
> ```
> +-------------------+      +-------------------+      +-------------------+
> |   Front‑end UI    | ---> |   API Gateway     | ---> |   Auth Service    |
> +-------------------+      +-------------------+      +-------------------+
>                                 |
>                                 v
>               +-------------------------------+
>               |   Orchestration Service (FastAPI)   |
>               +-------------------------------+
>                 |            |            |
>        +--------+   +--------+   +--------+
>        |  Model  |   |  Queue |   |  DB   |
>        |Serving  |   |Broker  |   |Postgres|
>        +--------+   +--------+   +--------+
>               |            |
>               v            v
>          +-----------+  +-----------+
>          |  Worker   |  |  Worker   |
>          |(Celery)   |  |(Airflow)  |
>          +-----------+  +-----------+
> ```

### 4.2. Pipeline CI/CD détaillé  

1. **Build**  
   - `docker build` avec *multi‑stage* pour réduire la taille de l’image.  
   - Tag : `registry.example.com/automatisation-ia:${{ github.sha }}`.  

2. **Test**  
   - Unit + integration (`pytest -m "not integration"`).  
   - Test de charge léger (`locust --headless -u 10 -r 2`).  

3. **Scan sécurité**  
   - Trivy (`trivy image --severity HIGH,CRITICAL`).  

4. **Push**  
   - `docker push` vers le registre privé.  

5. **Deploy**  
   - Manifests K8s templatisés (Helm).  
   - `helm upgrade --install automation-ia ./chart --set image.tag=${{ github.sha }}`.  

6. **Validation post‑déploiement**  
   - Health‑check HTTP 200 sur `/healthz`.  
   - Vérification de la latence < 200 ms (script Python).  

7. **Promotion**  
   - Si tous les seuils OK → tag `prod-${{ github.sha }}` et déclenchement du déploiement en production via ArgoCD.  

### 4.3. Exemple de workflow GitHub Actions (YAML)  

```yaml
name: CI/CD – Automation IA

on:
  push:
    branches: [ main ]
  pull_request:
    types: [ opened, synchronize, reopened ]

env:
  REGISTRY: registry.example.com
  IMAGE_NAME: automation-ia

jobs:
  build-test:
    runs-on: ubuntu-latest
    steps:
      # 1️⃣ Checkout du code
      - name: Checkout repository
        uses: actions/checkout@v4

      # 2️⃣ Cache Docker layers
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      # 3️⃣ Build multi‑stage image
      - name: Build Docker image
        id: build
        uses: docker/build-push-action@v5
        with:
          context: .
          push: false
          tags: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }}
          cache-from: type=registry,ref=${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:cache
          cache-to: type=registry,ref=${{

---

## Module 5 — contenu

## Module 5 – Mise en production, surveillance et gouvernance des solutions d’automatisation IA  

### 5.1 Objectifs techniques  
- **Déployer** un modèle IA dans un environnement conteneurisé (Docker + Kubernetes).  
- **Instrumenter** le service avec des métriques d’observabilité (Prometheus, OpenTelemetry).  
- **Mettre en place** un tableau de bord de suivi (Grafana) incluant performance, latence, taux d’erreur et dérive de données.  
- **Implémenter** un mécanisme de versionnage et de rollback (MLflow + Git).  
- **Formaliser** les règles de gouvernance : conformité RGPD, traçabilité des décisions, gestion des accès.

---

### 5.2 Architecture de surveillance (schéma texte)

```
┌─────────────────────┐
│  Client / API GW    │
└───────┬─────────────┘
        │
        ▼
┌─────────────────────┐      ┌─────────────────────┐
│ Service IA (K8s)   │◄─────│ Side‑car OpenTelemetry│
│  - FastAPI          │      │  (exporter metrics) │
│  - Model (ONNX)     │      └─────────────────────┘
└───────┬─────────────┘                │
        │                              ▼
        │                     ┌─────────────────┐
        │                     │ Prometheus      │
        │                     │ (scrape / store)│
        │                     └───────┬─────────┘
        │                             │
        ▼                             ▼
┌─────────────────────┐      ┌─────────────────┐
│ MLflow Tracking      │◄─────│ Grafana Dashboard│
│ (model registry,    │      │ (visualisation) │
│  experiments)       │      └─────────────────┘
└─────────────────────┘
```

---

### 5.3 Déploiement conteneurisé du modèle  

#### Dockerfile (extrait)  

```dockerfile
# Base Python 3.11 slim
FROM python:3.11-slim

# Install system deps (needed for ONNX + OpenTelemetry)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 libsm6 libxext6 libxrender1 && \
    rm -rf /var/lib/apt/lists/*

# Create non‑root user
RUN useradd -m appuser
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY src/ .

# Expose FastAPI port
EXPOSE 8080

# Run with OpenTelemetry auto‑instrumentation
ENV OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317
ENV OTEL_SERVICE_NAME=ia-automation-service
CMD ["opentelemetry-instrument", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
```

#### `requirements.txt` (extraits)  

```text
fastapi==0.110.0
uvicorn[standard]==0.27.0
onnxruntime==1.18.0
mlflow==2.12.2
opentelemetry-sdk==1.24.0
opentelemetry-instrumentation-fastapi==0.45b0
prometheus-client==0.20.0
```

#### `src/main.py` (exemple fonctionnel)  

```python
"""Service d’inférence IA exposé via FastAPI.
   Instrumenté avec OpenTelemetry et expose des métriques Prometheus.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import onnxruntime as ort
import numpy as np
import mlflow
import time
from prometheus_client import Counter, Histogram, start_http_server

# ---------- Prometheus metrics ----------
REQUEST_COUNT = Counter(
    "ia_inference_requests_total",
    "Nombre total de requêtes d’inférence",
    ["model_name", "status"]
)
REQUEST_LATENCY = Histogram(
    "ia_inference_latency_seconds",
    "Latence d’inférence",
    ["model_name"]
)

# ---------- FastAPI ----------
app = FastAPI(title="IA Automation Service")

# ---------- Modèle ONNX ----------
MODEL_PATH = "/app/models/model.onnx"
session = ort.InferenceSession(MODEL_PATH)
MODEL_NAME = "churn-predictor"

# ---------- MLflow tracking ----------
mlflow.set_tracking_uri("http://mlflow:5000")
mlflow.set_experiment("automation-prod")

class Payload(BaseModel):
    """Schéma d’entrée attendu par le modèle."""
    age: int
    tenure_months: int
    monthly_fee: float
    contract_type: str  # 'monthly' | 'annual'

def preprocess(payload: Payload) -> np.ndarray:
    """Encode les variables catégorielles et crée le tableau d’entrée."""
    contract = 1 if payload.contract_type == "annual" else 0
    return np.array([[payload.age, payload.tenure_months,
                      payload.monthly_fee, contract]],
                    dtype=np.float32)

@app.post("/predict")
def predict(payload: Payload):
    start = time.time()
    try:
        X = preprocess(payload)
        # ONNX inference
        ort_outs = session.run(None