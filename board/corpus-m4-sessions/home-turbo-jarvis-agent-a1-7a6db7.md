[user] Diagnostique et, si c'est sans risque, remets en service un service web local mort sur cette machine (M1, Ubuntu, hôte turbo-MS-7C56, utilisateur turbo).

PROBLÈME
Le port 18801 ne répond plus. Une sonde HTTP sur http://127.0.0.1:18801/ échoue (connexion refusée), alors que ses voisins de la même famille répondent :
- 18800 = hub LLM (chat_proxy.js) : OK
- 18802 = ccr proxy : OK
- 18803 = sql-bridge : OK
- 18801 = dashboard : MORT  ← ton sujet

D'après la documentation interne du projet, 18801 est le « dashboard » de la carte des ports JARVIS.

TA MISSION
1. Identifier CE QU'EST réellement ce dashboard : quel programme, lancé par quoi (systemd system ou --user, script, docker, cron, ou rien du tout). Cherche large : `systemctl list-units --all | grep -i dash`, `systemctl --user list-units --all | grep -i dash`, grep de "18801" dans /home/turbo/jarvis (bin/, scripts/, .claude/), /home/turbo/.config/systemd/user/, /etc/systemd/system/, et les fichiers de config docker.
2. Déterminer POURQUOI il est arrêté : jamais installé ? unité désactivée ? crash au démarrage ? dépendance morte ? port pris par autre chose ? Lis les journaux (`journalctl --user -u <unité> -n 50 --no-pager`).
3. Si — et seulement si — la remise en service est SANS RISQUE (un simple `systemctl --user start`, ou le lancement d'un script de lecture seule qui sert une page), fais-le et prouve que ça répond par un `curl -s -o /dev/null -w '%{http_code}'`.

PIÈGES DE CET ENVIRONNEMENT
- `sleep` en avant-plan est blo

[assistant] Found candidates. Let me disambiguate which unit files live where and what they run.

[assistant] The cause is emerging. Let me verify the script is safe to start and check when it last ran.

[assistant] Safe to start: binds 127.0.0.1 only, no side effects at startup (the `execSync` paths only fire on inbound requests). Starting it.

[assistant] `216/GROUP` — a second defect. Let me stop the flapping unit and start the correct one.

[assistant] Le port 18801 répond de nouveau (HTTP 200). Voici le diagnostic.

## 1. Ce qu'est le dashboard 18801

**Programme** : `/home/turbo/Workspaces/jarvis-linux/canvas/dashboard-server.js` — serveur HTTP Node sans dépendance, bind **127.0.0.1:18801** uniquement. Sert `dashboard.html` (« JARVIS v12.6 — Cluster Dashboard ») + une API dominos (`/api/dominos`, `/api/domino-chains`, `/api/domino-run`).

**Lancement** : deux unités systemd **--user** pointent sur le MÊME script — c'est là qu'est le piège :

| Unité (`~/.config/systemd/user/`) | `WantedBy` | `User=` | État initial |
|---|---|---|---|
| `jarvis-agent-dashboard.service` | `default.target` ✅ | absent ✅ | **disabled**, dead |
| `jarvis-dashboard-node.service` | `multi-user.target` ❌ | `turbo` ❌ | **enabled**, dead |

Le référentiel `/home/turbo/jarvis/infra/config/cluster/service-ownership.json` (l. 37) désigne **`jarvis-agent-dashboard`, port 18801, owner M1** comme le service légitime. C'est bien celui qui a servi jusqu'au 2026-08-03 22:34 (mtime de `/home/turbo/jarvis/logs/agent-dashboard.log`, qui contient le bandeau de démarrage `🚀 JARVIS Dashboard + Dominos API → http://127.0.0.1:18801`).

## 2. Cause exacte — deux défauts cumulés sur l'unité *enabled*

`jarvis-dashboard-node.service` était la seule unité activée, et elle est **doublement incapable de démarrer en scope `--user`** :

**Défaut A — jamais tirée au login.** Elle déclare `WantedBy=multi-user.target`, or dans le gestionnaire utilisateur la cible de démarrage 