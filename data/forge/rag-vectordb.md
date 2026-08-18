# RAG & Bases Vectorielles

> Référence `rag-vectordb` · 89 €

## Plan

## Module 1 : Principes fondamentaux du Retrieval‑Augmented Generation (RAG)  
**Objectif mesurable** : L’apprenant pourra expliquer le flux de données d’un système RAG et implémenter un pipeline simple (requête → recherche → génération) en moins de 30 minutes.  
**Notions couvertes**  
1. Architecture RAG : composantes (retriever, reader, generator) et points d’intégration.  
2. Types de recherche (sparse vs dense) et critères de sélection des documents.  
3. Métriques d’évaluation (recall@k, precision, R‑Precision, BLEU/ROUGE sur la sortie générée).  
4. Gestion du contexte : limites de tokens, stratégies de chunking et de fenêtrage.  
5. Risques de contamination (hallucination, biais de récupération) et mesures d’atténuation.

## Module 2 : Indexation et interrogation des bases vectorielles  
**Objectif mesurable** : L’apprenant sera capable de créer, peupler et interroger une base vectorielle (ex. FAISS, Annoy, Milvus) avec un taux de rappel ≥ 0,90 sur un jeu de test de 10 000 documents.  
**Notions couvertes**  
1. Représentations vectorielles : embeddings de texte (BERT, Sentence‑Transformers, OpenAI embeddings).  
2. Structures d’indexation (IVF, HNSW, PQ) et compromis précision‑performance.  
3. Procédures de normalisation et de dimensionnement (L2‑normalisation, réduction de dimension via PCA/UMAP).  
4. API d’insertion, mise à jour et suppression de vecteurs (batch vs streaming).  
5. Requête vectorielle : distance cosine vs L2, recherche k‑NN, filtrage par métadonnées.

## Module 3 : Entraînement et adaptation de modèles de récupération dense  
**Objectif mesurable** : L’apprenant pourra fine‑tuner un modèle de passage retriever (ex. DPR, Contriever) sur un jeu de données propriétaire et atteindre un MRR ≥ 0,70.  
**Notions couvertes**  
1. Construction de jeux de paires requête‑document (positifs, négatifs) et stratégies de hard‑negative mining.  
2. Architectures de dual‑encoder et partage de poids (si‑si).  
3. Optimisation (learning‑rate schedulers, mixed‑precision, gradient accumulation).  
4. Évaluation en‑ligne vs hors‑ligne (FAISS recall, bien‑et‑mal).  
5. Déploiement du modèle entraîné dans un service d’inférence (ONNX, TorchServe).

## Module 4 : Intégration du RAG dans des applications production  
**Objectif mesurable** : L’apprenant implémentera un service RESTful qui combine recherche vectorielle et génération de texte, avec un temps de latence moyen ≤ 200 ms pour la phase de récupération.  
**Notions couvertes**  
1. Orchestration du pipeline (Celery, FastAPI, gRPC) et gestion des files d’attente.  
2. Caching des résultats de recherche (Redis, LRU) et invalidation de cache.  
3. Sécurisation des appels (authentification JWT, contrôle d’accès basé sur les métadonnées).  
4. Monitoring (Prometheus metrics : latency, hit‑rate, error‑rate) et alerting.  
5. Stratégies de scaling horizontal (sharding de la base vectorielle, load‑balancing).

## Module 5 : Optimisation avancée et bonnes pratiques de maintenance  
**Objectif mesurable** : L’apprenant pourra diagnostiquer et

---

## Module 1 — contenu

## 1. Architecture RAG : flux de données et composants

| Étape | Entrée | Opération | Sortie | Composant |
|-------|--------|-----------|--------|-----------|
| 1️⃣  | Question texte (ex. « Quel est le prix du modèle X ? ») | Tokenisation → embedding | Vecteur d’interrogation | **Retriever** (dense ou sparse) |
| 2️⃣  | Vecteur d’interrogation | Recherche k‑NN dans l’index | *k* documents (texte + métadonnées) | **Retriever** (FAISS, Annoy, …) |
| 3️⃣  | Question + documents récupérés | Concatenation + passage à un LLM | Prompt complet | **Orchestrateur** (FastAPI, Celery…) |
| 4️⃣  | Prompt complet | Génération | Réponse naturelle | **Generator** (GPT‑3.5, LLaMA, …) |
| 5️⃣  | Réponse | (optionnel) post‑processing | Texte final | **Reader** (filtrage, reranking) |

Le **retriever** ne doit jamais voir le texte complet de la réponse générée ; il ne travaille qu’avec des embeddings. Le **generator** reçoit le texte complet (question + documents) et produit la réponse. Le **reader** (ou reranker) peut être un modèle de classification qui élimine les documents hors‑sujet avant la génération.

---

## 2. Types de recherche

| Type | Principe | Avantages | Inconvénients | Cas d’usage typique |
|------|----------|-----------|---------------|----------------------|
| **Sparse** (BM25, TF‑IDF) | Indexe les termes exacts et leur fréquence | Interprétable, peu de ressources GPU | Sensible à la synonymie, ne capture pas la sémantique | Corpus très structuré, recherche juridique |
| **Dense** (embeddings + ANN) | Vecteur dense représente le sens; recherche par proximité (cosine/L2) | Capture la sémantique, tolerant aux fautes d’orthographe | Nécessite un modèle d’embedding, index ANN coûteux | FAQ, assistance client, bases de connaissances non structurées |

**Choix du critère de distance**  
- Cosine : ‑1 → 1, invariant à la norme du vecteur, recommandé avec des embeddings L2‑normalisés.  
- L2 : distance euclidienne, sensible à la norme, utile quand les embeddings ne sont pas normalisés.

---

## 3. Métriques d’évaluation

| Métrique | Formule | Interprétation | Quand l’utiliser |
|----------|---------|----------------|------------------|
| **Recall@k** | \(\frac{\#\text{documents pertinents parmi les k récupérés}}{\#\text{documents pertinents dans le corpus}}\) | Capacité du retriever à ramener les bons documents | Évaluation du retriever (indépendante du generator) |
| **Precision@k** | \(\frac{\#\text{documents pertinents parmi les k récupérés}}{k}\) | Qualité du top‑k | Quand le coût de traitement de chaque document est élevé |
| **R‑Precision** | Precision@R, où R = nombre de documents pertinents pour la requête | Métrique unique, pas de paramètre *k* | Jeux de données où le nombre de pertinents varie |
| **MRR (Mean Reciprocal Rank)** | \(\frac{1}{|Q|}\sum_{q\in Q}\frac{1}{\text{rank}_{q}}\) | Position moyenne du premier document pertinent | Fine‑tuning de dual‑encoder |
| **BLEU / ROUGE** | Scores n‑grammes entre réponse générée et référence | Qualité de la génération (fluide vs factuel) | Évaluation du generator, souvent combinée à une métrique de factualité |

> **Note** : les métriques de récupération (Recall, MRR) sont calculées **avant** la génération. Les métriques de génération (BLEU, ROUGE) sont calculées **après**.

---

## 4. Gestion du contexte : tokens, chunking, fenêtrage

1. **Limite de tokens du LLM**  
   - GPT‑3.5‑turbo : 4096 tokens (prompt + réponse).  
   - LLaMA‑2‑13B : 4096 tokens (défaut).  
   - Dépassement → tronquage ou réduction du nombre de documents.

2. **Chunking**  
   - Découper chaque document en fragments de 200‑300 tokens (≈ 150‑200 mots).  
   - Conserver les métadonnées (ID, titre) pour le reranking.  
   - Exemple de fonction `chunk_text(text, max_tokens=256)`.

3. **Fenêtrage dynamique**  
   - Trier les *k* documents par score de similarité.  
   - Accumuler les chunks tant que `len(prompt_tokens) + len(chunk_tokens) ≤ max_context`.  
   - Si le budget est atteint, remplacer les chunks les moins pertinents.

4. **Compression de documents**  
   - Utiliser un modèle de résumé (ex. `facebook/bart-large-cnn`) pour réduire le texte avant l’injection dans le prompt.  
   - Vérifier que le résumé conserve les entités clés (ex. numéros de série).

---

## 5. Risques de contamination et mesures d’atténuation

---

## Module 2 — contenu

## 2.1 Représentations vectorielles  

| Méthode | Modèle | Dimension typique | Licence | Usage recommandé |
|--------|--------|-------------------|---------|------------------|
| BERT‑base (cased) | `bert-base-cased` (HuggingFace) | 768 | Apache‑2.0 | Texte court, besoin de contextualisation fine‑grained |
| Sentence‑Transformers (all‑mpnet‑base‑v2) | `sentence-transformers/all-mpnet-base-v2` | 768 | Apache‑2.0 | Recherche sémantique, bonne performance‑/‑latence |
| OpenAI embeddings (text‑embedding‑3‑large) | API OpenAI | 1536 | Commercial | Volume élevé, besoin d’API externe, pas de GPU local requis |

**Processus de création d’embeddings**  

```python
from transformers import AutoTokenizer, AutoModel
import torch

def embed_sentences(sentences: list[str], model_name: str = "sentence-transformers/all-mpnet-base-v2"):
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModel.from_pretrained(model_name)
    model.eval()
    with torch.no_grad():
        encoded = tokenizer(sentences, padding=True, truncation=True, return_tensors="pt")
        output = model(**encoded)
        # Moyenne des token embeddings, ignore le token CLS si présent
        embeddings = output.last_hidden_state.mean(dim=1)
        # L2‑normalisation (obligatoire pour la recherche cosine avec FAISS)
        embeddings = torch.nn.functional.normalize(embeddings, p=2, dim=1)
    return embeddings.cpu().numpy()
```

*Commentaires*  

* `tokenizer(..., truncation=True)` évite les dépassements de longueur maximale (512 tokens pour la plupart des BERT).  
* La moyenne pondérée par `mean(dim=1)` donne un vecteur de taille fixe, compatible avec tous les index.  
* La normalisation L2 (`F.normalize`) rend la distance cosine équivalente à un produit scalaire, ce qui simplifie les requêtes FAISS (`metric=faiss.METRIC_INNER_PRODUCT`).  

---

## 2.2 Structures d’indexation  

| Structure | Algorithme | Métrique native | Complexité d’insertion | Complexité de recherche (k‑NN) |
|-----------|------------|-----------------|------------------------|-------------------------------|
| IVF‑Flat | Inverted File, clusters k‑means | L2 ou inner‑product | O(1) (ajout à un posting list) | O(log n) + O(k · C)  (C = nb. de cellules probées) |
| IVF‑PQ | IVF + Product Quantization | L2 | O(1) | O(log n) + O(k) (approx. via codes) |
| HNSW | Hierarchical Navigable Small World graph | L2 ou inner‑product | O(log n) | O(log n) (pratiquement constant) |
| Flat | Brute‑force | L2 ou inner‑product | O(1) | O(n) (déconseillé > 10⁴ vecteurs) |

**Choix pratique**  

* **Petit jeu (< 10 000 vecteurs)** → `IndexFlatIP` (exact, aucune phase d’entraînement).  
* **Moyen‑grand jeu (10⁴‑10⁶)** → `IndexIVFFlat` avec `nlist≈√n` (ex. 256 pour n=65 536).  
* **Très grand jeu (> 10⁶) & latence < 5 ms** → `IndexHNSW32` (paramètre `M=32`).  

---

## 2.3 Normalisation et réduction de dimension  

```python
import numpy as np
from sklearn.decomposition import PCA

def reduce_dim(vectors: np.ndarray, target_dim: int = 256):
    """PCA sans centrement si les vecteurs sont déjà normalisés."""
    pca = PCA(n_components=target_dim, svd_solver="randomized")
    reduced = pca.fit_transform(vectors)
    # Re‑normaliser pour garder la métrique cosine cohérente
    reduced = reduced / np.linalg.norm(reduced, axis=1, keepdims=True)
    return reduced, pca
```

*Pièges*  

* **Centres non‑zero** : si les vecteurs sont L2‑normalisés, le centre est déjà proche de 0 ; centrer à nouveau introduit un biais.  
* **Perte de précision** : la plupart des modèles de passage (DPR, Contriever) conservent > 95 % de la variance dans les 256 premières composantes ; descendre sous 128 peut réduire le recall de > 5 %.  

---

## 2.4 API d’insertion, mise à jour, suppression  

### 2.4.1 Insertion batch (FAISS)

```python
import faiss, numpy as np

def build_index(vectors: np.ndarray, metric=faiss.METRIC_INNER_PRODUCT, nlist=256):
    d = vectors.shape[1]
    quantizer = faiss.IndexFlatIP(d)               # quantizer pour IVF
    index = faiss.IndexIVFFlat(quantizer, d, nlist, metric)
    index.train(vectors)                           # obligatoire avant add
    index.add(vectors)                             # batch unique
    return index
```

### 2.4.2 Insertion incrémentale (IVF)

```python
def add_incremental(index: faiss.IndexIVFFlat, new_vectors: np.ndarray):
    # FAISS ne supporte pas l’ajout après entraînement si l’index n’est pas en mode “addable”
    # Il faut appeler `index.make_direct_map()` avant le premier add.

---

## Module 3 — contenu

## 3.1 Construction du jeu d’entraînement : paires requête‑document  

| Étape | Action concrète | Vérification |
|------|----------------|--------------|
| 3.1.1 | Collecter les **queries** (questions, prompts) et les **passages** (paragraphes) pertinents. | Chaque query doit avoir au moins un passage positif (réponse correcte). |
| 3.1.2 | Générer les **négatifs** : <br>‑ *random negatives* : passages tirés aléatoirement dans le corpus. <br>‑ *hard negatives* : passages proches du positif selon un modèle pré‑entraîné (ex. `sentence‑transformers/all‑mpnet-base-v2`). | Calculer la distance cosine entre le query embedding et chaque passage ; garder les k passages les plus proches qui ne sont pas le positif. |
| 3.1.3 | Formater le fichier **TSV** : `query_id<TAB>query_text<TAB>positive_passage_id<TAB>positive_passage_text<TAB>negative_passage_id<TAB>negative_passage_text`. | Le nombre de colonnes doit être constant ; chaque ligne représente un *triplet* (query, pos, neg). |
| 3.1.4 | Splitter **train / dev** (ex. 80 % / 20 %). | Vérifier que les IDs de passages ne se chevauchent pas entre les deux splits. |

### Exemple de script de hard‑negative mining (Python 3.9)

```python
# hard_negative_mining.py
import csv
import argparse
from pathlib import Path
import torch
from sentence_transformers import SentenceTransformer, util

def load_corpus(corpus_path: Path):
    """Retourne dict {pid: passage_text}."""
    corpus = {}
    with corpus_path.open(encoding="utf-8") as f:
        reader = csv.reader(f, delimiter="\t")
        for pid, text in reader:
            corpus[pid] = text
    return corpus

def mine_hard_negatives(queries, corpus, model_name="sentence-transformers/all-mpnet-base-v2",
                        top_k=5, batch_size=64):
    model = SentenceTransformer(model_name, device="cuda")
    # Encode passages once
    passage_ids, passage_texts = zip(*corpus.items())
    passage_emb = model.encode(passage_texts, batch_size=batch_size,
                               normalize_embeddings=True, show_progress_bar=True)
    # Encode queries
    query_ids, query_texts = zip(*queries.items())
    query_emb = model.encode(query_texts, batch_size=batch_size,
                             normalize_embeddings=True, show_progress_bar=True)

    # Recherche k‑NN pour chaque query
    hard_negs = {}
    for qid, qvec in zip(query_ids, query_emb):
        scores = util.cos_sim(qvec, passage_emb)[0]          # (n_passages,)
        top_idx = torch.topk(scores, k=top_k + 1).indices   # +1 pour exclure le positif éventuel
        # Filtrer le positif s’il apparaît dans les top‑k
        filtered = [pid for i, pid in enumerate(passage_ids) if i in top_idx and pid != queries[qid]["pos_id"]]
        hard_negs[qid] = filtered[:top_k]
    return hard_negs

def main(args):
    corpus = load_corpus(Path(args.corpus))
    # queries.tsv → {qid: {"text": ..., "pos_id": ...}}
    queries = {}
    with open(args.queries, encoding="utf-8") as f:
        for line in f:
            qid, qtxt, pos_id = line.strip().split("\t")
            queries[qid] = {"text": qtxt, "pos_id": pos_id}
    hard_negs = mine_hard_negatives(
        {qid: {"text": q["text"], "pos_id": q["pos_id"]} for qid, q in queries.items()},
        corpus,
        top_k=args.top_k,
    )
    # Écriture du fichier d’entraînement
    out_path = Path(args.out)
    with out_path.open("w", encoding="utf-8", newline="") as fout:
        writer = csv.writer(fout, delimiter="\t")
        for qid, q in queries.items():
            pos_id = q["pos_id"]
            pos_txt = corpus[pos_id]
            for neg_id in hard_negs[qid]:
                neg_txt = corpus[neg_id]
                writer.writerow([qid, q["text"], pos_id, pos_txt, neg_id, neg_txt])

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus", required=True, help="TSV pid<tab>passage")
    parser.add_argument("--queries", required=True, help="TSV qid<tab>query<tab>pos_id")
    parser.add_argument("--out", required=True, help="TSV d’entraînement")
    parser.add_argument("--top_k", type=int, default=5, help="Nombre de hard negatives")
    args = parser.parse_args()
    main(args)
```

*Commentaires clés*  

* `SentenceTransformer(..., device="cuda")` accélère le calcul d’embeddings.  
* `normalize_embeddings=True` garantit que la distance cosine = produit scalaire.  
* Le `+1` dans `top_k+1` évite que le passage positif soit compté comme négatif.  

---

## 3.2 Architecture dual‑encoder : partage de poids (si‑si)

- **Query encoder** et **passage encoder** sont deux instances du même

---

## Module 4 — contenu

## Module 4 – Intégration du RAG dans des applications production  

### 4.1 Orchestration du pipeline  

| Composant | Rôle | Points de vigilance |
|-----------|------|----------------------|
| **FastAPI** | serveur HTTP asynchrone, expose les endpoints RAG | éviter le `await` bloquant, garder le serveur en mode *uvicorn* avec `--workers` ≥ 2 |
| **Celery** | exécute les tâches lourdes (génération LLM) hors du thread HTTP | ne pas lancer de tâches synchrones depuis le worker, configurer `task_acks_late=True` pour la résilience |
| **gRPC** (optionnel) | appel interne entre le service de recherche et le service de génération, sérialisation binaire (Protobuf) | le coût de sérialisation peut dépasser 5 ms ; mesurer le temps de *marshalling* dans les métriques |

#### Exemple d’orchestration (FastAPI + Celery)  

```python
# app/main.py
import os
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from celery import Celery
import redis
import jwt
import time
import prometheus_client
from prometheus_client import Histogram, Counter

# ---------- Configuration ----------
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
FAISS_INDEX_PATH = "data/faiss.index"
JWT_SECRET = os.getenv("JWT_SECRET", "change_me")
CELERY_BROKER = os.getenv("CELERY_BROKER", "redis://localhost:6379/1")
CELERY_BACKEND = os.getenv("CELERY_BACKEND", "redis://localhost:6379/2")

# ---------- Services ----------
app = FastAPI()
celery_app = Celery(broker=CELERY_BROKER, backend=CELERY_BACKEND)
cache = redis.from_url(REDIS_URL, decode_responses=True)

# ---------- Prometheus ----------
REQUEST_LATENCY = Histogram(
    "rag_request_latency_seconds",
    "Latency of the RAG endpoint (seconds)",
    ["stage"]
)
CACHE_HIT = Counter("rag_cache_hits_total", "Number of cache hits")
CACHE_MISS = Counter("rag_cache_misses_total", "Number of cache misses")

# ---------- Sécurité ----------
security = HTTPBearer()

def verify_jwt(creds: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(creds.credentials, JWT_SECRET, algorithms=["HS256"])
        return payload  # dict contenant "sub", "role", …
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=401, detail="Invalid token") from exc

# ---------- Modèles ----------
class QueryRequest(BaseModel):
    query: str
    top_k: int = 5

class GenerationResponse(BaseModel):
    answer: str
    sources: list[str]

# ---------- Recherche vectorielle ----------
def load_faiss():
    import faiss, numpy as np, pickle
    index = faiss.read_index(FAISS_INDEX_PATH)
    with open("data/id2doc.pkl", "rb") as f:
        id2doc = pickle.load(f)
    return index, id2doc

FAISS_INDEX, ID2DOC = load_faiss()

def embed(text: str) -> list[float]:
    """Embedding via OpenAI API – synchronisé pour la demo."""
    import openai
    resp = openai.Embedding.create(input=text, model="text-embedding-ada-002")
    return resp["data"][0]["embedding"]

def search(query: str, top_k: int):
    vec = embed(query)
    D, I = FAISS_INDEX.search(np.array([vec], dtype="float32"), top_k)
    docs = [ID2DOC[i] for i in I[0]]
    return docs, D[0].tolist()

# ---------- Génération (Celery) ----------
@celery_app.task(name="generate_answer")
def generate_answer(prompt: str) -> str:
    """Appel bloquant à l’API LLM – isolé du thread HTTP."""
    import openai
    resp = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0,
    )
    return resp["choices"][0]["message"]["content"]

# ---------- Endpoint ----------
@app.post("/rag", response_model=GenerationResponse)
async def rag_endpoint(
    payload: QueryRequest,
    token: dict = Depends(verify_jwt),
    request: Request = None,
):
    # 1️⃣ Cache lookup (key = hash(query+top_k))
    cache_key = f"rag:{payload.query}:{payload.top_k}"
    cached = cache.get(cache_key)
    if cached:
        CACHE_HIT.inc()
        return GenerationResponse.parse_raw(cached)

    CACHE_MISS.inc()
    # 2️⃣ Recherche vectorielle (mesure latence)
    with REQUEST_LATENCY.labels(stage="search").time():
        docs, distances = search(payload.query, payload.top_k)

    # 3️⃣ Construction du prompt
    context = "\n---\n".join(docs)
    prompt = f"""You are a concise assistant. Answer the user query using only the following excerpts (keep citations):
{context}

Question: {payload.query}

---

## Module 5 — contenu

## Module 5 : Optimisation avancée et bonnes pratiques de maintenance  

### 5.1. Gestion du cycle de vie des embeddings  

| Phase | Action | Détails vérifiables |
|-------|--------|---------------------|
| **Création** | Fixer la version du modèle d’embedding (ex. `sentence‑transformers/all‑mpnet‑base‑v2` v 1.2.0). | Le hash du fichier `pytorch_model.bin` doit être stocké dans le catalogue de métadonnées. |
| **Versionnage** | Chaque jeu d’embeddings possède un `embedding_id` unique (UUID) et un `model_version`. | Le champ `embedding_id` est indexé dans la table `embeddings_meta`. |
| **Mise à jour** | Utiliser une **re‑indexation incrémentale** : ajouter les nouveaux vecteurs avec le même `index_name` puis **merge** (FAISS : `index.merge_from`). | Le taux de rappel (`recall@10`) avant et après merge doit rester > 0,95 sur le jeu de validation. |
| **Dépréciation** | Marquer les anciens vecteurs comme `archived` et les exclure des recherches via un filtre de métadonnées. | La requête `filter={"archived":false}` doit renvoyer uniquement les vecteurs actifs. |
| **Archivage** | Exporter les vecteurs archivés vers un stockage froid (ex. S3) au format `npz` + métadonnées JSON. | Le script d’archivage doit générer un checksum SHA‑256 et le consigner dans le log d’audit. |

#### Piège concret  
> **Ne pas ré‑indexer les embeddings après un changement de modèle** conduit à un **drift** : les vecteurs sont dans un espace différent de celui du modèle de requête, ce qui fait chuter le MRR de plus de 30 % en moyenne (mesuré sur MS‑MARCO).  

**Solution** : automatiser le recalcul complet dès que `model_version` change, même si le coût de calcul est élevé ; planifier la tâche pendant les fenêtres de faible trafic.

---

### 5.2. Optimisation de l’index vectoriel  

#### 5.2.1. Choix de la structure d’index  

| Structure | Complexité moyenne (recherche) | Mémoire (bits/vecteur) | Cas d’usage recommandé |
|-----------|-------------------------------|------------------------|------------------------|
| **IVF‑Flat** (FAISS) | `O(log n)` (coarse quantizer) | 4 × d (float32) | Jeux de données < 10 M, besoin de haute précision. |
| **IVF‑PQ** | `O(log n)` + décodage PQ | 1 × d/8 (8 bits/centroïde) | Jeux > 10 M, contrainte mémoire stricte. |
| **HNSW** | `O(log n)` (graph navigation) | 2 × d (float32) | Recherche ultra‑rapide (< 1 ms) sur GPU/CPU, tolérance à un léger rappel réduit. |
| **IVF‑HNSW** (FAISS) | `O(log n)` + `O(log n)` | 2 × d (float32) | Compromis entre précision HNSW et filtrage IVF pour très grands corpus (> 100 M). |

**Règle d’or** : mesurer `recall@k` et la latence sur un sous‑ensemble de 10 k requêtes avant de déployer en production.  

#### 5.2.2. Quantisation et distillation  

- **Quantisation 8‑bits (FAISS `IndexIVFPQ` + `faiss.IndexScalarQuantizer`)** réduit la mémoire de 4×, mais le rappel chute typiquement de 0,02 à 0,07 selon la distribution des vecteurs.  
- **Distillation de modèle d’embedding** (ex. `MiniLM‑L6‑v2` à la place de `MPNet`) diminue le dimensionnement de 768 à 384, ce qui accélère le calcul de la similarité de 30 % tout en conservant un MRR > 0,68 sur le même jeu.  

**Piège** : appliquer la quantisation **sans recalibrer** les paramètres du `nlist` (IVF) entraîne un déséquilibre de clusters et augmente le taux de « empty lists » ; le rappel chute de plus de 15 %.  

**Correction** : après quantisation, recomposer l’index avec `nlist = sqrt(N)` (arrondi à la puissance de 2) et ré‑entraîner le coarse quantizer (`faiss.Clustering`).  

---

### 5.3. Monitoring, alerting et observabilité  

#### 5.3.1. Métriques essentielles (exposé via **Prometheus**)

```python
# metrics.py
from prometheus_client import Counter, Histogram, Gauge, start_http_server
import time

# Compteurs
REQ_TOTAL = Counter(
    "rag_requests_total",
    "Nombre total de requêtes RAG trait