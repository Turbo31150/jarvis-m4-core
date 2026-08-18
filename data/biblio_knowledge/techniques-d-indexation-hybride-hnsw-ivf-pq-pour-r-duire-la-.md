# Techniques d'indexation hybride (HNSW + IVF-PQ) pour réduire la latence de recherche en temps réel sur des datasets massifs

*Domaine : Vectors & Embeddings*

# Indexation Hybride HNSW + IVF-PQ : Réduire la Latence sur des Datasets Massifs

## Contexte
Dans les architectures de type **JARVIS** ou pour le déploiement d'**LLMs locaux**, la recherche vectorielle (Similarité Cosinus/Euclidienne) est souvent le goulot d'étranglement. Sur des datasets dépassant 10 millions d'embeddings, une indexation standard comme HNSW seule peut consommer trop de mémoire RAM ou nécessiter un temps de construction prohibitif, tandis qu'une IVF (Inverted File Index) pure souffre de "faux voisins" en cas de mauvaise partitionnement.

La combinaison **HNSW + IVF-PQ** (Product Quantization) offre une approche hybride : l'IVF agit comme un filtre rapide pour réduire l'espace de recherche, et HNSW assure la précision finale au sein des partitions. Cette synergie est cruciale pour les applications temps réel exigeant une latence < 50ms sur du matériel serveur standard (CPU/RAM limités).

## Points Clés Techniques

*   **Architecture en Cascade** : Le système divise le dataset en clusters (IVF), quantifie les vecteurs (PQ) pour compresser la distance, puis utilise HNSW uniquement dans les partitions pertinentes.
*   **Réduction de l'Espace de Recherche** : Au lieu de parcourir tout le graphe HNSW ($O(N)$ ou $O(\log N)$ selon la configuration), on ne cherche que dans les *n-listes* (partitions) adjacentes au vecteur de requête.
*   **Compression Agressive (PQ)** : La Product Quantization réduit la taille des embeddings (ex: 768 dim -> 128 float32 ou moins), permettant de charger l'index complet en RAM même sur des datasets de plusieurs Go, réduisant ainsi les accès disque.
*   **Paramétrage Critique** :
    *   `nlist` (IVF) : Nombre de partitions (ex: 100-500). Trop bas = faux voisins ; trop haut = surcoût de calcul pour HNSW.
    *   `m` (HNSW) : Degré du graphe. Un `m` plus élevé améliore la précision mais augmente la latence de construction et la mémoire.
    *   `quantization`: Utilisation de `SCANN` ou `PQ` pour compresser les vecteurs avant l'indexation HNSW.

## Exemple Concret : Déploiement Local avec FAISS

Pour une application Python utilisant **FAISS** (bibliothèque standard de référence) sur un serveur Linux avec 64 Go de RAM et un dataset de 50M embeddings :


