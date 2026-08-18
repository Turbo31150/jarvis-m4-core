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
- Définition de composants Kubeflow Pipeline (Python DSL, `aipl

---

## Module 1 — contenu

## Module 1 – Architecture GCP IA : services, sécurité et gouvernance  

### 1.1 Vue d’ensemble des produits IA de GCP  

| Service | Fonction principale | API / SDK | Facturation |
|--------|---------------------|-----------|--------------|
| **Vertex AI Workbench** | Environnement Jupyter‑Lab managé, accès aux GPU/TPU, stockage persistant via Cloud Storage | `google-cloud-aiplatform` (Python) | Facturation du notebook (CPU/GPU) + stockage Cloud Storage |
| **Vertex AI Training** | Exécution de jobs de formation (custom containers ou scripts) | `aiplatform.CustomJob` | CPU/​GPU * heure + coût du stockage des artefacts (Bucket) |
| **Vertex AI Prediction** | Déploiement d’endpoints pour inference (online) ou batch prediction | `aiplatform.Endpoint` | CPU/​GPU * heure d’allocation + nombre de prédictions (par 1 000) |
| **Vertex AI Feature Store** | Gestion centralisée des features (online + offline) | `aiplatform.Featurestore` | Stockage offline (GB‑mois) + stockage online (GB‑mois) + requêtes en ligne |
| **Vertex AI Pipelines** | Orchestration de workflows Kubeflow sur GKE‑Autopilot | `kfp` (Python DSL) | CPU/​GPU * heure des pods + stockage des artefacts |
| **Gemini API** (Gemini 1.5/2.0) | Modèles de génération de texte, code et multimodal | `google-generativeai` | Nombre de tokens d’entrée + tokens générés (tarif par 1 000) |

> **Note de facturation** : les coûts GPU sont facturés à la seconde, arrondis au 1 minute. Les tarifs varient selon la zone (ex. `us-central1` = $2.83 / heure pour A100, `europe-west1` ≈ $2.96).  

### 1.2 Modèle de facturation de Vertex AI  

```text
Coût total = Σ (CPU‑heure × tarif_CPU) 
           + Σ (GPU‑heure × tarif_GPU) 
           + Σ (stockage_artéfacts_GB‑mois × tarif_Stockage) 
           + Σ (prédictions × tarif_par_1k) 
           + Σ (tokens_Gemini × tarif_par_1k)
```

- **CPU‑heure** : `e2-standard-4` = $0.134/heure (US)  
- **GPU‑heure** : `nvidia-tesla-a100` = $2.83/heure (US)  
- **Stockage artefacts** : Cloud Storage Standard = $0.020/GB‑mois  

#### Exemple de calcul  
Un job d’entraînement de 3 h sur 1 A100 + 2 vCPU + 8 GiB RAM, générant 5 GB d’artefacts :

```
GPU : 3 h × $2.83 = $8.49
CPU : 3 h × $0.134 = $0.40
Stockage : 5 GB × $0.020 = $0.10
Total ≈ $9.00
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

---

## Module 2 — contenu

## 2.1 Ingestion des données dans Vertex AI Dataset  

| Source | Méthode d’import | Points de contrôle obligatoires |
|--------|------------------|---------------------------------|
| Cloud Storage (CSV, JSONL, TFRecord) | `aiplatform.TextDataset.create` ou `aiplatform.ImageDataset.create` | Vérifier le **schema** (colonnes, types) avec `gcloud storage cp` + `pandas.read_csv` avant import. |
| BigQuery | `aiplatform.TabularDataset.create` (paramètre `bigquery_source`) | S’assurer que la requête ne dépasse **10 Go** de données exportées (limite d’import). |
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

print(f"Statut de la validation : {validation.state}")
```

**Pièges courants**  

| Symptom | Cause probable | Remède |
|---------|----------------|--------|
| `InvalidArgument: Column X missing` | Le CSV ne contient pas la colonne attendue par le schéma. | Ajoutez la colonne ou mettez à jour le schéma via `schema_uri`. |
| `ValueError: NaN found in required column` | Valeur manquante dans une colonne marquée `required`. | Imputez (`df.fillna`) ou définissez la colonne comme `optional` dans le schéma. |
| `ResourceExhausted: quota exceeded` | Import > 10 GiB ou dépassement du quota `aiplatform.datasets.create`. | Découpez le fichier, ou demandez une augmentation de quota via Cloud Console. |

---

## 2.3 Création d’un Feature Store  

### 2.3.1 Création du Feature Store (ressource globale)

```python
fs = aiplatform.Featurestore.create(
    display_name="ecom_featurestore",
    online_store_fixed_node_count=2,   # 2 nœuds = ~1 GiB RAM chacun, suffisant pour < 10 M d'entities
    online_store_enable_automatic_scaling=True,
    sync=True,
)
print(f"Featurestore ARN : {fs.resource_name}")
```

| Paramètre | Valeur par défaut | Impact |
|-----------|-------------------|--------|
| `online_store_fixed_node_count` | `1` | Nombre de nœuds de la boutique en ligne (coût + capacité). |
| `online_store_enable_automatic_scaling` | `False` | Si `True`, GCP ajuste le nombre de nœuds en fonction du QPS. |
| `offline_store

---

## Module 3 — contenu

## Module 3 – Entraînement de modèles : Custom Training & AutoML  

### 1. Environnement de travail avec Vertex AI Workbench  

| Élément | Valeur attendue | Vérification |
|--------|------------------|--------------|
| **Machine type** | `n1-standard-8` (8 vCPU, 30 GiB RAM) ou plus | `gcloud compute machine-types describe n1-standard-8` |
| **GPU** | NVIDIA A100 (40 GB) – `a100` ou `a100-40gb` | `gcloud compute accelerator-types list --filter="name:a100"` |
| **Quota GPU** | ≥ 1 A100 dans la zone du Workbench | `gcloud compute regions describe <REGION> --format="value(quotas)"` |
| **Image** | `gcr.io/deeplearning-platform-release/tf-gpu.2-12` (TensorFlow 2.12 + GPU) ou `pytorch-gpu.2-2` (PyTorch 2.2) | `gcloud compute images list --project=deeplearning-platform-release` |

> **Note** : le Workbench crée automatiquement un service‑account `vertex‑ai‑workbench@PROJECT.iam.gserviceaccount.com`. Attribuez‑lui les rôles `aiplatform.user` et `storage.objectAdmin` pour éviter les erreurs d’accès.

### 2. Construction d’un container d’entraînement custom  

#### 2.1. Structure du répertoire  

```
my_custom_job/
├── Dockerfile
├── setup.py               # si vous utilisez un package Python
├── requirements.txt
└── trainer/
    ├── __init__.py
    └── train.py          # point d’entrée
```

#### 2.2. Dockerfile (exemple TensorFlow 2.12, GPU)

```dockerfile
# Base image officielle contenant TensorFlow GPU
FROM gcr.io/deeplearning-platform-release/tf-gpu.2-12

# Crée un répertoire de travail
WORKDIR /app

# Copie les fichiers de dépendances
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie le code source
COPY trainer/ ./trainer/

# Définit le point d’entrée du container
ENTRYPOINT ["python", "-m", "trainer.train"]
```

*Commentaires*  

- `gcr.io/deeplearning-platform-release/*` est maintenu par Google ; les tags sont **immuables**.  
- `--no-cache-dir` évite d’encombrer l’image avec le cache pip, ce qui réduit la taille finale (< 1 GiB).  
- L’entrée `python -m trainer.train` garantit que le module est exécuté même si le répertoire est monté en volume.

#### 2.3. `requirements.txt` (exemple)

```
tensorflow==2.12.0
pandas
scikit-learn
google-cloud-aiplatform>=1.30.0
```

#### 2.4. Script d’entraînement (`trainer/train.py`)

```python
#!/usr/bin/env python
"""
Entraînement d’un modèle de classification d’iris avec TensorFlow.
Le script lit les données depuis Cloud Storage, entraîne, puis sauvegarde
les artefacts dans le répertoire /output (monté par Vertex AI).
"""

import os
import tensorflow as tf
import pandas as pd
from google.cloud import storage

# ----------------------------------------------------------------------
# 1️⃣ Lecture des paramètres d’environnement injectés par Vertex AI
# ----------------------------------------------------------------------
PROJECT = os.getenv("AIP_PROJECT_ID")
REGION  = os.getenv("AIP_REGION")
BUCKET  = os.getenv("AIP_TRAINING_DATA_URI")   # ex: gs://my-bucket/iris.csv
OUTPUT_DIR = os.getenv("AIP_MODEL_DIR")        # ex: /output/model

# ----------------------------------------------------------------------
# 2️⃣ Chargement des données depuis Cloud Storage
# ----------------------------------------------------------------------
def load_data(uri: str) -> tf.data.Dataset:
    # Utilise pandas pour le CSV, puis convertit en tf.data
    df = pd.read_csv(uri)
    labels = df.pop("species").astype("int32")
    ds = tf.data.Dataset.from_tensor_slices((df.values.astype("float32"), labels.values))
    ds = ds.shuffle(buffer_size=len(df)).batch(32)
    return ds

# ----------------------------------------------------------------------
# 3️⃣ Définition du modèle
# ----------------------------------------------------------------------
def build_model(input_dim: int) -> tf.keras.Model:
    model = tf.keras.Sequential([
        tf.keras.layers.InputLayer(input_shape=(input_dim,)),
        tf.keras.layers.Dense(64, activation="relu"),
        tf.keras.layers.Dense(3, activation="softmax")
    ])
    model.compile(
        optimizer="adam",
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"]
    )
    return model

# ----------------------------------------------------------------------
# 4️⃣ Entraînement
# ----------------------------------------------------------------------
def main():
    # 4.1 Chargement
    dataset = load_data(BUCKET)
    sample = next(iter(dataset))
    input_dim = sample[0].shape[1]

    # 4.2 Construction
    model = build_model(input_dim)

    # 4.3 Callback TensorBoard (écrit dans /output/tb)
    tb_callback = tf.keras.callbacks.TensorBoard(
        log_dir=os.path.join(OUTPUT_DIR, "tensorboard")
    )

    # 4.4 Entraînement
    model.fit(dataset, epochs=20, callbacks=[tb_callback])

    # 4.5 Sauvegarde du modèle (SavedModel format)
    model.save(os.path.join(OUTPUT_DIR, "saved_model"))
    print(f"Modèle sauvegardé dans {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
```

*Points de contrôle*  

| Étape | Vérification | Action corrective |
|------|--------------|-------------------|
| Lecture du

---

## Module 4 — contenu

## 4.1 Vue d’ensemble du workflow CI/CD avec Vertex AI Pipelines  

| Étape | Service GCP | Artefact produit | Points de contrôle |
|------|--------------|------------------|---------------------|
| **Pré‑traitement** | Vertex AI Pipelines (composant Python) → Cloud Storage (raw / transformed) | `dataset_train.parquet`, `dataset_val.parquet` | Validation du schéma avec **Vertex AI Data Validation** |
| **Entraînement** | Vertex AI Training (CustomJob) → Artifact Registry (container) | `model.tar.gz`, `metadata.json` | Vérification du `training_output` dans **Vertex AI Experiments** |
| **Enregistrement** | Vertex AI Model Registry (`aiplatform.Model.upload`) | Version de modèle (ID) | Tagging (`labels`) et audit (`Cloud Audit Logs`) |
| **Déploiement** | Vertex AI Endpoint (`aiplatform.Endpoint.create` ou `.deploy`) | Endpoint ID, `deployed_model_id` | Traffic split, `machine_type`, `min_replica_count`/`max_replica_count` |
| **Monitoring** | Vertex AI Model Monitoring, Cloud Monitoring, Cloud Logging | Métriques de latence, drift, error rate | Alertes (`AlertPolicy`) |

Le pipeline est décrit en **Python DSL** (Kubeflow Pipelines) et compilé en fichier JSON/YAML que Vertex AI Pipelines exécute dans un **Vertex AI Workload Identity** (service account).  

---

## 4.2 Définition d’un composant de pré‑traitement  

```python
# file: components/preprocess.py
import kfp
from kfp import dsl, components
from typing import NamedTuple
import pandas as pd
import pyarrow.parquet as pq
import os

def preprocess(
    gcs_input: str,
    gcs_output_train: str,
    gcs_output_val: str,
    test_size: float = 0.2,
    random_state: int = 42,
) -> NamedTuple('Outputs', [('train_path', str), ('val_path', str)]):
    """Lit un CSV depuis GCS, le nettoie et le scinde en train/val au format Parquet."""
    # 1️⃣ Chargement
    df = pd.read_csv(gcs_input)                     # pandas utilise gcsfs via le token du service account
    # 2️⃣ Nettoyage minimal (exemple vérifiable)
    df = df.dropna(subset=['target'])               # supprime les lignes où la cible est manquante
    # 3️⃣ Split
    from sklearn.model_selection import train_test_split
    train, val = train_test_split(df, test_size=test_size,
                                   random_state=random_state, stratify=df['target'])
    # 4️⃣ Écriture
    train_path = '/tmp/train.parquet'
    val_path   = '/tmp/val.parquet'
    train.to_parquet(train_path, index=False)
    val.to_parquet(val_path, index=False)

    # 5️⃣ Upload vers GCS (utilise la lib google‑cloud‑storage)
    from google.cloud import storage
    client = storage.Client()
    bucket_name, prefix = gcs_output_train.replace('gs://', '').split('/', 1)
    bucket = client.bucket(bucket_name)
    bucket.blob(f'{prefix}/train.parquet').upload_from_filename(train_path)
    bucket_name, prefix = gcs_output_val.replace('gs://', '').split('/', 1)
    bucket = client.bucket(bucket_name)
    bucket.blob(f'{prefix}/val.parquet').upload_from_filename(val_path)

    return (f'gs://{gcs_output_train}/train.parquet',
            f'gs://{gcs_output_val}/val.parquet')

# Export du composant KFP (déploiement sans Dockerfile supplémentaire)
preprocess_op = components.create_component_from_func(
    preprocess,
    base_image='python:3.9-slim',
    packages_to_install=['pandas', 'pyarrow', 'scikit-learn', 'google-cloud-storage']
)
```

*Points de vigilance*  

* Le service account du pipeline doit posséder les rôles `storage.objectAdmin` sur les buckets d’entrée et de sortie.  
* `gcs_input` doit être accessible ; sinon le job échoue avant même le premier `print`.  
* Le paramètre `test_size` ne doit pas être > 0.5 pour éviter un jeu de validation trop petit.  

---

## 4.3 Composant d’entraînement custom (TensorFlow 2.x)  

```python
# file: components/train.py
import kfp
from kfp import dsl, components
from typing import NamedTuple
import os
import json
from google.cloud import aiplatform

def train(
    project: str,
    location: str,
    display_name: str,
    container_image_uri: str,
    gcs_train: str,
    gcs_val: str,
    machine_type: str = 'n1-standard-4',
    accelerator_type: str = 'NVIDIA_TESLA_T4',
    accelerator_count: int = 1,
    replica_count: int = 1,
    args: list = None,
) -> NamedTuple('Outputs',

---

## Module 5 — contenu

## Module 5 – Observabilité, optimisation et mise à l’échelle des modèles Gemini sur Vertex AI  

### 5.1. Principes d’observabilité sur Vertex AI  

| Niveau | Service | Métrique clé | Où la retrouver |
|--------|---------|--------------|-----------------|
| **Infrastructure** | Cloud Monitoring (metrics) | `aiplatform.googleapis.com/custom_job/accelerator_duty_cycle` | Console > Monitoring > Metrics Explorer |
| **Plate‑forme** | Vertex AI Experiments | `training_loss`, `validation_accuracy` | Console > Vertex AI > Experiments |
| **Modèle en production** | Vertex AI Prediction (Endpoints) | `prediction_latency`, `prediction_count`, `model_error_rate` | Console > Vertex AI > Endpoints > Metrics |
| **Données** | Cloud Audit Logs + Data Catalog | `data_read`, `data_write` sur les datasets | Cloud Logging > Log Explorer (filter `resource.type="aiplatform.googleapis.com/Dataset"` ) |

*Les logs d’audit sont automatiquement créés pour chaque appel `aiplatform.googleapis.com/*`. Ils sont immuables et conservés 30 jours par défaut (modifiable via la politique de rétention du bucket de logs).*

#### 5.1.1. Instrumentation du code de modèle Gemini  

```python
import time
import logging
from google.cloud import aiplatform
from google.cloud.aiplatform import gapic as aip_gapic
from google.protobuf import json_format
from google.protobuf.struct_pb2 import Value

# Initialise le client Vertex AI (déploiement dans le même projet)
aiplatform.init(project="my-gcp-project", location="europe-west1")

# Logger compatible Cloud Logging
logger = logging.getLogger("gemini_observability")
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
logger.addHandler(handler)
logger.setLevel(logging.INFO)

def predict_with_observability(endpoint_id: str, instances: list[dict]) -> list[dict]:
    """Envoie une requête de prédiction et journalise latence + statut."""
    start = time.time()
    endpoint = aiplatform.Endpoint(endpoint_name=endpoint_id)

    try:
        response = endpoint.predict(instances=instances, timeout=30)
        latency_ms = (time.time() - start) * 1000
        logger.info(
            "prediction_success",
            extra={"custom_dimensions": {"latency_ms": latency_ms, "n_instances": len(instances)}},
        )
        return response.predictions
    except Exception as exc:
        latency_ms = (time.time() - start) * 1000
        logger.error(
            "prediction_failure",
            exc_info=True,
            extra={"custom_dimensions": {"latency_ms": latency_ms, "error": str(exc)}},
        )
        raise
```

*Le `extra["custom_dimensions"]` est reconnu par Cloud Logging comme **structured logging** ; les champs apparaissent automatiquement comme dimensions dans Cloud Monitoring → Metrics Explorer (`logging.googleapis.com/user/latency_ms`).*  

### 5.2. Optimisation des coûts GPU/TPU pour Gemini  

| Ressource | Facteur d’ajustement | Commande gcloud / SDK | Impact mesurable |
|-----------|----------------------|----------------------|------------------|
| **GPU** | `accelerator_type` (A2 vs. A100) | `gcloud ai custom-jobs create --accelerator-type=nvidia-tesla-a100 --accelerator-count=1` | A100 ≈ 2× le TFLOPS d’un A2, coût ≈ 1,4× |
| **TPU** | `accelerator_type` `v4-8` vs `v4-32` | `aiplatform.CustomJob(..., machine_type="tpu-v4-8")` | V4‑32 offre 4× la bande passante, coût ≈ 4× |
| **Batch size** | Ajuster à la capacité du GPU (mémoire) | `--args="--batch-size=256"` | Augmente le throughput jusqu’à la saturation de la mémoire, réduit le temps total d’entraînement de 15‑30 % |
| **Mixed precision** | `tf.keras.mixed_precision.set_global_policy('mixed_float16')` (TF) ou `torch.backends.cuda.amp.autocast` (PyTorch) | Aucun coût additionnel, nécessite GPU ≥ V100 | Réduction du temps d’entraînement de 20‑35 % sans perte de précision sur la plupart des modèles Gemini |

#### 5.2.1. Exemple : passage à la précision mixte sur un modèle Gemini (TensorFlow 2.13)

```python
import tensorflow as tf
from tensorflow import keras

# Activation du mode mixed precision
tf.keras.mixed_precision.set_global_policy('mixed_float16')

# Modèle simple compatible Gemini (Transformer‑based)
inputs = keras.Input(shape=(None,), dtype="int32", name="input_ids")
embedding = keras.layers.Embedding(input_dim=30522, output_dim=768)(inputs)
x = keras.layers.MultiHeadAttention(num_heads=12, key_dim=64)(embedding, embedding)
x = keras.layers.GlobalAveragePooling1D()(x)
logits = keras.layers.Dense(2, dtype="float32")(x)   # sortie en float32 pour stabilité loss
model = keras.Model(inputs, logits)

model.compile(
    optimizer=keras.optimizers.Adam(learning_rate=3e-4),
    loss=keras.losses.SparseCategoricalCrossentropy(from_logits=True),
    metrics=["accuracy"],
)

# Entraînement sur Vertex AI (CustomJob)
aiplatform.init(project="my-gcp-project", location="us-central1")
custom_job = aiplatform.CustomJob(
    display_name="gemini-mixed-precision",
    worker_pool_specs