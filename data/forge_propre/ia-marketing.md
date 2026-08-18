# IA pour le Marketing Digital

> Référence `ia-marketing`

## Plan

## Module 1 – Fondamentaux de l’IA appliquée au marketing digital  
**Objectif d’apprentissage** : Être capable de sélectionner, préparer et exploiter les données marketing pour entraîner un modèle d’apprentissage supervisé.  
- Types de données marketing (CRM, logs web, données publicitaires) et leurs formats (CSV, JSON, Parquet).  
- Méthodes de nettoyage et d’enrichissement (imputation, normalisation, encodage catégoriel).  
- Partitionnement des jeux de données (train/validation/test) selon les bonnes pratiques de validation croisée.  
- Construction d’un pipeline de pré‑traitement avec `scikit‑learn` (`Pipeline`, `ColumnTransformer`).  

## Module 2 – Modélisation prédictive pour la performance publicitaire  
**Objectif d’apprentissage** : Implémenter, évaluer et déployer un modèle de prédiction du CPC (coût par clic) avec une précision élevée.  
- Régression linéaire et ridge, sélection de variables (Lasso, RFE).  
- Modèles d’ensemble (Random Forest, Gradient Boosting, XGBoost) et réglage d’hyper‑paramètres (`GridSearchCV`).  
- Métriques de performance (RMSE, MAE, R²) et validation temporelle (TimeSeriesSplit).  
- Export du modèle au format ONNX pour intégration dans les plateformes DSP.  

## Module 3 – Segmentation et ciblage automatisés  
**Objectif d’apprentissage** : Concevoir un système de clustering qui identifie plusieurs segments d’utilisateurs distincts avec un indice de silhouette satisfaisant.  
- Algorithmes de clustering (K‑means, DBSCAN, Agglomerative Clustering).  
- Réduction de dimensionnalité (PCA, t‑SNE) pour visualisation et pré‑traitement.  
- Interprétation des clusters (profilage, importance des variables).  
- Implémentation d’un service REST (FastAPI) qui renvoie le segment d’un utilisateur en temps réel.  

## Module 4 – Optimisation en temps réel des campagnes publicitaires  
**Objectif d’apprentissage** : Mettre en place une boucle d’optimisation qui ajuste les enchères CPC à intervalles réguliers en fonction du ROAS (Return on Ad Spend) cible.  
- Formulation du problème comme un bandit multi‑bras (UCB, Thompson Sampling).  
- Simulation d’environnements publicitaires avec `gym‑advertising`.  
- Intégration d’une API d’enchères (ex. Google Ads API) via OAuth2.  
- Monitoring des KPI avec Grafana et alertes automatisées.  

## Module 5 – Explicabilité et conformité des modèles IA  
**Objectif d’apprentissage** : Produire un rapport d’explicabilité conforme au RGPD qui détaille les facteurs influençant les décisions de ciblage pour toutes les prédictions.  
- Calcul des valeurs SHAP et LIME pour modèles de classification et régression.  
- Génération de rapports PDF automatisés (`ReportLab`) incluant graphiques et seuils de conformité.  
- Gestion des biais de données (détection de corrélations indésirables, re‑bal...
---

## Module 1 — contenu

## Module 1 – Fondamentaux de l’IA appliquée au marketing digital  

### 1.1 Types de données marketing et formats

| Source | Exemple de champ | Format le plus répandu | Particularités |
|--------|------------------|------------------------|----------------|
| CRM (Customer Relationship Management) | `customer_id`, `last_purchase_date`, `lifetime_value` | CSV, JSON, Parquet | Données client‑centrées, souvent déséquilibrées (clients actifs vs inactifs). |
| Logs web (serveur, clickstream) | `session_id`, `url`, `timestamp`, `user_agent` | JSONL, Parquet, Avro | Volume très élevé, timestamps à la milliseconde, besoin de normaliser les fuseaux horaires. |
| Données publicitaires (DSP, SSP) | `ad_id`, `impression`, `click`, `cost` | CSV, Parquet | Granularité horaire ou 15 min, métriques agrégées (cpc, ctr). |
| Données tierces (social, météo) | `region`, `temperature`, `event_type` | CSV, JSON | Peuvent enrichir le modèle, mais nécessitent un mapping géographique fiable. |

**Vérification** : chaque format possède une spécification officielle (ex. [Apache Parquet Specification](https://github.com/apache/parquet-format)).  

### 1.2 Nettoyage et enrichissement des données  

| Étape | Technique | Implémentation scikit‑learn / pandas | Piège fréquent |
|------|-----------|--------------------------------------|----------------|
| Imputation des valeurs manquantes | `SimpleImputer` (mean, median, most_frequent) | `SimpleImputer(strategy='median')` | Imputer les variables catégorielles avec la moyenne provoque une perte d’information ; préférer `most_frequent` ou un code spécial (`'unknown'`). |
| Normalisation / standardisation | `StandardScaler`, `MinMaxScaler` | `StandardScaler().fit_transform(X_num)` | Appliquer le scaler **après** le split train/validation ; sinon fuite de données. |
| Encodage catégoriel | `OneHotEncoder` (sparse=False), `OrdinalEncoder` | `OneHotEncoder(handle_unknown='ignore')` | `handle_unknown='ignore'` évite les erreurs sur des catégories inédites dans le set de test. |
| Gestion des outliers | `IsolationForest`, `clip` | `X_num = np.clip(X_num, lower, upper)` | Suppression brutale d’observations peut biaiser la distribution si les outliers sont réellement informatifs (ex. achats très élevés). |
| Enrichissement externe | Jointure sur clé géographique ou temporelle | `pd.merge(df, weather_df, on=['date','region'], how='left')` | Vérifier la granularité (jour vs heure) avant la jointure, sinon duplication de lignes. |

#### Exemple de pipeline complet

```python
# -*- coding: utf-8 -*-
"""
Pipeline de pré‑traitement pour un jeu de données marketing.
- Imputation des numériques (médiane)
- Imputation des catégoriques (mode)
- Standardisation des numériques
- One‑Hot encoding des catégoriques
- Retour d'un DataFrame pandas (nom des colonnes conservé)
"""

import pandas as pd
import numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder

# ------------------------------------------------------------------
# 1. Chargement (exemple minimal)
# ------------------------------------------------------------------
df = pd.read_csv('marketing_raw.csv')   # CSV contenant des colonnes mixtes

# 2. Sélection des colonnes
num_cols = df.select_dtypes(include=['int64', 'float64']).columns.tolist()
cat_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()

# 3. Définition des transformateurs
numeric_transformer = Pipeline(steps=[
    ('imputer', SimpleImputer(strategy='median')),
    ('scaler',  StandardScaler())
])

categorical_transformer = Pipeline(steps=[
    ('imputer', SimpleImputer(strategy='most_frequent')),
    ('onehot',  OneHotEncoder(handle_unknown='ignore', sparse=False))
])

# 4. Assemblage
preprocess = ColumnTransformer(
    transformers=[
        ('num', numeric_transformer, num_cols),
        ('cat', categorical_transformer, cat_cols)
    ])

# 5. Exécution du pipeline
X_processed = preprocess.fit_transform(df)

# 6. Reconstruction du DataFrame avec noms de colonnes
#   - OneHotEncoder expose les noms via .get_feature_names_out()
num_features = num_cols
cat_features = preprocess.named_transformers_['cat']\
                     .named_steps['onehot']\
                     .get_feature_names_out(cat_cols).tolist()
feature_names = num_features + cat_features

X_processed_df = pd.DataFrame(X_processed, columns=feature_names)

# 7. Sauvegarde du pipeline pour réutilisation en production
import joblib
joblib.dump(preprocess, 'pipeline_preprocess.pkl')
X_processed_df.to_parquet('marketing_preprocessed.parquet')
```

**Points de vérification**  
- `fit_transform` est appelé **uniquement** sur le jeu d’entraînement ; pour le jeu de validation/test on utilise `preprocess.transform`.  
- Le fichier `pipeline_preprocess.pkl` doit être chargé dans le service de scoring pour garantir la même transformation.

### 1.3 Partitionnement des jeux de données  

#### 1.3.1 Règle de base  
- **Train** : la majorité des observations est réservée à l’entraînement.  
- **Validation** : une portion plus petite est utilisée pour le réglage d’hyper‑paramètres.  
- **Test** : une portion finale, jamais vue pendant l’entraînement, sert à l’évaluation finale.

#### 1.3.2 Validation croisée temporelle  

Dans le marketing digital les observations sont autocorrélées dans le temps. La stratégie `KFold` aléatoire viole l’indépendance temporelle et conduit à une **fuite de données**.
---

## Module 2 — contenu

## 2.1 Pré‑traitement requis pour la régression du CPC  
- **Cible** : `cpc` (coût par clic) – variable continue, généralement exprimée en € ou $.  
- **Features** : variables numériques (budget, impressions, CTR) et catégorielles (type de campagne, device).  
- **Encodage** : `OneHotEncoder(handle_unknown='ignore')` pour les variables nominales, `StandardScaler` pour les numériques.  
- **Pipeline** (exemple minimal) :

```python
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.pipeline import Pipeline

numeric_features = ['budget', 'impressions', 'ctr']
categorical_features = ['campaign_type', 'device']

preprocess = ColumnTransformer(
    transformers=[
        ('num', StandardScaler(), numeric_features),
        ('cat', OneHotEncoder(handle_unknown='ignore'), categorical_features)
    ])
```

> **Vérifiable** : `StandardScaler` centre et réduit chaque colonne numérique (moyenne ≈ 0, variance ≈ 1). `OneHotEncoder` crée `n_categories` colonnes binaires.

---

## 2.2 Modèles linéaires de base  

| Modèle | Formulation | Hyper‑paramètre clé |
|--------|-------------|---------------------|
| Régression linéaire | 𝑦̂ = 𝛽₀ + Σ𝛽ᵢxᵢ | Aucun (sauf `fit_intercept`) |
| Ridge (L2) | minimise ‖y‑Xβ‖² + α‖β‖² | `alpha` (force de régularisation) |
| Lasso (L1) | minimise ‖y‑Xβ‖² + α‖β‖₁ | `alpha` (sparsité) |

```python
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.model_selection import train_test_split

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

lin = LinearRegression()
ridge = Ridge(alpha=1.0)
lasso = Lasso(alpha=0.001, max_iter=10_000)

for model in (lin, ridge, lasso):
    model.fit(X_train, y_train)
    print(model.__class__.__name__, model.score(X_test, y_test))   # R²
```

- **Interprétation** : `LinearRegression().score` renvoie le coefficient de détermination R².  
- **Seuil cible** : R² ≥ 0.85 sur le jeu de test.

---

## 2.3 Sélection de variables  

### 2.3.1 Lasso comme sélection intégrée  
Le L1 pousse les coefficients inutiles à zéro. Après entraînement :

```python
selected_features = X.columns[lasso.coef_ != 0]
print("Variables retenues :", selected_features.tolist())
```

### 2.3.2 RFE (Recursive Feature Elimination) avec un estimateur linéaire  

```python
from sklearn.feature_selection import RFE
rfe = RFE(estimator=LinearRegression(), n_features_to_select=10, step=1)
rfe.fit(X_train, y_train)
print("RFE sélection :", X.columns[rfe.support_].tolist())
```

- **Piège** : RFE ne tient pas compte de la corrélation entre variables; deux variables fortement corrélées peuvent être conservées simultanément, gonflant le risque d’over‑fit.

---

## 2.4 Modèles d’ensemble  

### 2.4.1 Random Forest Regressor  

```python
from sklearn.ensemble import RandomForestRegressor

rf = RandomForestRegressor(
    n_estimators=300,
    max_depth=12,
    min_samples_leaf=5,
    random_state=42,
    n_jobs=-1)
rf.fit(X_train, y_train)
print("RF R² :", rf.score(X_test, y_test))
```

### 2.4.2 Gradient Boosting (sklearn)  

```python
from sklearn.ensemble import GradientBoostingRegressor

gbr = GradientBoostingRegressor(
    n_estimators=500,
    learning_rate=0.05,
    max_depth=6,
    subsample=0.8,
    random_state=42)
gbr.fit(X_train, y_train)
print("GBR R² :", gbr.score(X_test, y_test))
```

### 2.4.3 XGBoost  

```python
import xgboost as xgb

xgb_reg = xgb.XGBRegressor(
    n_estimators=800,
    max_depth=8,
    learning_rate=0.03,
    subsample=0.9,
    colsample_bytree=0.8,
    reg_lambda=1.0,
    objective='reg:squarederror',
    n_jobs=-1,
    random_state=42)

xgb_reg.fit(X


---

## Module 3 — contenu

## 3.1. Principes du clustering appliqué au marketing digital  

| Concept | Définition vérifiable | Usage typique en marketing |
|---------|----------------------|---------------------------|
| **Clustering** | Algorithme non supervisé qui regroupe des observations selon une fonction de similarité (ex. distance euclidienne). | Découverte de segments d’utilisateurs, de produits, de comportements de navigation. |
| **Indice de silhouette** | \(s(i)=\frac{b(i)-a(i)}{\max\{a(i),b(i)\}}\) où *a(i)* est la distance moyenne intra‑cluster et *b(i)* la distance moyenne à l’autre cluster le plus proche. Valeur dans \([-1,1]\). | Mesure de la cohérence d’un clustering ; un seuil pratique indique des clusters bien séparés. |
| **Réduction de dimension** | Transformation linéaire (PCA) ou non linéaire (t‑SNE) qui projette les variables d’origine dans un espace de dimension *d* < *d_original*. | Facilite la visualisation et réduit le bruit pour les algorithmes sensibles à la malédiction de la dimension. |
| **Standardisation** | Transformation \(x' = (x-\mu)/\sigma\) (moyenne 0, écart‑type 1). | Nécessaire pour les algorithmes basés sur distances (K‑means, DBSCAN). |

### 3.1.1. Choix de l’algorithme  

| Algorithme | Hypothèses | Complexité (n = nb d’observations, p = nb variables) | Points forts / limites |
|-----------|------------|---------------------------------------------------|------------------------|
| **K‑means** | Clusters sphériques, même variance, variables numériques, distance euclidienne. | \(O(k·n·p·i)\) (i = nb d’itérations). | Rapide, mais sensible aux outliers et à la forme des clusters. |
| **DBSCAN** | Densité locale, forme arbitraire, gère les outliers. | \(O(n·\log n)\) (avec arbre KD). | Pas besoin de spécifier *k*, mais requiert *eps* et *min_samples* ; difficile à calibrer en haute dimension. |
| **Agglomerative (Ward)** | Fusion hiérarchique, distance Ward minimise la variance intra‑cluster. | \(O(n^2·p)\). | Produit un dendrogramme exploitable, mais coûteux en mémoire pour de très grands jeux de données. |

## 3.2. Pipeline complet de clustering  

```python
# -*- coding: utf-8 -*-
"""
Exemple complet : segmentation d’utilisateurs à partir d’un jeu de données marketing.
1. Chargement et nettoyage
2. Standardisation + réduction de dimension (PCA)
3. Recherche du nombre optimal de clusters (silhouette)
4. Entraînement du modèle K‑means
5. Enregistrement du pipeline (pickle) et visualisation
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
import matplotlib.pyplot as plt
import pickle

# ----------------------------------------------------------------------
# 1. Chargement et nettoyage (exemple synthétique)
# ----------------------------------------------------------------------
df = pd.read_csv("marketing_users.csv")  # colonnes : user_id, age, gender, country, sessions, spend, device
df = df.drop(columns=["user_id"])       # id non informatif pour le clustering

# Gestion des valeurs manquantes : imputation simple
df["age"] = df["age"].fillna(df["age"].median())
df["spend"] = df["spend"].fillna(0)

# ----------------------------------------------------------------------
# 2. Pré‑traitement : colonnes numériques vs catégorielles
# ----------------------------------------------------------------------
num_features = ["age", "sessions", "spend"]
cat_features = ["gender", "country", "device"]

numeric_transformer = Pipeline(
    steps=[("scaler", StandardScaler())]  # standardisation obligatoire pour K‑means
)

categorical_transformer = Pipeline(
    steps=[("onehot", OneHotEncoder(handle_unknown="ignore"))]
)

preprocess = ColumnTransformer(
    transformers=[
        ("num", numeric_transformer, num_features),
        ("cat", categorical_transformer, cat_features),
    ]
)

# ----------------------------------------------------------------------
# 3. Pipeline complet (pré‑traitement → PCA → K‑means)
# ----------------------------------------------------------------------
pipeline = Pipeline(
    steps=[
        ("preprocess", preprocess),
        ("pca", PCA(n_components=0.95, random_state=42)),  # conserve la plupart de la variance
        ("kmeans", KMeans(init="k-means++", n_init=10, random_state=42)),
    ]
)

# ----------------------------------------------------------------------
# 4. Recherche du k optimal via silhouette
# ----------------------------------------------------------------------
X = df.values  # on passe le DataFrame complet au pipeline (les colonnes inutiles sont déjà exclues)
silhouette_scores = []

for k in range(2, 11):
    pipeline.set_params(kmeans__n_clusters=k)
    pipeline.fit(df)                         # le pipeline entraîne pré‑traitement + PCA + K‑means
    labels = pipeline.named_steps["kmeans"].labels_
    score = silhouette_score(pipeline.named_steps["pca"].transform(
        pipeline.named_steps["preprocess"].transform(df)), labels)
    silhouette_scores.append(score)

# Visualisation du score silhouette
plt.figure(figsize=(6, 4))
plt.plot(range(2, 11), silhouette_scores, marker="o")
plt.title("Silhouette en fonction du nombre de clusters")
plt.xlabel("k")
plt
```
---

## Module 4 — contenu

## Module 4 – Optimisation en temps réel des campagnes publicitaires  

### 4.1 Formulation du problème comme un bandit multi‑bras  

| Concept | Formule | Commentaire |
|---|---|---|
| **Action** (bras) | \(a_t \in \mathcal{A} = \{1,\dots,K\}\) | Chaque bras représente une stratégie d’enchère (ex. CPC fixe, CPC incrémental, enchère par objectif). |
| **Récompense** | \(r_t = \text{ROAS}_t = \frac{\text{Revenue}_t}{\text{Spend}_t}\) | La récompense observée à chaque intervalle de 15 min. |
| **Objectif** | \(\max_{\pi}\; \mathbb{E}\big[\sum_{t=1}^{T} r_t\big]\) | Maximiser le ROAS cumulé sous contrainte de budget quotidien. |
| **UCB1** | \(a_t = \arg\max_{i}\Big(\hat{\mu}_i + \sqrt{\frac{2\ln t}{n_i}}\Big)\) | \(\hat{\mu}_i\) moyenne empirique du bras *i*, \(n_i\) nombre de tirages du bras. |
| **Thompson Sampling (TS)** | Tirer \(\theta_i \sim \text{Beta}(\alpha_i,\beta_i)\) puis choisir \(a_t = \arg\max_i \theta_i\) | Pour des récompenses binaires (ex. “ROAS > cible”). Pour des récompenses continues on utilise une distribution normale conjugée (Normal‑Gamma). |

#### 4.1.1 Implémentation d’UCB1 (CPC fixe vs incrémental)  

```python
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

class RealTimeBidderUCB:
    """UCB1 pour choisir entre K stratégies d'enchère toutes les 15 min."""
    def __init__(self, n_arms: int, init_reward: float = 0.0):
        self.n_arms = n_arms
        self.counts = np.zeros(n_arms, dtype=int)          # n_i
        self.values = np.full(n_arms, init_reward, dtype=float)  # \hat{\mu}_i
        self.t = 0                                          # horizon

    def select_arm(self) -> int:
        """Retourne l'indice du bras à jouer."""
        self.t += 1
        if 0 in self.counts:               # forcer chaque bras à être tiré une fois
            return int(np.where(self.counts == 0)[0][0])
        ucb = self.values + np.sqrt(2 * np.log(self.t) / self.counts)
        return int(np.argmax(ucb))

    def update(self, chosen_arm: int, reward: float) -> None:
        """Mise à jour incrémentale de la moyenne empirique."""
        self.counts[chosen_arm] += 1
        n = self.counts[chosen_arm]
        # moyenne pondérée : μ←μ+(r-μ)/n
        self.values[chosen_arm] += (reward - self.values[chosen_arm]) / n

# Exemple d’utilisation (simulation simplifiée)
if __name__ == "__main__":
    np.random.seed(42)
    true_means = [0.12, 0.15, 0.09]          # ROAS moyen attendu par stratégie
    bidder = RealTimeBidderUCB(n_arms=3)

    logs = []  # stocker les décisions pour audit
    for _ in range(96):                     # 24 h × 4 intervalles de 15 min
        arm = bidder.select_arm()
        # simulation d'une récompense gaussienne (σ=0.02)
        reward = np.random.normal(loc=true_means[arm], scale=0.02)
        bidder.update(arm, reward)
        logs.append(dict(timestamp=datetime.utcnow(),
                         arm=arm,
                         reward=reward,
                         cum_reward=sum(l["reward"] for l in logs)))
    df = pd.DataFrame(logs)
    print(df.tail())
```

*Points de vérification*  
- `select_arm` garantit que chaque bras est testé au moins une fois (condition de départ de UCB).  
- La mise à jour de la moyenne utilise la formule incrémentale sans recomputation coûteuse.  
- L’algorithme ne dépend pas du nombre total d’observations, il fonctionne en streaming.

### 4.2 Simulation d’environnements publicitaires avec `gym‑advertising`  

`gym‑advertising` (v0.2.0) expose un environnement OpenAI Gym compatible avec les API standards.  

```python
import gym
import gym_advertising   # enregistre automatiquement l'environnement "AdvertisingEnv-v0"
import numpy as np

env = gym.make("AdvertisingEnv-v0",
               budget_per_interval=500,      # € dépensés max toutes les 15 min
               cpc_options=[0.10, 0.15, 0.20],  # trois stratégies d'enchère
               revenue_noise=0.05)           # bruit gaussien sur le revenu

obs = env.reset()
total_reward = 0.0
for t in range(96):  # 24 h × 4 intervalles
    # policy = UCB1 (voir classe ci‑dessus)
    arm = bidder.select_arm()
    # l'action attend un tableau de forme (1,) contenant le CPC choisi
    action = np.array([env.cpc_options[arm]])
    obs, reward, done, info = env.step(action)
    # reward = ROAS = revenue / spend (déjà normalisé par l'env)
    bidder.update(arm, reward)
    total_reward += reward
    if done:
        break
print(f"ROAS cumulé sur 24 h : {


---

## Module 5 — contenu

## 5.1. Cadre légal et exigences de conformité RGPD  

| Exigence RGPD | Implication IA | Implémentation concrète |
|---------------|----------------|------------------------|
| **Droit à l’explication** (article 15‑2‑d) | Chaque décision automatisée doit être compréhensible par la personne concernée. | Produire un rapport contenant les features les plus influentes (ex. top‑5) pour chaque prédiction. |
| **Documentation du traitement** (article 30) | Le registre des traitements doit mentionner le modèle, les données d’entraînement, les métriques, les méthodes d’explicabilité. | Générer un fichier JSON « model‑audit.json » lors du déploiement. |
| **Minimisation & exactitude** (article 5‑1‑c) | Les variables sensibles (ex. genre, origine) ne doivent pas être utilisées à moins d’une justification légale. | Implémenter un filtre de colonnes « sensitive_columns » et vérifier l’absence de corrélation > 0,3 avec la cible. |
| **Évaluation d’impact sur la protection des données (DPIA)** | L’utilisation de modèles complexes (XGBoost, réseaux) nécessite une DPIA si le risque d’impact est élevé. | Automatiser la génération d’un tableau de risques (probabilité × gravité) à partir des scores de biais. |

---

## 5.2. Calcul des valeurs d’explicabilité  

### 5.2.1. SHAP (SHapley Additive exPlanations)

* Théorie vérifiable : les valeurs de Shapley proviennent de la théorie des jeux coopératifs (Lloyd Shapley, 1953).  
* Implémentation : `shap.TreeExplainer` pour les modèles d’arbre, `shap.KernelExplainer` pour les modèles « black‑box ».  

```python
# -*- coding: utf-8 -*-
"""
Exemple complet : entraînement d'un GradientBoostingRegressor,
calcul des valeurs SHAP et export d'un tableau CSV d'explications
pour chaque observation du jeu de test.
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import GradientBoostingRegressor
import shap
import json
import os

# 1️⃣ Chargement des données (exemple synthétique)
df = pd.read_csv("data/ads_features.csv")               # colonnes : ['click', 'impr', 'budget', 'device', 'hour', 'cpc']
X = df.drop(columns="cpc")
y = df["cpc"]

# 2️⃣ Séparation train / test
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# 3️⃣ Entraînement du modèle
model = GradientBoostingRegressor(
    n_estimators=200,
    learning_rate=0.05,
    max_depth=4,
    random_state=0,
)
model.fit(X_train, y_train)

# 4️⃣ Calcul des valeurs SHAP (TreeExplainer = optimal pour les arbres)
explainer = shap.TreeExplainer(model)
shap_values = explainer.shap_values(X_test)          # shape = (n_samples, n_features)

# 5️⃣ Construction du tableau d’explications (top‑3 features par ligne)
feature_names = X_test.columns.tolist()
top_k = 3
explanations = []

for i, row in enumerate(shap_values):
    # tri décroissant de l'importance absolue
    idx = np.argsort(-np.abs(row))[:top_k]
    explanations.append({
        "row_id": int(i),
        "prediction": float(model.predict(X_test.iloc[[i]])[0]),
        "features": [
            {
                "name": feature_names[j],
                "shap_value": float(row[j]),
                "value": X_test.iloc[i, j]
            }
            for j in idx
        ]
    })

# 6️⃣ Sauvegarde au format JSON (compatible avec le rapport PDF)
out_path = "output/shap_explanations.json"
os.makedirs(os.path.dirname(out_path), exist_ok=True)
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(explanations, f, ensure_ascii=False, indent=2)

print(f"✅ SHAP explanations saved to {out_path}")
```

* **Points de contrôle**  
  - `explainer.expected_value` correspond à la moyenne de la cible sur le train.  
  - Pour les modèles linéaires, `shap.LinearExplainer` est plus rapide.  
  - `shap_values` occupe `n_samples × n_features × 8 bytes`. Sur de gros jeux, écrivez batch‑wise.

### 5.2.2. LIME (Local Interpretable Model‑agnostic Explanations)

* Théorie vérifiable : LIME approxime la frontière locale par une régression linéaire pondérée (Ribeiro et al., 2016).  
* Usage recommandé : modèles non‑arbres (SVM, réseaux de neurones) ou quand on veut un aperçu *expliqué* par des features binaires.

```python
import lime
import lime.lime_tabular
import joblib

# 1️⃣ Chargement du même modèle que précédemment (déjà entraîné)
model = joblib.load("models/gbc.pkl")

# 2️⃣ Instanciation du LIME explainer
explainer = lime.lime_tabular.LimeTabularExplainer(
    training_data=X_train.values,
    feature_names=X_train.columns,
    class_names=["cpc"],
    mode="regression",
    discretize_continuous=True
)

# 3️⃣ Fonction d’exp