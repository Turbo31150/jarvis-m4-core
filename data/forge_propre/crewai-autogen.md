# CrewAI & AutoGen Multi-Agents

> Référence `crewai-autogen` · 79 €

## Plan

## Module 1 – Installation, configuration et premiers pas avec CrewAI & AutoGen  
**Objectif mesurable** : Installer les versions stables de CrewAI (≥ 0.4.0) et d’AutoGen (≥ 0.2.1), configurer un environnement virtuel Python 3.10 et lancer un script « Hello World » qui crée deux agents qui s’échangent un message.  
**Notions couvertes**  
- Gestion d’environnements virtuels (venv/conda) et dépendances via `pip` et `poetry`.  
- Structure du projet : répertoires `agents/`, `tools/`, `configs/`.  
- API de base de CrewAI : `Crew`, `Agent`, `Task`.  
- API de base d’AutoGen : `AssistantAgent`, `UserProxyAgent`, `GroupChat`.  
- Vérification d’intégrité : tests unitaires simples avec `pytest` et validation du fichier `requirements.txt`.

---

## Module 2 – Conception d’agents spécialisés et définition des rôles  
**Objectif mesurable** : Concevoir trois agents (extraction, synthèse, validation) avec des prompts paramétrés, les enregistrer dans le répertoire `agents/` et démontrer, via un test automatisé, que chaque agent produit une sortie conforme à un schéma JSON prédéfini.  
**Notions couvertes**  
- Prompt engineering avancé : utilisation de `system_prompt`, `user_prompt`, placeholders Jinja.  
- Gestion des contextes : `memory` (short‑term, long‑term) et `max_tokens`.  
- Création de classes dérivées `BaseAgent` pour encapsuler des outils spécifiques.  
- Validation de sortie : schémas JSON avec `pydantic` et `jsonschema`.  
- Enregistrement et récupération d’agents via le catalogue CrewAI (`Crew.register_agent`).

---

## Module 3 – Orchestration multi‑agents avec AutoGen GroupChat  
**Objectif mesurable** : Implémenter un `GroupChat` qui orchestre les trois agents du module 2, configurer les règles de routage (qui parle à qui et quand) et produire, à l’aide d’un script de test, un flux de conversation complet aboutissant à un document de synthèse validé.  
**Notions couvertes**  
- Construction de `GroupChat` : participants, `max_round`, `termination_condition`.  
- Stratégies de routage : `selector` basé sur le contenu du message (`regex`, `intent_classifier`).  
- Transmission de données entre agents : `Message.content`, `Message.metadata`.  
- Gestion des dead‑locks et des boucles infinies via `max_round` et `timeout`.  
- Enregistrement du chat (`GroupChat.save_history`) et relecture pour audit.

---

## Module 4 – Intégration d’outils externes et gestion des ressources  
**Objectif mesurable** : Ajouter deux outils (API REST et accès à une base de données SQLite) à l’agent d’extraction, les appeler depuis le groupe d’agents et vérifier, à

---

## Module 1 — contenu

## Module 1 – Installation, configuration et premiers pas avec CrewAI & AutoGen  

### 1.1 Gestion d’un environnement virtuel Python 3.10  

| Méthode | Commandes | Remarques |
|--------|-----------|-----------|
| **venv** (standard) | ```bash\npython3.10 -m venv .venv\nsource .venv/bin/activate   # Linux/macOS\n.venv\Scripts\activate      # Windows\n``` | `python3.10` doit pointer sur une version 3.10.x. |
| **conda** | ```bash\nconda create -n crewai python=3.10 -y\nconda activate crewai\n``` | Conda crée un environnement isolé avec son propre `pip`. |
| **poetry** (gestion de dépendances) | ```bash\npoetry env use $(which python3.10)\npoetry shell\n``` | Poetry crée et active automatiquement un venv. |

> **Piège** : ne pas **activer** l’environnement avant d’installer les paquets ; sinon les dépendances seront installées dans le Python global et les tests échoueront.

### 1.2 Installation des bibliothèques  

```bash
# Si vous utilisez pip directement
pip install "crewai>=0.4.0" "autogen>=0.2.1"

# Si vous utilisez poetry (recommandé pour la gestion de versions)
poetry add "crewai>=0.4.0" "autogen>=0.2.1"
```

- `crewai` : framework d’orchestration de tâches et de catalogage d’agents.  
- `autogen` : implémentation de *GroupChat* et d’agents conversationnels.  

### 1.3 Structure de projet recommandée  

```
my_crew_project/
├─ agents/          # Modules Python contenant les définitions d’agents
│   ├─ __init__.py
│   └─ hello_agent.py
├─ tools/           # Implémentations d’outils externes (APIs, DB, etc.)
│   └─ __init__.py
├─ configs/        # Fichiers YAML/JSON de configuration de crew & chat
│   └─ crew.yaml
├─ tests/           # Tests unitaires avec pytest
│   └─ test_hello.py
├─ requirements.txt
└─ main.py          # Point d’entrée du script « Hello World »
```

> **Piège** : ne pas placer les fichiers `__init__.py` dans les dossiers `agents/` et `tools/`. Sans eux, Python ne reconnaît pas les répertoires comme des packages et `import agents.hello_agent` échoue.

### 1.4 Fichier `requirements.txt` (verrouillage des versions)  

```text
crewai==0.4.2
autogen==0.2.3
pydantic==2.5.2
pytest==7.4.3
```

- Utilisez `pip freeze > requirements.txt` après l’installation pour capturer les versions exactes.
- Le test d’intégrité (section 1.7) compare le contenu du fichier avec les versions importées au runtime.

### 1.5 API de base de CrewAI  

```python
# agents/hello_agent.py
from crewai import Agent, Task, Crew

class HelloAgent(Agent):
    """Agent minimal qui renvoie le texte reçu."""
    def __init__(self):
        super().__init__(
            name="EchoAgent",
            role="Renvoie le message reçu",
            goal="Faire un simple écho",
            backstory="Créé pour les tests de base."
        )

    def run(self, input_text: str) -> str:
        # La méthode `run` est appelée par Crew lorsqu’une tâche lui est assignée.
        return f"ECHO : {input_text}"
```

### 1.6 API de base d’AutoGen  

```python
# agents/autogen_agents.py
from autogen import AssistantAgent, UserProxyAgent, GroupChat, Message

# Agent qui agit comme un assistant simple
assistant = AssistantAgent(name="AssistantEcho", system_message="Tu répètes tout ce qu’on te dit.")

# Proxy qui représente l’utilisateur (dans ce script, le script lui-même)
user = UserProxyAgent(name="UserProxy")

# Chat de groupe contenant les deux participants
group_chat = GroupChat(
    participants=[assistant, user],
    max_round=2,                # Limite le nombre d’échanges
    termination_condition=lambda chat: len(chat.history) >= 2
)

def echo_via_autogen(payload: str) -> str:
    """Envoie un message à l’assistant et récupère sa réponse."""
    # Le UserProxy envoie le message initial
    user.send(Message(content=payload))
    # Le groupe démarre le dialogue
    group_chat.run()
    # La réponse de l’assistant se trouve dans le dernier message du chat
    return group_chat.history[-1].content
```

### 1.7 Script « Hello World » combinant CrewAI & AutoGen  

```python
# main.py
import json
from crewai import Crew
from agents.hello_agent import HelloAgent
from agents.autogen_agents import echo_via_autogen

def main():
    # 1️⃣ Instanciation des agents
    crew_agent = HelloAgent()
    # 2️⃣ Définition d’une tâche CrewAI qui utilise l’agent
    task = crew_agent.create_task(
        description="Renvoie le texte fourni",
        input_vars=["payload"],
        output_vars=["echo"]
    )
    # 3️⃣ Création du crew (catalogue d’agents)
    crew = Crew(name="DemoCrew")
    crew.register_agent(crew_agent)

    # 4️⃣ Exécution de la tâche CrewAI
    crew_result = crew.run_task(task, payload="Bonjour CrewAI")

---

## Module 2 — contenu

## Module 2 – Conception d’agents spécialisés et définition des rôles  

### 2.1 Architecture du répertoire `agents/`

```
project/
├─ agents/
│  ├─ __init__.py
│  ├─ base_agent.py          # classe abstraite commune
│  ├─ extraction_agent.py
│  ├─ synthesis_agent.py
│  └─ validation_agent.py
├─ schemas/
│  └─ output_schema.py       # modèles Pydantic
├─ tests/
│  └─ test_agents.py
└─ pyproject.toml
```

*Tous les fichiers sont importables via le chemin du projet (`import agents.extraction_agent`).*  

---

### 2.2 Prompt engineering avancé  

CrewAI accepte deux champs de prompt :

* `system_prompt` : contexte permanent du LLM.  
* `user_prompt` : texte fourni à chaque appel.  

Les prompts peuvent être des **templates Jinja2**.  
Exemple :

```jinja
{# agents/extraction_agent.py – template Jinja #}
{% raw %}
SYSTEM:
Vous êtes un extracteur de données structuré. Vous devez renvoyer un JSON conforme au schéma {{ schema_name }}.

USER:
Voici le texte source :
{{ document }}

Extraire les champs suivants :
{{ fields | join(', ') }}
{% endraw %}
```

Le rendu se fait avec `jinja2.Environment().from_string(template).render(**variables)`.

---

### 2.3 Gestion du contexte (mémoire)  

CrewAI expose trois types de mémoire :

| Mémoire          | Durée | Usage typique |
|------------------|-------|---------------|
| `ShortTermMemory`| jusqu’à `max_round` du *Crew* | garder le dernier message du même agent |
| `LongTermMemory` | persistance sur disque (via `pickle` ou `sqlite`) | historiser les extractions pour éviter les doublons |
| `SessionMemory`  | durée de la session Python | partage de variables entre agents via `metadata` |

Dans les agents spécialisés on fixe :

```python
self.memory = ShortTermMemory(max_entries=5)
self.max_tokens = 1024          # limite LLM
```

---

### 2.4 Classe de base `BaseAgent`

```python
# agents/base_agent.py
from crewai import Agent
from jinja2 import Environment, BaseLoader
from typing import Dict, Any

class BaseAgent(Agent):
    """Classe mère pour les agents métiers.
    - charge un template Jinja depuis le même répertoire
    - expose `render_prompt` qui injecte les variables dynamiques
    - conserve une mémoire courte par défaut
    """

    template_name: str = ""          # à surcharger
    template_vars: Dict[str, Any] = {}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.env = Environment(loader=BaseLoader())
        self.memory = self.memory or ShortTermMemory(max_entries=10)

    def render_prompt(self, **extra) -> str:
        """Rendu du template Jinja en combinant `template_vars` et `extra`."""
        with open(self.template_path(), "r", encoding="utf-8") as f:
            tmpl = self.env.from_string(f.read())
        ctx = {**self.template_vars, **extra}
        return tmpl.render(**ctx)

    def template_path(self) -> str:
        import pathlib, inspect
        module_dir = pathlib.Path(inspect.getfile(self.__class__)).parent
        return str(module_dir / f"{self.template_name}.j2")
```

> **Vérifiable** : `BaseAgent` hérite de `crewai.Agent` (v0.4.0) et expose `self.memory` qui correspond à l’API officielle.

---

### 2.5 Agents spécialisés  

#### 2.5.1 ExtractionAgent  

```python
# agents/extraction_agent.py
from .base_agent import BaseAgent
from schemas.output_schema import ExtractionResult
import json

class ExtractionAgent(BaseAgent):
    name = "ExtractionAgent"
    role = "Extracteur de données structurées"
    template_name = "extraction_prompt"
    template_vars = {
        "schema_name": "ExtractionResult",
        "fields": ["title", "date", "author", "summary"]
    }

    def run(self, document: str) -> ExtractionResult:
        # 1️⃣ Rendu du prompt
        prompt = self.render_prompt(document=document)

        # 2️⃣ Appel du LLM (CrewAI utilise par défaut OpenAI)
        raw = self.llm.complete(prompt, max_tokens=self.max_tokens)

        # 3️⃣ Validation JSON via Pydantic
        try:
            data = json.loads(raw)
            return ExtractionResult(**data)
        except Exception as exc:
            raise ValueError(f"Extraction invalide : {exc}") from exc
```

#### 2.5.2 SynthesisAgent  

```python
# agents/synthesis_agent.py
from .base_agent import BaseAgent
from schemas.output_schema import S

---

## Module 3 — contenu

## 3.1. Principes de l’orchestration avec **AutoGen GroupChat**

| Concept | Description | Implémentation AutoGen |
|--------|-------------|-----------------------|
| **Participants** | Instances d’`AssistantAgent` (ou dérivées) qui échangent des messages. | `GroupChat(agents=[agent_extraction, agent_synthese, agent_validation])` |
| **max_round** | Nombre maximal de tours de dialogue (un « tour » = un message envoyé par un agent). | `max_round=20` |
| **termination_condition** | Fonction qui reçoit le dernier `Message` et indique si le chat doit s’arrêter. | `lambda msg: "FIN" in msg.content` |
| **selector / routing** | Décide quel agent doit répondre à chaque message. | `selector=RegexSelector(patterns={...})` ou `IntentClassifierSelector` |
| **Message** | Objet transportant `content`, `metadata` (ex. `source`, `timestamp`). | `Message(content="...", metadata={"source":"extraction"})` |
| **Dead‑lock** | Situation où aucun agent ne répond (ex. toutes les règles de routage renvoient `None`). | Géré par `max_round` et `timeout` (ex. `timeout=300` s). |
| **Sauvegarde / audit** | Historique complet sérialisé en JSON ou pickle. | `chat.save_history("history.json")` |

---

## 3.2. Mise en place du scénario de synthèse

### 3.2.1. Prérequis (agents déjà créés)

```python
# agents/extraction_agent.py
from crewai import Agent
from tools.api_client import RestAPIClient

class ExtractionAgent(Agent):
    def __init__(self):
        super().__init__(
            name="Extraction",
            role="Récupérer les données brutes depuis l’API REST",
            system_prompt="Tu es un agent d'extraction. Tu ne fais que des appels HTTP GET et renvoies du JSON.",
        )
        self.api = RestAPIClient(base_url="https://api.example.com")

    def run(self, query: str) -> dict:
        # Retourne le JSON brut
        return self.api.get("/data", params={"q": query})
```

```python
# agents/synthese_agent.py
from crewai import Agent
from pydantic import BaseModel

class SyntheseOutput(BaseModel):
    title: str
    summary: str
    keywords: list[str]

class SyntheseAgent(Agent):
    def __init__(self):
        super().__init__(
            name="Synthèse",
            role="Transformer le JSON brut en texte structuré",
            system_prompt="Tu reçois un JSON et tu produis un résumé conforme au schéma SyntheseOutput.",
        )

    def run(self, raw_json: dict) -> SyntheseOutput:
        # Implémentation fictive, le vrai LLM remplira le schéma
        return SyntheseOutput(
            title=raw_json["title"],
            summary=raw_json["content"][:200] + "...",
            keywords=raw_json.get("tags", [])[:5],
        )
```

```python
# agents/validation_agent.py
from crewai import Agent
from pydantic import ValidationError

class ValidationAgent(Agent):
    def __init__(self):
        super().__init__(
            name="Validation",
            role="Vérifier que le résumé respecte le schéma JSON et les contraintes métier",
            system_prompt="Tu reçois le résultat de Synthèse. Retourne 'OK' ou une description d’erreur.",
        )

    def run(self, synthese: dict) -> str:
        try:
            # Utilise le même modèle que SyntheseAgent pour validation
            from agents.synthese_agent import SyntheseOutput
            SyntheseOutput(**synthese)  # raise ValidationError si non conforme
            return "OK"
        except ValidationError as e:
            return f"Erreur de validation : {e}"
```

> **NB** : chaque classe hérite de `crewai.Agent` afin de pouvoir être enregistrée dans le catalogue CrewAI (`Crew.register_agent`).

### 3.2.2. Construction du **GroupChat** avec routage basé sur le contenu

```python
# group_chat/main.py
import json
from autogen import AssistantAgent, UserProxyAgent, GroupChat, Message
from autogen.selector import RegexSelector
from agents.extraction_agent import ExtractionAgent
from agents.synthese_agent import SyntheseAgent
from agents.validation_agent import ValidationAgent

# 1️⃣ Instanciation des agents AutoGen à partir des classes CrewAI
extraction = AssistantAgent(name="extraction", llm=ExtractionAgent())
synthese   = AssistantAgent(name="synthese",   llm=SyntheseAgent())
validation = AssistantAgent(name="validation", llm=ValidationAgent())

# 2️⃣ Définition du sélecteur de routage
#   - messages contenant "raw" → extraction
#   - messages contenant "summary" → synthese
#   - messages contenant "validation" → validation
selector = RegexSelector(
    patterns={
        "extraction": r"\braw\b",
        "synthese":   r"\bsummary\b",
        "validation": r"\bvalidation\b",
    },
    default_agent="extraction",  # fallback
)

# 3️⃣ Fonction de terminaison : on attend le token "FIN" dans le dernier message
def termination_condition(last_msg: Message) -> bool:
    return "FIN" in last_msg.content

# 4️⃣ Création du groupe de discussion
chat = GroupChat(
    agents=[extraction, synthese, validation],
    selector=selector,
    max_round=15,
    termination_condition=termination_condition,
    timeout=120,               # secondes
)

---

## Module 4 — contenu

## 4 – Intégration d’outils externes et gestion des ressources  

### 4.1. Principes d’intégration  

| Aspect | Description | Référence technique |
|--------|-------------|----------------------|
| **Abstraction** | Chaque outil est encapsulé dans une classe dérivée de `Tool` (CrewAI) ou `FunctionTool` (AutoGen) afin d’isoler les dépendances et de faciliter le test unitaire. | `crewai.tools.base.Tool` |
| **Contrat d’entrée / sortie** | Les fonctions doivent accepter et renvoyer des objets JSON sérialisables. Le schéma de sortie est validé avec `pydantic.BaseModel`. | `pydantic` v2.5 |
| **Gestion de la connexion** | Les connexions HTTP (via `httpx`) et SQLite (`sqlite3`) sont créées à l’instanciation de l’outil et fermées dans `__del__` ou via un context manager. | `httpx.AsyncClient`, `sqlite3.Connection` |
| **Limitation de débit** | Un décorateur `@rate_limiter(calls=5, period=60)` empêche plus de 5 appels par minute à l’API REST. | `asyncio.Semaphore` + `time.monotonic` |
| **Sécurité** | Les secrets (tokens, chemins de fichier) sont injectés depuis les variables d’environnement via `python-dotenv`. | `dotenv.load_dotenv` |

---

### 4.2. Implémentation de l’outil **REST API**  

```python
# agents/tools/rest_extractor.py
import os
import json
import httpx
import asyncio
from typing import Any, Dict
from crewai.tools.base import Tool
from pydantic import BaseModel, ValidationError, Field
from dotenv import load_dotenv

load_dotenv()  # charge .env dans os.environ

# ----------------------------------------------------------------------
# Schéma de réponse attendu de l’API (exemple : recherche d’articles)
# ----------------------------------------------------------------------
class Article(BaseModel):
    id: int
    title: str = Field(..., min_length=1)
    abstract: str
    url: str

class ApiResponse(BaseModel):
    total: int
    items: list[Article]

# ----------------------------------------------------------------------
# Décorateur de limitation de débit (5 appels / minute)
# ----------------------------------------------------------------------
def rate_limiter(calls: int, period: int):
    semaphore = asyncio.Semaphore(calls)
    reset_time = asyncio.Event()

    async def wrapper(fn):
        async def inner(*args, **kwargs):
            async with semaphore:
                result = await fn(*args, **kwargs)
                # déclenche le reset après `period` secondes
                if semaphore._value == calls - 1:  # première acquisition
                    asyncio.get_event_loop().call_later(
                        period, reset_time.set
                    )
                await reset_time.wait()
                semaphore.release()
                return result
        return inner
    return wrapper

# ----------------------------------------------------------------------
# Classe d’outil
# ----------------------------------------------------------------------
class RestArticleExtractor(Tool):
    """
    Appelle l’API publique `https://api.example.com/articles?q={query}`.
    Retourne un dictionnaire conforme à `ApiResponse`.
    """

    name = "RestArticleExtractor"
    description = "Récupère les articles pertinents depuis l’API REST."

    def __init__(self):
        self.base_url = os.getenv("API_BASE_URL", "https://api.example.com")
        self.api_key = os.getenv("API_KEY")
        self.client = httpx.AsyncClient(timeout=10.0)

    @rate_limiter(calls=5, period=60)
    async def _call_api(self, query: str) -> Dict[str, Any]:
        headers = {"Authorization": f"Bearer {self.api_key}"}
        url = f"{self.base_url}/articles"
        params = {"q": query}
        response = await self.client.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()

    async def run(self, query: str) -> Dict[str, Any]:
        """
        Méthode appelée par CrewAI / AutoGen.
        """
        raw = await self._call_api(query)
        try:
            validated = ApiResponse(**raw)
        except ValidationError as exc:
            raise ValueError(f"Réponse API invalide : {exc}") from exc
        # Retourne un dict sérialisable (pydantic .dict())
        return validated.dict()

    async def __aexit__(self, exc_type, exc, tb):
        await self.client.aclose()

    # Compatibilité avec le protocole sync de CrewAI (facultatif)
    def __call__(self, query: str) -> Dict[str, Any]:
        return asyncio.run(self.run(query))
```

#### Points d’attention  

1. **Async vs sync** – CrewAI invoque les outils de façon synchrone par défaut. Le wrapper `__call__` utilise `asyncio.run`; ne pas appeler `run` depuis un événement déjà en cours (`RuntimeError: Event loop is closed`).  
2. **Gestion des erreurs HTTP** – `response.raise_for_status()` lève `httpx.HTTPStatusError`. Capturez-le dans le code appelant pour éviter la rupture du `GroupChat`.  
3. **Expiration du token** – Si le token a une durée de vie, implémentez un rafraîchissement dans `__init__` ou via un décorateur `@refresh_token`.  

---

### 4.3. Implémentation de l’outil **SQLite**  

```python
# agents/tools/sql_extractor.py
import os
import sqlite3
from typing import List, Dict, Any
from crewai.tools.base import Tool
from pydantic import BaseModel, Field, ValidationError

# ----------------------------------------------------------------------
# Schéma de la table `documents`
# ----------------------------------------------------------------------
class DocumentRecord(BaseModel):
    doc_id: int

---

## Module 5 — contenu

## Module 5 – Déploiement, monitoring et optimisation des pipelines multi‑agents

---

### 5.1. Architecture de production recommandée

| Composant | Rôle | Technologies compatibles |
|-----------|------|---------------------------|
| **Environnement d’exécution** | Isolation, reproducibilité | `venv`, `conda`, `poetry` |
| **Conteneurisation** | Portabilité, scaling | Docker (≥ 20.10) |
| **Orchestrateur** | Gestion du scaling, résilience | Kubernetes, Docker‑Compose (dev) |
| **Interface d’appel** | Exposer le crew comme service | FastAPI, Flask, Quart |
| **Gestion des secrets** | Stockage sécurisé des clés API | `dotenv`, HashiCorp Vault, Kubernetes Secrets |
| **Logging & tracing** | Débogage, audit, métriques | `structlog`, OpenTelemetry, Prometheus‑Grafana |
| **Cache** | Réduction du nombre d’appels LLM | `redis`, `diskcache` |
| **Circuit‑breaker / retry** | Tolérance aux pannes d’API | `tenacity`, `aiobreaker` |
| **CI/CD** | Tests automatisés, déploiement continu | GitHub Actions, GitLab CI, Azure Pipelines |

---

### 5.2. Conteneurisation d’un crew complet

#### 5.2.1. Structure du projet (exemple)

```
my_crew/
├─ agents/
│   ├─ extraction_agent.py
│   ├─ synthesis_agent.py
│   └─ validation_agent.py
├─ tools/
│   ├─ api_client.py
│   └─ db_accessor.py
├─ configs/
│   └─ crew_config.yaml
├─ app/
│   └─ main.py          # FastAPI entry point
├─ tests/
│   └─ test_crew.py
├─ Dockerfile
├─ pyproject.toml
└─ .env.example
```

#### 5.2.2. Dockerfile (commenté)

```Dockerfile
# ---- Étape 1 : construction de l'environnement ----
FROM python:3.10-slim AS builder

# Variables d'environnement utiles
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VERSION=1.7.1

# Installation de Poetry (gestionnaire de dépendances)
RUN pip install "poetry==$POETRY_VERSION"

# Copie du fichier de dépendances
WORKDIR /app
COPY pyproject.toml poetry.lock ./

# Installation en mode « no‑dev » pour réduire la taille finale
RUN poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi --only main

# ---- Étape 2 : runtime ----
FROM python:3.10-slim

# Copie du runtime depuis le builder
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /app /app

WORKDIR /app

# Ajout du répertoire contenant les agents et la config
COPY agents/ agents/
COPY tools/ tools/
COPY configs/ configs/
COPY app/ app/

# Exposition du port FastAPI (par défaut 8000)
EXPOSE 8000

# Variable d'environnement pour le mode production
ENV ENV=production

# Commande d’entrée : serveur Uvicorn avec rechargement désactivé
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### 5.2.3. `docker-compose.yml` (développement)

```yaml
version: "3.9"
services:
  crew-api:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env
    volumes:
      - ./agents:/app/agents:ro
      - ./tools:/app/tools:ro
      - ./configs:/app/configs:ro
    restart: unless-stopped
```

---

### 5.3. API FastAPI qui déclenche le crew

```python
# app/main.py
import os
import asyncio
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from crewai import Crew, Agent, Task
from crewai.memory import SimpleMemory
from crewai.tools import BaseTool
from tenacity import retry, stop_after_attempt, wait_exponential
import structlog

logger = structlog.get_logger()

# -------------------------------------------------
# Modèles de requête / réponse
# -------------------------------------------------
class ExtractionRequest(BaseModel):
    query: