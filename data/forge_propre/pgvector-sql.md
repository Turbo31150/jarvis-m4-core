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
- Stratégies de partitionnement pour jeux de données très volumineux.

## Module 3 : Recherche de similarité avec les index ivfflat  
**Objectif mesurable** : Créer un index `ivfflat` sur une colonne vectorielle, l’entraîner (`CREATE INDEX … USING ivfflat (embedding) WITH (lists = 100);`) et exécuter une requête de k‑NN (`SELECT * FROM items ORDER BY embedding <-> '[0.1,0.2,…]' LIMIT 10;`) qui renvoie les 10 plus proches en un temps très court sur un jeu d’enregistrements de taille importante.  
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
| Vérifier la version installée | `SELECT extversion FROM pg_extension WHERE extname='vector';` | Retourne, par exemple, `0.5.0`. |
| Mettre à jour (si une version plus récente est disponible) | `ALTER EXTENSION vector UPDATE;` | Applique les scripts SQL de migration. |
| Forcer une version précise | `ALTER EXTENSION vector UPDATE TO '0.6.0';` | Nécessaire lorsqu’on a plusieurs versions dans le dépôt. |

---

## 3. Configuration de PostgreSQL pour les vecteurs  

### 3.1. Paramètre `vector.max_dimensions`  

*Valeur par défaut* : `2048`.  
Définir dans `postgresql.conf` (ou via `ALTER SYSTEM`) si l’on prévoit des embeddings supérieurs à la dimension par défaut (ex. CLIP = 512 → pas besoin).  

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

> **Piège** : forcer `PLAIN` sur des vecteurs de 768 dims (float4) crée des lignes de plusieurs kilooctets, dépassant la taille de page (8 KB) et déclenchant un **ERROR:  row is too big**. Utiliser le type `vector(768)` (float4) qui reste sous le seuil ou laisser le stockage TOAST par défaut.

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
- L’erreur de quantification est négligeable pour la recherche de similarité.

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
- **Taille** : un vecteur 768 × 4 bytes ≈ quelques kilooctets ; plusieurs millions d’enregistrements occupent plusieurs dizaines de gigaoctets, avec overhead TOAST.  

#### 2.4.2. Insertion massive avec `COPY`

```sql
-- 1. Créez un fichier CSV (ou TSV) où la colonne vector est