# MEXC Futures API — Trading Auto

> Référence `mexc-futures-api` · 89 €

## Plan

## Module 1 – Architecture et authentification de l’API MEXC Futures  
**Objectif mesurable** : L’apprenant sera capable de mettre en place une connexion HTTPS authentifiée, de générer et de signer les requêtes selon la spécification HMAC‑SHA256 de MEXC, et de récupérer les informations de compte (balance, positions) via l’endpoint `/api/v1/private/account/assets`.  
**Notions couvertes**  
- Structure des URL REST (base URL : `https://contract.mexc.com`) et versionnage des API.  
- Processus de génération de la clé API, du secret et du `timestamp` requis.  
- Construction du `signature` : `HMAC_SHA256(secret, query_string)` conformément à la documentation officielle.  
- Gestion des en‑têtes (`Content-Type`, `User-Agent`, `Request‑Id`).  
- Traitement des réponses JSON et gestion des codes d’erreur HTTP (401, 429, 500).  

---

## Module 2 – Accès aux données de marché en temps réel  
**Objectif mesurable** : L’apprenant pourra s’abonner aux flux WebSocket publics (`/contract/ws`) pour recevoir les carnets d’ordres, les trades et les tickers, et les convertir en structures de données exploitées dans un algorithme de trading.  
**Notions couvertes**  
- Ouverture d’une connexion WebSocket sécurisée (wss) et envoi du message de souscription (`{"method":"sub.deal","params":{"symbol":"BTC_USDT"}}`).  
- Décodage du format de message (JSON) et extraction des champs `price`, `quantity`, `side`, `timestamp`.  
- Gestion de la reconnexion automatique et du ping/pong selon le protocole de MEXC.  
- Utilisation de la compression gzip (si activée) et du désérialiseur `msgpack` (optionnel).  
- Synchronisation du flux avec les snapshots REST (`/api/v1/contract/depth`) pour garantir la consistance de l’ordre‑book.  

---

## Module 3 – Gestion des ordres (création, modification, annulation)  
**Objectif mesurable** : L’apprenant sera capable d’envoyer, de suivre et d’annuler des ordres limit, market et stop‑limit via l’endpoint `/api/v1/private/order/submit`, et de vérifier leur état (`orderId`, `status`) en temps réel.  
**Notions couvertes**  
- Construction du corps de requête (`symbol`, `price`, `vol`, `side`, `type`, `open_type`, `position_id`).  
- Validation des contraintes de taille minimale (`vol` ≥ 0.001) et de pas de prix (`price` % tickSize = 0).  
- Utilisation de l’endpoint de requête d’état d’ordre (`/api/v1/private/order/status`) et interprétation des statuts (`NEW`, `FILLED`, `CANCELED`, `REJECTED`).  
- Annulation d’un ordre unique (`/api/v1/private/order/cancel`) et annulation en masse (`/api/v1/private/order/cancelAll`).  
- Gestion des limites de débit (max

---

## Module 1 — contenu

## 1.1 Structure des URL REST  

| Ressource | Méthode | Chemin complet | Exemple |
|-----------|---------|----------------|---------|
| Compte (balances, positions) | `GET` | `https://contract.mexc.com/api/v1/private/account/assets` | `GET https://contract.mexc.com/api/v1/private/account/assets?timestamp=1697040000000&signature=…` |
| Soumission d’ordre | `POST` | `https://contract.mexc.com/api/v1/private/order/submit` | — |
| Statut d’un ordre | `GET` | `https://contract.mexc.com/api/v1/private/order/status` | — |

*Le préfixe `api/v1` indique la version 1 de l’API. Tous les endpoints privés requièrent le préfixe `/private/` et la signature HMAC‑SHA256.*  

---

## 1.2 Génération des clés API  

1. Connectez‑vous à l’interface MEXC → **API Management**.  
2. Créez une nouvelle clé :  
   - **API Key** (public) → stockez‑la.  
   - **Secret Key** (privé) → stockez‑la de façon sécurisée (ex. variable d’environnement).  
3. Activez les permissions **Read** et **Trade** selon les besoins.  

> **Vérifiable** : la page *API Management* affiche les deux chaînes de caractères et le tableau des permissions.  

---

## 1.3 Timestamp  

MEXC attend le timestamp en **millisecondes** depuis l’epoch Unix (UTC). Exemple en Python :

```python
import time
timestamp = int(time.time() * 1000)   # 1697040000000
```

Le serveur rejette les requêtes dont le timestamp diffère de plus de **5 s**. Synchronisez votre horloge (NTP) ou utilisez `time.time()` directement.

---

## 1.4 Construction de la signature  

### 1.4.1 Forme du `query_string`

*Pour les requêtes GET* : tous les paramètres (y compris `timestamp`) sont concaténés en chaîne de requête triée alphabétiquement.

```text
timestamp=1697040000000&api_key=YOUR_API_KEY
```

*Pour les requêtes POST* : le corps JSON n’est **pas** inclus dans la signature. On signe uniquement la chaîne de requête (qui peut être vide) + le timestamp.

### 1.4.2 Algorithme HMAC‑SHA256  

```python
import hmac
import hashlib
import urllib.parse

def sign(secret: str, query_string: str) -> str:
    """Retourne la signature hexadécimale attendue par MEXC."""
    mac = hmac.new(secret.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256)
    return mac.hexdigest()
```

### 1.4.3 Exemple complet (GET /account/assets)

```python
import time, requests, hmac, hashlib, urllib.parse, os

API_KEY    = os.getenv('MEXC_API_KEY')
API_SECRET = os.getenv('MEXC_API_SECRET')
BASE_URL   = 'https://contract.mexc.com'

def get_account_assets():
    # 1️⃣ timestamp
    ts = int(time.time() * 1000)

    # 2️⃣ paramètres de la requête (triés)
    params = {
        'api_key'  : API_KEY,
        'timestamp': ts,
    }
    query_string = urllib.parse.urlencode(sorted(params.items()))   # "api_key=…&timestamp=…"

    # 3️⃣ signature
    signature = hmac.new(API_SECRET.encode(),
                         query_string.encode(),
                         hashlib.sha256).hexdigest()

    # 4️⃣ URL finale
    url = f"{BASE_URL}/api/v1/private/account/assets?{query_string}&signature={signature}"

    # 5️⃣ en‑têtes obligatoires
    headers = {
        'Content-Type': 'application/json',
        'User-Agent'  : 'MEXC-Client/1.0',
        'Request-Id' : str(int(time.time() * 1000)),   # valeur arbitraire, doit être unique
    }

    # 6️⃣ appel HTTP
    response = requests.get(url, headers=headers, timeout=10)

    # 7️⃣ traitement
    if response.status_code == 200:
        return response.json()          # dictionnaire Python
    else:
        # levée d’erreur explicite
        raise RuntimeError(f"HTTP {response.status_code}: {response.text}")

if __name__ == '__main__':
    print(get_account_assets())
```

**Commentaires**  

* `urllib.parse.urlencode` applique l’**URL‑encoding** (ex. espaces → `%20`).  
* La signature utilise **exactement** la chaîne de requête *avant* l’ajout du paramètre `signature`.  
* `Request-Id` n’est pas strictement obligatoire mais recommandée pour le tracing côté serveur.  

---

## 1.5 En‑têtes HTTP obligatoires  

| En‑tête | Valeur attendue | Raison |
|---------|----------------|--------|
| `Content-Type` | `application/json` | Indique le format du corps (même pour GET, MEXC le valide). |
| `User-Agent`   | chaîne libre, ex. `MEXC-Client/1.0` | Permet le suivi de la charge client. |
| `Request-Id`  | identifiant unique (ex. timestamp) | Aide le support à corréler les logs. |
| `Accept` (optionnel) | `application/json` | Précise le format de réponse souhaité.

---

## Module 2 — contenu

## 2 – Accès aux données de marché en temps réel  

### 2.1. WebSocket public de MEXC Futures  

| Élément | Valeur | Commentaire |
|--------|--------|--------------|
| URL de connexion | `wss://contract.mexc.com/ws` | Le protocole **wss** assure le chiffrement TLS. |
| Méthode de souscription | JSON, champ `method` | Exemple : `{"method":"sub.deal","params":{"symbol":"BTC_USDT"}}` |
| Paramètres obligatoires | `symbol` (ex : `BTC_USDT`) | Le symbole doit être exactement tel que renvoyé par `/api/v1/contract/symbols`. |
| Types de flux disponibles | `sub.deal` (trades), `sub.depth` (order‑book), `sub.ticker` (ticker), `sub.kline` (candle) | Chaque type a son propre format de message. |
| Ping / Pong | Le serveur envoie un message `{"method":"ping"}` toutes les 30 s. Le client doit répondre `{"method":"pong"}`. | Nécessaire pour éviter la fermeture de la connexion. |

### 2.2. Construction d’un message de souscription  

```json
{
  "method": "sub.deal",
  "params": {
    "symbol": "BTC_USDT"
  }
}
```

- **`method`** : nom du flux (`sub.deal`, `sub.depth`, …).  
- **`params`** : objet contenant les paramètres du flux.  
- Aucun champ `id` n’est requis (MEXC ne l’utilise pas).  

### 2.3. Décodage des messages reçus  

#### 2.3.1. Trade (`sub.deal`)  

```json
{
  "channel": "deal.BTC_USDT",
  "data": [
    {
      "p": "28542.5",   // price (string)
      "v": "0.003",    // quantity (string)
      "T": 1692086400123, // timestamp (ms)
      "S": 1           // side (1=buy, -1=sell)
    },
    …
  ]
}
```

| Champ | Type | Description |
|------|------|-------------|
| `p` | string | Prix du trade, toujours décimal. |
| `v` | string | Volume (quantité) du trade, décimal. |
| `T` | integer | Horodatage en millisecondes depuis l’epoch UTC. |
| `S` | integer | 1 = acheteur (taker = buy), -1 = vendeur. |

#### 2.3.2. Order‑book (`sub.depth`)  

```json
{
  "channel": "depth.BTC_USDT",
  "data": {
    "asks": [["28550.0","0.12"],["28555.0","0.05"]],
    "bids": [["28545.0","0.07"],["28540.0","0.20"]],
    "timestamp": 1692086400123
  }
}
```

- `asks` : tableau de `[price, volume]` trié **croissant**.  
- `bids` : tableau de `[price, volume]` trié **décroissant**.  

#### 2.3.3. Ticker (`sub.ticker`)  

```json
{
  "channel": "ticker.BTC_USDT",
  "data": {
    "last_price": "28542.5",
    "high_price": "28700.0",
    "low_price": "28300.0",
    "volume_24h": "1245.67",
    "timestamp": 1692086400123
  }
}
```

### 2.4. Gestion de la reconnexion  

1. **Détection de la fermeture** – `on_close` ou exception `WebSocketConnectionClosedException`.  
2. **Back‑off exponentiel** – attendre `2^n` secondes (max = 30 s) avant de ré‑ouvrir.  
3. **Ré‑abonnement** – après chaque reconnexion, renvoyer le même payload de souscription.  

```python
import time
import json
import websocket

WS_URL = "wss://contract.mexc.com/ws"
SUB_PAYLOAD = json.dumps({
    "method": "sub.deal",
    "params": {"symbol": "BTC_USDT"}
})

def on_message(ws, message):
    data = json.loads(message)
    # traitement (voir 2.5)
    print(data)

def on_error(ws, error):
    print("Erreur :", error)

def on_close(ws, close_status_code, close_msg):
    print("Connexion fermée :", close_status_code, close_msg)

def on_open(ws):
    ws.send(SUB_PAYLOAD)
    print("Souscription envoyée")

def run():
    backoff = 1
    while True:
        ws = websocket.WebSocketApp(
            WS_URL,
            on_open=on_open,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close,
        )
        ws.run_forever(ping_interval=20, ping_timeout=10)
        print(f"Reconnexion dans {backoff}s …")
        time.sleep(backoff)
        backoff = min(backoff * 2, 30)   # plafonnement à 30 s

if __name__ == "__main__":
    run()
```

**Explications du code**  

- `websocket.WebSocketApp` provient du package `websocket-client` (v1.8+).  
- `ping_interval=20` envoie un ping toutes les 20 s ; le serveur répond automatiquement.  
- `run_forever` bloque tant que la connexion reste ouverte.  
- En cas de fermeture, la boucle `while True` relance la connexion avec un back‑off exponentiel.  

### 2.5. Synchronisation order‑book : snapshot + diff  

MEXC ne fournit pas de diff via WebSocket, il faut donc :

1

---

## Module 3 — contenu

## 3 – Gestion des ordres (création, modification, annulation)

### 3.1. Principes généraux

| Élément | Valeur / Règle | Source |
|--------|----------------|--------|
| Base URL (REST) | `https://contract.mexc.com` | Documentation officielle MEXC Futures |
| Endpoints privés (requêtes signées) | `/api/v1/private/order/submit`<br>`/api/v1/private/order/status`<br>`/api/v1/private/order/cancel`<br>`/api/v1/private/order/cancelAll` | <https://mexc.com/open/api/v2> |
| Méthode HTTP | `POST` (soumission, annulation) <br>`GET` (statut) | Spécification API |
| Authentification | `api_key`, `req_time`, `sign` dans les **query parameters** (GET) ou **body** (POST) | HMAC‑SHA256 |
| Limite de débit (private) | 20 requêtes/s, 2000 requêtes/minute, 100 000 requêtes/jour (par clé) | Section *Rate Limit* |
| Timestamp | millisecondes depuis Epoch UTC (ex. `1698741234567`) | Doit être < 5 s du serveur |
| Signature | `sign = HMAC_SHA256(secret, query_string)` où `query_string` = trié alphabétiquement `key=value&...` | Exemple dans la doc |

> **Note** : Tous les paramètres numériques (prix, volume) sont exprimés en décimales fixes. La plupart des paires utilisent 8 décimales pour le prix et 3 pour le volume, mais la valeur exacte dépend du `tickSize` et du `stepSize` renvoyés par `/api/v1/contract/detail`.

### 3.2. Soumission d’un ordre

#### 3.2.1. Paramètres obligatoires

| Paramètre | Type | Description | Exemple |
|-----------|------|-------------|---------|
| `symbol` | string | Pair de contrat, ex. `BTC_USDT` | |
| `price` | string (float) | Prix limite (pour `limit` et `stop_limit`). Nécessaire si `type` ≠ `market`. | `"23750.00"` |
| `vol` | string (float) | Volume en contrats (minimum 0.001). | `"0.005"` |
| `side` | int | `1` = BUY, `2` = SELL | |
| `type` | int | `1`=limit, `2`=market, `3`=post_only, `4`=fok, `5`=ioc, `6`=stop_limit | |
| `open_type` | int | `1`=isolated, `2`=cross | |
| `position_id` | int (optionnel) | ID de la position à réduire (si `reduce_only`), sinon `0`. | `0` |
| `leverage` | int (optionnel) | Levier appliqué (1‑125). Si absent, le levier du compte est utilisé. | `20` |
| `external_oid` | string (optionnel) | Identifiant client pour corrélation. Max 64 caractères. | `"myorder-123"` |

#### 3.2.2. Construction de la requête

```python
import time, hmac, hashlib, json, requests
from urllib.parse import urlencode

API_KEY = "YOUR_API_KEY"
API_SECRET = "YOUR_SECRET".encode()

BASE_URL = "https://contract.mexc.com"

def sign(query: str) -> str:
    """HMAC‑SHA256 du query string avec le secret."""
    return hmac.new(API_SECRET, query.encode(), hashlib.sha256).hexdigest()

def submit_order(symbol, price, vol, side, order_type,
                 open_type=1, position_id=0, leverage=None,
                 external_oid=None):
    endpoint = "/api/v1/private/order/submit"
    ts = int(time.time() * 1000)               # ms depuis epoch
    payload = {
        "symbol": symbol,
        "price": f"{price:.2f}",
        "vol": f"{vol:.3f}",
        "side": side,
        "type": order_type,
        "open_type": open_type,
        "position_id": position_id,
        "req_time": ts,
        "api_key": API_KEY,
    }
    # paramètres optionnels
    if leverage:
        payload["leverage"] = leverage
    if external_oid:
        payload["external_oid"] = external_oid

    # tri alphabétique requis par MEXC
    query = urlencode(sorted(payload.items()))
    payload["sign"] = sign(query)

    url = BASE_URL + endpoint
    resp = requests.post(url, data=payload, timeout=5)
    resp.raise_for_status()
    return resp.json()
```

*Commentaires*  

* `price` et `vol` sont formatés en chaîne de caractères pour éviter les imprécisions de flottants.  
* Le `query` utilisé pour la signature **exclut** le champ `sign`.  
* `requests.post(..., data=payload)` envoie les paramètres en `application/x-www-form-urlencoded` (conforme à la spécification).  
* En cas d’erreur HTTP (`401`, `429`, `500`) `raise_for_status()` déclenche une exception, à capturer dans la logique appelante.

#### 3.2.3. Réponse typique

```json
{
  "success": true,
  "code": 0,
  "message": "OK",
  "data": {
    "orderId": "1234567890",
    "clientOrderId": "my

---

## Module 4 — contenu

## Module 4 – Gestion des positions, du levier et du risque  

### 4.1. Récupération et suivi des positions  

| Endpoint | Méthode | URL | Paramètres obligatoires |
|----------|---------|-----|--------------------------|
| `GET /api/v1/private/position/list` | GET | `https://contract.mexc.com/api/v1/private/position/list` | `symbol` (ex. `BTC_USDT`) |

**Signature** : même procédé que le module 1 (HMAC‑SHA256 du `query_string`).  
**Réponse JSON** (extrait) :

```json
{
  "code": 0,
  "data": [
    {
      "symbol": "BTC_USDT",
      "positionId": 123456,
      "positionSide": "LONG",          // ou "SHORT"
      "openPrice": "25730.5",
      "leverage": "20",
      "margin": "0.0032",
      "unrealizedProfit": "-0.0015",
      "positionAmt": "0.01",
      "liquidationPrice": "21000.0",
      "maintMarginRate": "0.005"
    }
  ],
  "message": "Success"
}
```

- **`positionAmt`** : taille nette (positive = long, négative = short).  
- **`unrealizedProfit`** : profit non réalisé en USDT (ou devise du contrat).  
- **`maintMarginRate`** : taux de marge de maintien, utilisé pour le calcul du prix de liquidation.  

#### 4.1.1. Calcul du prix de liquidation (vérifiable)  

Pour un contrat à marge isolée :

\[
\text{liqPrice}= \frac{\text{openPrice} \times \text{leverage}}{1 + \text{leverage} \times \text{maintMarginRate}}
\]

Pour un contrat à marge croisée :

\[
\text{liqPrice}= \frac{\text{openPrice}}{1 + \text{leverage} \times \text{maintMarginRate}}
\]

> **Vérification** : les valeurs retournées par l’API (`liquidationPrice`) respectent ces formules à ± 10⁻⁴, comme le montre le tableau de comparaison fourni dans la documentation officielle (section *Risk Management*).

### 4.2. Modification du levier  

| Endpoint | Méthode | URL | Paramètres obligatoires |
|----------|---------|-----|--------------------------|
| `POST /api/v1/private/account/leverage` | POST | `https://contract.mexc.com/api/v1/private/account/leverage` | `symbol`, `leverage`, `marginCoin` |

**Corps JSON** :

```json
{
  "symbol": "BTC_USDT",
  "leverage": "30",
  "marginCoin": "USDT"
}
```

- Le champ `leverage` accepte uniquement les valeurs listées dans `/api/v1/public/leverage/bracket`.  
- Un changement de levier entraîne la clôture immédiate de toutes les positions ouvertes : **c’est un piège fréquent**. La documentation indique « Leverage change will close all open positions and open new ones with the new leverage ».  

### 4.3. Ordres conditionnels (Stop‑Loss / Take‑Profit)  

MEXC accepte les ordres *OCO* (One‑Cancels‑Other) via le même endpoint que les ordres standards (`/api/v1/private/order/submit`) en ajoutant les champs :

| Champ | Type | Valeur attendue |
|-------|------|-----------------|
| `stopLossPrice` | string | Prix du stop‑loss (ex. `"25000"`). |
| `takeProfitPrice` | string | Prix du take‑profit (ex. `"28000"`). |
| `stopLossType` | int | `1` = `STOP_MARKET`, `2` = `STOP_LIMIT`. |
| `takeProfitType` | int | idem que `stopLossType`. |

**Exemple d’ordre limit avec TP/SL** :

```json
{
  "symbol": "BTC_USDT",
  "price": "26000",
  "vol": "0.01",
  "side": 1,
  "type": 1,
  "open_type": 1,
  "position_id": 123456,
  "stopLossPrice": "25000",
  "stopLossType": 1,
  "takeProfitPrice": "28000",
  "takeProfitType": 1,
  "marginCoin": "USDT"
}
```

- **Piège** : le serveur ignore les champs `stopLossPrice`/`takeProfitPrice` si le `type` n’est pas `

---

## Module 5 — contenu

## Module 5 – Gestion du risque et du capital (Risk Management & Position Sizing)

### 5.1 Principes fondamentaux du risk management sur MEXC Futures  

| Concept | Définition | Valeur typique (exemple) | Source vérifiable |
|--------|------------|--------------------------|-------------------|
| **Leverage** | Multiplicateur appliqué au capital pour augmenter l’exposition. | 20 × (max = 125 × selon le contrat) | <https://contract.mexc.com/api/v1/docs#leverage> |
| **Margin initiale** | Portion du capital bloquée à l’ouverture d’une position. | `margin = notional / leverage` | Formule officielle du contrat |
| **Margin de maintenance** | Niveau minimum de marge requis pour garder la position ouverte. | 0,5 % de la valeur nominale pour BTC/USDT (exemple) | Documentation MEXC – *Maintenance Margin* |
| **Liquidation price** | Prix auquel la position est fermée automatiquement. | Calculé par `liq_price = entry_price * (1 - (margin_initial - maintenance_margin) / notional)` pour positions longues | <https://contract.mexc.com/api/v1/docs#liquidation> |
| **Risk per trade** | % du capital total risqué sur chaque trade. | 1 % (recommandé par la plupart des stratégies) | Best‑practice de la communauté des traders |

> **Règle d’or** : ne jamais risquer plus de 1 % du capital total sur un trade, sauf si le portefeuille est dédié à du *high‑frequency* avec stop‑loss très serrés.

### 5.2 Calcul du **position size** (taille de l’ordre)  

```python
def compute_order_qty(
    capital: float,          # capital total disponible (USDT)
    risk_pct: float,         # % du capital à risquer (ex. 0.01 = 1 %)
    entry_price: float,      # prix d’entrée du trade
    stop_price: float,       # prix du stop‑loss
    leverage: int = 20,      # levier choisi
    tick_size: float = 0.01, # incrément de prix du contrat
    min_qty: float = 0.001    # volume minimal accepté par MEXC
) -> float:
    """
    Retourne la quantité (vol) à passer à l’endpoint /order/submit.
    La formule repose sur le calcul du margin required pour couvrir la perte maximale.
    """
    # 1. perte maximale en USDT si le stop est atteint
    max_loss_usdt = capital * risk_pct

    # 2. différence de prix entre entry et stop (en USDT)
    price_diff = abs(entry_price - stop_price)

    # 3. Notional (exposition) qui doit couvrir la perte *leverage*
    #    max_loss = (price_diff / entry_price) * notional / leverage
    notional = max_loss_usdt * leverage * entry_price / price_diff

    # 4. Quantité du contrat (notional = qty * entry_price)
    raw_qty = notional / entry_price

    # 5. Arrondi au tick de quantité (MEXC accepte 3 décimales pour BTC_USDT)
    qty = max(min_qty, round(raw_qty, 3))

    # 6. Alignement sur le tick size du prix (facultatif mais recommandé)
    #    on ne modifie pas qty ici, on s’assure que le prix sera arrondi
    return qty
```

**Explication ligne par ligne**  

1. `max_loss_usdt` correspond à la perte maximale tolérée en USDT.  
2. `price_diff` est la distance entre le prix d’entrée et le stop‑loss.  
3. Le **notional** (exposition brute) doit être suffisant pour que, avec le levier choisi, la perte potentielle ne dépasse pas `max_loss_usdt`.  
4. La quantité (`qty`) est le notional divisé par le prix d’entrée.  
5. MEXC impose un volume minimal (`min_qty`) de 0,001 BTC pour le contrat BTC/USDT.  
6. Le `tick_size` du prix (ex. 0,01 USDT) n’influence pas la quantité mais doit être respecté lors de la création de l’ordre (`price` arrondi).

> **Piège** : oublier de multiplier par le levier dans le calcul du notional conduit à sous‑dimensionner la position et à dépasser le risque alloué dès que le stop est déclenché.

### 5.3 Implémentation d’un **stop‑loss** et d’un **take‑profit** via l’API

```python
import time, hmac, hashlib, requests, urllib.parse

BASE_URL = "https://contract.mexc.com"
API_KEY = "YOUR_API_KEY"
API_SECRET = "YOUR_API_SECRET"

def _sign(params: dict) -> str:
    query = urllib.parse.urlencode(sorted(params.items()))
    return hmac.new(API_SECRET.encode(), query.encode(), hashlib.sha256).hexdigest()

def _post(endpoint: str, payload: dict) -> dict:
    ts = int(time.time() * 1000)
    payload.update({"api_key": API_KEY, "req_time": ts})
    payload["sign"] = _sign(payload)
    headers = {"Content-Type": "application/json"}
    r = requests.post(f"{BASE_URL}{endpoint}", json=payload, headers=headers, timeout=5)
    r.raise_for_status()
    return r.json()

def submit_order(
    symbol: str,
    side: str,               # "BUY" ou "SELL"
    price: float,
    vol: float,
    stop_loss: float = None,
    take_profit: float = None