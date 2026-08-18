# API Claude — Maîtrise Avancée

> Référence `claude-api-avance` · 69 €

## Plan

## Module 1 – Architecture et flux de travail de l’API Claude  
**Objectif :** Être capable de configurer un appel API complet (authentification, paramètres, pagination) et d’interpréter le schéma de réponse dans un projet Node.js ou Python.  
- Modèle de langage de Claude : architecture Transformer, décodage par échantillonnage vs beam search.  
- Méthode d’authentification : clés API, en-têtes `Authorization`, rotation sécurisée.  
- Structure des requêtes : endpoint `/v1/complete`, corps JSON (`prompt`, `max_tokens`, `temperature`, `stop_sequences`).  
- Gestion des réponses : champs `completion`, `usage`, `stop_reason`, traitement des erreurs HTTP 4xx/5xx.  
- Pagination et streaming : paramètres `stream` et `next_token`, reconstruction d’une réponse longue.

## Module 2 – Optimisation des prompts et contrôle de la génération  
**Objectif :** Concevoir des prompts qui atteignent un taux de réussite ≥ 90 % sur des critères de pertinence définis (ex. exactitude factuelle, style).  
- Prompt engineering : rôle du système, instructions explicites, exemples de few‑shot.  
- Paramètres de génération : `temperature`, `top_p`, `presence_penalty`, impact mesurable sur la diversité.  
- Utilisation des “stop sequences” et du “max_tokens” pour contraindre la longueur.  
- Techniques de “chain‑of‑thought” et de “self‑consistency” pour améliorer la logique.  
- Validation automatisée : scripts de test unitaires comparant la sortie à des réponses attendues.

## Module 3 – Gestion du contexte et des limites de tokenisation  
**Objectif :** Implémenter une logique de gestion de contexte qui maintient la cohérence sur plus de 10 000 tokens d’échange sans perte d’information critique.  
- Tokenisation : BPE de Claude, fonction `token_count`, différence avec les tokenizers OpenAI.  
- Fenêtrage dynamique : stratégies de “sliding window”, résumé incrémental, sélection de messages pertinents.  
- Mémoire à court terme vs long terme : utilisation de `system` messages persistants et de `user` messages temporaires.  
- Compression de contexte : appels à un modèle de résumé, stockage de résumés dans une base de données.  
- Surveillance des quotas : calcul du coût en tokens, alertes de dépassement.

## Module 4 – Sécurité, conformité et bonnes pratiques de déploiement  
**Objectif :** Déployer une API Claude en production tout en respectant le RGPD et les exigences de sécurité (OWASP Top 10).  
- Masquage des données sensibles : filtrage des PII avant l’envoi, post‑traitement de la réponse.  
- Gestion des erreurs et des time‑outs : retry avec back‑off exponentiel, circuit breaker.  
- Isolation des clés : variables d’environnement, secret managers (AWS Secrets Manager, HashiCorp Vault).  
- Journalisation et audit : logs structurés (`request_id`, `prompt_hash`, `usage`), conformité GDPR.  
- Tests de charge : simulation de 100 req/s avec k6, mesure du temps moyen de réponse et du taux d’erreur.

## Module 5 – Intégration avancée et extensions fonctionnelles  
**Objectif :** Construire deux intégrations concrètes (chatbot multicanal et génération de code) qui exploitent les fonctions de l’API Claude et les webhook personnalisés.  
- Webhook de callback : mise en place d’un endpoint `POST /claude/webhook` pour recevoir les réponses en streaming.  
- Multicanal : adaptation du format de réponse pour

---

## Module 1 — contenu

## 1.1 Architecture du modèle Claude  

| Élément | Description | Référence |
|--------|-------------|-----------|
| **Transformeur** | Encoder‑décodeur à 32 couches, 64 têtes d’attention, dimension de modèle 4096. | Documentation Anthropic, section *Model Architecture* |
| **Décodage** | - **Échantillonnage** : tirage aléatoire selon la distribution softmax, contrôlé par `temperature` et `top_p`. <br>- **Beam search** : non disponible via l’API publique ; l’API ne supporte que le décodage par échantillonnage. | API spec, paramètre `temperature` |
| **Limites de token** | 100 000 tokens maximum par appel (prompt + completion). | API spec, champ `max_tokens` |

---

## 1.2 Authentification  

1. **Clé API** : chaîne alphanumérique fournie dans le tableau de bord Anthropic.  
2. **En‑tête HTTP**  

```http
Authorization: Bearer sk-ant-xxxxxxxxxxxxxxxxxxxx
```

3. **Rotation sécurisée**  
   * Stocker la clé dans un secret manager (AWS Secrets Manager, HashiCorp Vault).  
   * Récupérer la valeur à chaque démarrage du processus ou via un middleware qui rafraîchit le secret toutes les 24 h.  

**Piège** : l’en‑tête doit être exactement `Authorization` (casse respectée). Un `authorization` minuscule entraîne une réponse `401 Unauthorized`.

---

## 1.3 Structure des requêtes  

| Champ | Type | Obligatoire | Valeur par défaut | Description |
|------|------|-------------|-------------------|-------------|
| `model` | string | oui | – | Identifiant du modèle, ex. `claude-2.1` |
| `prompt` | string | oui | – | Texte d’entrée. |
| `max_tokens` | integer | non | 1024 | Nombre maximal de tokens générés. |
| `temperature` | float (0‑2) | non | 0.7 | Contrôle de la randomisation. |
| `top_p` | float (0‑1) | non | 1.0 | Nucleus sampling. |
| `stop_sequences` | array[string] | non | [] | Séquences qui terminent la génération. |
| `stream` | boolean | non | false | Si `true`, la réponse est renvoyée en flux SSE. |
| `metadata` | object | non | – | Données arbitraires (ex. `request_id`). |

**Endpoint** : `POST https://api.anthropic.com/v1/complete`  
**Content‑Type** : `application/json`

### Exemple de corps JSON (compact)

```json
{
  "model": "claude-2.1",
  "prompt": "\n\nHuman: Quelle est la capitale du Brésil?\nAssistant:",
  "max_tokens": 64,
  "temperature": 0.0,
  "stop_sequences": ["\nHuman:", "\nAssistant:"]
}
```

---

## 1.4 Gestion des réponses  

### 1.4.1 Payload standard (non‑stream)

```json
{
  "completion": "Brasília.",
  "stop_reason": "stop_sequence",
  "model": "claude-2.1",
  "usage": {
    "input_tokens": 23,
    "output_tokens": 4
  }
}
```

| Champ | Type | Description |
|------|------|-------------|
| `completion` | string | Texte généré. |
| `stop_reason` | string | `stop_sequence`, `max_tokens`, `error`. |
| `usage` | object | Comptage des tokens d’entrée et de sortie. |
| `model` | string | Modèle utilisé (utile pour la journalisation). |

### 1.4.2 Gestion des erreurs HTTP  

| Code | Situation | Action recommandée |
|------|-----------|--------------------|
| 400 | Paramètre manquant ou mal formé | Log détaillé, ne pas ré‑essayer. |
| 401 | Clé API invalide ou expirée | Rafraîchir le secret, abort. |
| 429 | Quota dépassé ou taux de requêtes trop élevé | Back‑off exponentiel, puis retry. |
| 500‑504 | Erreur serveur | Retry avec back‑off, puis alerter. |

### 1.4.3 Exemple de traitement en Python (requests)

```python
import os
import json
import time
import requests
from typing import Dict

API_URL = "https://api.anthropic.com/v1/complete"
HEADERS = {
    "Content-Type": "application/json",
    "x-api-key": os.getenv("ANTHROPIC_API_KEY"),   # recommandé: secret manager
    "anthropic-version": "2023-06-01"
}

def call_claude(payload: Dict) -> Dict:
    """Envoie une requête à Claude et renvoie le JSON décodé.
    Gère les retries 429/5xx avec back‑off exponentiel."""
    max_retries = 5
    backoff = 1.0  # secondes
    for attempt in range(max_retries):
        response = requests.post(API_URL, headers=HEADERS, json=payload, timeout=30)
        if response.status_code == 200:
            return response.json()
        if response.status_code in (429, 500, 502, 503, 504):
            time.sleep(backoff)
            backoff *= 2  # exponentiel
            continue
        # autres codes = fatal
        raise RuntimeError(f"Claude API error {response.status_code}: {response.text}")

# Exemple d’appel
payload = {
    "model": "claude-2

---

## Module 2 — contenu

## Module 2 – Optimisation des prompts et contrôle de la génération  

### 2.1 Prompt engineering  

| Élément | Rôle | Exemple concret |
|--------|------|-----------------|
| **Message système** | Définit le rôle, le ton et les contraintes globales. | ```json {"role":"system","content":"Tu es un assistant spécialisé en droit du travail. Réponds de façon concise, sans jamais divulguer d’informations personnelles."}``` |
| **Instruction explicite** | Limite l’ambiguïté du comportement attendu. | `« Donne la réponse en trois phrases », « Utilise uniquement les sources suivantes »` |
| **Few‑shot** | Fournit des paires question‑réponse qui guident le modèle vers le format souhaité. | ```json {"role":"user","content":"Quelle est la durée légale du préavis en CDI ?"} {"role":"assistant","content":"Le préavis est de 1 mois pour le salarié et 2 mois pour l’employeur, sauf convention plus favorable."}``` |
| **Contextualisation** | Insère les variables dynamiques (ex. *user_name*, *date*) via interpolation. | `f"Bonjour {user_name}, voici le résumé du rapport du {date}."` |

**Bonnes pratiques**  
- Limiter le nombre de lignes du message système à < 150 tokens pour éviter le débordement de la fenêtre.  
- Placer les exemples **avant** la question cible afin que le modèle les considère comme des modèles de réponse.  
- Utiliser un vocabulaire **exact** (ex. « préavis », pas « délai ») pour réduire la variance sémantique.  

### 2.2 Paramètres de génération  

| Paramètre | Plage admissible | Impact mesurable | Valeur typique pour haute précision |
|-----------|------------------|------------------|--------------------------------------|
| `temperature` | 0 – 2 | Contrôle l’aléatoire : 0 = déterministe, > 1 = très créatif | **0.0 – 0.2** |
| `top_p` (nucleus sampling) | 0 – 1 | Fraction de probabilité cumulative retenue | **0.9** (défaut) |
| `presence_penalty` | –2 – 2 | Décourage la réapparition de tokens déjà vus | **0.5** pour éviter les répétitions |
| `max_tokens` | 1 – 4096 (selon le modèle) | Limite la longueur de la réponse | **150** pour des réponses factuelles courtes |
| `stop_sequences` | tableau de chaînes | Force l’arrêt dès qu’une séquence apparaît | `["\n\n", "###"]` |

**Mesure de l’impact**  
```python
import time, statistics
def benchmark(prompt, **gen_params):
    latencies = []
    for _ in range(20):
        start = time.time()
        response = claude.complete(prompt, **gen_params)
        latencies.append(time.time() - start)
    return statistics.mean(latencies), statistics.stdev(latencies)
```
Comparer la moyenne de latence et la variance de la longueur de sortie entre `temperature=0.0` et `temperature=0.8` montre que la précision factuelle décroît dès que la température dépasse 0.3.

### 2.3 Utilisation des “stop sequences” et du “max_tokens”  

```python
# Exemple complet en Python (SDK hypothétique)
import os, json, requests

API_KEY = os.getenv("CLAUDE_API_KEY")
HEADERS = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

def call_claude(prompt: str):
    payload = {
        "model": "claude-2.1",
        "messages": [
            {"role": "system", "content": "Tu es un assistant de support technique."},
            {"role": "user",   "content": prompt}
        ],
        "max_tokens": 120,
        "temperature": 0.0,
        "stop_sequences": ["\n---", "<END>"]
    }
    r = requests.post("https://api.anthropic.com/v1/complete", headers=HEADERS, json=payload)
    r.raise_for_status()
    return r.json()["completion"]

# Utilisation
question = "Comment réinitialiser le mot de passe d’un compte Windows ?"
print(call_claude(question))
```
*Commentaires*  
- `stop_sequences` empêche le modèle de générer du texte superflu (ex. signatures, listes non désirées).  
- `max_tokens` agit comme garde‑fou : même si la séquence d’arrêt n’est pas rencontrée, la réponse est tronquée proprement.  

### 2.4 Techniques de “chain‑of‑thought” (CoT)  

1. **Prompt explicite** : demander explicitement de raisonner étape par étape.  
2. **Séparer le raisonnement du résultat** : inclure un marqueur (`<<RESULT>>`) que le script extrait ensuite.  

```python
def call_claude_cot(question: str):
    cot_prompt = f"""Réponds à la question suivante en détaillant chaque étape de raisonnement, puis indique le résultat final après le marqueur <<RESULT>>.

Question : {question}
Réponse :"""
    raw = call_claude(cot_prompt)
    # Extraction du résultat
    result = raw.split("<<RESULT>>")[-1].strip()
    return result
```

**Effet observé** : sur le benchmark *MATH* (questions à 2

---

## Module 3 — contenu

## Module 3 – Gestion du contexte et des limites de tokenisation  

### 1. Tokenisation chez Claude  

| Aspect | Claude (Anthropic) | OpenAI (GPT‑3/4) |
|--------|-------------------|-----------------|
| Algorithme | Byte‑Pair Encoding (BPE) entraîné sur le corpus d’Anthropic, vocabulaire ≈ 52 k tokens | BPE (t‑davinci‑002) ou t‑p‑bpe (GPT‑4) ; vocabulaire ≈ 50 k tokens |
| Fonction utilitaire | `anthropic.Tokenizer().encode(text)` → `list[int]` | `openai.ChatCompletion.create(...).usage.total_tokens` (pas d’accès direct au tokenizer) |
| Comptage exact | `len(tokenizer.encode(text))` donne le nombre de *tokens* utilisés dans la requête | `len(encoding.encode(text))` via `tiktoken` donne le même résultat |

> **Vérifiable** : le dépôt `anthropic-sdk-python` expose `anthropic.Tokenizer` (v0.6+).  

#### 1.1. Fonction de comptage  

```python
# token_utils.py
from anthropic import Anthropic, Tokenizer

def token_count(text: str) -> int:
    """
    Retourne le nombre de tokens BPE utilisés par Claude pour le texte fourni.
    """
    tokenizer = Tokenizer()
    return len(tokenizer.encode(text))
```

*Le tokenizer est stateless ; il n’est pas nécessaire de le ré‑instancier à chaque appel.*

---

### 2. Fenêtrage dynamique (sliding window)  

Claude accepte **max 100 000 tokens** (prompt + completion). Au‑delà, le serveur renvoie **HTTP 400** « prompt too long ».  

#### 2.1. Stratégie de base  

1. **Définir une fenêtre cible** (`WINDOW = 90_000`).  
2. **Conserver** les messages système + les *N* derniers messages utilisateur/assistant qui tiennent dans la fenêtre.  
3. **Si dépassement**, supprimer les messages les plus anciens jusqu’à ce que `token_count(window) ≤ WINDOW`.  

#### 2.2. Implémentation Python (compatible avec l’API `messages`)  

```python
# context_manager.py
from typing import List, Dict, Any
from token_utils import token_count

WINDOW = 90_000          # tokens réservés aux réponses (max 100k - 10k safety)
SYSTEM_TOKEN_BUDGET = 2_000   # réserve pour le message système

def prune_messages(messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """
    Retourne une sous‑liste de `messages` qui tient dans la fenêtre.
    `messages` doit être ordonné chronologiquement (system → … → dernier user).
    """
    # Séparer le message système (s'il existe) du reste
    system_msg = [m for m in messages if m["role"] == "system"]
    other_msgs = [m for m in messages if m["role"] != "system"]

    # Réserve pour le système
    used = sum(token_count(m["content"]) for m in system_msg)
    if used > SYSTEM_TOKEN_BUDGET:
        raise ValueError("Message système dépasse le budget réservé")

    # Ajout progressif depuis la fin (messages récents)
    pruned = list(system_msg)          # commence avec le système
    for msg in reversed(other_msgs):
        msg_len = token_count(msg["content"])
        if used + msg_len > WINDOW:
            break                       # fenêtre pleine, on arrête d’ajouter
        pruned.insert(1, msg)            # insère juste après le système
        used += msg_len
    return pruned
```

*Notes*  
- `pruned.insert(1, msg)` garde l’ordre chronologique tout en insérant les nouveaux messages juste après le système.  
- La fonction lève une exception si le message système dépasse le budget ; c’est un **piège** fréquent lorsqu’on place un long contexte d’instructions.

---

### 3. Résumé incrémental (compression de contexte)  

Lorsque la conversation dépasse plusieurs dizaines de milliers de tokens, le simple glissement entraîne perte d’historique. On peut **résumer** les parties anciennes et les remplacer par un message `assistant` contenant le résumé.

#### 3.1. Pipeline de résumé  

1. **Détecter** que la fenêtre dépasse un seuil (`THRESHOLD = 80_000`).  
2. **Regrouper** les *k* premiers messages (ex. 10) en un seul bloc de texte.  
3. **Appeler Claude** avec le prompt :  

   ```
   Résume le texte suivant en 200 mots, en conservant les faits, les décisions et les références. 
   Texte : <bloc>
   ```  

4. **Créer** un nouveau message `assistant` : `content = <résumé>` et **remplacer** les *k* messages d’origine.  

#### 3.2. Exemple de code (Python, fonction asynchrone)  

```python
# incremental_summarizer.py
import asyncio
from anthropic import Anthropic
from token_utils import token_count
from context_manager import prune_messages

anthropic_client = Anthropic(api_key="YOUR_API_KEY")
MAX_TOKENS = 100_000
THRESHOLD = 80_000
SUMMARY_MAX_TOKENS = 500   # 200 mots ≈ 500 tokens

async def summarize_oldest(messages: list[dict]) -> list[dict]:
    """
    Résume les messages les plus anciens jusqu'à ce que le total ≤ THRESHOLD.
    Retourne la nouvelle liste de messages.
    """
    total = sum(token_count(m["content"]) for m in messages)
    if total <= THRESHOLD:
        return messages

    # Regrouper les 10 premiers messages (ou moins si moins disponibles)
    to_summarize =

---

## Module 4 — contenu

## 4.1 Masquage des données sensibles  

| Risque | Contre‑mesure | Implémentation |
|--------|---------------|----------------|
| Envoi de PII (nom, email, numéro de sécurité sociale) dans le `prompt` | Filtrer avant l’appel ; remplacer par des tokens anonymes (`<USER_ID>`) | Fonction `sanitize_prompt(prompt: str) -> str` qui applique des expressions régulières ; garder le mapping dans un store chiffré si besoin de ré‑association. |
| Réponse contenant des données extraites du prompt (ex. « Voici votre numéro : 123‑45‑6789 ») | Post‑traiter la réponse avec le même filtre inverse ; vérifier la présence de patterns PII | Utiliser la bibliothèque `presidio-analyzer` (Microsoft) ou `pii‑detect` pour détecter les entités dans la chaîne de sortie. |

```python
import re
from presidio_analyzer import AnalyzerEngine

PII_REGEX = re.compile(r'\b\d{3}-\d{2}-\d{4}\b')  # SSN US simple

def sanitize_prompt(prompt: str) -> str:
    # Remplace les emails et numéros de sécurité sociale par des placeholders
    prompt = re.sub(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}', '<EMAIL>', prompt)
    prompt = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', '<SSN>', prompt)
    return prompt

def redact_response(text: str) -> str:
    analyzer = AnalyzerEngine()
    results = analyzer.analyze(text=text, language='en')
    for r in results:
        start, end = r.start, r.end
        text = text[:start] + f'<{r.entity_type}>' + text[end:]
    return text

# Exemple d’usage
raw_prompt = "Mon email est alice@example.com et mon SSN 123-45-6789."
clean_prompt = sanitize_prompt(raw_prompt)
# appel API Claude avec `clean_prompt` …
raw_response = "Merci, votre numéro 123-45-6789 a été enregistré."
safe_response = redact_response(raw_response)
print(safe_response)   # → "Merci, votre numéro <SSN> a été enregistré."
```

### Pièges concrets  
* **Filtrage trop agressif** : le regex `.*` peut supprimer du texte légitime et dégrader la pertinence du modèle. Limiter le scope aux formats clairement identifiés.  
* **Double‑encodage** : si le prompt est JSON‑stringifié puis passé à `sanitize_prompt`, les caractères d’échappement (`\n`, `\"`) peuvent empêcher la détection. Appliquer le filtre sur la chaîne décodée.  
* **Détection de PII multilingue** : `presidio-analyzer` ne supporte pas encore tous les langages. Compléter avec des listes de mots‑clés ou des modèles NER spécifiques.

---

## 4.2 Gestion des erreurs et des time‑outs  

| Code HTTP | Signification | Action recommandée |
|-----------|----------------|-------------------|
| 429 | Too Many Requests | Retry avec back‑off exponentiel (ex. 2 s, 4 s, 8 s) jusqu’à 5 tentatives. |
| 500‑504 | Erreurs serveur | Retry avec jitter (randomisation) pour éviter la thundering herd. |
| 400‑499 (hors 429) | Erreur client (prompt trop long, paramètre invalide) | Log et abandonner la requête. |

```javascript
// Node.js – wrapper API Claude avec retry exponentiel + jitter
const fetch = require('node-fetch');

async function callClaude(payload, maxAttempts = 5) {
  const url = 'https://api.anthropic.com/v1/complete';
  const headers = {
    'Content-Type': 'application/json',
    'x-api-key': process.env.CLAUDE_API_KEY,
    'Accept': 'application/json',
  };

  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 30_000); // 30 s

    try {
      const res = await fetch(url, {
        method: 'POST',
        headers,
        body: JSON.stringify(payload),
        signal: controller.signal,
      });
      clearTimeout(timeout);

      if (res.ok) return await res.json();

      if (res.status === 429 || (res.status >= 500 && res.status <= 504)) {
        const delay = Math.pow(2, attempt) * 1000 + Math.random() * 200;
        await new Promise(r => setTimeout(r, delay));
        continue; // retry
      }

      // autres 4xx → log et abort
      const errBody = await res.text();
      console.error(`Claude error ${res.status}: ${errBody}`);
      throw new Error(`Claude request failed ${res.status}`);
    } catch (e) {
      if (e.name === 'AbortError') {
        console.warn('Claude request timeout, retrying...');
      } else {
        console.error('Unexpected error:', e);
      }
      if (attempt === maxAttempts) throw e;
      const delay = Math.pow(2, attempt) * 1000 + Math.random() * 200;
      await new Promise(r => setTimeout(r, delay));
    }
  }
}
```

### Pièges concrets  
* **Oublier le `AbortController`** : sans timeout, un appel bloqué consomme un thread et empêche le circuit‑breaker de s’activer.

---

## Module 5 — contenu

## 5.1. Architecture générale des intégrations avancées  

| Composant | Rôle | Points de contrôle |
|-----------|------|--------------------|
| **Client** (front‑end, Slack, Teams, IDE…) | Génère le *prompt* et envoie la requête HTTP vers votre service d’orchestration. | Validation du format, filtrage PII. |
| **Service d’orchestration** (Node.js/Express ou Python/FastAPI) | Authentifie, enrichit le prompt, appelle `/v1/complete` (ou `/v1/chat/completions`), gère le streaming et les erreurs, persiste le contexte. | Gestion du `Authorization` header, rotation de clé, back‑off, circuit‑breaker. |
| **Claude API** | Produit le texte ou le code. | `max_tokens`, `temperature`, `stream`. |
| **Webhook de callback** (`POST /claude/webhook`) | Reçoit les fragments de réponse en streaming (si `stream=true`) ou la réponse finale. | Vérification du `request_id`, idempotence, journalisation. |
| **Stockage** (Redis, PostgreSQL) | Conserve le contexte (messages, résumés) et les métriques d’usage. | TTL, éviction de messages hors fenêtre. |
| **Gateway multicanal** | Transforme la réponse Claude en format compatible (Slack blocks, Teams cards, VS Code snippets). | Mapping de `completion` → `text`, `code`, `attachments`. |

---

## 5.2. Intégration : Chatbot multicanal  

### 5.2.1. Flux de travail  

1. **Réception du message** depuis le canal (ex. Slack `event_callback`).  
2. **Filtrage PII** : suppression ou masquage des numéros de sécurité sociale, adresses e‑mail, etc. (regex ou lib `presidio`).  
3. **Construction du prompt** :  
   ```json
   {
     "system": "Tu es un assistant professionnel, réponds en français, style concis.",
     "messages": [
       {"role":"user","content":"<message filtré>"}
     ]
   }
   ```  
4. **Appel à Claude** avec `stream=true`.  
5. **Réception du streaming** via webhook → agrégation des fragments.  
6. **Transformation** du texte en *blocks* Slack (ou *cards* Teams).  
7. **Envoi** de la réponse au canal d’origine.  

### 5.2.2. Exemple de code (Node.js + Express)  

```js
// file: server.js
const express = require('express');
const fetch = require('node-fetch');
const crypto = require('crypto');
require('dotenv').config();

const app = express();
app.use(express.json());

// ---------- 1. Endpoint Slack (receives event) ----------
app.post('/slack/events', async (req, res) => {
  const { type, challenge, event } = req.body;
  // URL verification
  if (type === 'url_verification') return res.json({ challenge });

  // Ignorer les messages du bot lui‑même
  if (event.bot_id) return res.sendStatus(200);

  const rawText = event.text;
  const cleanText = maskPII(rawText); // fonction définie plus bas

  // Construire le payload Claude
  const payload = {
    model: "claude-2.1",
    max_tokens: 1024,
    temperature: 0.3,
    stream: true,
    messages: [
      { role: "system", content: "Tu es un assistant professionnel, réponds en français, style concis." },
      { role: "user", content: cleanText }
    ]
  };

  // Appel asynchrone à Claude (pas d’attente du corps)
  const response = await fetch('https://api.anthropic.com/v1/complete', {
    method: 'POST',
    headers: {
      'x-api-key': process.env.CLAUDE_API_KEY,
      'Content-Type': 'application/json',
      'anthropic-version': '2023-06-01'
    },
    body: JSON.stringify(payload)
  });

  // Récupérer le request_id pour le webhook
  const requestId = response.headers.get('request-id');
  // Persister le mapping Slack→requestId (Redis ou en‑mémoire)
  pending[requestId] = { channel: event.channel, ts: event.ts };
  res.sendStatus(200); // Slack attend un 200 rapidement
});

// ---------- 2. Webhook de callback ----------
app.post('/claude/webhook', async (req, res) => {
  const { request_id, completion, stop_reason, usage } = req.body;
  const pendingInfo = pending[request_id];
  if (!pendingInfo) return res.sendStatus(404); // id inconnu

  // Agrégation du texte (Claude envoie un fragment par appel)
  if (!aggregates[request_id]) aggregates[request_id] = '';
  aggregates[request_id] += completion;

  // Si stop_reason !== null, la réponse est terminée
  if (stop_reason) {
    const finalText = aggregates[request_id];
    delete aggregates[request_id];
    delete pending[request_id];

    // Format Slack Block Kit
    const blocks = [
      { type: "section", text: { type: "mrkdwn", text: finalText } }
    ];
    await fetch('https://slack.com/api/chat.postMessage', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${process.env.SLACK_BOT_TOKEN}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        channel: pendingInfo.channel,
        thread_ts: pendingInfo.ts,