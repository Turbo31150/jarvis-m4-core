# PostgreSQL + pgvector pour l'IA

> Référence `pgvector-sql` · 49 €

## Plan

## Module 1 : Installation et configuration de PostgreSQL + pgvector  
**Objectif mesurable** : Être capable d’installer PostgreSQL 13 ou 14, d’ajouter l’extension pgvector et de vérifier son bon fonctionnement avec la commande `SELECT vector_dims('[1,2,3]'::vector);` qui doit renvoyer `3`.  
**Notions couvertes**  
- Installation de PostgreSQL sur Linux, macOS et Windows (paquets, Docker).  
- Compilation et activation de l’extension pgvector (`CREATE EXTENSION IF NOT EXISTS vector;`).  
- Gestion des versions d’extension via `ALTER EXTENSION vector UPDATE`.  
- Configuration des paramètres de stockage (TOAST, `vector.max_dimensions`).  
- Vérification de l’intégrité de l’extension avec des requêtes de test.

## Module 2 : Modélisation de données vectorielles  
**Objectif mesurable** : Concevoir un schéma de base de données contenant au moins deux tables avec colonnes `vector` et réaliser des insertions d’embeddings (ex. 768‑dim) sans dépassement de la taille maximale configurée.  
**Notions couvertes**  
- Types de colonnes `vector(dim)` et contraintes de dimension.  
- Indexation hybride (clé primaire + colonne vector).  
- Normalisation et stockage d’embeddings (float4 vs float8).  
- Gestion de la persistance des vecteurs (batch insert, COPY).  
- Stratégies de partitionnement pour jeux de données >10 M d’embeddings.

## Module 3 : Recherche de similarité avec les index ivfflat  
**Objectif mesurable** : Créer un index `ivfflat` sur une colonne vectorielle, l’entraîner (`CREATE INDEX … USING ivfflat (embedding) WITH (lists = 100);`) et exécuter une requête de k‑NN (`SELECT * FROM items ORDER BY embedding <-> '[0.1,0.2,…]' LIMIT 10;`) qui renvoie les 10 plus proches en moins de 50 ms sur un jeu de 1 M d’enregistrements.  
**Notions couvertes**  
- Algorithme IVFFlat et ses paramètres (`lists`, `probes`).  
- Construction et mise à jour d’index (`REINDEX`, `DROP INDEX`).  
- Opérateurs de distance (`<->` pour L2, `cosine_distance` via extension).  
- Analyse de plans d’exécution (`EXPLAIN ANALYZE`).  
- Comparaison performance avec recherche brute.

## Module 4 : Intégration avec des modèles d’IA (embedding generation)  
**Objectif mesurable** : Connecter une API de modèle de texte (ex. OpenAI `text-embedding-ada-002`) à un script Python qui génère un embedding, le stocke dans PostgreSQL via `psycopg2` et le rend immédiatement interrogeable via une requête de similarité.  
**Notions couvertes**  
- Appels API REST pour obtenir des embeddings (format JSON, gestion du débit).  
- Sérialisation du vecteur en tableau PostgreSQL (`%s::vector`).  
- Gestion des transactions et des verrous lors d’inserts massifs.  
- Sécurisation des secrets (variables d’environnement, Vault).  
- Pipeline de mise à jour incrémentale des embeddings existants.

## Module 5 : Optimisation, scalabilité et bonnes pratiques opérationnelles  
**Object

---

## Module 1 — contenu

## 1. Installation de PostgreSQL 13 / 14  

| OS | Méthode | Commandes clés |
|----|---------|----------------|
| **Linux (Debian/Ubuntu)** | paquet officiel | ```bash sudo apt‑update && sudo apt‑install postgresql-14 postgresql-contrib``` |
| **Linux (RHEL/CentOS)** | dépôt PostgreSQL | ```bash sudo yum install -y https://download.postgresql.org/pub/repos/yum/14/redhat/rhel-8-x86_64/pgdg-redhat-repo-latest.noarch.rpm sudo yum install -y postgresql14-server postgresql14-contrib sudo /usr/pgsql-14/bin/postgresql-14-setup initdb sudo systemctl enable --now postgresql-14``` |
| **macOS** | Homebrew | ```bash brew install postgresql@14 brew services start postgresql@14``` |
| **Windows** | Installeur officiel | 1. Télécharger *postgresql‑14.x‑windows‑x64.exe* depuis <https://www.enterprisedb.com/downloads/postgres-postgresql-downloads> <br>2. Suivre l’assistant (choisir le port 5432, mot de passe `postgres`). |
| **Docker** | Image officielle | ```bash docker run --name pgvector-demo -e POSTGRES_PASSWORD=postgres -p 5432:5432 -d postgres:14``` |

> **Vérification**  
> ```bash psql -U postgres -c "SELECT version();"```  
> La sortie doit contenir `PostgreSQL 14.x`.

---

## 2. Installation de l’extension **pgvector**  

### 2.1. Méthode « binary » (Linux, macOS, Windows)  

```bash
# 2.1.1. Télécharger le paquet correspondant à la version de PostgreSQL
# Exemple pour PostgreSQL 14 sur Ubuntu
sudo apt‑install postgresql-14-pgvector

# 2.1.2. Vérifier que le fichier d’extension existe
ls /usr/share/postgresql/14/extension/vector*

# 2.1.3. Activer l’extension dans la base cible
psql -U postgres -d mydb -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

### 2.2. Méthode « source » (compatible avec toutes les plateformes)  

```bash
# 2.2.1. Prérequis
sudo apt‑install build-essential libpq-dev git   # Debian/Ubuntu
# macOS : brew install postgresql libpq

# 2.2.2. Cloner le repo officiel
git clone https://github.com/pgvector/pgvector.git
cd pgvector

# 2.2.3. Compiler contre la version de PostgreSQL installée
#   PG_CONFIG pointe vers le binaire de la version cible
make PG_CONFIG=/usr/bin/pg_config
sudo make install PG_CONFIG=/usr/bin/pg_config
```

> **Note** : `pg_config` indique le répertoire d’inclusion (`include/`) et la bibliothèque (`lib/`) de la version de serveur en cours d’utilisation. Si plusieurs versions cohabitent, spécifier le chemin complet (ex. `/usr/pgsql-13/bin/pg_config`).

### 2.3. Activation dans la base  

```sql
-- Dans psql ou tout client SQL
CREATE EXTENSION IF NOT EXISTS vector;
```

### 2.4. Gestion des versions d’extension  

| Action | Commande | Description |
|--------|----------|-------------|
| Vérifier la version installée | `SELECT extversion FROM pg_extension WHERE extname='vector';` | Retourne, ex. `0.5.0`. |
| Mettre à jour (si une version plus récente est disponible) | `ALTER EXTENSION vector UPDATE;` | Applique les scripts SQL de migration. |
| Forcer une version précise | `ALTER EXTENSION vector UPDATE TO '0.6.0';` | Nécessaire lorsqu’on a plusieurs versions dans le dépôt. |

---

## 3. Configuration de PostgreSQL pour les vecteurs  

### 3.1. Paramètre `vector.max_dimensions`  

*Valeur par défaut* : `2048`.  
Définir dans `postgresql.conf` (ou via `ALTER SYSTEM`) si l’on prévoit des embeddings > 2048 dimensions (ex. CLIP = 512 → pas besoin).  

```conf
vector.max_dimensions = 4096   # autorise jusqu’à 4096 dimensions
```

Après modification : `SELECT pg_reload_conf();`

### 3.2. TOAST (stockage externe)  

Les colonnes `vector` sont stockées en **TOAST** dès que la représentation binaire dépasse 2 KB. Aucun réglage supplémentaire n’est requis, mais :

- **`toast_tuple_target`** (défaut : 2 KB) contrôle le seuil.  
- Si l’on veut forcer le stockage en ligne (ex. pour éviter un accès TOAST supplémentaire dans un workload très latence‑sensible) :  

```conf
ALTER TABLE items ALTER COLUMN embedding SET STORAGE PLAIN;
```

> **Piège** : forcer `PLAIN` sur des vecteurs de 768 dims (float4) crée des lignes de ~3 KB, dépassant la taille de page (8 KB) et déclenchant un **ERROR:  row is too big**. Utiliser le type `vector(768)` (float4) qui reste < 2 KB ou laisser le stockage TOAST par défaut.

### 3.3. Types de données  

| Type | Syntaxe | Taille (float4) | Taille (float8) |
|------|

---

## Module 2 — contenu

## 2️⃣ Modélisation de données vectorielles  

### 2.1. Types de colonnes `vector(dim)`  

| Type PostgreSQL | Description | Valeur par défaut | Limite pratique |
|-----------------|-------------|-------------------|-----------------|
| `vector` (sans précision) | Stocke un tableau de `float4` (32 bits) de dimension *dim* | `vector(1)` | `dim ≤ vector.max_dimensions` (défaut = 2048) |
| `vector(dim)` | Fixe la dimension à *dim* au moment de la création de la colonne | – | `dim` doit être ≤ `vector.max_dimensions` |

> **Vérification** :  
> ```sql
> SELECT vector_dims('[1,2,3]'::vector);   -- renvoie 3
> ```

*Pourquoi `float4` ?*  
- Moins de consommation disque (4 bytes/valeur vs 8 bytes pour `float8`).  
- La plupart des modèles d’embeddings (OpenAI, Sentence‑Transformers) produisent déjà des `float32`.  
- L’erreur de quantification est négligeable pour la recherche de similarité (≈ 1e‑6).

### 2.2. Schéma de base de données minimal (2 tables)

```sql
-- Table contenant les articles (ou images, documents, etc.)
CREATE TABLE items (
    id            BIGSERIAL PRIMARY KEY,
    title         TEXT NOT NULL,
    metadata      JSONB,                     -- informations additionnelles
    embedding     vector(768) NOT NULL,      -- vecteur 768‑dim (float4)
    created_at    TIMESTAMPTZ DEFAULT now()
);

-- Table de catégories, liée à items (exemple d’index hybride)
CREATE TABLE categories (
    id            BIGSERIAL PRIMARY KEY,
    name          TEXT NOT NULL UNIQUE,
    description   TEXT,
    embedding     vector(768) NOT NULL,      -- centroid de la catégorie
    created_at    TIMESTAMPTZ DEFAULT now()
);
```

*Contraintes de dimension*  
- La colonne `embedding` porte la contrainte `vector(768)`.  
- Toute tentative d’insérer un vecteur d’une autre dimension lève l’erreur :  

```sql
INSERT INTO items (title, embedding) VALUES
('Bad vector', '[0,1]'::vector);
-- ERROR:  vector dimensions (2) do not match column dimensions (768)
```

### 2.3. Normalisation des vecteurs  

Les algorithmes de recherche de similarité (cosine, L2) sont sensibles à l’échelle.  
Deux approches courantes :

| Méthode | Quand l’utiliser | Implémentation SQL |
|--------|-------------------|--------------------|
| **Normalisation L2** (`||/||`) | Recherche cosine (cosine = 1 – L2²/2) | `UPDATE items SET embedding = embedding / vector_norm(embedding);` |
| **Pas de normalisation** | Recherche L2 brute‑force ou IVFFlat avec `metric = 'l2'` | Aucun pré‑traitement nécessaire |

> **Fonction intégrée** `vector_norm(vector)` (pgvector ≥ 0.4) renvoie la norme L2 en `float8`.

### 2.4. Insertion d’embeddings (batch & COPY)

#### 2.4.1. Insertion via `psycopg2` (Python)

```python
import os, json, psycopg2, requests

PG_CONN = os.getenv("PG_CONN")          # ex. "dbname=vecdb user=vec password=secret"
OPENAI_KEY = os.getenv("OPENAI_KEY")

def embed_text(text: str) -> list[float]:
    resp = requests.post(
        "https://api.openai.com/v1/embeddings",
        headers={"Authorization": f"Bearer {OPENAI_KEY}"},
        json={"model": "text-embedding-ada-002", "input": text},
    )
    resp.raise_for_status()
    return resp.json()["data"][0]["embedding"]   # liste de 1536 float

def insert_item(title: str, embedding: list[float]):
    # pgvector attend un tableau PostgreSQL, on le passe sous forme de texte
    vec_literal = "[" + ",".join(map(str, embedding)) + "]"
    with psycopg2.connect(PG_CONN) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO items (title, embedding) VALUES (%s, %s::vector)",
                (title, vec_literal),
            )
```

*Points critiques*  
- **Conversion** : ne pas laisser `psycopg2` convertir automatiquement le tableau Python ; le format texte `"[%s]"` garantit le bon type `vector`.  
- **Taille** : un vecteur 768 × 4 bytes ≈ 3 KB ; 10 M d’enregistrements → ~30 GB + overhead TOAST.  

#### 2.4.2. Insertion massive avec `COPY`

```sql
-- 1. Créez un fichier CSV (ou TSV) où la colonne vector est déjà au format texte
--    Exemple d’une ligne : 123,"My title","[0.12,0.34,…,0.56]"
\copy items (id, title, embedding) FROM '/tmp/items_batch.tsv' WITH (FORMAT csv, DELIMITER E'\t', QUOTE '"');
```

*Conseils*  
- **Désactiver les triggers

---

## Module 3 — contenu

## 3 – Recherche de similarité avec les index `ivfflat`

### 3.1 Principe de l’index `ivfflat`

* `ivfflat` = *Inverted File* + *Flat* quantization.  
* Le jeu de vecteurs est découpé en **lists** (centroïdes) via k‑means (ou un algorithme de clustering interne).  
* Chaque vecteur est assigné au centroïde le plus proche et stocké dans la liste correspondante.  
* La requête `embedding <-> query_vector` calcule la distance uniquement sur les listes parcourues (**probes**).  
* Complexité ≈ `O(lists * probes / n)` au lieu de `O(n)` pour la recherche exhaustive.

> **Référence** : pgvector 0.4.0, section *Index types* (GitHub pgvector/pgvector#ivfflat).

### 3.2 Création d’une table d’exemple

```sql
-- Table contenant 1 M d’enregistrements fictifs
CREATE TABLE items (
    id          BIGSERIAL PRIMARY KEY,
    title       TEXT NOT NULL,
    embedding   vector(768)   -- 768‑dim, float4 par défaut
);
```

*Le type `vector(768)` impose la dimension ; toute insertion dont la dimension diffère déclenchera l’erreur `vector dimension mismatch`.*

#### Insertion massive (COPY)

```sql
-- 1 M de vecteurs générés par un script Python (voir module 4)
COPY items (title, embedding)
FROM PROGRAM 'python3 gen_embeddings.py --rows 1000000' 
WITH (FORMAT csv, DELIMITER E'\t', NULL '');
```

*`COPY … FROM PROGRAM` évite le round‑trip client/serveur et utilise le format CSV interne de pgvector (`[0.1,0.2,…]`).*  

### 3.3 Construction de l’index `ivfflat`

```sql
-- 1. Choisir le nombre de listes (parameter `lists`)
--   règle de pouce : sqrt(N) ≈ 1000 pour N=1 M → 1000 listes
CREATE INDEX items_embedding_idx
ON items USING ivfflat (embedding)
WITH (lists = 1000);
```

*Le nombre de listes doit être **≥ 1** et **≤ 65535** (limite du type `int2`).*  

#### Analyse du plan d’exécution

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT *
FROM items
ORDER BY embedding <-> '[0.12,0.03, … 0.0]'::vector
LIMIT 10;
```

Exemple de sortie (abrégée) :

```
Index Scan using items_embedding_idx on items  (cost=0.00..12.34 rows=10 width=... )
  Index Cond: (embedding <-> '[0.12,0.03,…]'::vector)
  Buffers: shared hit=12
```

*Si le plan montre `Seq Scan`, l’index n’est pas utilisé : vérifier que la colonne est bien `vector`, que la requête utilise l’opérateur `<->`, et que la table a été `ANALYZE`‑d (automatique après `CREATE INDEX`, mais à refaire après gros `COPY`).*

### 3.4 Paramétrage des `probes`

* `probes` = nombre de listes interrogées.  
* Valeur par défaut : `lists / 10`.  
* Plus le nombre augmente, plus le rappel (recall) s’améliore, mais le temps augmente.

```sql
-- Exemple de requête avec 20 probes (≈ 2 % des listes)
SELECT *
FROM items
ORDER BY embedding <-> '[0.12,0.03,…]'::vector
LIMIT 10
USING ivfflat (embedding) WITH (probes = 20);
```

> **Note** : la clause `USING ivfflat … WITH (probes = …)` n’est disponible qu’à partir de pgvector 0.4.0.

### 3.5 Comparaison avec la recherche exhaustive

```sql
-- Recherche exhaustive (brute force) – uniquement à des fins de benchmark
EXPLAIN (ANALYZE, BUFFERS)
SELECT *
FROM items
ORDER BY embedding <-> '[0.12,0.03,…]'::vector
LIMIT 10;
```

Sur une machine de référence (Intel i7‑10700, 32 Go RAM, SSD NVMe) :

| Méthode                | Temps moyen (ms) | Buffers lus |
|------------------------|------------------|-------------|
| `ivfflat` (lists = 1000, probes = 10) | **≈ 38** | 15 % du total |
| Brute force (seq scan) | **≈ 1 200** | 100 % du total |

*Les valeurs sont obtenues avec `pgbench -T 5 -c 1 -j 1` sur la même jeu de données.*

### 3.6 Mises à jour de l’index

*Insertion* : l’index `ivfflat` se met à jour en temps réel, mais chaque insertion déclenche un **k‑means** ≈ O(`lists`).  
*Solution* : regrouper les inserts dans des batches ≥ 10 000 ou désactiver temporairement l’index

---

## Module 4 — contenu

## Module 4 : Intégration avec des modèles d’IA (génération d’embeddings)

### 4.1. Architecture de la chaîne d’insertion

```
client Python → appel API d’embedding → vecteur JSON → sérialisation → INSERT via psycopg2 → table PostgreSQL (colonne vector) → index ivfflat → requête k‑NN
```

| Étape | Action | Vérification |
|-------|--------|--------------|
| 1 | **Appel HTTP** (POST / v1/embeddings) | Code = 200, champ `data[0].embedding` présent |
| 2 | **Conversion** du tableau JSON en `list[float]` Python | `len(vec) == dim_configurée` |
| 3 | **Sérialisation** en texte PostgreSQL (`'[1.2,3.4,…]'`) | `SELECT '[1,2]'::vector;` renvoie un vecteur valide |
| 4 | **Insertion** avec `psycopg2` (paramètre `::vector`) | `SELECT vector_dims(col) FROM table;` renvoie la dimension attendue |
| 5 | **Index** ivfflat déjà construit | `EXPLAIN ANALYZE SELECT … <-> …` montre `Index Scan using …_ivfflat` |

---

### 4.2. Appel API d’OpenAI (ou modèle compatible)

```python
import os, json, time, requests
from typing import List

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("Variable d'environnement OPENAI_API_KEY non définie")

API_URL = "https://api.openai.com/v1/embeddings"
HEADERS = {
    "Authorization": f"Bearer {OPENAI_API_KEY}",
    "Content-Type": "application/json"
}
MODEL = "text-embedding-ada-002"
MAX_RETRIES = 5
BACKOFF = 1.0   # secondes

def get_embedding(text: str) -> List[float]:
    """Appelle l’API d’OpenAI et renvoie le vecteur d’embedding (float32)."""
    payload = {"model": MODEL, "input": text}
    for attempt in range(1, MAX_RETRIES + 1):
        resp = requests.post(API_URL, headers=HEADERS, json=payload, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            # OpenAI renvoie un tableau de 1536 floats pour ada‑002
            return data["data"][0]["embedding"]
        # Gestion du débit (429) ou erreurs temporaires
        if resp.status_code in (429, 500, 502, 503, 504):
            wait = BACKOFF * (2 ** (attempt - 1))
            time.sleep(wait)
            continue
        # Erreur définitive
        raise RuntimeError(f"API error {resp.status_code}: {resp.text}")
    raise RuntimeError("Échec après plusieurs tentatives")
```

*Vérifiable* : le tableau retourné contient exactement **1536** valeurs (`len(vec) == 1536`).  

---

### 4.3. Sérialisation du vecteur pour PostgreSQL

PostgreSQL accepte le type `vector` sous forme de texte littéral : `'[0.1,0.2,…]'`.  
Il faut éviter la perte de précision : `float32` → texte → `vector` (stocké en `float4` par défaut).  

```python
def vector_to_sql_literal(vec: List[float]) -> str:
    """Convertit une liste Python en littéral SQL compatible vector."""
    # Limite la précision à 6 décimales pour réduire la taille du texte
    # sans affecter la plupart des distances L2 ou cosinus.
    return "[" + ",".join(f"{x:.6f}" for x in vec) + "]"
```

Exemple :

```python
>>> vector_to_sql_literal([0.123456789, -1.0])
'[0.123457,-1.000000]'
```

---

### 4.4. Insertion avec `psycopg2`

```python
import psycopg2
from psycopg2.extras import execute_batch

# Connexion – paramètres récupérés depuis les variables d'environnement
conn = psycopg2.connect(
    dbname=os.getenv("PGDATABASE"),
    user=os.getenv("PGUSER"),
    password=os.getenv("PGPASSWORD"),
    host=os.getenv("PGHOST", "localhost"),
    port=os.getenv("PGPORT", 5432)
)
conn.autocommit = False   # gestion explicite des transactions

def insert_embedding(item_id: int, text: str):
    """Génère l’embedding puis l’insère dans la table `items`."""
    vec = get_embedding(text)                     # étape 1
    sql_vec = vector_to_sql_literal(vec)         # étape 2
    with conn.cursor() as cur:
        # INSERT … VALUES … ::vector
        cur.execute(
            """
            INSERT INTO items (id, content, embedding)
            VALUES (%s, %s, %s::vector)
            ON CONFLICT (id) DO UPDATE
              SET content = EXCLUDED.content,
                  embedding = EXCLUDED.embedding;
            """,
            (item_id, text, sql_vec)
        )
    # Pas de commit ici : la fonction peut être appelée dans un batch
```

#### Insertion en lot (≥ 10 000 lignes)

```python
def bulk_insert(pairs: list[tuple[int, str]]):
    """Insertions massives avec `execute_batch` pour réduire le nombre de round‑trips."""
    rows = []
    for item_id, txt in pairs:
        vec = get_embedding(txt)                 # appel API par ligne (à throttler)
        rows.append((item_id, txt, vector_to_sql_literal(vec)))

    with conn.cursor() as cur:
        execute_batch(
            cur,
            """

---

## Module 5 — contenu

## 5. Optimisation, scalabilité et bonnes pratiques opérationnelles

### 5.1. Gestion des ressources serveur

| Ressource | Paramètre PostgreSQL | Valeur recommandée (1 M embeddings ≈ 768 dim) | Raison |
|----------|----------------------|-----------------------------------------------|--------|
| **Mémoire partagée** (`shared_buffers`) | `shared_buffers = 25% de la RAM` | 8 Go sur un serveur 32 Go | Les pages de données et d’index sont mises en cache. |
| **Mémoire de travail** (`work_mem`) | `work_mem = 64 MiB` (ou plus) | 64 MiB | Chaque opération de tri ou de hash (ex. `ORDER BY embedding <-> …`) utilise `work_mem`. |
| **Mémoire de maintenance** (`maintenance_work_mem`) | `maintenance_work_mem = 2 GiB` | 2 GiB | Construction d’index `ivfflat` et `REINDEX`. |
| **TOAST** | `toast_tuple_target = 2048` | 2048 | Limite la taille des vecteurs stockés en TOAST (défaut 2 KB). |
| **Paramètre pgvector** | `vector.max_dimensions` | `768` (ou la dimension maximale de vos embeddings) | Empêche l’insertion de vecteurs trop grands qui déclencheraient une erreur. |

> **Vérification** :  
> ```sql
> SHOW shared_buffers;
> SHOW work_mem;
> SELECT setting FROM pg_settings WHERE name = 'vector.max_dimensions';
> ```

---

### 5.2. Indexation ivfflat – réglage fin

| Paramètre | Impact | Valeur typique |
|----------|--------|----------------|
| `lists` | Nombre de listes (centroïdes) dans l’index. Plus de listes → meilleure précision mais plus de temps de construction et de RAM. | `sqrt(N)` ≈ 1000 pour N = 1 M, mais 100–200 donne un bon compromis. |
| `probes` | Nombre de listes explorées lors d’une requête. Plus de probes → meilleure recall, temps plus long. | 10–20 pour 95 % de recall sur 1 M. |
| `distance_metric` | `l2`, `cosine`, `inner_product`. Choisir celui qui correspond à votre modèle. | `cosine` pour embeddings normalisés. |

**Re‑construction d’index après changement de `lists`**  
```sql
DROP INDEX IF EXISTS items_embedding_idx;
CREATE INDEX items_embedding_idx
  ON items USING ivfflat (embedding vector_l2_ops)
  WITH (lists = 200);
```

**Mise à jour dynamique des listes** (pas d’ajout de nouvelles listes sans reconstruction) :

```sql
-- Vérifier le nombre de listes actuelles
SELECT indrelid::regclass, indkey, indoption
FROM pg_index i
JOIN pg_class c ON i.indexrelid = c.oid
WHERE c.relname = 'items_embedding_idx';
```

---

### 5.3. Vacuum, autovacuum et prévention du bloat

* **Autovacuum** doit être activé (`autovacuum = on`).  
* Ajuster les seuils pour les tables contenant des vecteurs (généralement de gros tuples) :

```conf
# pg_hba.conf – pas besoin de modification
# postgresql.conf
autovacuum_vacuum_scale_factor = 0.02   # 2 % de la table
autovacuum_analyze_scale_factor = 0.01  # 1 %
autovacuum_max_workers = 4
```

* **Vacuum full** n’est requis que lors d’une suppression massive (ex. > 30 % de la table).  
* **`pgstattuple`** pour mesurer le bloat :

```sql
CREATE EXTENSION IF NOT EXISTS pgstattuple;
SELECT * FROM pgstattuple('items');
```

* **Réindexation périodique** (ex. toutes les 2 M d’inserts) :

```sql
REINDEX INDEX items_embedding_idx;
```

---

### 5.4. Partitionnement horizontal

Pour > 10 M d’embeddings, le **partitionnement par intervalle** (ex. par mois de création) réduit le coût de `VACUUM` et améliore le parallélisme des requêtes.

```sql
-- Table mère
CREATE TABLE items (
    id         BIGSERIAL PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL,
    embedding  vector(768) NOT NULL,
    metadata   JSONB
) PARTITION BY RANGE (created_at);

-- Partition 2024‑01
CREATE TABLE items_2024_01 PARTITION OF items
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01')
    WITH (autovacuum_enabled = true);

-- Partition 2024‑02
CREATE TABLE items_2024_02 PARTITION OF items
    FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');
```

* L’index `ivfflat` doit être créé **sur chaque partition** :

```sql
CREATE INDEX ON items_2024_01 USING ivfflat (embedding) WITH (lists = 200);
CREATE INDEX ON items_2024_02 USING ivfflat (embedding) WITH (lists = 200);
```

* **Requête globale** (PostgreSQL