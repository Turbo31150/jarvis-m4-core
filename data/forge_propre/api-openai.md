# API OpenAI — Intégration Avancée

> Référence `api-openai` · €  

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
5. Impact des tokens sur le coût et sur la latence.

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
| 2 | Cliquer **Create new secret key** | Le bouton crée une chaîne alphanumérique (ex. `sk-...`). |
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
| **Automatiser la rotation** | Script CI/CD (ex. GitHub Actions) qui :<br>1. Crée une nouvelle clé<br>2. Met à jour le secret manager<br>3. Révoque l’ancienne | Garantit un intervalle (recommandation OpenAI). |

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
  "temperature": ,
  "max_tokens": ,
  "top_p": ,
  "frequency_penalty": ,
  "presence_penalty": ,
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
  "temperature": ,
  "max_tokens": ,
  "top_p": ,
  "frequency_penalty": ,
  "presence_penalty": ,
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
| `max_tokens` | int | (selon le modèle) | Nombre maximal de tokens générés. |
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
    # Si le budget restant est très faible, on restreint la créativité
    if remaining_budget_usd <  :
        return {"temperature": , "max_tokens": }
    # Sinon on autorise plus de créativité
    return {"temperature": , "max_tokens": }
```

> **Vérifiable** : les tarifs sont affichés dans le tableau tarifaire d’OpenAI (section *Pricing*).  

---

## Module 3 — contenu

## 3.1 Tokenisation avec **tiktoken**

| Concept | Détails vérifiables |
|---------|----------------------|
| Modèle de tokenisation | `tiktoken.encoding_for_model("gpt-3.5-turbo")` renvoie l’encoding utilisé par le modèle. |
| Token = unité de texte (souvent un sous‑mot). | La même chaîne `"ChatGPT"` → 2 tokens (`"Chat"` + `"GPT"`). |
| Coût = nombre de tokens * prix du modèle (ex. $/ tokens pour `gpt‑3.5‑turbo`). | Calcul direct. |

```python
import tiktoken

def get_encoding(model: str = "gpt-3.5-turbo"):
    """Retourne l'objet d'encodage correspondant au modèle."""
    return tiktoken.encoding_for_model(model)

def count_tokens(text: str, model: str = "gpt-3