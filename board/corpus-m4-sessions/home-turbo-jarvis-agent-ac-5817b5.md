[user] Tu assainis deux problèmes d'unités systemd en scope **utilisateur** (`systemctl --user`) sur une machine Linux (Ubuntu, hôte turbo-MS-7C56, utilisateur turbo). Tu ne connais rien de la conversation qui précède. Ces deux problèmes ont chacun un diagnostic déjà établi et prouvé : ta mission est d'appliquer les corrections et de les vérifier, pas de re-diagnostiquer.

## Problème 1 — Doublon d'unités sur le port 18801

Deux unités systemd `--user` pointent vers le **même script** `/home/turbo/Workspaces/jarvis-linux/canvas/dashboard-server.js` (serveur Node qui écoute sur 127.0.0.1:18801) :

| Unité | `WantedBy` | `User=` | État |
|---|---|---|---|
| `jarvis-agent-dashboard.service` | `default.target` ✅ | absent ✅ | **disabled**, mais actuellement démarrée à la main |
| `jarvis-dashboard-node.service` | `multi-user.target` ❌ | `turbo` ❌ | **enabled**, incapable de démarrer |

`jarvis-dashboard-node.service` est cassée pour deux raisons cumulées, toutes deux vérifiées :
- `WantedBy=multi-user.target` : dans le gestionnaire *utilisateur*, la cible de démarrage est `default.target`, et `multi-user.target` n'est jamais activée. Le lien d'activation existe mais pend sous une cible que personne ne démarre.
- `User=turbo` : directive **interdite** dans une unité `--user`. Tentative de démarrage → `status=216/GROUP` (systemd refuse de changer d'utilisateur), et avec `Restart=always` elle bouclait.

Le référentiel `/home/turbo/jarvis/infra/config/cluster/service-ownership.json` désigne 

[assistant] Problem 1 confirmed (agent-dashboard disabled but serving 200; dashboard-node enabled/inactive). Applying the fix.

[assistant] Problem 1 done. Now BrowserOS — the unit is `active (running)` since 1h30 but 9105 never opened, exactly the described symptom. Backing up and patching.

[assistant] Both fixes applied and verified.

## Problème 1 — Doublon port 18801

| Unité | Avant | Après |
|---|---|---|
| `jarvis-agent-dashboard.service` | `disabled` (active à la main) | **`enabled`** — symlink créé sous `default.target.wants/` |
| `jarvis-dashboard-node.service` | `enabled` (inactive, incapable de démarrer) | **`disabled`** — symlink retiré de `multi-user.target.wants/` |

Port 18801 : `HTTP 200` avant, `HTTP 200` après. Aucun fichier d'unité supprimé, la manœuvre est réversible par `systemctl --user enable jarvis-dashboard-node.service`.

## Problème 2 — BrowserOS / CDP 9105

Sauvegarde : `/home/turbo/.config/systemd/user/browseros.service.bak-20260806-140825` (copie `cp -a`, horodatée).

Diff de l'`ExecStart` — un seul argument inséré, tout le reste identique :
```
-ExecStart=… browseros --no-first-run --no-default-browser-check --remote-debugging-port=9105 …
+ExecStart=… browseros --no-first-run --no-default-browser-check --password-store=basic --remote-debugging-port=9105 …
```

Preuve que 9105 écoute (le port était fermé avant, alors que l'unité était `active (running)` depuis 1 h 30 — le symptôme décrit, confirmé) :

```
LISTEN 0 10  127.0.0.1:9105  0.0.0.0:*  users:(("browseros",pid=1220670,fd=95))

$ curl -s http://127.0.0.1:9105/json/version
{
   "Browser": "Chrome/146.0.7818.31",
   "Protocol-Version": "1.3",
   "webSocketDebuggerUrl": "ws://127.0.0.1:9105/devtools/browser/51f3f113-…"
}
```

Le port s'est ouvert en ~4 s après le `restart` (sondage par bouc