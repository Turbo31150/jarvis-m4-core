# Tuning des Paramètres de Fenêtre d'Envoi (Window Size) et de Segmentation pour les Connexions Longues à Très Haute Latence

*Domaine : Réseau Avancé*

# Optimisation TCP : Fenêtre d'Envoi et Segmentation pour la Haute Latence

## Contexte
Dans les architectures modernes (Cloud hybride, liens satellite, connexions WAN), la latence de propagation ($RTT$) peut être élevée (100ms à plusieurs secondes). Le protocole TCP standard utilise souvent une fenêtre d'envois (`snd_wnd`) sous-optimale ou un algorithme de contrôle de congestion (Cubic) qui réagit trop lentement aux pertes, limitant le débit utile. Pour les connexions longues et instables, il est impératif de découpler la taille de la fenêtre TCP de la taille du tampon réseau (`net.core.rmem_max`) et d'ajuster la segmentation des paquets pour maximiser l'utilisation de la bande passante disponible sans saturer le réseau.

## Points Clés Techniques

*   **Découplage Fenêtre vs RTT** : La fenêtre d'envois TCP doit être calculée dynamiquement. Une fenêtre fixe est inefficace sur des liens à haute latence car elle ne compense pas l'accumulation de paquets en vol. L'objectif est de maintenir une "file d'attente" (pipe) remplie pour masquer la latence.
*   **Ajustement de `tcp_window_scaling`** : Activer l'échelle de fenêtre est obligatoire (`net.ipv4.tcp_window_scaling = 1`) lorsque le tampon réseau dépasse 64Ko, ce qui est fréquent sur les liens WAN optimisés. Cela permet d'utiliser des fenêtres logiques bien supérieures à la taille physique du tampon TCP.
*   **Optimisation de `tcp_mtu_discovery`** : Sur les liens longs, éviter les fragmentation coûteux. Activer le PMTUD (`net.ipv4.tcp_mtu_probing = 2`) permet au système de découvrir dynamiquement la MTU optimale, réduisant ainsi la charge CPU liée à la reassemblage des paquets et évitant les timeouts dus aux ICMP "Fragmentation Needed".
*   **Gestion de `tcp_congestion_window`** : Pour les connexions longues, privilégier l'algorithme **Cubic** (défaut sur Linux) ou **BBR** (`net.ipv4.tcp_congestion_control=bbr`). BBR est particulièrement efficace sur les liens à haute latence car il modélise la bande passante disponible plutôt que de réagir uniquement aux pertes de paquets.
*   **Taille des Segments (MSS)** : Augmenter la taille minimale du segment (`net.ipv4.tcp_mtu_probe_count`) ou forcer une MSS plus grande via `tcp_moderate_rcvbuf` peut aider, mais attention à ne pas dépasser la MTU physique du lien pour éviter les ICMP.

##
