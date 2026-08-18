# IA & Productivité Personnelle

> Référence `ia-productivite` · 39 €

## Plan

## Module 1 – Automatisation des tâches récurrentes avec des scripts IA  
**Objectif mesurable** : Être capable de concevoir, tester et déployer un script Python qui utilise l’API OpenAI pour automatiser au moins trois processus quotidiens (ex. tri d’emails, génération de rapports, mise à jour de bases de données).  
- Appels REST à l’API OpenAI (authentification, gestion des quotas)  
- Prompt engineering : structuration de prompts pour des réponses déterministes  
- Gestion des flux de travail avec `asyncio` et `aiohttp`  
- Persistance des résultats (SQLite, CSV, Google Sheets)  
- Mise en place de logs et de notifications (Slack, email)

## Module 2 – Assistants de prise de notes et de synthèse en temps réel  
**Objectif mesurable** : Produire un outil qui capture l’audio d’une réunion, le transcrit via Whisper, puis génère un résumé structuré exploitable dans un système de gestion de tâches.  
- Utilisation de Whisper (modèle `base` ou `large`) via `whisper.cpp` ou l’API OpenAI  
- Post‑traitement du texte : nettoyage, détection de points d’action, extraction d’entités nommées (spaCy)  
- Génération de résumés avec GPT‑3.5/4 (prompt de type “extractive + abstractive”)  
- Export vers Markdown, Notion ou Todoist via leurs APIs  
- Gestion des erreurs de transcription (confidence scores, re‑prompting)

## Module 3 – Optimisation de la gestion de projets par IA  
**Objectif mesurable** : Implémenter un tableau de bord qui prédit les retards de tâches et propose des réallocations de ressources basées sur l’historique du projet.  
- Modélisation de séries temporelles avec Prophet ou ARIMA sur les durées de tâches  
- Classification des risques (logistique, technique) via un modèle fine‑tuned BERT  
- Intégration avec des outils de suivi (Jira, Trello) via leurs webhooks  
- Visualisation dynamique avec Plotly/Dash ou Streamlit  
- Boucle de rétroaction : mise à jour du modèle à chaque sprint

## Module 4 – Génération de code assistée pour accélérer le développement  
**Objectif mesurable** : Utiliser Codex ou GPT‑4‑Code pour créer, tester et documenter automatiquement au moins deux modules fonctionnels dans un projet existant.  
- Appels à l’API `code-davinci-002` ou `gpt-4-code` (paramètres `temperature=0`, `max_tokens`)  
- Validation syntaxique et linting automatisés (flake8, black)  
- Génération de tests unitaires avec `pytest` à partir de spécifications en langage naturel  
- Documentation auto‑générée (docstrings, Sphinx)  
- Gestion des versions avec Git (branches, PR automatisées)

## Module 5 – Sécurité et conformité des solutions IA de productivité  
**Objectif mesurable** : Auditer un workflow IA existant et appliquer au moins trois correctifs pour garantir la conformité RGPD et la robustesse contre les injections de prompt.  
- Analyse des flux de données personnelles (identification, chiffrement AES‑256)  
- Mise en place de filtres de contenu (OpenAI Moderation endpoint)  
- Stratégies de défense contre les “prompt injection” (

---

## Module 1 — contenu

## 1.1. Appels REST à l’API OpenAI  

| Élément | Détails techniques vérifiables |
|--------|--------------------------------|
| **Endpoint** | `https://api.openai.com/v1/chat/completions` (Chat) ou `https://api.openai.com/v1/completions` (Legacy). |
| **Authentification** | Header `Authorization: Bearer <API_KEY>`. La clé doit être stockée dans une variable d’environnement (`OPENAI_API_KEY`) ou dans un secret manager. |
| **Quota & limites** | 60 req/minute par compte (plan « Pay‑as‑you‑go ») – documenté dans la page *Rate limits* du tableau de bord OpenAI. |
| **Payload minimal** | ```json { "model": "gpt-4o-mini", "messages": [{ "role": "user", "content": "…" }], "temperature": 0 }``` |
| **Gestion des erreurs** | 4xx → problème de requête (ex. `401` auth, `429` rate‑limit). 5xx → problème serveur (retry avec back‑off exponentiel). |

> **Bon à savoir** : le champ `max_tokens` représente le nombre maximal de tokens renvoyés, pas le nombre d’entrée. Le calcul du coût doit inclure les tokens d’entrée + de sortie.

---

## 1.2. Prompt engineering pour des réponses déterministes  

1. **Structure fixe** – Utiliser le même schéma de messages (`system` → `assistant` → `user`) à chaque appel.  
2. **Contraintes explicites** – Ajouter `temperature: 0`, `top_p: 1`, `presence_penalty: 0`, `frequency_penalty: 0`.  
3. **Format de sortie** – Demander un JSON valide et encadrer la réponse avec des balises ```json … ``` afin de faciliter le parsing.  

```text
System: Vous êtes un assistant qui ne génère que du JSON valide.
User: Retourne les informations suivantes pour chaque e‑mail reçu aujourd’hui : { "subject", "sender", "date", "category" }. Utilise les catégories suivantes : ["Facture", "Invitation", "Spam", "Autre"].
```

---

## 1.3. Gestion asynchrone avec `asyncio` et `aiohttp`

```python
import os
import asyncio
import json
from typing import List, Dict

import aiohttp

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
BASE_URL = "https://api.openai.com/v1/chat/completions"
HEADERS = {
    "Authorization": f"Bearer {OPENAI_API_KEY}",
    "Content-Type": "application/json",
}


async def call_openai(messages: List[Dict[str, str]]) -> Dict:
    """Envoi d’une requête chat à OpenAI avec gestion du timeout et du retry."""
    payload = {
        "model": "gpt-4o-mini",
        "messages": messages,
        "temperature": 0,
        "max_tokens": 500,
    }

    retry = 0
    backoff = 1
    while retry < 5:
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    BASE_URL, headers=HEADERS, json=payload, timeout=30
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data["choices"][0]["message"]
                    elif resp.status == 429:  # rate‑limit
                        await asyncio.sleep(backoff)
                        backoff *= 2
                        retry += 1
                    else:
                        txt = await resp.text()
                        raise RuntimeError(f"OpenAI error {resp.status}: {txt}")
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                await asyncio.sleep(backoff)
                backoff *= 2
                retry += 1
    raise RuntimeError("Maximum retries exceeded")
```

*Points clés*  
* `aiohttp.ClientSession` doit être créé **à l’intérieur** de la boucle de retry pour éviter les connexions orphelines.  
* Le `timeout` de 30 s couvre le temps total de la requête ; ajuster en fonction de la longueur du prompt.  
* Le back‑off exponentiel empêche les blocages de quota.

---

## 1.4. Persistance des résultats  

### 1.4.1. SQLite (fichier local)

```python
import sqlite3
from pathlib import Path

DB_PATH = Path("automation.db")

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS email_tri (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject TEXT,
                sender TEXT,
                date TEXT,
                category TEXT,
                processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()

def insert_email(record: dict):
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO email_tri (subject, sender, date, category)
            VALUES (:subject, :sender, :date, :category)
            """,
            record,
        )
        conn.commit()
```

*Remarque* : SQLite ne supporte pas le parallélisme d’écriture multi‑processus sans `PRAGMA journal_mode=WAL`. Dans un script `asyncio` unique, le verrouillage est géré automatiquement.

### 1.4.2. Export CSV (fallback)

```python
import csv
from

---

## Module 2 — contenu

## 2.1 Capture audio de la réunion  

| Étape | Bibliothèque | Code minimal | Remarque |
|------|--------------|--------------|----------|
| Enregistrement en temps réel (16 kHz, mono) | `sounddevice` + `numpy` | ```python\nimport sounddevice as sd, wave, numpy as np\nfs = 16000\nseconds = 300  # durée max, à adapter\nprint('Enregistrement…')\naudio = sd.rec(int(seconds * fs), samplerate=fs, channels=1, dtype='int16')\nsd.wait()\nwave_file = 'meeting.wav'\nwith wave.open(wave_file, 'wb') as wf:\n    wf.setnchannels(1)\n    wf.setsampwidth(2)  # 16 bits\n    wf.setframerate(fs)\n    wf.writeframes(audio.tobytes())\nprint('Fichier enregistré :', wave_file)\n``` | `sounddevice` nécessite les drivers PortAudio ; sur Linux, installer `python3‑portaudio` ou `apt-get install libportaudio2`. |
| Découpage en segments de 30 s (facultatif) | `pydub` | ```python\nfrom pydub import AudioSegment\naudio = AudioSegment.from_wav('meeting.wav')\nsegment_len = 30_000  # ms\nsegments = [audio[i:i+segment_len] for i in range(0, len(audio), segment_len)]\nfor idx, seg in enumerate(segments):\n    seg.export(f'segment_{idx}.wav', format='wav')\n``` | Le découpage réduit le temps de latence de Whisper et simplifie la gestion des quotas. |

### Piège 1 – Qualité du signal  
- **Bruit de fond > -30 dBFS** → taux d’erreur élevé.  
- Utiliser un micro directionnel ou placer le dispositif près du haut‑parleur.  
- Appliquer un filtre passe‑haut (`pydub.low_pass_filter`) si le bruit est basse fréquence.

### Piège 2 – Saturation du buffer  
- `sounddevice` lève `PortAudioError` si le buffer n’est pas vidé assez rapidement.  
- Augmenter `blocksize` ou écrire directement dans un fichier via un callback.

## 2.2 Transcription avec Whisper  

### 2.2.1 Installation  

```bash
pip install -U openai-whisper  # ou pip install -U git+https://github.com/openai/whisper.git
pip install torch               # version CPU ou CUDA selon le GPU
```

### 2.2.2 API locale (whisper.cpp) vs API OpenAI  

| Critère | whisper.cpp (local) | OpenAI API |
|--------|--------------------|------------|
| Latence | < 1 s/segment (GPU) | dépend du réseau, quota |
| Confidentialité | 100 % locale | données envoyées à OpenAI |
| Coût | Aucun (GPU requis) | $0.006 / min (large) |

### 2.2.3 Exemple de transcription locale (model `base`)  

```python
import whisper
import pathlib

model = whisper.load_model("base")  # modèle 74 Mo, CPU ~ 2 min/heure audio
audio_path = pathlib.Path("meeting.wav")

# Découpage automatique interne (30 s) et fusion des timestamps
result = model.transcribe(str(audio_path), language="fr", word_timestamps=True)

# Résultat brut
print(result["text"])

# Export JSON avec timestamps
import json
with open("transcript.json", "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)
```

### 2.2.4 Gestion des scores de confiance  

```python
# chaque mot possède un champ `confidence` (0‑1)
low_confidence = [w for w in result["segments"][0]["words"]
                  if w["confidence"] < 0.6]
print(f"{len(low_confidence)} mots à faible confiance")
```

- **Stratégie** : regrouper les mots faibles dans un sous‑prompt « re‑transcrire » et appeler l’API Whisper (ou GPT) pour clarification.

## 2.3 Post‑traitement du texte  

### 2.3.1 Nettoyage de base  

```python
import re

def clean(text: str) -> str:
    # suppression des balises temporelles éventuelles
    text = re.sub(r"\[[0-9:.]+\]", "", text)
    # normalisation des espaces
    return re.sub(r"\s+", " ", text).strip()

cleaned = clean(result["text"])
```

### 2.3.2 Extraction des points d’action  

```python
import spacy

nlp = spacy.load("fr_core_news_md")  # modèle ~ 120 Mo, bonne précision NER

doc = nlp(cleaned)

# heuristique simple : phrase contenant un verbe à l’infinitif + un nom de personne ou "nous"
action_items = []
for sent in doc.sents:
    if any(tok.pos_ == "VERB" and tok.morph.get("VerbForm") == ["Inf"] for tok in sent):
        if any(ent.label_ in {"PER", "ORG"} for ent in sent.ents) or "nous" in sent.text.lower():
            action_items.append(sent.text.strip())

print("Points d’action :", action_items)
```

### 2.3.3 Extraction d’entités nomm

---

## Module 3 — contenu

## 3.1 Modélisation des durées de tâches – séries temporelles  

### 3.1.1 Données d’entrée  
| Champ | Type | Description |
|-------|------|-------------|
| `task_id` | `str` | Identifiant unique de la tâche (ex. `PROJ-123`). |
| `start_date` | `datetime` | Date/heure de démarrage réel. |
| `end_date` | `datetime` | Date/heure de clôture réel. |
| `estimated_hours` | `float` | Charge prévue (en heures). |
| `actual_hours` | `float` | Charge réellement consommée (`(end‑start).total_seconds()/3600`). |
| `status` | `str` | `done`, `in_progress`, `blocked`, … |
| `assignee` | `str` | Nom ou ID de la personne assignée. |
| `project` | `str` | Nom du projet ou composant. |

On ne conserve que les tâches terminées (`status == "done"`). La série temporelle est construite à l’échelle **hebdomadaire** (ou journalière) : chaque point représente la moyenne (ou la somme) des écarts `actual_hours - estimated_hours` pour les tâches clôturées dans la période.

```python
import pandas as pd

def build_time_series(df: pd.DataFrame, freq: str = "W-MON") -> pd.DataFrame:
    """
    Transforme un DataFrame brut de tickets en série temporelle d'écarts.
    - df doit contenir les colonnes décrites ci‑dessus.
    - freq = "W-MON" → semaines commençant le lundi.
    Retourne un DataFrame avec deux colonnes : ds (date) et y (écart moyen).
    """
    # Filtrer les tickets terminés
    done = df[df["status"] == "done"].copy()
    # Calculer l'écart
    done["error"] = done["actual_hours"] - done["estimated_hours"]
    # Convertir les dates de clôture en période agrégée
    done["ds"] = done["end_date"].dt.to_period(freq).dt.start_time
    # Agréger
    ts = (
        done.groupby("ds")["error"]
        .mean()
        .reset_index()
        .rename(columns={"error": "y"})
    )
    return ts
```

### 3.1.2 Prophet (Facebook)  

```python
from prophet import Prophet
import matplotlib.pyplot as plt

# ts = build_time_series(raw_df)   # DataFrame avec colonnes ds, y
model = Prophet(
    yearly_seasonality=False,
    weekly_seasonality=True,
    daily_seasonality=False,
    changepoint_prior_scale=0.05,   # réduit la sensibilité aux variations brusques
)
model.fit(ts)

# Prévision sur les 4 prochaines semaines
future = model.make_future_dataframe(periods=4, freq="W-MON")
forecast = model.predict(future)

# Visualisation
model.plot(forecast)
plt.title("Prévision de l'écart de charge")
plt.show()
```

*Points de vérification*  

| Vérification | Pourquoi |
|--------------|----------|
| `ds` au format `datetime` (UTC) | Prophet exige le type `datetime`. |
| `y` sans valeurs manquantes | Les `NaN` provoquent une erreur de fitting. |
| `changepoint_prior_scale` ≈ 0.05–0.1 | Valeur trop élevée crée des sauts artificiels. |
| `interval_width` (par défaut 0.80) | Ajuster à 0.95 si la tolérance au risque est faible. |

### 3.1.3 ARIMA (statsmodels)  

```python
import statsmodels.api as sm
import numpy as np

# Assurer une série stationnaire (differencing)
ts_series = ts.set_index("ds")["y"]
ts_series = ts_series.asfreq("W-MON")                     # fréquence explicite
ts_series = ts_series.fillna(method="ffill")             # imputation simple

# Test d’ADF (Augmented Dickey‑Fuller)
adf = sm.tsa.stattools.adfuller(ts_series)
print(f"p‑value ADF : {adf[1]:.4f}")                     # < 0.05 → stationnaire

# Sélection automatique (p,d,q) avec auto_arima (pmdarima)
from pmdarima import auto_arima
stepwise = auto_arima(ts_series, seasonal=False, trace=False,
                      error_action="ignore", suppress_warnings=True,
                      max_p=5, max_q=5, d=None, start_p=0, start_q=0)
print(stepwise.summary())

# Entraînement du modèle choisi
model = sm.tsa.SARIMAX(ts_series,
                       order=stepwise.order,
                       enforce_stationarity=False,
                       enforce_invertibility=False)
result = model.fit(disp=False)

# Prévision 4 semaines
pred = result.get_forecast(steps=4)
pred_ci = pred.conf_int()
pred_ci.plot()
```

*Pièges fréquents*  

| Situation | Conséquence | Remède |
|-----------|--------------|--------|
| Série non stationnaire (p‑value ADF > 0.05) | Prévisions biaisées | Appliquer `diff()` jusqu’à stationnarité. |
| `NaN` dans `ts_series` après `asfreq` | `ValueError: exog contains NaN` | Imputer (`ffill` ou interpolation) avant le fit. |
| Choix de `order` trop élevé | Over‑fitting, prévisions instables | Utiliser `auto_arima` avec `information_criterion='aic'`. |

---

## Module 4 — contenu

## 4.1. Principes de génération de code avec l’API OpenAI  

| Élément | Valeur recommandée | Raison |
|--------|--------------------|--------|
| Modèle | `gpt-4-code` (ou `code-davinci-002` si le quota GPT‑4‑Code n’est pas disponible) | Fine‑tuned sur des tâches de programmation, meilleure précision syntaxique. |
| `temperature` | `0` | Force la génération déterministe, indispensable pour du code reproductible. |
| `max_tokens` | `500` (ou le minimum qui couvre le bloc attendu) | Limite le coût et évite les réponses incomplètes. |
| `stop` | `["\n\n"]` ou `["# End"]` selon le style de votre prompt | Empêche la génération d’un texte hors du bloc de code. |
| `top_p` | `1` | Pas de filtrage supplémentaire, le modèle a déjà été entraîné pour la précision. |
| `presence_penalty` / `frequency_penalty` | `0` | Pas de pénalité de répétition dans le code. |

**Appel minimal en Python (bibliothèque `openai`)**  

```python
import openai, os, json

openai.api_key = os.getenv("OPENAI_API_KEY")

def generate_code(prompt: str) -> str:
    response = openai.ChatCompletion.create(
        model="gpt-4-code",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        max_tokens=500,
        stop=["\n\n"],          # arrête après le bloc de code
    )
    # Le texte renvoyé contient généralement le code dans un bloc markdown
    content = response.choices[0].message["content"]
    # Extraction du code brut
    if "```" in content:
        code = content.split("```")[1].split("```")[0]
    else:
        code = content.strip()
    return code
```

---

## 4.2. Prompt engineering pour du code fiable  

1. **Définir le contexte** – Commencez par un bref rappel du projet et des conventions (PEP 8, typage).  
   ```text
   Tu es un assistant de développement Python. Le projet suit les conventions PEP8, utilise le typage statique (typing) et les tests pytest.
   ```

2. **Spécifier la tâche** – Formulez la fonction attendue sous forme de *specification* claire.  
   ```text
   Écris une fonction `def fibonacci(n: int) -> List[int]` qui renvoie les `n` premiers nombres de la suite de Fibonacci.
   ```

3. **Demander les artefacts complémentaires** – Ajoutez dans le même prompt les exigences de docstring, de tests unitaires et de linting.  
   ```text
   Fournis également :
   - une docstring au format NumPy,
   - deux tests pytest couvrant les cas limites,
   - le résultat du formatage avec black (sans les commentaires de diff).
   ```

4. **Utiliser des balises explicites** – Encadrez chaque partie attendue avec des marqueurs que vous pourrez parser.  
   ```text
   ### CODE
   ```python
   ...code...
   ```
   ### TESTS
   ```python
   ...tests...
   ```
   ```

---

## 4.3. Exemple complet : génération, linting, tests, documentation  

```python
import os, subprocess, textwrap, json, openai
from pathlib import Path

openai.api_key = os.getenv("OPENAI_API_KEY")

PROMPT = """
Tu es un assistant de développement Python. Le projet suit les conventions PEP8, utilise le typage statique (typing) et les tests pytest.

Écris une fonction `def prime_factors(n: int) -> List[int]` qui renvoie la liste des facteurs premiers de `n` triés par ordre croissant.

Fournis également :
- une docstring au format NumPy,
- deux tests pytest couvrant un nombre premier et un nombre composé,
- le code formaté avec black (sans les commentaires de diff).

Encadre chaque partie avec les balises suivantes :

### CODE
```python
...
```
### TESTS
```python
...
```
"""

def call_openai(prompt: str) -> dict:
    return openai.ChatCompletion.create(
        model="gpt-4-code",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        max_tokens=800,
        stop=None,
    )

def extract_block(text: str, tag: str) -> str:
    """Retourne le contenu entre les balises ### TAG et le prochain bloc markdown."""
    start = f"### {tag}"
    if start not in text:
        raise ValueError(f"Balise {tag} introuvable")
    # Le bloc commence après la ligne contenant "```python"
    block = text.split(start)[1].split("```python")[1].split("```")[0]
    return block.strip()

# 1️⃣ Génération
raw = call_openai(PROMPT).choices[0].message["content"]
code_str   = extract_block(raw, "CODE")
tests_str  = extract_block(raw, "TESTS")

# 2️⃣ Écriture sur disque
src_dir = Path("generated")
src_dir.mkdir(exist_ok=True)
module_path = src_dir / "prime_factors.py"
tests_path  = src_dir / "test_prime_factors.py"

module_path.write_text(code_str + "\n")
tests_path.write_text(tests_str + "\n")

# 3️⃣ Linting avec black (appel système)
subprocess.run(["black", str(module_path

---

## Module 5 — contenu

## 5.1 Analyse des flux de données personnelles  

| Étape | Action vérifiable | Outils / Bibliothèques |
|------|-------------------|------------------------|
| 5.1.1 | Identifier chaque champ de donnée traitée (ex. `email`, `nom`, `adresse IP`). | `pandas` + `pydantic` pour la description de schémas. |
| 5.1.2 | Classifier les champs comme **sensibles** (RGPD : données d’identification, santé, finances). | Tableau de classification fourni par la CNIL. |
| 5.1.3 | Tracer le trajet de chaque champ : collecte → stockage → appel IA → sortie. | Diagramme Mermaid (`graph TD`). |
| 5.1.4 | Vérifier que les points d’entrée externes (API, webhook) sont authentifiés (OAuth 2.0, JWT). | `fastapi.security.HTTPBearer`. |
| 5.1.5 | Documenter le **Data Processing Agreement (DPA)** avec le fournisseur IA (OpenAI). | Clause : « OpenAI ne conserve pas les données de prompts ». |

### Exemple de cartographie (Mermaid)

```mermaid
graph TD
    A[Formulaire web] -->|collecte| B[Base SQLite (chiffrée)]
    B -->|lecture| C[FastAPI endpoint /process]
    C -->|envoie prompt| D[OpenAI API]
    D -->|réponse| C
    C -->|enregistrement| E[Google Sheet (chiffrée)]
```

---

## 5.2 Chiffrement AES‑256 des données en transit et au repos  

### 5.2.1 Principe  

* **Clé symétrique** : 256 bits générés par `secrets.token_bytes(32)`.  
* **Mode** : GCM (authentifié) → garantit intégrité et confidentialité.  
* **Stockage de la clé** : coffre‑fort (ex. AWS KMS, Azure Key Vault) ; jamais en clair dans le code source.  

### 5.2.2 Code Python (commenté)  

```python
import os
import json
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend

# ------------------------------------------------------------------
# 1️⃣  Récupération de la clé depuis une variable d'environnement
#     (dans la prod, la variable provient d'un secret manager)
# ------------------------------------------------------------------
_AES_KEY_B64 = os.getenv("AES256_KEY_B64")
if not _AES_KEY_B64:
    raise RuntimeError("Clé AES256 non fournie")
_AES_KEY = base64.b64decode(_AES_KEY_B64)          # 32 bytes

# ------------------------------------------------------------------
# 2️⃣  Fonction d’encryptage (entrée : dict → sortie : str JSON base64)
# ------------------------------------------------------------------
def encrypt_payload(payload: dict) -> str:
    """
    Convertit un dictionnaire en JSON, le chiffre en AES‑GCM,
    puis renvoie le ciphertext encodé en base64.
    """
    # Sérialisation JSON canonique (tri des clés) → déterminisme
    json_bytes = json.dumps(payload, sort_keys=True).encode("utf-8")

    # 96‑bit nonce aléatoire recommandé par le standard GCM
    nonce = os.urandom(12)

    aesgcm = AESGCM(_AES_KEY)
    ct = aesgcm.encrypt(nonce, json_bytes, associated_data=None)

    # Stockage du nonce + ciphertext dans un seul blob
    blob = nonce + ct
    return base64.b64encode(blob).decode("ascii")

# ------------------------------------------------------------------
# 3️⃣  Fonction de décryptage (inverse de encrypt_payload)
# ------------------------------------------------------------------
def decrypt_payload(token: str) -> dict:
    """
    Décodage base64 → sépare nonce / ciphertext → déchiffrement.
    Lève une exception si l’authentification GCM échoue.
    """
    blob = base64.b64decode(token)
    nonce, ct = blob[:12], blob[12:]

    aesgcm = AESGCM(_AES_KEY)
    plain = aesgcm.decrypt(nonce, ct, associated_data=None)
    return json.loads(plain.decode("utf-8"))

# ------------------------------------------------------------------
# 4️⃣  Exemple d’usage (environnement de test uniquement)
# ------------------------------------------------------------------
if __name__ == "__main__":
    # Données contenant un email (RGPD‑sensible)
    data = {"email": "alice@example.com", "action": "create_ticket"}

    token = encrypt_payload(data)
    print("Ciphertext (base64) :", token)

    recovered = decrypt_payload(token)
    print("Déchiffré :", recovered)
```

* **Vérifiabilité** : le script utilise la bibliothèque `cryptography` 1.10+, conforme aux RFC 5116 (AES‑GCM).  
* **Piège** : ne jamais ré‑utiliser le même nonce avec la même clé ; le code génère un nonce aléatoire à chaque appel.  

---

## 5.3 Filtrage de contenu avec l’endpoint **Moderation** d’OpenAI  

| Paramètre | Valeur recommandée | Raison |
|-----------|--------------------|--------|
| `model`   | `text-moderation-latest` | Dernière version, mise à jour des listes de mots interdits. |
| `input`   | texte brut (max = 10 k tokens) | Limite d’API. |
| `threshold` | `0.5` (défaut) | Ajustable : réduire