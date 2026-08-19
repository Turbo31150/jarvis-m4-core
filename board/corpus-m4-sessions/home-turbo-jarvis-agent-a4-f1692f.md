[user] Tu enquêtes sur une prolifération de processus qui sature le CPU d'une machine Linux (Ubuntu, hôte turbo-MS-7C56, utilisateur turbo, 16 threads). Tu ne connais rien de la conversation qui précède.

## Le constat

La charge système est montée jusqu'à **25.41 pour 16 threads** (surcharge de 60 %). Un relevé a montré :

```
PID     %CPU  DEPUIS    COMMANDE
687591   602   7 min    python3 rdit_analysis.py      (cwd: /home/turbo/jarvis/artifacts/e1-20260806)
47356     99   1h04     python3 /home/turbo/jarvis/bin/jarvis-plan.py --sync
128451    99   57 min   python3 /home/turbo/labo/bibliotheque/scripts/gen_sql_shortcuts.py
```

Et surtout, **plusieurs exemplaires du même script tournaient simultanément** :

```
jarvis-plan.py           3 exemplaire(s)
gen_sql_shortcuts.py     3 exemplaire(s)
rdit_analysis.py         7 exemplaire(s)
```

`rdit_analysis.py` avait un parent `timeout 900` (il mourra donc seul), mais pas les deux autres, qui tournaient depuis près d'une heure à 100 % d'un cœur chacun.

## Ce que tu dois établir

1. **L'état ACTUEL** : ces processus tournent-ils encore ? Combien d'exemplaires de chacun ? Depuis quand ? Relève la charge courante (`/proc/loadavg`).
2. **Qui les lance, et en boucle ?** Cherche dans : `crontab -l`, `sudo crontab -l` si accessible, `/etc/cron.*`, `systemctl list-timers --all` ET `systemctl --user list-timers --all`, les unités systemd des deux scopes, et tout script qui les invoque (`grep -rn` dans `/home/turbo/jarvis/bin`, `/home/turbo/jarv

[assistant] The pgrep patterns matched my own shell. Let me use safer detection and gather details.

[assistant] Key finding: `rdit_analysis` is gone, but 6 instances of `moisson.py` now dominate. Let me trace all launchers and parent chains.

[assistant] Both are children of `systemd --user`. Let me identify the exact units via cgroups.

[assistant] Both units are `Type=oneshot` (systemd won't stack them). Let me measure progression and hunt other launchers.

[assistant] Decisive: **zero syscalls in 75s** for both. Let me confirm with a stack dump and find the other launchers.

[assistant] Found the likely pattern: recursive `glob.glob("/home/turbo/**/*.db")`. Let me confirm what syscall they're actually in (zero-risk via `/proc/pid/syscall`) and check for SSHFS mounts under the walked tree.

[assistant] Critical clue: **67% of CPU time is kernel time** (stime 3959s vs utime 1908s) — that's a stat/getdents storm, not a userland loop. Let me confirm the tree being walked.

[assistant] ## Diagnostic — prolifération CPU sur turbo-MS-7C56

### 1. État actuel chiffré (14:15, 16 threads)

`/proc/loadavg` : **14.81 / 18.56 / 17.54** — redescendu des 25.41 constatés, mais toujours ~93 % de saturation.

| Script | Exemplaires | PID | Démarré | Depuis | %CPU |
|---|---|---|---|---|---|
| `jarvis-plan.py --sync` | **1** | 47356 | 12:34:14 | 1h41 | 99 % |
| `gen_sql_shortcuts.py` | **1** | 128451 | 12:41:14 | 1h34 | 99 % |
| `rdit_analysis.py` | **0** | — | — | — | — |

`rdit_analysis.py` a bien expiré tout seul (son `timeout 900`). Les 3 exemplaires de chaque script ont fondu à 1 : **il n'y a plus d'empilement**.

**Mais un nouveau foyer a pris le relais et pèse plus lourd que les trois réunis :**

```
1096648..1096653   6 × python3 moisson.py 5881238115 6   ~93 % chacun (~6 cœurs)
```
Lancés à 14:01 par `nohup` depuis un scratchpad Claude Code (`/tmp/claude-1000/-home-turbo-jarvis/4d0b99cc-.../scratchpad`), cgroup `vte-spawn-…scope` — donc **une session Claude parallèle, pas un timer**.

### 2. Qui les lance — et l'anti-réentrance

| Script | Lanceur | Fréquence | Garde |
|---|---|---|---|
| `jarvis-plan.py --sync` | `~/.config/systemd/user/jarvis-plan-refresh.timer` → `.service` → `/home/turbo/jarvis/bin/jarvis-plan-refresh:9` | `OnBootSec=3min` + `OnUnitActiveSec=20min`, `Persistent=true` | **aucune** (`flock`/`pgrep` = 0 occurrence dans les 4 fichiers) |
| `gen_sql_shortcuts.py` | `~/.config/systemd/user/biblio-rebuild.timer` → `.service` → `/home/turbo/labo/bib