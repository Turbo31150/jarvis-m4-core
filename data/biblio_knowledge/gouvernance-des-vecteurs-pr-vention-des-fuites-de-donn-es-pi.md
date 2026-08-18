# Gouvernance des Vecteurs : Prévention des Fuites de Données (PII) via l'Obscurcissement Dynamique dans les Indexes Vectoriels

*Domaine : Sécurité*

# Gouvernance des Vecteurs : Prévention des Fuites de Données (PII) via l'Obscurcissement Dynamique

## Contexte
Dans les architectures modernes basées sur l'IA locale (JARVIS, LLMs autonomes), la sécurité ne réside pas seulement dans le chiffrement au repos, mais dans la **gestion du contexte**. Les indexes vectoriels (ChromaDB, Qdrant, Milvus) stockent souvent des métadonnées riches contenant des informations sensibles (PII : noms, emails, adresses). Une requête de recherche standard (`vector_search`) peut exposer ces données brutes à l'utilisateur ou au modèle lui-même, créant un vecteur de fuite latéral.

L'approche traditionnelle (chiffrement statique) rend les vecteurs inutilisables pour la similarité s'ils sont chiffrés. La solution résidente est l'**Obscurcissement Dynamique** : une technique où les métadonnées sensibles sont masquées ou hachées *à la volée* lors de la construction de la requête, uniquement si nécessaire, tout en préservant la capacité du moteur vectoriel à indexer et récupérer le bon enregistrement.

## Points Clés

*   **Séparation des Couches** : Le stockage brut des vecteurs reste dans l'index, mais les métadonnées sensibles sont traitées via une couche de gouvernance externe (middleware ou application).
*   **Masquage par Contexte** : L'obscurcissement n'est pas permanent. Il s'applique conditionnellement selon le rôle de l'utilisateur (`RBAC`) et la sensibilité des données détectée dans la requête.
*   **Intégrité du Vecteur** : Le vecteur mathématique (embeddings) reste inchangé pour garantir la précision de la recherche, seule la couche sémantique (métadonnées) est altérée.
*   **Auditabilité** : Chaque accès aux métadonnées originales doit être journalisé avec un hash de l'ID du vecteur, permettant une traçabilité complète sans stocker les données brutes dans les logs.

## Exemple Concret : Implémentation avec Python & ChromaDB

Imaginez un agent JARVIS local interrogeant une base de connaissances client. Sans protection, une recherche retourne directement l'email du client. Avec obscurcissement dynamique :

```python
import chromadb
from chromadb.config import Settings

client = chromadb.Client(Settings(chroma_db_impl="duckdb+parquet"))
collection = client.get_or_create_collection("support_tickets")

# Données sensibles stockées (métadonnées)
metadata = {
    "ticket_id": 102,
    "email": "jean.dupont@entreprise.com", # PII
    "status": "open"
