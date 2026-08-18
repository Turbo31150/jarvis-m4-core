# Implémentation de stratégies de 'Re-join' automatique pour les nœuds sortis du cluster suite à une panne réseau transitoire (Split-brain recovery).

*Domaine : Cluster - Recovery & Resilience*

# Stratégies de Re-join Automatique : Récupération après Split-Brain Réseau

## Contexte
Dans les architectures de cluster (Kubernetes, Pacemaker, ou clusters LLM locaux), une panne réseau transitoire peut isoler un nœud du reste du groupe. Si ce nœud conserve ses données locales mais perd la connectivité avec le quorum, il risque de déclencher un état *split-brain* (le cluster se divise en deux groupes décisionnels incompatibles). La stratégie de **Re-join automatique** vise à permettre au nœud isolé de détecter sa réintégration, valider l'état du cluster majoritaire et se synchroniser sans intervention manuelle ni perte de données.

## Points Clés

*   **Détection de la Réintégration (Heartbeat)** : Le mécanisme repose sur la restauration des cœurs (heartbeats) entre le nœud isolé et le quorum. Une fois la latence réseau réduite en dessous du seuil de tolérance, le nœud doit passer d'un état "isolé" à "connecté".
*   **Gestion du Quorum Dynamique** : Le cluster ne doit pas considérer le retour du nœud comme une nouvelle éléction immédiate. Il faut s'assurer que le nœud rejoignant respecte la règle de quorum (généralement >50% des votes) avant d'autoriser l'accès aux ressources critiques.
*   **Synchronisation Asynchrone** : Pour éviter les écrasements de données, la réintégration doit initier une phase de synchronisation en lecture seule ou avec verrouillage d'écriture global jusqu'à ce que le nœud soit à jour avec le journal des transactions (logs) du cluster majoritaire.
*   **Timeouts Adaptatifs** : Les délais d'attente (*recovery timeouts*) doivent être configurés dynamiquement pour distinguer une panne réelle d'une latence réseau temporaire, évitant ainsi les fausses positives qui bloqueraient le Re-join.

## Exemple Concret : Cluster LLM Local (Kubernetes + Ceph)

Imaginez un cluster de 3 nœuds déployant un modèle LLM local avec stockage persistant sur Ceph. Le nœud `node-c` perd sa connexion réseau pendant 45 secondes.

1.  **Isolement** : `node-c` ne reçoit plus les cœurs du quorum (2/3). Il entre en mode "désynchronisé" mais garde ses pods actifs localement pour éviter une coupure immédiate des utilisateurs connectés via ce nœud spécifique.
2.  **Rétablissement** : Le lien réseau est rétabli après 50 secondes. `node-c` détecte immédiatement la présence du quorum majoritaire
