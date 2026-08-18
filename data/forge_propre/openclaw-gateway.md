# OpenClaw Gateway — 77 Agents et 961 scripts

> Référence `openclaw-gateway` · 99 €

## Plan

## Module 1 – Installation et configuration de l’environnement OpenClaw  
**Objectif mesurable :** Installer, configurer et vérifier le bon fonctionnement d’OpenClaw Gateway sur une machine Linux (Ubuntu 20.04 + Docker) dans un délai raisonnable.  
**Notions couvertes**  
- Prérequis système : versions de Python, Docker, PostgreSQL.  
- Déploiement via le script `install.sh` et le fichier `docker-compose.yml`.  
- Gestion des variables d’environnement (`.env`) et des secrets.  
- Vérification du service : `docker ps`, logs (`docker logs openclaw_gateway`).  
- Mise à jour et rollback avec Git tags (`v1.2.3`).

## Module 2 – Architecture des agents et du moteur de scripts  
**Objectif mesurable :** Décrire et diagrammer les flux de données entre les 77 agents et le moteur d’exécution, et identifier le point d’injection d’un script personnalisé.  
**Notions couvertes**  
- Modèle de communication (gRPC + Redis Pub/Sub).  
- Structure des agents : classes `BaseAgent`, `TaskAgent`, `MonitoringAgent`.  
- Cycle de vie d’un script : chargement, compilation, sandboxing, exécution.  
- Gestion des dépendances via le fichier `requirements.yaml`.  
- Points d’extension (`hooks/`, `plugins/`).

## Module 3 – Développement d’un script OpenClaw (API et bonnes pratiques)  
**Objectif mesurable :** Créer, tester et déployer un script complet (entrée, traitement, sortie) dans un délai raisonnable.  
**Notions couvertes**  
- API Python : `openclaw.sdk` – classes `Task`, `Context`, `Result`.  
- Gestion des entrées/sorties (`jsonschema` validation, `pydantic` models).  
- Utilisation des services internes : base de données (`db.session`), cache (`redis_client`).  
- Gestion des erreurs : `OpenClawException`, retries avec `tenacity`.  
- Tests unitaires avec `pytest` et simulation d’environnement (`fixtures/`).

## Module 4 – Orchestration avancée et optimisation des agents  
**Objectif mesurable :** Configurer une orchestration qui répartit les charges sur plusieurs nœuds, améliorer le temps moyen d’exécution d’un script grâce à la parallélisation.  
**Notions couvertes**  
- Paramétrage du scheduler (`celery` + `redis` broker).  
- Stratégies de répartition : round‑robin, poids dynamiques.  
- Profilage des scripts (`cProfile`, `py-spy`).  
- Optimisation du code : asynchronisme (`asyncio`), batch processing.  
- Monitoring avec Prometheus + Grafana (metrics `openclaw_task_duration_seconds`).

## Module 5 – Sécurité, conformité et mise en production  
**Objectif mesurable :** Appliquer le modèle de sécurité OpenClaw (sandbox, audit) et publier une version stable avec pipeline CI/CD complet dans un délai raisonnable.  
**Notions couvertes**  
- Sandbox Docker : limites de ressources (`--memory`, `--cpus`), user ns.  
- Gestion des permissions : RBAC dans `openclaw.yaml`, tokens JWT.  
- Audits de scripts : signatures SHA‑256, validation de provenance.  
- Pipeline CI/CD avec GitHub Actions (`build.yml`

---

## Module 1 — contenu

## Module 1 – Installation et configuration de l’environnement OpenClaw  

### 1.1 Prérequis système  

| Composant | Version minimale | Vérification | Installation (Ubuntu 20.04) |
|-----------|-------------------|--------------|-----------------------------|
| Python    | 3.9               | `python3 --version` | `sudo apt-get install -y python3.9 python3.9-venv` |
| Docker    | 20.10 +           | `docker --version` | `sudo apt-get install -y docker.io` |
| Docker‑compose | 2.2 +        | `docker compose version` | `sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose && sudo chmod +x /usr/local/bin/docker-compose` |
| PostgreSQL client | 12 +    | `psql --version` | `sudo apt-get install -y postgresql-client` |
| Git       | 2.25 +            | `git --version` | `sudo apt-get install -y git` |

> **Note** : Docker doit être lancé avec les droits suffisants (`sudo usermod -aG docker $USER` puis *relogin*).  

### 1.2 Récupération du dépôt OpenClaw Gateway  

```bash
# Clone le dépôt officiel (exemple d'URL)
git clone https://github.com/openclaw/openclaw-gateway.git
cd openclaw-gateway
# Checkout la version stable recommandée
git checkout tags/v1.2.3 -b work-v1.2.3
```

### 1.3 Fichier `.env` – variables d’environnement  

Copier le template fourni et adapter les valeurs :

```bash
cp .env.example .env
```

```dotenv
# .env – commentaires en ligne
POSTGRES_USER=oc_user               # utilisateur DB
POSTGRES_PASSWORD=SuperSecret123   # mot de passe DB (ne jamais commit)
POSTGRES_DB=oc_gateway              # nom de la base
POSTGRES_HOST=db                    # nom du service Docker
POSTGRES_PORT=5432

REDIS_HOST=redis
REDIS_PORT=6379

# JWT secret – 32 bytes encodés en base64
JWT_SECRET=U2VjcmV0S2V5Rm9ySmF2YVNFQ1JfMjAyMw==
```

**Piège** : le fichier `.env` est souvent exclu du dépôt (`.gitignore`). Si vous le créez après le premier `docker compose up`, Docker ne le rechargera pas automatiquement. Relancez le stack ou exécutez `docker compose up -d --force-recreate`.

### 1.4 Script d’installation `install.sh`  

Le script réalise :  

1. Vérifie la présence de Docker et Docker‑compose.  
2. Crée le réseau Docker `openclaw_net`.  
3. Lance `docker compose up -d`.  
4. Initialise la base de données (migration Alembic).  

```bash
#!/usr/bin/env bash
set -euo pipefail

# 1. Vérifications préliminaires
command -v docker >/dev/null 2>&1 || { echo "Docker absent. Installez-le avant de continuer."; exit 1; }
command -v docker-compose >/dev/null 2>&1 || { echo "docker-compose absent. Installez-le avant de continuer."; exit 1; }

# 2. Création du réseau (idempotent)
docker network inspect openclaw_net >/dev/null 2>&1 || \
    docker network create openclaw_net

# 3. Démarrage des services
echo "Démarrage du stack Docker..."
docker compose up -d

# 4. Attente que PostgreSQL soit prêt
echo "Attente de PostgreSQL..."
until docker exec openclaw_gateway-db pg_isready -U "$POSTGRES_USER" >/dev/null 2>&1; do
    sleep 2
done

# 5. Migration Alembic (créée dans le conteneur)
echo "Application des migrations..."
docker exec openclaw_gateway-web alembic upgrade head

echo "Installation terminée. OpenClaw Gateway est opérationnel."
```

*Commentaires* :  

* `set -euo pipefail` garantit l’arrêt du script en cas d’erreur ou de variable non définie.  
* `docker exec` cible les conteneurs créés par le `docker-compose.yml` (`openclaw_gateway-db` et `openclaw_gateway-web`).  
* La boucle `until pg_isready` évite les erreurs de migration quand PostgreSQL n’est pas encore disponible.  

### 1.5 Fichier `docker-compose.yml` (extrait clé)  

```yaml
version: "3.9"

networks:
  openclaw_net:
    external: true

services:
  db:
    image: postgres:14-alpine
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    volumes:
      - pgdata:/var/lib/postgresql/data
    networks:
      - openclaw_net

  redis:
    image: redis:7-alpine
    networks:
      - openclaw_net

  web:
    build: .
    command: uvicorn openclaw.gateway:app --host 0.0.0.0 --port 8000
    env_file: .env
    depends_on:
      - db
      - redis
    ports:
      - "8000:8000"
    networks:
      - openclaw_net

volumes:
  pgdata:
```

**Piège** : le réseau déclaré `external: true` nécessite qu’il existe déjà (`docker network create openclaw_net`). Si vous supprimez le réseau, le `docker compose up` échouera avec *network not found*.

### 1.6 Vérification du service  

```bash
# 1. Conteneurs actifs
docker ps --filter "name

---

## Module 2 — contenu

## 2.1 Modèle de communication interne  

| Composant | Technologie | Port | Direction | Format |
|-----------|--------------|------|------------|--------|
| **Gateway API** | gRPC (proto `gateway.proto`) | 50051 | Client → Gateway | Protobuf |
| **Scheduler** | gRPC (proto `scheduler.proto`) | 50052 | Gateway ↔ Scheduler | Protobuf |
| **Agents** | Redis Pub/Sub (channel `agent:{id}`) | 6379 | Scheduler → Agent (task) <br> Agent → Scheduler (ack) | JSON |
| **Cache** | Redis (key‑value) | 6379 | Tous | JSON / primitives |
| **DB** | PostgreSQL (SQLAlchemy) | 5432 | Tous | SQL |

*Flux typique*  

1. Un client envoie `ExecuteTaskRequest` via gRPC au **Gateway**.  
2. Le **Gateway** crée un objet `Task` (UUID, métadonnées) et le persiste en DB.  
3. Le **Gateway** publie le message `{"task_id":"…","script":"my_script.py"}` sur le canal `agent:dispatcher`.  
4. Le **DispatcherAgent** (agent 0) reçoit le message, sélectionne un **TaskAgent** disponible et publie `{"task_id":"…","script":"my_script.py","target":"agent:7"}` sur le canal correspondant.  
5. Le **TaskAgent** télécharge le script depuis le stockage partagé (`/opt/openclaw/scripts/`), le compile en sandbox Docker et le lance.  
6. À la fin, le **TaskAgent** publie `{"task_id":"…","status":"SUCCESS","result":"…"} → agent:gateway`.  
7. Le **Gateway** met à jour la DB, renvoie `ExecuteTaskResponse` au client.

### Point d’injection d’un script personnalisé  

- Tous les scripts sont montés dans le volume Docker `openclaw_scripts:/opt/openclaw/scripts`.  
- Le **DispatcherAgent** est le seul composant qui décide *où* (quel agent) un script sera exécuté.  
- Pour ajouter un script, il suffit de placer le fichier dans le volume et d’appeler l’API `ExecuteTask`. Aucun changement de code n’est requis tant que le script respecte le SDK.

---

## 2.2 Structure des agents  

```text
openclaw/
├─ agents/
│  ├─ base.py          # BaseAgent (abstract)
│  ├─ dispatcher.py    # DispatcherAgent (inherits BaseAgent)
│  ├─ task_agent.py    # TaskAgent (inherits BaseAgent)
│  └─ monitoring.py    # MonitoringAgent (inherits BaseAgent)
├─ plugins/
│  └─ *.py            # hooks exécutés par les agents
└─ hooks/
   └─ pre_exec.py     # hook exécuté avant chaque script
```

### 2.2.1 `BaseAgent` (extrait)

```python
# agents/base.py
import abc
import asyncio
import json
import os
import redis
import logging

logger = logging.getLogger(__name__)

class BaseAgent(abc.ABC):
    """Classe de base pour tous les agents OpenClaw."""
    CHANNEL_PREFIX = "agent:"

    def __init__(self, agent_id: str, redis_url: str = "redis://localhost:6379/0"):
        self.id = agent_id
        self.redis = redis.from_url(redis_url, decode_responses=True)
        self.channel = f"{self.CHANNEL_PREFIX}{self.id}"
        logger.info("Agent %s listening on %s", self.id, self.channel)

    async def run(self) -> None:
        """Boucle principale : écoute les messages et délègue."""
        pubsub = self.redis.pubsub()
        await pubsub.subscribe(self.channel)
        async for message in self._aioredis_iter(pubsub):
            if message["type"] != "message":
                continue
            payload = json.loads(message["data"])
            try:
                await self.handle_message(payload)
            except Exception as exc:
                logger.exception("Error handling %s", payload)
                await self.publish_error(payload, exc)

    @abc.abstractmethod
    async def handle_message(self, payload: dict) -> None:
        """Implémenté par chaque sous‑classe."""
        ...

    async def publish(self, target: str, data: dict) -> None:
        """Envoie un message JSON sur le canal target."""
        self.redis.publish(target, json.dumps(data))

    async def publish_error(self, original: dict, exc: Exception) -> None:
        err = {"task_id": original.get("task_id"), "status": "ERROR", "error": str(exc)}
        await self.publish(f"{self.CHANNEL_PREFIX}gateway", err)

    async def _aioredis_iter(self, pubsub):
        """Wrapper async pour redis‑py (bloquant) – à remplacer par aioredis en prod."""
        loop = asyncio.get_event_loop()
        while True:
            message = await loop.run_in_executor(None, pubsub.get_message, True, 1)
            if message:
                yield message
```

### 2.2.2 `DispatcherAgent`

```python
# agents/dispatcher.py
from .base import BaseAgent
import random

class DispatcherAgent(BaseAgent):
    """Répartit les tâches vers les agents de type TaskAgent."""
    TARGET_AGENTS = [f"task:{i}" for i in range(1, 6)]  # 5 workers

    async def handle_message(self, payload: dict) -> None:
        # 1️⃣ Validation minimale
        if "task_id" not in payload or "script" not in payload:
            raise ValueError("Invalid payload")
        # 2️⃣ Sélection du worker (round‑robin simplifié)
        target = random.choice(self

---

## Module 3 — contenu

## 3.1 API Python `openclaw.sdk`

| Élément | Description | Référence |
|--------|-------------|------------|
| `Task` | Objet représentant une exécution de script. Il possède les attributs `id: str`, `name: str`, `payload: dict`, `created_at: datetime`. | `openclaw.sdk.task.Task` |
| `Context` | Fournit l’accès aux services internes (DB, cache, logger). Instanci