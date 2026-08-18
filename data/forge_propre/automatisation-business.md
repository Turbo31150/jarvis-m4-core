# Automatisation Business IA

> Référence `automatisation-business` · 69 €

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
| **Contraintes** | - Confidentialité (RGPD) : chiffrement des pièces jointes.<br>- Temps de traitement doit rester dans des limites opérationnelles.<br>- Traçabilité (audit log). | Matrice de conformité. |

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
* **Service de validation** : UI interne (React) + API REST, décision manuelle ou règle métier (ex. plafond).  
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

* **FastAPI** assure une réponse rapide pour des payloads modestes (mesure sur `uvicorn`).  
* Le service d’inférence tourne dans un conteneur Docker 20.10, version `python:3.11-slim`.  
* Le modèle est sérialisé avec `joblib.dump(..., compress=3)` pour réduire le poids du fichier.  

### 2.3. Exemple de code complet (Python 3.11)

```python
# file: app/main.py
# --------------------------------------------------------------
# API FastAPI exposant un endpoint /predict pour classer le texte
# d'un e‑mail en "Facture" vs "Non‑Facture".  Modèle LogisticRegression
# entraîné sur TF‑IDF (scikit‑learn).  Toutes les fonctions sont
# commentées et testées unitaires (pytest) dans le répertoire tests/.
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
| **API d’inférence IA** | Expose le modèle (LLM, classification, OCR) via HTTP | FastAPI + Uvicorn, Flask, ou TorchServe | Temps de réponse raisonnable, gestion du pool de workers |
| **Moteur RPA** | Exécute les actions sur les applications métier | UiPath Orchestrator, Automation Anywhere, ou script Python + Playwright | Idempotence des tâches, gestion des sessions |
| **Broker de messages** | Découple les appels entre RPA et IA | RabbitMQ, Apache Kafka, ou Azure Service Bus | Persistance, ACK/NACK, dead‑letter queue |
| **Base de données de suivi** | Historise les exécutions, résultats, métriques | PostgreSQL, MySQL, ou Azure Cosmos DB | Indexation sur `run_id`, `timestamp` |
| **Orchestrateur de workflow** | Planifie, relance, et visualise les pipelines | Apache Airflow, Prefect, ou Azure Data Factory | DAG versionné, retries configurés, SLA |
| **Observabilité** | Logs, métriques, alertes | Grafana + Prometheus, ELK stack, ou Azure Monitor | Dashboard temps réel, seuil d’erreur faible |

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
   *Vérifiable* : la construction de l’image produit une image de taille raisonnable.

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
```

---

## Module 4 — contenu

## Module 4 – Mise en production, gouvernance et observabilité d’une solution d’automatisation IA  

### 4.1. Architecture cible en production  

| Composant | Rôle | Technologie typique | Points de contrôle |
|-----------|------|---------------------|--------------------|
| **API d’orchestration** | Point d’entrée des requêtes métier | FastAPI (Python) + Uvicorn | AuthN/AuthZ, quotas, validation schéma |
| **Moteur d’inférence** | Exécution du modèle IA | TensorFlow Serving ou TorchServe (Docker) | Version du modèle, latence, utilisation des ressources |
| **Message broker** | Découplage asynchrone | RabbitMQ ou Kafka | DLQ, rétention, partitions |
| **Worker d’automatisation**