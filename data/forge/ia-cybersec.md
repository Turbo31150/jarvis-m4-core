# IA pour la Cybersécurité

> Référence `ia-cybersec` · 99 €

## Plan

## Module 1 – Fondamentaux de l’IA appliquée à la cybersécurité  
**Objectif d’apprentissage** : Être capable de sélectionner, entraîner et valider un modèle d’apprentissage supervisé pour la classification de flux réseau, avec une précision ≥ 85 % sur un jeu de test séparé.  

- Représentation des données réseau (NetFlow, pcap) sous forme de vecteurs de caractéristiques.  
- Pré‑traitement : normalisation, encodage des variables catégorielles, gestion des déséquilibres (SMOTE, undersampling).  
- Algorithmes de classification classiques (logistic regression, random forest, gradient boosting) et critères d’évaluation (confusion matrix, ROC AUC).  
- Validation croisée stratifiée et réglage d’hyper‑paramètres (grid search, random search).  
- Mise en place d’un pipeline Scikit‑learn reproductible (Pipeline, ColumnTransformer).  

## Module 2 – Détection d’anomalies par apprentissage non supervisé  
**Objectif d’apprentissage** : Implémenter un autoencodeur à couches entièrement connectées capable de détecter les anomalies réseau avec un taux de faux positifs ≤ 5 % sur un jeu de données de référence (NSL‑KDD).  

- Principes des autoencodeurs et fonction de perte (MSE, reconstruction error).  
- Architecture de réseaux de neurones profonds (Keras/TensorFlow ou PyTorch).  
- Sélection du seuil de détection à partir de la distribution de l’erreur de reconstruction.  
- Comparaison avec d’autres méthodes d’anomalie (Isolation Forest, One‑Class SVM).  
- Visualisation des espaces latents (t‑SNE, UMAP) pour interpréter les anomalies.  

## Module 3 – Analyse de malware avec le machine learning  
**Objectif d’apprentissage** : Construire un classifieur de type XGBoost qui identifie correctement au moins 90 % des échantillons malveillants dans le dataset EMBER 2020.  

- Extraction de caractéristiques statiques (hash, entropie, imports/exports).  
- Utilisation du format PEFile et de la bibliothèque pefile (Python).  
- Entraînement d’un modèle XGBoost avec gestion du déséquilibre (scale_pos_weight).  
- Métriques spécifiques aux malwares (precision, recall, F1‑score).  
- Analyse d’importance des features et génération de rapports d’interprétabilité (SHAP).  

## Module 4 – Sécurité des modèles d’IA (adversarial ML)  
**Objectif d’apprentissage** : Générer des exemples adversaires contre un classifieur de phishing et réduire la perte de précision de plus de 30 % grâce à une défense basée sur l’entraînement adversarial.  

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

> **Note** : les flux sont souvent agrégés sur un intervalle de temps (ex. 60 s). L’agrégation doit être appliquée **avant** le split train/test pour éviter le « data leakage ».

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

> **Piège** : ne pas normaliser les adresses IP conduit à des valeurs de l’ordre de 10⁹, qui dominent les gradients des modèles linéaires.  

---

## 1.2 Pré‑traitement  

| Étape | Action | Implémentation scikit‑learn | Pourquoi |
|-------|--------|----------------------------|----------|
| Normalisation | `StandardScaler` (z‑score) ou `MinMaxScaler` | `StandardScaler()` | Met toutes les variables à la même échelle, indispensable pour la régression logistique et les SVM. |
| Encodage catégoriel | `OneHotEncoder` pour protocoles rares | `OneHotEncoder(handle_unknown='ignore')` | Les modèles basés sur les arbres gèrent les entiers, mais les modèles linéaires ont besoin d’un encodage sans ordre. |
| Gestion du déséquilibre | `SMOTE` (sur‑échantillonnage) ou `RandomUnderSampler` | `imblearn.over_sampling.SMOTE(k_neighbors=5)` | Le ratio benign/malveillant est souvent < 5 % en production ; sans correction, la précision globale masque un rappel quasi nul. |
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
| **Hypothèse d’anomalie** | Le modèle est entraîné uniquement sur des données « normales ». Les exemples anormaux ont un **reconstruction error** (RE) plus élevé que la majorité des données d’entraînement. |
| **Seuil de décision** | Le seuil τ est généralement fixé à un quantile (ex. 95ᵉ) de la distribution du RE sur un jeu de validation normal. Tout RE > τ ⇒ anomalie. |
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
    """Encodeur → latent_dim → décodeur symétrique."""
    inputs = layers.Input(shape=(dim,))
    # Encodeur
    x = layers.Dense(128, activation="relu")(inputs)
    x = layers.Dense(64, activation="relu")(x)
    x = layers.Dense(32, activation="relu")(x)
    latent = layers.Dense(latent_dim, activation="linear", name="latent")(x)
    # Décodeur
    x = layers.Dense(32, activation="relu")(latent)
    x = layers.Dense(64, activation="relu")(x)
    x = layers.Dense(128, activation="relu")(x)
    outputs = layers.Dense(dim, activation="linear")(x)
    return models.Model(inputs, outputs, name="autoencoder")

autoencoder = build_autoencoder(input_dim, latent_dim=16)
autoencoder.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=1e-3),
                    loss="mse")

# 4. Entraînement avec early stopping
es = callbacks.EarlyStopping(monitor="val_loss", patience=5, restore_best_weights=True)

history = autoencoder.fit(
    X_train, X_train,
    epochs=100,
    batch_size=256,
    shuffle=True,
    validation_data=(X_val, X_val),
    callbacks=[es],
    verbose=0,
)

# 5. Calcul du RE et définition du seuil
re_train = np.mean(np.square(X_train - autoencoder.predict(X_train)), axis=1)
tau = np.percentile(re_train, 95)   # 95ᵉ percentile → 5 % de faux positifs théoriques

# 6. Évaluation sur l’ensemble complet (normaux + anomalies)
re_all = np.mean(np.square(X_processed - autoencoder.predict(X_processed)), axis=1)
y_pred = (re_all > tau).astype(int)

print("Confusion matrix")
print(confusion_matrix(y, y_pred))
print("ROC‑AUC :", roc_auc_score(y, re_all))

# 7. Extraction du latent space pour visualisation
encoder = models.Model(autoencoder.input,
                       autoencoder.get_layer("latent").output)

latent_vectors = encoder.predict(X_processed)

# Sauvegarde du modèle (optionnel)
autoencoder.save("autoencoder_nslkdd.h5")
```

### Points clés du code

| Ligne | Pourquoi |
|------|----------|
| `ColumnTransformer` | Traite simultanément normalisation numérique et encodage one‑hot, évitant les fuites de données entre

---

## Module 3 — contenu

## 3.1 Contexte et exigences  

- **Dataset** : **EMBER 2020** (https://github.com/elastic/ember).  
  - 1 000 000 d’échantillons (≈ 900 k benignes, 100 k malveillants).  
  - Chaque fichier PE a déjà été transformé en 2384 vecteurs de caractéristiques (float32).  
- **Objectif** : classer les échantillons avec **XGBoost** et atteindre **≥ 90 % de rappel** (détection) sur la classe *malware* tout en conservant une précision raisonnable.  
- **Contraintes** : déséquilibre important (≈ 1 : 9). On utilisera `scale_pos_weight` et/ou un sur‑échantillonnage léger.  

---

## 3.2 Chargement du jeu de données  

```python
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier
from sklearn.metrics import classification_report, roc_auc_score

# Le jeu de données EMBER est fourni sous forme de fichiers .npz
# Chaque fichier contient deux tableaux : 'features' (N, 2384) et 'labels' (N,)
def load_ember(npz_path: str) -> tuple[np.ndarray, np.ndarray]:
    data = np.load(npz_path, allow_pickle=True)
    X = data['features'].astype(np.float32)
    y = data['labels'].astype(np.int8)
    return X, y

X, y = load_ember('ember_2018.npz')          # Exemple avec la version 2018 (compatible 2020)
print(f"Shape : {X.shape}, Positives : {y.sum()}, Negatives : {len(y)-y.sum()}")
```

*Résultat attendu* (exemple) :

```
Shape : (1000000, 2384), Positives : 100000, Negatives : 900000
```

---

## 3.3 Pré‑traitement minimal  

EMBEDR fournit déjà des valeurs normalisées (float32 entre 0 et 1).  
Les seules étapes nécessaires :

| Étape | Pourquoi | Implémentation |
|------|-----------|----------------|
| **Suppression des colonnes à variance nulle** | Évite des splits inutiles dans les arbres. | `X = X[:, X.var(axis=0) > 0]` |
| **Conversion en `np.float32`** | XGBoost utilise `float32` pour la vitesse mémoire. | déjà fait dans le loader. |
| **Gestion du déséquilibre** | `scale_pos_weight = n_neg / n_pos` compense le déséquilibre dans la fonction de perte. | `scale_pos_weight = (len(y) - y.sum()) / y.sum()` |

```python
# Suppression des colonnes constantes
var = X.var(axis=0)
X = X[:, var > 0]

scale_pos_weight = (len(y) - y.sum()) / y.sum()
print(f"scale_pos_weight = {scale_pos_weight:.2f}")
```

---

## 3.4 Partition train / test  

```python
X_train, X_test, y_train, y_test = train_test_split(
    X, y,
    test_size=0.20,
    stratify=y,          # conserve le ratio 1:9 dans les deux splits
    random_state=42
)
```

---

## 3.5 Modélisation avec XGBoost  

```python
# Hyper‑paramètres de base (valeurs éprouvées pour EMBER)
params = {
    "objective": "binary:logistic",
    "eval_metric": "auc",
    "learning_rate": 0.1,
    "max_depth": 6,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "scale_pos_weight": scale_pos_weight,
    "n_estimators": 300,
    "tree_method": "hist",          # accélère l'entraînement sur CPU
    "verbosity": 0,
}

model = XGBClassifier(**params, random_state=42)

model.fit(
    X_train, y_train,
    early_stopping_rounds=20,
    eval_set=[(X_test, y_test)],
    verbose=False
)

# Meilleur nombre d'arbres retenu
best_n = model.best_iteration + 1
print(f"Best n_estimators (early stopping) : {best_n}")
```

**Évaluation**  

```python
y_pred_proba = model.predict_proba(X_test)[:, 1]
y_pred = (y_pred_proba >= 0.5).astype(int)

print(classification_report(y_test, y_pred, digits=4))
print(f"ROC‑AUC : {roc_auc_score(y_test, y_pred_proba):.4f}")
```

Exemple de sortie (les chiffres varient légèrement selon la seed) :

```
              precision    recall  f1-score   support
0           0.9873    0.9985    0.9928   180000
1           0.8254    0.5900    0.6880    20000

accuracy                           0.9853   200000
macro avg

---

## Module 4 — contenu

## 4.1. Menaces adversariales sur les modèles de cybersécurité  

| Type d’attaque | Objectif | Métrique de succès | Implémentation typique |
|----------------|----------|--------------------|------------------------|
| **FGSM** (Fast Gradient Sign Method) | Maximiser la perte en un pas de gradient | ‑ Δ accuracy ≥ 30 % ou taux de succès ≥ 80 % | `torch.nn.functional.cross_entropy` + `torch.sign(grad)` |
| **PGD** (Projected Gradient Descent) | Itérer FGSM avec projection dans un ε‑ball | même que FGSM, mais plus robuste | boucle `for i in range(k): …` |
| **Carlini‑Wagner (L₂)** | Minimiser la distance L₂ tout en changeant la classe | distance moyenne L₂ < ε cible | `torch.optim.Adam` sur variable `δ` avec contrainte `||δ||₂` |

Les modèles de phishing (texte ou URL) sont souvent des classifieurs **logistic regression** ou **CNN** sur des embeddings. Les attaques ci‑dessous ciblent la fonction de perte du modèle (cross‑entropy) et supposent un accès **white‑box** (poids et gradients disponibles).  

---

## 4.2. Exemple complet : attaque FGSM puis entraînement adversarial sur un classifieur de phishing  

> **Environnement** : Python 3.10, PyTorch 2.2, `torchtext` pour le pré‑traitement, `advertorch` (facultatif).  
> **Dataset** : *PhishTank* (URL + label). Nous ne chargerons que les colonnes `url` et `label`.  

```python
# --------------------------------------------------------------
# 1. Imports et configuration
# --------------------------------------------------------------
import torch, torch.nn as nn, torch.optim as optim
from torch.utils.data import DataLoader, Dataset
from torchtext.vocab import build_vocab_from_iterator
from torch.nn.utils.rnn import pad_sequence
import re, string, random, json, pathlib

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
SEED = 42
torch.manual_seed(SEED)
random.seed(SEED)

# --------------------------------------------------------------
# 2. Mini‑dataset (URL → 0/1)
# --------------------------------------------------------------
class PhishDataset(Dataset):
    def __init__(self, path: pathlib.Path, vocab=None, max_len=200):
        data = json.loads(path.read_text())
        self.urls = [x["url"] for x in data]
        self.labels = torch.tensor([int(x["label"]) for x in data], dtype=torch.long)
        self.max_len = max_len
        if vocab is None:
            vocab = build_vocab_from_iterator(
                (self.tokenize(u) for u in self.urls), specials=["<pad>", "<unk>"]
            )
            vocab.set_default_index(vocab["<unk>"])
        self.vocab = vocab

    @staticmethod
    def tokenize(text):
        # tokenisation très simple : caractères alphanum + '.' '/' '-'
        return re.findall(r"[a-zA-Z0-9\.\-_/]+", text.lower())

    def __len__(self): return len(self.urls)

    def __getitem__(self, idx):
        tokens = self.tokenize(self.urls[idx])
        ids = torch.tensor([self.vocab[t] for t in tokens], dtype=torch.long)
        # padding / truncation
        if len(ids) > self.max_len:
            ids = ids[:self.max_len]
        return ids, self.labels[idx]

def collate_batch(batch):
    ids, labels = zip(*batch)
    ids = pad_sequence(ids, batch_first=True, padding_value=0)  # 0 = <pad>
    return ids.to(DEVICE), torch.stack(labels).to(DEVICE)

# --------------------------------------------------------------
# 3. Modèle très simple : Embedding + GlobalAvgPool + Linear
# --------------------------------------------------------------
class PhishCNN(nn.Module):
    def __init__(self, vocab_size, embed_dim=64):
        super().__init__()
        self.emb = nn.Embedding(vocab_size, embed_dim, padding_idx=0)
        self.fc = nn.Linear(embed_dim, 2)   # 2 classes
    def forward(self, x):
        # x : [B, L]
        mask = (x != 0).unsqueeze(-1).float()          # ignore padding
        emb = self.emb(x) * mask
        avg = emb.sum(dim=1) / mask.sum(dim=1).clamp(min=1.0)
        return self.fc(avg)

# --------------------------------------------------------------
# 4. Entraînement standard (baseline)
# --------------------------------------------------------------
def train_one_epoch(model, loader, opt, criterion):
    model.train()
    tot_loss, tot_correct = 0.0, 0
    for X, y in loader:
        opt.zero_grad()
        logits = model(X)
        loss = criterion(logits, y)
        loss.backward()
        opt.step()
        tot_loss += loss.item() * X.size(0)
        tot_correct += (logits.argmax(1) == y).sum().item()
    return tot_loss / len(loader.dataset), tot_correct / len(loader.dataset)

def evaluate(model, loader, criterion):
    model.eval()
    tot_loss, tot_correct = 0.0, 0
    with torch.no_grad():
        for X, y in loader:
            logits = model(X)
            loss = criterion(logits, y)
            tot_loss += loss.item() * X.size(0)
            tot_correct += (logits.argmax(1) == y).sum().item()

---

## Module 5 — contenu

## Module 5 – Déploiement, monitoring et gouvernance des modèles IA en cybersécurité  

### 5.1 Principes de mise en production  

| Aspect | Détails techniques vérifiables |
|--------|--------------------------------|
| **Serialisation** | `joblib.dump(model, path)` conserve les poids + les paramètres de `scikit‑learn`; `torch.save(state_dict, path)` pour PyTorch. `pickle` doit être limité à des environnements de confiance (CVE‑2020‑1570). |
| **API de prédiction** | FastAPI (≥ 0.78) + Pydantic pour validation JSON. Temps de réponse < 50 ms sur CPU i7‑10700K pour un modèle RandomForest (100 arbres). |
| **Conteneurisation** | Dockerfile basé sur `python:3.11-slim`. Taille image < 150 Mo si `pip install --no-cache-dir`. |
| **Orchestration** | Kubernetes Deployment + Service (type ClusterIP). Liveness‑probe `/healthz` → 200 OK, readiness‑probe `/ready` → 200 OK uniquement si le modèle chargé. |
| **CI/CD** | GitHub Actions → `docker build` → `docker push` → `kubectl rollout restart`. |
| **Observabilité** | Prometheus exporter (`prometheus_fastapi_instrumentator`). Métriques : `request_duration_seconds`, `prediction_errors_total`. |
| **Détection de dérive (drift)** | `alibi-detect` : `DataDriftTest` sur les vecteurs d’entrée en temps réel. Seuil de p‑value = 0.05 déclenche alerte Slack. |
| **Gestion des secrets** | `python-dotenv` + Kubernetes Secrets. Aucun secret en clair dans l’image Docker. |
| **Hardening du service** | `uvicorn --workers 4 --limit-concurrency 100`. Rate‑limit avec `slowapi` (max 10 req/s/IP). |
| **Traçabilité** | `mlflow` ou `dvc` pour versionner le modèle (`mlflow.log_model`). Chaque déploiement porte le tag Git SHA. |

---

### 5.2 Architecture de référence  

```
+-------------------+       +-------------------+       +-------------------+
|  CI/CD pipeline   | --->  |  Container Registry| --->  |  Kubernetes Cluster|
+-------------------+       +-------------------+       +-------------------+
                                   |                         |
                                   v                         v
                         +-------------------+      +-------------------+
                         |  Docker Image     |      |  Prometheus       |
                         |  (FastAPI + model)|      |  (scrape /metrics)|
                         +-------------------+      +-------------------+
                                   |                         |
                                   v                         v
                         +-------------------+      +-------------------+
                         |  FastAPI Service  | <--> |  Alerting (Slack) |
                         |  /predict endpoint|      +-------------------+
                         +-------------------+
```

---

### 5.3 Exemple de code complet (FastAPI + scikit‑learn)  

```python
# file: app/main.py
import joblib
import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, validator
from prometheus_fastapi_instrumentator import Instrumentator
import logging
import os

# ----------------------------------------------------------------------
# 1️⃣ Configuration du logger (fichier rotatif, niveau INFO)
# ----------------------------------------------------------------------
log_path = os.getenv("LOG_PATH", "/var/log/prediction.log")
logging.basicConfig(
    filename=log_path,
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

# ----------------------------------------------------------------------
# 2️⃣ Modèle et pipeline (chargement unique à l'import)
# ----------------------------------------------------------------------
MODEL_PATH = os.getenv("MODEL_PATH", "/app/model.joblib")
try:
    model = joblib.load(MODEL_PATH)          # type: sklearn.pipeline.Pipeline
except Exception as exc:
    logging.error(f"Impossible de charger le modèle : {exc}")
    raise

# ----------------------------------------------------------------------
# 3️⃣ Schéma d'entrée (validation stricte)
# ----------------------------------------------------------------------
class FlowFeatures(BaseModel):
    src_ip: str = Field(..., regex=r"^\d{1,3}(\.\d{1,3}){3}$")
    dst_ip: str = Field(..., regex=r"^\d{1,3}(\.\d{1,3}){3}$")
    src_port: int = Field(..., ge=0, le=65535)
    dst_port: int = Field(..., ge=0, le=65535)
    protocol: int = Field(..., ge=0, le=255)
    packet_len: float = Field(..., gt=0)

    @validator("*")
    def no_nan(cls, v):
        if isinstance(v, float) and np.isnan(v):
            raise ValueError("Valeur