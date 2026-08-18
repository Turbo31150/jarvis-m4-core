# IA pour la Santé & Médical

> Référence `ia-sante` · 79 €

## Plan

## Module 1 : Fondamentaux de l’IA appliquée aux données de santé  
**Objectif** : Être capable de prétraiter, normaliser et encoder des jeux de données cliniques conformément aux standards HL7 FHIR et aux exigences RGPD.  
- Structuration des dossiers patients selon le modèle FHIR (Resources, Bundles, Profiles).  
- Nettoyage et imputation des valeurs manquantes : méthodes de moyenne, régression, K‑NN.  
- Encodage des variables catégorielles : one‑hot, embeddings, codeurs de fréquence.  
- Normalisation et mise à l’échelle (z‑score, min‑max) pour les modèles de machine learning.  
- Documentation du pipeline de prétraitement avec DVC ou MLflow.

## Module 2 : Modélisation prédictive pour le diagnostic et le pronostic  
**Objectif** : Construire, entraîner et évaluer un modèle de classification binaire ou multiclasse sur un jeu de données de pathologie avec un AUC ≥ 0,80.  
- Sélection de modèles (logistique, Random Forest, XGBoost, réseaux de neurones profonds).  
- Gestion du déséquilibre de classes : sur‑échantillonnage SMOTE, pondération des classes.  
- Validation croisée stratifiée et métriques (AUC‑ROC, précision, rappel, F1‑score).  
- Interprétabilité avec SHAP et LIME pour identifier les variables cliniques influentes.  
- Déploiement d’un endpoint REST avec FastAPI pour la prédiction en temps réel.

## Module 3 : Analyse d’images médicales avec les réseaux de neurones convolutifs  
**Objectif** : Implémenter un pipeline complet d’apprentissage supervisé sur un jeu d’imagerie (ex. : Chest‑X‑Ray) et atteindre une sensibilité ≥ 0,85 sur la classe d’intérêt.  
- Chargement et augmentation d’images (rotation, flip, normalisation de l’histogramme).  
- Architecture de base : ResNet‑50 pré‑entraîné sur ImageNet, fine‑tuning des dernières couches.  
- Utilisation de PyTorch Lightning pour la gestion des boucles d’entraînement et de validation.  
- Métriques de segmentation ou de classification (IoU, Dice, sensibilité, spécificité).  
- Visualisation des cartes de chaleur (Grad‑CAM) pour la localisation des lésions.

## Module 4 : Traitement du langage naturel (NLP) pour les notes cliniques  
**Objectif** : Extraire automatiquement les diagnostics et traitements à partir de notes libres avec une précision ≥ 0,90 (F1‑score).  
- Tokenisation et normalisation avec spaCy et les modèles MedSpaCy.  
- Modélisation de séquence à séquence (BERT‑base, ClinicalBERT) pour la reconnaissance d’entités nommées (NER).  
- Annotation de corpus avec BRAT ou Prodigy et création d’un jeu d’entraînement.  
- Évaluation du NER (precision, recall, F1) et correction post‑traitement par règles regex.  
- Intégration du pipeline dans un serveur d’API (FastAPI) pour la consultation en temps réel.

## Module 5 : Gouvernance, conformité et mise en production sécurisée  
**Objectif** : Déployer un modèle IA certifié conforme aux normes ISO 13485 et aux exigences de la CNIL, avec un audit complet du cycle de vie.  
- Gestion des versions de modèle et traçabilité des données avec DVC et Git‑LFS.  
- Mise en place de tests unitaires et de validation de biais (fairness) avec AIF

---

## Module 1 — contenu

## 1.1 Structuration des dossiers patients selon le modèle FHIR  

| Élément FHIR | Description | Exemple JSON minimal |
|-------------|-------------|----------------------|
| **Patient** | Identité, date de naissance, sexe, identifiants externes. | ```json { "resourceType": "Patient", "id": "12345", "identifier": [{ "system": "urn:oid:1.2.250.1.213.1.1", "value": "NIR-1234567890" }], "name": [{ "family": "Dupont", "given": ["Marie"] }], "gender": "female", "birthDate": "1975-04-12" }``` |
| **Observation** | Valeur d’un paramètre clinique (ex. glycémie). | ```json { "resourceType": "Observation", "id": "obs-001", "status": "final", "code": { "coding": [{ "system": "http://loinc.org", "code": "2345-7", "display": "Glucose [mg/dL]" }]}, "subject": { "reference": "Patient/12345" }, "effectiveDateTime": "2024-03-01T08:30:00Z", "valueQuantity": { "value": 112, "unit": "mg/dL", "system": "http://unitsofmeasure.org", "code": "mg/dL" } }``` |
| **Bundle** | Regroupe plusieurs ressources (Patient + Observations). | ```json { "resourceType": "Bundle", "type": "collection", "entry": [ { "resource": { ...Patient... } }, { "resource": { ...Observation... } } ] }``` |

*Implémentation Python* (bibliothèque officielle `fhir.resources` ≥ 6.0.0) :

```python
# -*- coding: utf-8 -*-
"""
Exemple complet : création d’un Bundle contenant un Patient et deux Observations.
Le résultat est sérialisé en JSON conforme au standard FHIR R4.
"""

from fhir.resources.patient import Patient
from fhir.resources.observation import Observation
from fhir.resources.bundle import Bundle, BundleEntry
from fhir.resources.fhirdate import FHIRDate
from fhir.resources.quantity import Quantity
import json

# 1️⃣ Patient
patient = Patient(
    id="p-001",
    identifier=[{
        "system": "urn:oid:1.2.250.1.213.1.1",
        "value": "NIR-1234567890"
    }],
    name=[{
        "family": "Dupont",
        "given": ["Marie"]
    }],
    gender="female",
    birthDate=FHIRDate("1975-04-12")
)

# 2️⃣ Observation – glycémie
obs_glucose = Observation(
    id="obs-glc-001",
    status="final",
    code={
        "coding": [{
            "system": "http://loinc.org",
            "code": "2345-7",
            "display": "Glucose [mg/dL]"
        }]
    },
    subject={"reference": f"Patient/{patient.id}"},
    effectiveDateTime=FHIRDate("2024-03-01T08:30:00Z"),
    valueQuantity=Quantity(value=112, unit="mg/dL", system="http://unitsofmeasure.org", code="mg/dL")
)

# 3️⃣ Observation – pression systolique
obs_bp = Observation(
    id="obs-bp-001",
    status="final",
    code={
        "coding": [{
            "system": "http://loinc.org",
            "code": "8480-6",
            "display": "Systolic blood pressure"
        }]
    },
    subject={"reference": f"Patient/{patient.id}"},
    effectiveDateTime=FHIRDate("2024-03-01T08:32:00Z"),
    valueQuantity=Quantity(value=138, unit="mmHg", system="http://unitsofmeasure.org", code="mm[Hg]")
)

# 4️⃣ Bundle
bundle = Bundle(
    type="collection",
    entry=[
        BundleEntry(resource=patient),
        BundleEntry(resource=obs_glucose),
        BundleEntry(resource=obs_bp)
    ]
)

# Sérialisation
print(json.dumps(bundle.dict(), indent=2, ensure_ascii=False))
```

> **Vérifiable** : le JSON produit passe la validation du *FHIR Validator* (version 4.0.1).  

### Pièges récurrents  

| Situation | Pourquoi c’est un problème | Remède |
|----------|---------------------------|--------|
| Utilisation d’un **identifiant interne** uniquement (`id`) sans `identifier` : le patient ne peut pas être relié à d’autres systèmes (ex. DMP). | Violation du principe d’interopérabilité (ISO 13606). | Toujours ajouter un `identifier` avec un `system` officiel (OID, UUID, MRN). |
| **Dates au format texte libre** (`"12/04/1975"`). | Le champ `birthDate` attend le format ISO 8601 (`YYYY-MM-DD`). | Normaliser avec `datetime.strftime('%Y-%m-%d')`. |
| Omission du **`resourceType`** dans les objets imbriqués (ex. `Observation` dans un `Bundle`). | Le serveur FHIR rejette le Bundle (erreur 400). | Vérifier que chaque instance possède `resourceType` (automatique avec `fhir.resources`). |
| **Doublons d’identifiants** (`Patient.id` réutilisé). | Conflit de références internes, perte de traçabilité. | Générer des IDs UUID (`uuid4().hex`). |
| Mauvaise **déclaration de l’unité** (`"mg/dl"` au lieu de `"mg/dL"`). | Le moteur de calcul de dosage ne reconnaît pas l’unité

---

## Module 2 — contenu

## 2. Modélisation prédictive pour le diagnostic et le pronostic  

### 2.1. Sélection du modèle  

| Modèle | Points forts | Limites | Quand le choisir |
|-------|--------------|--------|------------------|
| Régression logistique | Interprétable, rapide, bonne base pour des données linéaires | Incapable de capturer des interactions non linéaires | Petit nombre de variables, besoin d’interprétabilité |
| Random Forest | Gère variables mixtes, robuste aux outliers, importance des variables | Mémoire élevée, moins performant sur très grands jeux de données | Données tabulaires, besoin de robustesse |
| XGBoost (gradient‑boosted trees) | Performance SOTA sur tabulaire, gestion du déséquilibre via `scale_pos_weight` | Paramétrage sensible, risque d’over‑fitting | Priorité à la performance, jeu de données moyen‑grand |
| Réseau de neurones (MLP) | Capable d’apprendre des interactions complexes | Nécessite beaucoup de données, difficile à interpréter | Très grand jeu de données, besoin de représentation non linéaire |

> **Règle de sélection** : commencez par un modèle linéaire comme baseline, puis montez en complexité (RF → XGBoost → MLP) en suivant la courbe d’apprentissage.

---

### 2.2. Gestion du déséquilibre de classes  

| Technique | Implémentation | Quand l’utiliser |
|-----------|----------------|------------------|
| **SMOTE** (synthetic minority oversampling) | `imblearn.over_sampling.SMOTE` | Ratio de classes < 1:4, besoin d’augmenter la minorité sans dupliquer |
| **Pondération des classes** | `class_weight='balanced'` (sklearn) ou `scale_pos_weight` (XGBoost) | Petit déséquilibre, on veut éviter la génération de nouvelles instances |
| **Under‑sampling** | `RandomUnderSampler` | Jeux de données très volumineux où la majorité écrase la mémoire |

**Attention** : appliquer le sur‑échantillonnage **après** la division train/validation (pipeline `Pipeline` ou `ColumnTransformer`). Sinon, fuite de l’information (les exemples synthétiques du test apparaissent dans le train).

---

### 2.3. Pipeline complet (exemple avec XGBoost + SMOTE)  

```python
# -*- coding: utf-8 -*-
"""
Pipeline complet : 
- lecture CSV
- split stratifié
- pré‑traitement (imputation, encodage, scaling)
- SMOTE sur le train uniquement
- entraînement XGBoost avec recherche d'hyper‑paramètres
- validation croisée stratifiée
- métriques AUC‑ROC, précision, rappel, F1
- interprétabilité SHAP
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import StratifiedKFold, train_test_split, GridSearchCV
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from imblearn.over_sampling import SMOTE
from imblearn.pipeline import Pipeline as ImbPipeline
import xgboost as xgb
from sklearn.metrics import roc_auc_score, precision_score, recall_score, f1_score
import shap
import joblib

# -------------------------------------------------
# 1. Chargement & split
# -------------------------------------------------
df = pd.read_csv("data/patient_pathology.csv")   # colonne cible = 'target'
X = df.drop(columns="target")
y = df["target"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, stratify=y, random_state=42
)

# -------------------------------------------------
# 2. Définition des colonnes
# -------------------------------------------------
num_cols = X_train.select_dtypes(include=["int64", "float64"]).columns.tolist()
cat_cols = X_train.select_dtypes(include=["object", "category"]).columns.tolist()

numeric_transformer = Pipeline(
    steps=[
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
    ]
)

categorical_transformer = Pipeline(
    steps=[
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("onehot", OneHotEncoder(handle_unknown="ignore")),
    ]
)

preprocess = ColumnTransformer(
    transformers=[
        ("num", numeric_transformer, num_cols),
        ("cat", categorical_transformer, cat_cols),
    ]
)

# -------------------------------------------------
# 3. Pipeline imbriqué (SMOTE + XGBoost)
# -------------------------------------------------
xgb_clf = xgb.XGBClassifier(
    objective="binary:logistic",
    eval_metric="auc",
    use_label_encoder=False,
    n_jobs=-1,
    random_state=42,
)

pipeline = ImbPipeline(
    steps=[
        ("preprocess", preprocess),
        ("smote", SMOTE(sampling_strategy="auto", random_state=42)),
        ("model", xgb_clf),
    ]
)

# -------------------------------------------------
# 4. Recherche d'hyper‑paramètres (grid simple)
# -------------------------------------------------
param_grid = {
    "model__max_depth": [3, 5, 7],
    "model__learning_rate": [0.01, 0.1],
    "model__n_estimators": [100, 300],
    "model__scale_pos_weight": [ (y_train==0).sum() / (y_train==1).sum() ]  # gestion du déséquilibre
}

cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

grid = GridSearchCV(
    estimator=pipeline,
    param_grid=param_grid,

---

## Module 3 — contenu

## 3.1 Chargement et pré‑traitement des images  

| Étape | Fonction PyTorch | Description | Remarque |
|------|------------------|-------------|----------|
| Lecture du dataset | `torchvision.datasets.ImageFolder` | Attend une arborescence `root/<classe>/image.jpg`. | Compatible avec les datasets publics (e.g. NIH Chest‑X‑Ray). |
| Décodage & conversion | `torchvision.transforms.ToTensor()` | Convertit `PIL.Image` en `torch.FloatTensor` de shape `(C, H, W)` et normalise les pixels dans `[0, 1]`. | Nécessaire avant la normalisation des canaux. |
| Normalisation des canaux | `transforms.Normalize(mean, std)` | Soustrait le moyen et divise par l’écart‑type. Pour ImageNet : `mean=[0.485, 0.456, 0.406]`, `std=[0.229, 0.224, 0.225]`. | Si les images sont en niveaux de gris, répéter le canal 3 fois ou ajuster les valeurs. |
| Augmentation (train) | `transforms.RandomResizedCrop(224)`, `RandomHorizontalFlip(p=0.5)`, `RandomRotation(degrees=15)` | Crée de la variance spatiale pour réduire l’over‑fitting. | Appliquer **avant** la normalisation. |
| Redimensionnement (val / test) | `transforms.Resize(256)`, `transforms.CenterCrop(224)` | Garantit une taille d’entrée fixe pour le backbone. | Aucun flip/rotation. |

```python
# fichier: data.py
import pathlib
from torch.utils.data import DataLoader, random_split
from torchvision import transforms, datasets

DATA_ROOT = pathlib.Path("./chest_xray")   # structure: train/NORMAL, train/PNEUMONIA, ...

# Transformations train
train_tf = transforms.Compose([
    transforms.RandomResizedCrop(224, scale=(0.8, 1.0)),
    transforms.RandomHorizontalFlip(p=0.5),
    transforms.RandomRotation(degrees=15),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                         std =[0.229, 0.224, 0.225]),
])

# Transformations validation / test (déterministes)
val_tf = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                         std =[0.229, 0.224, 0.225]),
])

# Chargement du dataset complet (train + val)
full_dataset = datasets.ImageFolder(root=DATA_ROOT / "train", transform=train_tf)

# Split 80/20 stratifié (en fonction des classes)
train_len = int(0.8 * len(full_dataset))
val_len   = len(full_dataset) - train_len
train_set, val_set = random_split(full_dataset,
                                  [train_len, val_len],
                                  generator=torch.Generator().manual_seed(42))

# DataLoader
BATCH_SIZE = 32
train_loader = DataLoader(train_set, batch_size=BATCH_SIZE, shuffle=True,
                          num_workers=4, pin_memory=True)
val_loader   = DataLoader(val_set,   batch_size=BATCH_SIZE, shuffle=False,
                          num_workers=4, pin_memory=True)
```

*Le `random_split` conserve la distribution des classes parce que `ImageFolder` renvoie les indices dans l’ordre alphabétique des dossiers. Si le déséquilibre est important, il faut recourir à `WeightedRandomSampler` (voir 3.4).*

---

## 3.2 Architecture : ResNet‑50 pré‑entraîné + fine‑tuning  

1. **Chargement du backbone**  
   ```python
   import torch
   import torchvision.models as models

   backbone = models.resnet50(pretrained=True)   # poids ImageNet
   ```
2. **Gel partiel** – les 1‑2 premières couches sont généralement conservées figées pour éviter la destruction des filtres bas‑niveau.  
   ```python
   for name, param in backbone.named_parameters():
       if "layer4" not in name:   # ne pas geler les blocs les plus profonds
           param.requires_grad = False
   ```
3. **Adaptation du classifieur** – le `fc` d’origine possède 1000 sorties (ImageNet). On le remplace par un `nn.Linear` à `n_classes`.  
   ```python
   n_classes = 2   # ex. : NORMAL vs PNEUMONIA
   backbone.fc = torch.nn.Sequential(
       torch.nn.Dropout(p=0.5),
       torch.nn.Linear(in_features=backbone.fc.in_features,
                       out_features=n_classes)
   )
   ```
4. **Initialisation du nouveau `Linear`** – la fonction de He (`kaiming_normal_`) est recommandée pour les ReLU.  
   ```python
   torch.nn.init.kaiming_normal_(backbone.fc[1].weight)
   torch.nn.init.constant_(backbone.fc[1].bias, 0.)
   ```

---

## 3.3 Entraînement avec PyTorch Lightning  

```python
# fichier: lit_model.py
import torch
import torch.nn.functional as F
import pytorch_lightning as pl
from torchmetrics import AUROC, Accuracy, Recall, Precision, F1Score

class ChestXRayLitModel(pl.LightningModule):
    def __init__(self, backbone, lr=1e-4, weight_decay=1e-5):
        super().__init__()
        self.save_hyperparameters()          # sauvegarde lr, etc.
        self.model = backbone
        self.lr = lr
        self.weight_decay = weight_decay

        # Métriques (binary classification)
        self.val_auc = AUROC(num_classes=2

---

## Module 4 — contenu

## 4.1. Pipeline général d’extraction d’entités cliniques  

| Étape | Action | Bibliothèque / Outil | Sortie |
|------|--------|----------------------|--------|
| 1. Collecte | Lecture de fichiers texte (UTF‑8) ou de champs DB | `pandas.read_csv`, `sqlalchemy` | `DataFrame` avec colonne `note` |
| 2. Nettoyage de base | Suppression des caractères de contrôle, normalisation Unicode, décodage des entités HTML | `unicodedata.normalize`, `html.unescape` | texte propre |
| 3. Dé‑identification (optionnelle) | Masquage des PHI (nom, date, ID) | `presidio‑anonymizer`, regex personnalisées | texte anonymisé |
| 4. Tokenisation & lemmatisation | Segmentation en tokens, POS, lemmas, dépendances | **spaCy 3** + modèle `en_core_sci_lg` (SciSpaCy) ou `medspacy` | `Doc` spaCy |
| 5. Alignement avec le modèle BERT | Conversion du `Doc` en `input_ids`, `attention_mask` | `transformers.AutoTokenizer` (ex. `emilyalsentzer/Bio_ClinicalBERT`) | tensors PyTorch |
| 6. Inférence NER | Passage du batch dans le modèle, décodage des logits en labels BIO | `transformers.AutoModelForTokenClassification` | listes de (token, label) |
| 7. Post‑traitement | Fusion des sous‑tokens, correction regex (ex. “HTN” → “hypertension”) | fonction Python `merge_subtokens`, `re.sub` | entités finales |
| 8. Export / API | Sérialisation JSON, mise à disposition via FastAPI | `FastAPI`, `uvicorn` | endpoint `/ner` |

---

## 4.2. Implémentation pas à pas  

### 4.2.1. Installation des dépendances (versions fixées)

```bash
pip install "spacy==3.7.2" \
            "medspacy==0.2.4" \
            "scispacy==0.5.4" \
            "torch==2.2.0" \
            "transformers==4.40.0" \
            "datasets==2.18.0" \
            "fastapi==0.111.0" \
            "uvicorn[standard]==0.30.1"
python -m spacy download en_core_sci_lg
```

> **Vérifiable** : `pip show` doit afficher les versions ci‑dessus.

### 4.2.2. Chargement et pré‑traitement des notes

```python
import pandas as pd, unicodedata, html
from pathlib import Path

def load_notes(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path, dtype=str).fillna("")
    # Normalisation Unicode NFC + suppression des caractères de contrôle
    df["note"] = df["note"].apply(
        lambda txt: unicodedata.normalize("NFC", txt.translate(str.maketrans("", "", "\x00-\x1f")))
    )
    # Décodage des entités HTML (ex. &amp; → &)
    df["note"] = df["note"].apply(html.unescape)
    return df

notes_df = load_notes("data/clinical_notes.csv")
print(notes_df.head(2)["note"].iloc[0][:200])
```

### 4.2.3. Dé‑identification (exemple simple)

```python
import re

PATIENT_ID = re.compile(r"\bPATIENT\s*#?\s*\d{1,6}\b", flags=re.I)

def deidentify(text: str) -> str:
    # Remplace les identifiants patient par <PATIENT_ID>
    return PATIENT_ID.sub("<PATIENT_ID>", text)

notes_df["note"] = notes_df["note"].apply(deidentify)
```

> **Piège** : les regex ne capturent pas les variantes « MRN:12345 », « Dr. Smith ». Utiliser un outil dédié (Presidio) pour les environnements réglementés.

### 4.2.4. Tokenisation spaCy + MedSpaCy pipeline

```python
import spacy
import medspacy

# Chargement du modèle SciSpaCy (vocabulaire biomédical)
nlp = spacy.load("en_core_sci_lg")
# Ajout du pipeline MedSpaCy pour la normalisation des unités
nlp.add_pipe("medspacy_contextualizer")
nlp.add_pipe("medspacy_target_matcher")   # détecte "HTN", "DM2", etc.

def spacy_preprocess(text: str):
    doc = nlp(text)
    # Conserver tokens, lemmas et offsets utiles pour le mapping BERT
    tokens = [(t.text, t.lemma_, t.idx, t.idx + len(t)) for t in doc]
    return tokens, doc

sample_tokens, sample_doc = spacy_preprocess(notes_df["note"].iloc[0])
print(sample_tokens[:10])
```

### 4.2.5. Alignement avec ClinicalBERT  

```python
from transformers import AutoTokenizer, AutoModelForTokenClassification
import torch

MODEL_NAME = "emilyalsentzer/Bio_ClinicalBERT"
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, use_fast=True)
model = AutoModelForTokenClassification.from_pretrained(MODEL_NAME, num_labels=9)  # BIO + 4 entités

def encode_for_bert(tokens):
    # tokens : list of (text, lemma

---

## Module 5 — contenu

## 5.1. Gestion du cycle de vie du modèle (MLOps)  

| Étape | Action | Outils (exemple) | Points de contrôle ISO 13485 / CNIL |
|------|--------|-----------------|--------------------------------------|
| 1️⃣  | **Versionnage du code** | Git + Git‑LFS (pour les poids) | Traçabilité des modifications (clause 4.2.2) |
| 2️⃣  | **Versionnage des données** | DVC (`dvc init`, `dvc add`, `dvc push`) | Conservation de la provenance des données (RGPD art. 30) |
| 3️⃣  | **Enregistrement du modèle** | DVC `dvc add model.pkl`; `dvc.yaml` décrivant les étapes | Historique des versions de modèle (ISO 13485 7.5) |
| 4️⃣  | **Métadonnées de conformité** | `model_card.yaml` (nom, version, date, jeu d’entraînement, métriques, limites, données d’origine, consentement) | Documentation obligatoire pour tout dispositif médical (ISO 13485 7.5.1) |
| 5️⃣  | **Tests unitaires & validation** | `pytest`, `hypothesis`, `fairlearn` | Vérification de la robustesse et de l’équité (RGPD art. 5‑principes de licéité) |
| 6️⃣  | **Intégration continue** | GitHub Actions / GitLab CI | Chaque commit déclenche les tests, la validation du DVC et le linting |
| 7️⃣  | **Déploiement sécurisé** | Docker, FastAPI, OAuth2‑JWT, HTTPS (Let’s Encrypt) | Sécurité des données en transit (RGPD art. 32) |
| 8️⃣  | **Monitoring en production** | Prometheus + Grafana, `evidently` pour drift | Détection du dérive de données / modèle (ISO 13485 8.5) |
| 9️⃣  | **Audit & archivage** | Export `dvc metrics show`, logs CI, snapshots Docker (`docker save`) | Dossier d’audit complet (ISO 13485 4.2.4) |

---

## 5.2. Exemple de pipeline automatisé (GitHub Actions)  

```yaml
# .github/workflows/mlops.yml
name: MLOps CI/CD

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  build-test:
    runs-on: ubuntu-latest
    steps:
      # ----- 1️⃣ Checkout & setup -----
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.11"

      # ----- 2️⃣ Cache DVC remote (S3) -----
      - name: Install DVC & dependencies
        run: |
          pip install "dvc[s3]" pandas scikit-learn pytest fairlearn
      - name: Pull data & model artefacts
        env:
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        run: |
          dvc pull -f  # force pull to guarantee reproducibility

      # ----- 3️⃣ Lint & type check -----
      - name: Lint with ruff
        run: pip install ruff && ruff check .

      # ----- 4️⃣ Unit & fairness tests -----
      - name: Run pytest
        run: pytest -v tests/

      # ----- 5️⃣ Validate DVC metrics (AUC ≥ 0.80) -----
      - name: Check model performance
        run: |
          auc=$(dvc metrics show -v | grep auc | awk '{print $2}')
          echo "AUC=$auc"
          python -c "import sys; sys.exit(0) if float('$auc') >= 0.80 else sys.exit(1)"

      # ----- 6️⃣ Build Docker image (only on main) -----
      - name: Build Docker image
        if: github.ref == 'refs/heads/main'
        run: |
          docker build -t registry.example.com/ia-sante:$(git rev-parse --short HEAD) .
          echo ${{ secrets.REGISTRY_PASSWORD }} | docker login registry.example.com -u ${{ secrets.REGISTRY_USER }} --password-stdin
          docker push registry.example.com/ia-sante:$(git rev-parse --short HEAD)

      # ----- 7️⃣ Archive artefacts for audit -----
      - name: Archive artefacts
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: ci-artifacts
          path: |
            dvc.lock
            model_card.yaml
            logs/
```

*Commentaires*  
* `dvc pull -f` garantit que le même jeu de données et le même modèle sont utilisés à chaque run (point de contrôle de traçabilité).  
* La vérification de l’AUC via `dvc metrics` assure que le critère de performance défini dans le cahier des charges (≥ 0,80) est respecté avant tout déploiement.  
* `fairlearn` (installé dans les dépendances) doit être utilisé dans les tests (`tests/test_fairness.py`) pour vérifier que l’écart de taux d’erreur entre les groupes protégés ne dépasse pas 5 % (exigence CNIL sur la non‑discrimination).  
* Le secret du registre Docker doit être stocké dans le **Vault** de GitHub (`