# Kernel Scheduling & Resource Contention Optimization for Low-Latency Applications - Realtime Extensions and QoS

*Domaine : Kernel / Performance Tuning*

# Optimisation du Kernel et Contention des Ressources pour Applications Faible Latence

## Contexte
Dans les architectures modernes basées sur Linux (notamment pour l'exécution de modèles LLM locaux ou d'applications temps réel critiques), le scheduler par défaut (`CFS` - Completely Fair Scheduler) privilégie l'équité plutôt que la réactivité immédiate. Pour des applications nécessitant une latence déterministe (ex: inférence audio, trading haute fréquence, contrôle industriel), le comportement asynchrone du kernel et les contentions sur les ressources partagées (CPU cache, mémoire, bus PCIe) peuvent introduire des *jitter* inacceptables. L'objectif est de transformer le système en une plateforme déterministe via des extensions temps réel (*Realtime Extensions*) et une gestion rigoureuse de la Qualité de Service (QoS).

## Points Clés

*   **Activation du Scheduler Temps Réel** : Le scheduler `CFS` standard ne garantit pas l'exécution immédiate. Il est impératif d'activer le scheduler `SCHED_FIFO` ou `SCHED_RR` pour les threads critiques. Cela nécessite généralement un noyau compilé avec l'option `CONFIG_PREEMPT_RT_FULL`. Ce patchset transforme le kernel en mode préemptif, réduisant drastiquement la latence de réponse aux interruptions et les délais d'échéance (*wakeup latency*).
*   **Gestion des Priorités CPU** : Utiliser `chrt` pour assigner des priorités élevées (ex: priorité 95-99) aux processus critiques. Cependant, une priorité élevée ne suffit pas si le thread est bloqué par un autre mécanisme du kernel (ex: attente sur un fichier ou une ressource de périphérique).
*   **Isolation CPU (`isolcpus`)** : Réserver des cœurs physiques spécifiques uniquement à l'application critique via les paramètres `isolcpus`. Cela empêche le scheduler de placer des tâches non critiques (comme le daemons du système ou le swap) sur ces cœurs, évitant ainsi les *cache misses* et la contention mémoire.
*   **Affinité Numérique (`numactl`)** : Pour les applications gourmandes en mémoire (LLM), lier explicitement les processus aux nœuds de mémoire NUMA correspondants réduit la latence d'accès à la RAM et évite les traversées inter-nœuds coûteuses.
*   **Gestion des Interruptions** : Affecter les IRQ (Interruptions Requises) du matériel critique (cartes réseau, GPU PCIe) aux cœurs isolés pour éviter que le traitement de l'interruption ne perturbe la logique de calcul principale.

## Exemple Concret : Déploiement d'un Serveur LLM Local

Pour exécuter un modèle
