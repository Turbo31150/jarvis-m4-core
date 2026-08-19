[assistant] RAM libérée (3,8 → 6,6 Gi, pression 87 % → 37 %). Le load 32 n'est plus du CPU (PSI cpu full = 0 %) mais de l'I/O : tout est bloqué en D-state pendant que 4 Go de swap remontent. Je coupe les batchs orphelins qui alimentent le thrash.

[assistant] Le vrai coupable est identifié : **LM Studio a lu 43 Go de disque en 15 min** — le modèle est mmap'é mais ne tient pas en RAM, donc ses pages sont évincées puis relues en boucle. C'est ce refault continu qui met toute la machine en D-state.

[assistant] Diagnostic net : le modèle fait **5,3 Go** mais llama-server n'a plus que **454 Mo résidents** — ses pages mmap ont été quasi intégralement évincées. Chaque inférence relit donc des Go depuis le disque. Je vérifie si les GPU sont utilisés.

[assistant] Le dégel prend : load **32 → 14,5**, pression I/O **68 % → 19 %**. Les GPU tiennent bien le modèle (2,5 Go + 4,7 Go), le thrash venait du chargement sous pression mémoire. Je passe maintenant à la réparation du service en échec.

[assistant] Le service échoue toutes les 2 min : le lien câble direct M6 ↔ M4 est absent. Je vérifie l'interface.

[assistant] Dégel terminé. Je regarde si le script de bascule sait retomber sur Tailscale, puisque M4 est joignable par là.

[assistant] Cause trouvée : le unit `lmstudio-server.service` relance une **seconde** instance de LM Studio, l'AppImage détecte « Another instance is already running », se termine → systemd redémarre → boucle → start-limit-hit. Pendant ce temps l'instance légitime (PID 7385) sert bien `:1234` (HTTP 200 en 3 ms). Je rends le unit idempotent.

[assistant] L'inférence tourne mais tombe sur le bug connu de qwen3.5 : 200 tokens consommés à 100 % en *reasoning*, `content` vide, `/no_think` ignoré. Le contournement existe déjà en maison — je le vérifie.

[assistant] Dégel et réparations terminés.

## Dégel

La machine n'était pas plantée : elle était en *direct reclaim*. Mesures avant → après :

| | avant | après |
|---|---|---|
| Load | 32,8 | 6,3 |
| RAM disponible | 3,8 Gi | 5,5 Gi |
| Pression mémoire (full) | 47 % | 0,7 % |
| Pression I/O (full) | 68 % | 11,6 % |
| Processus bloqués D-state | 15+ | 0 |
| Services en échec | 5 | 0 |

Enchaînement : `m6-relief run` (20 timers + 9 services de fond arrêtés) → puis arrêt de 3 batchs orphelins (`jarvis-executor`, `jarvis-producer`, `reports-reindex`) que les timers avaient déjà lancés et qui continuaient à marteler SQLite pendant que 4 Go de swap remontaient.

## Trois causes réparées

**1. `lmstudio-server.service` — boucle de relance (le vrai bug).** Le unit relançait une seconde instance de l'AppImage ; LM Studio répond « Another instance is already running » et se termine ; `Restart=always` relançait → 6 fois → `start-limit-hit`. Pendant ce temps `:1234` servait très bien, mais via une instance lancée hors du unit — systemd et la réalité avaient divergé.

Ajout d'une garde d'idempotence : `~/jarvis/bin/lmstudio-server-guard.sh` + drop-in `10-idempotence.conf`. Si `:1234` répond déjà, la garde surveille au lieu de dupliquer, et ne rend la main à systemd qu'après 3 sondes ratées d'affilée. Le unit est maintenant `active` et **propriétaire** du processus (MainPID 41004), une seule instance, modèle rechargé sur les deux GPU.

**2. `m6-server-watch.service` — échec toutes les 2 min.** Rien