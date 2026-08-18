# FastAPI pour l'IA — APIs Production

> Référence `fastapi-ia` · 59 €

## Plan

## Module 1 : Architecture d’une API FastAPI pour les modèles d’IA  
**Objectif** : Concevoir et déployer une API FastAPI capable de charger, servir et versionner un modèle de machine‑learning dans un délai raisonnable.  

- Structure du projet (app, routers, services, modèles) conforme aux bonnes pratiques PEP 8 et à la documentation officielle de FastAPI.  
- Gestion des dépendances avec `Depends` et injection de modèles pré‑entraînés via `Singleton` ou `Cache`.  
- Versionnage d’API (path‑/query‑parameters, header `Accept‑Version`) et documentation OpenAPI auto‑générée.  
- Utilisation de `pydantic` pour la validation stricte des entrées (types, contraintes, schémas JSON).  
- Tests unitaires de points d’entrée avec `pytest` et `httpx.AsyncClient`.

---

## Module 2 : Sérialisation et pré‑traitement des données d’entrée  
**Objectif** : Implémenter un pipeline de pré‑traitement performant qui transforme les requêtes HTTP en tenseurs compatibles avec le modèle, avec une latence très faible sur un CPU standard.  

- Conversion des formats courants (JSON, multipart/form‑data, base64) en `numpy.ndarray` ou `torch.Tensor`.  
- Normalisation, tokenisation (ex. `transformers.PreTrainedTokenizer`) et padding dynamique.  
- Gestion des erreurs de validation avec réponses HTTP 422 détaillées.  
- Caching des pré‑traitements statiques via `functools.lru_cache`.  
- Benchmarking du pipeline à l’aide de `timeit` et `asynciometer`.

---

## Module 3 : Exécution asynchrone et mise à l’échelle  
**Objectif** : Configurer une exécution asynchrone de l’inférence et dimensionner l’API pour supporter un trafic élevé avec un temps de réponse moyen acceptable.  

- Routes asynchrones (`async def`) et utilisation de `asyncio` pour le chargement différé du modèle.  
- Gestion du thread‑pool (`concurrent.futures.ThreadPoolExecutor`) pour les appels bloquants aux bibliothèques C/C++.  
- Limitation de débit (`fastapi-limiter` ou `redis`) et protection contre les attaques de type “slowloris”.  
- Déploiement avec Uvicorn + Gunicorn (workers = `$(nproc)`) et configuration de `max_requests`.  
- Monitoring en temps réel avec Prometheus client (`fastapi_prometheus`) et visualisation Grafana.

---

## Module 4 : Sécurité, authentification et conformité  
**Objectif** : Appliquer une authentification JWT et un contrôle d’accès RBAC afin de restreindre l’usage de l’API aux utilisateurs autorisés, tout en respectant le RGPD.  

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
```

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
# 1️⃣ Décodage base64 → Pillow.Image → numpy.ndarray
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
    """Cache le décodage base64 → Pillow.Image."""
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

* **`@lru_cache`** : le décodage base64 est purement fonctionnel (pas d’état mutable). Le cache évite de re‑décompresser plusieurs fois la même image, ce qui améliore la latence dans les charges où les mêmes exemplaires reviennent.  
* **Gestion du batch** : le modèle d’inférence attend généralement un batch dimension = 1. La fonction `_np_to_tensor` ajoute cette dimension automatiquement.  

---

## Module 3 — contenu

## Module 3 : Exécution asynchrone et mise à l’échelle  

### 1. Principes d’une route asynchr