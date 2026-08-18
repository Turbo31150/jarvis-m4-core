# IA pour la Finance — Analyse

> Référence `ia-finance` · 89 €

## Plan

## Module 1 – Prétraitement et enrichissement des données financières  
**Objectif mesurable** : Être capable de construire un pipeline automatisé qui récupère, nettoie et enrichit des jeux de données boursières ou macroéconomiques avec un taux d’erreur de transformation ≤ 1 %.  
**Notions couvertes**  
1. Extraction via API (Alpha Vantage, Bloomberg, Refinitiv) et gestion des quotas.  
2. Normalisation des fréquences (alignement quotidien, mensuel, trimestriel) et interpolation des valeurs manquantes (méthodes linéaire, spline, Kalman).  
3. Gestion des outliers : détection (IQR, Z‑score) et traitement (winsorisation, remplacement par valeurs prédites).  
4. Enrichissement avec facteurs exogènes (sentiment Twitter, indicateurs ESG) et jointure de tables (hash‑join, merge asof).  
5. Versionnage des jeux de données avec DVC ou Git‑LFS et traçabilité des transformations (MLflow tracking).

---

## Module 2 – Modélisation de séries temporelles financières  
**Objectif mesurable** : Implémenter et comparer au moins trois modèles de prévision (ARIMA, LSTM, Prophet) sur un jeu de prix d’actifs, en obtenant un RMSE inférieur à 5 % du rendement moyen sur une période de validation de 6 mois.  
**Notions couvertes**  
1. Stationnarité, différenciation et tests d’ADF/PP.  
2. Modèles linéaires classiques : AR, MA, ARMA, ARIMA, SARIMA (sélection de p, d, q via AIC/BIC).  
3. Réseaux récurrents (LSTM, GRU) : architecture, séquence de fenêtres, normalisation temporelle.  
4. Modèles de décomposition additive/multiplicative et Prophet (changepoints, holidays).  
5. Évaluation robuste : backtesting rolling‑window, métriques MASE, sMAPE, VaR‑scaled error.

---

## Module 3 – Apprentissage supervisé pour la prédiction de risques de crédit  
**Objectif mesurable** : Développer un classificateur (XGBoost ou LightGBM) capable de détecter les défauts de paiement avec un AUC‑ROC ≥ 0.78 sur un jeu de test indépendant.  
**Notions couvertes**  
1. Construction de variables d’entrée (ratio d’endettement, historique de paiement, score de crédit).  
2. Encodage des variables catégorielles (target encoding, catboost encoding) et gestion des déséquilibres (SMOTE, class weighting).  
3. Hyper‑parameter tuning (grid search, Bayesian optimisation avec Optuna) et validation croisée stratifiée.  
4. Interprétabilité : SHAP values, feature importance globales et locales.  
5. Calibration du score de probabilité (Platt scaling, isotonic regression) et seuil de décision basé sur coût de défaut.

---

## Module 4 – Traitement du langage naturel appliqué aux rapports financiers  
**Objectif mesurable** : Extraire automatiquement les indicateurs clés (EB

---

## Module 1 — contenu

## 1. Extraction via API  

### 1.1 Principes généraux  
| Élément | Description | Vérifiable |
|--------|-------------|------------|
| Authentification | La plupart des fournisseurs (Alpha Vantage, Bloomberg, Refinitiv) utilisent une clé API transmise dans le header `Authorization` ou comme paramètre `apikey`. | Documentation officielle de chaque API |
| Quota | Alpha Vantage : 5 requêtes/minute, 500 requêtes/jour (free tier). Bloomberg : 10 000 messages/heure (via B-PIPE). Refinitiv : 200 requêtes/secondes (Enterprise). | Conditions d’utilisation publiées |
| Pagination | Certaines endpoints retournent un `next_token` ou un `offset`. Il faut itérer jusqu’à ce que le token soit nul. | Exemple de réponse JSON de Refinitiv Data Platform |

### 1.2 Exemple fonctionnel – Alpha Vantage (données journalières)  

```python
import os
import time
import requests
import pandas as pd
from pathlib import Path

API_KEY = os.getenv("ALPHAVANTAGE_KEY")          # à définir dans l'environnement
BASE_URL = "https://www.alphavantage.co/query"
SYMBOL = "AAPL"
OUTPUT_DIR = Path("data/raw")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def fetch_daily(symbol: str, api_key: str, retries: int = 3) -> pd.DataFrame:
    """
    Récupère les prix journaliers (open, high, low, close, volume) pour `symbol`.
    Retourne un DataFrame indexé par date (timezone UTC).
    """
    params = {
        "function": "TIME_SERIES_DAILY_ADJUSTED",
        "symbol": symbol,
        "outputsize": "full",          # 'compact' = 100 derniers points
        "apikey": api_key,
        "datatype": "json"
    }

    for attempt in range(retries):
        r = requests.get(BASE_URL, params=params, timeout=10)
        if r.status_code == 200:
            break
        time.sleep(2 ** attempt)      # back‑off exponentiel
    else:
        raise RuntimeError(f"Échec de la requête après {retries} tentatives")

    data = r.json()
    if "Error Message" in data:
        raise ValueError(f"Erreur API : {data['Error Message']}")
    if "Note" in data:               # quota dépassé
        raise RuntimeError(f"Quota dépassé : {data['Note']}")

    # Extraction du dictionnaire de séries temporelles
    ts = data["Time Series (Daily)"]
    df = pd.DataFrame.from_dict(ts, orient="index", dtype=float)
    df.index = pd.to_datetime(df.index)                     # conversion en datetime
    df = df.sort_index()                                    # ascendant
    df.columns = [c.split(". ")[1] for c in df.columns]    # '1. open' → 'open'
    df = df.rename_axis("date")
    return df

# Exécution
df_aapl = fetch_daily(SYMBOL, API_KEY)
df_aapl.to_parquet(OUTPUT_DIR / f"{SYMBOL}_daily.parquet")
print(df_aapl.head())
```

*Points de contrôle*  
- La clé est lue depuis l’environnement, évitant le versionnage en clair.  
- Le back‑off gère les réponses temporaires (`503`, `429`).  
- Le `Note` d’Alpha Vantage indique le dépassement de quota ; on le transforme en exception.  

---

## 2. Normalisation des fréquences  

### 2.1 Alignement de séries de fréquences différentes  
- **Fréquence cible** : choisir `D` (daily), `M` (month‑end) ou `Q` (quarter‑end).  
- **Méthode** : `pandas.DataFrame.resample`.  
- **Interpolation** : `method='linear'`, `method='spline'` (order=3) ou filtre de Kalman (`pykalman`).  

### 2.2 Exemple – Alignement quotidien → mensuel, interpolation des jours manquants  

```python
import numpy as np
from pykalman import KalmanFilter

def align_and_interpolate(df: pd.DataFrame, freq: str = "M") -> pd.DataFrame:
    """
    1. Re‑indexe le DataFrame à la fréquence `freq` (ex: 'M' = month‑end).
    2. Interpole les valeurs manquantes avec un filtre de Kalman (plus robuste que linéaire).
    Retourne le DataFrame interpolé.
    """
    # 1. Re‑indexation
    df_resampled = df.resample(freq).last()               # on garde le dernier jour du mois
    # 2. Construction du masque de valeurs manquantes
    mask = df_resampled.isna()

    # 3. Kalman interpolation (unidimensionnel pour chaque colonne)
    interpolated = pd.DataFrame(index=df_resampled.index)
    for col in df_resampled.columns:
        series = df_resampled[col].values
        # Initialise le filtre avec variance d'observation = variance empirique
        kf = KalmanFilter(
            transition_matrices=[1],
            observation_matrices=[1],
            initial_state_mean=series[~np.isnan(series)][0],
            observation_covariance=np.nanvar(series),
            transition_covariance=0.01
        )
        # Remplit les NaN avec la prédiction du filtre
        state_means, _ = kf.smooth(series)
        interpolated[col] = state_means.ravel()
    return interpolated

df_monthly = align_and

---

## Module 2 — contenu

## 2.1 Stationnarité et tests de racine unitaire  

| Concept | Formule / Algorithme | Implémentation Python |
|--------|----------------------|-----------------------|
| **Stationnarité** (moyenne & variance constantes, autocorrélation qui dépend seulement du lag) | \(X_t = \mu + \epsilon_t\) avec \(\epsilon_t \sim \mathcal{N}(0,\sigma^2)\) | `statsmodels.tsa.stattools.adfuller` |
| **ADF (Augmented Dickey‑Fuller)** | \( \Delta X_t = \alpha + \beta t + \gamma X_{t-1} + \sum_{i=1}^{p}\delta_i \Delta X_{t-i} + \varepsilon_t\) <br>H0 : \(\gamma = 0\) (non‑stationnaire) | `adfuller(series, autolag='AIC')` |
| **PP (Phillips‑Perron)** | Variante non‑paramétrique du test de Dickey‑Fuller, corrige l’autocorrélation via un estimateur de Newey‑West | `statsmodels.tsa.stattools.ppoll(series)` |

**Procédure recommandée**  

1. Tracer la série, la fonction d’autocorrélation (ACF) et de corrélation partielle (PACF).  
2. Appliquer ADF / PP. Si p‑value > 0.05 → non‑stationnaire.  
3. Différencier une fois (`ΔX_t = X_t - X_{t-1}`) et retester.  
4. Répéter jusqu’à obtenir p‑value ≤ 0.05, mais ne pas différencier plus que nécessaire (évite le sur‑différenciage qui introduit du bruit).  

```python
import pandas as pd
import matplotlib.pyplot as plt
from statsmodels.tsa.stattools import adfuller, pacf, acf

def test_stationarity(series, name='Series'):
    """Affiche le graphe, ACF/PACF et renvoie le p‑value du test ADF."""
    fig, ax = plt.subplots(3, 1, figsize=(10, 8))
    series.plot(ax=ax[0], title=f'{name} - évolution')
    acf_vals = acf(series.dropna(), nlags=30)
    pacf_vals = pacf(series.dropna(), nlags=30)
    ax[1].stem(acf_vals, use_line_collection=True)
    ax[1].set_title('ACF')
    ax[2].stem(pacf_vals, use_line_collection=True)
    ax[2].set_title('PACF')
    plt.tight_layout()
    plt.show()
    
    result = adfuller(series.dropna())
    print(f'ADF p‑value : {result[1]:.4f}')
    return result[1]

# Exemple d’usage
prices = pd.read_csv('SP500.csv', parse_dates=['Date'], index_col='Date')['Close']
pval = test_stationarity(prices, 'SP500 Close')
if pval > 0.05:
    returns = prices.pct_change().dropna()
    test_stationarity(returns, 'SP500 Returns')
```

---

## 2.2 Modèles linéaires classiques  

### 2.2.1 Sélection des ordres (p, d, q)  

* **AIC / BIC** : `statsmodels.tsa.statespace.sarimax.SARIMAX` possède un attribut `aic`.  
* **Approche automatisée** : `pmdarima.auto_arima` explore les combinaisons (p ≤ 5, d ≤ 2, q ≤ 5) et retourne le modèle avec le plus petit AIC/BIC.

```python
import pmdarima as pm

# Série déjà rendue stationnaire (ex : rendements log)
log_ret = np.log(prices).diff().dropna()

model_auto = pm.auto_arima(log_ret,
                           start_p=0, max_p=5,
                           start_q=0, max_q=5,
                           d=None,          # laisse le modèle le détecter
                           seasonal=False,
                           stepwise=True,
                           information_criterion='aic',
                           trace=True)

print(f'Méilleur (p,d,q) : {model_auto.order}')
```

### 2.2.2 Implémentation SARIMA (saisonnier)  

```python
from statsmodels.tsa.statespace.sarimax import SARIMAX

# Exemple : prévision mensuelle de l’indice S&P 500 (saisonnalité annuelle)
sarima = SARIMAX(log_ret,
                 order=(1,1,1),
                 seasonal_order=(1,0,1,12),
                 enforce_stationarity=False,
                 enforce_invertibility=False)
sarima_fit = sarima.fit(disp=False)
print(sarima_fit.summary())
```

### 2.2.3 Métriques de performance  

| Métrique | Formule | Interprétation |
|----------|---------|----------------|
| **RMSE** | \(\sqrt{\frac{1}{N}\sum_{t=1}^{N

---

## Module 3 — contenu

## Module 3 – Apprentissage supervisé pour la prédiction de risques de crédit  

### 3.1 Construction des variables d’entrée  

| Variable | Source typique | Transformation recommandée | Exemple de calcul |
|----------|----------------|-----------------------------|-------------------|
| **Ratio d’endettement** | `total_debt` / `total_assets` | Normalisation log + capping à 99ᵉ percentile | `np.log1p(df['total_debt'] / df['total_assets']).clip(upper=np.log1p(df['total_debt'].quantile(0.99)))` |
| **Historique de paiement** | Nombre de retards sur 12 mois | Binning (0, 1‑2, 3‑5, >5) → catégorie | `pd.cut(df['late_payments_12m'], bins=[-1,0,2,5,np.inf], labels=['0','1‑2','3‑5','>5'])` |
| **Score de crédit interne** | Modèle propriétaire ou externalité | StandardScaler (µ=0, σ=1) | `StandardScaler().fit_transform(df[['internal_score']])` |
| **Durée d’ancienneté** | `account_age_days` | Transformation sqrt pour réduire l’asymétrie | `np.sqrt(df['account_age_days'])` |
| **Variables macro‑économiques** | Taux de chômage, PIB trimestriel | Alignement temporel via `merge_asof` (voir §3.4) | – |

> **Bon à savoir** : Conserver la granularité temporelle (ex. mois) dans les variables macro‑économiques évite le « leakage » de futur dans le jeu d’entraînement.

---

### 3.2 Encodage des variables catégorielles  

| Technique | Quand l’utiliser | Implémentation (sklearn‑compatible) |
|-----------|------------------|------------------------------------|
| **Target encoding** | Variables à forte cardinalité, corrélation avec la cible | `category_encoders.TargetEncoder(cols=categorical_cols).fit_transform(X, y)` |
| **CatBoost encoding** | Données déséquilibrées, besoin de prise en compte du prior | `category_encoders.CatBoostEncoder(cols=categorical_cols, sigma=1.0).fit_transform(X, y)` |
| **One‑hot** | Cardinalité ≤ 10, modèle linéaire | `OneHotEncoder(handle_unknown='ignore', sparse=False).fit_transform(X[categorical_cols])` |

*Piège* : Le target encoding introduit un **leakage** si le calcul du mean target utilise les mêmes observations que le modèle. Corrigez‑le en **k‑fold target encoding** ou en **LeaveOneOutEncoder** (paramètre `fold=5`).

```python
# Exemple de k‑fold target encoding sécurisé
from category_encoders import TargetEncoder
from sklearn.model_selection import KFold
import numpy as np

def kfold_target_encode(X, y, cat_cols, n_folds=5, random_state=42):
    X_enc = X.copy()
    kf = KFold(n_splits=n_folds, shuffle=True, random_state=random_state)
    for col in cat_cols:
        X_enc[col] = np.nan
        for train_idx, val_idx in kf.split(X):
            enc = TargetEncoder(cols=[col])
            enc.fit(X.iloc[train_idx], y.iloc[train_idx])
            X_enc.iloc[val_idx, X_enc.columns.get_loc(col)] = enc.transform(
                X.iloc[val_idx])[col]
        # Global mean for test set
        global_enc = TargetEncoder(cols=[col]).fit(X, y)
        X_enc[col].fillna(global_enc.transform(X)[col], inplace=True)
    return X_enc
```

---

### 3.3 Gestion du déséquilibre de la cible  

| Méthode | Implémentation | Impact sur le modèle |
|---------|----------------|----------------------|
| **SMOTE** (Synthetic Minority Over‑sampling Technique) | `imblearn.over_sampling.SMOTE(k_neighbors=5, random_state=0)` | Crée des points synthétiques dans l’espace des features, améliore la capacité du modèle à apprendre la classe minoritaire. |
| **Class weighting** (XGBoost/LightGBM) | `scale_pos_weight = (n_negative / n_positive)` | Ajuste la fonction de perte ; aucune modification des données. |
| **Under‑sampling** (RandomUnderSampler) | `imblearn.under_sampling.RandomUnderSampler(random_state=0)` | Réduit le nombre d’exemples majoritaires, peut perdre de l’information. |

> **Recommandation** : Commencer par `scale_pos_weight` (pas de risque de sur‑ajustement), puis tester SMOTE si le gain d’AUC reste insuffisant.

---

### 3.4 Pipeline complet (exemple fonctionnel)  

```python
# -*- coding: utf-8 -*-
"""
Pipeline complet de classification du risque de crédit.
Utilise LightGBM, Optuna pour le tuning, SHAP pour l’interprétabilité.
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, StratifiedKFold
from sklearn.preprocessing import StandardScaler
from category_encoders import CatBoostEncoder
from imblearn.over_sampling import SMOTE
import lightgbm as lgb
import optuna
import shap
import joblib

# ------------------------------------------------------------------
# 1. Chargement et split
# ------------------------------------------------------------------
df = pd.read_csv('credit_data.csv', parse_dates=['application_date'])
y = df['default']                     # 1 = défaut, 0 = bon
X = df.drop(columns=['default'])

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, stratify=y, random_state=42)

# ------------------------------------------------------------------
# 2. Feature engineering

---

## Module 4 — contenu

## 4.1. Cadre général du NLP financier  

| Aspect | Détails techniques | Références vérifiables |
|--------|-------------------|------------------------|
| Sources | PDF (rapports annuels, 10‑K), HTML (press releases), texte brut (transcriptions d’appels) | `pdfplumber`, `BeautifulSoup4`, `requests` |
| Langues | Majoritairement anglais, mais les modèles multilingues (XLM‑R, mBERT) sont capables de traiter le français, l’espagnol, le mandarin, etc. | HuggingFace 🤗 |
| Particularités du vocabulaire | Abréviations (EBIT, EPS), unités (M€, $bn), expressions idiomatiques (“bottom‑line”, “top‑line growth”) | Glossaire interne ou listes de termes (`finance‑lexicon.txt`) |
| Structure | Paragraphes narratifs + tables (balance, compte de résultat) + figures | Extraction tabulaire via `camelot` ou `tabula-py` |
| Objectifs typiques | 1) Extraction de KPI (EBITDA, ROE, cash‑flow) 2) Analyse de sentiment (positif/negatif) 3) Résumé automatisé de sections clés 4) Classification de sections (Management Discussion, Risk Factors) | Études de cas de la Banque de France, McKinsey (2022) |

---

## 4.2. Pipeline d’extraction de KPI depuis un rapport PDF  

### 4.2.1. Étapes de base  

1. **Lecture du PDF** – `pdfplumber` lit page par page, conserve la mise en forme (colonnes, espaces).  
2. **Détection de tables** – `camelot` (mode `stream`) identifie les bordures implicites ; `pdfplumber` peut aussi extraire les lignes de texte et les recomposer.  
3. **Normalisation des nombres** – suppression des séparateurs de milliers, conversion des unités (`M`, `B`, `k`) en valeurs numériques.  
4. **Matching de libellés** – recherche de patterns regex parmi les libellés (ex. `r'\bEBITDA\b'`). Utilisation de *fuzzy matching* (`rapidfuzz`) pour couvrir les variantes (`EBIT‑DA`, `Earnings Before Interest, Taxes, Depreciation & Amortisation`).  
5. **Stockage** – DataFrame pandas, versionné avec DVC (`dvc add kpi_extracted.csv`).  

### 4.2.2. Code fonctionnel (Python 3.10)  

```python
# -*- coding: utf-8 -*-
"""
Extraction automatisée d'indicateurs financiers (KPI) depuis un PDF de rapport annuel.
Version testée avec pdfplumber 0.10.2, camelot‑pandas 0.10.1, pandas 2.2.0.
"""

import re
import json
from pathlib import Path
import pdfplumber
import camelot
import pandas as pd
from rapidfuzz import process, fuzz

# ----------------------------------------------------------------------
# 1. Configuration
# ----------------------------------------------------------------------
PDF_PATH = Path("data/annual_report_2023.pdf")
KPI_LIST = [
    "Revenue", "Net Revenue", "EBIT", "EBITDA", "Operating Income",
    "Net Income", "EPS", "Free Cash Flow", "Total Assets", "Total Liabilities"
]

# Mapping d'abréviations fréquentes → libellé canonique
ALIAS = {
    r"\bEBITDA?\b": "EBITDA",
    r"\bEBIT\b": "EBIT",
    r"\bNet\s*Income\b": "Net Income",
    r"\bEPS\b": "EPS",
    r"\bFree\s*Cash\s*Flow\b": "Free Cash Flow",
    r"\bRevenue\b": "Revenue",
}

# ----------------------------------------------------------------------
# 2. Fonctions utilitaires
# ----------------------------------------------------------------------
def clean_number(txt: str) -> float | None:
    """
    Convertit une chaîne contenant un nombre et une unité (M, B, k) en float.
    Retourne None si la conversion échoue.
    """
    txt = txt.replace(",", "").replace(" ", "")
    match = re.fullmatch(r"([+-]?\d*\.?\d+)([MKk]?)([€$]?)", txt)
    if not match:
        return None
    num, unit, _ = match.groups()
    num = float(num)
    factor = {"M": 1e6, "B": 1e9, "k": 1e3, "": 1}[unit.upper()]
    return num * factor

def normalize_label(label: str) -> str:
    """
    Normalise un libellé de tableau en le rapprochant d'un KPI connu.
    Utilise fuzzy matching avec un seuil de 85 % de similarité.
    """
    label = label.strip()
    # 1) recherche directe via regex alias
    for pattern, canon in ALIAS.items():
        if re.search(pattern, label, flags=re.I):
            return canon
    # 2) fuzzy fallback sur la liste KPI
    best, score, _ = process.extractOne(
        label, KPI_LIST, scorer=fuzz.WRatio, score_cutoff=85
    )
    return best if best else None

# ----------------------------------------------------------------------
# 3. Extraction des tables
# ----------------------------------------------------------------------
def extract_tables(pdf_path: Path) -> list[pd.DataFrame]:
    """
    Utilise camelot en mode stream (détection par espaces)

---

## Module 5 — contenu

## Module 5 – Déploiement, gouvernance et monitoring des modèles IA en finance  

### 5.1 Architecture de mise en production  

| composant | rôle | technologie typique (2024) |
|-----------|------|----------------------------|
| **Feature store** | versionnage, partage et ré‑exécution des transformations de features | Feast, Hopsworks |
| **Orchestrateur** | planification des pipelines ETL/ML | Apache Airflow 2.7, Prefect 2 |
| **Containerisation** | isolation, reproductibilité, scalabilité | Docker 24, OCI‑compatible runtimes |
| **Service d’inférence** | exposition du modèle via API REST/gRPC | FastAPI 0.110, gRPC‑Python 1.60 |
| **Gestion de versions de modèle** | traçabilité, rollback | MLflow 2.12, DVC 3 |
| **Pipeline de données en temps réel** | ingestion, enrichissement, scoring | Kafka 3.5, ksqlDB, Flink 1.18 |
| **Observabilité** | métriques, logs, alertes | Prometheus 2.50, Grafana 10, OpenTelemetry |
| **Sécurité & conformité** | chiffrement, contrôle d’accès, audit | HashiCorp Vault, OPA, GDPR‑ready logs |

> **Principe** : chaque composant doit être **stateless** (sauf le store de features) afin de permettre le scaling horizontal derrière un load‑balancer (NGINX 1.25 ou Traefik 2.10).

---

### 5.2 Containerisation d’un modèle LightGBM avec FastAPI  

#### 5.2.1 Structure du répertoire  

```
project/
├─ src/
│  ├─ model/
│  │   ├─ model.pkl          # LightGBM Booster (binary)
│  │   └─ preprocess.py      # fonctions de pré‑traitement
│  ├─ api/
│  │   └─ main.py            # FastAPI app
│  └─ requirements.txt
├─ Dockerfile
└─ mlflow/
   └─ model/                 # export MLflow (optional)
```

#### 5.2.2 `src/api/main.py` (commenté)

```python
# -*- coding: utf-8 -*-
"""
FastAPI service exposing a LightGBM model.
Assumes:
- model.pkl is a LightGBM Booster saved with joblib.dump().
- preprocess.transform(df) returns a pandas.DataFrame ready for prediction.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, conlist, validator
import pandas as pd
import joblib
import numpy as np
from src.model.preprocess import transform

app = FastAPI(
    title="Scoring de crédit",
    version="1.0.0",
    description="API REST pour le scoring en temps réel d’une demande de crédit."
)

# -------------------------------------------------------------------------
# 1️⃣ Schéma d’entrée – validation stricte (Pydantic)
# -------------------------------------------------------------------------
class CreditRequest(BaseModel):
    # Exemple de 12 variables numériques, contraintes de type
    age: int
    income: float
    loan_amount: float
    loan_term: int
    # variables catégorielles encodées sous forme de texte
    employment_status: str
    purpose: str
    # vecteur de scores externes (ex. sentiment)
    external_scores: conlist(float, min_items=3, max_items=3)

    @validator("*")
    def no_nan(cls, v):
        if isinstance(v, float) and np.isnan(v):
            raise ValueError("Valeur NaN interdite")
        return v

# -------------------------------------------------------------------------
# 2️⃣ Chargement du modèle (singleton)
# -------------------------------------------------------------------------
try:
    model = joblib.load("/app/src/model/model.pkl")
except Exception as exc:
    raise RuntimeError(f"Impossible de charger le modèle : {exc}")

# -------------------------------------------------------------------------
# 3️⃣ Endpoint de scoring
# -------------------------------------------------------------------------
@app.post("/score")
def score(request: CreditRequest):
    # 3.1 → conversion en DataFrame (compatible avec transform())
    payload = pd.DataFrame([request.dict()])
    try:
        X = transform(payload)                # pré‑traitement hors‑ligne
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    # 3.2 → prédiction (probabilité de défaut)
    prob = model.predict_proba(X)[:, 1].item()  # LightGBM renvoie (n_samples, 2)

    # 3.3 → décision métier (seuil 0.35, configurable)
    decision = "refus" if prob >= 0.35 else "acceptation"

    return {"probability_default": prob, "decision": decision}
```

#### 5.2.3 `Dockerfile`

```dockerfile
# syntax = docker/dockerfile:1.4
FROM python:3.11-slim AS base

# 1️⃣ Dépendances système minimales (libgomp requis par LightGBM)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 && rm -rf /var/lib/apt/lists/*

# 2️⃣ Création d’un environnement virtuel (optionnel mais recommandé)
ENV VIRTUAL_ENV=/opt/venv
RUN