# API OpenAI — Intégration Avancée

> Référence `api-openai` · 59 €

## Plan

## Module 1 : Authentification et gestion sécurisée des clés API  
**Objectif mesurable** : L’apprenant pourra créer, stocker et renouveler une clé d’API OpenAI en respectant les exigences de sécurité (confidentialité, rotation, audit).  
**Notions couvertes**  
1. Procédure de génération de clé via le tableau de bord OpenAI.  
2. Stockage sécurisé (variables d’environnement, services de secret management).  
3. Rotation périodique et révocation de clés.  
4. Limites de quota et gestion des erreurs d’authentification.  
5. Conformité RGPD et politiques de confidentialité liées aux données d’API.

## Module 2 : Construction de requêtes avancées (Chat & Completion)  
**Objectif mesurable** : L’apprenant pourra formuler et envoyer des requêtes paramétrées aux endpoints `chat/completions` et `completions` en contrôlant le comportement du modèle.  
**Notions couvertes**  
1. Structure JSON des payloads (messages, prompt, parameters).  
2. Paramètres de contrôle : `temperature`, `top_p`, `max_tokens`, `frequency_penalty`, `presence_penalty`.  
3. Utilisation de `system` messages pour orienter le comportement.  
4. Gestion des réponses multi‑tour et extraction des contenus (choices, finish_reason).  
5. Gestion des limites de débit (`rate limits`) et stratégies de back‑off.

## Module 3 : Gestion du contexte et des tokens  
**Objectif mesurable** : L’apprenant pourra calculer le nombre de tokens d’une conversation, appliquer le découpage (truncation) et implémenter le “sliding window” pour rester sous la limite du modèle.  
**Notions couvertes**  
1. Méthode de tokenisation avec le package `tiktoken`.  
2. Calcul du nombre de tokens d’un message ou d’un prompt complet.  
3. Stratégies de réduction du contexte (résumé, suppression des messages les plus anciens).  
4. Implémentation d’un tampon circulaire (sliding window) en Python.  
5. Impact des tokens sur le coût (prix par 1 000 tokens) et sur la latence.

## Module 4 : Optimisation des coûts et monitoring en production  
**Objectif mesurable** : L’apprenant pourra instrumenter une application pour suivre la consommation de tokens, prévoir les dépenses et ajuster dynamiquement les paramètres afin de respecter un budget défini.  
**Notions couvertes**  
1. Récupération des métriques d’usage via les en‑têtes de réponse (`openai-organization`, `openai-processing-ms`).  
2. Enregistrement des logs d’appels (timestamp, modèle, tokens, coût).  
3. Mise en place de seuils d’alerte (ex. via CloudWatch, Prometheus).  
4. Algorithme de réglage adaptatif du `temperature`/`max_tokens` selon le budget restant.  
5. Analyse post‑mortem des factures OpenAI (exemple de calcul du coût total).

## Module 5 : Sécurisation des données et conformité aux politiques d’utilisation  
**Objectif mesurable** :

---

## Module 1 — contenu

## 1.1 Génération de la clé API via le tableau de bord OpenAI  

| Étape | Action | Détail vérifiable |
|------|--------|-------------------|
| 1 | Se connecter à <https://platform.openai.com/account/api-keys> | L’URL ne change pas (vérifiable dans la documentation officielle). |
| 2 | Cliquer **Create new secret key** | Le bouton crée une chaîne alphanumérique de 48 caractères (ex. `sk-...`). |
| 3 | Copier immédiatement la clé affichée | La clé n’est plus affichable après fermeture du dialogue. |
| 4 | Enregistrer la clé dans un gestionnaire de secrets (ex. 1Password, HashiCorp Vault) | La clé doit rester hors du code source. |

> **Note de sécurité** : chaque clé est liée à l’organisation et aux quotas du compte. Toute utilisation non autorisée consomme le même quota.

---

## 1.2 Stockage sécurisé  

### 1.2.1 Variables d’environnement (méthode minimale)

```bash
# .bashrc / .zshrc (NE JAMAIS COMMITTER CE FICHIER)
export OPENAI_API_KEY="sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

* **Vérification** : `echo $OPENAI_API_KEY` doit renvoyer la clé sans guillemets.  
* **Pitfall** : si le fichier de profil est versionné, la clé fuit dans le VCS.

### 1.2.2 Fichier `.env` avec `python-dotenv`

```text
# .env (ajouter .env à .gitignore)
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

```python
# app/config.py
from pathlib import Path
from dotenv import load_dotenv
import os

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")          # charge .env uniquement pour ce répertoire

API_KEY = os.getenv("OPENAI_API_KEY")
if not API_KEY:
    raise RuntimeError("OPENAI_API_KEY non définie dans l'environnement")
```

* **Vérifiable** : `python -c "import app.config; print(app.config.API_KEY[:5])"` affiche `sk-...`.  
* **Pitfall** : ne jamais pousser le fichier `.env` ; ajoutez‑le systématiquement à `.gitignore`.

### 1.2.3 Secret Management (ex. HashiCorp Vault)

```python
# vault_secret.py
import hvac
import os

client = hvac.Client(url=os.getenv("VAULT_ADDR"))
client.token = os.getenv("VAULT_TOKEN")   # token d’accès au vault, lui‑même stocké en env

secret = client.secrets.kv.v2.read_secret_version(path="openai/api_key")
API_KEY = secret["data"]["data"]["key"]
```

* **Vérifiable** : `client.secrets.kv.v2.read_secret_version` renvoie un dict contenant `key`.  
* **Pitfall** : le token Vault doit être limité aux seules lectures de ce secret (policy `path "secret/data/openai/*" { capabilities = ["read"] }`).

---

## 1.3 Rotation périodique et révocation  

| Action | Commande | Effet |
|--------|----------|-------|
| **Créer une nouvelle clé** | Via le tableau de bord ou `openai api keys.create` (CLI) | Nouvelle clé active, ancienne reste valide. |
| **Révoquer l’ancienne** | `openai api keys.delete <OLD_KEY_ID>` | L’ancienne clé devient immédiatement inutilisable, les appels renvoient `401 Unauthorized`. |
| **Automatiser la rotation** | Script CI/CD (ex. GitHub Actions) qui :<br>1. Crée une nouvelle clé<br>2. Met à jour le secret manager<br>3. Révoque l’ancienne | Garantit un intervalle ≤ 30 jours (recommandation OpenAI). |

### Exemple de script de rotation (Python + OpenAI CLI)

```python
#!/usr/bin/env python3
import subprocess, json, os, sys
from pathlib import Path

# 1. Crée une nouvelle clé via le CLI (nécessite OPENAI_API_KEY admin)
result = subprocess.run(
    ["openai", "api", "keys", "create", "--output", "json"],
    capture_output=True,
    text=True,
    check=True,
)
new_key = json.loads(result.stdout)
new_secret = new_key["secret_key"]
new_id = new_key["id"]
print(f"🔑 Nouvelle clé créée : {new_id}")

# 2. Met à jour le secret manager (ex. .env)
env_path = Path(__file__).parent / ".env"
lines = env_path.read_text().splitlines()
new_lines = [f"OPENAI_API_KEY={new_secret}" if l.startswith("OPENAI_API_KEY=") else l for l in lines]
env_path.write_text("\n".join(new_lines))
print("✅ .env mis à jour")

# 3. Révoque l’ancienne clé (id stocké dans une variable d’environnement)
old_id = os.getenv("OPENAI_OLD_KEY_ID")
if old_id:
    subprocess.run(
        ["openai", "api", "keys", "delete", old_id],
        check=True,
    )
    print(f"🗑️ Ancienne clé {old_id} révoquée")
else:
    print("⚠️ Aucun ID d'ancienne clé fourni – rotation manuelle requise")
```

* **Pré‑requis** : le token utilisé doit posséder le scope `keys:write`.  
* **Pitfall** : ne pas attendre la propagation du

---

## Module 2 — contenu

## 1. Structure JSON des payloads  

| Endpoint | Méthode | URL (v1) | Corps attendu |
|----------|---------|----------|----------------|
| `chat/completions` | POST | `https://api.openai.com/v1/chat/completions` | `{ model, messages, … }` |
| `completions` | POST | `https://api.openai.com/v1/completions` | `{ model, prompt, … }` |

### 1.1 `chat/completions`  

```json
{
  "model": "gpt-4o-mini",
  "messages": [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user",   "content": "Explique la différence entre IA faible et IA forte."}
  ],
  "temperature": 0.7,
  "max_tokens": 512,
  "top_p": 1,
  "frequency_penalty": 0,
  "presence_penalty": 0,
  "stream": false
}
```

- **`model`** : identifiant exact du modèle (ex. `gpt-4o`, `gpt-3.5-turbo`).  
- **`messages`** : tableau ordonné. Chaque objet possède **`role`** (`system`, `user`, `assistant`, `tool`) et **`content`** (string ou tableau d’objets multimédia).  
- **`temperature`**, **`top_p`**, **`max_tokens`**, **`frequency_penalty`**, **`presence_penalty`** : paramètres de génération (voir §2).  
- **`stream`** : `true` active le mode de streaming HTTP/1.1 (requête plus lourde, nécessite un traitement asynchrone).  

### 1.2 `completions`  

```json
{
  "model": "text-davinci-003",
  "prompt": "Liste les 5 pays les plus peuplés en 2023.",
  "temperature": 0,
  "max_tokens": 150,
  "top_p": 1,
  "frequency_penalty": 0,
  "presence_penalty": 0,
  "stop": ["\n"]
}
```

- **`prompt`** peut être une chaîne ou un tableau de chaînes (chaque entrée est traitée séparément).  
- **`stop`** accepte une chaîne ou un tableau de chaînes qui indiquent où le modèle doit s’arrêter.  

> **Vérifiable** : la spécification JSON est publiée dans la documentation officielle d’OpenAI (section *Chat Completion* et *Completions*).  

---

## 2. Paramètres de contrôle  

| Paramètre | Type | Intervalle valide | Effet |
|-----------|------|-------------------|------|
| `temperature` | float | `[0, 2]` | Contrôle la randomisation ; 0 = déterministe, 2 = très créatif. |
| `top_p` | float | `[0, 1]` | Nucleus sampling ; le modèle ne considère que les tokens cumulant `top_p` de probabilité. |
| `max_tokens` | int | `1` – `8192` (selon le modèle) | Nombre maximal de tokens générés. |
| `frequency_penalty` | float | `[-2, 2]` | Pénalise les tokens déjà fréquents dans la sortie. |
| `presence_penalty` | float | `[-2, 2]` | Pénalise les tokens déjà présents dans le contexte. |
| `logprobs` (optionnel) | int | `0` – `5` | Retourne les log‑probabilités des `logprobs` tokens les plus probables. |
| `response_format` (v1.1+) | object | `{type: "json_object"}` ou `{type: "text"}` | Force le format de sortie. |

### 2.1 Interaction entre `temperature` et `top_p`  

- Si `temperature = 0`, le modèle agit comme un **décodeur déterministe** : le token avec la plus haute probabilité est toujours choisi, `top_p` devient sans effet.  
- Si `temperature > 0` et `top_p < 1`, le modèle applique d’abord le **nucleus sampling** (filtrage par probabilité cumulative) puis la **softmax** tempérée.  

### 2.2 Exemple d’ajustement dynamique  

```python
def choose_parameters(remaining_budget_usd, tokens_used, model="gpt-4o-mini"):
    # Prix public (au 14/08/2026) : 0.000150 $ / 1 000 tokens (input) + 0.000300 $ / 1 000 tokens (output)
    price_per_1k = 0.00045  # coût moyen estimé
    # Si le budget restant est < 10 % du budget initial, on restreint la créativité
    if remaining_budget_usd < 0.1 * price_per_1k * (tokens_used + 1_000):
        return {"temperature": 0.2, "max_tokens": 256}
    # Sinon on autorise plus de créativité
    return {"temperature": 0.8, "max_tokens": 1024}
```

> **Vérifiable** : les tarifs sont affichés dans le tableau tarifaire d’OpenAI (section *Pricing*).  

---

##

---

## Module 3 — contenu

## 3.1 Tokenisation avec **tiktoken**

| Concept | Détails vérifiables |
|---------|----------------------|
| Modèle de tokenisation | `tiktoken.encoding_for_model("gpt-3.5-turbo")` renvoie l’encoding utilisé par le modèle. |
| Token = unité de texte (souvent un sous‑mot). | La même chaîne `"ChatGPT"` → 2 tokens (`"Chat"` + `"GPT"`). |
| Coût = nombre de tokens * prix du modèle (ex. $0.002 / 1 000 tokens pour `gpt‑3.5‑turbo`). | Calcul direct : `tokens * 0.002 / 1000`. |

```python
import tiktoken

def get_encoding(model: str = "gpt-3.5-turbo"):
    """Retourne l'objet d'encodage correspondant au modèle."""
    return tiktoken.encoding_for_model(model)

def count_tokens(text: str, model: str = "gpt-3.5-turbo") -> int:
    """Compte les tokens d'une chaîne brute."""
    enc = get_encoding(model)
    return len(enc.encode(text))
```

### Pièges courants
- **Oublier le rôle** : chaque message JSON possède un champ `role` (`system`, `user`, `assistant`). L’API compte les tokens du rôle et des séparateurs (`\n`). Ignorer ces éléments sous‑estime le total.
- **Différence d’encodage** : `tiktoken` utilise le même encodage que l’API, mais les versions locales peuvent être désynchronisées. Toujours installer la version la plus récente (`pip install -U tiktoken`).
- **Caractères non‑ASCII** : les emojis ou caractères CJK sont souvent un token chacun, contrairement à l’idée qu’ils seraient “plus gros”.

## 3.2 Calcul du nombre de tokens d’un **message** complet

Le format interne de l’API (extrait du code source) :

```
<|start|>{role/name}\n{content}

---

## Module 4 — contenu

## Module 4 : Optimisation des coûts et monitoring en production  

### 4.1 Récupération des métriques d’usage via les en‑têtes de réponse  

| En‑tête | Description | Exemple de valeur |
|--------|-------------|-------------------|
| `openai-organization` | Identifiant de l’organisation facturée | `org-1234567890abcdef` |
| `openai-processing-ms` | Temps de traitement côté serveur (ms) | `342` |
| `openai-version` | Version de l’API utilisée | `2020‑10‑01` |
| `x-ratelimit-limit-requests` | Nombre maximal de requêtes autorisées dans la fenêtre de quota | `3500` |
| `x-ratelimit-remaining-requests` | Requêtes restantes dans la fenêtre courante | `2745` |
| `x-ratelimit-reset-requests` | Temps (s) avant le reset du quota | `60` |

```python
import os, json, time, logging, requests
import openai

openai.api_key = os.getenv("OPENAI_API_KEY")
openai.api_base = "https://api.openai.com/v1"

def call_chat(messages, **params):
    """Envoie une requête chat/completions et renvoie la réponse + métriques."""
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=messages,
        **params,
    )
    # Les en‑têtes sont accessibles via response.headers (requests.Response)
    headers = response.headers
    usage = {
        "model": response.model,
        "prompt_tokens": response.usage.prompt_tokens,
        "completion_tokens": response.usage.completion_tokens,
        "total_tokens": response.usage.total_tokens,
        "processing_ms": int(headers.get("openai-processing-ms", 0)),
        "org_id": headers.get("openai-organization"),
        "rate_limit_remaining": int(headers.get("x-ratelimit-remaining-requests", -1)),
        "rate_limit_reset": int(headers.get("x-ratelimit-reset-requests", 0)),
    }
    return response, usage
```

*Vérifiable* : la documentation officielle d’OpenAI (section *Response Headers*) liste exactement ces en‑têtes.  

### 4.2 Enregistrement des logs d’appels  

Le log minimal doit contenir : timestamp ISO 8601, modèle, paramètres pertinents (`temperature`, `max_tokens`), nombre de tokens (prompt, completion, total), coût estimé, durée serveur, code de statut HTTP.  

```python
import csv
from datetime import datetime

LOG_FILE = "openai_calls.log"

def log_call(usage: dict, params: dict, status_code: int):
    """Écrit une ligne CSV dans le fichier de log."""
    # Calcul du coût (USD) – tarifs au 14 / 2024 (exemple)
    # gpt-4o-mini : $0.150 / 1 000 tokens (prompt) ; $0.600 / 1 000 tokens (completion)
    PROMPT_RATE = 0.150 / 1_000
    COMPLETION_RATE = 0.600 / 1_000

    cost = (
        usage["prompt_tokens"] * PROMPT_RATE +
        usage["completion_tokens"] * COMPLETION_RATE
    )
    row = {
        "timestamp": datetime.utcnow().isoformat(),
        "model": usage["model"],
        "temperature": params.get("temperature"),
        "max_tokens": params.get("max_tokens"),
        "prompt_tokens": usage["prompt_tokens"],
        "completion_tokens": usage["completion_tokens"],
        "total_tokens": usage["total_tokens"],
        "cost_usd": round(cost, 6),
        "processing_ms": usage["processing_ms"],
        "status_code": status_code,
        "org_id": usage["org_id"],
    }
    file_exists = os.path.isfile(LOG_FILE)
    with open(LOG_FILE, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=row.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)
```

**Bonnes pratiques**  
* Utiliser un logger structuré (JSON) lorsqu’on envoie les logs vers un agrégateur (ex. Elastic, CloudWatch).  
* Rotations de fichiers : `logging.handlers.TimedRotatingFileHandler` pour éviter l’épuisement du disque.  
* Ne jamais logger la clé d’API ou le contenu complet du prompt si celui‑ci contient des données sensibles ; remplacer par un hash SHA‑256 du texte.  

### 4.3 Mise en place de seuils d’alerte  

#### 4.3.1 Exemple avec AWS CloudWatch (Python boto3)

```python
import boto3
import os

cloudwatch = boto3.client("cloudwatch", region_name="eu-west-1")
NAMESPACE = "OpenAI/Usage"
METRIC = "DailyCostUSD"

def publish_daily_cost(cost_usd: float):
    cloudwatch.put_metric_data(
        Namespace=NAMESPACE,
        MetricData=[
            {
                "MetricName": METRIC,
                "Timestamp": datetime.utcnow(),
                "Value": cost_usd,
                "Unit": "None",
                "StorageResolution": 60,  # 1‑minute granularity
            }
        ],
    )
```

*Création d’une alarme* (via console ou `aws cloudwatch put-metric-alarm`) :  

```bash
aws cloudwatch put-metric-alarm \
  --alarm-name "OpenAI‑Budget‑Exceeded" \
  --metric-name DailyCostUSD \
  --namespace OpenAI/Usage \
  --threshold 50.0 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 1 \
  --period 86400 \
  --statistic Sum \
  --actions-enabled \
  --alarm-actions arn:

---

## Module 5 — contenu

## 5.1. Principes de sécurisation des données en amont de l’appel API  

| Aspect | Exigence vérifiable | Implémentation typique |
|--------|---------------------|-----------------------|
| **Confidentialité** | Aucun champ contenant des données à caractère personnel (PII) ne doit transiter en clair vers l’API. | Filtrage / anonymisation pré‑envoi (regex, modèles NER). |
| **Intégrité** | Le payload JSON doit être signé ou transmis via TLS 1.2+ (obligatoire pour l’API OpenAI). | Utiliser `https://api.openai.com/v1/...` avec la bibliothèque officielle qui force TLS. |
| **Traçabilité** | Chaque appel doit être journalisé avec horodatage, modèle, nombre de tokens, mais **sans** les données sensibles. | Logger uniquement le hash (SHA‑256) du prompt ou la version redacted. |
| **Durée de conservation** | Les logs contenant des données utilisateur doivent être conservés ≤ 30 jours (exigence RGPD standard). | Rotation quotidienne des fichiers de log, suppression automatisée. |
| **Accès restreint** | Les clés d’API et les secrets de chiffrement ne doivent jamais être codés en dur. | Variables d’environnement, secret manager (AWS Secrets Manager, GCP Secret Manager, Azure Key Vault). |
| **Consentement** | L’utilisateur doit être informé que son texte sera envoyé à un service tiers (OpenAI) et accepter explicitement. | UI → checkbox + stockage de l’accusé de réception. |
| **Politique d’utilisation d’OpenAI** | Aucun contenu illicite, violent, harcelant, ou qui incite à la désinformation ne doit être généré ou transmis. | Validation du prompt via liste blanche / blacklist avant l’envoi. |

## 5.2. Gestion du PII avec `presidio‑analyzer` (exemple fonctionnel)

```python
# fichier : secure_chat.py
import os
import hashlib
import json
import logging
from typing import Tuple

import openai
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine

# ----------------------------------------------------------------------
# Configuration sécurisée
# ----------------------------------------------------------------------
openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    raise RuntimeError("OPENAI_API_KEY non définie dans l’environnement")

# Logger minimal : on ne conserve jamais le texte brut
logger = logging.getLogger("secure_chat")
handler = logging.FileHandler("secure_chat.log")
formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# ----------------------------------------------------------------------
# Instanciation des moteurs Presidio (analyse + anonymisation)
# ----------------------------------------------------------------------
analyzer = AnalyzerEngine()
anonymizer = AnonymizerEngine()

# ----------------------------------------------------------------------
# Fonction utilitaire : hash SHA‑256 (non réversible) du texte complet
# ----------------------------------------------------------------------
def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

# ----------------------------------------------------------------------
# Redaction du PII
# ----------------------------------------------------------------------
def redact_pii(text: str) -> Tuple[str, dict]:
    """
    Retourne le texte anonymisé et le mapping des entités détectées.
    Exemple de mapping : {"EMAIL": ["john.doe@example.com"]}

    Les entités sont remplacées par le placeholder <ENTITY>.
    """
    results = analyzer.analyze(text=text, language="fr")
    # Construction du dictionnaire de remplacement
    anonymize_map = {r.entity_type: "<{}>".format(r.entity_type) for r in results}
    anonymized = anonymizer.anonymize(text=text, analyzer_results=results,
                                      operators={k: {"type": "replace"} for k in anonymize_map})
    # Création d’un dictionnaire simple pour le log (sans texte brut)
    entities = {}
    for r in results:
        entities.setdefault(r.entity_type, []).append(r.entity_value)
    return anonymized.text, entities

# ----------------------------------------------------------------------
# Envoi sécurisé vers l’API ChatCompletion
# ----------------------------------------------------------------------
def chat_secure(user_message: str, model: str = "gpt-4o-mini", temperature: float = 0.0) -> str:
    """
    1. Vérifie le consentement (exemple simplifié : variable d’environnement)
    2. Redacte le PII
    3. Envoie le texte anonymisé
    4. Logue le hash du texte original + le mapping d’entités
    """
    if os.getenv("USER_CONSENT") != "1":
        raise PermissionError("Consentement utilisateur manquant")

    # 2. Redaction
    safe_message, entities = redact_pii(user_message)

    # 3. Appel API
    response = openai.ChatCompletion.create(