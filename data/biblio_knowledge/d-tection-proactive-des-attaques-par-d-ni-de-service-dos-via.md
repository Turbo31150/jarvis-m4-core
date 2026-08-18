# Détection proactive des attaques par déni de service (DoS) via analyse des patterns d'appels système (syscalls) anormaux en temps réel.

*Domaine : Security - Incident Response*

# Détection Proactive DoS via Analyse des Syscalls sur Linux

## Contexte
Dans les environnements sécurisés modernes, notamment ceux pilotés par des agents autonomes comme **JARVIS** ou des modèles LLM locaux déployés sur du matériel Linux, la réponse aux attaques par déni de service (DoS) ne peut plus se limiter à l'analyse passive des logs réseau. Les attaques modernes exploitent souvent des vulnérabilités logicielles subtiles ou saturent les ressources système avant que le pare-feu n'intervienne.

L'analyse des **appels système (syscalls)** en temps réel offre une visibilité granulaire au niveau noyau (kernel). Contrairement aux logs réseau qui montrent "ce qui est arrivé", les syscalls révèlent "ce qui a été demandé". Une attaque DoS se manifeste souvent par un comportement anormal de ces requêtes, permettant une détection proactive bien avant l'épuisement total des ressources.

## Points Clés

*   **Surveillance des appels d'E/S massifs** : Un processus normal effectue un nombre limité d'appels `read`, `write` ou `sendmsg`. Une attaque DoS visant à saturer le réseau ou le disque se caractérise par une fréquence de ces syscalls anormalement élevée (ex: > 10k appels/seconde depuis un seul PID).
*   **Détection des boucles infinies** : Les attaques par rejeu (replay attacks) ou l'exploitation de bugs provoquent souvent des boucles dans le noyau, générant une séquence identique et répétitive de syscalls (`open`, `read`, `close`) sans progression logique.
*   **Analyse des arguments des syscalls** : L'examen des paramètres passés aux syscalls (ex: taille du buffer dans `write`, adresse mémoire dans `mmap`) permet d'identifier des tentatives d'injection de données massives ou d'allocation mémoire malveillante (`brk`, `mmap` excessifs).
*   **Corrélation Processus-Ressource** : Croiser les syscalls avec l'utilisation du CPU et de la mémoire (via `/proc/[pid]/status`) permet de distinguer une charge légitime d'une attaque DoS ciblant spécifiquement le processeur ou la mémoire vive.

## Exemple Concret : Scénario d'Exploitation

Imaginez un serveur Linux hébergeant un modèle LLM local. Un attaquant tente de saturer le service en envoyant des requêtes malformées qui déclenchent une boucle dans l'application.

1.  **Observation** : Le système génère une alerte car le processus `llm_server` (PID 4520) effectue 50 000 appels
