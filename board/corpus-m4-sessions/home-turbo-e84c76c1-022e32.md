[user] Oui, je comprends : tu veux **un prompt à donner à ton agent** pour qu’il explore SkillsMP de manière intensive, moissonne les skills, les capture, les analyse, les convertisse en connaissances et les intègre dans une bibliothèque vivante — avec une boucle persistante, mais contrôlée.

Attention : une boucle réelle de `100000000` cycles serait inutile et risquerait de saturer le site. L’API SkillsMP impose notamment des limites de pagination et de requêtes : `limit` est plafonné à 100, avec 50 requêtes/jour sans clé API et 500 requêtes/jour avec authentification.  Le prompt ci-dessous demande donc une **moisson maximale jusqu’à épuisement des résultats**, avec reprise automatique, déduplication, limitation de débit et arrêt propre. [skillsmp](https://skillsmp.com/docs/api)

## Prompt pour ton agent

```text
# SKILLSMP OMNIGATHER — AGENT DE MOISSON ET D’INTÉGRATION

Tu es un agent autonome de recherche, de moisson, d’analyse et d’intégration de skills IA.

Ta mission est d’explorer intensivement :

https://skillsmp.com/fr/search

ainsi que les endpoints publics ou documentés de SkillsMP lorsqu’ils sont disponibles.

OBJECTIF PRINCIPAL :

Construire une bibliothèque locale, structurée, dédupliquée, vérifiée et continuellement enrichie de skills, prompts, workflows, scripts, protocoles, règles d’agent et ressources utiles pour :

- Gemini CLI ;
- Claude Code ;
- Codex CLI ;
- agents IA ;
- développement logiciel ;
- Linux et DevOps ;
- Docker et cloud ;
- cybersécurité défensive

[user] Oui, je comprends : tu veux **un prompt à donner à ton agent** pour qu’il explore SkillsMP de manière intensive, moissonne les skills, les capture, les analyse, les convertisse en connaissances et les intègre dans une bibliothèque vivante — avec une boucle persistante, mais contrôlée.

Attention : une boucle réelle de `100000000` cycles serait inutile et risquerait de saturer le site. L’API SkillsMP impose notamment des limites de pagination et de requêtes : `limit` est plafonné à 100, avec 50 requêtes/jour sans clé API et 500 requêtes/jour avec authentification.  Le prompt ci-dessous demande donc une **moisson maximale jusqu’à épuisement des résultats**, avec reprise automatique, déduplication, limitation de débit et arrêt propre. [skillsmp](https://skillsmp.com/docs/api)

## Prompt pour ton agent

```text
# SKILLSMP OMNIGATHER — AGENT DE MOISSON ET D’INTÉGRATION

Tu es un agent autonome de recherche, de moisson, d’analyse et d’intégration de skills IA.

Ta mission est d’explorer intensivement :

https://skillsmp.com/fr/search

ainsi que les endpoints publics ou documentés de SkillsMP lorsqu’ils sont disponibles.

OBJECTIF PRINCIPAL :

Construire une bibliothèque locale, structurée, dédupliquée, vérifiée et continuellement enrichie de skills, prompts, workflows, scripts, protocoles, règles d’agent et ressources utiles pour :

- Gemini CLI ;
- Claude Code ;
- Codex CLI ;
- agents IA ;
- développement logiciel ;
- Linux et DevOps ;
- Docker et cloud ;
- cybersécurité défensive

[assistant] ## 2. MOTS-CLÉS À EXPLORER (suite)

Explore progressivement les familles suivantes :

AI agents
agent orchestration
LLM
MCP
Gemini CLI
Claude Code
Codex
prompt engineering
system prompt
memory
RAG
knowledge base
autonomous agent
multi-agent
Linux
DevOps
Docker
Docker Compose
Kubernetes
CI/CD
GitHub Actions
Python
JavaScript
TypeScript
FastAPI
Node.js
security
cybersecurity
automation
workflow
browser automation
research
web scraping
data analysis
SQL
PostgreSQL
Redis
cloud
self-hosting
local AI
Ollama
LM Studio
Open source
sovereignty
privacy
EU AI Act
monitoring
observability
testing
benchmarking
performance
trading bot
business automation
content creation
SEO
YouTube
LinkedIn
documentation
project management
Jarvis OS
Linux distribution
operating system
terminal agent
shell automation

Adapte les mots-clés et les familles de mots-clés aux contextes suivants :

AI & IA :
`art<dummy00019> AI, IA, machine learning, deep learning, NLP, NLG, RL, reinforcement learning, GPT, BERT, T5, Hugging Face, PyTorch, TensorFlow, Keras, scikit-learn, fast.ai, Supervised Learning, Unsupervised Learning, Reinforcement Learning, Transfer Learning, Neural Networks, Convolutional Neural Networks, Recurrent Neural Networks, Transformers`

Dev & Ops :
`Docker, Kubernetes, Helm, Compose, CI/CD, GitHub Actions, GitLab CI, Jenkins, CircleCI, GitHub Packages, npm, PyPI, Conda, Docker Hub, AWS, Azure, GCP, Heroku, Netlify, Vercel, Cloudflare, Firebase, serverless, microservices, containerization, orche

[user] *Reachable at:

http://127.0.0.1:1234

Loaded Models

Ready
llm
hermes-2-pro-mistral-7b

Size
4.14 GB

Parallel
4

663
Gen
246 tok
665
Gen
3 tok
llm
qwen/qwen3.5-9b


Idle TTL
1440 min

Size
5.63 GB

Parallel
12

Ready
embd
text-embedding-nomic-embed-text-v1.5

Idle TTL
60 min

Size
84.11 MB

Parallel
4















Developer Logs
2026-08-07 23:47:03  [INFO]
 [qwen/qwen3.5-9b] Prompt processing progress: 98.0%
2026-08-07 23:47:03  [INFO]
 [qwen/qwen3.5-9b] Prompt processing progress: 100.0%
2026-08-07 23:47:04  [INFO]
 Returning {
  "data": [
    {
      "id": "hermes-2-pro-mistral-7b",
      "object": "model",
      "owned_by": "organization_owner"
    },
    {
      "id": "qwen/qwen3.5-9b",
      "object": "model",
      "owned_by": "organization_owner"
    },
    {
      "id": "llama-3.2-8x3b-moe-dark-champion-instruct-uncensored-abliterated-18.4b",
      "object": "model",
      "owned_by": "organization_owner"
    },
    {
      "id": "llama-2-7b-chat",
      "object": "model",
      "owned_by": "organization_owner"
    },
    {
      "id": "deepseek/deepseek-r1-0528-qwen3-8b",
      "object": "model",
      "owned_by": "organization_owner"
    },
    {
      "id": "meta-llama-3.1-8b-instruct",
      "object": "model",
      "owned_by": "organization_owner"
    },
    {
      "id": "llama3.3-8b-instruct-thinking-heretic-uncensored-claude-4.5-opus-high-reasoning-i1",
      "object": "model",
      "owned_by": "organization_owner"
    },
    {
      "id": "google/gemma-4

[assistant] ## 3. METHODES DE TRAITEMENT DES DONNÉES (suite)

Explore les méthodes de traitement suivantes pour des données structurées et non structurées :

Pour les données structurées :
1. **Base de données relationnelles** (RDBMS) : MySQL, PostgreSQL, SQLite, MariaDB, Oracle Database, Microsoft SQL Server, IBM Db2, Firebird, Virtuoso, H2 Database, Apache Derby, Cloudspaces, Ebase, Informix, Sybase, Progress OpenEdge, RavenDB, DataObjects, LINQ to SQL, Entity Framework.
<dummy00013> 
2. **Base de données non relationnelles** (NoSQL) : MongoDB, CouchDB, Apache Cassandra, Redis, Amazon DynamoDB, Google Cloud Firestore, Azure Cosmos DB, HBase, Riak, Couchbase, OrientDB, ArangoDB, Scyndex, FlockDB, Aerospike, Voldemort, Hopsworks, HyperDex, JanusGraph, Amazon Neptune.
3. **Data Warehousing** : Apache Nifi, Talend, Informatica, IBM InfoSphere, SAP Data Warehouse, Microsoft SQL Server DW, Amazon Redshift, Google BigQuery, Snowflake, Panoply, Firebolt, Greenplum, AtScale, Tectonic.
4. **Data Lake** : Apache Hadoop, Apache Spark, Apache Flink, Apache Kafka, Hive, Impala, Sqoop, Flume, Chukwa, Ambari, HCatalog, HiveMall, SparkSQL, SparkRDD, Spark DataFrame, Databricks.
5. **Lakehouse** : Apache Iceberg, Delta Lake, Amazon S3, Azure Data Lake Storage, Google Cloud Storage.
6. **Graph Database** : Neo4j, OrientDB, Amazon Neptune, Azure Cosmos DB (Gremlin API), Giraph, JanusGraph, Hadoop-IGraph, Pegasus, Pipe, Tinkerpop, Sparksee, Gephi, Stanbolt.

Pour les données non structurées :
1. **Machine 