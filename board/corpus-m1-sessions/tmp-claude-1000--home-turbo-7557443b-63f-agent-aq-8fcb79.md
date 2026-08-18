[assistant] Je regarde les deux commits séparément pour distinguer ce qu'apporte chacun, puis le fichier complet pour juger du style.

[assistant] Revue transmise à `main`. Verdict : **corrections requises**, trois points bloquants.

Le changement est conforme, bien commenté et sans dérive de périmètre — et j'ai confirmé que l'idiome `${VAR}` est le bon choix : `docker stack` ne lit pas de `.env`, même dans le cwd (testé via `docker stack config`), donc l'export par le script de boot est la seule voie qui marche.

Ce qui manque, ce sont les conséquences du passage d'antigravity-mcp en réseau host, non traitées dans le même lot :

- **La route nginx 18902 est morte.** Le service ayant quitté `jarvis-net`, l'upstream `http://antigravity-mcp:8902` (`infra/docker/nginx.conf:134`) n'est plus résoluble — `curl http://127.0.0.1:18902/` renvoie 503 après 4 s. Le loadbalancer ayant déjà `extra_hosts`, le correctif est de repointer sur `host.docker.internal:8902`.
- **Le proxy MCP est exposé au LAN et à Tailscale.** `ss` montre `*:8902`, et les IP 192.168.0.10 comme 100.112.114.32 répondent, `/sse` compris. Avant, le port n'existait que dans l'overlay derrière le `limit_req` de nginx. Ce port donne accès à `openclaw acp`.
- **Le script de boot n'a aucun garde-fou.** J'ai vérifié que la substitution à vide sort en exit 0 sans le moindre avertissement, et `docker stack deploy` réécrit la spec des services : une lecture ratée transitoire dégrade durablement un service qui marchait. Je l'ai classé Important plutôt que Critical (réparable par une relance, boot best-effort), mais le correctif coûte trois lignes.

Point annexe confirmé 

[assistant] La revue est terminée et le rapport a déjà été envoyé à `main`. Je le relaie à toi directement pour être sûr qu'il t'arrive.

[assistant] Oui, la revue était terminée — le rapport avait été envoyé à `main`, je viens de te le relayer directement.

**Verdict : corrections requises**, trois points bloquants, tous vérifiés empiriquement sur la machine :

1. **La route nginx 18902 est morte.** antigravity-mcp ayant quitté `jarvis-net`, l'upstream `http://antigravity-mcp:8902` (`infra/docker/nginx.conf:134`) n'est plus résoluble par le DNS de l'overlay — `curl http://127.0.0.1:18902/` renvoie 503 après 4 s. Un service Swarm ne pouvant pas cumuler réseau `host` et overlay, le correctif est côté nginx : le loadbalancer a déjà `extra_hosts`, il suffit de pointer sur `host.docker.internal:8902`.
2. **Le proxy MCP est ouvert au LAN et à Tailscale.** `ss` montre `*:8902`, et les adresses 192.168.0.10 comme 100.112.114.32 répondent, `/sse` compris. Le port donne accès à `openclaw acp` sans authentification HTTP ; avant, il n'était joignable que via nginx:18902 avec son `limit_req`.
3. **Le script de boot ne se protège d'aucun des deux échecs de lecture.** J'ai confirmé que la substitution à vide sort en exit 0 sans le moindre avertissement, et que `docker stack deploy` réécrit la spec des services : une lecture ratée transitoire dégrade durablement un service qui fonctionnait. Classé Important et non Critical, puisqu'une relance répare et qu'il s'agit d'un boot best-effort.

S'y ajoute un point d'hygiène confirmé : le `set -a` propage les 30 variables du `.env` aux daemons de monitoring lancés en fin de script — le node_age