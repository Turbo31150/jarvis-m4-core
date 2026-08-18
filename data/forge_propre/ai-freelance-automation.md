# AI Freelance & LinkedIn Automation

> Référence `ai-freelance-automation` · 59 €

## Plan

## Module 1 – Architecture d’une solution d’automatisation LinkedIn avec IA  
**Objectif mesurable** : Concevoir et déployer un pipeline complet (scraping, enrichissement, actions) fonctionnant sur un compte LinkedIn professionnel dans un délai court.  
**Notions couvertes**  
1. Modélisation des flux de données (ETL) appliquée aux API LinkedIn et aux services de NLP.  
2. Gestion des quotas et des limites d’appels API (rate‑limiting, back‑off).  
3. Conteneurisation (Docker) et orchestration légère (Docker‑Compose) d’un environnement d’automatisation.  
4. Sécurisation des secrets (dotenv, HashiCorp Vault) dans le contexte de scripts d’automatisation.  
5. Monitoring basique (logs, métriques) avec Prometheus / Grafana ou alternatives légères.

## Module 2 – Extraction et structuration de profils LinkedIn  
**Objectif mesurable** : Implémenter un scraper fiable qui récupère la majorité des champs clés (nom, poste, entreprise, compétences) d’un profil public sans déclencher de blocage.  
**Notions couvertes**  
1. Utilisation de Selenium / Playwright avec gestion de cookies et de captchas.  
2. Analyse du DOM LinkedIn et définition de sélecteurs résilients (XPath, CSS).  
3. Techniques de rotation d’IP et de user‑agent (proxy résidentiel, services de rotation).  
4. Normalisation des données brutes (schema JSON‑LD, validation avec JSON‑Schema).  
5. Stockage initial dans une base NoSQL (MongoDB) ou fichier Parquet pour le traitement ultérieur.

## Module 3 – Enrichissement de données par IA générative  
**Objectif mesurable** : Produire, à partir d’un profil brut, un résumé concis et une petite liste d’arguments de prise de contact pertinents, avec une pertinence évaluée positivement par un jeu de validation interne.  
**Notions couvertes**  
1. Prompt engineering pour GPT‑4 (ou modèle open‑source équivalent) afin d’obtenir des résumés et des accroches.  
2. Chaînage de prompts (Chain‑of‑Thought) pour extraire compétences et besoins spécifiques.  
3. Gestion des coûts d’API (batching, caching des réponses).  
4. Évaluation de la qualité de sortie (BLEU, ROUGE, métriques sémantiques).  
5. Intégration du modèle dans le pipeline via LangChain ou un wrapper maison.

## Module 4 – Automation des actions de connexion et de messagerie  
**Objectif mesurable** : Déployer un bot qui envoie automatiquement des invitations personnalisées chaque jour, avec un taux d’acceptation cible sur un segment de prospects défini.  
**Notions couvertes**  
1. Construction de scénarios d’interaction (invite → message de suivi) avec des délais aléatoires pour éviter les patterns détectables.  
2. Utilisation de l’API LinkedIn (v2) ou de l’automatisation UI pour les actions non exposées.  
3. Gestion des réponses entrantes (webhooks, polling) et déclenchement de séquences de suivi.  
4. Implémentation de règles de conformité (RG).
---

## Module 1 — contenu

## 1. Modélisation des flux de données (ETL) appliquée aux API LinkedIn et aux services de NLP  

| Étape | Description technique | Artefact produit |
|------|------------------------|------------------|
| **Extract** | - appel HTTP GET vers `https://api.linkedin.com/v2/people/(id)` <br> - pagination via `start` / `count` <br> - décodage JSON → dictionnaire Python | `raw_profile.json` (ou objet en mémoire) |
| **Transform** | - normalisation des champs (ex. `firstName.localized.en_US`) <br> - enrichissement : appel à l’API de génération de texte (OpenAI, Cohere…) avec un prompt de résumé <br> - validation JSON‑Schema (`profile_schema.json`) | `profile_enriched.json` |
| **Load** | - insertion dans MongoDB (`profiles` collection) <br> - écriture d’un fichier Parquet (`profiles.parquet`) pour le batch downstream | Persistance durable |

> **Note** : le pipeline doit être **idempotent**. Chaque exécution doit pouvoir reprendre depuis l’étape déjà réalisée (ex. en vérifiant la présence du fichier `raw_profile.json`).

### 1.1 Exemple de schéma JSON‑Schema (validation)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "LinkedInProfile",
  "type": "object",
  "required": ["id", "firstName", "lastName", "headline", "summary"],
  "properties": {
    "id": { "type": "string" },
    "firstName": { "type": "string" },
    "lastName": { "type": "string" },
    "headline": { "type": "string" },
    "summary": { "type": "string" },
    "skills": {
      "type": "array",
      "items": { "type": "string" }
    },
    "ai_summary": { "type": "string" }
  }
}
```

---

## 2. Gestion des quotas et des limites d’appels API  

| API | Limite typique* | Stratégie de mitigation |
|-----|----------------|--------------------------|
| LinkedIn (v2) | 100 requêtes / heure (développeur) | - **Token bucket** implémenté avec `ratelimit` <br> - back‑off exponentiel (`time.sleep(2**retry)`) <br> - rafraîchissement du token OAuth 2.0 avant expiration |
| OpenAI (GPT‑4) | 60 req / minute (pay‑as‑you‑go) | - **batching** : regrouper 5 profiles avant appel <br> - **caching** : `functools.lru_cache` sur le prompt + profil hash |

\*Les quotas varient selon le contrat. Vérifier dans le tableau de bord développeur.

### 2.1 Code Python de gestion du rate‑limiting

```python
import time
import requests
from ratelimit import limits, sleep_and_retry

# 100 appels LinkedIn par heure → 1 appel toutes les 36 s en moyenne
CALLS = 100
PERIOD = 3600  # seconds

@sleep_and_retry
@limits(calls=CALLS, period=PERIOD)
def linkedin_get(url: str, headers: dict) -> dict:
    """Effectue un GET LinkedIn en respectant le quota."""
    resp = requests.get(url, headers=headers, timeout=10)
    if resp.status_code == 429:          # dépassement de quota
        retry_after = int(resp.headers.get("Retry-After", "60"))
        time.sleep(retry_after)
        raise Exception("Rate limit exceeded, retrying")
    resp.raise_for_status()
    return resp.json()
```

---

## 3. Conteneurisation (Docker) et orchestration légère (Docker‑Compose)

### 3.1 Architecture des conteneurs

```
┌─────────────────────┐
│  prometheus (metrics)│
└─────────▲───────────┘
          │
┌─────────┴───────────┐
│  etl_worker (Python) │   ← expose /metrics on 8000
└─────────▲───────────┘
          │
┌─────────┴───────────┐
│  mongodb (data store)│
└─────────────────────┘
```

### 3.2 Dockerfile du worker

```dockerfile
# syntax=docker/dockerfile:1
FROM python:3.11-slim

# 1️⃣ Installation des dépendances système
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc && \
    rm -rf /var/lib/apt/lists/*

# 2️⃣ Copie du code source
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ .

# 3️⃣ Variables d’environnement (définies dans .env, injectées par compose)
ENV PYTHONUNBUFFERED=1

# 4️⃣ Point d’entrée
CMD ["python", "-m", "worker"]
```

### 3.3 docker‑compose.yml (version 3.8)

```yaml
version: "3.8"

services:
  mongodb:
    image: mongo:7


---

## Module 2 — contenu

## Module 2 – Extraction et structuration de profils LinkedIn  

### 2.1 Architecture du scraper  

| Composant | Rôle | Implémentation typique |
|-----------|------|------------------------|
| **Navigateur headless** | Exécuter le JavaScript du site, charger le DOM complet. | Playwright (Python/Node) ou Selenium + Chrome/Chromium headless. |
| **Gestion des cookies & session** | Conserver la connexion LinkedIn et éviter le re‑login à chaque run. | `context.add_cookies()` (Playwright) ou `driver.add_cookie()` (Selenium). |
| **Rotation d’IP / User‑Agent** | Limiter le risque de blocage par le système anti‑bot de LinkedIn. | Proxy résidentiel (ex. : Luminati, Smartproxy) + liste d’UA aléatoires. |
| **Détection & mitigation de CAPTCHA** | Identifier les challenges et les résoudre ou suspendre le run. | Analyse du texte « captcha », appel à un service de résolution (2Captcha) ou mise en pause manuelle. |
| **Extraction du DOM** | Sélectionner les champs requis de façon résiliente. | Sélecteurs CSS/XPath basés sur `data-test-id` ou `aria-label`. |
| **Normalisation & validation** | Convertir le HTML brut en JSON‑LD conforme au schéma `Person`. | `jsonschema` + schéma JSON‑LD officiel. |
| **Persistance** | Stocker les documents bruts ou normalisés. | MongoDB (`collection.insert_one`) ou fichiers Parquet via `pyarrow`. |

---

### 2.2 Analyse du DOM LinkedIn (exemple de profil public)

```html
<div class="pv-top-card--list">
  <h1 class="text-heading-xlarge">John Doe</h1>
  <div class="text-body-medium break-words">Senior Data Scientist at Acme Corp</div>
</div>

<section id="experience-section">
  <ul>
    <li class="pv-entity__position-group-pager">
      <h3 class="t-16 t-black t-bold">Data Scientist</h3>
      <p class="pv-entity__secondary-title">Acme Corp</p>
      <span class="pv-entity__date-range">
        <span class="visually-hidden">Dates Employed</span>
        <time datetime="2019-01-01">Jan 2019 – Present</time>
      </span>
    </li>
    …
  </ul>
</section>

<section id="skill-section">
  <ul class="pv-skill-categories-section">
    <li class="pv-skill-category-entity">
      <span class="pv-skill-category-entity__name">Machine Learning</span>
    </li>
    …
  </ul>
</section>
```

**Observations vérifiables**  

* Les titres de poste sont dans `h3.t-16.t-black.t-bold`.  
* Le nom complet est toujours dans `h1.text-heading-xlarge`.  
* Les expériences sont encapsulées sous `section#experience-section`.  
* Les compétences sont listées sous `section#skill-section` → `span.pv-skill-category-entity__name`.  

Ces sélecteurs sont **résilients** parce qu’ils reposent sur des classes générées par le système de design de LinkedIn (`t-16`, `pv-entity__...`) qui changent rarement, contrairement aux index numériques.

---

### 2.3 Exemple de code complet (Playwright + Python)

> **Pré‑requis**  
> * Python ≥ 3.9  
> * `playwright` (`pip install playwright && playwright install`)  
> * `pymongo` (`pip install pymongo`)  
> * Un fichier `.env` contenant `LINKEDIN_EMAIL`, `LINKEDIN_PASSWORD`, `MONGO_URI`, `PROXY_URL` (optionnel).  

```python
# scraper_linkedin.py
import os
import json
import random
import asyncio
from pathlib import Path
from typing import List, Dict

from dotenv import load_dotenv
from pymongo import MongoClient
from playwright.async_api import async_playwright

load_dotenv()  # charge .env dans os.environ

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
EMAIL = os.getenv("LINKEDIN_EMAIL")
PASSWORD = os.getenv("LINKEDIN_PASSWORD")
MONGO_URI = os.getenv("MONGO_URI")
PROXY_URL = os.getenv("PROXY_URL")  # ex: http://user:pass@proxy:3128
USER_AGENTS = [
    # quelques UA courants, on en tire au hasard à chaque session
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_5_2) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.15",
    # …
]

# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------
def build_mongo_client() -> MongoClient:
    return MongoClient(MONGO_URI)

def normalize_profile(raw: Dict) -> Dict:
    """Convertit le dict brut en JSON‑LD conforme au schéma Person."""
    # schéma minimal, extensible
    return {
        "@context": "https://schema.org",
        "@type": "Person",
        "name": raw.get("name"),
        "jobTitle": raw.get("headline"),
        "worksFor": {"@type": "Organization", "name": raw


---

## Module 3 — contenu

## Module 3 – Enrichissement de données par IA générative  

### 3.1 Prompt engineering pour GPT‑4 (ou modèle open‑source équivalent)

| Étape | Action | Détail technique vérifiable |
|------|--------|-----------------------------|
| 1. | Définir le **system prompt** | `You are a concise professional copywriter. Generate a 150‑200 word summary and 5 outreach arguments for a LinkedIn prospect. Use a neutral tone.` |
| 2. | Définir le **user prompt** | Inclure les champs du profil sous forme de JSON structuré. Exemple : <br>`{ "name": "Alice Dupont", "title": "Senior Data Engineer", "company": "TechCorp", "skills": ["Python", "Airflow", "Data Lake"], "experience": "5 years in data pipeline design", "education": "M.Sc. Computer Science" }` |
| 3. | Utiliser **few‑shot** (exemples) | Ajouter quelques exemples de sortie dans le même appel afin de contraindre le format. |
| 4. | Limiter le nombre de tokens | Le modèle GPT‑4‑turbo (2024‑08) accepte un grand nombre de tokens ; garder le prompt suffisamment court pour laisser de la marge aux réponses. |
| 5. | Spécifier le **output schema** | `{"summary":"…","outreach_args":["…","…","…","…","…"]}`. La validation se fait ensuite avec JSON‑Schema. |

> **Vérifiable** : la documentation OpenAI indique que le paramètre `response_format={"type":"json_object"}` force le modèle à renvoyer un JSON valide (OpenAI API v1, 2024‑03).  

### 3.2 Chaînage de prompts (Chain‑of‑Thought)  

1. **Étape 1 – Extraction des compétences**  
   ```python
   prompt = f"""Extract the list of hard skills from the following profile JSON and return them as a JSON array.\n{profile_json}"""
   response = client.chat.completions.create(
       model="gpt-4o-mini",
       messages=[{"role":"system","content":"You output only JSON."},
                 {"role":"user","content":prompt}],
       response_format={"type":"json_object"}
   )
   skills = json.loads(response.choices[0].message.content)["skills"]
   ```
2. **Étape 2 – Génération du résumé** (en incluant les `skills` extraites)  
3. **Étape 3 – Construction des arguments** (en s’appuyant sur le résumé et les compétences).  

Le chain‑of‑thought augmente la pertinence : chaque sous‑tâche possède son propre prompt, ce qui réduit les hallucinations liées à la surcharge d’informations.

### 3.3 Gestion des coûts d’API  

| Technique | Implémentation concrète | Impact chiffré (exemple) |
|-----------|------------------------|--------------------------|
| **Batching** | Regrouper plusieurs profils dans un même appel en utilisant le paramètre `messages` avec plusieurs `user` messages. | Réduction du coût de tokenisation. |
| **Caching** | Mémoire locale (Redis) : clé = hash SHA‑256 du JSON du profil, valeur = réponse complète. | Évite les appels répétés et génère des économies. |
| **Limite de débit** | `time.sleep(...)` entre les appels pour rester sous la limite officielle de l’API. | Conformité aux SLA d’OpenAI, évite les erreurs de dépassement de quota. |

### 3.4 Évaluation de la qualité de sortie  

| Métrique | Calcul | Bibliothèque Python |
|----------|--------|----------------------|
| **ROUGE‑L** (longest common subsequence) | Compare le résumé généré à un *reference* rédigé par un humain. | `rouge_score.rouge_scorer.RougeScorer(['rougeL'], use_stemmer=True)` |
| **BLEU** (n‑gram) | Mesure la similarité du texte d’argumentation. | `nltk.translate.bleu_score.sentence_bleu` |
| **Embedding‑based semantic similarity** | Cosine similarity entre l’embedding du texte généré et celui du texte de référence (model `text-embedding-ada-002`). | `openai.embeddings.create` + `numpy.dot` |
| **Taux de validité JSON** | `jsonschema.validate` contre le schema défini. | `jsonschema` |

Un seuil de pertinence est atteint lorsque les métriques clés sont satisfaites simultanément :  
- ROUGE‑L atteint un niveau élevé,  
- La similarité sémantique est forte,  
- La validation JSON réussit.  

### 3.5 Intégration du modèle dans le pipeline  

#### 3.5.1 Exemple avec LangChain (v0.2)

```python
# file: pipeline/enrichment.py
import os, json, hashlib, time
import redis
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.schema import StrOutputParser
from langchain.schema.runnable import RunnableLambda

# pause between calls to respect rate limits
# time.sleep(...)  

# ... reste du code d'intégration ...
```
---

## Module 4 — contenu

## Module 4 – Automation des actions de connexion et de messagerie  

### 4.1 Construction de scénarios d’interaction  

| Étape | Description technique | Implémentation concrète |
|------|------------------------|------------------------|
| 1️⃣ Sélection du segment | Filtrage dans la base (MongoDB/Parquet) → liste de `profile_id` et de métadonnées (poste, secteur, localisation). | ```python<br>prospects = db.profiles.find({"seniority": {"$in": ["Senior", "Manager"]}, "location": "Paris"})<br>``` |
| 2️⃣ Génération du texte d’invitation | Prompt GPT‑4 : *« Rédige un message d’invitation de 300 caractères à {first_name} qui travaille chez {company} en tant que {title}. »* → cache résultat dans Redis (TTL = 24 h). | ```python<br>cache_key = f"invite:{profile_id}"<br>msg = redis.get(cache_key) or generate_msg(profile)…``` |
| 3️⃣ Envoi de l’invitation | Utilisation de l’API LinkedIn (v2) lorsqu’elle supporte `invitations`. Sinon, fallback UI via Playwright. | ```python<br>if api_token: send_via_api(profile_id, msg) else: send_via_ui(profile_url, msg)<br>``` |
| 4️⃣ Gestion du timing | Ajout d’un délai aléatoire **uniforme** entre 30 s et 180 s. Après chaque 10 invitations, pause de 5 min. | ```python<br>time.sleep(random.uniform(30, 180))<br>if i % 10 == 0: time.sleep(300)<br>``` |
| 5️⃣ Enregistrement du statut | Table `invites_log` : `profile_id`, `sent_at`, `msg_hash`, `status` (`sent`, `error`, `duplicate`). | ```python<br>log_collection.insert_one({...})<br>``` |

#### Pourquoi ces choix ?  

* **Délais aléatoires** : LinkedIn détecte les intervalles fixes (ex. 30 s constant) via les métriques de “behavioral biometrics”.  
* **Batching + cache** : chaque appel GPT‑4 coûte ~0,03 USD / 1 000 tokens. En cachant le message par profil on évite les appels répétés.  
* **Fallback UI** : l’API ne permet pas d’envoyer un message de suivi avant que la connexion soit acceptée. La couche UI (Playwright) peut envoyer le premier message dans la même session d’invitation, mais elle doit être isolée dans un conteneur dédié pour éviter les fuites de cookies.

---

### 4.2 Utilisation de l’API LinkedIn (v2)  

| Endpoint | Méthode | Payload minimal | Réponse attendue |
|----------|---------|------------------|-------------------|
| `/v2/invitations` | `POST` | ```json<br>{ "invitee": { "com.linkedin.voyager.dash.invitation.InviteeProfile": { "profileId": "ACoAA..." } }, "message": "Bonjour {first_name}, …" }<br>``` | `201 Created` avec `{ "entityUrn": "urn:li:invitation:12345" }` |
| `/v2/invitations/{invitationId}` | `GET` | – | Statut (`PENDING`, `ACCEPTED`, `REVOKED`) |

**Authentification** : OAuth 2.0 Bearer token. Le token doit être stocké dans un secret manager (ex. HashiCorp Vault) et injecté via `dotenv` :

```python
import os, requests
TOKEN = os.getenv("LI_TOKEN")
headers = {"Authorization": f"Bearer {TOKEN}", "X-Restli-Protocol-Version": "2.0.0"}
```

**Gestion du rate‑limit** : LinkedIn renvoie `429 Too Many Requests` avec l’en‑tête `X-RateLimit-Reset`. Implémentation d’un back‑off exponentiel :

```python
def call_api(url, json_body):
    for attempt in range(5):
        r = requests.post(url, json=json_body, headers=headers)
        if r.status_code == 429:
            wait = int(r.headers.get("X-RateLimit-Reset", 60))
            time.sleep(wait * (2 ** attempt))
            continue
        r.raise_for_status()
        return r.json()
    raise RuntimeError("Rate limit exceeded after retries")
```

---

### 4.3 Fallback UI avec Playwright  

> **Pré‑requis** : Playwright ≥ 1.35, Chromium, session LinkedIn pré‑authentifiée (`cookies.json`).  

```python
import json, random, time
from playwright.sync_api import sync_playwright

def load_cookies(page):
    with open("cookies.json") as f:
        for cookie in json.load(f):
            page.context.add_cookies([cookie])

def send_invite_via_ui(profile_url: str, message: str):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)          # headless=False facilite le debug
        context = browser.new_context()
        page =


---

## Module 5 — contenu

## Module 5 – Analyse des performances, optimisation et conformité  

### 5.1. Indicateurs clés de performance (KPI) pour l’automatisation LinkedIn  

| KPI | Formule | Source de donnée | Pourquoi c’est utile |
|-----|---------|------------------|----------------------|
| **Taux d’invitation envoyée** | `Invitations envoyées / Prospects ciblés` | Logs d’envoi (MongoDB / PostgreSQL) | Mesure le respect du cadence définie (ex : 30/jour). |
| **Taux d’acceptation** | `Invitations acceptées / Invitations envoyées` | Webhook + API `/connections` | Indicateur de pertinence du message d’invitation. |
| **Taux de réponse** | `Messages reçus / Invitations acceptées` | Webhook + API `/messaging/conversations` | Qualité du suivi et pertinence du pitch. |
| **Taux de conversion** | `Leads qualifiés / Invitations acceptées` | Tag `lead` dans la base | Retour sur investissement de la séquence. |
| **Coût moyen par lead (CPL)** | `Coût total API + Proxy / Leads qualifiés` | Facturation API + logs de dépenses | Optimisation budgétaire. |
| **Temps moyen de réponse** | `Σ (timestamp réponse – timestamp acceptation) / Nombre de réponses` | Timestamps des événements | Détecte les goulots d’attente. |

> **Vérifiable** : les formules sont des ratios simples calculés à partir de champs stockés dans les collections MongoDB `scrape_logs`, `action_logs` et `conversation_logs`.  

### 5.2. Architecture de collecte et de visualisation des métriques  

```mermaid
graph LR
    A[Scraper / Bot] --> B[MongoDB (raw logs)]
    B --> C[ETL Python (pandas)]
    C --> D[Prometheus Pushgateway]
    D --> E[Prometheus TSDB]
    E --> F[Grafana Dashboard]
    C --> G[InfluxDB (optional)]
    G --> F
```

* **MongoDB** conserve les événements bruts (`event_type`, `timestamp`, `payload`).  
* **ETL Python** (pandas + psycopg2) agrège les logs toutes les 5 min, calcule les KPI et les pousse via le client HTTP du **Pushgateway**.  
* **Prometheus** stocke les séries temporelles ; **Grafana** interroge Prometheus pour les graphiques en temps réel.  

**Exemple de code d’agrégation et de push** (Python 3.11, commenté) :

```python
#!/usr/bin/env python3
"""
push_kpi.py – agrège les logs MongoDB et pousse les KPI vers Prometheus Pushgateway.
Exigences : pymongo, pandas, requests
"""

import os
import datetime as dt
from collections import Counter

import pandas as pd
import pymongo
import requests

# --------------------------------------------------------------
# 1️⃣ Configuration – variables d’environnement sécurisées
# --------------------------------------------------------------
MONGO_URI = os.getenv("MONGO_URI")          # ex: "mongodb://user:pwd@mongo:27017"
DB_NAME   = os.getenv("MONGO_DB", "linkedin")
PGW_URL   = os.getenv("PUSHGATEWAY_URL")    # ex: "http://pushgateway:9091/metrics/job/linkedin_bot"

# --------------------------------------------------------------
# 2️⃣ Connexion MongoDB
# --------------------------------------------------------------
client = pymongo.MongoClient(MONGO_URI)
db = client[DB_NAME]

# --------------------------------------------------------------
# 3️⃣ Chargement des logs de la fenêtre temporelle (dernier jour)
# --------------------------------------------------------------
now = dt.datetime.utcnow()
yesterday = now - dt.timedelta(days=1)

pipeline = [
    {"$match": {"timestamp": {"$gte": yesterday, "$lt": now}}},
    {"$project": {"event_type": 1, "timestamp": 1, "prospect_id": 1}}