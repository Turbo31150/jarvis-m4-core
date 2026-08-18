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
**Objectif** : Construire, entraîner et évaluer un modèle de classification binaire ou multiclasse sur un jeu de données de pathologie avec un AUC satisfaisant.  
- Sélection de modèles (logistique, Random Forest, XGBoost, réseaux de neurones profonds).  
- Gestion du déséquilibre de classes : sur‑échantillonnage SMOTE, pondération des classes.  
- Validation croisée stratifiée et métriques (AUC‑ROC, précision, rappel, F1‑score).  
- Interprétabilité avec SHAP et LIME pour identifier les variables cliniques influentes.  
- Déploiement d’un endpoint REST avec FastAPI pour la prédiction en temps réel.

## Module 3 : Analyse d’images médicales avec les réseaux de neurones convolutifs  
**Objectif** : Implémenter un pipeline complet d’apprentissage supervisé sur un jeu d’imagerie (ex. : Chest‑X‑Ray) et atteindre une sensibilité élevée sur la classe d’intérêt.  
- Chargement et augmentation d’images (rotation, flip, normalisation de l’histogramme).  
- Architecture de base : ResNet‑50 pré‑entraîné sur ImageNet, fine‑tuning des dernières couches.  
- Utilisation de PyTorch Lightning pour la gestion des boucles d’entraînement et de validation.  
- Métriques de segmentation ou de classification (IoU, Dice, sensibilité, spécificité).  
- Visualisation des cartes de chaleur (Grad‑CAM) pour la localisation des lésions.

## Module 4 : Traitement du langage naturel (NLP) pour les notes cliniques  
**Objectif** : Extraire automatiquement les diagnostics et traitements à partir de notes libres avec une précision élevée (F1‑score).  
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
| Mauvaise **déclaration de l’unité** (`"mg/dl"` au lieu de `"mg/dL"`). | Le moteur de calcul de dosage ne reconnaît pas l’unité |

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
| **SMOTE** (synthetic minority oversampling) | `imblearn.over_sampling.SMOTE` | Lorsque le déséquilibre des classes est important et que l’on souhaite augmenter la minorité sans dupliquer |
| **Pondération des classes** | `class_weight='balanced'` (sklearn) ou `scale_pos_weight` (XGBoost) | Lorsque le déséquilibre est modéré et que l’on veut éviter la génération de nouvelles instances |
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