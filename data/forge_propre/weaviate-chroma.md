# Weaviate & ChromaDB — RAG Local

> Référence `weaviate-chroma`

## Plan

## Module 1 – Installation et configuration locale de Weaviate et ChromaDB  
**Objectif mesurable** : L’apprenant pourra installer, lancer et configurer un nœud Weaviate et une instance ChromaDB en local, puis vérifier leur bon fonctionnement via les API REST.  
**Notions couvertes**  
1. Prérequis système (Docker ≥ 20.10, Python ≥ 3.9, GPU optional).  
2. Déploiement de Weaviate avec Docker Compose : `docker compose up -d weaviate`.  
3. Installation de ChromaDB (`pip install chromadb`) et création d’un répertoire de stockage persistant.  
4. Vérification de la santé des services (`curl http://localhost:8080/v1/.well-known/ready`).  
5. Configuration du client Python Weaviate (`weaviate.Client(url="http://localhost:8080")`) et du client Chroma (`chromadb.Client(settings=chromadb.Settings(...))`).  

## Module 2 – Modélisation du schéma et ingestion des documents  
**Objectif mesurable** : L’apprenant sera capable de définir un schéma Weaviate adapté à un corpus textuel, d’ingérer au moins 1 000 documents et de les indexer dans ChromaDB.  
**Notions couvertes**  
1. Définition d’une classe Weaviate avec propriétés `text` (type `text`) et `vector` (type `blob`).  
2. Utilisation de `weaviate.Schema().add_class(...)` via le client.  
3. Extraction de texte brut (PDF, HTML, Markdown) avec `pdfminer.six` ou `BeautifulSoup`.  
4. Vectorisation avec un modèle HuggingFace (ex. `sentence-transformers/all-MiniLM-L6-v2`).  
5. Ingestion simultanée : stockage du vecteur dans Weaviate et création d’une collection Chroma (`client.create_collection(name="docs")`).  

## Module 3 – Recherche hybride RAG (retrieval‑augmented generation) locale  
**Objectif mesurable** : L’apprenant pourra exécuter une requête hybride (texte + vecteur) qui récupère les 5 documents les plus pertinents et les injecte dans un LLM local (ex. Llama‑2‑7B) pour générer une réponse.  
**Notions couvertes**  
1. Construction d’une requête hybride Weaviate (`where` + `nearVector`).  
2. Récupération des IDs et des métadonnées depuis ChromaDB (`client.get(..., limit=5)`).  
3. Passage du texte récupéré à un LLM via `transformers.pipeline("text-generation")`.  
4. Gestion du contexte (prompt engineering) : concaténation des extraits, limite de tokens.  
5. Évaluation de la pertinence avec la métrique : précision@5 et BLEU sur un jeu de test.  

## Module 4 – Optimisation des performances et scalabilité  
**Objectif mesurable** : L’apprenant pourra réduire le temps moyen de recherche, en ajustant les index et la configuration mémoire, et pourra déployer un cluster à deux nœuds Weaviate.  
**Notions couvertes**  
1. Activation de l’index HNSW dans Weaviate (`vectorIndexConfig: {"efConstruction": 200, "ef`  

---

## Module 1 — contenu

## 1. Prérequis système  

| Élément | Version minimale | Vérification |
|---------|------------------|--------------|
| Docker Engine | 20.10 | `docker --version` |
| Docker Compose (plugin) | 2.0 | `docker compose version` |
| Python | 3.9 | `python3 --version` |
| pip | 21.0 | `pip --version` |
| (Optionnel) GPU NVIDIA + driver 470+ + CUDA 11.8 | – | `nvidia-smi` |

> **Note** : sous Windows, privilégier Docker Desktop ≥ 4.30 (inclut le plugin Compose). Sous macOS, Docker Desktop ≥ 4.30 ou Docker Engine via Colima.  

---

## 2. Déploiement de Weaviate avec Docker Compose  

### 2.1 Fichier `docker-compose.yml` minimal  

```yaml
version: "3.8"

services:
  weaviate:
    image: semitechnologies/weaviate:1.23.0
    ports:
      - "8080:8080"                 # API REST
    environment:
      - QUERY_DEFAULTS_LIMIT=20
      - AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED=true
      - PERSISTENCE_DATA_PATH=/var/lib/weaviate
      - DEFAULT_VECTORIZER_MODULE=none   # on injecte nos propres vecteurs
    volumes:
      - weaviate-data:/var/lib/weaviate   # persistance locale

volumes:
  weaviate-data:
```

* `QUERY_DEFAULTS_LIMIT` limite le nombre de résultats par défaut.  
* `AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED=true` désactive l’authentification pour un laboratoire local.  
* `PERSISTENCE_DATA_PATH` indique où Weaviate écrit ses métadonnées et son index.  
* Le volume nommé `weaviate-data` garantit la persistance entre les relances du conteneur.  

### 2.2 Lancement  

```bash
docker compose up -d weaviate
```

* `-d` exécute le conteneur en arrière‑plan.  
* Si le service ne démarre pas, consulter les logs : `docker compose logs weaviate`.  

### 2.3 Vérification de l’état de santé  

```bash
curl -s http://localhost:8080/v1/.well-known/ready | jq .
```

Réponse attendue :

```json
{
  "status": "ready"
}
```

* `jq` n’est pas obligatoire ; il sert à formater la sortie.  
* En cas de `{"status":"not ready"}` vérifier les logs et que le port **8080** n’est pas occupé par un autre processus.  

---

## 3. Installation de ChromaDB (Python)  

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install "chromadb[sqlite]"   # version 0.4.x au moment de la rédaction
```

* Le suffixe `[sqlite]` installe le backend de stockage persistant le plus simple.  
* Pour un usage GPU ou un backend plus performant, remplacer par `chromadb[duckdb]` ou `chromadb[postgresql]`.  

### 3.1 Création du répertoire de stockage persistant  

```bash
mkdir -p ./chroma_data
```

Le répertoire sera passé à la configuration du client (voir 3.3).  

---

## 4. Clients Python  

### 4.1 Client Weaviate  

```python
# weaviate_client.py
import weaviate

# connexion au nœud local
client = weaviate.Client(
    url="http://localhost:8080",   # adresse du conteneur exposé
    timeout_config=(5, 30)        # (connect, read) en secondes
)

# test de connexion
if client.is_ready():
    print("✅ Weaviate est prêt")
else:
    raise RuntimeError("Weaviate n'est pas disponible")
```

* `timeout_config` évite que le script bloque indéfiniment si le service ne répond pas.  

### 4.2 Client ChromaDB  

```python
# chroma_client.py
import chromadb
from chromadb.config import Settings

client = chromadb.Client(
    Settings(
        chroma_db_impl="sqlite",          # backend choisi
        persist_directory="./chroma_data" # répertoire persistant créé ci‑dessus
    )
)

# création (ou récupération) d’une collection nommée "docs"
collection = client.get_or_create_collection(name="docs")
print(f"Collection prête : {collection.name}")
```

* `get_or_create_collection` garantit l’idempotence : la même collection peut être récupérée plusieurs fois sans duplication.  

---

## 5. Pièges concrets  

| Situation | Symptom | Cause fréquente | Remède |
|-----------|---------|-----------------|--------|
| `docker compose up` échoue avec *“bind: address already in use”* | Le port 8080 est occupé | Un autre service (ex. Jupyter, serveur local) écoute déjà sur 8080 | Modifier le mapping `ports` (`"8081:8080"`), ou arrêter le service concurrent (`lsof -i:8080`). |
| `curl http://localhost:8080/v1/.well-known/ready` renvoie *404* | Le conteneur n’est pas encore initialisé | Weaviate met quelques secondes à charger les index internes | Ré‑exécuter la requête après quelques secondes ou ajouter `--retry 5 --retry-delay 2` |

---

## Module 2 — contenu

## 2.1 Définition du schéma Weaviate

Weaviate stocke chaque objet dans une *classe*.  
Pour un corpus textuel, la classe minimale comporte :

| Propriété | Type Weaviate | Description |
|-----------|---------------|-------------|
| `text`    | `text`        | texte brut du document |
| `vector` | `blob`        | vecteur d’embedding (dimension 384 pour `all‑MiniLM‑L6‑v2`) |
| `source`  | `string`      | chemin ou URL d’origine (facultatif, utile pour le debugging) |

```python
import weaviate

client = weaviate.Client(url="http://localhost:8080")

# Suppression éventuelle d’une classe existante (idempotence)
if "Document" in [c["class"] for c in client.schema.get()["classes"]]:
    client.schema.delete_class("Document")

# Définition de la classe
class_obj = {
    "class": "Document",
    "description": "Document texte indexé pour RAG",
    "properties": [
        {"name": "text", "dataType": ["text"]},
        {"name": "vector", "dataType": ["blob"]},
        {"name": "source", "dataType": ["string"]},
    ],
    # Le vecteur sera fourni explicitement (pas de module de vectorisation interne)
    "vectorizer": "none"
}

client.schema.create_class(class_obj)
print("Classe Document créée.")
```

*Points de vérification*  

* `client.schema.get()` doit renvoyer la classe `Document`.  
* Le champ `vectorizer` à `"none"` indique à Weaviate de ne **pas** appeler son propre modèle de vecteurisation.  

---

## 2.2 Extraction du texte brut

### 2.2.1 PDF

```python
from pdfminer.high_level import extract_text
from pathlib import Path

def pdf_to_text(path: Path) -> str:
    """Retourne le texte complet d’un PDF, sans mise en forme."""
    return extract_text(str(path))
```

### 2.2.2 HTML / Markdown

```python
from bs4 import BeautifulSoup
import markdown
import re

def html_to_text(html: str) -> str:
    """Supprime balises et scripts, conserve le texte visible."""
    soup = BeautifulSoup(html, "html.parser")
    for script in soup(["script", "style"]):
        script.decompose()
    return soup.get_text(separator=" ", strip=True)

def markdown_to_text(md: str) -> str:
    """Convertit Markdown → HTML → texte brut."""
    html = markdown.markdown(md)
    return html_to_text(html)
```

**Piège** : les PDF scannés ne contiennent pas de texte. Dans ce cas, il faut recourir à OCR (ex. `pytesseract`) ; le module ne le couvre pas, mais il faut le signaler.

---

## 2.3 Vectorisation avec HuggingFace

Le modèle `sentence-transformers/all-MiniLM-L6-v2` produit des vecteurs de dimension 384.

```python
from sentence_transformers import SentenceTransformer
import numpy as np

model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

def embed_text(text: str) -> np.ndarray:
    """
    Retourne un vecteur numpy de dtype float32.
    Normalisation L2 recommandée (Weaviate attend déjà des vecteurs normalisés).
    """
    vec = model.encode(text, normalize_embeddings=True)
    return vec.astype(np.float32)
```

**Piège** : le modèle charge les poids en mémoire GPU si disponible. Si le