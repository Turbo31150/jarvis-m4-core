# Weaviate & ChromaDB — RAG Local

> Référence `weaviate-chroma` · 69 €

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
**Objectif mesurable** : L’apprenant pourra réduire le temps moyen de recherche de 30 % en ajustant les index et la configuration mémoire, et pourra déployer un cluster à deux nœuds Weaviate.  
**Notions couvertes**  
1. Activation de l’index HNSW dans Weaviate (`vectorIndexConfig: {"efConstruction": 200, "ef

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
| `curl http://localhost:8080/v1/.well-known/ready` renvoie *404* | Le conteneur n’est pas encore initialisé | Weaviate met ~10 s à charger les index internes | Ré‑exécuter la requête après quelques secondes ou ajouter `--retry 5 --retry-delay 2`

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

**Piège** : le modèle charge les poids en mémoire GPU si disponible. Si le serveur n’a pas de GPU, forcez le CPU : `SentenceTransformer(..., device="cpu")`.  

---

## 2.4 Création de la collection ChromaDB

```python
import chromadb
from chromadb.config import Settings
from pathlib import Path

# Répertoire persistant (ex. ./chroma_data)
persist_dir = Path("./chroma_data")
persist_dir.mkdir(parents=True, exist_ok=True)

chroma_client = chromadb.Client(
    Settings(
        chroma_db_impl="duckdb+parquet",
        persist_directory=str(persist_dir),
        anonymized_telemetry=False
    )
)

# (Re)création de la collection
if "docs" in [c.name for c in chroma_client.list_collections()]:
    chroma_client.delete_collection(name="docs")

collection = chroma_client.create_collection(name="docs")
print("Collection Chroma 'docs' prête.")
```

---

## 2.5 Ingestion simultanée : Weaviate + ChromaDB

### 2.5.1 Stratégie de batch

- **Taille de lot** : 64 documents (optimisé pour le GPU et le réseau).  
- **Gestion des erreurs** : `try/except` autour de chaque lot, journalisation, reprise possible.  

```python
import json
from pathlib import Path
from tqdm import tqdm   # barre de progression
import weaviate
import chromadb
import numpy as np

# Clients déjà initialisés (voir sections précédentes)
weaviate_client = weaviate.Client(url="http://localhost:8080")
chroma_collection = collection

def ingest_folder(root: Path, batch_size: int = 64):
    """Parcourt récursivement root, extrait le texte, le vectorise,
    puis stocke dans Weaviate et ChromaDB."""
    # 1️⃣ Récupération de tous les fichiers supportés
    files = list(root.rglob("*.[pP][dD][fF]")) + \
            list(root.rglob("*.html")) + \
            list(root.rglob

---

## Module 3 — contenu

## 3.1 Construction d’une requête hybride Weaviate  

Weaviate accepte simultanément un filtre **where** (sur les propriétés textuelles) et un filtre **nearVector** (sur le vecteur). La combinaison donne une recherche « hybride » : le texte affine le champ `text` tandis que le vecteur assure la similarité sémantique.

```python
import weaviate
import numpy as np
from sentence_transformers import SentenceTransformer

# 1️⃣ Chargement du modèle d’encodage
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

# 2️⃣ Initialisation du client (Weaviate tourne en local sur le port 8080)
client = weaviate.Client(url="http://localhost:8080")

# 3️⃣ Phrase de l’utilisateur
question = "Comment sécuriser les communications d’un micro‑service Kubernetes ?"

# 4️⃣ Encodage en vecteur (float32, normalisé)
vector = model.encode(question, normalize_embeddings=True).astype(np.float32).tolist()

# 5️⃣ Construction de la requête hybride
response = client.query.get(
    class_name="Document",                     # classe définie au module 2
    properties=["text", "source"]              # champs que l’on veut récupérer
).with_near_vector({
    "vector": vector,
    "certainty": 0.7                          # seuil de similarité (0‑1)
}).with_where({
    "operator": "Or",
    "operands": [
        {
            "path": ["source"],              # filtre sur la métadonnée source
            "operator": "Equal",
            "valueString": "kubernetes"
        },
        {
            "path": ["text"],                # filtre texte simple (full‑text)
            "operator": "ContainsAny",
            "valueString": "sécurité"
        }
    ]
}).with_limit(5).do()

# 6️⃣ Extraction des IDs et du texte
hits = response["data"]["Get"]["Document"]
ids  = [hit["_additional"]["id"] for hit in hits]
texts = [hit["text"] for hit in hits]
```

*Points clés*  

| Élément | Valeur recommandée | Pourquoi |
|--------|----------------------|----------|
| `certainty` | 0.7 – 0.85 | Au‑delà de 0.85 le nombre de hits chute, en dessous de 0.6 le bruit augmente. |
| `with_limit` | 5 (ou 10) | Limite le temps de réponse et le nombre de passages au LLM. |
| `normalize_embeddings` | `True` | Weaviate stocke les vecteurs normalisés ; sinon la distance Euclidienne devient incohérente. |

---

## 3.2 Récupération des métadonnées depuis ChromaDB  

Weaviate renvoie les IDs internes (`_additional.id`). Ces IDs sont identiques à ceux stockés dans la collection Chroma si l’on les a synchronisés lors de l’ingestion (voir module 2). On récupère alors les métadonnées (ex. titre, source, date) qui ne sont pas dans le schéma Weaviate.

```python
import chromadb
from chromadb.config import Settings

# 1️⃣ Client Chroma (stockage persistant dans ./chroma)
chroma_client = chromadb.Client(
    Settings(
        chroma_db_impl="duckdb+parquet",
        persist_directory="./chroma"
    )
)

collection = chroma_client.get_collection(name="docs")

# 2️⃣ Recherche par IDs (Weaviate → Chroma)
#   Chroma accepte une liste d'IDs et renvoie les documents correspondants.
metadata = collection.get(
    ids=ids,                     # liste d'IDs obtenue ci‑dessus
    include=["documents", "metadatas"]
)

# 3️⃣ Extraction des champs utiles
documents = metadata["documents"]
metadatas = metadata["metadatas"]   # dictionnaire libre, ex. {"title": "...", "date": "..."}
```

*Notes d’implémentation*  

- **Synchronisation des IDs** : lors de l’ingestion, on a passé `id=uuid` à `client.data_object.create` (Weaviate) et le même `id` à `collection.add`. Si les IDs divergent, la jointure échoue.  
- **Performance** : la méthode `collection.get` avec uniquement les IDs évite le recalcul de vecteurs, le temps d’accès est < 5 ms pour < 10 000 documents sur un SSD.  

---

## 3.3 Passage du texte récupéré à un LLM local  

On utilise `transformers.pipeline` avec un modèle quantifié (ex. Llama‑2‑7B‑Chat ggml) installé en local. Le pipeline accepte un prompt complet ; on doit donc construire le prompt en respectant la limite de tokens du modèle (≈ 4096 pour Llama‑2‑7B).

```python
from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM

# 1️⃣ Chargement du modèle (exemple : Llama‑2‑7B‑Chat en GGML, format .bin)
model_name = "meta-llama/Llama-2-7b-chat-hf"
tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=True)
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    device_map="auto",          # GPU si disponible, sinon CPU
    torch_dtype="auto"
)

generator = pipeline(
    "text-generation",
    model=model,
    tokenizer=tokenizer,
    max_new_tokens=256,
    temperature=0.7,
    do_sample=True,
    truncation=True
)

# 2️⃣ Construction du prompt (prompt engineering)
def build_prompt(question: str, docs: list[str]) -> str:
    # Limite de 3500

---

## Module 4 — contenu

## 4. Optimisation des performances et scalabilité

### 4.1. Accélérer les recherches vectorielles (HNSW)

| Paramètre | Impact | Valeur recommandée (benchmark ≥ 30 % de gain) |
|-----------|--------|----------------------------------------------|
| `efConstruction` | Qualité de l’index lors de la construction. Plus élevé → index plus précis mais temps de build plus long. | 200 → 400 (double le défaut 100) |
| `ef` (ou `efSearch`) | Nombre de voisins explorés à chaque requête. Plus élevé → meilleure recall, plus lent. | 64 → 128 (souvent le meilleur compromis) |
| `maxConnections` | Degré du graphe HNSW. Plus élevé → densité accrue, index plus lourd. | 64 (défaut) → 128 |
| `vectorCacheMaxObjects` | Nombre d’objets mis en cache en RAM. | 100 000 (≈ 10 % du corpus) |

**Modification du schéma** (exemple : classe `Document` déjà créée) :

```python
import weaviate

client = weaviate.Client(url="http://localhost:8080")

# 1️⃣ Récupérer le schéma actuel
schema = client.schema.get()

# 2️⃣ Modifier la configuration HNSW de la classe
for cls in schema["classes"]:
    if cls["class"] == "Document":
        cls["vectorIndexConfig"] = {
            "efConstruction": 300,          # +200% du défaut
            "ef": 128,                      # +100% du défaut
            "maxConnections": 128,          # +100% du défaut
            "vectorCacheMaxObjects": 100_000
        }

# 3️⃣ Appliquer le nouveau schéma (remplace l’ancien)
client.schema.update(schema)
print("Configuration HNSW mise à jour.")
```

*Le code ci‑dessus utilise l’API `schema.update` qui remplace le schéma complet ; il faut donc le lancer uniquement après avoir sauvegardé le schéma actuel (ex. `client.schema.get() → json`).*  

#### Vérification de l’impact

```python
import time, numpy as np

def benchmark_search(client, query_vec, k=5, n=100):
    start = time.time()
    for _ in range(n):
        client.query.get("Document", ["text"]).with_near_vector({"vector": query_vec, "certainty": 0.7}).with_limit(k).do()
    return (time.time() - start) / n  # temps moyen en s

# vecteur d’exemple
query = np.random.rand(384).tolist()  # dimension du modèle MiniLM‑L6‑v2

t_before = benchmark_search(client, query)   # exécution avant changement
# → 0.120 s (exemple)
# appliquer les paramètres HNSW (voir ci‑dessus)
t_after = benchmark_search(client, query)    # exécution après changement
# → 0.082 s (exemple)

print(f"Gain : {(t_before - t_after) / t_before:.1%}")
```

> **Résultat attendu** : gain ≥ 30 % (exemple : 0.120 → 0.082 s = 31,7 %).

---

### 4.2. Gestion de la mémoire et du cache

| Variable d’environnement | Description | Valeur typique |
|--------------------------|-------------|----------------|
| `WEAVIATE_MEMORY_MAX_SIZE` | Mémoire maximale allouée au processus (en bytes). | `4GB` pour un serveur 8 GB |
| `WEAVIATE_VECTOR_CACHE_MAX_OBJECTS` | Nombre d’objets vectoriels conservés en RAM (override du paramètre ci‑dessus). | `200000` |
| `WEAVIATE_MAX_IMPORT_BATCH_SIZE` | Taille maximale d’un batch d’ingestion. | `1000` |
| `WEAVIATE_GC_ENABLED` | Active le garbage‑collector interne (utile avec de gros index). | `true` |

Dans le

---

## Module 5 — contenu

## Module 5 – Sécurisation, monitoring et mise en production d’un pipeline RAG local avec Weaviate & ChromaDB  

### 5.1 Authentification et contrôle d’accès dans Weaviate  

| Élément | Valeur attendue | Vérification |
|--------|------------------|--------------|
| **API‑Key** | Chaîne alphanumérique de 32 caractères (ex. `8a3f...d2c9`) | `curl -H "Authorization: Bearer $API_KEY" http://localhost:8080/v1/.well-known/ready` renvoie `200` |
| **RBAC** | Rôles `admin`, `reader`, `writer` définis dans le fichier `auth_config.json` | `weaviate-client` lève `weaviate.exceptions.AuthException` si un rôle ne possède pas la permission demandée |

**Configuration** (Docker‑Compose) :  

```yaml
services:
  weaviate:
    image: semitechnologies/weaviate:1.23.0
    environment:
      - AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED=false
      - AUTHENTICATION_APIKEY_ENABLED=true
      - AUTHENTICATION_APIKEY_USERS=admin:8a3f5c1e2d4b9f6a7c8d9e0b1c2d3f4a,reader:1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e
      - AUTHORIZATION_ADMINLIST_ENABLED=true
      - AUTHORIZATION_ADMINLIST_USERS=admin
    ports:
      - "8080:8080"
```

- `AUTHENTICATION_APIKEY_USERS` associe chaque rôle à une clé.  
- `AUTHORIZATION_ADMINLIST_USERS` restreint les appels d’administration (création de schéma, mise à jour de configuration) au rôle `admin`.  

#### 5.1.1 Exemple de client Python avec API‑Key  

```python
import weaviate

# ------------------------------------------------------------------
# 1️⃣  Instanciation du client en injectant l'API‑Key dans le header
# ------------------------------------------------------------------
API_KEY = "8a3f5c1e2d4b9f6a7c8d9e0b1c2d3f4a"
client = weaviate.Client(
    url="http://localhost:8080",
    auth_client_secret=weaviate.AuthApiKey(API_KEY),
    additional_headers={"X-OpenAI-Api-Key": API_KEY}  # optionnel, montre que le header passe
)

# ------------------------------------------------------------------
# 2️⃣  Vérification du rôle : on tente de créer une classe.
#    Si la clé n'est pas admin, Weaviate renvoie 403.
# ------------------------------------------------------------------
try:
    client.schema.create_class({
        "class": "Test",
        "properties": [{"name": "content", "dataType": ["text"]}]
    })
    print("Classe créée – la clé possède le rôle admin.")
except weaviate.exceptions.UnexpectedStatusCodeException as exc:
    print(f"Échec de création de classe (code {exc.status_code})")
```

> **Note** : le même principe s’applique à ChromaDB via le paramètre `settings=chromadb.Settings(chroma_db_impl="duckdb+parquet", persist_directory="./chroma", auth_token="mytoken")`. ChromaDB ne possède pas de RBAC natif ; la sécurisation se fait au niveau du service (ex. reverse‑proxy Nginx avec auth‑basic).

---

### 5.2 Monitoring des métriques de recherche  

| Métrique | Source | Exporter vers |
|----------|--------|---------------|
| `search_latency_ms` | Weaviate (endpoint `/metrics`) | Prometheus |
| `vector_dimensionality` | ChromaDB (via `client.get_collection(name).metadata`) | Grafana |
| `cpu/memory usage` | Docker stats (`docker stats weaviate`) | cAdvisor |

#### 5.2.1 Prometheus + Grafana (docker‑compose)  

```yaml
services:
  prometheus:
    image: prom/prometheus:v2.48.0
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana:10.2.0
    ports:
      - "3000:3000"
    depends_on:
      - prometheus
```

`prometheus.yml` (extrait) :

```yaml
scrape_configs:
  - job_name: "weaviate"
    static_configs:
      - targets: ["weaviate:8080"]
    metrics_path: /metrics
    scheme: http
```

- **Alerting** : ajouter une règle `alert: HighSearchLatency` si `search_latency_ms > 200` pendant plus de 5 min.

---

### 5.3 Gestion des logs et traçage distribué  

| Outil | Rôle | Configuration minimale |
|-------|------|------------------------|
| **Filebeat** | Forwarder de logs Docker → Elasticsearch | `filebeat.inputs: - type: docker` |
| **Elastic APM** | Tracing des appels Python (client Weaviate, pipeline RAG) | `ELASTIC_APM_SERVICE_NAME=rag-pipeline` |
| **OpenTelemetry** (option) | Export vers Jaeger ou Zipkin | `OTEL_EXPORTER_OTLP_ENDPOINT=http://jaeger:4317` |

#### 5.3.1 Exemple d’instrumentation du pipeline RAG  

```python
import weaviate
from opente