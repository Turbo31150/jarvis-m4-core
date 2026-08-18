# TradeOracle — Consensus Multi-IA Crypto

> Référence `tradeoracle`

## Plan

## Module 1 : Architecture du système TradeOracle  
**Objectif mesurable** : Concevoir et déployer une instance fonctionnelle de TradeOracle sur un cluster Kubernetes, en justifiant chaque composant par son rôle dans le pipeline de consensus.  
**Notions couvertes**  
1. Topologie micro‑services (API Gateway, Service de collecte, Engine de consensus, Base de données de séries temporelles).  
2. Déploiement conteneurisé : Dockerfile minimal, Helm chart, configuration des probes de santé.  
3. Gestion des secrets et des clés API (Kubernetes Secrets, HashiCorp Vault).  
4. Communication inter‑services via gRPC et protobuf : définition des messages, versionning.  
5. Monitoring et logs centralisés (Prometheus, Grafana, Loki).

## Module 2 : Acquisition et normalisation des flux de données crypto‑actifs  
**Objectif mesurable** : Implémenter des connecteurs robustes pour plusieurs exchanges (Binance, Kraken, Coinbase) et produire un flux normalisé conforme au schéma TradeOracle avec une latence très faible.  
**Notions couvertes**  
1. API REST et WebSocket des principaux exchanges : authentification HMAC, limites de taux.  
2. Gestion des désynchronisations de timestamps (NTP, drift correction).  
3. Transformation des données brutes en événements TradeOracle (OHLCV, order‑book snapshots, trades).  
4. Gestion des erreurs et reconnections automatiques (circuit breaker, exponential back‑off).  
5. Sérialisation en Avro/Parquet pour le stockage à froid.

## Module 3 : Moteur de consensus multi‑IA  
**Objectif mesurable** : Développer un pipeline d’agrégation qui combine plusieurs modèles de prévision (LSTM et Gradient Boosting) et un algorithme de consensus (Weighted Majority Voting) pour produire une prédiction de prix avec un RMSE inférieur à un seuil raisonnable sur un jeu de test représentatif.  
**Notions couvertes**  
1. Entraînement et export de modèles TensorFlow / PyTorch (SavedModel, ONNX).  
2. Inference en temps réel avec Triton Inference Server.  
3. Métriques de performance (RMSE, MAE, Sharpe) et calibration des poids de vote.  
4. Détection de dérive de modèle (concept drift) via monitoring des résidus.  
5. Orchestration du pipeline avec Apache Airflow (DAGs, XCom).

## Module 4 : Stratégies de trading algorithmique basées sur le consensus  
**Objectif mesurable** : Implémenter et back‑tester deux stratégies (mean‑reversion et breakout) qui utilisent les signaux du moteur de consensus, et obtenir un ratio gain/perte (Profit Factor) supérieur à un niveau satisfaisant sur les données historiques de 2022‑2023.  
**Notions couvertes**  
1. Construction de signaux d’entrée : seuils dynamiques, filtres de volatilité.  
2. Gestion du risque (position sizing, stop‑loss, take‑profit, VaR).  
3. Back‑testing avec vectorbt et Zipline : data‑alignment, slippage model.  
4. Optimisation de paramètres via Bayesian Optimization (optuna).  
5. Export des ordres vers les APIs de brokers (CCXT, FIX).

## Module

---

## Module 1 — contenu

## 1. Topologie micro‑services

| Service | Rôle | Interface exposée | Persistance |
|---------|------|-------------------|-------------|
| **API Gateway** | Point d’entrée unique, routage, authentification légère (JWT) | HTTP/REST (JSON) + gRPC (optionnel) | Aucun |
| **Collector** | Connexion aux exchanges, agrégation brute, normalisation | gRPC `CollectService` (push) | Aucun (les données brutes sont immédiatement envoyées au moteur) |
| **Consensus Engine** | Chargé de l’inférence IA, agrégation des prédictions, calcul du consensus | gRPC `ConsensusService` (request/response) | TSDB (ex. InfluxDB, TimescaleDB) pour les séries temporelles de prix prédites |
| **TSDB** | Stockage durable des OHLCV, order‑book, prédictions | HTTP (REST) ou InfluxDB line protocol | Persistance sur disque (PVC) |

Le diagramme logique (simplifié) :

```
[Client] → HTTP → [API‑Gateway] → gRPC → [Collector] → gRPC → [Consensus Engine] ↔ SQL/TSDB
```

- Tous les services sont **stateless** (sauf la TSDB).  
- La scalabilité horizontale s’obtient en dupliquant chaque pod; le service de découverte Kubernetes assure le load‑balancing.  
- Le **collector** ne garde aucun état entre deux appels ; il s’appuie sur le **gateway** pour le throttling global (limite de taux agrégée).

---

## 2. Déploiement conteneurisé

### 2.1 Dockerfile minimal (Python 3.11)

```dockerfile
# syntax = docker/dockerfile:1.4
FROM python:3.11-slim AS builder

# 1. Installer les dépendances de compilation (si besoin)
RUN apt-get update && apt-get install -y --no-install-recommends gcc && \
    rm -rf /var/lib/apt/lists/*

# 2. Créer un environnement isolé
WORKDIR /app
COPY pyproject.toml poetry.lock ./
RUN pip install --no-cache-dir poetry && poetry export -f requirements.txt --output requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# 3. Copier le code source (exclure les dossiers .git, tests, etc.)
COPY . .

# 4. Runtime image (multi‑stage)
FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /app /app

# 5. Variables d’environnement obligatoires
ENV PYTHONUNBUFFERED=1 \
    GRPC_PORT=50051

# 6. Lancement du service (exemple : collector)
ENTRYPOINT ["python", "-m", "collector.main"]
```

**Points de vérification**  
- `--no-install-recommends` évite les paquets inutiles, réduisant la surface d’attaque.  
- Le multi‑stage élimine le compilateur du runtime, réduisant la taille de l’image.  
- `PYTHONUNBUFFERED=1` garantit que les logs sont flushés immédiatement, indispensable pour Loki.

### 2.2 Helm chart (extrait : `templates/deployment.yaml`)

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "tradeoracle.fullname" . }}-collector
  labels: {{- include "tradeoracle.labels" . | nindent 4 }}
spec:
  replicas: {{ .Values.collector.replicaCount }}
  selector:
    matchLabels:
      app.kubernetes.io/name: {{ include "tradeoracle.name" . }}
      app.kubernetes.io/component: collector
  template:
    metadata:
      labels:
        app.kubernetes.io/name: {{ include "tradeoracle.name" . }}
        app.kubernetes.io/component: collector
    spec:
      containers:
        - name: collector
          image: "{{ .Values.collector.image.repository }}:{{ .Values.collector.image.tag }}"
          imagePullPolicy: {{ .Values.collector.image.pullPolicy }}
          ports:
            - containerPort: {{ .Values.collector.service.port }}
          envFrom:
            - secretRef:
                name: {{ include "tradeoracle.fullname" . }}-secrets
          livenessProbe:
            grpc:
              port: {{ .Values.collector.service.port }}
            initialDelaySeconds: 10
            periodSeconds: 30
          readinessProbe:
            grpc:
              port: {{ .Values.collector.service.port }}
            initialDelaySeconds: 5
            periodSeconds: 10
          resources:
            limits:
              cpu: "500m"
              memory: "256Mi"
            requests:
              cpu: "250m"
              memory: "128Mi"
```

- **`envFrom.secretRef`** injecte les clés API (voir § 3).  
- Les probes **gRPC** utilisent le même port que le service (`50051` par défaut).  
- Les limites / requests sont calibrées pour un service qui ne consomme que du CPU pendant les appels réseau.

### 2.3 Probes de santé

| Probe | Type | Condition de succès | Exemple de configuration |

---

## Module 2 — contenu

## Module 2 : Acquisition et normalisation des flux de données crypto‑actifs  

### 2.1 Architecture du collecteur  

| Composant | Rôle | Technologie | Points de vigilance |
|-----------|------|--------------|----------------------|
| **Connector** | Sous‑scrition WebSocket ou polling REST d’un exchange | `aiohttp` (REST), `websockets` (WS) | Gestion du *ping/pong*, reconnexion, limites de taux |
| **Normalizer** | Convertit le format natif en schéma TradeOracle (OHLCV, order‑book, trade) | Protobuf + Avro schema | Versionning du schema, champs manquants |
| **Timestamp synchronizer** | Aligne les timestamps avec le temps UTC du cluster | `ntplib` + correction de drift (ex. `offset = server_time - local_time`) | NTP fallback, dérive → rejet du message |
| **Buffer / Queue** | Découplage entre acquisition et persistance | Kafka topic `raw.trades` (partition = symbol) | Taille du batch, back‑pressure |
| **Serializer** | Sérialise les événements normalisés en Avro (ou Parquet) pour le stockage à froid | `fastavro` / `pyarrow` | Compatibilité du schema avec le lecteur downstream |

---

### 2.2 Gestion des secrets et authentification HMAC  

```yaml
# kubernetes secret (base64‑encoded)
apiVersion: v1
kind: Secret
metadata:
  name: exchange‑api‑keys
type: Opaque
data:
  binance_api_key:      <base64>
  binance_api_secret:   <base64>
  kraken_key:           <base64>
  kraken_secret:        <base64>
  coinbase_api_key:     <base64>
  coinbase_api_secret:  <base64>
```

*En Python* :

```python
import os
import base64
import hmac
import hashlib
import time
from urllib.parse import urlencode

def get_secret(name: str) -> str:
    """Lit un secret Kubernetes injecté en variable d'environnement."""
    b64 = os.getenv(name)
    if not b64:
        raise RuntimeError(f"Secret {name} non défini")
    return base64.b64decode(b64).decode()

BINANCE_KEY    = get_secret("BINANCE_API_KEY")
BINANCE_SECRET = get_secret("BINANCE_API_SECRET")
```

**HMAC pour Binance (REST)**  

```python
def binance_signature(query: dict) -> str:
    """Génère la signature HMAC SHA256 attendue par l'API Binance."""
    query_string = urlencode(query)
    return hmac.new(BINANCE_SECRET.encode(),
                    query_string.encode(),
                    hashlib.sha256).hexdigest()
```

---

### 2.3 Connecteur Binance (WebSocket)  

```python
import asyncio
import json
import time
import logging
from websockets import connect

BINANCE_WS_URL = "wss://stream.binance.com:9443/ws"

# Schéma protobuf simplifié (pseudo‑code)
# message Trade {
#   string symbol = 1;
#   uint64 ts_utc = 2;   // epoch ms
#   double price = 3;
#   double qty   = 4;
# }

async def binance_trade_stream(symbol: str, queue):
    """Sous‑scrition au flux de trades d'un symbole Binance."""
    stream = f"{symbol.lower()}@trade"
    url = f"{BINANCE_WS_URL}/{stream}"
    async with connect(url, ping_interval=20, ping_timeout=10) as ws:
        logging.info("Connected to Binance WS %s", stream)
        async for raw_msg in ws:
            try:
                data = json.loads(raw_msg)
                # Normalisation
                trade = {
                    "symbol": symbol.upper(),
                    "ts_utc": int(data["T"]),               # timestamp de l'échange
                    "price": float(data["p"]),
                    "qty":   float(data["q"]),
                }
                # Correction de drift (exemple simple)
                drift = time.time()*1000 - trade["ts_utc"]
                # > ms → désynchronisation
                if abs(drift) > 50:                     # > ms → désynchronisation
                    logging.warning("Drift %d ms, discarding", drift)
                    continue
                await queue.put(trade)                  # envoi vers le buffer
            except Exception as exc:

---

## Module 3 — contenu

## Module 3 : Moteur de consensus multi‑IA  

### 3.1 Entraînement et export des modèles  

| Étape | Action | Commande / API | Vérification |
|------|--------|----------------|--------------|
| **Collecte** | Sérialiser les OHLCV (1 min) dans un `DataFrame` Pandas, indexé par `timestamp`. | `df = pd.read_parquet('ohlcv.parquet')` | `df.head()` |
| **Pré‑traitement** | Normaliser chaque série avec `StandardScaler`. | `scaler = StandardScaler(); X = scaler.fit_transform(df[['open','high','low','close','volume']])` | `np.mean(X,axis=0)≈0` |
| **Split** | Diviser les données en ensembles d’entraînement, de validation et de test, en conservant l’ordre temporel. | `train, val, test = np.split(X, [int(.7*len(X)), int(.85*len(X))])` | `len(train)+len(val)+len(test)==len(X)` |
| **LSTM** | Modèle `tf.keras.Sequential([LSTM(64,return_sequences=False), Dense(1)])`. | ```python\nmodel = tf.keras.Sequential([\n    tf.keras.layers.LSTM(64, input_shape=(seq_len, n_features)),\n    tf.keras.layers.Dense(1)\n])\nmodel.compile(optimizer='adam', loss='mse')\nmodel.fit(train_X, train_y, epochs=30, validation_data=(val_X, val_y))\n``` | `model.evaluate(test_X, test_y)` renvoie une erreur quadratique moyenne faible |
| **Gradient Boosting** | `xgboost.XGBRegressor(max_depth=6, n_estimators=200, learning_rate=0.05)`. | ```python\nimport xgboost as xgb\ngb = xgb.XGBRegressor(\n    max_depth=6,\n    n_estimators=200,\n    learning_rate=0.05,\n    objective='reg:squarederror'\n)\ngb.fit(train_X, train_y)\n``` | `gb.score(test_X, test_y)` indique une forte capacité explicative du modèle |
| **Export LSTM** | `SavedModel` → `model.save('lstm_saved')`. | `model.save('models/lstm_saved')` | `ls models/lstm_saved` contient `saved_model.pb` |
| **Export GB** | Convertir en ONNX via `skl2onnx`. | ```python\nimport skl2onnx\nfrom skl2onnx import convert_sklearn\nfrom skl2onnx.common.data_types import FloatTensorType\nonnx_model = convert_sklearn(gb, initial_types=[('input', FloatTensorType([None, n_features]))])\nwith open('models/gb.onnx','wb') as f:\n    f.write(onnx_model.SerializeToString())\n``` | `onnxruntime.InferenceSession('models/gb.onnx')` charge sans erreur |
| **Versionnage** | Créer un tag Git `v1.0.0` et un fichier `model_manifest.json` contenant `{"lstm":"1.0.0","gb":"1.0.0","date":"2024-08-14"}`. | `git tag v1.0.0 && git push origin v1.0.0` | `cat model_manifest.json` |

### 3.2 Inference en temps réel avec Triton Inference Server  

#### 3.2.1 Déploiement du serveur  

```yaml
# helm/triton-values.yaml
service:
  type: ClusterIP
  port: 8000
model_repository: /models
resources:
  limits:
    cpu: "4"
    memory: "8Gi"
```

```bash
helm repo add nvcr https://helm.ngc.nvidia.com
helm install triton nvcr/triton-inference-server -f helm/triton-values.yaml
```

- **Vérification** : `curl -v http://triton-service:8000/v2/health/ready` doit renvoyer `200`.

#### 3.2.2 Client Python (gRPC)  

```python
import numpy as np
import tritonclient.grpc as grpcclient
from tritonclient.grpc import InferInput, InferRequestedOutput

# Connexion
triton = grpcclient.InferenceServerClient(url="triton-service:8008", verbose=False)

def predict_lstm(features: np.ndarray) -> float:
    """
    features : np.ndarray de forme (1, seq_len, n_features) en float32
    Retourne le prix prédit (float)
    """
    # 1. Construction du tensor d'entrée
    input_tensor = InferInput(
        name="input_0",               # nom du tensor tel que défini dans le modèle
        shape=features.shape,
        datatype="FP32"
    )
    input_tensor.set_data_from_numpy(features)

    # 2. Déclaration de la sortie attendue
    output = InferRequestedOutput(name="output_0")

    # 3. Appel d'inférence
    resp = triton.infer(
        model_name="lstm_saved",
        inputs=[input_tensor],
        outputs=[output]
    )

    # 4. Extraction du résultat
    pred = resp.as_numpy("output_0")  # shape (1, 1)
    return float(pred.squeeze())

def predict_gb(features: np.ndarray) -> float:
    """
    features : np.ndarray de forme (1, n_features) en float32
    """
    input_tensor = InferInput(name="input", shape=features.shape, datatype="FP32")
    input_tensor.set_data_from_numpy(features)

    output = InferRequestedOutput(name

---

## Module 4 — contenu

## 4.1 Construction des signaux d’entrée  

| Élément | Description technique | Implémentation typique |
|---------|----------------------|-----------------------|
| **Seuils dynamiques** | Le prix prédit `p̂_t` est comparé à la moyenne mobile exponentielle (EMA) de la série `p`. Le seuil est exprimé en écart‑type `σ_t` de la différence `Δ_t = p̂_t - EMA_t`. | ```python\ndef dynamic_threshold(ema, sigma, k):\n    return ema + k * sigma, ema - k * sigma\n``` |
| **Filtre de volatilité** | La volatilité instantanée est estimée par l’ATR (Average True Range) sur `n` barres. Un signal n’est accepté que si `ATR_t < beta * EMA_ATR_t`. | ```python\ndef volatility_filter(atr, ema_atr, beta):\n    return atr < beta * ema_atr\n``` |
| **Signal brut** | `signal = 1` (long) si `p̂_t > upper_thresh` et `volatility_filter` est vrai ; `signal = -1` (short) si `p̂_t < lower_thresh` et le filtre est vrai ; sinon `0`. | ```python\ndef generate_signal(p_pred, ema, sigma, atr, ema_atr, k, beta):\n    up, low = dynamic_threshold(ema, sigma, k)\n    if volatility_filter(atr, ema_atr, beta):\n        if p_pred > up:\n            return 1\n        if p_pred < low:\n            return -1\n    return 0\n``` |

### Points de vérification
* Le calcul de `σ_t` doit être réalisé sur la même fenêtre que l’EMA (ex. 20 bars) pour éviter le biais de look‑ahead.  
* L’ATR utilise le **True Range** : `max(high-low, abs(high-prev_close), abs(low-prev_close))`.  
* Toutes les séries sont alignées sur le même index temporel (`pd.DatetimeIndex` en UTC).  

---

## 4.2 Gestion du risque  

| Concept | Formule | Implémentation |
|---------|---------|----------------|
| **Position sizing (Kelly fraction)** | `f = (μ / σ²)` où `μ` est le gain moyen par trade et `σ` l’écart‑type des gains. | ```python\ndef kelly_fraction(mean_ret, std_ret):\n    return max(0.0, min(1.0, mean_ret / (std_ret ** 2)))\n``` |
| **Stop‑loss** | `SL = entry_price * (1 - sl_pct)` pour une position longue, `SL = entry_price * (1 + sl_pct)` pour courte. | ```python\ndef stop_price(entry, sl_pct, side):\n    return entry * (1 - sl_pct) if side == 1 else entry * (1 + sl_pct)\n``` |
| **Take‑profit** | `TP = entry_price * (1 + tp_pct)` (long) ou `TP = entry_price * (1 - tp_pct)` (short). | idem `stop_price` avec `tp_pct`. |
| **VaR** | `VaR = Z * σ_portfolio * sqrt(h)` où `Z` est le quantile correspondant au niveau de confiance souhaité, `σ_portfolio` la volatilité du portefeuille, `h` l’horizon (jours). | ```python\ndef portfolio_var(vol, horizon_days, Z):\n    return Z * vol * np.sqrt(horizon_days)\n``` |

### Pièges fréquents
1. **Over‑allocation** : multiplier la Kelly fraction par un facteur excessif entraîne un **draw‑down** exponentiel.  
2. **Slippage non modélisé** : le back‑test sous‑estime les coûts si le modèle de slippage est trop optimiste (ex. un slippage fixe).  
3. **Risque de corrélation** : appliquer la même `f` à plusieurs actifs sans tenir compte de la corrélation peut dépasser le capital disponible.  

---

## 4.3 Back‑testing avec **vectorbt**  

```python
import pandas as pd
import numpy as np
import vectorbt as vbt
from sklearn.metrics import mean_squared_error

# -------------------------------------------------
# 1. Chargement des données (OHLCV) et du signal
# -------------------------------------------------
df = vbt.YFData.download(
    "BTC-USD",
    start="2022-01-01",
    end="2023-12-31",
    interval="1h"
).get()
price = df["Close"]

# Signal produit par le moteur de consensus (exemple simplifié)
# Ici on utilise une EMA‑crossover comme placeholder
fast = price.ewm(span=12).mean()
slow = price.ewm(span=26).mean()
raw_signal = (fast > slow).astype(int) * 2 - 1   # 1 long, -1 short

# -------------------------------------------------
# 2. Application du filtre de volatilité
# -------------------------------------------------
atr = vbt.ATR.run(df["High"], df["Low"], df["Close"], window=14).atr
ema_atr = atr.ewm(span=14).mean()
vol_filter = atr < ema_atr  # le facteur multiplicatif a été retiré
signal = raw_signal * vol_filter.astype(int)

# -------------------------------------------------
# 3. Gestion du risque (Kelly + SL/TP)
# -------------------------------------------------
# Estimation des retours moyens et std sur le signal brut
returns = price.pct_change().shift(-1) * signal
mean_ret = returns.mean()
std_ret = returns.std()
kelly_f = max(0.0, min(1.0, mean_ret / (std_ret ** 2)))  # fraction du capital

# Paramètres SL/TP (les pourcentages ont été

---

## Module 5 — contenu

## Module 5 : Mise en production, observabilité avancée et gouvernance des modèles IA  

### 5.1. Déploiement continu des micro‑services IA  

| Étape | Action concrète | Outil / Artefact | Vérification |
|------|----------------|------------------|--------------|
| **Build** | Générer une image Docker *multi‑stage* contenant le code du service d’inférence et le modèle exporté (ONNX ou SavedModel). | `Dockerfile` avec `FROM python:3.11-slim` → `FROM nvidia/cuda:12.2.0-runtime-ubuntu22.04` | `docker build -t tradeoracle/inference:$(git rev-parse --short HEAD) .` → image de petite taille (sans dépendances de build). |
| **Scan** | Exécuter Trivy pour détecter les vulnérabilités CVE. | `trivy image tradeoracle/inference:tag` | Aucun CVE détecté dans le rapport. |
| **Push** | Publier l’image dans un registre privé (Harbor). | `docker push harbor.company.com/tradeoracle/inference:tag` | Tag présent dans le registre (`curl -s https://harbor.company.com/api/v2.0/projects/tradeoracle/repositories/inference/tags`). |
| **Helm release** | Déployer via Helm chart versionné (`Chart.yaml` `appVersion: tag`). | `helm upgrade --install inference ./charts/inference --set image.tag=tag --namespace prod` | `helm status inference -n prod` montre *deployed* et la révision affichée. |
| **Canary** | Créer un *Deployment* avec `strategy: RollingUpdate` et `maxSurge`, `maxUnavailable: 0`. Utiliser *Argo Rollouts* pour le canary. | `rollout.yaml` avec `steps:` → progression graduelle | `kubectl argo rollouts get rollout inference -n prod` indique le pourcentage actuel. |
| **Rollback** | En cas de dégradation du SLO, déclencher `kubectl argo rollouts undo`. | Policy `analysis: {}` | Le rollback se produit automatiquement si le taux d’erreur HTTP 5xx dépasse le seuil défini pendant une courte période. |

#### 5.1.1. Exemple de Dockerfile (multi‑stage, modèle ONNX)

```dockerfile
# ---------- Build stage ----------
FROM python:3.11-slim AS builder
WORKDIR /app
# Installation des dépendances de build uniquement
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ make && \
    pip install --upgrade pip && \
    pip install \
        onnxruntime==1.18.0 \
        numpy==1.26.4 \
        # autres dépendances de pré‑traitement
        && \
    apt-get purge -y --auto-remove gcc g++ make && \
    rm -rf /var/lib/apt/lists/*

# ---------- Runtime stage ----------
FROM python:3.11-slim
WORKDIR /app
# Copie du runtime minimal depuis le builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
# Ajout du modèle exporté (ONNX) et du code serveur
COPY model.onnx .
COPY inference_server.py .
# Variables d’environnement immuables
ENV PYTHONUNBUFFERED=1 \
    MODEL_PATH=/app/model.onnx
EXPOSE 8080
CMD ["python", "inference_server.py"]
```

*Vérifiable* : `docker run --rm -p 8080:8080 tradeoracle/inference:tag curl -s http://localhost:8080/health` renvoie `{"status":"ok"}`.

---

### 5.2. Observabilité avancée  

#### 5.2.1. Métriques personnalisées (Prometheus)  

```python
# inference_server.py (extrait)
from prometheus_client import Counter, Histogram, start_http_server

REQ_COUNT = Counter(
    "inference_requests_total",
    "Nombre total de requêtes d'inférence",
    ["model", "status"]
)
REQ_LATENCY = Histogram(
    "inference_request_latency_seconds",
    "Latence d'inférence",
    # les buckets sont définis par défaut
)
```