[assistant] Je comprends : **M1 (cette machine) crash** et tu veux un **mode secours**. Je diagnostique d'abord la cause réelle des crashs avant de toucher à quoi que ce soit.

[assistant] Compris — la machine où l'on discute est **M6**, à transformer en **serveur** (LM Studio + MCP + OpenClaw + agents + SQL + outils), câblé Ethernet direct avec **M4**, en évitant les crashs. J'inventorie le terrain réel avant de proposer le plan.

[assistant] **Cause du crash trouvée — ce n'est pas un mystère matériel, c'est une famine mémoire :**

| Fait | Valeur |
|---|---|
| RAM totale | **11 Gi** (très peu pour cette charge) |
| RAM libre | **248 Mi** |
| zram | 6 G, **déjà 4,2 G occupés**, priorité 100 |
| swapfiles (4G+8G) | priorité −1 → **jamais utilisés**, zram absorbe tout |
| `vm.swappiness` | **100** (agressif au maximum) |
| Load average | **8,05 après 2 min d'uptime** |
| Redémarrages | **12 en 36 h**, certains après 3-4 min → gel dur, pas arrêt propre |

Et la charge posée dessus : `llama-server` 4,3 Go + GNOME + Xorg + Chrome + Remmina + gnome-remote-desktop + n8n + asterisk + wakeword. Sur 11 Go, ça ne tient pas — le noyau part en thrash zram et la machine gèle.

Le lien Ethernet direct **existe déjà et fonctionne** : `enp3s0` → `10.42.0.230/24`, voisin `10.42.0.1` joignable en **1,4 ms**.

Je vérifie deux points avant de toucher au graphique (tu es peut-être connecté en RDP dessus) :

[assistant] Situation claire — et **c'est bien M6** (`/etc/sysctl.d/99-jarvis-m6-tuning.conf`). Point décisif : **aucune session RDP ni SSH active**, ta session active est `tty3` (console texte). Le bureau GNOME tourne dans le vide et gaspille RAM + VRAM. La bascule serveur est donc sans risque pour ton accès.

J'applique la transformation. Étape 1 — garde-fous mémoire (la cause du gel) :

[assistant] La config mémoire M6 existante est déjà réfléchie (datée d'hier, en plein pic de crashs) — le vrai levier n'est pas le réglage, c'est **réduire la charge**. Mais avant de couper le graphique je vérifie un point critique : **LM Studio tourne sous la session de bureau** et mourrait avec elle.

[assistant] Voilà le vrai coupable. **LM Studio est un enfant de la session GNOME** (`gnome-session-b` → `lm-studio` → `llama-server`) : couper le bureau le tuerait. Et il tourne une flotte de services autonomes 24/7 sur 11 Go. Je mesure qui mange quoi :

[assistant] **64 services user tournent en parallèle** sur 11 Go — dont `user@1000.service` à **7 Go**. Je confirme l'identité du voisin sur le câble et les adresses d'écoute avant de basculer :

[assistant] Identités confirmées via Tailscale : cette machine = `jarvis-franck-m1` (fichier de tuning nommé m6), et **M4 = `jarvis-franck-m4` / 100.124.121.16**. Bonne nouvelle : **LM Studio écoute déjà sur `0.0.0.0:1234`** — donc joignable par M4 via le câble. Ollama, lui, est enfermé sur `127.0.0.1`.

Je bascule. Phase 1 — détacher LM Studio de la session graphique (sans ça, couper le bureau le tue) :

[assistant] Point important : la machine a accumulé **des dizaines d'unités LM Studio concurrentes** (`lms-headless`, `lmstudio-server`, `lms-keepwarm`, `lms-sentinelle`, `lmstudio-dual-warm`, `jarvis-lms-qwen-warm`, 3 watchdogs…). Des réchauffeurs qui chargent des modèles en même temps sur 11 Go — c'est une cause directe de gel. Je regarde lesquels sont réellement actifs :

[assistant] Voilà la cause réelle, et ce n'est pas le matériel :

**224 unités systemd user définies · 64 services actifs · plus de 20 timers qui se déclenchent toutes les 8 à 60 secondes** — `cluster-warmer`, `jarvis-resolution-guard`, `lms-sentinelle`, `jarvis-task-auto`, `mirra-rundue`, `jarvis-gpu-cb`, `widget-s9-reverse`… Chacun forke un Python/Node. Sur 11 Go avec un `llama-server` de 4,3 Go, la machine passe son temps à démarrer des processus : d'où le **load 8,05 après 2 minutes d'uptime** et le gel dur.

J'applique les deux gains sans risque immédiatement (garde-fou anti-gel + ouverture d'Ollama vers M4) :

[assistant] `earlyoom` est actif — la machine tuera désormais un processus au lieu de geler. Phase 2 — ouvrir Ollama vers M4 sur le câble direct :

[assistant] **Les deux endpoints sont joignables par M4 via le câble** :

| Service | Adresse pour M4 | État |
|---|---|---|
| LM Studio (qwen3.5-9b) | `http://10.42.0.230:1234/v1` | HTTP 200 ✅ |
| Ollama | `http://10.42.0.230:11434` | HTTP 200 ✅ |

Load redescendu de 8,05 → 3,57. Mais **il reste 191 Mi de RAM libre et le swap est monté à 5,7 Gi** : la machine reste au bord du gel tant que la charge n'est pas réduite.

Il me faut ton arbitrage sur un point que je ne peux pas trancher à ta place — sur 11 Go, **on ne peut pas tout garder**. Tu as construit ~50 automatisations qui tournent en boucle :