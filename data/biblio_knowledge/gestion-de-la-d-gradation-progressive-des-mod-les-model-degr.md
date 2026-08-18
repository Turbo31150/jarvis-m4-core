# Gestion de la dégradation progressive des modèles (Model Degradation) et stratégies de fallback vers un modèle plus petit lors d'une surcharge mémoire.

*Domaine : LLM Local - Runtime Resilience*

# Gestion de la Dégradation des Modèles Locaux et Stratégies de Fallback Mémoire

## Contexte
Dans les déploiements **LLM locaux** (ex: Ollama, vLLM, LM Studio) sur infrastructure Linux/JARVIS, la résilience du runtime est critique. Contrairement aux serveurs cloud élastiques, un serveur local possède des ressources physiques fixes. Une dégradation progressive se manifeste souvent par une augmentation de la latence d'inférence ou des erreurs d'allocation mémoire (`OOM Killer`), forçant l'arrêt brutal du service. L'objectif est de maintenir la disponibilité en basculant dynamiquement vers un modèle plus petit (fallback) lorsque la charge dépasse le seuil tolérable.

## Points Clés

*   **Détection Précoce de la Dégradation** : Surveiller les métriques `vLLM` ou `Ollama` (latence P99, taux d'erreur GPU). Une latence qui s'accélère exponentiellement indique une fragmentation mémoire ou un approvisionnement imminent en RAM/GPU VRAM.
*   **Surveillance de la Mémoire Système** : Utiliser `free -m`, `/proc/meminfo` et les outils NVIDIA (`nvidia-smi`) pour détecter le remplissage du swap ou l'activation de l'OOM Killer avant l'échec total.
*   **Architecture de Fallback Dynamique** : Implémenter un pattern "Circuit Breaker" où la requête échouée ou trop lente déclenche automatiquement une réinitialisation vers une configuration de modèle à faible consommation (ex: passer de `Llama-3-8B` à `TinyLlama-1.1B`).
*   **Gestion des Poids Quantifiés** : Privilégier les modèles quantifiés (`FP8`, `INT4`) pour le modèle de fallback afin de réduire drastiquement l'empreinte mémoire tout en conservant une qualité acceptable.
*   **Isolation par Conteneurisation** : Exécuter chaque instance de modèle dans un conteneur Docker séparé avec des limites de mémoire strictes (`--memory`), permettant au système d'arrêter le conteneur lourd sans tuer l'hôte.

## Exemple Concret : Script Bash de Surveillance et Fallback

Ce script surveille la charge GPU et bascule vers un modèle léger si la VRAM dépasse 80% pendant plus de 10 secondes.

```bash
#!/bin/bash
# Configurations
MODEL_HEAVY="llama3:8b"
MODEL_LIGHT="tinyllama:1.1b"
GPU_THRESHOLD=80 # %
CHECK_INTERVAL=5 # secondes

while true; do
    # Récupération de l'utilisation VRAM (%)
    USAGE=$(nvidia-sm
