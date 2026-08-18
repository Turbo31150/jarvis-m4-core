# Claude Code Pro

> Référence `claude-code-pro` · 49 €

## Plan

## Module 1 – Architecture et principes de Claude 2  
**Objectif mesurable** : L’apprenant pourra expliquer le fonctionnement interne de Claude 2 et identifier les composants clés d’une requête, avec un taux de réussite ≥ 85 % à un quiz de 20 questions.  
- Modèle de transformeur à attention multi‑têtes (decoder‑only)  
- Mémoire contextuelle : fenêtre de contexte (≈ 100 k tokens) et gestion du « truncation »  
- Méthodes d’inférence : décodage greedy, top‑p (nucleus) et temperature  
- Alignement par RLHF (Reinforcement Learning from Human Feedback) et supervision fine‑tuned  
- Limites de hallucination et métriques de factualité (BLEU, ROUGE, BERTScore)

## Module 2 – Prompt Engineering avancé pour la génération de code  
**Objectif mesurable** : L’apprenant rédigera des prompts qui produisent du code fonctionnel (tests unitaires passés) dans 4 / 5 cas d’usage différents, validés par un script d’évaluation automatisé.  
- Structuration du prompt : rôle, contexte, consignes, exemples (few‑shot)  
- Techniques de chain‑of‑thought et de self‑refinement  
- Utilisation de balises de langage (```python```, ```//```…) et de directives de style (PEP 8, Google Style)  
- Gestion des dépendances et des imports via prompt  
- Détection et correction d’erreurs de compilation générées par le modèle

## Module 3 – Intégration de Claude dans les environnements de développement  
**Objectif mesurable** : L’apprenant configurera et utilisera l’API Claude dans VS Code et GitHub Copilot like, en automatisant au moins deux flux de travail (ex. génération de stub, revue de PR) avec succès démontré par des logs d’exécution.  
- Authentification OAuth 2.0 et gestion des tokens d’accès  
- Appels REST / gRPC à l’API Claude (endpoints : /v1/completions, /v1/stream)  
- Extensions VS Code : création d’un “Claude Assistant” (Webview, commands)  
- CI/CD : intégration dans les pipelines GitHub Actions (ex. linting, génération de doc)  
- Sécurité des prompts : filtrage des données sensibles (PII, secrets)

## Module 4 – Tests, validation et debugging automatisés du code généré  
**Objectif mesurable** : L’apprenant mettra en place un pipeline de test qui détecte et corrige automatiquement ≥ 80 % des défauts de syntaxe et logique dans le code produit par Claude.  
- Génération de tests unitaires avec pytest via prompt  
- Utilisation de coverage py et mutation testing (mutmut) pour évaluer la robustesse  
- Boucle de feedback : re‑prompting basé sur les sorties d’erreur (traceback)  
- Analyse statique (flake8, mypy) intégrée au processus de génération  
- Gestion des dépendances de version (requirements.txt, poetry)

## Module 5 – Optimisation des coûts et gouvernance de l’IA générative  
**Objectif mesurable** : L’apprenant pourra réduire la dépense d’API Claude d’au moins 30 % tout en maintenant la qualité du code, et documentera une politique de gouvernance conforme au

---

## Module 1 — contenu

## 1.1 Architecture interne de Claude 2  

| composant | rôle | référence |
|-----------|------|-----------|
| **Decoder‑only Transformer** | génère le texte token par token à partir d’une séquence d’entrée (pas d’encodeur séparé). | Vaswani et al., *Attention is All You Need*, 2017 |
| **Bloc multi‑head attention** | chaque tête calcule `Attention(Q,K,V) = softmax(QKᵀ/√d_k) V`. Le modèle agrège `h` têtes (h ≈ 32) puis projette le résultat. | même source |
| **Feed‑Forward Network (FFN)** | deux couches linéaires séparées par GELU, dimension interne `d_ff ≈ 4·d_model`. | idem |
| **Layer‑Norm + résidu** | stabilise l’entraînement, ajoute l’entrée du bloc à sa sortie. | idem |
| **Positional embeddings** | encode la position relative des tokens (rotary embeddings dans Claude 2). | Su et al., *RoFormer*, 2021 |
| **Paramètres** | `d_model ≈ 8192`, `L ≈ 80` couches, `≈ 2,5 × 10⁹` poids. | Anthropic, doc technique 2023 |

### 1.1.1 Flux de données (simplifié)

```
input tokens → embedding + positional → L × [MHA → Add & Norm → FFN → Add & Norm] → LM head → logits → token sampling
```

---

## 1.2 Mémoire contextuelle  

* **Fenêtre de contexte** : ≈ 100 k tokens (≈ 750 k caractères).  
* **Truncation** : si le prompt + les tokens déjà générés dépassent la fenêtre, les tokens les plus anciens sont supprimés (policy « first‑in‑first‑out »).  
* **Sliding‑window** (optionnel) : on peut garder les `N` derniers tokens et ré‑injecter les résumés des parties supprimées via un prompt de rappel.  

> **Piège** : lorsqu’on dépasse la fenêtre, le modèle « oublie » les informations précédentes ; les réponses peuvent devenir incohérentes si le rappel n’est pas explicite.

---

## 1.3 Méthodes d’inférence  

| méthode | formule de sélection | usage typique |
|---------|----------------------|---------------|
| **Greedy** | `argmax_i p_i` | génération déterministe, rapide, mais souvent monotone. |
| **Top‑p (nucleus)** | garde le plus petit ensemble `S` tel que `∑_{i∈S} p_i ≥ p` (p ∈ [0,1]), puis échantillonne dans `S`. | équilibre diversité et cohérence; p ≈ 0.9 recommandé. |
| **Temperature** | modifie les logits : `p_i ∝ exp(logit_i / T)`. T < 1 rend la distribution plus pointue, T > 1 plus plate. | réglage fin de la créativité ; T = 0.7 souvent bon compromis. |
| **Top‑k** (occasionnel) | conserve les `k` plus probables tokens. | utile quand on veut limiter le vocabulaire (k ≈ 50). |

> **Piège** : combiner `temperature > 1` avec `top‑p ≈ 0.9` peut générer des sorties incohérentes ; il faut tester chaque combinaison.

---

## 1.4 Alignement par RLHF  

1. **Pré‑entraînement** (large‑scale language modeling) → minimise la perte de cross‑entropy sur un corpus de plusieurs téra‑tokens.  
2. **Supervised Fine‑Tuning (SFT)** : jeux de prompts‑réponses humains (≈ 10 M exemples) ; le modèle apprend à imiter les réponses souhaitées.  
3. **Reward Model (RM)** : un classifieur entraîné à prédire le score humain (échelle 0‑1) à partir de `(prompt, réponse)`.  
4. **Proximal Policy Optimization (PPO)** : le modèle de politique (Claude) est ajusté pour maximiser l’espérance du reward tout en restant proche de la politique SFT (`KL‑penalty`).  

> **Piège** : le RM peut refléter les biais du jeu de données d’évaluation ; une mauvaise calibration entraîne des réponses “plausibles mais fausses”.

---

## 1.5 Hallucinations et métriques de factualité  

| métrique | ce qu’elle mesure | limites |
|----------|-------------------|----------|
| **BLEU** | n‑gram overlap (1‑4) avec référence(s). | sensible aux variations lexicales, pas de véracité. |
| **ROUGE‑L** | plus longue sous‑séquence commune. | même limitation que BLEU. |
| **BERTScore** | similarité sémantique via embeddings (cosine). | dépend du modèle de base, ne détecte pas les erreurs factuelles. |
| **FactCC** (202

---

## Module 2 — contenu

## Module 2 – Prompt Engineering avancé pour la génération de code  

### 2.1. Structuration du prompt  

| Élément | Rôle | Syntaxe recommandée |
|--------|------|---------------------|
| **Rôle** | Définit le point de vue du modèle (ex. « You are a senior Python developer »). | `You are a senior Python developer.` |
| **Contexte** | Donne les informations de domaine, les contraintes d’environnement, les versions de bibliothèques. | `The project uses Python 3.11, FastAPI 0.104, and PostgreSQL 15.` |
| **Consignes** | Liste les exigences fonctionnelles et non‑fonctionnelles (style, tests, performance). | `- Write a function that …\n- Follow PEP 8.\n- Include type hints.` |
| **Exemples (few‑shot)** | Fournit un ou deux exemples d’entrée/sortie pour ancrer le format attendu. | ```\n# Example 1\nInput: …\nOutput: …\n``` |
| **Délimiteurs de code** | Encadre le code avec des fences de langage afin que le modèle ne mélange pas texte et code. | ````python\n...code...\n```` |
| **Balises de style** | Indique explicitement le guide de style à appliquer. | `Apply Google Python Style Guide.` |
| **Prompt final** | Concatène les blocs dans l’ordre : rôle → contexte → consignes → exemples → tâche. | `You are a senior Python developer.\nThe project uses …\n- Write …\n- Follow …\n# Example …\nWrite the function …` |

> **Bon à savoir** : chaque ligne séparée par un double saut de ligne augmente la probabilité que le modèle considère le bloc comme une unité sémantique distincte.

### 2.2. Techniques de Chain‑of‑Thought (CoT)  

1. **Décomposition explicite** – demander au modèle de « penser à haute voix » avant de produire le code.  
   ```text
   Step 1: Identify inputs and outputs.
   Step 2: Choose the appropriate data structures.
   Step 3: Sketch the algorithm in pseudocode.
   Step 4: Translate to Python with type hints.
   ```  
2. **Utilisation du token `'''THINK'''`** (ou tout marqueur unique) pour séparer la réflexion du code. Le modèle a montré une amélioration moyenne de 12 % du taux de réussite sur les tâches de génération de fonctions complexes (benchmark OpenAI 2023).  
3. **Self‑refinement** – après la première génération, ré‑injecter le code et les erreurs éventuelles dans un second prompt :  
   ```text
   The previous code raised the following error: <traceback>.
   Refactor the function to fix the error while preserving the original API.
   ```

### 2.3. Directives de style et de documentation  

| Directive | Exemple concret | Impact mesurable |
|-----------|----------------|------------------|
| **PEP 8** | `import os\n\ndef foo(bar: int) -> None:` | `flake8` score ≥ 9.0 |
| **Google Style** | Docstring format : `"""Summary.\n\nArgs:\n    x (int): …\n\nReturns:\n    bool: …\n"""` | `pydocstyle` passes |
| **Type hints** | `def add(a: int, b: int) -> int:` | `mypy` passes with `--strict` |
| **Explicit imports** | `from pathlib import Path` (avoid `import *`) | Réduction de 27 % des warnings `flake8 F403` |
| **Dependency declaration** | `# requirements.txt\nfastapi==0.104.0\nuvicorn[standard]==0.23.2` | CI : `pip install -r requirements.txt` ne génère pas de conflits de version |

### 2.4. Gestion des dépendances via le prompt  

- **Demander la version exacte** : `Specify the exact version of any third‑party library you import.`
- **Inclure un bloc `requirements.txt`** dans la réponse :  
  ```text
  # requirements.txt
  fastapi==0.104.0
  sqlalchemy==2.0.20
  ```
- **Utiliser `poetry add`** si le projet est géré par Poetry :  
  ```text
  Add the following line to pyproject.toml under [tool.poetry.dependencies]:
  fastapi = "^0.104.0"
  ```

### 2.5. Détection et correction d’erreurs de compilation  

1. **Boucle de validation** :  
   - Prompt 1 → génération du code.  
   - Exécution `python -m py_compile <file>` (ou `mypy` pour typage).  
   - Capture du traceback.  
   - Prompt 2 → « Correct the syntax error(s) shown below ».  
2. **Prompt de correction typique** :  
   ```text
   The following code fails to compile:
   <code block>

   Fix the syntax errors without changing the function signature.
   ```  
3. **Utilisation de `--logprobs`** (si l’API le permet) pour repérer les tokens les plus incertains ; les remplacer par des suggestions explicites dans le prompt (ex. « use `:` after the function name »).

### 2.6. Exemple complet de prompt et de réponse  

#### Prompt  

```text
You are a senior Python developer.
The project uses Python 3.11, FastAPI 0.104, and PostgreSQL 15.
- Write an endpoint `/items/{item_id}` that returns an item from a PostgreSQL table `items`.
-

---

## Module 3 — contenu

## Module 3 – Intégration de Claude dans les environnements de développement  

### 3.1 Authentification OAuth 2.0 et gestion des tokens  

| Étape | Action | Détails vérifiables |
|------|--------|----------------------|
| 1. Enregistrement de l’application | Créez une **client‑id** et **client‑secret** dans le portail Anthropic → *Developer Settings* → *OAuth Apps*. | L’URL de création : `https://console.anthropic.com/settings/oauth`. |
| 2. Autorisation | Redirigez l’utilisateur vers `https://api.anthropic.com/oauth/authorize?response_type=code&client_id=YOUR_CLIENT_ID&redirect_uri=YOUR_REDIRECT_URI&scope=read+write`. | Le paramètre `scope` accepte `read` et `write`. |
| 3. Échange du code d’autorisation | POST `https://api.anthropic.com/oauth/token` avec `grant_type=authorization_code`, `code=AUTH_CODE`, `redirect_uri`, `client_id`, `client_secret`. Retourne `access_token` (JWT) et `refresh_token`. |
| 4. Rafraîchissement du token | POST identique avec `grant_type=refresh_token` et `refresh_token`. | Le `access_token` a une durée de vie de 3600 s (1 h). |
| 5. Stockage sécurisé | Utilisez le **keyring** du système ou un secret manager (ex. HashiCorp Vault). Ne jamais hard‑coder les secrets. |

```python
# token_manager.py – gestion sécurisée du token OAuth
import os
import time
import requests
import keyring  # pip install keyring

CLIENT_ID = os.getenv("CLAUDE_CLIENT_ID")
CLIENT_SECRET = os.getenv("CLAUDE_CLIENT_SECRET")
REDIRECT_URI = "http://localhost:8080/callback"
TOKEN_SERVICE = "anthropic_claude"

TOKEN_ENDPOINT = "https://api.anthropic.com/oauth/token"

def store_token(token: str, refresh: str, expires_in: int) -> None:
    """Enregistre le token et sa date d’expiration dans le keyring."""
    keyring.set_password(TOKEN_SERVICE, "access_token", token)
    keyring.set_password(TOKEN_SERVICE, "refresh_token", refresh)
    keyring.set_password(TOKEN_SERVICE, "expires_at", str(int(time.time()) + expires_in))

def load_token() -> dict:
    """Récupère le token, le rafraîchit si expiré."""
    access = keyring.get_password(TOKEN_SERVICE, "access_token")
    refresh = keyring.get_password(TOKEN_SERVICE, "refresh_token")
    expires_at = int(keyring.get_password(TOKEN_SERVICE, "expires_at") or "0")
    if time.time() >= expires_at:
        # rafraîchir
        resp = requests.post(
            TOKEN_ENDPOINT,
            data={
                "grant_type": "refresh_token",
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "refresh_token": refresh,
            },
        )
        resp.raise_for_status()
        data = resp.json()
        store_token(data["access_token"], data["refresh_token"], data["expires_in"])
        access = data["access_token"]
    return {"Authorization": f"Bearer {access}"}
```

**Piège :**
- **Expiration silencieuse** : si le token est utilisé après expiration, l’API renvoie `401 Unauthorized`. Toujours vérifier `expires_at` avant chaque appel.  
- **Scope insuffisant** : un token créé avec uniquement `read` bloque les appels `POST /v1/completions`.  

---

### 3.2 Appels REST / gRPC à l’API Claude  

#### 3.2.1 Endpoint `/v1/completions` (REST)  

```python
# claude_api.py – wrapper minimal
import json
import requests
from token_manager import load_token

API_URL = "https://api.anthropic.com/v1/completions"

def complete(prompt: str,
             model: str = "claude-2.1",
             max_tokens: int = 1024,
             temperature: float = 0.0,
             top_p: float = 1.0) -> str:
    """
    Envoie un prompt et renvoie le texte généré.
    """
    headers = load_token()
    headers.update({
        "Content-Type": "application/json",
        "anthropic-version": "2023-06-01"
    })
    payload = {
        "model": model,
        "prompt": prompt,
        "max_tokens_to_sample": max_tokens,
        "temperature": temperature,
        "top_p": top_p,
    }
    resp = requests.post(API_URL, headers=headers, data=json.dumps(payload))
    resp.raise_for_status()
    return resp.json()["completion"]
```

#### 3.2.2 Streaming via `/v1/stream` (Server‑Sent Events)  

```python
def stream_complete(prompt: str, **kwargs):
    """
    Génère du texte en temps réel. Retourne un générateur de fragments.
    """
    headers = load_token()
    headers.update({
        "Content-Type": "application/json",
        "anthropic-version": "2023-06-01",
        "Accept": "text/event-stream"
    })
    payload = {"prompt": prompt, "model": "claude-2.1", **kwargs}
    with requests.post(
        "https://api.anthropic.com/v1/stream",
        headers=headers,
        json=payload,
        stream=True,
    ) as r:
        r.raise_for_status()
        for line in r.iter_lines(decode_unicode=True):
            if line.startswith("data: "):
                data = json.loads(line[6:])
                if "completion" in data:
                    yield data["completion"]
                if data.get("stop_reason"):
                    break
```

**Piège :**
- **Mauvaise version d’API** : le header `anthropic-version`

---

## Module 4 — contenu

## Module 4 – Tests, validation et debugging automatisés du code généré  

### 4.1 Objectif mesurable  
- Mettre en place, dans un dépôt Git, un pipeline CI qui :  
  1. Exécute les tests unitaires générés par Claude (pytest).  
  2. Mesure la couverture avec **coverage.py** (target ≥ 80 %).  
  3. Lance **mutmut** pour le mutation testing (score ≥ 60 %).  
  4. Ré‑invite Claude avec le traceback lorsqu’une exécution échoue.  
- Atteindre un taux de correction automatique ≥ 80 % des défauts de syntaxe et de logique détectés pendant la CI.  

---

### 4.2 Architecture du pipeline  

| Étape | Outil | Rôle | Commande typique |
|------|-------|------|-------------------|
| 1. Génération du code | Claude (prompt `# generate function …`) | Produit le fichier source (`module.py`). | `curl -X POST …/v1/completions …` |
| 2. Génération des tests | Claude (prompt `# generate pytest for module.py`) | Crée `tests/test_module.py`. | idem |
| 3. Linting & typage | **flake8**, **mypy** | Détecte erreurs de style et incohérences de type. | `flake8 module.py`<br>`mypy module.py` |
| 4. Exécution des tests | **pytest** | Vérifie le comportement fonctionnel. | `pytest -q` |
| 5. Couverture | **coverage.py** | Calcule % de lignes exécutées. | `coverage run -m pytest && coverage report -m` |
| 6. Mutation testing | **mutmut** | Mesure la robustesse des tests (score = % de mutants tués). | `mutmut run && mutmut results` |
| 7. Boucle de feedback | Script Python `re_prompt.py` | Capture le traceback, reformule le prompt, renvoie à Claude. | `python re_prompt.py` |
| 8. CI/CD | **GitHub Actions** | Orchestration automatisée. | `.github/workflows/ci.yml` |

---

### 4.3 Implémentation détaillée  

#### 4.3.1 Fichier `re_prompt.py` (exemple complet)  

```python
#!/usr/bin/env python3
"""
Script de boucle de feedback pour le code généré par Claude.
1. Exécute pytest ; capture la sortie.
2. Si un test échoue, extrait le traceback.
3. Construit un prompt de correction et le renvoie à l'API Claude.
4. Écrase le fichier source avec la version corrigée.
"""

import json, subprocess, os, sys, textwrap, pathlib, requests

API_URL = "https://api.anthropic.com/v1/completions"
API_KEY = os.getenv("CLAUDE_API_KEY")
HEADERS = {
    "x-api-key": API_KEY,
    "anthropic-version": "2023-06-01",
    "content-type": "application/json",
}
MODEL = "claude-2.1"

def run_pytest() -> subprocess.CompletedProcess:
    """Lance pytest en mode capture et renvoie l'objet CompletedProcess."""
    return subprocess.run(
        ["pytest", "-q"], capture_output=True, text=True, check=False
    )

def extract_failure(output: str) -> str:
    """
    Retourne le dernier bloc de traceback contenant le mot clé 'AssertionError'.
    Si aucune assertion, renvoie le premier traceback trouvé.
    """
    blocks = output.split("\n\n")
    for block in reversed(blocks):
        if "AssertionError" in block:
            return block.strip()
    # fallback
    for block in reversed(blocks):
        if "Traceback (most recent call last)" in block:
            return block.strip()
    return ""

def build_prompt(source_path: pathlib.Path, failure: str) -> str:
    """
    Prompt de correction :
    - rôle : assistant de debugging Python
    - contexte : code source complet
    - consigne : corriger le bug indiqué par le traceback, ne pas changer l'API.
    """
    source = source_path.read_text(encoding="utf8")
    return textwrap.dedent(f"""
        Vous êtes un assistant de debugging Python.  
        Vous recevez le code source ci‑dessous et un traceback d’erreur.  
        Corrigez le code de façon à ce que le test passe, sans modifier les
        signatures de fonction ni les imports.

        ```python
        {source}
        ```

        Traceback :
        ```
        {failure}
        ```

        Retournez **uniquement** le code complet corrigé, entouré de balises
        ```python ... ``` sans aucune explication supplémentaire.
    """)

def call_claude(prompt: str) -> str:
    payload = {
        "model": MODEL,
        "max_tokens": 2048,
        "temperature": 0.0,
        "top_p": 1,
        "messages": [{"role": "user", "content": prompt}],
    }
    resp = requests.post(API_URL, headers=HEADERS, json=payload, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    # Anthropic renvoie la réponse dans `completion`
    return data["completion"]

def replace_source(source_path: pathlib.Path, new_code: str):
    # Le modèle renvoie parfois des backticks supplémentaires ; on les nettoie.
    cleaned = new_code.strip()
    if cleaned.startswith("```python"):
        cleaned = cleaned[len("```python") :].strip()
    if cleaned.endswith("```"):
        cleaned = cleaned[: -len("```")].strip()
    source_path.write_text(cleaned + "\n", encoding="utf8")

def main():
    src = pathlib.Path("module.py")
    result = run_pytest()
    if result.returncode == 0:
        print("✅ Tous les tests passent.")
        sys

---

## Module 5 — contenu

## 5. Optimisation des coûts et gouvernance de l’IA générative

### 5.1 Principes de réduction de la facture Claude

| Facteur | Impact sur le coût | Méthode de réduction | Vérification |
|--------|-------------------|----------------------|--------------|
| **Nombre de tokens d’entrée** | Directement proportionnel au tarif (`$0.015 / 1 k tokens` pour Claude‑2) | - **Prompt compression** : supprimer les parties redondantes, utiliser des alias (`{{code}}`), externaliser les données volumineuses dans des fichiers. <br>- **Few‑shot minimal** : ne garder que le(s) exemple(s) indispensable(s). | Comparez `len(prompt)` avant/après avec `len(tokenize(prompt))`. |
| **Nombre de tokens de sortie** | Même tarif que les tokens d’entrée | - **Limite de `max_tokens`** à la valeur réellement nécessaire (ex. 150 au lieu de 500). <br>- **Stop‑sequences** (`"\n\n"` ou `"# End"` ) pour éviter les digressions. | Loggez `completion.usage.completion_tokens`. |
| **Fréquence d’appel** | Multiplication du coût par appel | - **Batching** : regroupez plusieurs requêtes (ex. génération de stubs pour 5 fonctions) dans un même prompt. <br>- **Cache** : réutilisez les réponses déjà obtenues (hash du prompt → réponse). | Ratio `hits / total` du cache. |
| **Modèle** | Claude‑2 > Claude‑1.5 > Claude‑Instant | - **Sélection dynamique** : n’utiliser Claude‑2 que pour les tâches critiques (ex. refactoring). <br>- **Fallback** : si le prompt est simple (ex. docstring), appeler Claude‑Instant. | Table de mapping `task → model`. |
| **Paramètres de décodage** | `temperature` et `top_p` n’influent pas sur le prix, mais influencent le nombre de tokens générés (plus de diversité → plus de texte). | - **Temperature = 0** pour code (déterministe, moins de texte). <br>- **Top‑p = 0.9** uniquement pour génération de texte libre. | Comparez `completion.usage.total_tokens` avec différents paramètres. |

### 5.2 Implémentation concrète : wrapper Python avec cache et compression

```python
# file: claude_wrapper.py
import os
import json
import hashlib
import time
from pathlib import Path
import requests
from typing import List, Dict, Any

# ----------------------------------------------------------------------
# Configuration (gouvernance)
# ----------------------------------------------------------------------
API_URL = "https://api.anthropic.com/v1/complete"
API_KEY = os.getenv("CLAUDE_API_KEY")          # secret géré par le CI/CD
MODEL_DEFAULT = "claude-2.0"
MODEL_INSTANT = "claude-instant-1.2"
CACHE_DIR = Path(os.getenv("CLAUDE_CACHE_DIR", ".claude_cache"))
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# ----------------------------------------------------------------------
# Utilitaires
# ----------------------------------------------------------------------
def _hash_prompt(prompt: str, model: str) -> str:
    """Retourne un hash SHA‑256 stable du prompt + modèle."""
    h = hashlib.sha256()
    h.update(model.encode("utf-8"))
    h.update(b"\0")
    h.update(prompt.encode("utf-8"))
    return h.hexdigest()

def _load_from_cache(key: str) -> Dict[str, Any] | None:
    cache_file = CACHE_DIR / f"{key}.json"
    if cache_file.is_file():
        with cache_file.open("r", encoding="utf-8") as f:
            return json.load(f)
    return None

def _save_to_cache(key: str, payload: Dict[str, Any]) -> None:
    cache_file = CACHE_DIR / f"{key}.json"
    with cache_file.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

def _compress_prompt(prompt: str, max_len: int = 3000) -> str:
    """
    Réduit la taille du prompt en :
    1. Remplaçant les blocs de code par des placeholders.
    2. Supprimant les lignes vides et les commentaires inutiles.
    3. Troncant les exemples à `max_len` tokens (approx. 4 char/token).
    """
    # 1. Placeholder
    prompt = prompt.replace("```python", "<<<CODE>>>")
    # 2. Nettoyage
    lines = [l.strip() for l in prompt.splitlines() if l.strip() and not l.strip().startswith("#")]
    compact = " ".join(lines)
    # 3. Troncature
    if len(compact) > max_len:
        compact = compact[:max_len] + " ..."
    return compact

# ----------------------------------------------------------------------
# Core API call (coût contrôlé)
# ----------------------------------------------------------------------
def claude_complete(
    prompt: str,
    *,
    model: str = MODEL_DEFAULT,
    max_tokens: int = 150,
    temperature: float = 0.0,
    stop: List[str] | None = None,
    use_cache: bool = True,
    fallback_to_instant: bool = True,
) -> str:
    """
    Retourne la complétion Claude en appliquant :
    - compression du prompt,
    - cache SHA‑256,
    - fallback vers Claude‑Instant si le coût estimé dépasse 0.02 $.
    """
    # 1. Compression
    prompt_c