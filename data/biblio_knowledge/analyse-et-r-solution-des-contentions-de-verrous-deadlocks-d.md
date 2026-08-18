# Analyse et résolution des contentions de verrous (deadlocks) dans les bases de données NoSQL à journalisation forte (ex: Cassandra, ScyllaDB)

*Domaine : SQL Performance Tuning*

# Gestion des Contentions dans les Bases NoSQL à Journalisation Forte : Cas Cassandra et ScyllaDB

## Contexte
Contrairement aux bases de données relationnelles (SQL) où les *deadlocks* sont gérés par le moteur via la détection de cycles, les systèmes NoSQL comme **Apache Cassandra** ou **ScyllaDB** adoptent une philosophie différente. Ils privilégient la disponibilité et la latence faible au détriment parfois de la cohérence immédiate (modèle CAP).

Dans ces architectures, il n'existe pas de mécanisme natif de "rollback automatique" lors d'une contention. Si deux transactions tentent d'écrire sur les mêmes données simultanément avec des conflits de lecture-écriture ou écriture-écriture, le système rejette la transaction avec une erreur (ex: `WriteConflictException` en Cassandra). Pour un administrateur système ou un développeur orienté performance, comprendre et résoudre ces contentions est crucial pour éviter l'accumulation de latence et les timeouts en cascade.

## Points Clés

*   **Absence de Deadlocks Classiques** : Cassandra ne détecte pas de cycles d'attente. Une contention se manifeste par un échec d'écriture immédiat si la version stockée diffère de celle fournie dans la requête (version vectorielle).
*   **Le Rôle du `TTL` et des Consistences** : L'utilisation de consistances trop élevées (`QUORUM`, `ALL`) sur des clés hotspots augmente drastiquement le risque de conflits. La stratégie consiste souvent à basculer vers `LOCAL_QUORUM` ou `ONE` pour les écritures fréquentes, en acceptant une cohérence éventuelle (eventual consistency).
*   **Gestion des Clés et Partitionnement** : Les contentions surviennent principalement lorsque plusieurs nœuds tentent d'écrire sur le même partitionneur. Une mauvaise répartition des données (hot partitions) force un seul nœud à gérer une charge disproportionnée, créant des goulots d'étranglement locaux.
*   **Stratégie de Rejet et Retry** : Cassandra rejette les écritures conflictuelles avec une erreur spécifique contenant la version actuelle de la donnée. L'application doit implémenter une logique de *retry* (re-tentative) avec backoff exponentiel pour résoudre ces conflits sans bloquer le système.
*   **ScyllaDB et l'Optimisation** : ScyllaDB, étant un fork en C++ de Cassandra, hérite de ce modèle mais offre des outils de profilage plus performants (`sysdig`, `scylla-gui`) pour identifier les hotspots en temps réel grâce à son architecture multi-threadée.

## Exemple Concret

Imaginez un service de réservation de billets où deux utilisateurs tent
