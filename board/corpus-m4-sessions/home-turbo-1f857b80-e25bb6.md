[user] benchmark de linux orifigine et hardware de cette machine origine etb amélmioration en % teste fort mega complet pour evaluer % et poursuivre

[assistant] Je lance d'abord un contrôle mémoire (règle M6 : lire `/proc/pressure/memory` avant tout benchmark lourd), puis j'établis la fiche hardware complète.

[assistant] ⚠️ **Alerte avant de "tester fort"** : la machine est déjà à **load 11.3** (pour un i5-4460 4 cœurs), **swap à 6.9 Gi utilisé** et pression mémoire `some avg10=24`. Lancer un stress mega-complet maintenant = risque de gel GUI (incident M6 connu). Je fais d'abord l'inventaire hardware + j'identifie ce qui charge déjà, puis je lance des micro-benchmarks bornés (pas un stress destructeur).

[assistant] Diagnostic clair. Voici l'état **M6 (machine origine)** :

| Composant | Détail |
|---|---|
| **CPU** | Intel i5-4460 — **4 cœurs / 4 threads** (pas d'HT), 3.2→3.4 GHz, L3 6 Mo |
| **RAM** | 11 Gio (DDR3) + zram 6 Go + swap fichier 12 Go |
| **GPU 0** | RTX 2060 **12 Go** (7.6 Go occupés par llama-server) |
| **GPU 1** | RTX 3080 **10 Go** (6.6 Go occupés) |
| **Disque /** | SSD SATA WD Blue SA510 1 To (root sur sdb2, 44%) + SSD WD 500 Go |
| **OS** | Ubuntu 24.04.4 LTS, **noyau 7.0.0-29** (mainline) |

La **load 11 est normale ici** : 2× `llama-server` + `ollama` + serveurs modèles node + 3 `claude` tournent (cluster JARVIS actif). GPU à 2-3 % mais VRAM chargée. Je lance maintenant des benchmarks **bornés** (pas de stress destructeur) pour fixer le baseline mesurable.

[assistant] Tous les outils présents (sysbench, fio, stress-ng), gouverneur **performance**, CPU à pleine fréquence (3.19 GHz). Je lance la suite de benchmarks bornée (~90 s total) et je sauvegarde le baseline.

[assistant] Résultats **fortement contendus** (load monté à 14 pendant le test) — c'est le vrai état "origine". Maintenant le disque, puis je mesure le **potentiel d'amélioration en %** en comparant contendu vs allégé.