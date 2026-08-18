# Configuration Fine du Buffering TCP et Gestion de la Congestion pour Microservices à Haute Fréquence

*Domaine : Réseau Avancé*

# Configuration Fine du Buffering TCP et Gestion de la Congestion pour Microservices Haute Fréquence

### Contexte
Dans les architectures microservices à haute fréquence (ex: trading, IoT temps réel), le modèle de communication par requête-réponse standard (`send-and-wait`) devient un goulot d'étranglement majeur. Les connexions TCP brèves mais fréquentes génèrent une surcharge de contrôle (handshake/TLS) et sous-utilisent la bande passante disponible. L'optimisation du *buffering* et des algorithmes de congestion est donc critique pour maximiser le débit utile tout en maintenant une latence prévisible.

### Points Clés

*   **Optimisation des Fenêtres TCP (`TCP Window`)** :
    Le mécanisme fondamental pour éviter les pauses d'attente (head-of-line blocking) est l'augmentation de la fenêtre de réception (`rcv_buf`). Par défaut, Linux utilise souvent 256 Ko, ce qui est insuffisant pour saturer les liens 10 Gbps. Il est impératif d'augmenter `net.core.rmem_max` et `net.ipv4.tcp_rmem` (min/opt/max) pour permettre des fenêtres de plusieurs Mo, voire Go, selon la latence RTT du réseau.

*   **Gestion Aggressive de la Congestion (`BBR` vs `Cubic`)** :
    L'algorithme par défaut (`Cubic`) réagit lentement aux pertes de paquets en réduisant le taux d'envoi, ce qui peut provoquer des oscillations de débit dans les environnements bruyants. Pour les microservices sensibles à la latence, l'utilisation de **BBR (Bottleneck Bandwidth and RTT)** est recommandée. BBR modélise la capacité du goulot d'étranglement et maintient un taux d'envoi élevé même en présence de pertes légères, optimisant ainsi le *throughput* sans augmenter artificiellement la latence perçue.

*   **Réduction de la Latence de Filet (`Zero-Copy` & `TCP_NODELAY`)** :
    Activer `TCP_NODELAY` empêche l'attente d'un buffer plein avant l'envoi, réduisant la latence mais augmentant le nombre de paquets (et donc les risques de perte). Dans un contexte haute fréquence, c'est souvent nécessaire. Couplé à `sendfile()` et `zerocopy`, cela élimine les copies de données entre noyau et espace utilisateur, crucial pour réduire la CPU overhead sur les serveurs d'application.

*   **Durée de Vie des Connexions (`Keepalive` & `TIME_WAIT`)** :
    Pour éviter l'épuisement des ports et maintenir la connectivité, ajuster `tcp_keepalive_time` et `tcp_keepalive
