# IA pour la Cybersécurité

> Référence `ia-cybersec`

## Plan

## Module 1 – Fondamentaux de l’IA appliquée à la cybersécurité  
**Objectif d’apprentissage** : Être capable de sélectionner, entraîner et valider un modèle d’apprentissage supervisé pour la classification de flux réseau, avec une précision élevée sur un jeu de test séparé.  

- Représentation des données réseau (NetFlow, pcap) sous forme de vecteurs de caractéristiques.  
- Pré‑traitement : normalisation, encodage des variables catégorielles, gestion des déséquilibres (SMOTE, undersampling).  
- Algorithmes de classification classiques (logistic regression, random forest, gradient boosting) et critères d’évaluation (confusion matrix, ROC AUC).  
- Validation croisée stratifiée et réglage d’hyper‑paramètres (grid search, random search).  
- Mise en place d’un pipeline Scikit‑learn reproductible (Pipeline, ColumnTransformer).  

## Module 2 – Détection d’anomalies par apprentissage non supervisé  
**Objectif d’apprentissage** : Implémenter un autoencodeur à couches entièrement connectées capable de détecter les anomalies réseau avec un taux de faux positifs faible sur un jeu de données de référence (NSL‑KDD).  

- Principes des autoencodeurs et fonction de perte (MSE, reconstruction error).  
- Architecture de réseaux de neurones profonds (Keras/TensorFlow ou PyTorch).  
- Sélection du seuil de détection à partir de la distribution de l’erreur de reconstruction.  
- Comparaison avec d’autres méthodes d’anomalie (Isolation Forest, One‑Class SVM).  
- Visualisation des espaces latents (t‑SNE, UMAP) pour interpréter les anomalies.  

## Module 3 – Analyse de malware avec le machine learning  
**Objectif d’apprentissage** : Construire un classifieur de type XGBoost qui identifie correctement la majorité des échantillons malveillants dans le dataset EMBER 2020.  

- Extraction de caractéristiques statiques (hash, entropie, imports/exports).  
- Utilisation du format PEFile et de la bibliothèque pefile (Python).  
- Entraînement d’un modèle XGBoost avec gestion du déséquilibre (scale_pos_weight).  
- Métriques spécifiques aux malwares (precision, recall, F1‑score).  
- Analyse d’importance des features et génération de rapports d’interprétabilité (SHAP).  

## Module 4 – Sécurité des modèles d’IA (adversarial ML)  
**Objectif d’apprentissage** : Générer des exemples adversaires contre un classifieur de phishing et réduire la perte de précision de manière significative grâce à une défense basée sur l’entraînement adversarial.  

- Types d’attaques (FGSM, PGD, Carlini‑Wagner) et leurs implémentations (cleverhans, advertorch).  
- Évaluation de la robustesse : métriques de succès d’attaque, distance L₂/L∞.  
- Défenses : adversarial training, randomization, distillation.  
- Mise en place d’un

---

## Module 1 — contenu

## 1.1 Représentation des flux réseau  

| Source | Format brut | Extraction → vecteur | Exemple de champ |
|--------|------------|---------------------|------------------|
| NetFlow / IPFIX | texte ou binaire (ex. `nfdump -r file.nfdump`) | parsing → dictionnaire → tableau | `src_ip`, `dst_ip`, `src_port`, `dst_port`, `protocol`, `bytes`, `packets`, `duration` |
| PCAP | binaire (libpcap) | `dpkt` / `scapy` → `Flow` (5‑tuple + métriques) | même que ci‑dessus + `flags`, `payload_len` |

Le vecteur final doit être **numérique** et de dimension fixe.  
- **IP** → 4 octets → conversion en entier (`int.from_bytes`) ou en 2 bits de préfixe (ex. `/24`).  
- **Port** → entier (0‑65535).  
- **Protocole** → variable catégorique (`TCP=6`, `UDP=17`, `ICMP=1`).  
- **Durée** → secondes, normalisée (voir 1.2).  

> **Note** : les flux sont souvent agrégés sur un intervalle de temps. L’agrégation doit être appliquée **avant** le split train/test pour éviter le « data leakage ».

```python
# flow_to_features.py
import ipaddress
import numpy as np

def ip_to_int(ip_str: str) -> int:
    """Convertit une adresse IPv4 en entier 32‑bits."""
    return int(ipaddress.IPv4Address(ip_str))

def flow_to_vector(flow: dict) -> np.ndarray:
    """
    Transforme un dictionnaire de flux en vecteur de 9 caractéristiques :
    [src_ip, dst_ip, src_port, dst_port, protocol, bytes, packets, duration, flag_syn]
    """
    src_ip = ip_to_int(flow["src_ip"])
    dst_ip = ip_to_int(flow["dst_ip"])
    src_port = flow["src_port"]
    dst_port = flow["dst_port"]
    protocol = flow["protocol"]          # déjà entier (ex. 6, 17)
    total_bytes = flow["bytes"]
    total_pkts = flow["packets"]
    duration = flow["duration"]          # en secondes, float
    # flag SYN : 1 si le flag SYN est présent dans le premier paquet du flux, sinon 0
    flag_syn = 1 if flow.get("flags", "").startswith("S") else 0

    return np.array([src_ip, dst_ip, src_port, dst_port,
                     protocol, total_bytes, total_pkts,
                     duration, flag_syn], dtype=float)
```

> **Piège** : ne pas normaliser les adresses IP conduit à des valeurs très grandes, qui dominent les gradients des modèles linéaires.  

---

## 1.2 Pré‑traitement  

| Étape | Action | Implémentation scikit‑learn | Pourquoi |
|-------|--------|----------------------------|----------|
| Normalisation | `StandardScaler` (z‑score) ou `MinMaxScaler` | `StandardScaler()` | Met toutes les variables à la même échelle, indispensable pour la régression logistique et les SVM. |
| Encodage catégoriel | `OneHotEncoder` pour protocoles rares | `OneHotEncoder(handle_unknown='ignore')` | Les modèles basés sur les arbres gèrent les entiers, mais les modèles linéaires ont besoin d’un encodage sans ordre. |
| Gestion du déséquilibre | `SMOTE` (sur‑échantillonnage) ou `RandomUnderSampler` | `imblearn.over_sampling.SMOTE(k_neighbors=5)` | Le ratio benign/malveillant est souvent très faible en production ; sans correction, la précision globale masque un rappel quasi nul. |
| Découpage train / test | `StratifiedShuffleSplit` | `StratifiedShuffleSplit(n_splits=1, test_size=0.2, random_state=42)` | Garantit la même proportion de classes dans chaque split. |

```python
# preprocessing_pipeline.py
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from imblearn.over_sampling import SMOTE
from sklearn.pipeline import Pipeline
from sklearn.model_selection import StratifiedShuffleSplit

# Exemple de DataFrame
df = pd.read_csv("flows_features.csv")          # colonnes = vecteur + label
X = df.drop(columns="label")
y = df["label"]

numeric_features = ["src_ip", "dst_ip", "src_port", "dst_port",
                    "bytes", "packets", "duration"]
categorical_features = ["protocol", "flag_syn"]

numeric_transformer = Pipeline(steps=[
    ("scaler", StandardScaler())
])

categorical_transformer = Pipeline(steps=[
    ("onehot", OneHotEncoder(handle_unknown="ignore"))
])

preprocess = ColumnTransformer(
    transformers=[
        ("num", numeric_transformer, numeric_features),
        ("cat", categorical_transformer, categorical_features)
    ])

# Pipeline complet (pré‑traitement → modèle)
def make_pipeline(model):
    return Pipeline(steps=[
        ("preprocess", preprocess),
        ("smote", SMOTE(random_state=42)),
        ("clf", model)
    ])

# Split stratifié
sss = StratifiedShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
train_idx, test_idx = next(sss.split(X, y))
X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
```

> **Piège** : placer `SMOTE` **avant** le `ColumnTransformer` entraîne une fuite de l’information de la moyenne/variance calculée sur les exemples synthétiques. Le `SMOTE` doit être **après** le

---

## Module 2 — contenu

## 2.1 Principes des auto‑encodeurs pour la détection d’anomalies  

| Concept | Description vérifiable |
|---------|------------------------|
| **Auto‑encodeur** | Réseau de neurones à deux parties : encodeur 𝑓(·) → vecteur latent 𝑧, décodeur 𝑔(·) → reconstruction 𝑥̂. La fonction de perte standard est l’erreur quadratique moyenne (MSE) : 𝓛 = ‖𝑥 − 𝑥̂‖². |
| **Hypothèse d’anomalie** | Le modèle est entraîné uniquement sur des données « normales ». Les exemples anormaux ont un **reconstruction error** plus élevé que la majorité des données d’entraînement. |
| **Seuil de décision** | Le seuil τ est généralement fixé à un quantile de la distribution du RE sur un jeu de validation normal. Tout RE > τ ⇒ anomalie. |
| **Avantages** | Apprentissage non supervisé, capacité à capturer des corrélations non linéaires, pas besoin d’étiquetage. |
| **Limites** | Sensible au déséquilibre de la distribution de caractéristiques, nécessite un jeu d’entraînement représentatif des « normaux ». |

---

## 2.2 Architecture recommandée (Keras / TensorFlow 2.x)

```python
# -*- coding: utf-8 -*-
"""
Auto‑encodeur dense pour la détection d’anomalies sur le jeu NSL‑KDD (version 0.2).
Version TensorFlow 2.12, Keras API.
"""

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.metrics import roc_auc_score, confusion_matrix
import tensorflow as tf
from tensorflow.keras import layers, models, callbacks

# ----------------------------------------------------------------------
# 1. Chargement & pré‑traitement
# ----------------------------------------------------------------------
# NSL‑KDD CSV (déjà nettoyé, colonnes numériques + 3 catégorielles)
df = pd.read_csv("NSL_KDD_Train.csv")          # 125 973 lignes, 41 features + label
y = (df["label"] != "normal").astype(int)      # 0 = normal, 1 = anomalie (pour validation)
X = df.drop(columns=["label"])

numeric_cols = X.select_dtypes(include=["int64", "float64"]).columns.tolist()
categorical_cols = X.select_dtypes(include=["object"]).columns.tolist()

preprocess = ColumnTransformer(
    transformers=[
        ("num", StandardScaler(), numeric_cols),
        ("cat", OneHotEncoder(sparse=False, handle_unknown="ignore"), categorical_cols),
    ]
)

X_processed = preprocess.fit_transform(X)

# 2. Séparer uniquement les exemples normaux pour l’entraînement
X_norm = X_processed[y == 0]
X_train, X_val = train_test_split(
    X_norm, test_size=0.2, random_state=42
)

# 3. Construction du modèle
input_dim = X_train.shape[1]

def build_autoencoder(dim, latent_dim=16):