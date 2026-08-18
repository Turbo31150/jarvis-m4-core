# Gestion des transactions ACID distribuées dans les bases de données vectorielles (ex: ChromaDB, Milvus) pour la cohérence des pipelines

*Domaine : Data Engineering*

# Gestion des transactions ACID distribuées dans les bases de données vectorielles

## Contexte
Dans l'écosystème **JARVIS** (systèmes d'exploitation Linux, LLM locaux et automatisation), la base de données vectorielle est le cœur du moteur de recherche sémantique. Des outils comme **ChromaDB** ou **Milvus** sont souvent déployés en mode "standalone" pour leur simplicité et leurs performances en lecture/écriture rapide. Cependant, une contrainte fondamentale persiste : la majorité de ces moteurs ne garantissent pas nativement les propriétés **ACID** (Atomicité, Cohérence, Isolation, Durabilité) à l'échelle distribuée ou même locale dans le sens strict des bases relationnelles traditionnelles.

Pour un pipeline de données robuste, comprendre cette limitation est crucial pour éviter la corruption de l'index et assurer la cohérence entre l'ingestion de documents et les requêtes RAG (Retrieval-Augmented Generation).

## Points Clés

*   **Modèle CAP vs ACID** : Les bases vectorielles privilégient généralement la disponibilité (A) et la tolérance au partitionnement (P) plutôt que la cohérence forte (C) stricte. Elles optimisent le compromis pour la latence de recherche, ce qui rend les transactions distribuées complexes à implémenter nativement.
*   **Atomicité limitée** : L'ajout d'un vecteur et la mise à jour de son métadonnées sont souvent des opérations atomiques internes, mais une transaction complexe impliquant plusieurs collections ou nœuds peut échouer partiellement sans rollback automatique garanti par le protocole ACID complet.
*   **Cohérence conditionnelle** : La plupart des implémentations utilisent des verrous optimistes ou des horodatages (timestamps) pour gérer les conflits, plutôt que des verrous exclusifs bloquants typiques des transactions SQL. Cela signifie qu'une lecture peut voir un état intermédiaire si la synchronisation n'est pas explicite.
*   **Durabilité asynchrone** : L'écriture est souvent journalisée dans un buffer avant d'être persistée sur disque pour éviter les goulets d'étranglement. En cas de crash immédiat, des écritures en cours peuvent être perdues si le WAL (Write-Ahead Log) n'est pas correctement configuré ou vérifié.
*   **Isolation faible** : Dans un déploiement multi-nœuds (ex: Milvus avec plusieurs shards), les lectures ne garantissent pas toujours une vue isolée du moment de la transaction, mais plutôt une cohérence éventuelle (eventual consistency).

## Exemple Concret : Pipeline d'Ingestion JARVIS

Imaginez un pipeline Linux où un script Python ingère des PDF dans **ChromaDB** via l
