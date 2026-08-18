# Patterns d'ingestion 'Change Data Capture' (CDC) asynchrones pour les pipelines de données en temps réel

*Domaine : Data Engineering*

# CDC Asynchrone : Architecture et Mise en Œuvre pour le Temps Réel

## Contexte
Dans les architectures de données modernes (Data Lakehouse ou Data Mesh), la synchronisation asynchrone via le **Change Data Capture (CDC)** est le standard pour ingérer des modifications depuis des bases de données transactionnelles (OLTP) vers des entrepôts analytiques (OLAP). Contrairement aux snapshots complets, le CDC capture uniquement les événements de modification (INSERT, UPDATE, DELETE), réduisant considérablement la charge réseau et le coût de stockage.

Cette approche est critique pour les pipelines en temps réel où la latence doit être inférieure à quelques secondes, permettant une visualisation quasi instantanée des données métier sans surcharger la base source.

## Points Clés Techniques

*   **Mécanisme de Détection** : Le CDC repose généralement sur le journal des transactions (WAL - Write Ahead Log) ou les logs binaires du moteur de base de données (ex: `pg_wal` pour PostgreSQL, Redo Logs pour Oracle). L'outil d'ingestion lit ces logs séquentielles.
*   **Architecture Event-Driven** : Le flux suit le modèle *Source -> Log Broker -> Consommateur*. Les logs sont souvent publiés sur un bus de messages (Kafka, Pulsar) avant traitement, découplant la lecture des écritures.
*   **Gestion du Décalage (Lag)** : La latence entre l'écriture dans la source et sa disponibilité en destination est minimale mais jamais nulle. Elle dépend de la vitesse d'évacuation des logs et de la capacité de traitement du consommateur.
*   **Support des Transactions ACID** : Les outils modernes (Debezium, Debezium Connector) garantissent l'atomicité : si une transaction échoue dans la source, aucune modification n'est propagée vers le lac de données, préservant la cohérence.
*   **Traitement des Suppressions (DELETE)** : Le CDC capture les événements de suppression. La reconstruction du modèle cible nécessite souvent un mécanisme de "Squash" ou une table de versioning pour gérer l'historique si nécessaire.

## Exemple Concret : Pipeline Kafka + Debezium

Imaginez une application bancaire enregistrant des virements en temps réel sur une base **PostgreSQL**.

1.  **Capture** : Un agent **Debezium** s'attache au flux `pg_wal` de PostgreSQL. Dès qu'un utilisateur effectue un virement, la transaction est écrite dans le WAL.
2.  **Buffering** : Debezium lit les entrées du WAL et génère des événements JSON contenant l'ID transactionnel, le type d'opération (`INSERT`, `UPDATE`, `DELETE`) et les champs modifiés (différence avant/ap
