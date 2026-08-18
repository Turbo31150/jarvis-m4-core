# Corrélation des traces de latence réseau avec les événements d'allocation de mémoire du noyau pour identifier les causes racines des timeouts dans les appels RPC inter-nœuds.

*Domaine : Observabilité - Debugging à Distance*

# Corrélation Traces Réseau / Allocation Mémoire : Diagnostic des Timeouts RPC Inter-nœuds

## Contexte
Dans les architectures distribuées (clusters Linux/JARVIS), un timeout lors d'un appel RPC (Remote Procedure Call) entre nœuds est souvent attribué à la congestion du réseau ou à une saturation CPU. Cependant, une cause fréquente et subtile réside dans l'interaction entre le **noyau Linux** et les appels système bloquants générés par des allocations de mémoire critiques.

Lorsque l'espace physique (RAM) est épuisé, le noyau déclenche un processus d'allocation de pages (`alloc_pages`) qui peut bloquer le thread du processeur en attendant que le gestionnaire de mémoire (`kswapd` ou `pdflush`) libère des pages. Si ce blocage se produit sur le thread gérant la pile TCP/IP, les paquets réseau sont non traités, provoquant un timeout apparent côté client RPC, bien que le réseau soit sain.

## Points Clés

*   **Mécanisme de Blocage** : Une allocation mémoire majeure (`kmalloc` ou `vmalloc`) dans l'espace utilisateur peut déclencher une allocation interne au noyau. Si la RAM est fragmentée ou insuffisante, le thread du processeur reste bloqué en état `D` (uninterruptible sleep) jusqu'à ce que de la mémoire soit libérée.
*   **Impact sur la Stack Réseau** : Les threads réseau (`ksoftirqd`, `NAPI`) et les processus d'application gérant les sockets RPC partagent des ressources CPU et mémoire. Un blocage prolongé dans l'espace utilisateur ou le noyau empêche le traitement des paquets ACK ou de données, simulant une perte de connectivité.
*   **Latence vs Timeout** : Une latence réseau élevée est linéaire (paquets retardés). Un timeout dû à l'allocation mémoire est non-linéaire et imprévisible, car il dépend du temps nécessaire au `kswapd` pour ramasser des pages libres (`page reclaim`).
*   **Outils de Corrélation** : Utiliser `bpftrace`, `ftrace` ou `perf` pour superposer les timestamps des événements réseau (`tcp_sendmsg`, `tcp_ack`) avec ceux d'allocation mémoire (`alloc_pages`, `kswapd_start`).

## Exemple Concret

**Scénario** : Un nœud JARVIS lance un LLM local. Une requête RPC vers un autre nœud échoue après 30 secondes (timeout configuré à 15s). Le réseau est stable (ping OK).

**Analyse des traces** :
1.  **Capture Réseau (`tcpdump`)** : On observe que les paquets de réponse du
