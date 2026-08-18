# OpenClaw Gateway — 77 Agents et 961 scripts

> Référence `openclaw-gateway` · 99 €

## Plan

## Module 1 – Installation et configuration de l’environnement OpenClaw  
**Objectif mesurable :** Installer, configurer et vérifier le bon fonctionnement d’OpenClaw Gateway sur une machine Linux (Ubuntu 20.04 + Docker) en moins de 30 minutes.  
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
**Objectif mesurable :** Créer, tester et déployer un script complet (entrée, traitement, sortie) qui utilise au moins deux services internes, en moins de 45 minutes.  
**Notions couvertes**  
- API Python : `openclaw.sdk` – classes `Task`, `Context`, `Result`.  
- Gestion des entrées/sorties (`jsonschema` validation, `pydantic` models).  
- Utilisation des services internes : base de données (`db.session`), cache (`redis_client`).  
- Gestion des erreurs : `OpenClawException`, retries avec `tenacity`.  
- Tests unitaires avec `pytest` et simulation d’environnement (`fixtures/`).

## Module 4 – Orchestration avancée et optimisation des agents  
**Objectif mesurable :** Configurer une orchestration qui répartit les charges sur 5 nœuds, réduire le temps moyen d’exécution d’un script de 20 % grâce à la parallélisation.  
**Notions couvertes**  
- Paramétrage du scheduler (`celery` + `redis` broker).  
- Stratégies de répartition : round‑robin, poids dynamiques.  
- Profilage des scripts (`cProfile`, `py-spy`).  
- Optimisation du code : asynchronisme (`asyncio`), batch processing.  
- Monitoring avec Prometheus + Grafana (metrics `openclaw_task_duration_seconds`).

## Module 5 – Sécurité, conformité et mise en production  
**Objectif mesurable :** Appliquer le modèle de sécurité OpenClaw (sandbox, audit) et publier une version stable avec pipeline CI/CD complet en moins de 60 minutes.  
**Notions couvertes**  
- Sandbox Docker : limites de ressources (`--memory`, `--cpus`), user ns.  
- Gestion des permissions : RBAC dans `openclaw.yaml`, tokens JWT.  
- Audits de scripts : signatures SHA‑256, validation de provenance.  
- Pipeline CI/CD avec GitHub Actions (`build.yml

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
| `Context` | Fournit l’accès aux services internes (DB, cache, logger). Instancié par le moteur avant d’appeler le script. | `openclaw.sdk.context.Context` |
| `Result` | Retour du script. Doit être sérialisable JSON. Attributs `status: str` (`SUCCESS`, `FAILURE`), `data: dict`, `error: Optional[str]`. | `openclaw.sdk.result.Result` |
| `OpenClawException` | Base des exceptions levées par le SDK. Le moteur les capture et les transforme en `Result(status='FAILURE')`. | `openclaw.sdk.exceptions.OpenClawException` |
| `db.session` | SQLAlchemy `Session` déjà configuré (autocommit désactivé). | `openclaw.sdk.services.db.session` |
| `redis_client` | Instance `redis.Redis` configurée avec le pool du conteneur `redis`. | `openclaw.sdk.services.redis_client` |

### 3.1.1 Structure minimale d’un script

```python
# my_script.py
from openclaw.sdk import Task, Context, Result, OpenClawException
from pydantic import BaseModel, Field
import jsonschema
from tenacity import retry, stop_after_attempt, wait_exponential

# ----------------------------------------------------------------------
# 1️⃣ Modèle d’entrée – validation stricte avec Pydantic
# ----------------------------------------------------------------------
class InputModel(BaseModel):
    user_id: int = Field(..., gt=0, description="Identifiant interne de l’utilisateur")
    start_date: str = Field(..., regex=r'^\d{4}-\d{2}-\d{2}$')
    end_date: str = Field(..., regex=r'^\d{4}-\d{2}-\d{2}$')

# ----------------------------------------------------------------------
# 2️⃣ Schéma JSON (optionnel) – utilisé par le moteur pour la doc
# ----------------------------------------------------------------------
INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "user_id": {"type": "integer", "minimum": 1},
        "start_date": {"type": "string", "format": "date"},
        "end_date": {"type": "string", "format": "date"},
    },
    "required": ["user_id", "start_date", "end_date"],
    "additionalProperties": False,
}

# ----------------------------------------------------------------------
# 3️⃣ Fonction principale – signature imposée par le moteur
# ----------------------------------------------------------------------
def run(task: Task, ctx: Context) -> Result:
    """
    Entrée : `task.payload` (dict) conforme à INPUT_SCHEMA.
    Sortie : Result(status='SUCCESS', data={...}) ou Result(status='FAILURE', error=...)
    """
    try:
        # 3.1 Validation JSON Schema (double sécurité)
        jsonschema.validate(instance=task.payload, schema=INPUT_SCHEMA)

        # 3.2 Désérialisation Pydantic (conversion + contraintes supplémentaires)
        payload = InputModel(**task.payload)

        # 3.3 Accès DB avec gestion de transaction
        user = _fetch_user(payload.user_id, ctx)

        # 3.4 Lecture cache – retry exponentiel en cas de timeout Redis
        stats = _fetch_stats(payload, ctx)

        # 3.5 Construction du résultat métier
        data = {
            "user_name": user.name,
            "total_events": stats["count"],
            "period": {"from": payload.start_date, "to": payload.end_date},
        }
        return Result(status="SUCCESS", data=data)

    except (jsonschema.ValidationError, OpenClawException) as exc:
        # Le moteur intercepte uniquement OpenClawException, on l’enveloppe
        raise OpenClawException(str(exc))
    except Exception as exc:
        # Toute autre exception est transformée en échec générique
        return Result(status="FAILURE", error=str(exc))


# ----------------------------------------------------------------------
# 4️⃣ Helpers – isolés pour faciliter le test unitaire
# ----------------------------------------------------------------------
def _fetch_user(user_id: int, ctx: Context):
    """Retourne l’objet SQLAlchemy `User` ou lève OpenClawException."""
    from openclaw.models import User  # modèle interne du projet

    user = ctx.db.session.query(User).filter(User.id == user_id).first()
    if not user:
        raise OpenClawException(f"User {user_id} not found")
    return user


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.5, min=0.5, max=2))
def _fetch_stats(payload: InputModel, ctx: Context) -> dict:
    """Récupère les statistiques agrégées depuis Redis."""
    key = f"stats:{payload.user_id}:{payload.start_date}:{payload.end_date}"
    raw = ctx.redis_client.get(key)
    if raw is None:
        # Simuler un fallback DB si le cache est vide (exemple simplifié)
        raw = _fallback_db_stats(payload, ctx)
        # Stocker pour les prochains appels
        ctx.redis_client.setex(key, 300, json.dumps(raw))
    else:
        raw = json.loads(raw)
    return raw


def _fallback_db_stats(payload: InputModel, ctx: Context) -> dict:
    """Exemple de requête SQL brute – à remplacer par un ORM réel."""
    sql = """
        SELECT COUNT(*) AS cnt
        FROM events
        WHERE user_id = :uid
          AND event_ts BETWEEN :start AND :end
    """
    result = ctx.db.session.execute(
        sql,

---

## Module 4 — contenu

## 4.1 Paramétrage du scheduler : Celery + Redis broker  

| Élément | Valeur recommandée | Raison |
|--------|--------------------|--------|
| `broker_url` | `redis://redis:6379/0` | Redis est déjà utilisé par OpenClaw pour le Pub/Sub ; un seul serveur évite la duplication de composants. |
| `result_backend` | `redis://redis:6379/1` | Séparer les files de tâches et les résultats évite les collisions de clés. |
| `task_serializer` / `result_serializer` | `json` | Compatibilité avec les modèles `pydantic` et le schéma JSON des scripts. |
| `accept_content` | `['json']` | Empêche l’exécution de code non‑JSON (sécurité). |
| `worker_concurrency` | `auto` (ou `$(nproc)`) | Utiliser tous les cœurs du nœud, sauf si la charge mémoire est critique. |
| `task_acks_late` | `True` | Garantit le re‑queue en cas d’échec du worker. |
| `worker_prefetch_multiplier` | `1` | Limite le nombre de tâches pré‑chargées, évite le “burst” sur un seul agent. |

**`celeryconfig.py`** (déposé dans `openclaw/config/` ; importé par chaque worker) :

```python
# celeryconfig.py
broker_url = "redis://redis:6379/0"
result_backend = "redis://redis:6379/1"

task_serializer = "json"
result_serializer = "json"
accept_content = ["json"]

task_acks_late = True
worker_prefetch_multiplier = 1
worker_concurrency = None            # Celery utilise os.cpu_count() par défaut
task_time_limit = 300                # 5 min, protège contre les boucles infinies
task_soft_time_limit = 240
```

Dans le `docker-compose.yml` :

```yaml
services:
  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]
  celery_worker:
    build: .
    command: celery -A openclaw.scheduler worker -Q default,high,low --loglevel=INFO
    environment:
      - CELERY_CONFIG_MODULE=openclaw.config.celeryconfig
    depends_on: [redis, openclaw_gateway]
    deploy:
      replicas: 5                # 5 nœuds d’exécution
```

> **Note** : le tag `--loglevel=INFO` doit être remplacé par `DEBUG` uniquement lors du débogage, sinon le volume de logs surcharge le broker.

---

## 4.2 Stratégies de répartition  

### 4.2.1 Round‑Robin (par défaut)  

Celery distribue les tâches dans l’ordre d’arrivée sur les workers disponibles. Aucun paramètre supplémentaire n’est requis.  

### 4.2.2 Poids dynamiques  

Pour privilégier certains nœuds (ex. : machines avec GPU), définissez des **queues** avec des **routing keys** :

```python
# openclaw/scheduler/routing.py
from kombu import Queue

# Deux queues : "cpu" (poids 1) et "gpu" (poids 2)
CELERY_QUEUES = (
    Queue("cpu", routing_key="cpu"),
    Queue("gpu", routing_key="gpu"),
)

# Mapping des tâches vers les queues
CELERY_ROUTES = {
    "openclaw.tasks.compute_heavy": {"queue": "gpu", "routing_key": "gpu"},
    "openclaw.tasks.io_intensive": {"queue": "cpu", "routing_key": "cpu"},
}
```

Dans `celeryconfig.py` :

```python
from .routing import CELERY_QUEUES, CELERY_ROUTES

task_queues = CELERY_QUEUES
task_routes = CELERY_ROUTES
```

Les workers qui consomment la queue `gpu` sont lancés avec :

```bash
celery -A openclaw.scheduler worker -Q gpu --loglevel=INFO
```

### 4.2.3 Limitation de débit (rate‑limit)  

Pour éviter de saturer un service externe :

```python
@app.task(rate_limit="10/m")   # max 10 exécutions par minute
def call_external_api(payload):
    ...
```

---

## 4.3 Profilage des scripts  

### 4.3.1 `cProfile` intégré à la tâche  

```python
# openclaw/tasks/profiled.py
import cProfile
import pstats
import io
from openclaw.sdk import Task, Context, Result

@app.task(bind=True, name="openclaw.tasks.profiled")
def profiled_task(self, task_id: str):
    """Exécute un script OpenClaw en mode profilage."""
    task: Task = Context.get_task(task_id)

    pr = cProfile.Profile()
    pr.enable()
    try:
        result = task.run()                     # appel du script utilisateur
    finally:
        pr.disable()
        s = io.StringIO()
        ps = pstats.Stats(pr, stream=s).sort_stats("cumtime")
        ps.print_stats(10)                      # top‑10 fonctions
        # Persister le rapport dans Redis pour le monitoring
        redis_client.setex(f"profile:{task_id}", 86400, s.getvalue())
    return Result.success(result)
```

*Le rapport est consultable via l’API interne : `GET /metrics/profile/{task_id}`.*

### 4.3.2 `py-spy` en mode “attach”  

Déploiement d’un side‑car :

```yaml
services:
  pyspy:
    image: pyspy/pyspy:latest
    command: >
      py-sp

---

## Module 5 — contenu

## 5 – Sécurité, conformité et mise en production  

### 5.1 Sandbox Docker – isolation et limites de ressources  

| Élément | Valeur recommandée (production) | Raison |
|---------|----------------------------------|--------|
| **User** | `nonroot` (UID 1000) | Empêche l’escalade de privilèges depuis le conteneur. |
| **Mémoire** | `--memory=512m` / `--memory-swap=512m` | Limite la consommation et évite le OOM du nœud. |
| **CPU** | `--cpus=0.5` | Garantit que chaque script n’utilise pas plus d’un demi‑cœur. |
| **Network** | `--network=none` (sauf si le script accède explicitement à un service) | Réduit la surface d’attaque. |
| **Read‑only rootfs** | `--read-only` + volume `tmpfs:/tmp:rw` | Empêche l’écriture persistante hors du répertoire de travail. |
| **Seccomp profile** | `docker/default` ou profil custom minimal | Bloque les appels système non nécessaires. |
| **AppArmor** | `profile=openclaw-sandbox` | Restreint les capacités du conteneur. |

```bash
# Exemple de lancement d’un script dans le sandbox
docker run -d \
  --name oc_script_$(uuidgen) \
  --user 1000:1000 \
  --memory=512m --memory-swap=512m \
  --cpus=0.5 \
  --network=none \
  --read-only \
  --tmpfs /tmp:rw,noexec,nosuid,size=64m \
  --security-opt seccomp=./seccomp-profile.json \
  --security-opt apparmor=openclaw-sandbox \
  -e SCRIPT_ID=42 \
  -v /var/openclaw/scripts/42:/workspace:ro \
  openclaw/sandbox:latest \
  python /workspace/main.py
```

#### Pièges concrets  
* **Oubli du flag `--read-only`** → le script peut modifier le système de fichiers du conteneur et persister des artefacts.  
* **Montage en lecture‑écriture du répertoire `scripts/`** → un script compromis peut remplacer d’autres scripts. Utiliser `:ro`.  
* **Valeur CPU trop élevée** → un script malveillant peut monopoliser le CPU du nœud. Vérifier `docker stats` après chaque déploiement.  

---

### 5.2 Gestion des permissions – RBAC et JWT  

#### 5.2.1 Définition du modèle RBAC dans `openclaw.yaml`

```yaml
rbac:
  roles:
    - name: admin
      permissions: ["*"]
    - name: operator
      permissions:
        - task:read
        - task:execute
        - script:read
    - name: auditor
      permissions:
        - script:read
        - script:audit
  bindings:
    - user: alice@example.com
      role: admin
    - user: bob@example.com
      role: operator
    - group: auditors
      role: auditor
```

*Le serveur charge ce fichier au démarrage (`openclaw --config openclaw.yaml`).*  

#### 5.2.2 Génération et validation d’un token JWT  

```python
# token_utils.py
import jwt
import datetime
from pathlib import Path

SECRET_KEY = Path("/etc/openclaw/jwt_secret.key").read_text().strip()
ALGORITHM = "HS256"
EXPIRATION_MINUTES = 60

def create_token(user_id: str, role: str) -> str:
    now = datetime.datetime.utcnow()
    payload = {
        "sub": user_id,
        "role": role,
        "iat": now,
        "exp": now + datetime.timedelta(minutes=EXPIRATION_MINUTES),
        "iss": "openclaw-gateway"
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str) -> dict:
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM], issuer="openclaw-gateway")
```

*Points de vigilance*  
* Ne **jamais** stocker la clé secrète dans le dépôt Git. Utiliser un secret Docker/K8s.  
* Vérifier le champ `iss` et `exp` à chaque décodage.  
* Limiter le **scope** du token aux actions réellement nécessaires (ex. `task:execute`).  

---

### 5.3 Audits de scripts – signatures SHA‑256 et provenance  

1. **Signature à l’enregistrement**  

```bash
# Dans le répertoire scripts/
SCRIPT_ID=73
SCRIPT_PATH=./scripts/${SCRIPT_ID}/main.py
HASH=$(sha256sum ${SCRIPT_PATH} | cut -d' ' -f1)
echo "${HASH}  ${SCRIPT_ID}" >> ./scripts/manifest.sha256
```

2. **Vérification au moment du chargement**  

```python
# audit.py
import hashlib
from pathlib import Path

def verify_signature(script_id: int) -> bool:
    manifest = Path("./scripts/manifest.sha256")
    expected = None
    for line in manifest.read_text().splitlines():
        h, sid = line.split()
        if int(sid) == script_id:
            expected = h
            break
    if expected is None:
        raise FileNotFoundError(f"Signature for script {script_id} not found")
    script_path = Path(f"./scripts/{script_id}/main.py")
    actual = hashlib.sha256(script_path.read_bytes()).hexdigest()
    return actual == expected
```

*Pièges*  
* **Modification du manifest** → stocker le fichier `manifest.sha256` dans un dépôt Git signé (GPG) ou dans un artefact immutable (S3 versioning).  
* **Collision de hash** improbable avec SHA‑256