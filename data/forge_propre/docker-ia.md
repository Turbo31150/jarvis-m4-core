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
| CPU‑only, petite taille | `python:3.11-slim` | Basée sur Debian bullseye, sans CUDA. |
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
* **ARG** – Permet de changer la version de Python ou de PyTorch