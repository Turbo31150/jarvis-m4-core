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

[assistant] Diagnostic net : **ce n'est ni le CPU ni la RAM — c'est le disque**. `sdb` à **97 % d'utilisation**, 30 % d'iowait. La charge 26 est de l'attente disque, pas du calcul.

[assistant] AnyDesk : **déjà accepté** — « Session démarrée · Connecté à 1466293477 (identité confirmée) », accès sans surveillance actif. Rien à cliquer.

Je passe au désengorgement.

[assistant] Vrai coupable identifié : **85 % d'iowait**, `sdb` à 91 % avec 167 ms de latence de lecture. Ce n'est pas du calcul — c'est le disque écrasé par les hooks de plugins Claude Code, des scans `find` récursifs et l'autovacuum Postgres. Je passe les ressources de M1 et je calme l'I/O.

[assistant] **rem-linux désengorgé.**

| Mesure | Avant | Après |
|---|---|---|
| Load (8 cœurs) | **26,1** | **4,6** |
| iowait | **85 %** | **10,5 %** |
| CPU idle | 0 % | 59 % |
| `sdb` %util | 97 % | retombé |

**Diagnostic — ce n'était pas le CPU ni les LLM.** 9 Go de RAM libres, ollama ne tenait qu'un `qwen3:1.7b`. Le disque `sdb` était écrasé (167 ms de latence de lecture) par les hooks de plugins Claude Code (`context-mode/posttooluse.mjs`, `claude-mem/worker-service.cjs`), des `find`/`bfs` récursifs sur `~/.claude/plugins`, et l'autovacuum Postgres. La load comptait des processus bloqués en attente disque, pas du calcul.

**Ce que j'ai fait**
1. `ionice -c3` + `renice 15` sur les processus D-state — rien tué, rien perdu.
2. Pagecache libéré.
3. **Ressources M1 passées à Rémi** : LM Studio exposé sur l'IP Tailscale via socat `100.112.114.32:1234` (jamais de bind natif). Le hub `:18800` était déjà joignable.
4. Profil `~/.jarvis-m1-resources.sh` déployé chez `rempc`, sourcé par `.bashrc` : `OPENAI_BASE_URL` pointe le hub M1, plus une fonction `m1ask`. Smoke réel depuis rem → *« Bonjour Remi, le calcul tourne sur M1. »*

Modèles désormais offerts à rem : `qwen/qwen3.5-9b`, `openai/gpt-oss-20b`, `nomic-embed`.

**AnyDesk** : rien à accepter, la session était déjà active — « Session démarrée · Connecté à 1466293477, identité confirmée », accès sans surveillance.

**Deux points restants, que je n'ai pas touchés**
- **10 zombies `node`** que le parent `node src/index.js` (PID 20718, 12