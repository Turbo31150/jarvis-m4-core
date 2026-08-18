# Mistral AI — Local & API

> Référence `mistral-local` · 49 €

## Plan

## Module 1 – Installation et configuration de Mistral AI Local  
**Objectif mesurable** : L’apprenant pourra installer la version 2.3.0 de Mistral AI en local, configurer le runtime et valider le bon fonctionnement via la commande `mistral health`.  
**Notions couvertes**  
- Prérequis matériels : un processeur multi‑cœurs, une quantité suffisante de RAM, un GPU NVIDIA compatible, les drivers et CUDA appropriés.  
- Installation avec `pip install mistral-local==2.3.0` et alternative Docker (`docker pull mistralai/mistral:2.3.0`).  
- Structure du fichier `mistral.yaml` : `model_path`, `log_dir`, `max_threads`, `cache_size`.  
- Lancement du serveur local (`mistral serve --config mistral.yaml`) et test de santé (`curl http://localhost:8000/health`).  
- Gestion des versions : utilisation de `pip list --outdated` et mise à jour sécurisée (`pip install --upgrade mistral-local`).

## Module 2 – Utilisation de l’API REST de Mistral AI  
**Objectif mesurable** : L’apprenant pourra envoyer une requête de génération de texte à l’endpoint `/v1/completions`, interpréter la réponse JSON et gérer les erreurs HTTP 4xx/5xx.  
**Notions couvertes**  
- Authentification par token statique (`Authorization: Bearer <clé>`).  
- Schéma de la requête : `model`, `prompt`, `max_tokens`, `temperature`, `top_p`.  
- Format de la réponse : `id`, `object`, `created`, `choices[0].text`, `usage`.  
- Gestion du débit et des retries exponentiels.  
- Outils de test : `curl`, Postman, client Python `requests` avec `Session`.

## Module 3 – Fine‑tuning d’un modèle Mistral AI en local  
**Objectif mesurable** : L’apprenant pourra préparer un jeu de données au format JSONL, lancer un job de fine‑tuning avec `mistral fine-tune` et évaluer le modèle fine‑tuned sur un jeu
---

## Module 1 — contenu

## 1.1 Prérequis matériels et logiciels  

| Élément | Minimum requis | Pourquoi |
|--------|----------------|----------|
| CPU    | 8 cœurs (ex. AMD Ryzen 9 5900X) | Le serveur Mistral parallélise le décodage; moins de cœurs augmente la latence. |
| RAM    | 32 Go DDR4/DDR5 | Le modèle 7B occupe ~13 Go en FP16 + cache + overhead. |
| GPU    | NVIDIA RTX 3080 (10 Go VRAM) ou supérieur | Décodage en FP16 nécessite au moins 8 Go VRAM ; la version 2.3.0 ne supporte que CUDA 11.8+. |
| Driver NVIDIA | ≥ 525.89.05 | Compatibilité avec CUDA 11.8. |
| CUDA   | 11.8 | Bibliothèques `torch` et `bitsandbytes` sont compilées contre cette version. |
| OS     | Linux (ubuntu 22.04 LTS recommandé) ou Windows 10 + WSL2 | Le binaire `mistral` s’appuie sur des librairies C++ qui ne sont pas garanties sous macOS. |
| Python | ≥ 3.9, < 3.13 | `mistral-local` dépend de `torch>=2.1`. |
| Outils réseau | `curl` (≥ 7.68) | Utilisé pour le health‑check. |
| Port libre | 8000 (TCP) | Le serveur écoute par défaut sur ce port. |

> **Vérification** :  
> ```bash
> nvidia-smi | grep -i driver
> nvcc --version   # doit afficher CUDA 11.8
> python3 -c "import sys; print(sys.version)"
> ```

---

## 1.2 Installation du package Python  

```bash
# 1. Créez un environnement virtuel isolé
python3 -m venv ~/.venv/mistral
source ~/.venv/mistral/bin/activate

# 2. Upgrade pip, wheel, setuptools (évite les erreurs de compilation)
pip install --upgrade pip wheel setuptools

# 3. Installation de la version 2.3.0
pip install mistral-local==2.3.0
```

*Pitfall : `pip` utilise parfois le cache d’une version antérieure de `torch`. Si l’installation échoue avec `ERROR: Could not find a version that satisfies the requirement torch`, videz le cache (`pip cache purge`) ou ajoutez `--no-cache-dir`.*

---

## 1.3 Installation alternative via Docker  

```bash
docker pull mistralai/mistral:2.3.0
docker run -d \
  --name mistral_local \
  -p 8000:8000 \
  -v $(pwd)/mistral.yaml:/app/mistral.yaml:ro \
  mistralai/mistral:2.3.0 \
  mistral serve --config /app/mistral.yaml
```

*Pitfall : le conteneur utilise le driver NVIDIA du host. Sous Docker ≥ 19.03, ajoutez `--gpus all` pour exposer le GPU, sinon le serveur démarre en CPU‑only et la latence grimpe.*

```bash
docker run -d --gpus all ...   # version correcte
```

---

## 1.4 Fichier de configuration `mistral.yaml`  

```yaml
# mistral.yaml – configuration du serveur local
model_path: /data/mistral-7b-instruct-v0.2  # répertoire contenant le modèle (FP16)
log_dir:   /var/log/mistral                 # où les logs rotatifs sont écrits
max_threads: 8                               # nombre de threads de décodage
cache_size: 4                               # nombre de batches en cache (GPU RAM)
port: 8000                                   # port d’écoute HTTP
host: 0.0.0.0                                 # écoute sur toutes les interfaces
```

*Explications*  

- `model_path` doit pointer vers un répertoire contenant `model.safetensors` et le fichier `config.json`.  
- `max_threads` ne doit pas dépasser le nombre de cœurs physiques ; un dépassement entraîne du **CPU‑oversubscription** et des pics de latence.  
- `cache_size` est exprimé en *batches* ; chaque batch consomme `model_dim * max_tokens * 2 bytes` en VRAM. Ajustez en fonction de la VRAM disponible.  

---

## 1.5 Lancement du serveur local  

```bash
# 1. Vérifiez que le répertoire du modèle est accessible
ls -l /data/mistral-7b-instruct-v0.2

# 2. Démarrez le serveur
mistral serve --config mistral.yaml
```

Le processus écrit dans la console :

```
[2026-08-14 10:12:03] INFO  Server listening on http://0.0.0.0:8000
[2026-08-14 10:12:04] INFO  Model loaded (FP16) – 13.2 GiB VRAM used
```

*Pitfall : Si le serveur s’arrête immédiatement avec `RuntimeError: CUDA out of memory`, réduisez `cache_size` ou passez en mode `cpu` (`device: cpu` dans le yaml).*

---

## 1.6 Vérification de santé (`mistral health`)  

```bash
# Méthode 1 – CLI
```
---

## Module 2 — contenu

## 2.1 Authentification  

- Le serveur local expose l’API REST sur **http://localhost:8000**.  
- L’accès est protégé par un **token statique** défini dans le fichier `mistral.yaml` :  

```yaml
auth:
  token: "MISTRAL_API_KEY_12345"
```  

- Le client doit ajouter l’en‑tête HTTP :  

```
Authorization: Bearer MISTRAL_API_KEY_12345
```  

> **Vérifiable** : la valeur du token est renvoyée dans le log du serveur au démarrage (`Auth token loaded`).  

### Piège : fuite du token  

Ne jamais placer le token en clair dans le code versionné. Utilisez une variable d’environnement :  

```bash
export MISTRAL_TOKEN="MISTRAL_API_KEY_12345"
```  

et référencez‑la dans vos scripts (`$MISTRAL_TOKEN` ou `os.getenv("MISTRAL_TOKEN")`).

---

## 2.2 Schéma de la requête `/v1/completions`

| Champ          | Type    | Obligatoire | Valeurs typiques                         |
|----------------|---------|--------------|------------------------------------------|
| `model`        | string  | oui          | `"mistral-7b-v2"`                        |
| `prompt`       | string  | oui          | texte à compléter                        |
| `max_tokens`  | int     | non (default = 256) | 1 – 2048                                  |
| `temperature` | float   | non (default = 0.7) | 0.0 – 2.0                                 |
| `top_p`        | float   | non (default = 0.9) | 0.0 – 1.0                                 |
| `stream`       | bool    | non (default = false) | `true` active le mode streaming (non couvert ici) |

Exemple de corps JSON :  

```json
{
  "model": "mistral-7b-v2",
  "prompt": "Explique la différence entre le machine learning supervisé et non‑supervisé.",
  "max_tokens": 150,
  "temperature": 0.6,
  "top_p": 0.95
}
```

**En‑tête obligatoire** : `Content-Type: application/json`.

---

## 2.3 Format de la réponse JSON  

```json
{
  "id": "cmpl-01F2Z3K9V8X9",
  "object": "text_completion",
  "created": 1723614802,
  "model": "mistral-7b-v2",
  "choices": [
    {
      "index": 0,
      "text": "Le machine learning supervisé repose sur un jeu de données étiqueté...",
      "finish_reason": "length"
    }
  ],
  "usage": {
    "prompt_tokens": 34,
    "completion_tokens": 150,
    "total_tokens": 184
  }
}
```

- `choices[0].text` contient le texte généré.  
- `usage` permet de suivre la consommation de tokens (utile pour la facturation ou le quota interne).  

---

## 2.4 Gestion du débit (rate limiting)  

Le serveur impose **60 requêtes par minute** par token.  

- En cas de dépassement, il renvoie **HTTP 429 Too Many Requests** avec l’en‑tête `Retry-After: <seconds>`.  
- Le client doit attendre le nombre de secondes indiqué avant de réessayer.  

> **Vérifiable** : exécuter 61 requêtes consécutives avec le même token et observer le code 429 et l’en‑tête `Retry-After`.

### Implémentation d’un back‑off exponentiel (exemple Python)

```python
import time
import random

def exponential_backoff(attempt, base=1.0, cap=30.0):
    """Retourne un délai en secondes, jitteré, limité à `cap`."""
    delay = min(cap, base * (2 ** attempt))
    # jitter pour éviter le thundering herd
    return delay * random.uniform(0.8, 1.2)
```

---

## 2.5 Exemple complet : appel à `/v1/completions` avec `requests`

```python
#!/usr/bin/env python3
"""
Exemple fonctionnel d’appel à l’API completions de Mistral AI (v2.3.0).
- Utilise un `requests.Session` pour réutiliser la connexion TCP.
- Gère les erreurs HTTP 4xx/5xx, le 429 avec back‑off exponentiel.
- Retourne le texte généré ou lève une exception en cas d’échec définitif.
"""

import os
import json
import time
import random
import logging
from typing import Dict, Any

import requests

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
API_URL = "http://localhost:8000/v1/completions"
TOKEN = os.getenv("MISTRAL_TOKEN")  # ← à définir dans l’environnement
HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json",
}
MAX_RETRIES = 5          # nombre maximal de tentatives



---

## Module 3 — contenu

## 3.1 Préparer le jeu de données

| Élément | Format obligatoire | Exemple minimal |
|--------|-------------------|-----------------|
| **Prompt** | Chaîne UTF‑8, max 1024 tokens | `{"prompt":"Quel est le capital de la France ?"}` |
| **Completion** | Chaîne UTF‑8, max 1024 tokens, doit commencer par un espace si le modèle attend un séparateur | `{"completion":" Paris"}` |
| **JSONL** | Un objet JSON par ligne, aucun séparateur de ligne supplémentaire | `{"prompt":"Quel est le capital de la France ?","completion":" Paris"}` |

```text
# data/train.jsonl (exemple 3 lignes)
{"prompt":"Quel est le capital de la France ?","completion":" Paris"}
{"prompt":"Qui a écrit \"Les Misérables\" ?","completion":" Victor Hugo"}
{"prompt":"Combien font 7*8 ?","completion":" 56"}
```

**Contraintes vérifiables**

* Chaque ligne doit être un JSON valide (`python -m json.tool < file` ne doit pas lever d’erreur).  
* Aucun champ supplémentaire n’est autorisé (le parser de Mistral ignore les clés inconnues).  
* Le total de tokens du **prompt + completion** ne doit pas dépasser la limite du modèle (`mistral info --model <model>` indique `max_input_length`).  

**Outils de contrôle**

```bash
# Vérifier le nombre de lignes
wc -l data/train.jsonl

# Vérifier la conformité JSON
python - <<'PY'
import json, sys
for i, line in enumerate(open('data/train.jsonl')):
    try:
        json.loads(line)
    except json.JSONDecodeError as e:
        print(f"Ligne {i+1} invalide : {e}")
        sys.exit(1)
print("Tout est valide")
PY
```

---

## 3.2 Lancer le job de fine‑tuning

### 3.2.1 Configuration du job

```yaml
# fine_tune.yaml
model: mistral-7b-v0.1          # modèle de base installé localement
train_data: data/train.jsonl
valid_data: data/valid.jsonl    # optionnel, sinon split aléatoire
output_dir: fine_tuned/        # répertoire où seront écrits les checkpoints
epochs: 3
batch_size: 4                  # dépend de la VRAM disponible
learning_rate: 2e-5
max_grad_norm: 1.0
seed: 42
```

### 3.2.2 Commande CLI

```bash
mistral fine-tune \
    --config fine_tune.yaml \
    --log_dir logs/ft_run_$(date +%Y%m%d_%H%M%S)
```

*Le processus crée* :

* `fine_tuned/checkpoint-<step>.pt` – poids intermédiaires.  
* `fine_tuned/config.json` – copie du fichier de configuration avec les valeurs résolues.  
* `logs/ft_run_*/metrics.jsonl` – métriques par étape (loss, learning_rate, throughput).

### 3.2.3 Surveillance en temps réel

```bash
tail -f logs/ft_run_*/metrics.jsonl | jq .
```

---

## 3.3 Évaluer le modèle fine‑tuned

### 3.3.1 Préparer le jeu de test

```bash
# data/test.jsonl (format identique à train, mais sans champ "completion" si on veut mesurer la génération)
{"prompt":"Quel est le plus grand océan du monde ?"}
{"prompt":"Quelle est la formule chimique de l'eau ?"}
```

### 3.3.2 Script d’évaluation (Python, `requests`)

```python
#!/usr/bin/env python3
"""
Évaluation d'un modèle fine‑tuned via l'API locale.
- Génère une réponse pour chaque prompt du jeu de test.
- Calcule la métrique Exact Match (EM) et le score ROUGE‑L.
"""

import json, pathlib, sys
import requests
from rouge_score import rouge_scorer

API_URL = "http://localhost:8000/v1/completions"
TOKEN = "local-dev-token"          # token généré par `mistral token create`
MODEL = "fine_tuned"                # nom du répertoire contenant le checkpoint

HEADERS = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}

def generate(prompt: str) -> str:
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "max_tokens": 64,
        "temperature": 0.0,      # désactiver la stochasticité pour EM
        "top_p": 1.0,
    }
    r = requests.post(API_URL, headers=HEADERS, json=payload, timeout=30)
    r.raise_for_status()
    return r.json()["choices"][0]["text"].strip()

def main(test_path: str):
    scorer = rouge_scorer.RougeScorer(['rougeL'], use_stemmer=True)
    em, rouge_l = 0, 0.0
    total = 0

    for line in pathlib.Path(test_path).read_text().splitlines():
        obj = json.loads(line)
        prompt = obj["prompt"]
        ref = obj.get("completion", "").strip()   # si référence fournie
        pred = generate(prompt)
```

---

## Module 4 — contenu

## Module 4 – Déploiement production, monitoring & sécurisation de l’API Mistral AI  

### 4.1 Architecture de service recommandée  

| Composant | Rôle | Technologie | Points de contrôle |
|-----------|------|--------------|--------------------|
| **Serveur d’inférence** | Expose `/v1/completions` | `uvicorn` + `fastapi` (fourni par `mistral serve`) | `health` & `ready` probes, limite de threads (`max_threads` dans `mistral.yaml`) |
| **Reverse‑proxy** | TLS termination, rate‑limit, métriques | `nginx` (ou `traefik`) | Certificat valide, `proxy_read_timeout` configuré à une valeur suffisante |
| **Load‑balancer** (optionnel) | Répartir les requêtes sur plusieurs workers | `haproxy` ou `k8s Service` | Affinité de session désactivée |
| **Metrics exporter** | Exporter les stats Prometheus | `prometheus_client` intégré à `mistral` (`/metrics`) | Scraping interval configuré à une courte période |
| **Logging centralisé** | Agréger logs JSON | `logstash` / `fluentd` + `ELK` | Format JSON, `log_dir` accessible en écriture |
| **Orchestrateur** | Redémarrage automatique, scaling | Docker‑Compose ou Kubernetes | `restart: unless-stopped`, `resources.limits` |

> **Règle de base** : chaque composant tourne dans son propre conteneur, les volumes partagés sont limités aux fichiers de modèle et aux logs.

---

### 4.2 Docker‑Compose complet (production)

```yaml
# docker-compose.yml
version: "3.9"

services:
  mistral-api:
    image: mistralai/mistral:2.3.0
    command: >
      mistral serve
      --config /app/config/mistral.yaml
      --host 0.0.0.0
      --port 8000
    environment:
      - MISTRAL_LOG_LEVEL=info
      - MISTRAL_TOKEN=${MISTRAL_TOKEN}   # token secret injecté via .env
    volumes:
      - ./model:/app/model:ro          # modèle en lecture seule
      - ./config/mistral.yaml:/app/config/mistral.yaml:ro
      - ./logs:/app/logs
    expose:
      - "8000"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 5s
      retries: 3

  nginx:
    image: nginx:1.27-alpine
    ports:
      - "443:443"
    volumes:
      - ./nginx/conf.d:/etc/nginx/conf.d:ro
      - ./certs:/etc/nginx/certs:ro
    depends_on:
      mistral-api:
        condition: service_healthy

  prometheus:
    image: prom/prometheus:v2.53.0
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml:ro
    command:
      - "--config.file=/etc/prometheus/prometheus.yml"
    ports:
      - "9090:9090"

networks:
  default:
    driver: bridge
```

**`nginx/conf.d/mistral.conf`**  

```nginx
server {
    listen 443 ssl http2;
    server_name api.mistral.local;

    ssl_certificate     /etc/nginx/certs/fullchain.pem;
    ssl_certificate_key /etc/nginx/certs/privkey.pem;
    ssl_protocols       TLSv1.2 TLSv1.3;
    ssl_ciphers         HIGH:!aNULL:!MD5;

    # Limite de débit globale : 60 req/min par IP
    limit_req_zone $binary_remote_addr zone=mistral:10m rate=60r/m;
    limit_req   zone=mistral burst=10 nodelay;

    location / {
        proxy_pass http://mistral-api:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 30s;
    }

    location /metrics {
        proxy_pass http://mistral-api:8000/metrics;
        allow 127.0.0.1;   # métriques uniquement depuis le réseau interne
        deny all;
    }
}
```

**`prometheus.yml`** (scrape uniquement le conteneur `mistral-api`)  

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 30s

scrape_configs:
  - job_name: "mistral"
    static_configs:
      - targets: ["mistral-api:8000"]
    metrics_path: /metrics
    scheme: http
```

---

### 4.3 Configuration `mistral.yaml` adaptée à la

---

## Module 5 — contenu

## Module 5 – Observabilité, journalisation et mise à l’échelle du serveur Mistral AI (v2.3.0)

### 5.1 Activation des métriques Prometheus  

| Paramètre | Valeur | Description |
|-----------|--------|--------------|
| `--metrics` | `true` | Expose `/metrics` au format Prometheus sur le même port HTTP que l’API (`8000` par défaut). |
| `--metrics-port` | `8001` (optionnel) | Si vous ne voulez pas mélanger API et métriques, indiquez un port dédié. |
| `metrics_path` (dans `mistral.yaml`) | `/metrics` | Chemin d’accès (peut être changé, mais le client Prometheus s’attend à `/metrics`). |

**Commande de lancement**  

```bash
mistral serve \
    --config mistral.yaml \
    --metrics \
    --metrics-port 8001
```

### 5.2 Configuration du logging  

`mistral.yaml` (extrait) :

```yaml
logging:
  level: INFO               # DEBUG, INFO, WARNING, ERROR, CRITICAL
  format: "%(asctime)s %(levelname)s %(name)s - %(message)s"
  file: "${log_dir}/mistral.log"
  rotate:
    when: midnight          # rotation quotidienne
    backupCount: 7          # garder 1 semaine
```

- Le répertoire `log_dir` doit être accessible en écriture par l’utilisateur qui exécute le service.
- `logging.level` : utilisez `DEBUG` uniquement en phase de développement, il génère un trafic supplémentaire notable sur le disque.

### 5.3 Mise en place d’un service systemd (production)

`/etc/systemd/system/mistral.service` :

```ini
[Unit]
Description=Mistral AI inference server
After=network.target

[Service]
User=mistral
Group=mistral
Environment=PYTHONUNBUFFERED=1
ExecStart=/usr/local/bin/mistral serve \
    --config /opt/mistral/mistral.yaml \
    --metrics \
    --metrics-port 8001 \
    --workers 4               # nombre de processus workers
Restart=on-failure
LimitNOFILE=65535            # éviter “Too many open files”

[Install]
WantedBy=multi-user.target
```

- `--workers` crée un pool de processus isolés, chacun charge le modèle en mémoire. La RAM requise dépend de la taille du modèle et du nombre de workers.  
- `LimitNOFILE` doit être configuré en fonction du nombre de requêtes simultanées et des besoins en fichiers.

Activation :

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now mistral.service
```

### 5.4 Surveillance des métriques clés  

Métriques exposées (extraits) :

| Métrique | Type | Description |
|----------|------|-------------|
| `mistral_requests_total` | counter | Nombre total de requêtes HTTP reçues. |
| `mistral_request_latency_seconds` | histogram | Latence de traitement (inclut décodage, génération, sérialisation). |
| `mistral_gpu_memory_bytes` | gauge | Mémoire GPU allouée par le processus worker. |
| `mistral_cpu_usage_percent` | gauge | Utilisation CPU du processus (exposé via `process_cpu_seconds_total`). |

#### 5.4.1 Exemple de script Python de monitoring  

```python
#!/usr/bin/env python3
"""
Surveille la latence moyenne des requêtes Mistral (histogramme prometheus).
Alerte si la latence dépasse un seuil pendant plusieurs intervalles consécutifs.
"""
import time
import requests
from collections import deque

METRICS_URL = "http://localhost:8001/metrics"
LATENCY_BUCKET = ...          # seuil de latence à définir
CONSECUTIVE_THRESHOLD = ...  # nombre d'alertes consécutives requis
INTERVAL = ...                # intervalle entre chaque scrape

def parse_histogram(text: str, name: str) -> dict:
    """
    Retourne un dict {le, le, …} où chaque clé est le bord supérieur du bucket
    et la valeur le compteur cumulé.
    """
    # Implémentation du parsing...
    pass
```

---