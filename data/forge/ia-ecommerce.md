# IA pour l'E-commerce & Shopify

> Référence `ia-ecommerce` · 59 €

## Plan

## Module 1 – Fondamentaux de l’IA appliquée à l’e‑commerce  
**Objectif mesurable** : À l’issue du module, le participant pourra identifier trois cas d’usage IA pertinents pour une boutique Shopify, sélectionner les sources de données correspondantes et formaliser un cahier des charges fonctionnel contenant au moins cinq exigences mesurables.  

- Cartographie des processus e‑commerce (acquisition, conversion, fidélisation) où l’IA apporte une valeur ajoutée prouvée (ex. : recommandation produit, prévision de churn).  
- Analyse des données disponibles sur Shopify (produits, commandes, clients) et exigences de conformité RGPD.  
- Méthodologie de définition d’indicateurs de performance (KPIs) IA (précision, taux de conversion, temps de réponse).  
- Sélection de modèles standards (filtrage collaboratif, régression logistique, réseaux de neurones) adaptés aux volumes de données Shopify.  
- Élaboration d’un plan de collecte, de stockage (ex. : Snowflake, BigQuery) et de gouvernance des données.

---

## Module 2 – Architecture et intégration technique avec Shopify  
**Objectif mesurable** : Le participant sera capable de créer, déployer et sécuriser une application privée Shopify qui expose une API REST et une API GraphQL, et d’y connecter un micro‑service IA via webhook en moins de 45 minutes.  

- Utilisation de l’API Admin REST et GraphQL de Shopify (authentification OAuth 2.0, pagination, limites de taux).  
- Développement d’une app privée (Node.js ou Python) hébergée sur une plateforme cloud (AWS Lambda, Google Cloud Run).  
- Configuration des webhooks Shopify (order/create, cart/update) pour déclencher des fonctions IA.  
- Gestion des secrets (API keys, JWT) avec HashiCorp Vault ou AWS Secrets Manager.  
- Mise en place d’un pipeline CI/CD (GitHub Actions, Docker) pour le déploiement automatisé de l’app.

---

## Module 3 – Systèmes de recommandation et personnalisation en temps réel  
**Objectif mesurable** : Le participant pourra implémenter un moteur de recommandation produit basé sur le filtrage collaboratif et les embeddings de texte, l’intégrer dans le thème Shopify via Liquid et mesurer une amélioration d’au moins 2 % du taux de

---

## Module 1 — contenu

## 1. Cartographie des processus e‑commerce où l’IA crée de la valeur  

| Processus | Sous‑processus | Impact IA typique | Métrique clé |
|----------|---------------|-------------------|--------------|
| **Acquisition** | Recherche organique, campagnes SEA, email acquisition | **Targeting prédictif** (look‑alike, look‑back) | CTR, CPA, ROAS |
| **Conversion** | Navigation produit, ajout au panier, checkout | **Recommandation produit**, **optimisation du tunnel** (AB‑test dynamique) | Taux de conversion, valeur moyenne du panier (AOV) |
| **Fidélisation** | Programme de points, relance post‑achat, service client | **Score de churn**, **chatbot IA**, **upsell/cross‑sell** | Taux de ré‑achat, LTV, NPS |

> **Note** : chaque case d’usage doit être justifiable par un gain mesurable (ex. + 2 % de CVR grâce à la recommandation « People also bought »).

---

## 2. Analyse des données disponibles sur Shopify  

| Table Shopify | Colonnes utiles pour l’IA | Type de donnée | Exemple de requête (REST) |
|---------------|---------------------------|----------------|---------------------------|
| `products` | `id`, `title`, `tags`, `variants.price`, `created_at` | Texte, numérique, temporel | `GET /admin/api/2024-04/products.json?fields=id,title,tags,variants` |
| `customers` | `id`, `email`, `tags`, `orders_count`, `total_spent`, `created_at` | Texte, numérique, temporel | `GET /admin/api/2024-04/customers.json?fields=id,email,orders_count,total_spent` |
| `orders` | `id`, `customer_id`, `line_items`, `total_price`, `created_at`, `financial_status` | Texte, numérique, temporel | `GET /admin/api/2024-04/orders.json?status=any&fields=id,customer_id,total_price,created_at` |

### 2.1 Conformité RGPD  

| Action | Obligation | Implémentation concrète |
|--------|------------|------------------------|
| Consentement | Enregistrement du consentement avant collecte de données personnelles | Stocker le champ `marketing_opt_in` de `customers` et le tracer dans un log immutable (ex. CloudTrail) |
| Droit à l’oubli | Suppression définitive des données à la demande du client | Utiliser l’endpoint `DELETE /admin/api/2024-04/customers/{id}.json` et purger les copies dans le data‑lake (ex. BigQuery) |
| Minimisation | Ne collecter que les attributs nécessaires aux modèles | Faire un **data‑audit** : chaque variable doit être liée à un KPI et à une exigence fonctionnelle. |

---

## 3. Méthodologie de définition d’indicateurs de performance (KPIs) IA  

1. **Alignement business** – chaque KPI doit répondre à une question métier (ex. « Quel sera le taux de conversion si on montre X ? »).  
2. **Mesurabilité** – la métrique doit être calculable à partir des logs Shopify ou du data‑warehouse.  
3. **Seuils de succès** – fixer un objectif chiffré (ex. précision ≥ 0,85, lift ≥ 1,15).  

| KPI IA | Formule | Source de calcul | Objectif typique |
|--------|---------|------------------|------------------|
| Précision du classif. churn | TP / (TP + FP) | Table `customers` + modèle churn | ≥ 0,80 |
| Lift de recommandation | CVR\_rec / CVR\_baseline | Sessions + `recommendations` logs | ≥ 1,10 |
| Temps de réponse API IA | (t₁ - t₀) | Timestamp avant/after appel micro‑service | ≤ 200 ms |

---

## 4. Sélection de modèles standards adaptés aux volumes Shopify  

| Cas d’usage | Volume de données (exemple) | Modèle recommandé | Pourquoi |
|-------------|-----------------------------|-------------------|----------|
| **Filtrage collaboratif** | 10 k produits, 50 k clients, 200 k interactions | *Matrix Factorization* (ALS) | Scalable en batch, bonnes performances sur matrices clairsemées |
| **Prédiction churn** | 30 k clients, 12 mois d’historique | *Logistic Regression* ou *XGBoost* | Interprétable, rapide à entraîner, gère variables catégorielles |
| **Analyse de texte (tags, reviews)** | 200 k reviews | *Sentence‑BERT* embeddings + *K‑NN* | Captures sémantiques, peu de données d’entraînement supplémentaires |
| **Détection d’anomalie de fraude** | 5 k transactions/jour | *Isolation Forest* | Non‑paramétrique, détecte outliers sans labels |

> **Rappel** : le choix du modèle doit être justifié par le **coût d’inférence** (latence) et le **budget de calcul** (ex. 2 vCPU, 4 Go RAM sur Cloud Run).

---

## 5. Élaboration d’un plan de collecte, de stockage et de gouvernance des données  

### 5.1 Pipeline de collecte (exemple)  

```mermaid
flowchart TD
    A[Shopify Webhooks] -->|order/create| B[Google Cloud Pub/Sub]
    B --> C[Cloud Function (Python)]
    C -->|transform| D[Big

---

## Module 2 — contenu

## 2.1. Architecture générale de l’application privée Shopify  

| Élément | Rôle | Technologie recommandée |
|--------|------|--------------------------|
| **Front‑end (Shopify)** | Thème Liquid, appels aux endpoints de l’app via JavaScript (fetch) | Liquid, Ajax API |
| **Back‑end** | API REST + GraphQL, gestion des webhooks, relais vers le micro‑service IA | Node.js ≥ 18 (Express ou Fastify) ou Python 3.11 (FastAPI) |
| **Infrastructure** | Exécution sans serveur, scalabilité, isolation des secrets | AWS Lambda + API Gateway **ou** Google Cloud Run |
| **Stockage des secrets** | API keys Shopify, JWT, URL du micro‑service IA | AWS Secrets Manager, HashiCorp Vault, ou Google Secret Manager |
| **CI/CD** | Build, test, déploiement automatisé | GitHub Actions + Docker (image : node:18‑slim) |
| **Monitoring** | Traces, métriques, alertes sur erreurs 5xx et dépassements de quota | CloudWatch (AWS) ou Stackdriver (GCP) |

> **Note** : la plupart des boutiques utilisent déjà un domaine `myshop.myshopify.com`. L’app privée s’installe dans le tableau de bord **Apps → Develop apps for your store**. Aucun store public n’est requis.

---

## 2.2. Authentification OAuth 2.0 avec Shopify  

1. **Création de l’app**  
   - Dans le tableau de bord Shopify → *Apps → Develop apps* → *Create an app*.  
   - Cochez **Admin API access** → *Read and write* sur les ressources nécessaires (Orders, Products, Customers).  
   - Activez **Storefront API** si vous comptez appeler le GraphQL côté client.  
   - Enregistrez l’**API key** (client_id) et le **API secret key** (client_secret).  

2. **Flux d’obtention du token** (client credentials grant) – recommandé pour les apps privées (pas d’interaction utilisateur) :

```http
POST https://{shop}.myshopify.com/admin/oauth/access_token
Content-Type: application/json

{
  "client_id": "<API_KEY>",
  "client_secret": "<API_SECRET>",
  "grant_type": "client_credentials"
}
```

Réponse :

```json
{
  "access_token": "shpat_XXXXXXXXXXXXXXXXXXXXXXXX",
  "expires_in": 86400,
  "scope": "read_products,write_orders"
}
```

- Le token est **stateless** (JWT signé par Shopify) ; il n’est pas rafraîchi automatiquement. Renouvelez‑le avant l’expiration (24 h).  
- **Piège** : ne stockez jamais le `client_secret` dans le code source. Utilisez un secret manager et injectez‑le au runtime (ex. `process.env.SHOPIFY_API_SECRET`).

---

## 2.3. Structure du projet (Node.js)  

```
my-shopify-app/
├─ src/
│  ├─ api/
│  │  ├─ adminRest.js          # wrapper REST
│  │  └─ adminGraphQL.js        # wrapper GraphQL
│  ├─ webhooks/
│  │  └─ orderCreate.js        # handler webhook order/create
│  ├─ services/
│  │  └─ aiClient.js            # appel au micro‑service IA
│  └─ index.js                  # entry point (Express)
├─ .github/
│  └─ workflows/
│     └─ ci-cd.yml              # GitHub Actions
├─ Dockerfile
├─ package.json
└─ README.md
```

---

## 2.4. Exemple complet : webhook `order/create` qui déclenche un micro‑service IA  

> **Objectif** : dès qu’une commande est créée, envoyer le panier (liste d’IDs produits, quantités, client_id) à un service IA qui renvoie une recommandation de cross‑sell. La réponse est stockée dans les métadonnées de la commande via l’API Admin.

### 2.4.1. `src/index.js`

```js
// src/index.js
import express from 'express';
import bodyParser from 'body-parser';
import crypto from 'crypto';
import { handleOrderCreate } from './webhooks/orderCreate.js';
import { getShopifyClient } from './api/adminRest.js';

const app = express();

// Shopify envoie les webhooks en `application/json` + header HMAC
app.use(bodyParser.json({
  verify: (req, res, buf) => {
    const hmacHeader = req.get('X-Shopify-Hmac-Sha256');
    const secret = process.env.SHOPIFY_WEBHOOK_SECRET; // stocké dans Secrets Manager
    const hash = crypto.createHmac('sha256', secret).update(buf).digest('base64');
    if (hash !== hmacHeader) {
      throw new Error('Webhook verification failed');
    }
  }
}));

app.post('/webhooks/order/create', async (req, res) => {
  try {
    await handleOrderCreate(req.body);
    res.status(200).send('OK');
  } catch (e) {
    console.error('Webhook error:', e);
    res.status(500).send('Internal Server Error');
  }
});

const PORT = process.env.PORT || 8080;
app.listen(PORT, () => console.log(`App listening on ${PORT}`));
```

### 2.4.2. `src/webhooks/orderCreate.js`

```js
// src/webhooks/orderCreate.js
import { getShopifyClient } from '../api/adminRest.js';
import { getRecommendation } from '../services/aiClient

---

## Module 3 — contenu

## 3.1 Principes théoriques du moteur de recommandation

| Concept | Définition | Formule / Algorithme clé |
|--------|------------|--------------------------|
| **Filtrage collaboratif (CF) – implicite** | Utilise les interactions (vues, ajouts au panier, achats) comme signal de préférence. | `p_ui = 1` si l’utilisateur *u* a interagi avec l’article *i*, sinon `0`. |
| **Factorisation matricielle (MF)** | Approxime la matrice d’interaction `R` (U×I) par le produit de deux matrices de rang *k* : `R ≈ P·Qᵀ`. | `min_{P,Q} Σ_{(u,i)∈K} (p_ui – p_u·q_i)² + λ(‖p_u‖²+‖q_i‖²)` |
| **Embeddings de texte** | Vecteurs dense obtenus à partir du titre / description produit via un modèle pré‑entraîné (ex. `sentence‑transformers/all‑MiniLM‑L6‑v2`). | `e_i = model.encode(text_i)` |
| **Hybridation** | Combine CF (scores de similarité utilisateur‑article) et contenu (similarité texte). | `score_ui = α·CF_ui + (1‑α)·cos(e_u, e_i)` |
| **Top‑N** | Classe les articles par score décroissant et renvoie les `N` premiers. | `rec_u = argsort(score_u)[‑N:]` |

### Pourquoi ces choix pour Shopify ?

* **Volumes** : une boutique moyenne (10 k produits, 50 k clients) tient dans la RAM d’une petite instance EC2 (≈ 8 GB).  
* **Temps réel** : les webhooks (`cart/update`, `order/create`) déclenchent une fonction Lambda qui calcule le top‑5 en < 100 ms.  
* **Coût** : `implicit` (bibliothèque Cython) et `sentence‑transformers` sont open‑source, aucune licence supplémentaire.

---

## 3.2 Pipeline de données

1. **Extraction** (Shopify Admin API)  
   ```bash
   GET /admin/api/2023-10/orders.json?status=any&fields=id,customer,email,line_items
   GET /admin/api/2023-10/products.json?fields=id,title,body_html,variants
   ```
2. **Transformation**  
   * Crée la table `interactions(user_id, product_id, weight)` où `weight = 1` pour chaque achat, `0.5` pour chaque ajout au panier.  
   * Nettoie le texte (`html.unescape`, suppression des balises) avant d’alimenter le modèle d’embeddings.  
3. **Chargement**  
   * Stocke `interactions` dans **BigQuery** (`project.dataset.interactions`).  
   * Stocke les embeddings dans la même table (`embedding ARRAY<FLOAT64>`).  

> **Conformité RGPD** – Conservez uniquement l’ID client (hash SHA‑256) et les métadonnées d’interaction. Supprimez les champs personnels (`email`, `nom`) dès la phase de transformation.

---

## 3.3 Entraînement du modèle (Python)

```python
# -*- coding: utf-8 -*-
"""
Entraînement d'un moteur de recommandation hybride pour Shopify.
- MF avec la bibliothèque implicit (ALS)
- Embeddings de texte via sentence‑transformers
- Sauvegarde des matrices P, Q et des embeddings dans un bucket S3
"""

import os
import json
import numpy as np
import pandas as pd
import boto3
from implicit.als import AlternatingLeastSquares
from sentence_transformers import SentenceTransformer

# ------------------------------------------------------------------
# 1. Chargement des données depuis BigQuery (export CSV pré‑préparé)
# ------------------------------------------------------------------
INTERACTIONS_PATH = "gs://my-bucket/shopify/interactions.csv"
df = pd.read_csv(INTERACTIONS_PATH)          # colonnes : user_id, product_id, weight
users = df["user_id"].astype("category")
items = df["product_id"].astype("category")

# Matrice sparse (CSC) attendue par implicit
from scipy.sparse import coo_matrix
matrix = coo_matrix(
    (df["weight"], (users.cat.codes, items.cat.codes))
).tocsc()

# ------------------------------------------------------------------
# 2. Factorisation matricielle (ALS)
# ------------------------------------------------------------------
als = AlternatingLeastSquares(
    factors=64,
    regularization=0.01,
    iterations=20,
    calculate_training_loss=False,
    random_state=42,
)
als.fit(matrix)

# Matrices d'embeddings utilisateurs et articles
user_factors = als.user_factors          # shape (n_users, 64)
item_factors = als.item_factors          # shape (n_items, 64)

# ------------------------------------------------------------------
# 3. Embeddings texte des produits
# ------------------------------------------------------------------
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
product_texts = df.drop_duplicates("product_id")["title"].tolist()
product_ids = df.drop_duplicates("product_id")["product_id"].tolist()
text_embeddings = model.encode(product_texts, batch_size=64, show_progress_bar=True)

# Alignement des embeddings avec l'index de `items`
embedding_matrix = np.zeros((len(items.cat.categories), text_embeddings.shape[1]))
for pid, vec in zip(product_ids, text_embeddings

---

## Module 4 — contenu

## Module 4 – MLOps, monitoring & optimisation des modèles IA sur Shopify  

**Objectif mesurable** : à l’issue du module, le participant pourra mettre en place un pipeline CI/CD / CD pour un modèle IA, le déployer en tant que micro‑service scalable, instrumenter le service pour collecter les métriques critiques et déclencher automatiquement une relance de formation lorsqu’un glissement de données (data‑drift) est détecté, le tout en moins de 30 minutes.

---

### 1. Architecture MLOps adaptée à Shopify  

| composant | rôle | technologie recommandée | remarque de conformité |
|-----------|------|------------------------|------------------------|
| **Source de données** | Export quotidien des tables `orders`, `customers`, `product_variants` | Shopify Admin API → S3 (ou GCS) en format Parquet | chiffrement côté‑repos, bucket privé |
| **Feature store** | Versionner les features, garantir la reproductibilité | Feast + BigQuery (ou Snowflake) | audit des accès, logs CloudTrail |
| **Entraînement** | Notebook ou pipeline batch | Vertex AI Pipelines / AWS SageMaker Pipelines | isolation réseau, VPC‑endpoint |
| **Model registry** | Stocker artefacts, métadonnées, tags | MLflow (backend DB PostgreSQL) | sauvegarde journalière, contrôle d’accès |
| **Inference service** | Exposer `/predict` via HTTP(s) | FastAPI + Docker + Cloud Run (ou AWS Lambda + API Gateway) | TLS terminée, JWT‑auth |
| **Orchestration** | Déclencher le service à chaque webhook `order/create` | Cloud Scheduler / EventBridge → Pub/Sub → Cloud Run | débit limité à 2 req/s (Shopify) |
| **Observabilité** | Logs, métriques, traces, alertes | Stack : Cloud Logging, Prometheus, Grafana, OpenTelemetry | rétention 90 jours, export GDPR‑compliant |
| **CI/CD** | Build, test, déploiement automatisés | GitHub Actions, Docker BuildKit, Terraform (infra) | secrets injectés via GitHub Encrypted Secrets ou Vault |

---

### 2. Pipeline CI/CD / CD détaillé (GitHub Actions)  

```yaml
name: mlops-deploy
on:
  push:
    branches: [ main ]
  workflow_dispatch:

env:
  IMAGE: gcr.io/${{ secrets.GCP_PROJECT }}/shopify-ml-service:${{ github.sha }}

jobs:
  lint-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Install deps
        run: pip install -r requirements.txt
      - name: Lint
        run: flake8 src/
      - name: Unit tests
        run: pytest -q tests/
      - name: Build Docker image
        run: |
          docker build -t $IMAGE .
          echo ${{ secrets.GCP_SA_KEY }} | docker login -u _json_key --password-stdin https://gcr.io
          docker push $IMAGE

  deploy:
    needs: lint-test
    runs-on: ubuntu-latest
    environment: production
    steps:
      - name: Deploy to Cloud Run
        uses: google-github-actions/deploy-cloudrun@v0
        with:
          service: shopify-ml-service
          image: ${{ env.IMAGE }}
          region: europe-west1
          env_vars: |
            MODEL_REGISTRY_URL=${{ secrets.MODEL_REGISTRY_URL }}
            JWT_SECRET=${{ secrets.JWT_SECRET }}
```

*Commentaires*  
- `flake8` assure la conformité PEP8, indispensable pour la maintenabilité.  
- Les secrets (`GCP_SA_KEY`, `MODEL_REGISTRY_URL`, `JWT_SECRET`) sont injectés uniquement au moment du déploiement, jamais stockés en clair.  
- L’image Docker contient le modèle chargé au démarrage (`model = mlflow.pyfunc.load_model(...)`), ce qui évite le temps de chargement à chaque requête.

---

### 3. Service d’inférence FastAPI (exemple fonctionnel)  

```python
# src/main.py
import os
import json
import mlflow.pyfunc
from fastapi import FastAPI, Request, HTTPException, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import jwt
import logging

# -------------------------------------------------
# Configuration
# -------------------------------------------------
MODEL_URI = os.getenv("MODEL_REGISTRY_URL")
JWT_SECRET = os.getenv("JWT_SECRET")
MODEL = mlflow.pyfunc.load_model(MODEL_URI)

# -------------------------------------------------
# Logging structuré (compatible avec Cloud Logging)
# -------------------------------------------------
logger = logging.getLogger("uvicorn.error")
def log_struct(message: str, **kwargs):
    logger.info(json.dumps({"message": message, **kwargs}))

# -------------------------------------------------
# Authentification JWT
# -------------------------------------------------
def verify_jwt(token: str):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return payload
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=401, detail

---

## Module 5 — contenu

## Module 5 – Mise en production, monitoring et optimisation continue des modèles IA sur Shopify  

**Objectif mesurable** : À l’issue du module, le participant pourra mettre en place un pipeline de déploiement continu incluant : (i) le versionnage du modèle, (ii) le monitoring des métriques de performance en temps réel, (iii) l’orchestration d’un processus de ré‑entraînement hebdomadaire, et (iv) l’exécution d’un test A/B automatisé avec un gain statistiquement significatif (p < 0,05) sur le taux de conversion.

---

### 5.1 Versionnage et gestion des artefacts de modèle  

| Composant | Rôle | Implémentation typique |
|-----------|------|------------------------|
| **Git LFS** | Stockage des poids (ex. : `model.pkl`, `embedding.npy`) | `git lfs track "*.pkl"` |
| **MLflow** | Enregistrement du modèle, des paramètres, des métriques, et du code source | `mlflow.start_run(); mlflow.log_metric("precision", 0.87); mlflow.log_artifact("model.pkl")` |
| **Docker** | Encapsulation de l’environnement d’inférence (Python 3.11, `torch==2.2.0`, `scikit‑learn==1.5.0`) | `FROM python:3.11-slim`<br>`RUN pip install torch==2.2.0 scikit-learn==1.5.0` |

> **Bon à savoir** : le hash du commit Git doit être injecté dans le tag Docker (`--label git_commit=$(git rev-parse --short HEAD)`) afin de garantir la traçabilité entre code, modèle et conteneur.

---

### 5.2 Déploiement du micro‑service IA avec **Google Cloud Run**  

```yaml
# cloudrun.yaml – configuration Cloud Run (gcloud CLI)
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: recommendation-service
spec:
  template:
    metadata:
      annotations:
        autoscaling.knative.dev/minScale: "1"
        autoscaling.knative.dev/maxScale: "100"
    spec:
      containers:
        - image: gcr.io/$PROJECT_ID/reco-service:{{VERSION}}
          env:
            - name: MODEL_PATH
              value: "/app/model.pkl"
            - name: LOG_LEVEL
              value: "INFO"
          resources:
            limits:
              cpu: "1000m"
              memory: "512Mi"
```

*Déploiement*  

```bash
# 1. Build l’image Docker avec le modèle versionné
docker build -t gcr.io/$PROJECT_ID/reco-service:${GIT_SHA} .

# 2. Push vers Container Registry
docker push gcr.io/$PROJECT_ID/reco-service:${GIT_SHA}

# 3. Déployer sur Cloud Run
gcloud run services replace cloudrun.yaml --region europe-west1
```

**Points de vigilance**  
- **Timeout** : Cloud Run coupe les requêtes > 15 min ; l’inférence doit être < 300 ms pour ne pas dépasser la limite de Shopify (1 s).  
- **Quota** : le nombre de révisions conservées par défaut est 10 ; configurez `--revision-history-limit=20` si vous avez besoin d’un audit plus long.  

---

### 5.3 Monitoring des métriques IA avec **Prometheus + Grafana**  

```python
# reco_service/app/metrics.py
from prometheus_client import Counter, Histogram, start_http_server

# Compteurs
REQ_TOTAL = Counter(
    "reco_requests_total",
    "Nombre total de requêtes d recommendation",
    ["status"]
)

# Histogramme de latence (en secondes)
REQ_LATENCY = Histogram(
    "reco_request_latency_seconds",
    "Latence d'exécution d'une requête de recommandation",
    buckets=(0.05, 0.1, 0.2, 0.5, 1.0)
)

def record_request(status: str, latency: float):
    REQ_TOTAL.labels(status=status).inc()
    REQ_LATENCY.observe(latency)

# Démarrage du endpoint /metrics sur le port 8000
start_http_server(8000)
```

Intégration dans le handler Flask :

```python
from flask import Flask, request, jsonify
import time
from metrics import record_request

app = Flask(__name__)

@app.route("/predict", methods=["POST"])
def predict():
    start = time.time()
    try:
        payload = request.json
        # … logique d’inférence …
        result = {"products": ["sku_123", "sku_456"]}
        status = "success"
        return jsonify(result), 200
    except Exception as e:
        status = "error"
        return jsonify({"error": str(e)}), 500
    finally:
        latency = time.time() - start
        record_request(status, latency)
```

**Alertes essentielles (Grafana)**  

| Alert | Condition | Action |
|-------|-----------|--------|
| `HighLatency` | `avg_over_time(reco_request_latency_seconds[5m]) > 0.4` | Slack webhook |
| `ErrorRate` | `sum by (status) (rate(reco_requests_total{status="error"}[5