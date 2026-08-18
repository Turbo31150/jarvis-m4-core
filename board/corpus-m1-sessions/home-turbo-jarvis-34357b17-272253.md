[user] la machine re remi linux doit tout basculer niveau containers sur sa machine 2 tous sa machine remi linux passe par sa machine 2  zsa machine 2 et un min ux classoique nos l'utilison pas nous m1 et ma m6 est juste connectyer a ellke et les bibliotheque vivante ensemble sqseulement et le partage de puissan,ce quye jue partagte

[assistant] Je sonde avant de router — il faut d'abord identifier « machine 2 de Rémi » et ce qui tourne réellement sur rem-linux.

[user] Base directory for this skill: /home/turbo/.claude/skills/run-rem-node

# run-rem-node — le portable de Rémi vu depuis M1

`rem-linux` est le portable de Rémi, joint par Tailscale. Tout se diagnostique
via un seul driver : `/home/turbo/.claude/skills/run-rem-node/driver.sh`. Il
fait du SSH + `xdotool`/`import` sur le **DISPLAY=:1** distant — il n'y a pas
d'API, la seule prise sur ce bureau est X11 par-dessus SSH.

## Identité de la machine — à ne pas confondre

| | |
|---|---|
| Nom d'hôte | `rem-linux` |
| Tailscale | **`jarvis-dva` = 100.113.121.61** |
| Comptes SSH | `root` et `rempc` **uniquement** |
| Bureau X | **`DISPLAY=:1`**, `XAUTHORITY=/run/user/1000/gdm/Xauthority` |

⚠️ `jarvis-server` / `100.124.69.1` / `serveurremjarvis` est une **autre**
machine (le serveur). Les deux forment le Swarm `jarvis-full-stack_*`, distinct
du Swarm `jarvis_prod_*` de M1. Confondre les deux est l'erreur classique.

## Prérequis (déjà en place sur M1)

Alias SSH dans `~/.ssh/config`, avec la clé dédiée `~/.ssh/rem_jarvis_ed25519` —
obligatoire, les autres clés du cluster (`jarvis_cluster`, `m5_jarvis_ed25519`)
sont refusées. Deux hôtes : `rem` (root) et `rem-desktop` (rempc), tous deux
sur `100.113.121.61`, avec `IdentitiesOnly yes` et `StrictHostKeyChecking no`.

## Run (chemin agent) — le driver

```bash
/home/turbo/.claude/skills/run-rem-node/driver.sh check
```

Sortie réelle observée :

```
== Accès SSH → rem-linux (100.113.121.61) ==
  ✓ alias 'rem' (root) → rem-linux
  ✓ alias '

[assistant] Les 4 accès répondent (le `check` du driver a faussé sur un timeout court). Inventaire des deux côtés :

[assistant] Le serveur est un **worker** Swarm — donc le manager est le portable. C'est exactement l'inversion à corriger.

[assistant] Load **62 sur 8 cœurs** — le portable de Rémi est effondré, et c'est lui le manager Swarm. Je sonde la cause et les volumes avant de basculer.

[assistant] Découverte importante : les services tournent **déjà** sur le serveur (volumes présents, 69 Mo). Ce qui reste sur le portable, c'est le rôle **manager** du Swarm. J'attends l'inventaire du portable.

[assistant] Le tableau est clair. Je récupère l'état Swarm côté manager avant de promouvoir.

[assistant] Swarm identifié : `rem-linux` = **Leader unique**, le serveur = simple worker. Les 7 services Swarm tournent déjà sur le serveur ; ce sont les **9 containers standalone** du portable + le rôle manager qui doivent basculer. Je promeus le serveur en manager (prérequis, réversible) :

[assistant] Control plane désormais redondant (serveur = `Reachable`). Les 9 containers standalone ne sont pas gérés par Swarm — je cherche leur définition avant de les recréer côté serveur :