# Board Multi — fusion réponses experts hétérogènes

*Domaine : board-multi*

# Board Multi : Fusion de Réponses d'Experts Hétérogènes

## Contexte
Dans les architectures **JARVIS** (Java AI Runtime Virtual Interface System) ou les déploiements **Linux** locaux avancés, le modèle "Board Multi" désigne une stratégie d'inférence où plusieurs modèles experts distincts (LLMs hétérogènes) traitent simultanément une même requête. Contrairement à l'agrégation simple de votes, cette approche fusionne les *trajectoires logiques* issues de modèles ayant des architectures, des tailles ou des spécialisations différentes (ex: un modèle dense petit pour la vitesse, un modèle MoE pour la complexité).

L'objectif est d'obtenir une réponse robuste qui combine la précision d'un expert spécialisé avec la généralité d'un autre, tout en optimisant l'utilisation des ressources GPU/CPU locales.

## Points Clés
*   **Hétérogénéité Structurale** : Le board accepte des modèles de formats variés (ex: `llama.cpp` pour le CPU/GPU léger et `vLLM` ou `TensorRT-LLM` pour l'accélération GPU). La fusion ne nécessite pas que les modèles partagent la même matrice de poids, mais qu'ils partagent un espace sémantique aligné.
*   **Mécanisme de Fusion Dynamique** : Au lieu d'une moyenne pondérée statique, le système utilise souvent une porte logique (gate) ou un agrégateur attentionnel pour pondérer les sorties en fonction de la confiance du modèle sur des segments spécifiques du texte généré.
*   **Alignement Sémantique Préalable** : Avant l'inférence en production, les experts doivent être "calibrés" sur un corpus commun (RAG partagé ou fine-tuning léger) pour éviter que le système de fusion ne choisisse arbitrairement entre deux interprétations contradictoires.
*   **Gestion des Latences Asynchrones** : Sur Linux, l'orchestrateur doit gérer les temps de réponse différents entre un modèle CPU (lent) et un modèle GPU (rapide) sans bloquer le thread principal, souvent via des file d'attente non bloquantes (`epoll` ou `io_uring`).

## Exemple Concret
Imaginez une requête technique complexe : *"Optimiser la consommation mémoire d'un kernel Linux en C"*.

1.  **Expert A (Petit modèle, ex: Phi-3-mini)** : Génère rapidement un script de test basique et identifie les fuites évidentes. Temps de réponse : 200ms.
2.  **Expert B (Grand modèle MoE, ex: Llama-3-70B quantifié)** : Analyse la complexité algorithmique du kernel et propose des optimisations
