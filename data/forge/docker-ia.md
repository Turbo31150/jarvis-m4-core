# Docker pour l'IA

> Référence `docker-ia` · 49 €

## Plan

## Module 1 : Installation et configuration de Docker pour les projets IA  
**Objectif mesurable** : L’apprenant installe Docker Engine et Docker Compose sur Ubuntu 22.04 LTS, Windows 10 Pro et macOS 13, puis configure le daemon pour l’accès aux GPU via NVIDIA Container Toolkit.  
**Notions couvertes**  
- Installation de Docker CE (packages `apt`, `yum`, `brew`) et vérification (`docker version`, `docker info`).  
- Installation de Docker Compose v2 (plugin CLI) et validation (`docker compose version`).  
- Configuration du daemon (`/etc/docker/daemon.json`) pour le support du runtime `nvidia`.  
- Installation de NVIDIA Container Toolkit 2.x et test avec `docker run --gpus all nvidia/cuda:12.2-base nvidia-smi`.  
- Gestion des permissions utilisateur (`docker` group) et résolution des problèmes courants (cgroup v2, SELinux).

---

## Module 2 : Construction d’images Docker contenant des environnements IA  
**Objectif mesurable** : L’apprenant écrit un `Dockerfile` optimisé pour un projet PyTorch 2.3 et un projet TensorFlow 2.16, construit l’image, la tague et la teste localement.  
**Notions couvertes**  
- Structure d’un `Dockerfile` : `FROM`, `ARG`, `ENV`, `RUN`, `COPY`, `WORKDIR`, `ENTRYPOINT`.  
- Utilisation d’images de base officielles (`python:3.11-slim`, `nvidia/cuda:12.2-runtime-ubuntu22.04`).  
- Installation de dépendances système (`apt-get install -y build-essential libglib2.0-0`) et de bibliothèques Python (`pip install torch==2.3.0+cu124 -f https://download.pytorch.org/whl/torch_stable.html`).  
- Gestion du cache Docker (`--mount=type=cache`) pour accélérer les reconstructions.  
- Validation de l’image avec un script de test (`python -c "import torch; print(torch.cuda.is_available())"`).

---

## Module 3 : Orchestration de pipelines IA avec Docker Compose et Makefile  
**Objectif mesurable** : L’apprenant crée un fichier `docker-compose.yml` orchestrant un service d’entraînement, un service de stockage de données et un service de visualisation (TensorBoard), puis lance, arrête et met à jour les services via `docker compose` et `make`.  
**Notions couvertes**  
- Définition de services multi‑container (`services`, `volumes`, `networks`).  
- Passage de variables d’environnement (`.env`, `environment:`) et secrets (`docker secret`).  
- Montage de volumes persistants pour les jeux de données (`./data:/data:ro`) et les checkpoints (`./ckpt:/ckpt`).  
- Utilisation de profils (`profiles:`) pour activer/désactiver TensorBoard.  
- Intégration d’un `Makefile` avec cibles `build`, `up`, `down`, `logs` pour automatiser les flux de travail.

---

## Module 4 : Déploiement de modèles IA en production avec Docker  
**Objectif mesurable** : L’apprenant containerise un modèle entraîné (ex

---

## Module 1 — contenu

## 1. Installation de Docker Engine  

### 1.1 Ubuntu 22.04 LTS  

```bash
# 1. Nettoyage d’éventuelles anciennes versions
sudo apt-get remove -y docker docker-engine docker.io containerd runc

# 2. Ajout du dépôt officiel
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg lsb-release
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] \
  https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 3. Installation du moteur
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# 4. Vérification
docker version          # doit afficher Client et Server version 24.x ou plus
docker info | grep -i 'cgroup'   # doit indiquer « cgroup driver: systemd »
```

### 1.2 Windows 10 Pro (édition 1909 ou plus)  

1. Télécharger **Docker Desktop for Windows** depuis <https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe>.  
2. Exécuter l’installateur ; cocher **“Use the WSL 2 based engine”**.  
3. Redémarrer Windows.  
4. Ouvrir un PowerShell **en mode administrateur** :  

```powershell
docker version   # doit renvoyer Client: Docker Engine - Community 24.x
docker compose version   # doit renvoyer Docker Compose version v2.x.x
```

> **Note** : Docker Desktop installe automatiquement le runtime `nvidia` si le **NVIDIA Container Toolkit** est présent dans le WSL 2 (voir § 2.2).

### 1.3 macOS 13 (Ventura)  

```bash
# 1. Installation via Homebrew (casse le besoin d’un .dmg)
brew install --cask docker

# 2. Lancer Docker Desktop depuis le dossier Applications
open -a Docker

# 3. Vérifier le démarrage
docker version
docker compose version
```

> Docker Desktop pour macOS utilise une VM Linux légère (hyperkit). Le support GPU n’est disponible que via **Apple Silicon** : il faut alors **Metal** et non NVIDIA. La section suivante s’applique donc uniquement aux plateformes Linux/WSL 2.

---

## 2. Installation de Docker Compose v2 (plugin CLI)  

Docker Compose v2 est fourni comme **plugin** du client Docker (`docker compose`). Aucun binaire séparé n’est requis.  

```bash
# Ubuntu – déjà installé avec le package docker-compose-plugin (voir §1.1)
docker compose version   # ex. Docker Compose version v2.24.0

# Windows/macOS – inclus dans Docker Desktop
docker compose version
```

*Vérification* : la sortie doit contenir `v2.` et non `v1.`.

---

## 3. Configuration du daemon pour le runtime NVIDIA  

### 3.1 Installation du NVIDIA Container Toolkit (Linux)  

```bash
# 1. Prérequis : driver NVIDIA ≥ 525.60.11 et CUDA Toolkit installé (facultatif)
nvidia-smi   # doit afficher la version du driver

# 2. Ajout du dépôt NVIDIA
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)   # ex. ubuntu22.04
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
  sudo tee /etc/apt/sources.list.d/nvidia-docker.list

# 3. Installation du toolkit (version 2.x)
sudo apt-get update
sudo apt-get install -y nvidia-docker2

# 4. Redémarrage du service Docker
sudo systemctl restart docker
```

### 3.2 Modification du daemon (`/etc/docker/daemon.json`)  

```json
{
  "runtimes": {
    "nvidia": {
      "path": "nvidia-container-runtime",
      "runtimeArgs": []
    }
  },
  "default-runtime": "runc",
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
```

```bash
# Appliquer les changements
sudo systemctl restart docker
```

### 3.3 Test de bon fonctionnement  

```bash
docker run --gpus all --rm nvidia/cuda:12.2-base nvidia-smi
```

*Résultat attendu* : tableau similaire à celui de `nvidia-smi` exécuté sur l’hôte, avec la même version de driver et la liste des GPU.

---

## 4. Gestion des permissions utilisateur  

```bash
# Crée le groupe docker (existe déjà sur la plupart des installations)
sudo groupadd docker

# Ajoute l’utilisateur courant au groupe
sudo usermod -aG docker $USER

---

## Module 2 — contenu

## 2 – Construction d’images Docker contenant des environnements IA  

### 2.1 Principes de base d’un Dockerfile  

| Directive | Rôle | Exemple d’usage |
|-----------|------|-----------------|
| `FROM`   | Image de base. Doit être la première ligne (sauf `ARG` de build‑time). | `FROM python:3.11-slim` |
| `ARG`    | Variable disponible **pendant** le build. Peut être sur‑chargée avec `--build-arg`. | `ARG CUDA_VERSION=12.2` |
| `ENV`    | Variable d’environnement persistante dans le conteneur. | `ENV PYTHONUNBUFFERED=1` |
| `RUN`    | Exécute une commande dans une couche intermédiaire. | `RUN apt-get update && apt-get install -y build-essential` |
| `COPY` / `ADD` | Copie des fichiers du contexte de build vers le système de fichiers de l’image. `ADD` accepte les archives et les URL, mais son usage est découragé. | `COPY requirements.txt /app/` |
| `WORKDIR`| Définit le répertoire de travail pour les instructions suivantes. | `WORKDIR /app` |
| `ENTRYPOINT` / `CMD` | Définit le processus principal. `ENTRYPOINT` est fixe, `CMD` fournit les arguments par défaut. | `ENTRYPOINT ["python"]`<br>`CMD ["train.py"]` |

> **Note** : chaque `RUN` crée une couche immuable. Regrouper les opérations qui modifient le même répertoire (ex. `apt-get install`) dans une même instruction minimise la taille finale.

### 2.2 Choix de l’image de base  

| Besoin | Image recommandée | Pourquoi |
|--------|-------------------|----------|
| CPU‑only, petite taille | `python:3.11-slim` | Basée sur Debian bullseye, < 120 Mo, sans CUDA. |
| GPU, compatibilité CUDA 12.2 | `nvidia/cuda:12.2-runtime-ubuntu22.04` | Contient le runtime CUDA 12.2, compatible avec PyTorch 2.3+ et TensorFlow 2.16. |
| Besoin de bibliothèques système spécifiques (libglib2.0‑0, ffmpeg) | `nvidia/cuda:12.2-runtime-ubuntu22.04` + `apt-get install` | La couche Ubuntu permet d’ajouter les paquets requis. |

> **Vérifiable** : `docker run --rm nvidia/cuda:12.2-runtime-ubuntu22.04 nvidia-smi` doit afficher le driver NVIDIA présent sur l’hôte.

### 2.3 Exemple complet – Image PyTorch 2.3 (GPU)  

```Dockerfile
# ------------------------------------------------------------
# 1️⃣  Image de base contenant le runtime CUDA 12.2
# ------------------------------------------------------------
FROM nvidia/cuda:12.2-runtime-ubuntu22.04 AS base

# ------------------------------------------------------------
# 2️⃣  Variables de build (peuvent être surchargées)
# ------------------------------------------------------------
ARG PYTHON_VERSION=3.11
ARG TORCH_VERSION=2.3.0
ARG TORCH_CUDA=cu124   # PyTorch build for CUDA 12.4 (compatible avec runtime 12.2)

# ------------------------------------------------------------
# 3️⃣  Installation des paquets système nécessaires
# ------------------------------------------------------------
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        python${PYTHON_VERSION} \
        python${PYTHON_VERSION}-dev \
        python3-pip \
        build-essential \
        libglib2.0-0 \
        git && \
    rm -rf /var/lib/apt/lists/*

# ------------------------------------------------------------
# 4️⃣  Création d’un environnement virtuel (facultatif)
# ------------------------------------------------------------
ENV VENV_PATH=/opt/venv
RUN python${PYTHON_VERSION} -m venv ${VENV_PATH}
ENV PATH="${VENV_PATH}/bin:$PATH"

# ------------------------------------------------------------
# 5️⃣  Installation de PyTorch + dépendances Python
# ------------------------------------------------------------
# Utilisation du cache de pip via un volume de build‑time
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip && \
    pip install \
        torch==${TORCH_VERSION}+${TORCH_CUDA} \
        -f https://download.pytorch.org/whl/torch_stable.html \
        torchvision \
        torchaudio

# ------------------------------------------------------------
# 6️⃣  Copie du code utilisateur
# ------------------------------------------------------------
WORKDIR /app
COPY . /app

# ------------------------------------------------------------
# 7️⃣  Vérification de l’accès GPU (exécution au build)
# ------------------------------------------------------------
RUN python -c "import torch; assert torch.cuda.is_available(), 'CUDA non disponible'"

# ------------------------------------------------------------
# 8️⃣  Point d’entrée du conteneur
# ------------------------------------------------------------
ENTRYPOINT ["python"]
CMD ["-c", "import torch; print('CUDA disponible:', torch.cuda.is_available())"]
```

**Explications ligne par ligne**  

* **FROM** – Image officielle NVIDIA contenant le runtime CUDA 12.2.  
* **ARG** – Permet de changer la version de Python ou de PyTorch sans modifier le Dockerfile.  
* **RUN apt‑get** – `DEBIAN_FRONTEND=noninteractive` évite les prompts pendant le build. `rm -rf /var/lib/apt/lists/*` supprime le cache apt pour réduire la taille.  
* **ENV VENV_PATH** – Crée un environnement virtuel isolé, évite les conflits avec les paquets système.  
* **--mount=type=cache** – Fonctionnalité BuildKit (Docker ≥ 18.09). Le répertoire `~/.cache/pip` est mis en cache entre builds, accélérant les reconstructions.  
* **RUN python -c …** – Teste la disponibilité du GPU pendant le build; l’étape échoue immédiatement si CUDA n’est pas accessible.  
* **ENTRYPOINT / CMD** – Le conteneur démarre avec `python`.

---

## Module 3 — contenu

## 3.1. Principes de base de Docker Compose

| Élément | Description | Exemple |
|---------|-------------|---------|
| `services` | Liste les conteneurs à lancer. Chaque service possède son propre nom. | `services:  trainer:` |
| `image` / `build` | `image` indique une image déjà disponible, `build` indique le répertoire contenant le `Dockerfile`. | `build: ./trainer` |
| `volumes` | Montage de répertoires ou de volumes nommés. Syntaxe `<host>:<container>[:ro|rw]`. | `./data:/data:ro` |
| `environment` | Variables d’environnement passées au conteneur. | `environment: - EPOCHS=10` |
| `env_file` | Fichier `.env` contenant des paires `KEY=VAL`. | `env_file: .env` |
| `depends_on` | Déclare les dépendances d’ordre de démarrage (pas de garantie de santé). | `depends_on: - data` |
| `profiles` | Permet d’activer ou désactiver un groupe de services via `docker compose --profile <name> up`. | `profiles: - monitoring` |
| `secrets` | Valeurs sensibles stockées dans le répertoire `secrets/`. Utilisées avec `file:`. | `secrets: - api_key` |
| `networks` | Isolation réseau ou partage de réseau entre services. | `networks: - backend` |

Docker Compose version 2.x (plugin CLI) utilise le même schéma que la version 3.x mais ajoute `profiles` et `secrets`. Le fichier doit commencer par `version: "2.4"` ou être omis (Docker‑Compose infère la version).

---

## 3.2. Exemple complet – Entraînement PyTorch + TensorBoard + stockage de données

```yaml
# docker-compose.yml
version: "2.4"

services:
  data:
    image: alpine:3.18
    command: ["sleep", "infinity"]
    volumes:
      - data_volume:/data:ro
    # Le conteneur `data` ne fait rien d’autre que d’exposer le volume.
    # Il sert de point de synchronisation pour les autres services.

  trainer:
    build:
      context: ./trainer
      dockerfile: Dockerfile
    runtime: nvidia               # active le runtime nvidia (Docker Engine >= 20.10)
    environment:
      - PYTHONUNBUFFERED=1
      - EPOCHS=5
    env_file: .env                # charge les variables communes (ex. WANDB_API_KEY)
    volumes:
      - data_volume:/data:ro
      - ckpt_volume:/ckpt
    depends_on:
      - data
    # Le conteneur démarre le script `train.py` qui écrit les checkpoints dans /ckpt
    # et les logs TensorBoard dans /ckpt/tb_logs.

  tensorboard:
    image: tensorflow/tensorflow:2.16.1
    command: ["tensorboard", "--logdir", "/ckpt/tb_logs", "--host", "0.0.0.0"]
    ports:
      - "6006:6006"
    volumes:
      - ckpt_volume:/ckpt:ro
    profiles:
      - monitoring               # activé uniquement avec `--profile monitoring`
    # Pas de dépendance explicite : TensorBoard lit les logs dès qu’ils existent.

volumes:
  data_volume:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: ${PROJECT_ROOT}/data   # variable définie dans .env
  ckpt_volume:
    driver: local

networks:
  default:
    name: ia_project_net
```

### 3.2.1. Dockerfile du service `trainer`

```Dockerfile
# ./trainer/Dockerfile
FROM nvidia/cuda:12.2-runtime-ubuntu22.04 AS base
ARG PYTHON_VERSION=3.11
ENV DEBIAN_FRONTEND=noninteractive

# 1️⃣ Installation minimale de Python et des outils de compilation
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        python${PYTHON_VERSION} \
        python${PYTHON_VERSION}-venv \
        python${PYTHON_VERSION}-dev \
        build-essential && \
    rm -rf /var/lib/apt/lists/*

# 2️⃣ Création d’un environnement virtuel (facultatif mais recommandé)
RUN python${PYTHON_VERSION} -m venv /opt/venv
ENV PATH="/opt/venv/bin:${PATH}"

# 3️⃣ Installation de PyTorch avec le bon CUDA
RUN pip install --no-cache-dir \
    torch==2.3.0+cu124 \
    -f https://download.pytorch.org/whl/torch_stable.html \
    torchvision==0.18.0+cu124 \
    -f https://download.pytorch.org/whl/torch_stable.html

# 4️⃣ Copie du code source (exclure les gros dossiers avec .dockerignore)
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# 5️⃣ Point d’entrée
ENTRYPOINT ["python", "-u", "train.py"]
```

*Commentaires*  

* `runtime: nvidia` dans le `docker-compose.yml` indique à Docker d’utiliser le runtime `nvidia` installé via le NVIDIA Container Toolkit.  
* Le `Dockerfile` utilise l’image `nvidia/cuda:12.2-runtime-ubuntu22.04` qui ne contient que les bibliothèques CUDA, pas les drivers. Les drivers sont fournis par l’hôte.  
* Le `--mount

---

## Module 4 — contenu

## Module 4 : Déploiement de modèles IA en production avec Docker  

### 4.1. Architecture typique d’un service de modèle  

| composant | rôle | image Docker recommandée |
|----------|------|--------------------------|
| **API** (FastAPI / Flask) | expose `/predict` via HTTP/HTTPS | `tiangolo/uvicorn-gunicorn-fastapi:python3.11` |
| **Serveur de modèle** (TorchServe / TensorFlow Serving) | charge le fichier `.pt` ou `.pb` en mémoire et sert les requêtes | `pytorch/torchserve:latest` ou `tensorflow/serving:2.16.0-gpu` |
| **Reverse‑proxy** (NGINX) | TLS termination, routing, limites de débit | `nginx:stable-alpine` |
| **Observabilité** (Prometheus‑exporter, Grafana) | métriques d’utilisation GPU, latence | images officielles `prom/prometheus`, `grafana/grafana` |
| **Stockage persistant** | modèles, logs, checkpoints | volume Docker ou bind‑mount sur un disque SSD |

Le schéma le plus simple : **NGINX → FastAPI → TorchServe**. NGINX écoute sur le port 443, redirige `/predict` vers le conteneur FastAPI (port 8000). FastAPI appelle TorchServe via gRPC ou HTTP (port 8080).  

---

### 4.2. Dockerfile du service d’inférence (FastAPI + TorchServe)  

```Dockerfile
# ---------------------------------------------------------
# Étape 1 – Build de l’application FastAPI
# ---------------------------------------------------------
FROM python:3.11-slim AS builder

# Variables de build
ARG TORCH_VERSION=2.3.0+cu124
ARG TORCHVISION_VERSION=0.18.0+cu124
ARG TORCHSERVE_VERSION=0.9.0

# Installation des dépendances système indispensables au runtime CUDA
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gcc g++ libglib2.0-0 libgl1 && \
    rm -rf /var/lib/apt/lists/*

# Installation de PyTorch, TorchVision et TorchServe compatibles CUDA 12.4
RUN pip install --no-cache-dir \
    torch==${TORCH_VERSION} \
    torchvision==${TORCHVISION_VERSION} \
    torchserve==${TORCHSERVE_VERSION} \
    fastapi uvicorn[standard] python-multipart

# Copie du code source
WORKDIR /app
COPY ./src ./src
COPY ./model_store ./model_store   # modèle .mar pré‑packagé

# ---------------------------------------------------------
# Étape 2 – Runtime minimal (multi‑stage)
# ---------------------------------------------------------
FROM nvidia/cuda:12.2-runtime-ubuntu22.04 AS runtime

# Crée un utilisateur non‑root
ARG USER_ID=1000
ARG GROUP_ID=1000
RUN groupadd -g ${GROUP_ID} appuser && \
    useradd -m -u ${USER_ID} -g ${GROUP_ID} -s /bin/bash appuser

# Copie des artefacts depuis le builder
COPY --from=builder /usr/local/lib/python3.11 /usr/local/lib/python3.11
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /app /app

# Permissions
RUN chown -R appuser:appuser /app && \
    chmod -R 755 /app

# Expose les ports attendus
EXPOSE 8000 8080

# Entrypoint : démarre à la fois FastAPI (Uvicorn) et TorchServe
ENTRYPOINT ["/bin/bash", "-c", "\
    # Démarrage de TorchServe en arrière‑plan
    torchserve --start --model-store /app/model_store --models mymodel=mnist.mar --ts-config /app/ts_config.properties && \
    # Démarrage de l’API FastAPI
    uvicorn src.main:app --host 0.0.0.0 --port 8000 \
"]
```

**Commentaires**  

* `nvidia/cuda:12.2-runtime-ubuntu22.04` garantit la présence du driver CUDA 12.2 au runtime, compatible avec les wheels PyTorch `+cu124`.  
* Le build se fait en deux étapes : le premier stage compile les dépendances Python, le second ne garde que le runtime minimal, ce qui réduit la taille finale à ≈ 350 Mo.  
* `torchserve --start` crée le processus `torchserve` qui écoute sur le port 8080 (HTTP) et le port 7070 (management).  
* `uvicorn` expose l’API `/predict` qui, dans le code Python, envoie la requête à TorchServe via HTTP (`requests.post("http://localhost:8080/predictions/mymodel", ...)`).  

---

### 4.3. Fichier `src/main.py` (FastAPI)  

```python
# src/main.py
from fastapi import FastAPI, File, UploadFile, HTTPException
import requests
import io
from PIL import Image
import numpy as np

app = FastAPI(
    title="Inference API",
    description="Expose un endpoint /predict qui délègue la prédiction à TorchServe.",
    version="1.0.0"
)

TORCHSERVE_URL = "http://localhost:8080/predictions/mymodel"

def preprocess(image_bytes: bytes) -> bytes:
    """Convertit une image JPEG/PNG en tableau Numpy, normalise et renvoie le tableau sérialisé."""
    img = Image.open(io.BytesIO(image_bytes)).convert("L")  # MNIST → 1 canal
    img = img.resize((28, 28))
    arr = np.array(img, dtype=np.float32) / 255.0
    # TorchServe attend un tableau 1x28x28 sous forme de bytes
    return arr[np.newaxis,

---

## Module 5 — contenu

## Module 5 : Sécurité, CI/CD et monitoring des conteneurs IA  

### 5.1 Durcissement des images Docker  

| Action | Commande / Dockerfile | Pourquoi c’est sûr |
|--------|------------------------|--------------------|
| **Utiliser un utilisateur non‑root** | ```Dockerfile\nFROM python:3.11-slim\n# création d’un uid/gid dédié\nRUN groupadd -r app && useradd -r -g app app\nWORKDIR /app\nCOPY --chown=app:app . /app\nUSER app\n``` | Empêche l’escalade de privilèges depuis le conteneur. |
| **Multi‑stage build** – ne garder que le runtime | ```Dockerfile\n# ---------- build stage ----------\nFROM python:3.11-slim AS builder\nWORKDIR /src\nCOPY requirements.txt .\nRUN pip install --user -r requirements.txt\n# ---------- runtime stage ----------\nFROM nvidia/cuda:12.2-runtime-ubuntu22.04\nWORKDIR /app\nCOPY --from=builder /root/.local /root/.local\nENV PATH=/root/.local/bin:$PATH\nCOPY . /app\n``` | Réduit la taille de l’image et supprime les outils de compilation qui pourraient être exploités. |
| **Supprimer les caches apt** | ```Dockerfile\nRUN apt-get update && apt-get install -y --no-install-recommends libglib2.0-0 \\\n    && rm -rf /var/lib/apt/lists/*\n``` | Évite de laisser des métadonnées de paquets qui pourraient révéler la version du système. |
| **Limiter les capacités Linux** | ```bash\ndocker run --security-opt=no-new-privileges --cap-drop=ALL myimage\n``` | Bloque les appels système non nécessaires. |
| **Activer le read‑only filesystem** | ```bash\ndocker run --read-only myimage\n``` | Empêche toute écriture accidentelle ou malveillante. |
| **Scannez les vulnérabilités** | ```bash\ndocker scan myimage   # utilise Snyk (intégré depuis Docker 23.0)\n``` | Détecte les CVE connues dans les couches de l’image. |
| **Signer les images** | ```bash\ndocker trust sign myregistry.example.com/myimage:1.0.0\n``` | Garantit l’intégrité et l’authenticité grâce à Docker Content Trust (DCT). |

#### Piège concret 1 – Oublier le `USER`  
Si le Dockerfile ne définit pas `USER`, le conteneur s’exécute en tant que `root`. Sur un hôte avec le socket Docker monté (`/var/run/docker.sock`), un attaquant peut créer de nouveaux conteneurs avec les mêmes privilèges que le daemon.  

#### Piège concret 2 – Utiliser `latest` comme tag  
`docker pull myimage:latest` ne garantit pas la même version entre deux builds. En CI/CD, cela rend les reproductions impossibles et peut introduire des vulnérabilités non testées.

---

### 5.2 Intégration continue et déploiement continu (CI/CD) avec GitHub Actions  

#### 5.2.1 Workflow de base  

```yaml
# .github/workflows/docker-ci.yml
name: CI – Build, Scan, Push

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  build-and-push:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write   # nécessaire pour pousser vers GHCR
      id-token: write   # pour Docker Content Trust (optional)

    steps:
      # 1️⃣ Checkout du code
      - name: Checkout repository
        uses: actions/checkout@v4

      # 2️⃣ Cache pip (accélère les reconstructions)
      - name: Cache pip
        uses: actions/cache@v3
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('requirements.txt') }}
          restore-keys: |
            ${{ runner.os }}-pip-

      # 3️⃣ Build de l’image (multi‑stage, tag SHA)
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v2

      - name: Log in to GitHub Container Registry
        uses: docker/login-action@v2
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: ghcr.io/${{ github.repository_owner }}/${{ github.event.repository.name