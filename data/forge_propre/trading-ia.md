# Trading IA — Signaux & Stratégies

> Référence `trading-ia`

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
**Objectif mesurable** : Générer un jeu de caractéristiques (features) reproductible et labelliser un nombre suffisant d’événements de marché pour entraîner un modèle de classification binaire (signal d’achat / signal de vente).  

**Notions couvertes**  
1. Calcul de facteurs techniques : EMA, RSI, MACD, Bollinger Bands, OBV, avec fenêtres glissantes paramétrables.  
2. Extraction de micro‑structures : spread, depth du carnet, ratio bid/ask, delta des ordres.  
3. Création de variables temporelles : heure du jour, jour de la semaine, volatilité intrajournalière (realized variance).  
4. Méthodes d’étiquetage : seuils de retour sur investissement, approche “triple‑barrier”.  
5. Normalisation & réduction de dimension : StandardScaler, PCA (variance expliquée élevée).

---

## Module 3 – Modélisation prédictive et sélection de l’architecture IA  
**Objectif mesurable** : Implémenter, entraîner et comparer au moins trois modèles (statistique, machine learning, deep learning) en utilisant les mêmes jeux d’entraînement/validation et obtenir une courbe ROC‑AUC satisfaisante pour chaque modèle.  

**Notions couvertes**  
1. Modèles linéaires : régression logistique avec régularisation L1/L2, interprétabilité des coefficients.  
2. Ensembles d’arbres : Random Forest, Gradient Boosting (XGBoost) – réglage du nombre d’estimators, profondeur maximale, taux d’apprentissage.  
3. Réseaux de neurones séquentiels : LSTM à une couche + couche dense, dropout, séquence d’entrée de plusieurs pas.  
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
* **Paramètres obligatoires** : `symbol`, `interval`, `startTime`, `endTime`, `limit`.  
* **Rate‑limit** : 1200 requêtes/minute pour le poids de requête = 1.  
* **Gestion** : implémenter un compteur de poids et un `sleep` dès que le poids cumulé dépasse le quota.  

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
* **Bonne pratique** : si le débit dépasse la limite, Binance ferme la connexion ; implémenter une pause entre les traitements lourds.

### 1.1.3 Alpha Vantage REST (historique)  
* **Endpoint** : `https://www.alphavantage.co/query`  
* **Clé API** : obligatoire, fournie lors de l’inscription.  
* **Rate‑limit** : 5 requêtes/minute (standard).  
* **Gestion** : pause entre deux appels.  

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
                       "adjusted": "adjusted"}, inplace=True)
    return df
```

---

## Module 2 — contenu

## Module 2 – Ingénierie des caractéristiques et étiquetage des signaux  

### 2.1 Calcul de facteurs techniques  

| Facteur | Formule | Paramètres clés | Implémentation (pandas) |
|---------|---------|----------------|------------------------|
| EMA (Exponential Moving Average) | `EMA_t = α·P_t + (1‑α)·EMA_{t‑1}` avec `α = 2/(N+1)` | `N` = période | `df['EMA_20'] = df['close'].ewm(span=20, adjust=False).mean()` |
| RSI (Relative Strength Index) | `RSI = 100 – 100/(1+RS)` où `RS = avg_gain / avg_loss` | `N` = période | `delta = df['close'].diff(); up = delta.clip(lower=0); down = -delta.clip(upper=0); roll_up = up.ewm(span=14, adjust=False).mean(); roll_down = down.ewm(span=14, adjust=False).mean(); df['RSI_14'] = 100 - 100/(1+roll_up/roll_down)` |
| MACD | `MACD = EMA_{fast} – EMA_{slow}` ; Signal = EMA_{macd}` | `fast`, `slow`, `signal` | `fast = df['close'].ewm(span=12, adjust=False).mean(); slow = df['close'].ewm(span=26, adjust=False).mean(); df['MACD'] = fast - slow; df['MACD_signal'] = df['MACD'].ewm(span=9, adjust=False).mean()` |
| Bollinger Bands | `MA = SMA_N`; `Upper = MA + k·σ`; `Lower = MA – k·σ` | `N` = période, `k` = facteur | `df['MA_20'] = df['close'].rolling(20).mean(); df['STD_20'] = df['close'].rolling(20).std(); df['BB_upper'] = df['MA_20'] + 2*df['STD_20']; df['BB_lower'] = df['MA_20'] - 2*df['STD_20']` |
| OBV (On‑Balance Volume) | `OBV_t = OBV_{t‑1} + sign(P_t – P_{t‑1})·V_t` | Aucun | `obv = (np.sign(df['close'].diff()) * df['volume']).fillna(0).cumsum(); df['OBV'] = obv` |

**Bonnes pratiques**  
- Utiliser `adjust=False` pour les EMA afin de reproduire la formule de la plupart des plateformes.  
- Vérifier que la série ne contient pas de `NaN` avant d’appliquer les rolling windows ; sinon, les premiers points seront `NaN`.  
- Conserver les valeurs brutes (ex. `close`) ainsi que les facteurs pour pouvoir recomposer les signaux plus tard.

---

### 2.2 Extraction de micro‑structures  

| Variable | Description | Calcul |
|----------|-------------|--------|
| **Spread** | Différence entre meilleur ask et meilleur bid | `df['spread'] = df['ask_price'] - df['bid_price']` |
| **Depth imbalance** | `(BidVol – AskVol) / (BidVol + AskVol)` | `df['depth_imbalance'] = (df['bid_volume'] - df['ask_volume'])