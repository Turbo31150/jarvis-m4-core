# IA sur GCP — Vertex AI & Gemini

> Référence `ia-cloud-gcp` · 79 €

## Plan

## Module 1 – Architecture GCP IA : services, sécurité et gouvernance  
**Objectif mesurable** : à l’issue du module, le participant pourra concevoir un diagramme d’architecture complet intégrant Vertex AI, Cloud Storage, IAM et VPC Service Controls, et justifier chaque choix du point de vue de la conformité et du coût.  

**Notions couvertes**  
- Vue d’ensemble des produits IA de GCP : Vertex AI Workbench, Training, Prediction, Feature Store, Pipelines, et Gemini API.  
- Modèle de facturation de Vertex AI (CPU/GPU, training vs prediction, stockage des artefacts).  
- Gestion des identités et des accès (IAM roles : `aiplatform.admin`, `aiplatform.user`; utilisation de Service Accounts).  
- Sécurisation réseau avec VPC Service Controls et Private Google Access.  
- Gouvernance des données : labels, tags, audit logs (Cloud Audit Logs, Data Catalog).  

---  

## Module 2 – Gestion des données et Feature Store  
**Objectif mesurable** : le participant sera capable de créer, ingérer et servir des jeux de données dans Vertex AI Feature Store, en appliquant le versioning et le monitoring de la dérive.  

**Notions couvertes**  
- Ingestion de données depuis Cloud Storage, BigQuery et Pub/Sub vers Vertex AI Dataset.  
- Schématisation et validation des données avec Data Validation (Vertex AI Data Validation).  
- Création de Entity Types, Feature Views et Feature Online Store.  
- Gestion du versioning des Feature Sets (timestamp‑based, TTL).  
- Monitoring de la dérive de features via Vertex AI Feature Monitoring (statistiques de distribution, alertes).  

---  

## Module 3 – Entraînement de modèles : Custom Training & AutoML  
**Objectif mesurable** : le participant pourra lancer un entraînement de modèle TensorFlow 2.x ou PyTorch 2.x sur Vertex AI Training, récupérer les artefacts et comparer les performances avec un modèle AutoML équivalent.  

**Notions couvertes**  
- Environnement de travail avec Vertex AI Workbench (JupyterLab, GPU NVIDIA A100, quotas).  
- Construction d’un Docker container custom (Cloud Build, Artifact Registry) pour le training.  
- Soumission de jobs d’entraînement (Python SDK `aiplatform.CustomJob`, `gcloud ai custom-jobs create`).  
- Utilisation d’AutoML Tables, Vision, Text & Video (configuration des budgets, early‑stopping).  
- Suivi des métriques d’entraînement avec TensorBoard intégré à Vertex AI Experiments.  

---  

## Module 4 – Déploiement, serving et MLOps avec Vertex AI Pipelines  
**Objectif mesurable** : le participant pourra créer un pipeline CI/CD complet (pré‑traitement → entraînement → déploiement) avec Vertex AI Pipelines, et mettre en production un endpoint scalable versionné.  

**Notions couvertes**  
- Définition de composants Kubeflow Pipeline (Python DSL, `aiplatform.CustomJob`).  

---  

## Module 1 — contenu

## Module 1 – Architecture GCP IA : services, sécurité et gouvernance  

### 1.1 Vue d’ensemble des produits IA de GCP  

| Service | Fonction principale | API / SDK | Facturation |
|--------|---------------------|-----------|--------------|
| **Vertex AI Workbench** | Environnement Jupyter‑Lab managé, accès aux GPU/TPU, stockage persistant via Cloud Storage | `google-cloud-aiplatform` (Python) | Facturation du notebook (CPU/GPU) + stockage Cloud Storage |
| **Vertex AI Training** | Exécution de jobs de formation (custom containers ou scripts) | `aiplatform.CustomJob` | CPU/GPU * heure + coût du stockage des artefacts (Bucket) |
| **Vertex AI Prediction** | Déploiement d’endpoints pour inference (online) ou batch prediction | `aiplatform.Endpoint` | CPU/GPU * heure d’allocation + nombre de prédictions (par 1 000) |
| **Vertex AI Feature Store** | Gestion centralisée des features (online + offline) | `aiplatform.Featurestore` | Stockage offline (GB‑mois) + stockage online (GB‑mois) + requêtes en ligne |
| **Vertex AI Pipelines** | Orchestration de workflows Kubeflow sur GKE‑Autopilot | `kfp` (Python DSL) | CPU/GPU * heure des pods + stockage des artefacts |
| **Gemini API** (Gemini 1.5/2.0) | Modèles de génération de texte, code et multimodal | `google-generativeai` | Nombre de tokens d’entrée + tokens générés (tarif par 1 000) |

> **Note de facturation** : les coûts GPU sont facturés à la seconde, arrondis au 1 minute. Les tarifs varient selon la zone (ex. `us-central1` = tarif pour A100, `europe-west1` ≈ tarif correspondant).  

### 1.2 Modèle de facturation de Vertex AI  

```text
Coût total = Σ (CPU‑heure × tarif_CPU) 
           + Σ (GPU‑heure × tarif_GPU) 
           + Σ (stockage_artéfacts_GB‑mois × tarif_Stockage) 
           + Σ (prédictions × tarif_par_1k) 
           + Σ (tokens_Gemini × tarif_par_1k)
```

- **CPU‑heure** : tarif indiqué dans la documentation GCP.  
- **GPU‑heure** : tarif indiqué dans la documentation GCP.  
- **Stockage artefacts** : Cloud Storage Standard tarif indiqué dans la documentation GCP.  

#### Exemple de calcul  
Un job d’entraînement de 3 h sur 1 A100 + 2 vCPU + 8 GiB RAM, générant 5 GB d’artefacts :

```
GPU : 3 h × tarif GPU
CPU : 3 h × tarif CPU
Stockage : 5 GB × tarif stockage
Total ≈ somme des lignes ci‑dessus
```

### 1.3 Gestion des identités et des accès (IAM)

| Rôle | Permissions clés | Usage recommandé |
|------|------------------|------------------|
| `roles/aiplatform.admin` | `aiplatform.*` (création, mise à jour, suppression) | Responsable IA, possède le droit de créer des projets, pipelines, endpoints. |
| `roles/aiplatform.user` | `aiplatform.*` (lecture, exécution) | Data scientist qui lance des jobs mais ne supprime pas les ressources. |
| `roles/storage.objectAdmin` | Gestion complète des objets Cloud Storage | Nécessaire pour accéder aux datasets et aux artefacts. |
| `roles/bigquery.dataEditor` | CRUD sur les tables BigQuery | Pour les pipelines qui lisent/écrivent des jeux de données. |

#### Attribution d’un rôle via `gcloud`

```bash
# 1️⃣ Créez un service account dédié aux pipelines
gcloud iam service-accounts create vertex-pipeline-sa \
    --display-name "Service Account for Vertex Pipelines"

# 2️⃣ Attribuez le rôle aiplatform.admin à ce SA sur le projet
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:vertex-pipeline-sa@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/aiplatform.admin"

# 3️⃣ Restreignez l’accès au bucket de données
gsutil iam ch \
    serviceAccount:vertex-pipeline-sa@$PROJECT_ID.iam.gserviceaccount.com:objectViewer \
    gs://my-vertex-data-bucket
```

> **Piège** : le SA doit aussi disposer du rôle `roles/iam.serviceAccountUser` sur les SA qu’il doit « impersonner », sinon les jobs échoueront avec `PermissionDenied`.

### 1.4 Sécurisation réseau  

#### 1.4.1 VPC Service Controls (VPC‑SC)  

- **Objectif** : créer un périmètre de confiance (service perimeter) qui empêche les appels API depuis des réseaux non approuvés.  
- **Étapes** :

```bash
# 1️⃣ Créez un périmètre nommé « vertex‑perimeter »
gcloud access-context-manager perimeters create vertex-perimeter \
    --title="Vertex Perimeter" \
    --resources=projects/$PROJECT_NUMBER \
    --restricted-services=aiplatform.googleapis.com,storage.googleapis.com

# 2️⃣ Ajoutez les VPC autorisées (ex. 10.0.0.0/16)
gcloud access-context-manager perimeters update vertex-perimeter \
    --add-allowed-services=aiplatform.googleapis.com
```

---  

## Module 2 — contenu

## 2.1 Ingestion des données dans Vertex AI Dataset  

| Source | Méthode d’import | Points de contrôle obligatoires |
|--------|------------------|---------------------------------|
| Cloud Storage (CSV, JSONL, TFRecord) | `aiplatform.TextDataset.create` ou `aiplatform.ImageDataset.create` | Vérifier le **schema** (colonnes, types) avec `gcloud storage cp` + `pandas.read_csv` avant import. |
| BigQuery | `aiplatform.TabularDataset.create` (paramètre `bigquery_source`) | S’assurer que la requête ne dépasse pas la limite d’import. |
| Pub/Sub (streaming) | Créez d’abord un **Vertex AI Dataset** vide, puis utilisez **Dataflow** (template `PubSub to Vertex AI Dataset`) pour pousser les messages. | Le format des messages doit être **JSONL** ou **Avro** conforme au schéma du dataset. |

```python
# -*- coding: utf-8 -*-
# Exemple complet d’ingestion depuis Cloud Storage vers un TabularDataset Vertex AI
from google.cloud import aiplatform
from google.cloud import storage
import pandas as pd

PROJECT_ID = "my-gcp-project"
REGION = "europe-west1"
BUCKET = "gs://my-ml-data/transactions_2024-07.csv"
DATASET_DISPLAY_NAME = "transactions_raw"

# 1️⃣ Initialise le SDK
aiplatform.init(project=PROJECT_ID, location=REGION)

# 2️⃣ Vérification locale du schéma (facultatif mais fortement recommandé)
df = pd.read_csv("transactions_2024-07.csv")
expected_cols = {"transaction_id": "object",
                 "customer_id": "object",
                 "amount_eur": "float64",
                 "timestamp": "datetime64[ns]"}
assert set(df.columns) == set(expected_cols), "Mauvais jeu de colonnes"
for col, dtype in expected_cols.items():
    assert df[col].dtype == dtype, f"Colonne {col} doit être {dtype}"

# 3️⃣ Création du dataset Vertex AI
dataset = aiplatform.TabularDataset.create(
    display_name=DATASET_DISPLAY_NAME,
    bq_source=None,                     # on utilise Cloud Storage ici
    import_schema_uri=aiplatform.schema.dataset.tabular,
    gcs_source=[BUCKET],
    sync=True,                          # attend la fin de l’import
)

print(f"Dataset créé : {dataset.resource_name}")
```

*Remarque* : `sync=True` bloque le notebook jusqu’à la fin de l’import. En production, utilisez le **callback** `job.wait_for_completion()` pour ne pas monopoliser le thread.

---

## 2.2 Validation des données avec Vertex AI Data Validation  

Vertex AI Data Validation fournit deux mécanismes :  

| Mécanisme | API | Exemple d’usage |
|-----------|-----|-----------------|
| **Schema validation** | `aiplatform.DataValidation.create` (type `SCHEMA`) | Vérifie que chaque ligne respecte le type déclaré (ex. `float64` vs `string`). |
| **Statistical validation** | `aiplatform.DataValidation.create` (type `STATISTICS`) | Compare les distributions (moyenne, std, quantiles) entre le *train* et le *validation* set. |

```python
# Validation du schéma du dataset créé précédemment
validation = aiplatform.DataValidation.create(
    display_name="transactions_schema_check",
    dataset=dataset,
    validation_type=aiplatform.DataValidation.ValidationType.SCHEMA,
    schema_uri=aiplatform.schema.dataset.tabular,
    sync=True,
)

print(f"Statut de la validation : {