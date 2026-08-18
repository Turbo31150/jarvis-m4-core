# Kernel-Level Optimizations for LLM Inference Performance - CPU Pinning, NUMA Awareness & Memory Layout

*Domaine : LLM Local & Kernel Tuning*

# Optimisation de l'Inférence LLM Locale : Tuning au Niveau du Kernel

**Contexte:** Les grands modèles linguistiques (LLM) nécessitent des ressources significatives pour l'inférence. L'exécution sur CPU, même avec des GPU relativement modestes, peut être lente et inefficace. Cette fiche se concentre sur les optimisations au niveau du kernel qui peuvent considérablement améliorer la performance de l’inférence LLM locale, particulièrement sur des systèmes JARVIS/Linux. Ces techniques visent à réduire la latence et augmenter le débit en exploitant les capacités du CPU.

**Points Clés:**

* **CPU Pinning (Fixation de Coeurs):**
    *  L'objectif : Attacher spécifiquement un ou plusieurs cœurs CPU aux couches individuelles des LLM, réduisant ainsi la "context switch" et le mouvement des données entre les caches. Cela minimize l’impact du scheduler du noyau.
    *  Implémentation (Exemple JARVIS): Utilisation de `taskset` ou d'une solution de gestion de tâches plus avancée pour assigner précisément des cœurs à des couches spécifiques.
    *  Avantages : Diminue fortement la latence pour les modèles complexes et réduit l’overhead du multithreading.

* **NUMA Awareness (Connaissance NUMA):**
   * Comprendre le concept du NUMA (Non-Uniform Memory Access) est crucial. Les systèmes modernes disposent de plusieurs nœuds mémoire, chacun accessible à des cœurs CPU spécifiques. L'accès à la mémoire proche du cœur rend l'exécution beaucoup plus rapide.
   *  Optimisation : Assurer que le code d’inférence utilise la mémoire du nœud NUMA approprié où les cœurs CPU responsables sont situés. Cela nécessite un mappage précis des couches du modèle et des tableaux de poids vers ces nœuds.
   *  Diagnostics: Utiliser des outils comme `numactl` pour identifier les nœuds NUMA actifs et leurs métriques d'accès à la mémoire.

* **Memory Layout (Disposition Mémoire):**
    *  L’organisation de la mémoire du modèle a un impact direct sur sa performance. Minimise la fragmentation.
    *  Stratégies :
        *   Aligner les données dans des structures en mémoire pour optimiser l'accès aux mots, souvent nécessaire avec des frameworks LLM.
        *   Utilisation de memory pools et de blocages dynamiques (dynamic allocation) de manière efficace pour minimiser la surcharge liées à l’allocation/désallocation.

**Exemple Concret:**

Imaginons un LLM d'architecture transformer. En utilisant `taskset`, on pourrait fixer le cœur CPU 0 aux couches d’attention en lecture et le cœur CPU 1 aux couches de projection.  En parallélisant l'inférence, on réduit les transferts entre les caches et améliore la vitesse globale.

**Pièges:**

* **Over-Pinning :** Attacher trop de cœurs à une couche peut entraîner une sous-utilisation d'autres cœurs et affecter négativement le débit global.
*   **Ignorer NUMA :**  Même si la performance est acceptable, l’accès à la mémoire distante augmente significativement la latence.
*   **Memory Fragmentation :** Une mauvaise gestion de la mémoire entraîne des allocations/désallocations fréquentes, bloquant les cœurs CPU et ralentissant l'inférence.  Préférez les pools pré-alloués lorsque possible.
* **Interférence avec le scheduler du noyau:** Le pinning peut parfois augmenter la latence si le système est fortement sollicité en termes de tâche planifiées. Surveillez attentivement le charge du système.

**Ressources Supplémentaires:**

*   `numactl` documentation : [https://man7.org/linux/numactl](https://man7.org/linux/numactl)
*   Documentation `taskset` : [https://www.gnu.org/software/coreutils/taskset.html](https://www.gnu.org/software/coreutils/taskset.html)

Note:  L'optimisation parfaite dépend fortement de l’architecture spécifique du système (nombre de cœurs, configuration NUMA), de la taille du modèle LLM et du framework d’inférence utilisé (PyTorch, TensorFlow...).
