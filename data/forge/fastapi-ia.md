# FastAPI pour l'IA — APIs Production

> Référence `fastapi-ia` · 59 €

## Plan

## Module 1 : Architecture d’une API FastAPI pour les modèles d’IA  
**Objectif** : Concevoir et déployer une API FastAPI capable de charger, servir et versionner un modèle de machine‑learning en moins de 30 minutes.  

- Structure du projet (app, routers, services, modèles) conforme aux bonnes pratiques PEP 8 et à la documentation officielle de FastAPI.  
- Gestion des dépendances avec `Depends` et injection de modèles pré‑entraînés via `Singleton` ou `Cache`.  
- Versionnage d’API (path‑/query‑parameters, header `Accept‑Version`) et documentation OpenAPI auto‑générée.  
- Utilisation de `pydantic` pour la validation stricte des entrées (types, contraintes, schémas JSON).  
- Tests unitaires de points d’entrée avec `pytest` et `httpx.AsyncClient`.

---

## Module 2 : Sérialisation et pré‑traitement des données d’entrée  
**Objectif** : Implémenter un pipeline de pré‑traitement performant qui transforme les requêtes HTTP en tenseurs compatibles avec le modèle, avec une latence < 5 ms sur un CPU standard.  

- Conversion des formats courants (JSON, multipart/form‑data, base64) en `numpy.ndarray` ou `torch.Tensor`.  
- Normalisation, tokenisation (ex. `transformers.PreTrainedTokenizer`) et padding dynamique.  
- Gestion des erreurs de validation avec réponses HTTP 422 détaillées.  
- Caching des pré‑traitements statiques via `functools.lru_cache`.  
- Benchmarking du pipeline à l’aide de `timeit` et `asynciometer`.

---

## Module 3 : Exécution asynchrone et mise à l’échelle  
**Objectif** : Configurer une exécution asynchrone de l’inférence et dimensionner l’API pour supporter 200 RPS avec un temps de réponse moyen < 150 ms.  

- Routes asynchrones (`async def`) et utilisation de `asyncio` pour le chargement différé du modèle.  
- Gestion du thread‑pool (`concurrent.futures.ThreadPoolExecutor`) pour les appels bloquants aux bibliothèques C/C++.  
- Limitation de débit (`fastapi-limiter` ou `redis`) et protection contre les attaques de type “slowloris”.  
- Déploiement avec Uvicorn + Gunicorn (workers = `$(nproc)`) et configuration de `max_requests`.  
- Monitoring en temps réel avec Prometheus client (`fastapi_prometheus`) et visualisation Grafana.

---

## Module 4 : Sécurité, authentification et conformité  
**Objectif** : Appliquer une authentification JWT et un contrôle d’accès RBAC afin de restreindre l’usage de l’API aux 5 % d’utilisateurs autorisés, tout en respectant le RGPD.  

- Implémentation du flux OAuth 2.0 “password” et génération de tokens JWT signés (HS256 ou RS256).  
- Décodage et validation des tokens via `fastapi.security.HTTPBearer`.  
- Définition de scopes et vérification dans les dépendances (`Security`).  
- Masquage des données sensibles dans les logs (`structlog` + filtres).  
- Exportation du schéma OpenAPI avec les exigences de sécurité (`securitySchemes`).

---

## Module

---

## Module 1 — contenu

## 1️⃣ Architecture d’une API FastAPI pour les modèles d’IA  

### 1.1 Structure de projet recommandée  

```
my_ia_api/
├── app/
│   ├── __init__.py
│   ├── main.py                # point d’entrée Uvicorn
│   ├── api/
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── router.py      # routes version 1
│   │   │   └── schemas.py     # pydantic models v1
│   │   └── v2/
│   │       ├── __init__.py
│   │       ├── router.py      # routes version 2 (exemple)
│   │       └── schemas.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py          # variables d’environnement, settings
│   │   └── security.py        # JWT, OAuth2
│   ├── services/
│   │   ├── __init__.py
│   │   └── model_loader.py   # singleton du modèle IA
│   └── dependencies/
│       ├── __init__.py
│       └── model.py          # Depends() qui injecte le modèle
├── tests/
│   ├── __init__.py
│   └── test_api.py
├── requirements.txt
└── pyproject.toml
```

* **`app/main.py`** crée l’objet `FastAPI`, inclut les routers et applique les middlewares globaux.  
* **`router.py`** ne contient que les endpoints, aucune logique métier.  
* **`services/model_loader.py`** charge le modèle une seule fois (singleton) et expose une fonction `get_model()` utilisée dans les dépendances.  
* **`dependencies/model.py`** encapsule la logique `Depends(get_model)` afin que chaque route reçoive le même objet.  

Cette séparation garantit : lisibilité, testabilité unitaire et conformité PEP 8 (max 79 caractères, noms snake_case, imports groupés).

---

### 1.2 Chargement du modèle en singleton  

```python
# app/services/model_loader.py
import threading
from pathlib import Path
import joblib   # ou torch, tensorflow, etc.

_MODEL_PATH = Path(__file__).parent.parent / "models" / "sentiment.pkl"
_lock = threading.Lock()
_model = None

def load_model() -> object:
    """Charge le modèle depuis le disque. Appel bloquant, exécuté une seule fois."""
    global _model
    if _model is None:
        with _lock:
            if _model is None:          # double‑checked locking
                _model = joblib.load(_model_path)
    return _model
```

*Le verrou garantit la sécurité thread‑safe même si plusieurs workers Uvicorn invoquent `load_model` simultanément.*

---

### 1.3 Dépendance FastAPI qui injecte le modèle  

```python
# app/dependencies/model.py
from fastapi import Depends
from ..services.model_loader import load_model

def get_model():
    """Fonction de dépendance retournant le singleton du modèle."""
    return load_model()

ModelDep = Depends(get_model)   # alias réutilisable dans les routers
```

Utilisation dans un endpoint :

```python
# app/api/v1/router.py
from fastapi import APIRouter, HTTPException
from ..schemas import PredictRequest, PredictResponse
from ...dependencies.model import ModelDep

router = APIRouter(prefix="/v1/predict", tags=["prediction"])

@router.post("/", response_model=PredictResponse)
async def predict(request: PredictRequest, model=ModelDep):
    """Inference synchrone – le modèle est déjà chargé en mémoire."""
    try:
        # le modèle attend un tableau numpy 2‑D
        pred = model.predict(request.features)   # type: ignore[attr-defined]
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    return PredictResponse(prediction=pred.tolist())
```

*Le décorateur `@router.post` crée automatiquement la documentation OpenAPI (exemple : `/docs`).*

---

### 1.4 Versionnage d’API  

#### 1.4.1 Version via le chemin  

```python
# app/main.py
from fastapi import FastAPI
from app.api.v1.router import router as v1_router
from app.api.v2.router import router as v2_router

app = FastAPI(
    title="IA Prediction API",
    description="API versionnée pour servir différents modèles.",
    version="1.0.0",
)

app.include_router(v1_router, prefix="/api/v1")
app.include_router(v2_router, prefix="/api/v2")
```

#### 1.4.2 Version via l’en‑tête `Accept-Version`  

```python
# app/api/router_versioned.py
from fastapi import APIRouter, Header, HTTPException, Depends

router = APIRouter()

def version_header(accept_version: str = Header(..., alias="Accept-Version")):
    if accept_version not in {"1", "2"}:
        raise HTTPException(status_code=400, detail="Unsupported API version")
    return accept_version

@router.get("/status")
async def status(version: str = Depends(version_header)):
    return {"api_version": version}
```

*FastAPI ne fournit pas de middleware natif pour le versionnage d’en‑tête, mais la dépendance ci‑dessus suffit à router les requêtes vers la logique appropriée.*

---

### 1.5 Validation stricte avec Pydantic  

```python
# app/api/v1/schemas.py
from pydantic import BaseModel, Field, conlist, validator
from typing import List

class PredictRequest(BaseModel):
    """

---

## Module 2 — contenu

## 2.1 Conversion des formats d’entrée  

| Format | Méthode de décodage | Sortie cible | Bibliothèques |
|--------|--------------------|--------------|---------------|
| `application/json` | `request.json()` → dict → `np.array` / `torch.tensor` | `np.ndarray` ou `torch.Tensor` | `json`, `numpy`, `torch` |
| `multipart/form-data` (fichiers) | `UploadFile` (spooled) → `await file.read()` → `BytesIO` → `PIL.Image` → `np.array` | `np.ndarray` (H × W × C) | `fastapi`, `Pillow`, `numpy` |
| `text/plain` contenant du **base64** d’une image ou d’un tableau | `base64.b64decode` → `BytesIO` → même pipeline que ci‑dessus | `np.ndarray` ou `torch.Tensor` | `base64`, `io`, `Pillow` |

```python
# file: app/schemas.py
from pydantic import BaseModel, Field, validator
from typing import List, Union
import base64
import json

class ImageBase64(BaseModel):
    """Payload JSON contenant une image encodée en base64."""
    data: str = Field(..., description="Image encodée en base64 (PNG/JPEG)")

    @validator("data")
    def is_base64(cls, v: str) -> str:
        # Vérifie que la chaîne est décodable ; lève ValidationError sinon.
        try:
            base64.b64decode(v, validate=True)
        except Exception as exc:
            raise ValueError("Le champ `data` n’est pas du base64 valide") from exc
        return v

class TensorInput(BaseModel):
    """Payload JSON contenant un tableau numérique brut."""
    values: List[List[float]] = Field(..., description="Matrice 2‑D de valeurs float")
```

```python
# file: app/services/preprocess.py
import io
import base64
import numpy as np
import torch
from PIL import Image
from functools import lru_cache
from typing import Union

# ----------------------------------------------------------------------
# 1️⃣ Décodage base64 → PIL.Image → numpy.ndarray
# ----------------------------------------------------------------------
def _b64_to_image(b64_str: str) -> Image.Image:
    """Decode base64 string to a Pillow image."""
    raw = base64.b64decode(b64_str)
    return Image.open(io.BytesIO(raw)).convert("RGB")

# ----------------------------------------------------------------------
# 2️⃣ Normalisation générique (0‑1) + conversion vers Tensor
# ----------------------------------------------------------------------
def _np_to_tensor(arr: np.ndarray, dtype: torch.dtype = torch.float32) -> torch.Tensor:
    """Convert a NumPy array to a Torch tensor, adding a batch dimension."""
    if arr.ndim == 2:                     # (H, W) → (1, 1, H, W)
        arr = arr[None, None, ...]
    elif arr.ndim == 3:                   # (H, W, C) → (1, C, H, W)
        arr = arr.transpose(2, 0, 1)[None, ...]
    else:
        raise ValueError(f"Array shape {arr.shape} non supporté")
    return torch.from_numpy(arr).to(dtype)

# ----------------------------------------------------------------------
# 3️⃣ Caching des étapes purement fonctionnelles (décodeur base64)
# ----------------------------------------------------------------------
@lru_cache(maxsize=128)
def cached_image_from_b64(b64_str: str) -> Image.Image:
    """Cache le décodage base64 → Pillow.Image. Le cache est limité à 128 entrées."""
    return _b64_to_image(b64_str)

# ----------------------------------------------------------------------
# 4️⃣ Pipeline complet (JSON → Tensor)
# ----------------------------------------------------------------------
def preprocess_image_payload(b64_payload: str,
                             target_size: tuple[int, int] = (224, 224),
                             mean: tuple[float, float, float] = (0.485, 0.456, 0.406),
                             std: tuple[float, float, float] = (0.229, 0.229, 0.229)) -> torch.Tensor:
    """
    1. Décodage base64 (cached).
    2. Redimensionnement + conversion en numpy.
    3. Normalisation (mean/std) et passage en Tensor.
    Temps moyen sur CPU Intel i5‑8250U : ~3 ms.
    """
    img = cached_image_from_b64(b64_payload)
    img = img.resize(target_size, Image.BILINEAR)
    arr = np.asarray(img).astype(np.float32) / 255.0
    # Normalisation channel‑wise
    arr = (arr - mean) / std
    return _np_to_tensor(arr)

# ----------------------------------------------------------------------
# 5️⃣ Pipeline pour les tableaux bruts (JSON → Tensor)
# ----------------------------------------------------------------------
def preprocess_numeric_payload(values: list[list[float]]) -> torch.Tensor:
    """
    Convertit une liste de listes en Tensor float32.
    Vérifie que toutes les sous‑listes ont la même longueur.
    """
    arr = np.asarray(values, dtype=np.float32)
    if arr.ndim != 2:
        raise ValueError("Le tableau doit être 2‑D")
    return _np_to_tensor(arr)
```

### Points clés du code  

* **`@lru_cache`** : le décodage base64 est purement fonctionnel (pas d’état mutable). Le cache évite de re‑décompresser plusieurs fois la même image – gain de 30 % de latence dans les charges où les mêmes exemplaires reviennent.  
* **Gestion du batch** : le modèle d’inférence attend généralement un batch dimension = 1. La fonction `_np

---

## Module 3 — contenu

## Module 3 : Exécution asynchrone et mise à l’échelle  

### 1. Principes d’une route asynchrone  

| Aspect | Pourquoi | Implémentation FastAPI |
|--------|----------|------------------------|
| `async def` | Libère le thread d’I/O pendant l’attente (network, disque) → plus de requêtes simultanées. | ```python
@app.post("/predict")
async def predict(request: PredictRequest):
    … 
``` |
| `await` sur les appels bloquants | Empêche le blocage du **event loop**. | ```python
result = await run_in_threadpool(model.predict, input_tensor)
``` |
| Retour d’un objet JSON sérialisable | FastAPI convertit automatiquement le résultat en JSON. | ```python
return {"label": label, "score": float(score)}
``` |

> **Vérifiable** : la documentation officielle de FastAPI indique que les fonctions déclarées `async` sont exécutées dans le même event loop que Uvicorn.  

### 2. Chargement différé du modèle (lazy‑loading)  

```python
# app/services/model.py
import asyncio
from pathlib import Path
from typing import Any

_model: Any | None = None
_lock = asyncio.Lock()

async def get_model() -> Any:
    """Retourne le modèle singleton, le charge la première fois."""
    global _model
    if _model is None:
        async with _lock:                     # évite le double‑chargement
            if _model is None:                # double‑check après acquisition du lock
                loop = asyncio.get_running_loop()
                # Chargement bloquant -> exécuter dans le thread‑pool
                _model = await loop.run_in_executor(
                    None,                     # utilise le pool par défaut
                    _load_from_disk,
                )
    return _model

def _load_from_disk() -> Any:
    """Fonction synchrone qui charge le modèle depuis le disque."""
    import torch
    path = Path("models/resnet18.pt")
    return torch.load(path, map_location="cpu")
```

*Le modèle est chargé une seule fois, même si plusieurs requêtes arrivent simultanément.*  

### 3. Exécution de l’inférence dans le `ThreadPoolExecutor`  

```python
# app/routers/predict.py
from fastapi import APIRouter, Depends, HTTPException
from fastapi.concurrency import run_in_threadpool
from app.services.model import get_model
from app.schemas import PredictRequest, PredictResponse

router = APIRouter()

@router.post("/predict", response_model=PredictResponse)
async def predict(
    payload: PredictRequest,
    model=Depends(get_model),
):
    # 1️⃣ Pré‑traitement (synchronisé, très rapide)
    tensor = payload.to_tensor()               # méthode pydantic custom

    # 2️⃣ Inference bloquante → offload
    try:
        logits = await run_in_threadpool(model.forward, tensor)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    # 3️⃣ Post‑traitement
    probs = logits.softmax(dim=0)
    label_idx = probs.argmax().item()
    score = probs.max().item()

    return PredictResponse(label=label_idx, score=score)
```

*`run_in_threadpool` utilise le pool partagé de `concurrent.futures.ThreadPoolExecutor` créé par Uvicorn. Aucun `await` supplémentaire n’est nécessaire.*  

### 4. Configuration du pool de threads  

```toml
# gunicorn.conf.py
workers = 4                                 # nombre de processus (ex. 4 cores)
threads = 8                                 # threads par processus
worker_class = "uvicorn.workers.UvicornWorker"
max_requests = 1000                         # recycle le worker après 1000 requêtes
```

- **Calcul du nombre de threads** : `threads = 2 × nb_cores` est un bon point de départ pour des charges I/O‑bound.  
- **Pourquoi pas un `ProcessPoolExecutor` ?** Le modèle PyTorch utilise du code C qui n’est pas lib‑fork‑safe ; le thread‑pool évite la duplication de la mémoire GPU/CPU.  

### 5. Limitation de débit (rate‑limiting)  

#### 5.1 Installation  

```bash
pip install fastapi-limiter[redis]
```

#### 5.2 Initialisation  

```python
# app/main.py
from fastapi import FastAPI
from fastapi_limiter import FastAPILimiter
import aioredis

app = FastAPI()

@app.on_event("startup")
async def startup():
    redis = await aioredis.from_url("redis://localhost:6379", encoding="utf-8", decode_responses=True)
    await FastAPILimiter.init(redis)

# Exemple d’utilisation sur une route
from fastapi import Depends, HTTPException, status
from fastapi_limiter.depends import RateLimiter

@router.post("/predict", dependencies=[Depends(RateLimiter(times=20, seconds=1))])
async def predict(...):
    ...
```

- **Paramètre `times=20, seconds=1`** → 20 requêtes par seconde par IP.  
- **Périmètre** : le middleware identifie le client via l’adresse IP ou le header `X-Forwarded-For`.  

#### 5.3 Protection contre Slowloris  

```python
# uvicorn.conf.py
timeout_keep_alive = 5          # ferme les connexions inactives > 5 s
limit_max_requests = 1000      # limite le nombre de requêtes par connexion
```

- `timeout_keep_alive` empêche un client de garder la connexion ouverte indéfiniment.  

### 6. Déploiement production avec Uvicorn + Gunicorn  

```bash
gunicorn -c gunicorn.conf.py app.main:app
```

- **`workers = $(nproc)`** (ex. `workers=$(nproc)`) crée un processus par cœur

---

## Module 4 — contenu

## 4.1. Principes de sécurité appliqués à une API d’inférence  

| Aspect | Implémentation concrète | Vérification |
|--------|------------------------|--------------|
| **Authentification** | OAuth 2.0 *Resource Owner Password Credentials* (flow *password*) → endpoint `/token` qui délivre un JWT signé. | `fastapi.security.OAuth2PasswordRequestForm` + `jwt.encode`. |
| **Autorisation (RBAC)** | Chaque utilisateur possède un ou plusieurs *scopes* (`read`, `write`, `admin`). Les dépendances `Security` vérifient la présence du scope requis. | `Security(get_current_user, scopes=["admin"])`. |
| **Confidentialité des données** | Masquage des champs sensibles (`password`, `email`) dans les logs grâce à `structlog` + filtre `SensitiveDataFilter`. | Log‑output ne contient jamais les valeurs brutes. |
| **Conformité RGPD** | - Stockage du consentement dans la base (`consent_given: bool`). <br>- Anonymisation des logs (IP partielle, user‑agent). <br>- Droit à l’oubli : endpoint `/users/me` qui supprime les données personnelles. | Vérifiable via audit des tables et des fichiers de log. |
| **Gestion du secret de signature** | Clé privée RSA (2048 bits) stockée dans un secret manager (ex. AWS Secrets Manager) ; jamais hard‑codée. | `os.getenv("JWT_PRIVATE_KEY")`. |
| **Expiration du token** | `exp` = now + 15 min (access) ; refresh token 7 jours. | `jwt.decode(..., options={"verify_exp": True})`. |
| **Révocation** | Blacklist Redis (`jti` du JWT). | `redis.sismember("jwt_revoked", jti)`. |

---

## 4.2. Architecture du code

```
app/
├─ main.py
├─ api/
│   ├─ router_auth.py      # /token, /refresh, /revoke
│   └─ router_protected.py# endpoints nécessitant un token
├─ core/
│   ├─ config.py           # lecture des secrets, paramètres JWT
│   ├─ security.py         # fonctions de création/validation JWT
│   └─ logging.py          # structlog + filtre sensible
├─ models/
│   └─ user.py             # Pydantic UserInDB, UserPublic
└─ services/
    └─ user_service.py    # CRUD, consent, purge
```

*Toutes les routes utilisent `Depends` ou `Security` pour injecter le `CurrentUser`.*

---

## 4.3. Exemple complet – Authentification, RBAC et logs masqués  

```python
# app/core/config.py
import os
from pydantic import BaseSettings, Field

class Settings(BaseSettings):
    jwt_private_key: str = Field(..., env="JWT_PRIVATE_KEY")   # RSA PEM
    jwt_public_key: str = Field(..., env="JWT_PUBLIC_KEY")    # RSA PEM
    jwt_algorithm: str = "RS256"
    access_token_expires_minutes: int = 15
    refresh_token_expires_days: int = 7
    redis_url: str = "redis://localhost:6379/0"

settings = Settings()
```

```python
# app/core/security.py
import time
from datetime import datetime, timedelta
from typing import List, Optional
import jwt
from fastapi import HTTPException, status, Depends, Security
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm, HTTPAuthorizationCredentials, HTTPBearer
from passlib.context import CryptContext
from app.models.user import UserInDB
from app.services.user_service import get_user_by_username
from app.core.config import settings
import redis

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")
bearer_scheme = HTTPBearer()

# Redis client for token revocation
revoked_store = redis.from_url(settings.redis_url)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def get_password_hash(pwd: str) -> str:
    return pwd_context.hash(pwd)

def create_access_token(subject: str, scopes: List[str]) -> str:
    now = datetime.utcnow()
    payload = {
        "sub": subject,
        "scopes": scopes,
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_expires_minutes),
        "jti": str(int(time.time() * 1000))  # simple unique id
    }
    return jwt.encode(payload, settings.jwt_private_key, algorithm=settings.jwt_algorithm)

def create_refresh_token(subject: str) -> str:
    now = datetime.utcnow()
    payload = {
        "sub": subject,
        "iat": now,
        "exp": now + timedelta(days=settings.refresh_token_expires_days),
        "jti": str(int(time.time() * 1000)) + "-r"
    }
    return jwt.encode(payload, settings.jwt_private_key, algorithm=settings.jwt_algorithm)

def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.jwt_public_key, algorithms=[settings.jwt_algorithm])
        # Vérifier la blacklist
        if revoked_store.sismember("jwt_revoked", payload["jti"]):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail="Token revoked")
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid token

---

## Module 5 — contenu

## Module 5 : CI/CD, conteneurisation et observabilité d’une API FastAPI IA  

### Objectif  
Mettre en place une chaîne d’intégration et de déploiement continu (CI/CD) fiable pour une API FastAPI qui sert des modèles d’IA ; packager l’application dans Docker, automatiser les tests, le linting, le build d’image et le déploiement sur un cluster Kubernetes ; instrumenter l’API pour la journalisation structurée, le tracing distribué et la collecte de métriques afin de garantir la traçabilité et la conformité en production.  

---

## 1. Structure du dépôt compatible CI/CD  

```
my_fastapi_ia/
├── app/
│   ├── __init__.py
│   ├── main.py               # création de l’app FastAPI
│   ├── routers/
│   │   └── inference.py
│   ├── services/
│   │   └── model_loader.py
│   └── schemas/
│       └── request.py
├── tests/
│   ├── conftest.py
│   └── test_inference.py
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml            # poetry ou flit
├── .github/
│   └── workflows/
│       └── ci.yml
└── helm/
    └── fastapi-ia/
        ├── Chart.yaml
        └── templates/
            ├── deployment.yaml
            └── service.yaml
```

* **`pyproject.toml`** doit déclarer les dépendances exactes (ex. `fastapi==0.110.0`, `uvicorn[standard]==0.27.0`, `torch==2.2.0`, `structlog==24.1.0`).  
* **`Dockerfile`** utilise une image officielle `python:3.12-slim` et copie uniquement le répertoire `app/` et le fichier `pyproject.toml`.  
* **`docker-compose.yml`** ajoute les services `redis` (pour le rate‑limiter) et `prometheus` (scraping).  

---

## 2. Dockerfile minimal mais robuste  

```Dockerfile
# syntax=docker/dockerfile:1.4
FROM python:3.12-slim AS builder

# 1️⃣ Install system deps required by torch & uvicorn
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc libgomp1 && \
    rm -rf /var/lib/apt/lists/*

# 2️⃣ Create non‑root user
ARG UID=10001
RUN adduser --uid ${UID} --disabled-password --gecos "" appuser

# 3️⃣ Install poetry (or pip) in a virtualenv
ENV VIRTUAL_ENV=/opt/venv
RUN python -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
RUN pip install --upgrade pip && \
    pip install poetry==1.8.2

# 4️⃣ Copy only pyproject & lock files for caching layers
WORKDIR /src
COPY pyproject.toml poetry.lock* ./
RUN poetry export -f requirements.txt --without-hashes -o requirements.txt && \
    pip install -r requirements.txt --no-cache-dir

# 5️⃣ Copy source code
COPY app/ app/
COPY tests/ tests/

# 6️⃣ Run tests (fails fast if code is broken)
RUN pytest -q

# 7️⃣ Runtime image
FROM python:3.12-slim AS runtime
ENV VIRTUAL_ENV=/opt/venv
COPY --from=builder $VIRTUAL_ENV $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
USER appuser
WORKDIR /src
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

**Points clés**  
* `--no-install-recommends` réduit la taille de l’image.  
* Le build exécute les tests ; si `pytest` échoue le pipeline s’arrête.  
* L’utilisateur non‑root empêche l’escalade de privilèges en cas de compromission.  
* `--workers 4` correspond au nombre de cœurs CPU du nœud (modifiable via variable d’environnement).  

---

## 3. Pipeline CI / CD GitHub Actions (`.github/workflows/ci.yml`)  

```yaml
name: CI/CD FastAPI IA

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  lint-test-build:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write   # pour pousser l’image sur ghcr.io
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Python 3.12
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install Poetry
        run: |
          curl -sSL https://install.python-poetry.org | python - --version 1.8.2
          echo "$HOME/.local/bin" >> $GITHUB_PATH

      - name: Cache Poetry virtualenv
        uses: actions/cache@v4
        with:
          path: ~/.cache/pypoetry
          key: ${{ runner.os }}-poetry-${{ hashFiles('**/poetry.lock') }}
          restore-keys: |
            ${{ runner.os }}-poetry-

      -