# IA pour l'Éducation & E-learning

> Référence `ia-education` · 49 €

## Plan

## Module 1 – Fondamentaux de l’IA appliquée à l’éducation  
**Objectif mesurable** : Sélectionner, entraîner et évaluer un modèle de classification de texte capable de trier des questions d’élèves avec une précision ≥ 80 % sur un jeu de validation de 500 exemples.  

**Notions couvertes**  
- Représentation vectorielle du texte : TF‑IDF, embeddings Word2Vec/GloVe.  
- Algorithmes de classification supervisée : SVM, Random Forest, Logistic Regression (scikit‑learn).  
- Métriques d’évaluation : précision, rappel, F1‑score, matrice de confusion.  
- Gestion du déséquilibre de classes : sur‑échantillonnage, sous‑échantillonnage, poids de classe.  
- Pipeline de pré‑traitement (tokenisation, lemmatisation, stop‑words) avec spaCy ou NLTK.  

---

## Module 2 – Personnalisation adaptative des parcours d’apprentissage  
**Objectif mesurable** : Implémenter un système de recommandation qui propose au moins trois ressources pertinentes à un élève en fonction de son historique, avec un taux de clics prédit (CTR) supérieur à 12 % sur un test A/B de 1000 sessions.  

**Notions couvertes**  
- Filtrage collaboratif (user‑based, item‑based) et modèles de factorisation matricielle (ALS, SVD).  
- Recommandations basées sur le contenu : similarité cosinus sur les embeddings de documents.  
- Méthodes hybrides : combinaison pondérée de scores collaboratif + contenu.  
- Evaluation offline : RMSE, MAP, NDCG.  
- Mise en place d’un test A/B simple avec Google Optimize ou un serveur Flask.  

---

## Module 3 – Analyse des données d’interaction et détection des difficultés  
**Objectif mesurable** : Construire un tableau de bord qui identifie les 10 % d’élèves présentant le plus fort risque d’échec, avec un rappel ≥ 85 % sur un jeu de données historiques de 10 000 enregistrements.  

**Notions couvertes**  
- Extraction de features à partir de logs (temps passé, nombre de tentatives, séquences d’actions).  
- Modèles de prédiction du décrochage : régression logistique, Gradient Boosting (XGBoost, LightGBM).  
- Interprétabilité : SHAP values, coefficients de régression.  
- Visualisation interactive avec Plotly/Dash ou Streamlit.  
- Gestion de la confidentialité : anonymisation, conformité RGPD.  

---

## Module 4 – Génération de contenus éducatifs par IA  
**Objectif mesurable** : Produire automatiquement un exercice à choix multiples (question, 4 propositions, réponse correcte) à partir

---

## Module 1 — contenu

## 1.1 Représentation vectorielle du texte  

| Méthode | Principes | Dimensions typiques | Avantages / limites |
|--------|-----------|--------------------|----------------------|
| **TF‑IDF** | Comptage des occurrences pondéré par l’inverse de la fréquence du terme dans le corpus. | `n_features = min(max_features, vocab_size)` (ex. 10 000). | Simple, interprétable. Ne capture pas la sémantique (synonymie, polysémie). |
| **Word2Vec / GloVe** | Embeddings pré‑entraînés (300 d) ou entraînés sur le corpus. Chaque token → vecteur dense. | 300 (ou 100‑200 selon le modèle). | Capture la similarité sémantique, mais nécessite agrégation (moyenne, TF‑IDF‑pondérée). |
| **FastText** | Sous‑mots → vecteurs, utile pour le vocabulaire limité. | 300. | Gère les mots OOV, mais augmente le temps d’inférence. |

**Agrégation** (pour Word2Vec/GloVe) :  
- moyenne simple (`np.mean(embeddings, axis=0)`)  
- moyenne pondérée par TF‑IDF (`np.average(embeddings, weights=tfidf_weights, axis=0)`)  

> **Note** : pour un jeu de 500 ex de validation, la différence de performance entre TF‑IDF et embeddings est souvent marginale ; privilégier TF‑IDF pour la rapidité d’itération.

---

## 1.2 Pipeline de pré‑traitement (spaCy)

```python
# -*- coding: utf-8 -*-
import spacy
import string
from sklearn.base import BaseEstimator, TransformerMixin

nlp = spacy.load("fr_core_news_md")  # modèle medium, 300 d embeddings

class SpacyPreprocessor(BaseEstimator, TransformerMixin):
    """
    Transforme une liste de phrases en tokens lemmatisés,
    supprime ponctuation, chiffres et stop‑words.
    Retourne une chaîne de tokens séparés par espaces,
    compatible avec CountVectorizer / TfidfVectorizer.
    """
    def __init__(self, keep_pos=None):
        self.keep_pos = keep_pos  # ex. ["NOUN","VERB"] ou None

    def fit(self, X, y=None):
        return self

    def _clean_token(self, token):
        if token.is_stop or token.is_punct or token.is_space:
            return None
        if token.like_num:
            return None
        if self.keep_pos and token.pos_ not in self.keep_pos:
            return None
        return token.lemma_.lower()

    def transform(self, X):
        cleaned = []
        for doc in nlp.pipe(X, batch_size=32, disable=["parser", "ner"]):
            lemmas = [self._clean_token(t) for t in doc]
            lemmas = [l for l in lemmas if l]          # filtre None
            cleaned.append(" ".join(lemmas))
        return cleaned
```

*Utilisation avec scikit‑learn* :

```python
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC

pipeline = Pipeline([
    ("prep", SpacyPreprocessor(keep_pos=["NOUN", "VERB"])),
    ("tfidf", TfidfVectorizer(max_df=0.9, min_df=3, ngram_range=(1,2))),
    ("clf", LinearSVC(class_weight="balanced"))  # gère le déséquilibre
])
```

---

## 1.3 Algorithmes de classification supervisée  

| Algorithme | Implémentation scikit‑learn | Complexité d’entraînement | Particularités |
|-----------|----------------------------|--------------------------|----------------|
| **LinearSVC** | `sklearn.svm.LinearSVC` | O(N · d) | Bon pour TF‑IDF haute dimension, `class_weight='balanced'` ajuste le déséquilibre. |
| **LogisticRegression** | `sklearn.linear_model.LogisticRegression` (solver=`liblinear` ou `saga`) | O(N · d) | Retourne des probabilités (`predict_proba`). |
| **RandomForestClassifier** | `sklearn.ensemble.RandomForestClassifier` | O(N · d · n_estimators) | Moins sensible aux features corrélées, mais plus lent. |
| **XGBoost** | `xgboost.XGBClassifier` | O(N · d · n_estimators) | Gère très bien le déséquilibre via `scale_pos_weight`. |

**Choix recommandé** : `LinearSVC` ou `LogisticRegression` avec `class_weight='balanced'` pour le premier prototype (rapidité + précision élevée sur texte sparse).

---

## 1.4 Gestion du déséquilibre de classes  

1. **Ré‑échantillonnage**  
   ```python
   from imblearn.over_sampling import RandomOverSampler
   ros = RandomOverSampler(random_state=42)
   X_res, y_res = ros.fit_resample(X_vec, y)
   ```
2. **Poids de classe** (préféré quand le nombre d’exemples est faible)  
   ```python
   clf = LinearSVC(class_weight='balanced')
   ```
3. **Threshold tuning** : après `LogisticRegression`, ajuster le seuil de décision pour maximiser la précision tout en conservant le rappel souhaité.  

> **Piège** : le sur‑échantillonnage crée des copies exactes, ce qui peut conduire à un sur‑apprentissage sur les minorités. Utiliser `SMOTE` seulement si

---

## Module 2 — contenu

## Module 2 – Personnalisation adaptative des parcours d’apprentissage  

### 1. Principes de base des systèmes de recommandation  

| Concept | Description vérifiable | Référence |
|--------|------------------------|-----------|
| **Filtrage collaboratif** | Prédit la préférence d’un utilisateur à partir des comportements d’utilisateurs similaires (user‑based) ou d’items similaires (item‑based). | Ricci et al., *Recommender Systems Handbook* (2015) |
| **Factorisation matricielle** | Décompose la matrice d’interactions \(R \in \mathbb{R}^{m \times n}\) (m = élèves, n = ressources) en deux matrices latentes \(U \in \mathbb{R}^{m \times k}\) et \(V \in \mathbb{R}^{n \times k}\) telles que \(R \approx UV^{\top}\). | Koren, *Matrix Factorization Techniques for Recommender Systems* (2009) |
| **Recommandation basée sur le contenu** | Compare les vecteurs d’embeddings des items (ex. TF‑IDF, Sentence‑BERT) avec le profil de l’utilisateur (moyenne pondérée des embeddings des items déjà consommés). | Lops et al., *Content‑Based Recommender Systems* (2011) |
| **Hybridation** | Combine plusieurs scores (ex. 0,7 × collaboratif + 0,3 × contenu) pour pallier les limites de chaque approche. | Burke, *Hybrid Recommender Systems* (2002) |

---

### 2. Pipeline de données  

1. **Collecte des interactions**  
   - Événement `view`, `click`, `submit`, `score`.  
   - Stockage sous forme de table `interactions(user_id, item_id, timestamp, event_type, weight)`.  
   - **Poids** : `view=1`, `click=2`, `submit=3`, `score=4` (exemple de pondération).  

2. **Pré‑traitement**  
   ```python
   import pandas as pd
   # Charger les logs bruts
   df = pd.read_csv('interactions.csv')
   # Filtrer les événements utiles
   df = df[df['event_type'].isin(['view','click','submit'])]
   # Créer une colonne de score pondéré
   weight_map = {'view':1, 'click':2, 'submit':3}
   df['rating'] = df['event_type'].map(weight_map)
   # Agréger par (user,item) → rating moyen
   rating_matrix = df.groupby(['user_id','item_id'])['rating'].mean().reset_index()
   ```
   - **Piège** : ne pas normaliser les timestamps peut introduire un biais temporel lors de la validation (le modèle apprend des interactions futures).  

3. **Construction de la matrice d’interaction**  
   ```python
   from scipy.sparse import csr_matrix
   user_ids = rating_matrix['user_id'].astype('category')
   item_ids = rating_matrix['item_id'].astype('category')
   rows = user_ids.cat.codes
   cols = item_ids.cat.codes
   data = rating_matrix['rating'].astype(float)
   R = csr_matrix((data, (rows, cols)), shape=(user_ids.cat.categories.size,
                                               item_ids.cat.categories.size))
   ```
   - **Piège** : l’ordre des catégories doit être conservé entre entraînement et prédiction ; sauvegarder les mappings `user_id ↔ index` et `item_id ↔ index`.  

---

### 3. Modèles de factorisation matricielle  

#### 3.1 ALS (Alternating Least Squares) avec `implicit`  

```python
# pip install implicit
import implicit
import numpy as np

# ALS attend une matrice *confidence* = 1 + alpha * rating
alpha = 40
C = (R * alpha).astype('double')
C.data = np.ones_like(C.data) + C.data   # 1 + alpha*rating

model = implicit.als.AlternatingLeastSquares(
    factors=64,          # dimension latente k
    regularization=0.1,
    iterations=20,
    calculate_training_loss=True,
    random_state=42,
)

model.fit(C)

# Recommandations pour l'utilisateur 0 (index interne)
user_idx = 0
recommended = model.recommend(user_idx, C[user_idx], N=5, filter_already_liked_items=True)
print("Top‑5 items :", recommended)
```
- **Explication** : `C` représente la confiance que l’utilisateur apprécie l’item. ALS minimise \(\|C - UV^{\top}\|_{F}^{2} + \lambda(\|U\|_{F}^{2}+\|V\|_{F}^{2})\) en alternant la résolution de systèmes linéaires pour \(U\) puis \(V\).  

#### 3.2 SVD (Sur‑décomposition) avec `surprise`  

```python
# pip install scikit-surprise
from surprise import Dataset, Reader, SVD
from surprise.model_selection import train_test_split

# Convertir le DataFrame en format Surprise
reader = Reader(rating_scale=(1, 4))
data = Dataset.load_from_df(rating_matrix[['user_id','item_id','rating']], reader)

trainset, testset = train_test_split(data, test_size=0.2, random_state=42)

svd = SVD(n_factors=64, reg_all=0.02, random_state=42)
svd.fit(trainset)

# Prédire la note d'un couple (user,item)
uid, iid = 'U123', 'I456'
pred = svd.predict(uid, iid)
print(f"Score prédit pour {uid}-{iid} : {pred.est:.3f}")
```
- **Explication** :

---

## Module 3 — contenu

## 3.1 Extraction de features à partir de logs d’interaction  

| Source de log | Exemple de champ | Feature dérivée | Type |
|--------------|------------------|----------------|------|
| `timestamp_start` / `timestamp_end` | 2024‑03‑12 09:15:00 / 2024‑03‑12 09:18:37 | `duration_sec = (end‑start).total_seconds()` | Numérique continu |
| `event_type` (click, submit, hint) | `click` | `nb_clicks`, `nb_hints`, `nb_submits` (comptage par session) | Numérique discret |
| `resource_id` | `lesson_42` | `unique_resources` (cardinalité) | Numérique discret |
| `attempt_number` | 3 | `mean_attempts`, `max_attempts` (par exercice) | Numérique continu |
| `score` | 0.75 | `mean_score`, `std_score` | Numérique continu |
| `device` | `mobile` | `is_mobile` (binaire) | Binaire |

```python
import pandas as pd
import numpy as np

# -------------------------------------------------
# 1️⃣ Chargement du fichier de logs (CSV)
# -------------------------------------------------
logs = pd.read_csv('logs.csv', parse_dates=['timestamp_start',
                                           'timestamp_end'])

# -------------------------------------------------
# 2️⃣ Agrégation par élève + cours (session)
# -------------------------------------------------
# On suppose que chaque ligne = une interaction sur un exercice
session = (
    logs
    .assign(duration_sec=(logs['timestamp_end'] - logs['timestamp_start'])
            .dt.total_seconds())
    .groupby(['student_id', 'course_id'], as_index=False)
    .agg(
        total_time_sec=('duration_sec', 'sum'),
        nb_events=('event_type', 'count'),
        nb_clicks=('event_type', lambda x: (x == 'click').sum()),
        nb_hints=('event_type', lambda x: (x == 'hint').sum()),
        nb_submits=('event_type', lambda x: (x == 'submit').sum()),
        unique_resources=('resource_id', 'nunique'),
        mean_score=('score', 'mean'),
        std_score=('score', 'std'),
        is_mobile=('device', lambda x: (x == 'mobile').any())
    )
)

# -------------------------------------------------
# 3️⃣ Gestion des valeurs manquantes
# -------------------------------------------------
session['std_score'] = session['std_score'].fillna(0)   # un seul exercice → std = 0
session.head()
```

*Commentaires*  

* `parse_dates` garantit que les timestamps sont des objets `datetime64[ns]`.  
* La fonction lambda dans `agg` permet de compter conditionnellement les événements.  
* `is_mobile` devient `True/False`; on le convertira en `int` (`astype(int)`) avant la modélisation.  

---

## 3.2 Modèles de prédiction du décrochage  

### 3.2.1 Sélection du modèle  

| Modèle | Avantages vérifiables | Inconvénients notables |
|--------|----------------------|------------------------|
| Régression logistique | Interprétable (coefficients), rapide sur jeux ≤ 100 k lignes, probas calibrées | Linéarité → performances limitées si les relations sont non linéaires |
| Gradient Boosting (XGBoost, LightGBM) | Gère variables mixtes, robustesse aux valeurs manquantes, performances SOTA sur tabulaire | Risque d’over‑fitting, besoin de réglage d’hyper‑paramètres, moins transparent (requiert SHAP) |

Pour atteindre **rappel ≥ 85 %** sur les élèves à risque, on privilégie un modèle qui maximise le vrai positif (ex. `scale_pos_weight` dans XGBoost).

### 3.2.2 Pipeline complet (exemple XGBoost)

```python
import xgboost as xgb
from sklearn.model_selection import train_test_split, StratifiedKFold
from sklearn.metrics import recall_score, precision_score, confusion_matrix

# -------------------------------------------------
# 1️⃣ Préparer X, y
# -------------------------------------------------
X = session.drop(columns=['student_id', 'course_id'])
y = session['dropout']               # 1 = risque d’échec, 0 = stable
X['is_mobile'] = X['is_mobile'].astype(int)

# -------------------------------------------------
# 2️⃣ Train / validation split (stratifié)
# -------------------------------------------------
X_train, X_val, y_train, y_val = train_test_split(
    X, y, test_size=0.2, stratify=y, random_state=42)

# -------------------------------------------------
# 3️⃣ Gestion du déséquilibre
# -------------------------------------------------
# poids = n_neg / n_pos (XGBoost attend un ratio > 1)
scale_pos_weight = (y_train == 0).sum() / (y_train == 1).sum()

# -------------------------------------------------
# 4️⃣ Entraînement
# -------------------------------------------------
model = xgb.XGBClassifier(
    n_estimators=300,
    max_depth=5,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    objective='binary:logistic',
    eval_metric='logloss',
    scale_pos_weight=scale_pos_weight,
    n_jobs=4,
    random_state=42
)
model.fit(X_train, y_train,
          eval_set=[(X_val, y_val)],
          early_stopping_rounds=30,
          verbose=False)

# -------------------------------------------------
# 5️⃣ Evaluation du rappel
# -------------------------------------------------
y_pred = (model.predict_proba(X_val)[:, 1] > 0.30).astype(int)   # seuil ajusté

---

## Module 4 — contenu

## 4.1 Concepts clés  

| Concept | Description vérifiable | Référence |
|--------|-----------------------|-----------|
| **LLM à génération contrôlée** | Utilisation de prompts structurés + contraintes de format (JSON, markdown) pour obtenir une sortie prévisible. | 🤖 OpenAI 2023, “Prompt Design” |
| **Fine‑tuning / instruction‑tuning** | Ajustement d’un modèle pré‑entraîné sur un petit corpus d’exemples QCM pour améliorer la pertinence et la conformité du style. | 🤗 HuggingFace 2022, “Fine‑tuning language models” |
| **Post‑processing** | Validation syntaxique (JSON schema), filtrage de réponses hors‑vocabulaire, dé‑duplication des distracteurs. | 📚 Miller 2021, “Data cleaning for NLP” |
| **Évaluation automatique** | Exact‑match sur la structure, BLEU ≥ 0.6 sur le texte, taux de plausibilité des distracteurs (score de similarité cosinus < 0.5 avec la bonne réponse). | 📊 Papineni et al. 2002, “BLEU” |
| **Biais et conformité** | Vérifier que les contenus ne contiennent pas de stéréotypes, respect du RGPD (pas de données personnelles dans les questions). | 🏛️ CNIL 2023, “Guidelines IA éducatives” |

---

## 4.2 Pipeline de génération d’un QCM  

1. **Sélection du sujet** – entrée libre ou issue d’un référentiel (ex. “les fractions”).
2. **Prompt de génération** – texte structuré qui impose le format JSON suivant :

```json
{
  "question": "...",
  "options": ["A) …", "B) …", "C) …", "D) …"],
  "answer": "B"
}
```

3. **Appel au modèle** – via `transformers` (Flan‑T5‑base) ou l’API OpenAI (gpt‑3.5‑turbo).  
4. **Validation du JSON** – `jsonschema` pour s’assurer que les 4 options sont uniques et que la clé `answer` correspond à l’indice.  
5. **Filtrage sémantique** – calcul du **cosine similarity** entre chaque distracteur et la bonne réponse à l’aide de `sentence‑transformers/all-MiniLM-L6-v2`. On accepte uniquement les distracteurs avec `sim < 0.5`.  
6. **Enrichissement** – ajout d’un champ `difficulty` (facile/moyen/difficile) estimé par le nombre de tokens de la question.  
7. **Stockage** – insertion dans une base SQLite ou un fichier JSONL pour le LMS.

---

## 4.3 Exemple de code (Python 3.9+)

```python
# -*- coding: utf-8 -*-
"""
Génération d'un QCM à partir d'un sujet donné.
Modèle : flan-t5-base (HuggingFace)
Contraintes : sortie JSON, 4 options uniques, distracteurs peu similaires.
"""

import json
import random
from pathlib import Path

import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from sentence_transformers import SentenceTransformer, util
from jsonschema import validate, ValidationError

# 1. Chargement du modèle et du tokenizer
MODEL_NAME = "google/flan-t5-base"
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)

# 2. Embedding model pour le filtrage sémantique
embedder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

# 3. Schéma JSON attendu
SCHEMA = {
    "type": "object",
    "properties": {
        "question": {"type": "string"},
        "options": {
            "type": "array",
            "minItems": 4,
            "maxItems": 4,
            "uniqueItems": True,
            "items": {"type": "string"},
        },
        "answer": {"type": "string", "enum": ["A", "B", "C", "D"]},
    },
    "required": ["question", "options", "answer"],
    "additionalProperties": False,
}


def build_prompt(topic: str) -> str:
    """Construit le prompt en français, impose le format JSON."""
    return f"""Tu es un assistant pédagogique. Génère, en français, un exercice à choix multiples (QCM) sur le sujet suivant : "{topic}".
Le résultat doit être un objet JSON strictement conforme au schéma suivant :

{json.dumps(SCHEMA, indent=2, ensure_ascii=False)}

Respecte exactement ce format, aucune explication supplémentaire."""


def generate_qcm(topic: str, max_tries: int = 3) -> dict:
    """Retourne un dictionnaire conforme au schéma ou lève une exception."""
    prompt = build_prompt(topic)

    for attempt

---

## Module 5 — contenu

## Module 5 – Déploiement, monitoring et maintenance des modèles IA en e‑learning  

### 1. Architecture de mise en production  

| Niveau | Rôle | Outils typiques |
|--------|------|----------------|
| **Modèle** | Entraînement, versionnage, artefacts | `scikit‑learn`, `torch`, `tensorflow`; versionnage avec **MLflow** ou **DVC** |
| **API** | Exposition du modèle via HTTP/REST | **FastAPI**, **Flask**, **TorchServe** |
| **Conteneur** | Isolation, reproductibilité | **Docker** (Dockerfile), **OCI** |
| **Orchestration** | Scaling horizontal, gestion du trafic | **Kubernetes** (Deployment, Service, HPA) |
| **CI/CD** | Build, test, déploiement automatisés | **GitHub Actions**, **GitLab CI**, **Argo CD** |
| **Monitoring** | Latence, taux d’erreur, drift de données | **Prometheus** + **Grafana**, **Evidently AI**, **Seldon Core** |
| **Sécurité** | Authentification, chiffrement, conformité RGPD | **OAuth2**, **HTTPS**, **Vault** pour secrets |

> **Vérifiable** : La combinaison FastAPI + Docker + Kubernetes est recommandée par la documentation officielle de FastAPI (fastapi.tiangolo.com) pour le déploiement de modèles ML en production.

### 2. Versionnage et traçabilité du modèle  

```bash
# Exemple de versionnage avec MLflow
mlflow run . -P alpha=0.01 -P n_estimators=200 \
    -e train \
    -A "--experiment-name eLearning_dropout"
```

* `mlflow.log_param`, `mlflow.log_metric`, `mlflow.log_artifact` permettent de reproduire exactement le même artefact (pickle, ONNX, TorchScript).  
* Le **run_id** est stocké dans la base de métadonnées (SQLite ou PostgreSQL) et sert de clé dans le tableau de bord de suivi.

### 3. Conteneurisation du modèle (Docker)  

```dockerfile
# Dockerfile minimal pour un modèle scikit‑learn
FROM python:3.11-slim

# 1. Installer les dépendances système strictes
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential && \
    rm -rf /var/lib/apt/lists/*

# 2. Créer un environnement isolé
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 3. Copier le code et le modèle versionné
COPY src/ ./src/
COPY models/model_v{{MLFLOW_RUN_ID}}.pkl ./models/

# 4. Exposer le port de l'API
EXPOSE 8000

# 5. Lancer l'application FastAPI avec Uvicorn
CMD ["uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "8000"]
```

* **Piège 1** – Oublier de fixer la version de Python et des bibliothèques (`requirements.txt` doit contenir des versions exactes, ex. `scikit-learn==1.4.0`). Sans cela, le même modèle peut produire des prédictions différentes après un rebuild.  
* **Piège 2** – Inclure le répertoire `__pycache__` ou des fichiers de test dans l’image augmente la taille de l’image et peut exposer du code interne. Utiliser `.dockerignore`.

### 4. Service FastAPI avec endpoint de prédiction et health‑check  

```python
# src/api.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import joblib
import numpy as np
import os

app = FastAPI(
    title="eLearning Dropout Predictor",
    version="1.0.0",
    description="Prédit le risque d'abandon d'un élève à partir de ses logs d'interaction."
)

# 1. Chargement du modèle au démarrage (singleton)
MODEL_PATH = os.getenv("MODEL_PATH", "/app/models/model.pkl")
try:
    model = joblib.load(MODEL_PATH)
except Exception as e:
    raise RuntimeError(f"Impossible de charger le modèle : {e}")

# 2. Schéma d'entrée (validation stricte)
class StudentFeatures(BaseModel):
    time_spent: float          # minutes
    attempts: int
    sessions_last_week: int
    avg_score: float           # 0‑1
    video_views: int

# 3. Endpoint de santé (latence < 100 ms)
@app.get("/healthz", summary="Health check")
def health_check():
    return {"status": "ok"}

# 4. Endpoint de prédiction
@app.post("/predict", summary="Prédire le risque d'abandon")
def predict(features: StudentFeatures):
    # Convertir le Pydantic model en tableau numpy 2‑D
    X = np.array([[features.time_spent,
                   features.attempts,
                   features