# Elasticsearch & Recherche IA

> Référence `elasticsearch-ia` · 69 €

## Plan

## Module 1 – Architecture et déploiement d’Elasticsearch  
**Objectif** : Être capable d’installer, configurer et valider le fonctionnement d’un cluster Elasticsearch 8.x à trois nœuds en local ou sur un cloud public.  

**Notions couvertes**  
- Architecture distribuée : nœuds maître, data, coordinating & ingest.  
- Installation (packages DEB/RPM, Docker, Elastic Cloud) et paramètres de découverte (zen 2).  
- Gestion du quorum, allocation de shards primaires et répliques.  
- Outils de santé du cluster : `_cluster/health`, Cat API, métriques de JVM.  

---

## Module 2 – Modélisation des données et indexation  
**Objectif** : Concevoir un mapping adapté et indexer 1 million de documents JSON en respectant les contraintes de performance et de pertinence.  

**Notions couvertes**  
- Types de champs (keyword, text, date, numeric, dense_vector).  
- Analyseurs standards, personnalisés et tokenizers (standard, whitespace, ICU).  
- Templates d’index, rollover et policies ILM (Index Lifecycle Management).  
- Bulk API, gestion des erreurs et optimisation du taux d’ingestion.  

---

## Module 3 – Recherche full‑text et requêtes DSL  
**Objectif** : Formuler et optimiser des requêtes DSL capables de récupérer les 10 premiers résultats pertinents avec un score > 0,7 pour un jeu de requêtes donné.  

**Notions couvertes**  
- Query DSL : `match`, `multi_match`, `bool`, `function_score`.  
- Analyse du score : TF‑IDF, BM25 (paramètres `k1`, `b`).  
- Highlighting, pagination (`from`/`size`) et tri (`sort`).  
- Profilage de requêtes (`_profile`) et ajustement des analyzers.  

---

## Module 4 – Recherche vectorielle et IA intégrée  
**Objectif** : Implémenter une recherche hybride (texte + vecteur) en utilisant le champ `dense_vector` et le plugin k‑NN, et obtenir un rappel ≥ 0,8 sur un benchmark de similarité sémantique.  

**Notions couvertes**  
- Génération de vecteurs d’embeddings (BERT, Sentence‑Transformers)

---

## Module 1 — contenu

## 1. Architecture distribuée d’Elasticsearch 8.x  

| Rôle du nœud | Fonction principale | Exemple de rôle dans un cluster 3‑nœuds |
|--------------|---------------------|------------------------------------------|
| **master‑eligible** | Élection du maître, coordination du cluster, mise à jour du state metadata. | 3 nœuds master‑eligible, aucun nœud dédié n’est obligatoire, mais on recommande **≥ 2** master‑eligible pour le quorum. |
| **data** | Stockage des shards primaires et répliques, exécution des requêtes de recherche et d’agrégation. | Tous les nœuds peuvent être data + master‑eligible (configuration par défaut). |
| **coordinating** | Réception des requêtes client, routage vers les nœuds data, agrégation des réponses. | Un nœud dédié « coordinating » (sans data) réduit la charge CPU sur les nœuds data. |
| **ingest** | Exécution des pipelines d’ingestion (processors, enrich). | On active le rôle `ingest` sur chaque nœud ou sur un nœud dédié. |

*Le rôle d’un nœud est déclaré via `node.roles` dans le fichier `elasticsearch.yml`. Si la clé est absente, le nœud possède tous les rôles.*  

### 1.1 Quorum et master‑eligible nodes  

- **Quorum** = `⌊(N/2)⌋ + 1` où `N` = nombre de master‑eligible.  
- Dans un cluster 3‑master‑eligible, le quorum est 2. Si un nœud master‑eligible tombe, le cluster reste opérationnel tant que les deux restants élisent un nouveau maître.  
- Le paramètre `discovery.zen.minimum_master_nodes` (déprécié depuis 7.0) n’est plus utilisé ; la logique de quorum est intégrée dans le module de découverte.  

### 1.2 Allocation de shards  

- **Primary shards** : définis à la création de l’index (`number_of_shards`).  
- **Replica shards** : définis via `number_of_replicas`. Chaque réplica est allouée sur un nœud différent du primaire tant que la contrainte `cluster.routing.allocation.same_shard.host` (défaut = false) le permet.  
- La répartition est gérée par le **allocation decider** qui prend en compte la capacité disque (`cluster.routing.allocation.disk.watermark.low` = 85 %, `high` = 90 %).  

---

## 2. Installation d’un cluster 3‑nœuds (local)  

### 2.1 Prérequis système  

| Élément | Valeur minimale |
|---------|-----------------|
| RAM | 4 GiB par nœud (heap ≤ 50 % de la RAM, max = 32 GiB) |
| CPU | 2 cœurs |
| OS | Linux (Ubuntu 20.04+, CentOS 7+, Debian 10+) |
| Ports | 9200 (HTTP), 9300 (transport) ouverts entre les nœuds |

### 2.2 Installation via packages DEB (Ubuntu/Debian)  

```bash
# 1. Importer la clé publique d’Elastic
wget -qO - https://artifacts.elastic.co/GPG-KEY-elasticsearch | sudo apt-key add -

# 2. Ajouter le repository
echo "deb https://artifacts.elastic.co/packages/8.x/apt stable main" | sudo tee /etc/apt/sources.list.d/elastic-8.x.list

# 3. Installer Elasticsearch
sudo apt-get update && sudo apt-get install elasticsearch

# 4. Démarrer le service
sudo systemctl enable elasticsearch --now
```

### 2.3 Configuration de chaque nœud  

`/etc/elasticsearch/elasticsearch.yml` (exemple nœud 1) :

```yaml
cluster.name: demo-cluster
node.name: node-1
node.roles: [master, data, ingest]   # tous les rôles
network.host: 10.0.0.1               # IP de l’interface réseau interne
http.port: 9200
transport.port: 9300

# Découverte unicast (Zen2)
discovery.seed_hosts: ["10.0.0.1", "10.0.0.2", "10.0.0.3"]
cluster.initial_master_nodes: ["node-1", "node-2", "node-3"]   # uniquement lors du premier démarrage
```

Copier le même fichier sur les nœuds 2 et 3 en adaptant :

- `node.name` → `node-2` / `node-3`
- `network.host` → `10.0.0.2` / `10.0.0.3`

**Important** : `cluster.initial_master_nodes` ne doit **plus** être présent après le premier master élu, sinon le cluster refuse de démarrer.  

### 2.4 Installation via Docker (alternative)  

```bash
docker network create esnet
for i in 1 2 3; do
  docker run -d --name es-node-$i \
    --net esnet \
    -p 920$i:9200 -p 930$i:9300 \
    -e "node.name=es-node-$i" \
    -e "cluster.name=demo-cluster" \
    -e "discovery.seed_hosts=es-node-1,es-node-2,es-node-3" \
    -e "cluster.initial_master_nodes=es-node-1,es-node-2,es-node-3" \
    -e "node.roles=master,data,ingest

---

## Module 2 — contenu

## 2.1 Modélisation des données – principes de base  

| Concept | Règle vérifiable | Impact sur le cluster |
|---------|------------------|-----------------------|
| **Champ `keyword`** | Valeur stockée telle‑quelle, non analysée. Utilisé pour les agrégations, les filtres exacts et les tris. | Pas de tokenisation → faible consommation de mémoire, mais chaque valeur unique crée un terme dans le dictionnaire. |
| **Champ `text`** | Analyseur appliqué (standard, whitespace, ICU, …). Produit un **inverted index** de tokens. | Permet la recherche full‑text, mais chaque token occupe de la RAM et du disque. |
| **Champ `date`** | Format ISO 8601 ou epoch ms accepté. Stocké en UTC. | Les requêtes de plage (`range`) sont rapides grâce à la structure de doc‑values. |
| **Champ `numeric`** (`long`, `double`, …) | Stocké sous forme de doc‑values. | Nécessaire pour le tri, les agrégations, les scripts. |
| **Champ `dense_vector`** | Nécessite le paramètre `dims` (ex. `dims: 768`). Stocké en **doc‑values** uniquement, non analysable. | Utilisé par le plugin k‑NN ou les scripts Painless. Consomme `dims * 4 bytes` par document. |
| **Objet `nested`** | Chaque sous‑document devient un **pseudo‑document** avec son propre `_id`. | Permet des requêtes **join** précises (`nested query`). Consomme plus de disque que `object`. |
| **Objet `object`** | Stocké en **flattened** (dot‑notation). | Plus compact, mais les requêtes de type “match sur un champ de l’objet” sont limitées aux filtres exacts. |

> **Règle d’or** : ne créez jamais de champ `text` et `keyword` avec le même nom. Utilisez le pattern `my_field.keyword` (multi‑field) pour garder les deux usages.

---

## 2.2 Mapping – conception d’un mapping complet  

```json
PUT /articles_v1
{
  "settings": {
    "number_of_shards": 3,
    "number_of_replicas": 1,
    "refresh_interval": "30s",          // on diminue la charge d’indexation
    "index.max_result_window": 10000    // limite de pagination
  },
  "mappings": {
    "properties": {
      "title": {
        "type": "text",
        "analyzer": "standard",
        "fields": {
          "keyword": { "type": "keyword", "ignore_above": 256 }
        }
      },
      "body": {
        "type": "text",
        "analyzer": "english"
      },
      "tags": {
        "type": "keyword"
      },
      "published_at": {
        "type": "date"
      },
      "author": {
        "type": "nested",                 // on veut pouvoir filtrer sur le pays de l’auteur
        "properties": {
          "name":   { "type": "text", "fields": { "keyword": { "type": "keyword" } } },
          "country":{ "type": "keyword" }
        }
      },
      "embedding": {
        "type": "dense_vector",
        "dims": 768,
        "index": true,                    // requis pour le plugin k‑NN
        "similarity": "cosine"
      }
    }
  }
}
```

*Commentaires*  

* `refresh_interval` à 30 s réduit le nombre d’appels de **refresh** pendant le bulk.  
* `ignore_above` évite que des chaînes très longues remplissent le dictionnaire `keyword`.  
* Le champ `author` est `nested` pour permettre des filtres combinés (`author.country:FR AND author.name:"John"`).  
* `dense_vector` doit être déclaré **indexable** (`"index": true`) pour que le plugin k‑NN crée un index de vecteurs.  

---

## 2.3 Templates d’index, rollover & ILM  

### 2.3.1 Template d’index (JSON)  

```json
PUT _index_template/articles_template
{
  "index_patterns": ["articles-*"],
  "template": {
    "settings": {
      "number_of_shards": 1,
      "number_of_replicas": 1,
      "refresh_interval": "30s",
      "lifecycle.name": "articles_policy",
      "lifecycle.rollover_alias": "articles"
    },
    "mappings": {
      "properties": {
        "title": { "type": "text", "fields": { "keyword": { "type": "keyword" } } },
        "body":  { "type": "text", "analyzer": "english" },
        "tags":  { "type": "keyword" },
        "published_at": { "type": "date" },
        "author": {
          "type": "nested",
          "properties": {
            "name":    { "type": "text", "fields": { "keyword": { "type": "keyword" } } },
            "country": { "type": "keyword" }
          }

---

## Module 3 — contenu

## 3.1 Requêtes DSL de base  

| Requête | Usage | Exemple minimal (`curl`) |
|---------|-------|--------------------------|
| `match` | Recherche full‑text sur un champ `text` avec l’analyzer du mapping. | `curl -XGET 'localhost:9200/articles/_search' -H 'Content-Type: application/json' -d'{ "query": { "match": { "title": "intelligence artificielle" } } }'` |
| `multi_match` | Même chose sur plusieurs champs, avec contrôle du type (`best_fields`, `most_fields`, `cross_fields`). | `... "query": { "multi_match": { "query": "deep learning", "fields": ["title^2","abstract"], "type": "best_fields" } }` |
| `bool` | Combinaison logique (`must`, `should`, `must_not`, `filter`). | `... "query": { "bool": { "must": [{ "match": { "title": "robot" } }], "filter": [{ "range": { "publish_date": { "gte": "2022-01-01" } } }] } }` |
| `function_score` | Modifie le score en fonction de fonctions (field value factor, decay, script). | `... "query": { "function_score": { "query": { "match": { "title": "NLP" } }, "field_value_factor": { "field": "popularity", "factor": 0.1, "modifier": "log1p" }, "boost_mode": "multiply" } }` |

### 3.1.1 Structure d’une requête complète  

```json
{
  "size": 10,                     // nombre de hits retournés
  "from": 0,                      // offset pour la pagination
  "query": { … },                 // le DSL (match, bool, etc.)
  "sort": [                       // tri secondaire (ex. par date)
    { "publish_date": { "order": "desc" } }
  ],
  "highlight": {                 // mise en évidence des fragments
    "fields": { "title": {} }
  }
}
```

## 3.2 Analyse du score  

* Elasticsearch utilise BM25 (par défaut) depuis la version 5.0.  
* Formule :  

\[
\text{score}(q,d) = \sum_{t \in q} IDF(t) \cdot \frac{f(t,d) \cdot (k_1 + 1)}{f(t,d) + k_1 \cdot (1 - b + b \cdot \frac{|d|}{avgdl})}
\]

* `k1` (saturation) : 1.2 ≤ k1 ≤ 2.0 (valeur par défaut = 1.2).  
* `b` (normalisation) : 0 ≤ b ≤ 1 (valeur par défaut = 0.75).  

### 3.2.1 Modifications via le paramètre `similarity`  

```json
PUT articles/_settings
{
  "index": {
    "similarity": {
      "my_bm25": {
        "type": "BM25",
        "k1": 1.5,
        "b": 0.6
      }
    }
  }
}
```

Puis associer le `similarity` dans le mapping du champ :

```json
PUT articles/_mapping
{
  "properties": {
    "title": {
      "type": "text",
      "similarity": "my_bm25"
    }
  }
}
```

## 3.3 Highlighting, pagination & tri  

* **Highlighting** : le fragment retourné dépend de l’analyzer. Si l’analyzer du champ supprime les stop‑words, les mots mis en évidence peuvent être « déconnectés ». Utiliser `highlight_query` pour forcer le même analyseur que la requête.  
* **Pagination profonde** : `from + size` > 10 000 déclenche le **deep pagination** qui charge tous les hits en mémoire. Solutions : `search_after` (tri stable) ou `scroll`.  
* **Tri** : le champ doit être **doc‑values** (true par défaut pour les champs `keyword`, `date`, `numeric`). Un champ `text` ne peut pas être trié directement.  

### Exemple de pagination stable avec `search_after`

```json
POST articles/_search
{
  "size": 5,
  "sort": [
    { "publish_date": "desc" },
    { "_id": "asc" }
  ],
  "search_after": ["2023-05-10T12:34:56Z", "AV7kX3YB8c9"],
  "query": { "match_all": {} }
}
```

## 3.4 Profilage de requêtes (`_profile`)  

```bash
curl -XGET 'localhost:9200/articles/_search?profile=true' -H 'Content-Type: application/json' -d'
{
  "query": {
    "bool": {
      "must": [
        { "match": { "title": "machine learning" } },
        { "range": { "publish_date": { "gte": "2021-01-01" } } }
      ]
    }
  },
  "size": 10
}'
```

Le retour contient :

* `query_breakdown` – temps passé dans chaque phase (`rewrite`, `match`, `score`).
* `collector` – temps d’agrégation des hits.
* `shards`

---

## Module 4 — contenu

## 1. Concepts clés  

| Concept | Description vérifiable |
|--------|-----------------------|
| **Champ `dense_vector`** | Stocke un tableau de nombres flottants (float) de dimension fixe. Disponible depuis Elasticsearch 7.3. |
| **Plugin k‑NN** | Implémentation native du moteur de recherche vectorielle (FAISS) fournie par Elastic 8.x (module `knn`). Nécessite l’installation du package `elasticsearch-knn`. |
| **Hybrid search** | Combinaison d’une requête texte (`match`, `multi_match`) et d’une requête k‑NN (`knn`) dans un même `bool`‑`must`. Le score final est la somme pondérée des deux sous‑scores. |
| **Embedding** | Vecteur dense généré par un modèle de langage (ex. `sentence‑transformers/all-MiniLM-L6-v2`). La dimension du modèle doit correspondre à celle déclarée dans le mapping. |
| **Recall** | Ratio du nombre de documents pertinents récupérés sur le nombre total de pertinents dans le jeu de référence. Calculé sur le top‑k (ex. k = 10). |

---

## 2. Prérequis techniques  

| Élément | Version minimale | Commande d’installation |
|---------|-------------------|--------------------------|
| Elasticsearch | 8.7.0 | `docker pull docker.elastic.co/elasticsearch/elasticsearch:8.7.0` |
| Plugin k‑NN | 8.7.0 | `bin/elasticsearch-plugin install https://artifacts.elastic.co/downloads/elasticsearch-plugins/opendistro-knn/knn-8.7.0.zip` |
| Python | 3.9+ | `python -m venv venv && source venv/bin/activate` |
| Bibliothèques Python | `elasticsearch==8.12.0`, `sentence-transformers==2.2.2` | `pip install elasticsearch sentence-transformers` |

> **Vérification** : après le redémarrage du nœud, l’API `GET /_plugins` doit renvoyer `knn`.  

---

## 3. Mapping et création de l’index  

```json
PUT /semantic_articles
{
  "settings": {
    "index": {
      "knn": true,                     // active le moteur k‑NN
      "knn.algo_param.ef_search": 512, // paramètre de précision (plus grand = meilleur recall)
      "number_of_shards": 3,
      "number_of_replicas": 1
    }
  },
  "mappings": {
    "properties": {
      "title": {
        "type": "text",
        "analyzer": "standard"
      },
      "body": {
        "type": "text",
        "analyzer": "standard"
      },
      "embedding": {
        "type": "dense_vector",
        "dims": 384,                     // dimension du modèle MiniLM‑L6‑v2
        "index": true,                  // rend le champ searchable via k‑NN
        "similarity": "cosine"          // métrique de distance
      },
      "category": {
        "type": "keyword"
      },
      "published_at": {
        "type": "date"
      }
    }
  }
}
```

*Points de validation*  

* `knn` doit être `true` au niveau `index`.  
* `dense_vector.dims` doit exactement correspondre à la dimension du modèle d’embeddings.  
* Le champ `embedding` doit être déclaré `index: true` pour que le plugin k‑NN crée un index inversé dédié.  

---

## 4. Génération d’embeddings (Python)  

```python
# -*- coding: utf-8 -*-
"""
Génération d'embeddings avec Sentence‑Transformers.
Le modèle renvoie des vecteurs de dimension 384 (MiniLM‑L6‑v2).
"""
from sentence_transformers import SentenceTransformer
import json

model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

def embed_document(doc: dict) -> dict:
    """
    Ajoute le champ `embedding` à un document JSON.
    Le texte concaténé est `title + " " + body`.
    """
    text = f"{doc.get('title','')} {doc.get('body','')}"
    vec = model.encode(text, normalize_embeddings=True)  # normalisation L2 → cosine = dot
    doc["embedding"] = vec.tolist()                     # Elasticsearch attend une liste Python
    return doc

# Exemple de chargement d’un fichier source
with open("sample_corpus.json", "r", encoding="utf-8") as f:
    corpus = json.load(f)   # liste de dicts contenant title, body, category, published_at

# Ajout des embeddings (batch de 64 pour limiter la RAM)
batch = []
for i, raw in enumerate(corpus, 1):
    batch

---

## Module 5 — contenu

## Module 5 – Sécurité, monitoring & optimisation opérationnelle  

### 1. Sécurisation du cluster  

| Élément | Action | Commande / API | Vérifiable |
|--------|--------|----------------|------------|
| **TLS** (transport & HTTP) | Générer un certificat auto‑signé ou importer un CA interne. | `bin/elasticsearch-certutil ca` → `bin/elasticsearch-certutil cert --ca elastic-stack-ca.p12` | Le fichier `elastic-certificates.p12` apparaît dans le répertoire `config/`. |
| **Activation du TLS** | Ajouter les chemins dans `elasticsearch.yml`. | ```yaml
xpack.security.enabled: true
xpack.security.transport.ssl.enabled: true
xpack.security.transport.ssl.verification_mode: certificate
xpack.security.transport.ssl.keystore.path: elastic-certificates.p12
xpack.security.transport.ssl.truststore.path: elastic-certificates.p12
xpack.security.http.ssl.enabled: true
xpack.security.http.ssl.keystore.path: elastic-certificates.p12
``` | `GET https://<node>:9200/_cluster/settings?include_defaults=true` renvoie `xpack.security.http.ssl.enabled: true`. |
| **Authentification native** | Créer un utilisateur admin. | ```bash
curl -u elastic:changeme -X POST "https://localhost:9200/_security/user/admin" \
 -H "Content-Type: application/json" -d '{
   "password" : "StrongP@ssw0rd!",
   "roles"    : [ "superuser" ],
   "full_name": "Cluster Administrator"
 }'
``` | `GET https://localhost:9200/_security/user/admin` renvoie le JSON créé. |
| **Roles basés sur les index** | Restreindre l’accès à l’index `sales`. | ```bash
curl -u elastic:StrongP@ssw0rd! -X POST "https://localhost:9200/_security/role/sales_reader" \
 -H "Content-Type: application/json" -d '{
   "indices": [
     {
       "names": [ "sales*" ],
       "privileges": [ "read", "view_index_metadata" ]
     }
   ]
 }'
``` | `GET https://localhost:9200/_security/role/sales_reader` montre les privilèges. |
| **API key** (usage programmatique) | Générer une clé liée au rôle `sales_reader`. | ```bash
curl -u elastic:StrongP@ssw0rd! -X POST "https://localhost:9200/_security/api_key" \
 -H "Content-Type: application/json" -d '{
   "name": "sales_reader_key",
   "role_descriptors": {
     "sales_reader": {
       "indices": [
         {
           "names": [ "sales*" ],
           "privileges": [ "read" ]
         }
       ]
     }
   }
 }'
``` | La réponse contient `"id"` et `"api_key"` utilisables dans `Authorization: ApiKey <id>:<api_key>`. |

#### Pièges concrets
* **Mot de passe par défaut** – ne jamais laisser `elastic:changeme` en production ; les API de sécurité sont désactivées tant que le mot de passe n’est changé (`xpack.security.enabled` reste `false` sinon).  
* **TLS incomplet** – activer le TLS uniquement sur le transport couche ne protège pas l’API HTTP; les deux doivent être activés simultanément.  
* **Autorisation trop large** – un rôle `all_index` avec `privileges: ["all"]` sur `*` annule les bénéfices du RBAC.  

---

### 2. Monitoring du cluster  

#### 2.1. Métriques de base via les APIs  

| API | Exemple | Description |
|-----|---------|-------------|
| `_cluster/health` | `curl -s -u elastic:pwd https://localhost:9200/_cluster/health?pretty` | État global (`green`, `yellow`, `red`). |
| `_cat/nodes?v&h=ip,heap.percent,ram.percent,cpu,load_1m,node.role` | `curl -s -u elastic:pwd https://localhost:9200/_