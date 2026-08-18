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
* Le `timeout` couvre le temps total de la requête ; ajuster en fonction de la longueur du prompt.  
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
```


---

## Module 2 — contenu

## 2.1 Capture audio de la réunion  

| Étape | Bibliothèque | Code minimal | Remarque |
|------|--------------|--------------|----------|
| Enregistrement en temps réel (mono) | `sounddevice` + `numpy` | ```python\nimport sounddevice as sd, wave, numpy as np\nfs = 16000\nseconds = 300  # durée max, à adapter\nprint('Enregistrement…')\naudio = sd.rec(int(seconds * fs), samplerate=fs, channels=1, dtype='int16')\nsd.wait()\nwave_file = 'meeting.wav'\nwith wave.open(wave_file, 'wb') as wf:\n    wf.setnchannels(1)\n    wf.setsampwidth(2)\n    wf.setframerate(fs)\n    wf.writeframes(audio.tobytes())\nprint('Fichier enregistré :', wave_file)\n``` | `sounddevice` nécessite les drivers PortAudio ; sur Linux, installer `python3‑portaudio` ou `apt-get install libportaudio2`. |
| Découpage en segments (facultatif) | `pydub` | ```python\nfrom pydub import AudioSegment\naudio = AudioSegment.from_wav('meeting.wav')\nsegment_len = 30000  # ms\nsegments = [audio[i:i+segment_len] for i in range(0, len(audio), segment_len)]\nfor idx, seg in enumerate(segments):\n    seg.export(f'segment_{idx}.wav', format='wav')\n``` | Le découpage réduit le temps de latence de Whisper et simplifie la gestion des quotas. |

### Piège 1 – Qualité du signal  
- **Bruit de fond élevé** → taux d’erreur élevé.  
- Utiliser un micro directionnel ou placer le dispositif près du haut‑parleur.  
- Appliquer un filtre passe‑haut si le bruit est basse fréquence.

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
| Latence | dépend du matériel | dépend du réseau, quota |
| Confidentialité | locale | données envoyées à OpenAI |
| Coût | Aucun (GPU requis) | — |

### 2.2.3 Exemple de transcription locale (model `base`)  

```python
import whisper
import pathlib

model = whisper.load_model("base")
audio_path = pathlib.Path("meeting.wav")

result = model.transcribe(str(audio_path), language="fr", word_timestamps=True)

print(result["text"])

import json
with open("transcript.json", "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)
```

### 2.2.4 Gestion des scores de confiance  

```python
# Définir le seuil de confiance souhaité (à ajuster selon le contexte)
LOW_CONFIDENCE_THRESHOLD = None  # à remplacer par la valeur appropriée

low_confidence = [
    w for w in result["segments"][0]["words"]
    if w["confidence"] < LOW_CONFIDENCE_THRESHOLD
]
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

nlp = spacy.load("fr_core_news_md")

doc = nlp(cleaned)

action_items = []
for sent in doc.sents:
    if any(tok.pos_ == "VERB" and tok.morph.get("VerbForm") == ["Inf"] for tok in sent):
        if any(ent.label_ in {"PER"} for ent in sent.ents):
            action_items.append(sent.text)

print("Points d'action détectés :", action_items)
```