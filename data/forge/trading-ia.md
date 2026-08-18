# Trading IA — Signaux & Stratégies

> Référence `trading-ia` · 79 €

## Plan

## Module 1 – Acquisition & Pré‑traitement des données de marché  
**Objectif mesurable** : Être capable de récupérer, stocker et nettoyer les flux de données historiques et temps réel (ticks, OHLCV) depuis au moins deux API publiques (ex. Binance, Alpha Vantage) en respectant les limites de taux et les formats JSON/CSV.  

**Notions couvertes**  
1. API REST & WebSocket : authentification, pagination, gestion du rate‑limit.  
2. Normalisation des séries temporelles : alignement des timestamps, conversion en fuseau UTC, gestion des gaps.  
3. Nettoyage des outliers et des erreurs de transmission (ex. prix négatifs, volumes nuls) via IQR et Z‑score.  
4. Construction d’un entrepôt de données (SQLite + Parquet) pour le versionnage et le replay.  
5. Validation de l’intégrité des données : checksum SHA‑256, contrôle de cohérence prix/volume.

---

## Module 2 – Ingénierie des caractéristiques et étiquetage des signaux  
**Objectif mesurable** : Générer un jeu de caractéristiques (features) reproductible et labelliser au moins 10 000 événements de marché pour entraîner un modèle de classification binaire (signal d’achat / signal de vente).  

**Notions couvertes**  
1. Calcul de facteurs techniques : EMA, RSI, MACD, Bollinger Bands, OBV, avec fenêtres glissantes paramétrables.  
2. Extraction de micro‑structures : spread, depth du carnet, ratio bid/ask, delta des ordres.  
3. Création de variables temporelles : heure du jour, jour de la semaine, volatilité intrajournalière (realized variance).  
4. Méthodes d’étiquetage : seuils de retour sur investissement (e.g., +2 % / –2 % sur 15 min), approche “triple‑barrier”.  
5. Normalisation & réduction de dimension : StandardScaler, PCA (variance expliquée ≥ 95 %).

---

## Module 3 – Modélisation prédictive et sélection de l’architecture IA  
**Objectif mesurable** : Implémenter, entraîner et comparer au moins trois modèles (statistique, machine learning, deep learning) en utilisant les mêmes jeux d’entraînement/validation et obtenir une courbe ROC‑AUC ≥ 0,70 pour chaque modèle.  

**Notions couvertes**  
1. Modèles linéaires : régression logistique avec régularisation L1/L2, interprétabilité des coefficients.  
2. Ensembles d’arbres : Random Forest, Gradient Boosting (XGBoost) – réglage du nombre d’estimators, profondeur maximale, taux d’apprentissage.  
3. Réseaux de neurones séquentiels : LSTM à une couche + couche dense, dropout 0,2, séquence d’entrée de 60 pas.  
4. Métriques d’évaluation : ROC‑AUC, précision, rappel, F1‑score, courbe de profit (cumulative returns).  
5. Validation croisée temporelle (walk‑forward) : découpage en blocs non chevauchants, évitement du « look‑ahead bias ».

---

## Module 4 – Back‑testing, optimisation et gestion du risque  
**Objectif mesurable** : Concevoir un moteur de back‑testing capable d’appliquer les signaux générés aux données historiques, d’ajuster les paramètres via optimisation

---

## Module 1 — contenu

## 1.1 API REST & WebSocket – Authentification, pagination, gestion du rate‑limit  

### 1.1.1 Binance REST (public)  
* **Endpoint** : `https://api.binance.com/api/v3/klines`  
* **Paramètres obligatoires** : `symbol`, `interval`, `startTime`, `endTime`, `limit` (max 1000).  
* **Rate‑limit** : 1200 requêtes/minute (≈ 20 req/s) pour le poids de requête = 1.  
* **Gestion** : implémenter un compteur de poids et un `sleep` dès que le poids cumulé dépasse 1200.  

```python
import time, hashlib, hmac, requests, pandas as pd
from collections import deque

BINANCE_URL = "https://api.binance.com/api/v3/klines"
MAX_WEIGHT = 1200          # poids max par minute
WINDOW = 60                # secondes

# file‑wide sliding window of request weights
weights = deque(maxlen=MAX_WEIGHT)

def _wait_if_needed():
    # si le nombre d'éléments dans la fenêtre = MAX_WEIGHT, on a atteint le quota
    if len(weights) == MAX_WEIGHT:
        oldest = weights[0]
        elapsed = time.time() - oldest
        if elapsed < WINDOW:
            time.sleep(WINDOW - elapsed)

def fetch_binance_klines(symbol: str, interval: str,
                        start_ts: int, end_ts: int) -> pd.DataFrame:
    """Retourne un DataFrame OHLCV (open, high, low, close, volume)"""
    all_rows = []
    start = start_ts
    while start < end_ts:
        _wait_if_needed()
        params = {
            "symbol": symbol,
            "interval": interval,
            "startTime": start,
            "endTime": end_ts,
            "limit": 1000,
        }
        resp = requests.get(BINANCE_URL, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if not data:
            break
        # chaque ligne = [open_time, o, h, l, c, v, close_time, ...]
        df = pd.DataFrame(data,
                          columns=["open_time", "open", "high", "low", "close",
                                   "volume", "close_time", "quote_asset_vol",
                                   "trades", "taker_base_vol", "taker_quote_vol",
                                   "ignore"])
        df["open_time"] = pd.to_datetime(df["open_time"], unit="ms", utc=True)
        df["close_time"] = pd.to_datetime(df["close_time"], unit="ms", utc=True)
        df = df[["open_time", "open", "high", "low", "close", "volume"]]
        all_rows.append(df)
        # le timestamp du prochain appel = close_time du dernier kline + 1 ms
        start = int(df["close_time"].iloc[-1].timestamp() * 1000) + 1
        # mise à jour du poids
        weights.append(time.time())
    return pd.concat(all_rows, ignore_index=True)
```

* **Points clés**  
  * `limit=1000` minimise le nombre d’appels.  
  * Le `while` avance le `start` avec le `close_time` du dernier lot.  
  * Le compteur `weights` utilise un `deque` pour garder les timestamps des dernières requêtes.  

### 1.1.2 Binance WebSocket (ticks)  
```python
import json, websockets, asyncio, pandas as pd

WS_URL = "wss://stream.binance.com:9443/ws/btcusdt@trade"

async def stream_trades():
    async with websockets.connect(WS_URL) as ws:
        async for message in ws:
            data = json.loads(message)
            # Exemple de payload : {'e':'trade','E':162..., 's':'BTCUSDT', 'p':'...','q':'...'}
            ts = pd.to_datetime(data["E"], unit="ms", utc=True)
            price = float(data["p"])
            qty   = float(data["q"])
            print(f"{ts} | price={price:.2f} | qty={qty}")

# asyncio.run(stream_trades())
```
* **Rate‑limit** : 5 messages/s max par connexion.  
* **Bonne pratique** : si le débit dépasse 5 msg/s, Binance ferme la connexion ; implémenter un `asyncio.sleep(0.2)` entre les traitements lourds.

### 1.1.3 Alpha Vantage REST (historique)  
* **Endpoint** : `https://www.alphavantage.co/query`  
* **Clé API** : obligatoire, fournie lors de l’inscription.  
* **Rate‑limit** : 5 requêtes/minute (standard).  
* **Gestion** : `time.sleep(12)` entre deux appels (12 s > 60/5).  

```python
import os, time, requests, pandas as pd

AV_API_KEY = os.getenv("AV_API_KEY")
AV_URL = "https://www.alphavantage.co/query"

def fetch_av_daily(symbol: str, outputsize: str = "full") -> pd.DataFrame:
    """Daily OHLCV pour US‑equities (format CSV dans la réponse)"""
    params = {
        "function": "TIME_SERIES_DAILY_ADJUSTED",
        "symbol": symbol,
        "outputsize": outputsize,
        "apikey": AV_API_KEY,
        "datatype": "csv",
    }
    resp = requests.get(AV_URL, params=params, timeout=10)
    resp.raise_for_status()
    df = pd.read_csv(pd.compat.StringIO(resp.text), parse_dates=["timestamp"])
    df.rename(columns={"timestamp": "date",
                       "open": "open",
                       "high": "high",
                       "low": "low",
                       "close": "close",
                       "adjusted

---

## Module 2 — contenu

## Module 2 – Ingénierie des caractéristiques et étiquetage des signaux  

### 2.1 Calcul de facteurs techniques  

| Facteur | Formule | Paramètres clés | Implémentation (pandas) |
|---------|---------|----------------|------------------------|
| EMA (Exponential Moving Average) | `EMA_t = α·P_t + (1‑α)·EMA_{t‑1}` avec `α = 2/(N+1)` | `N` = période (ex. 20) | `df['EMA_20'] = df['close'].ewm(span=20, adjust=False).mean()` |
| RSI (Relative Strength Index) | `RSI = 100 – 100/(1+RS)` où `RS = avg_gain / avg_loss` | `N` = période (ex. 14) | `delta = df['close'].diff(); up = delta.clip(lower=0); down = -delta.clip(upper=0); roll_up = up.ewm(span=14, adjust=False).mean(); roll_down = down.ewm(span=14, adjust=False).mean(); df['RSI_14'] = 100 - 100/(1+roll_up/roll_down)` |
| MACD | `MACD = EMA_{fast} – EMA_{slow}` ; Signal = EMA_{macd}` | `fast=12, slow=26, signal=9` | `fast = df['close'].ewm(span=12, adjust=False).mean(); slow = df['close'].ewm(span=26, adjust=False).mean(); df['MACD'] = fast - slow; df['MACD_signal'] = df['MACD'].ewm(span=9, adjust=False).mean()` |
| Bollinger Bands | `MA = SMA_N`; `Upper = MA + k·σ`; `Lower = MA – k·σ` | `N` = période, `k` = facteur (typ. 2) | `df['MA_20'] = df['close'].rolling(20).mean(); df['STD_20'] = df['close'].rolling(20).std(); df['BB_upper'] = df['MA_20'] + 2*df['STD_20']; df['BB_lower'] = df['MA_20'] - 2*df['STD_20']` |
| OBV (On‑Balance Volume) | `OBV_t = OBV_{t‑1} + sign(P_t – P_{t‑1})·V_t` | Aucun | `obv = (np.sign(df['close'].diff()) * df['volume']).fillna(0).cumsum(); df['OBV'] = obv` |

**Bonnes pratiques**  
- Utiliser `adjust=False` pour les EMA afin de reproduire la formule de la plupart des plateformes.  
- Vérifier que la série ne contient pas de `NaN` avant d’appliquer les rolling windows ; sinon, les premiers `N‑1` points seront `NaN`.  
- Conserver les valeurs brutes (ex. `close`) ainsi que les facteurs pour pouvoir recomposer les signaux plus tard.

---

### 2.2 Extraction de micro‑structures  

| Variable | Description | Calcul |
|----------|-------------|--------|
| **Spread** | Différence entre meilleur ask et meilleur bid | `df['spread'] = df['ask_price'] - df['bid_price']` |
| **Depth imbalance** | `(BidVol – AskVol) / (BidVol + AskVol)` | `df['depth_imbalance'] = (df['bid_volume'] - df['ask_volume']) / (df['bid_volume'] + df['ask_volume']).replace(0, np.nan)` |
| **Mid‑price** | Prix moyen du carnet | `df['mid_price'] = (df['ask_price'] + df['bid_price']) / 2` |
| **Order‑flow delta** | Variation du volume d’achat vs de vente sur un intervalle | `df['delta_volume'] = df['buy_volume'].rolling(window=5).sum() - df['sell_volume'].rolling(window=5).sum()` |

> **Note** : les flux de carnet (`bid_price`, `ask_price`, …) sont généralement fournis via WebSocket en temps réel. Pour les back‑tests, agrégez‑les à la même résolution que les OHLCV (ex. 1 min) en prenant la moyenne ou le dernier tick de chaque minute.

---

### 2.3 Variables temporelles  

```python
import pandas as pd
import numpy as np

def add_temporal_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ajoute les variables temporelles suivantes à un DataFrame contenant
    une colonne 'timestamp' au format datetime64[ns] (UTC) :
      - hour_of_day  : 0‑23
      - day_of_week  : 0‑6 (lundi=0)
      - is_market_open : bool (9:30‑16:00 UTC pour NYSE)
      - realized_variance_5m : variance des rendements sur les 5 dernières minutes
    """
    # S'assurer que le timestamp est en UTC
    df = df.copy()
    df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)

    # 1. Heure et jour
    df['hour_of_day'] = df['timestamp'].dt.hour
    df['day_of_week'] = df['timestamp'].dt.dayofweek

    # 2. Fenêtre d'ouverture (exemple NYSE, ajuster si besoin)
    df['is_market_open'] = df['hour_of_day'].between(13, 20)  # 9:30‑16:00 EST = 13‑20 UTC

    # 3. Rendements log
    df['log_ret'] = np.log(df['close']).diff()

    # 4. Variance réalisée sur 5 min (30 ticks si 1 s resolution)
    window = 5  # minutes, correspond à 5 lignes si les données sont déjà en 1‑min
    df['realized_variance_5m'] = (
        df

---

## Module 3 — contenu

## Module 3 – Modélisation prédictive et sélection de l’architecture IA  

### 3.1. Cadre expérimental commun  

| Élément | Description | Implémentation Python |
|--------|-------------|-----------------------|
| **Jeu de données** | `X` : matrice (n_samples, n_features) normalisée ; `y` : 0 = vente, 1 = achat. | `X = features.values.astype(np.float32)`<br>`y = labels.values.astype(np.int64)` |
| **Split temporel** | 70 % entraînement (les plus anciens), 15 % validation, 15 % test. | ```python<br>train_end = int(0.7 * len(df))<br>val_end   = int(0.85 * len(df))<br>X_train, y_train = X[:train_end], y[:train_end]<br>X_val,   y_val   = X[train_end:val_end], y[train_end:val_end]<br>X_test,  y_test  = X[val_end:], y[val_end:]<br>``` |
| **Standardisation** | `StandardScaler` fit sur le train, appliqué aux trois ensembles. | ```python<br>scaler = StandardScaler().fit(X_train)<br>X_train = scaler.transform(X_train)<br>X_val   = scaler.transform(X_val)<br>X_test  = scaler.transform(X_test)<br>``` |
| **Évaluation** | ROC‑AUC, précision, rappel, F1, courbe de profit cumulée. | `roc_auc_score(y_true, y_score)`, `precision_score`, `recall_score`, `f1_score`. |
| **Cross‑validation temporelle** | Walk‑forward de 5 blocs : chaque bloc = 20 % du train. | Utiliser `sklearn.model_selection.TimeSeriesSplit(n_splits=5)`. |

---

### 3.2. Modèle linéaire : régression logistique avec régularisation  

#### 3.2.1. Formulation mathématique  

\[
\hat{p}(x) = \sigma\bigl(w^{\top}x + b\bigr),\qquad
\sigma(z)=\frac{1}{1+e^{-z}}
\]

Objectif : minimiser la perte logistique pénalisée  

\[
\mathcal{L}(w,b)= -\frac{1}{N}\sum_{i=1}^{N}\Bigl[y_i\log\hat{p}(x_i)+(1-y_i)\log\bigl(1-\hat{p}(x_i)\bigr)\Bigr] + \lambda R(w)
\]

- **L1** : \(R(w)=\|w\|_1\) → sélection de variables.  
- **L2** : \(R(w)=\frac{1}{2}\|w\|_2^2\) → stabilité numérique.

#### 3.2.2. Implémentation (scikit‑learn)  

```python
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, classification_report

# modèle L1 (sparse) + C inversé du lambda
logreg_l1 = LogisticRegression(
    penalty='l1',
    C=0.1,               # lambda = 1/C = 10
    solver='saga',       # compatible L1
    max_iter=1000,
    n_jobs=-1,
    random_state=42,
)

logreg_l1.fit(X_train, y_train)

# probas sur le jeu de validation
y_val_proba = logreg_l1.predict_proba(X_val)[:, 1]
auc_val = roc_auc_score(y_val, y_val_proba)
print(f'ROC‑AUC validation : {auc_val:.4f}')

# métriques détaillées
y_val_pred = (y_val_proba >= 0.5).astype(int)
print(classification_report(y_val, y_val_pred, digits=4))
```

**Points de vigilance**  
* `solver='saga'` est le seul compatible avec `penalty='l1'` et accepte les données dense ou sparse.  
* Le paramètre `C` contrôle la force de la régularisation ; des valeurs trop petites (C < 1e‑4) provoquent un under‑fit, trop grandes → over‑fit.  
* La convergence peut échouer si les variables ne sont pas centrées ; `StandardScaler` est obligatoire.  

---

### 3.3. Modèle d’ensemble : Gradient Boosting (XGBoost)  

#### 3.3.1. Principes  

XGBoost construit un ensemble de **arbres de décision** en ajoutant successivement des arbres qui corrigent les résidus du modèle précédent. La fonction objectif à chaque itération :  

\[
\mathcal{L}^{(t)} = \sum_{i=1}^{N} \ell\bigl(y_i, \hat{y}_i^{(t-1)} + f_t(x_i)\bigr) + \Omega(f_t)
\]

avec \(\Omega(f) = \gamma T + \frac{1}{2}\lambda \|w\|^2\) (penalité sur le nombre de feuilles \(T\) et les poids).  

#### 3.3.2. Implémentation (xgboost)  

```python
import xgboost as xgb
from sklearn.metrics import roc_auc_score

# DMatrix optimise la mémoire et le calcul
dtrain = xgb.DMatrix(X_train, label=y_train)
dval   = xgb.DMatrix(X_val,   label=y_val)

params = {
    'objective'      : 'binary:logistic',
    'eval_metric'    : 'auc',
    'eta'            : 0.05,      # taux d'apprentissage
    'max_depth'      : 6,
    'subsample'      : 0.8,
    'colsample_bytree': 0.8,
    'lambda'         : 1.0,

---

## Module 4 — contenu

## Module 4 – Back‑testing, optimisation et gestion du risque  

### 4.1 Architecture d’un moteur de back‑testing  

| Composant | Rôle | Implémentation minimale (Python) |
|-----------|------|---------------------------------|
| **DataHandler** | Charge les OHLCV déjà nettoyés, aligne les timestamps, fournit une vue « slice » à chaque pas de temps. | `pd.read_parquet()` → `DataFrame.set_index('timestamp')`. |
| **SignalGenerator** | Applique le modèle IA (ou toute règle) et renvoie `1` (long), `-1` (short) ou `0` (neutral) pour chaque barre. | `signals = model.predict(features)` |
| **Portfolio** | Gère la taille de la position, le cash, le calcul du P&L, les frais, le slippage. | Méthodes `update_position()`, `update_cash()`. |
| **ExecutionSimulator** | Transforme le signal en ordre réel (market/limit) et applique un délai (`latency`) et un facteur de slippage. | `price_executed = price * (1 + slippage * np.sign(order))`. |
| **RiskEngine** | Applique les règles de gestion du risque (stop‑loss, take‑profit, max‑drawdown, exposure). | `if unrealized_drawdown > max_dd: close_all()`. |
| **MetricsCollector** | Calcule les indicateurs de performance (cumulative returns, Sharpe, Calmar, turnover). | `np.mean(returns) / np.std(returns) * sqrt(252)`. |
| **WalkForwardValidator** | Découpe la série temporelle en blocs « in‑sample » / « out‑of‑sample » et répète le cycle. | `for i in range(n_blocks): train = data[i*len:block]; test = data[(i+1)*len:block]`. |

> **Note technique** : chaque composant doit être purement fonctionnel (pas de dépendance globale) pour faciliter les tests unitaires et la parallélisation (`multiprocessing` ou `joblib`).

---

### 4.2 Implémentation fonctionnelle (exemple complet)

```python
# backtest_engine.py
import pandas as pd
import numpy as np

class DataHandler:
    """Charge les données et les rend accessibles bar‑by‑bar."""
    def __init__(self, path: str, tz: str = "UTC"):
        self.df = pd.read_parquet(path).set_index('timestamp')
        self.df = self.df.tz_convert(tz)
        self.idx = 0
        self.n = len(self.df)

    def next_bar(self):
        """Retourne (timestamp, ohlcv) ou None à la fin."""
        if self.idx >= self.n:
            return None
        row = self.df.iloc[self.idx]
        ts = self.df.index[self.idx]
        self.idx += 1
        return ts, row

    def reset(self):
        self.idx = 0


class ExecutionSimulator:
    """Simule un market order avec latence et slippage."""
    def __init__(self, latency: int = 1, slippage: float = 0.0005):
        self.latency = latency          # nombre de barres avant exécution
        self.slippage = slippage        # proportion du prix (ex. 5 bps)

    def execute(self, price: float, side: int):
        """side = +1 (buy) ou -1 (sell). Retourne le prix exécuté."""
        # slippage appliqué dans le sens de l’ordre
        adj = 1 + self.slippage * side
        return price * adj


class Portfolio:
    """Gestion du cash, des positions et du P&L."""
    def __init__(self, initial_cash: float = 100_000, commission: float = 0.0002):
        self.cash = initial_cash
        self.position = 0            # nombre de contrats / actions
        self.commission = commission
        self.equity_curve = []       # (timestamp, equity)

    def update(self, ts, price, executed_price, side, size):
        """Applique l’ordre, ajuste cash et position."""
        # frais = commission * taille * prix exécuté
        fee = self.commission * abs(size) * executed_price
        self.cash -= executed_price * size + fee
        self.position += size
        # valeur de portefeuille à la clôture de la barre
        equity = self.cash + self.position * price
        self.equity_curve.append((ts, equity))

    def close_all(self, price, ts):
        """Liquidation immédiate de la position restante."""
        if self.position != 0:
            side = -np.sign(self.position)
            size = -self.position
            exec_price = price * (1 + 0.0005 * side)   # slippage fixe pour clôture
            fee = self.commission * abs(size) * exec_price
            self.cash += self.position * price - fee
            self.position = 0
            equity = self.cash
            self.equity_curve.append((ts, equity))


def backtest(data_path: str,
             model,                     # fonction qui renvoie un signal (int)
             initial_cash: float = 100_000,
             latency: int = 1,
             slippage: float = 0.0005,
             commission: float = 0.0002,
             max_dd: float = 0.20):
    """Boucle principale du back‑testing."""
    dh =

---

## Module 5 — contenu

## Module 5 – Déploiement, monitoring et maintenance des modèles IA de trading  

### 5.1 Architecture de déploiement  

| Composant | Rôle | Technologie typique | Contraintes |
|-----------|------|----------------------|-------------|
| **Feature Store** | Fournit les features pré‑calculées en temps réel | Redis Streams, Apache Kafka + ksqlDB | Latence < 5 ms, persistance du dernier snapshot |
| **Inference Service** | Expose un endpoint HTTP/WS pour la prédiction | FastAPI / Flask + Uvicorn, gRPC | Concurrence ≥ 100 RPS, timeout ≤ 200 ms |
| **Orchestrateur** | Gère le scaling, le rolling‑update et la résilience | Kubernetes (Deployment, HPA) | Pod‑disruption‑budget, readiness‑probe |
| **Observabilité** | Collecte métriques, logs, traces | Prometheus + Grafana, Loki, OpenTelemetry | Exporter les métriques de latence, taux d’erreur, distribution des scores |
| **CI/CD** | Build, test, déploiement automatisé | GitHub Actions, GitLab CI, Argo CD | Validation du modèle (ROC‑AUC ≥ 0,70) avant promotion |

> **Règle de conception** : séparer la couche *feature engineering* (stateful) de la couche *inference* (stateless) pour éviter les effets de bord lors du scaling horizontal.

---

### 5.2 Containerisation du modèle  

```dockerfile
# Dockerfile – inference service
FROM python:3.11-slim

# 1. Dépendances système (ex. libgomp pour XGBoost)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 && rm -rf /var/lib/apt/lists/*

# 2. Crée un environnement virtuel minimal
ENV VENV=/opt/venv
RUN python -m venv $VENV
ENV PATH="$VENV/bin:$PATH"

# 3. Copie le code et les artefacts
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY model/ model/          # dossier contenant model.pkl, scaler.pkl
COPY inference/ inference/  # package FastAPI

# 4. Expose le port de l'API
EXPOSE 8000

# 5. Commande d’entrée
CMD ["uvicorn", "inference.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

*Points de vigilance*  
- **Version du runtime** : le même `python` et les mêmes versions de `numpy`, `pandas`, `xgboost` que celles utilisées lors de l’entraînement évitent les erreurs de désérialisation (`pickle`/`joblib`).  
- **Taille de l’image** : `slim` + `--no-cache-dir` minimise le temps de pull et le surface d’attaque.  
- **Sécurité** : ne pas copier le dossier `data/` contenant les historiques bruts, uniquement les artefacts de modèle.

---

### 5.3 Service d’inférence (FastAPI)  

```python
# inference/main.py
import json
import pickle
from pathlib import Path
from typing import List, Literal

import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, validator

# -------------------------------------------------
# 1. Chargement des artefacts (singleton)
# -------------------------------------------------
MODEL_PATH = Path(__file__).parent.parent / "model" / "model.pkl"
SCALER_PATH = Path(__file__).parent.parent / "model" / "scaler.pkl"

with open(MODEL_PATH, "rb") as f:
    model = pickle.load(f)               # type: ignore
with open(SCALER_PATH, "rb") as f:
    scaler = pickle.load(f)              # type: ignore

# -------------------------------------------------
# 2. Schéma d’entrée (validation stricte)
# -------------------------------------------------
class FeatureVector(BaseModel):
    """Un vecteur de features pré‑calculées."""
    ema_20: float = Field(..., description="EMA 20 periods")
    rsi_14: float = Field(..., ge=0, le=100)
    macd: float
    volume: float = Field(..., gt=0)
    hour_of_day: int = Field(..., ge=0, le=23)
    day_of_week: int = Field(..., ge=0, le=6)

    @validator("*")
    def no_nan(cls, v):
        if pd.isna(v):
            raise ValueError("NaN not allowed")
        return v

# -------------------------------------------------
# 3. API
# -------------------------------------------------
app = FastAPI(
    title="Trading IA Inference Service",
    version="0.1.0",
    description="Prédiction binaire (1=achat, 0=vente) à partir d’un vecteur de features."
)

@app.post("/predict")
def predict(features: List[FeatureVector]) -> dict:
    """
    Retourne la probabilité d’achat pour chaque vecteur.
    - **Input**: