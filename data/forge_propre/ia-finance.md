# IA pour la Finance — Analyse

> Référence `ia-finance` · 89 €

## Plan

## Module 1 – Prétraitement et enrichissement des données financières  
**Objectif mesurable** : Être capable de construire un pipeline automatisé qui récupère, nettoie et enrichit des jeux de données boursières ou macroéconomiques avec un taux d’erreur de transformation faible.  
**Notions couvertes**  
1. Extraction via API (Alpha Vantage, Bloomberg, Refinitiv) et gestion des quotas.  
2. Normalisation des fréquences (alignement quotidien, mensuel, trimestriel) et interpolation des valeurs manquantes (méthodes linéaire, spline, Kalman).  
3. Gestion des outliers : détection (IQR, Z‑score) et traitement (winsorisation, remplacement par valeurs prédites).  
4. Enrichissement avec facteurs exogènes (sentiment Twitter, indicateurs ESG) et jointure de tables (hash‑join, merge asof).  
5. Versionnage des jeux de données avec DVC ou Git‑LFS et traçabilité des transformations (MLflow tracking).

---

## Module 2 – Modélisation de séries temporelles financières  
**Objectif mesurable** : Implémenter et comparer au moins trois modèles de prévision (ARIMA, LSTM, Prophet) sur un jeu de prix d’actifs, en obtenant un RMSE inférieur au rendement moyen sur une période de validation de 6 mois.  
**Notions couvertes**  
1. Stationnarité, différenciation et tests d’ADF/PP.  
2. Modèles linéaires classiques : AR, MA, ARMA, ARIMA, SARIMA (sélection de p, d, q via AIC/BIC).  
3. Réseaux récurrents (LSTM, GRU) : architecture, séquence de fenêtres, normalisation temporelle.  
4. Modèles de décomposition additive/multiplicative et Prophet (changepoints, holidays).  
5. Évaluation robuste : backtesting rolling‑window, métriques MASE, sMAPE, VaR‑scaled error.

---

## Module 3 – Apprentissage supervisé pour la prédiction de risques de crédit  
**Objectif mesurable** : Développer un classificateur (XGBoost ou LightGBM) capable de détecter les défauts de paiement avec un AUC‑ROC élevé sur un jeu de test indépendant.  
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
```

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
| **RMSE** | \(\sqrt{\frac{1}{N}\sum_{t=1}^{N}\left(\hat{y}_t - y_t\right)^2}\) | Erreur quadratique moyenne, sensible aux grandes erreurs |
| **MAE**  | \(\frac{1}{N}\sum_{t=1}^{N}\left|\hat{y}_t - y_t\right|\) | Erreur absolue moyenne, plus robuste aux outliers |
| **sMAPE**| \(\frac{100\%}{N}\sum_{t=1}^{N}\frac{|\hat{y}_t - y_t|}{(|y_t|+|\hat{y}_t|)/2}\) | Erreur de pourcentage symétrique, comparable entre séries |
| **MASE** | \(\frac{\text{MAE du modèle}}{\text{MAE d’un naïf (différence lag‑1)}}\) | Ratio d’erreur par rapport à un modèle de référence simple |

---

## Module 3 — contenu

## Module 3 – Apprentissage supervisé pour la prédiction de risques de crédit  

### 3.1 Construction des variables d’entrée  

| Variable | Source typique | Transformation recommandée |