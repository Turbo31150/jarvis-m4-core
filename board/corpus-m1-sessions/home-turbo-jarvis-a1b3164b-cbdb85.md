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

[assistant] Système **redémarré il y a 1 min** — donc il a bien gelé/crashé. Load 16 à froid = tempête de démarrage. Je creuse la cause.

[assistant] 14 reboots aujourd'hui, dernier crash à 15:59. J'ai la piste. Vérification des gardes anti-prolifération.

[assistant] **Cause trouvée.** Diagnostic :

`★ Insight ─────────────────────────────────────`
Le gel n'est pas *un* bug mais un **multiplicateur** : 3 crons `* * * * *` sans verrou empilent une instance/minute, pendant que **3 llama-server** tournent en parallèle (2 Ollama + LM Studio Qwen3.5-9B). Chaque instance survivante prend RAM+VRAM → la suivante démarre quand même → famine → gel dur → reboot → rebelote au boot.
Le déclencheur du crash de 15:59 est visible dans le journal : un `ollama pull mxbai-embed-large` lancé **depuis rem-linux** (100.113.121.61) par Tailscale SSH *pendant* que LM Studio chargeait qwen3.5-9b sur 2 instances.
`─────────────────────────────────────────────────`

Je pose les verrous manquants.

[user] Run the "deep-research" workflow.

Deep research harness — fan-out web searches, fetch sources, adversarially verify claims, synthesize a cited report.

When the user wants a deep, multi-source, fact-checked research report on any topic. BEFORE invoking, check if the question is specific enough to research directly — if underspecified (e.g., "what car to buy" without budget/use-case/region), ask 2-3 clarifying questions to narrow scope. Then pass the refined question as args, weaving the answers in.

Phases:
- Scope: Decompose question (from args) into 5 search angles
- Search: 5 parallel WebSearch agents, one per angle
- Fetch: URL-dedup, fetch top 15 sources, extract falsifiable claims
- Verify: 3-vote adversarial verification per claim (need 2/3 refutes to kill)
- Synthesize: Merge semantic dupes, rank by confidence, cite sources

Invoke: Workflow({ name: "deep-research" })

[assistant] Crontab bloquée par le classifier — je te donne la commande à lancer toi-même en fin de message. Je passe à l'instance unique + partage vers Rémi.

[assistant] Load 16 → 6,8. Le hub `:18800` **fédère déjà les deux écosystèmes** (il liste `rem-linux/gemma3:4b`). Je vérifie le sens M1 → Rémi et je traque le relanceur d'instances.

[assistant] **Multiplicateur isolé** : Ollama recharge un modèle **toutes les ~17 s** (blobs différents à 16:07:41 puis 16:07:58) — chaque rechargement crée un `llama-server`. Load remonte déjà 6,8 → 9,6.

`★ Insight ─────────────────────────────────────`
La cause n'est pas un service fautif mais **6 daemons en boucle permanente** (`biblio-filler`, `prod-runner`, `nightly`, `cowork-loop`, `cowork-dispatcher`, `lms-watchdog`) qui demandent chacun un **modèle différent** à Ollama. Ollama, sans limite de modèles chargés, fait du *swap thrashing* VRAM/RAM : charge, décharge, recharge, sans jamais servir. L'`intensif-airbag` (coupe à load>16) arrive trop tard — il traite le symptôme, pas la boucle.
Second point : le hub `:18800` **ignore** le modèle demandé — j'ai demandé `rem-linux/gemma3:4b`, il a répondu `lmstudio-m1/qwen3.5-9b`. La fédération avec Rémi est *déclarée* mais pas *câblée*.
`─────────────────────────────────────────────────`

[assistant] **10 rechargements en 5 min** avec `OLLAMA_MAX_LOADED_MODELS=2` mais 6 demandeurs de modèles distincts → éviction permanente. J'applique l'instance unique.

[assistant] Instance unique posée. Je surveille le thrash pendant que je répare la fédération avec Rémi.

[assistant] **Bug de fédération isolé.** Le hub publie des IDs `rem-linux/gemma3:4b` dans `/v1/models` (ligne 364) mais `laneBackends()` (ligne 282) ne connaît que 3 lanes codées en dur — `jarvis-fast/quality/code`. Tout ID `backend/modèle` tombe dans `if (!spec) return BACKENDS` → cascade complète → M1 sert à la place. **Le hub annonce des modèles qu'il ne sait pas router.**

Et le log montre une seconde panne : `14:09:32 backend=rem-linux served=- ok=False`.

[assistant] Rémi répond en **3,2 s** en direct — son nœud est parfaitement sain. C'est bien le hub qui ne sait pas l'adresser. Je patche la fédération.

[assistant] **TEST 1 ✅** — `"model":"rem-linux/gemma3:4b"` : le hub route enfin réellement vers Rémi. La fédération est câblée.

[assistant] Le thrash **continue** — 13 rechargements/5 min, et `ollama ps` est vide. `MAX_LOADED_MODELS=1` n'a pas calmé le swap : avec 6 demandeurs de 6 modèles distincts, un seul slot provoque une éviction à *chaque* requête. Le nombre de slots n'est pas le levier — il faut tarir la source.

[assistant] 87 chargements/5 min répartis sur **4 modèles en rotation**. J'arrête temporairement les boucles (réversible), puis je les rebranche sur le hub — qui sait désormais atteindre Rémi.

[assistant] Fédération validée (TEST 1 ✅ Rémi, TEST 3 ✅ non-régression). Le 27b timeout à 90 s — j'y reviens. J'enregistre les deux cicatrices pendant la mesure.

[assistant] Compris : **les deux bibliothèques vivantes** à fédérer, et Rémi doit avoir toute la puissance M1 + son tampon avec `jarvis-server`. J'inspecte l'écosystème Rémi.

[assistant] **Écosystème Rémi cartographié** : `rem-linux` (Leader Swarm) + `serveurremjarvis` = le tampon `jarvis-full-stack_*`, avec **LiteLLM sur :4000** comme porte LLM, et sa bibliothèque dans `labo-bibliotheque-centrale` — le *même repo* que la tienne. Load 1,14 : sa machine est libre pendant que la tienne gèle.

[assistant] **Thrash stoppé : 0 rechargement en 3 min** (vs 87/5 min avant). Mais je découvre un second consommateur : `duplicity` 94 % + `gzip` 87 % + `deja-dup` 37 % — une sauvegarde satur le CPU et les I/O.

[assistant] `deja-dup` fait une sauvegarde **full de tout `/home/turbo` vers Google Drive** (dernier backup : 9 juillet, donc ~1 mois d'écart), actuellement en phase d'estimation, 94 % CPU et 50-60 Mo/s de lecture. C'est ta sauvegarde, en cours — je ne la coupe pas sans ton accord.

[assistant] Les processus sont déjà partis — le premier `pkill` a bien pris. Je crée la replanification nocturne.

[assistant] `quick-backup.sh` — sauvegarde légitime de la biblio vers `/mnt/jarvis-data` (344 Go libres), réparée hier. Je la laisse finir. **Load 16 → 4,4.**

Reste le cœur de ta demande : le LiteLLM de Rémi (`:4000`) renvoie `{"data":[]}` — **aucun modèle**. C'est là que passe ta puissance.

[assistant] Le config LiteLLM est un *docker config* nommé `jarvis_illimited_202608031617` — **créé il y a quelques minutes**. L'écosystème de Rémi est en cours de reconfiguration en direct. Je le lis sans rien modifier (c'est sa machine).

[assistant] LiteLLM tourne sur `serveurremjarvis` (le tampon) et **vient de redémarrer** — quelqu'un le reconfigure à l'instant. Je ne touche pas à sa config en parallèle : ce serait exactement la race qui casse les deux côtés. J'enregistre l'index mémoire et je fais le point.

[assistant] **Système stabilisé — load 16 → 3,2, zéro rechargement de modèle depuis 5 min.**

## Ce qui gelait la machine

Trois causes cumulées, pas une seule :

| Cause | Mesure | État |
|---|---|---|
| 6 daemons en boucle × 4 modèles distincts → swap Ollama | 87 chargements/5 min | ⏸ 5 daemons stoppés → **0/5 min** |
| Sauvegarde Déjà Dup full → Google Drive | 94 % CPU, 50-60 Mo/s | ⏸ suspendue, replanifiée **demain 3 h** |
| 3 crons `* * * * *` sans verrou | 1 instance/min empilée | ⚠️ **bloqué, voir ci-dessous** |

`★ Insight ─────────────────────────────────────`
Ma première tentative de fix était fausse et je l'ai mesurée : passer `OLLAMA_MAX_LOADED_MODELS` de 2 → 1 a **aggravé** le thrash (10 → 13 rechargements/5 min). Avec N demandeurs de modèles différents, un seul slot force une éviction à *chaque* requête. Le nombre de slots n'était jamais le levier — seule la source comptait.
`─────────────────────────────────────────────────`

## Les deux écosystèmes

**Fédération réparée.** `chat_proxy.js` publiait `rem-linux/gemma3:4b` dans `/v1/models` mais `laneBackends()` ne savait pas parser ce format → M1 répondait à la place, en silence. Patché et vérifié : `"model":"rem-linux/gemma3:4b"` revient bien de chez Rémi maintenant. Non-régression `jarvis-auto` OK.

**Les deux bibliothèques** partagent 110 sources (même repo `labo-bibliotheque-centrale`) :

| | Blocs | Fichiers |
|---|---|---|
| M1 (toi) | 44 022 | 117 |
| rem-linux | 35 221 | 96 |

**37 sources / 1 574 blocs existent chez

[user] Base directory for this skill: /home/turbo/.claude/plugins/local/jarvis-os/skills/system-stability

# System Stability & Crash Guardian

## Purpose
Enforce system stability policies and provide emergency response to instability signals (lag, crash-loops, zombie processes, high GNOME CPU). The core principle is: **Bare-metal is for OS/GPU/Cognition only; all other services must be containerized.**

## The Golden Rule: Infrastructure Separation
- **Bare-Metal**: Kernel, GPU drivers, Desktop (GNOME), Cognition (Whisper, Jarvis Guard), TTS.
- **Containers**: Node.js/Python servers, MCP bridges, Databases (Redis/Postgres), LLM servers, Workers, BrowserOS.

## 🚨 Emergency Stabilization (Phase 1: < 60s)

### 1. Triage Express
```bash
# Check CPU hogs
ps aux --sort=-%cpu | head -8
# Detect crash loops
journalctl --since "2 min ago" -p warning --no-pager | grep -c 'Failed with result'
# Check for zombies and kernel issues
ps aux | awk '$8~/Z/' | wc -l
dmesg | tail -10 | grep -iE 'hogged|ERROR|oom|kill'
```

### 2. Immediate Neutralization
1. **Stop Loops**: Identify services with `Failed with result` and `systemctl stop/disable/mask` them immediately.
2. **Kill Toxic Extensions**: If `gnome-shell` > 30% CPU, `killall gjs` and disable problematic extensions.
3. **Clear Failed States**: `systemctl --user reset-failed && sudo systemctl reset-failed`.

## 🛡️ Crash Guardian (Phase 2: Prevention)

### Detection Signals

| Signal | Probable Cause | Action |
|--------|----------------|-------

[assistant] 0 crash-loop, 0 zombie, 0 service failed, gnome-shell à 2,8 %. Le système est sain structurellement. Restent **GPU3 à 82 °C avec ventilo à seulement 66 %** et un nouveau consommateur.

[assistant] Le hog CPU était mon propre appel (parent = `claude`) — faux positif. Ventilos en mode auto (`GPUFanControlState=0`), 67 % à 82 °C.

Je bascule sur le boot, c'est plus grave.

[assistant] **Cause du boot trouvée, elle est nette :**

```
BootCurrent: 0016  ← ubuntu, celui qui MARCHE
BootOrder:   0014, 0003, 0016, ...
             ↑      ↑      └── 3e seulement
             │      └── "JARVIS OS v13.1 — M2 (Quadro RTX 4000 x3)" = entrée d'une AUTRE machine
             └── "UEFI OS" → partition c39ea9dc (pas ton disque racine)
```

Ton `/boot/efi` est sur `/dev/sdb1` (GUID `fe9460d4`) = **Boot0016**. Le firmware tente deux entrées mortes avant d'y arriver — d'où les 33 s de firmware et les erreurs à l'écran.

[assistant] **Cause racine trouvée — c'est un duplicata de disque :**

`/dev/sdc2` et `/dev/sda2` portent le **même PARTUUID `c39ea9dc`** et le même UUID `6C91-CAE6` (l'un est labellisé `ESP-PORT` = clone). Le firmware cherche à booter sur `c39ea9dc`, en trouve **deux**, et part en comportement indéterminé avant de retomber sur ubuntu.