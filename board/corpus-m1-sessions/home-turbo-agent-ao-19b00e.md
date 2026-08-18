[assistant] Je lance le diagnostic read-only. Première salve : état des processus et modèles chargés.

[assistant] Le processus est bien là. Deuxième salve : threads, connexions, logs, cartographie mémoire.

[assistant] Le journal montre un décodage en cours en direct. Je mesure maintenant le CPU instantané (le 507 % de `ps` est une moyenne sur 10 h) et le débit de requêtes.

[assistant] Verdict qui se dessine. Dernière salve pour confirmer la source des 9,5 Go et la config.

[assistant] Deux découvertes importantes : un second `llama-server` non listé par le premier `pgrep`, et 1181 requêtes d'embeddings toutes en 503. Je vérifie.

[assistant] Je vérifie le nom exact de la variable de plafonnement du cache avant de la proposer, pour ne pas recommander un réglage inexistant.

[assistant] ## Rapport — llama-server Ollama M1 (PID 2638953)

**Verdict : hypothèse (a) — trafic légitime continu du hub.** Le processus ne spin pas et n'accumule pas de requêtes fantômes : il décodait réellement des tokens pendant tout le diagnostic (task 839621, 26 à 30 t/s, `n_decoded` croissant), à la demande de `chat_proxy.js`. Deux dysfonctionnements réels se superposent quand même à ce trafic, détaillés plus bas.

### Processus

| PID | Rôle | Âge | %CPU | RSS | Swap | Threads |
|---|---|---|---|---|---|---|
| 2638953 | llama-server Ollama, gemma3:4b | 10 h 46 | **621 % (mesuré sur 5 s)** | 9,77 Go | 1,10 Go | 24, état R |
| 2460134 | llama-server **LM Studio** qwen3.5-9b | 2 min | 96 % | 3,77 Go | — | (hors sujet) |
| 4187101 | `ollama serve` (parent) | 18 h 51 | 2,0 % | 115 Mo | — | — |

Le 505 % initial était la moyenne de `ps` sur toute la vie du processus ; l'instantané est plus haut encore, 621 %. Le second `llama-server` que le premier `pgrep` n'avait pas listé appartient à LM Studio, il vient de démarrer et n'a rien à voir avec Ollama.

### Pourquoi ce n'est ni (b) ni (c)

Le TTL n'a jamais expiré : `expires_at` est à 23:31:01 alors qu'il était 23:02, donc il a été repoussé par du trafic frais — pas de boucle post-unload. Une seule connexion active vers le llama-server interne (`:32293`, détenue par `ollama serve`), et deux vers `:11434` détenues par `chat_proxy.js` : rien qui ressemble à des clients partis avec des générations orphelines. Sur la dernière heure, Ollama a 

[assistant] Rapport L14 transmis à `main`.

**Verdict : hypothèse (a) — trafic légitime continu du hub.** Le llama-server (PID 2638953) décodait réellement pendant tout le diagnostic, à 621 % de CPU instantané (le 505 % initial n'était que la moyenne de `ps` sur 10 h 46 de vie), 9,77 Go de RSS et 1,10 Go de swap. Le TTL n'avait pas expiré — `expires_at` repoussé à 23:31 par du trafic frais — donc ni requêtes fantômes, ni spin post-unload.

Deux problèmes réels se superposent à ce trafic légitime. Le premier explique le CPU : 67 des 104 tâches de l'heure, soit 64 %, ont déclenché un `forcing full prompt re-processing`, la fenêtre glissante de gemma3 invalidant les checkpoints de contexte. Le second explique la RAM : le prompt cache multi-entrées de llama.cpp, mesuré dans le journal à 50 entrées pour 7523 MiB et croissant, alors que le KV-cache d'un seul slot (`-np 1 -c 4096`) ne pèse que quelques centaines de Mo. `Referenced` à 2,91 Go sur 9,77 confirme que 70 % de cette empreinte est froide — on paie 7,5 Go pour un cache que la SWA invalide.

À part : **1181 `POST /api/embeddings` en une heure, toutes en 503**, émises par le même `chat_proxy.js`. Sans effet sur le CPU (échec en 20 ms) mais c'est un pilonnage continu d'un endpoint mort, à rapprocher de L13. Le hub garde aussi des connexions ouvertes vers rem-linux alors que L10 a été annulé.

Action recommandée : ne rien faire sur le llama-server maintenant, corriger d'abord les embeddings côté hub, et réserver `systemctl restart ollama` 