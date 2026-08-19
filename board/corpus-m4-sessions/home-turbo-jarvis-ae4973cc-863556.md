[user] repriiise lecture sql sql3  postgre bibliotheque vivante n8n container démarre et syncronise m6

[assistant] Reprise en cours : je sonde l'état réel (SQLite, Postgres cmdlib, container n8n, liaison M6) avant d'agir, plus l'alerte FAILED_SVC signalée par le hook.

[user] Base directory for this skill: /home/turbo/.claude/skills/run-m6-share

# run-m6-share — M6 en câble direct comme nœud de compute partagé

M6 est un nœud du cluster raccordé à **M1 par câble Ethernet direct** (partage réseau
GNOME/ICS : M1 = passerelle `enxf8e43b9b67d4` 10.42.0.1/24, M6 = `enp3s0` **10.42.0.230**).
Ce n'est pas une GUI : le « pilotage » = un **driver bash** qui vérifie la connectivité,
les endpoints LLM, l'enregistrement dans le routeur, et fait une inférence réelle.

Chemins relatifs à `/home/turbo/jarvis/`. Le driver vit dans le dossier du skill.

## Piège central (à connaître avant tout)
**L'ICMP est filtré sur M6** → `ping 10.42.0.230` échoue *à tort*. M6 est joignable :
vérifier via **ARP** (`ip neigh`) ou **TCP** (`/dev/tcp/.../22`), jamais via ping.

## Run (chemin agent) — le driver

```bash
cd /home/turbo/jarvis/.claude/skills/run-m6-share
./driver.sh check     # connectivité + endpoints + état config (lecture seule)
./driver.sh smoke     # inférence réelle : Ollama M6 + hub :18800
./driver.sh register  # (ré)enregistre les providers ollama-m6 + lmstudio-m6 (backup auto) + recharge le hub
./driver.sh all       # check + register + smoke
```

`./driver.sh check` attendu (tout vert) :
```
== Lien câble direct → M6 (10.42.0.230)  [ICMP filtré : on teste ARP+TCP, pas ping] ==
  ✓ ARP REACHABLE (44:8a:5b:a2:35:94)
  ✓ SSH ok (alias 'm6' → M6)
== Backends LLM joignables depuis M1 ==
  ✓ port 1234 ouvert   ✓ port 11434 ouvert   ✓ port 22 ouvert
  ✓ LM Studi

[user] Base directory for this skill: /home/turbo/jarvis/.claude/skills/run-board

# board — conseil d'experts local et souverain

`~/jarvis/board/` est un **board d'experts** : une question entre, N experts du domaine
répondent chacun avec **sa** grille de lecture (`lens`) **en citant** des extraits d'un
corpus indexé, puis un arbitre synthétise les accords et les divergences.

**Règle fondatrice : une réponse sans citation est invalide.** Ce n'est pas une consigne
qu'on espère voir respectée par le modèle — c'est une contrainte **vérifiable en SQL** :
la vue `answers_sans_citation` liste, à tout instant, les réponses à rejeter.

Python stdlib seule. SQLite + FTS5 (BM25 lexical) **et** embeddings BLOB float32
dimension 768, fusionnés par rang (RRF) dans `retrieve()`. Inférence et vectorisation en
local sur LM Studio `127.0.0.1:1234`. Rien ne sort de la machine, 0 token payant.

## À lancer en premier

```bash
~/jarvis/.claude/skills/run-board/driver.sh smoke
```

~30 s, **zéro appel LLM** (le seul contact réseau est un `GET /v1/models` avec timeout court).
Sortie réelle du 2026-08-06 :

```
board — smoke (0 token LLM)
  base : /home/turbo/jarvis/board/board.db

1. syntaxe
  ✓ board.py se parse (ast)
  ✓ board_schema.sql s'applique sur une base neuve

2. structure (7 tables + chunks_fts + vue)
  ✓ les 7 tables sont la : domains experts sources chunks queries answers citations
  ✓ table FTS5 chunks_fts presente
  ✓ vue answers_sans_citation presente
  ✓ 3 triggers de synchronisation 

[assistant] Tout est en place. Récapitulatif de la session :

**Reprise (demande initiale)**
- **SQLite** : lecture OK — `jarvis_master.db` 319 agents (l'erreur d'E/S initiale venait d'un `wal_checkpoint` interdit en mode ro, pas du disque), `jarvis_logs.db` 464 runs.
- **Postgres bibliothèque vivante** : `jv-infra-biblio-db` healthy, **145 665 commandes** lues dans `cmdlib` (user `cmduser`).
- **n8n** : container Up, répond 200 sur :5678 et :9742.
- **M6** : SSH OK, Ollama 15 modèles, providers `ollama-m6`/`lmstudio-m6` enregistrés, hub :18800 rechargé et répond. LM Studio côté M6 est éteint (Ollama assure le relais).
- `gpu-boost.service` en failed : c'est le **verrou GPU qui refuse** `nvidia-smi -pm 1` sans code de déverrouillage — comportement voulu, non touché.

**3080 réactivée en CUDA** — cause racine : `~/.pam_environment` figeait `CUDA_VISIBLE_DEVICES=0,1,2,3` au login (la 3080 = index 4 était exclue ; Vulkan l'ignorait, d'où sa visibilité en Vulkan seulement). Corrigé et **verrouillé sur 5 sources cohérentes** : `.pam_environment`, `environment.d/cuda.conf`, et les 3 units systemd (`lmstudio`, `lmstudio-server`, `lms-headless`) alignées sur les **5 UUID GPU** (robuste au remap d'index). Preuve : le backend llama.cpp-cuda12 occupe la 3080, énumération CUDA = 5 cartes.

**Board** : smoke vert (48 experts, 23 tests). La délibération a tenu la règle de citation, mais 3 experts sont tombés pendant que LM Studio rechargeait — et le corpus `cluster-m1` contient des fiches à l'ancienne

[user] # /skillmp — skills de l'écosystème JARVIS

Argument reçu : ``

Deux CLI, une seule racine durable : `~/labo/bibliotheque/skillsmp`.

## 1. Catalogue — `~/jarvis/bin/skillmp.py`

| Intention | Commande |
|---|---|
| chercher | `skillmp.py search <mots> -n 20` |
| détail + code source | `skillmp.py show <slug>` |
| installer | `skillmp.py install <slug> --cible both` |
| lot écosystème JARVIS | `skillmp.py sync-jarvis --seuil 2` |
| lister l'installé | `skillmp.py installed` |
| retirer | `skillmp.py uninstall <slug>` ou `--tout` |
| état du catalogue | `skillmp.py stats` |

## 2. Pipeline d'ingestion — `~/jarvis/bin/skillmp-pipeline.py`

Compacte 6 étages derrière une façade unique :

| Étage | Rôle |
|---|---|
| `expansion` | découvre les skills **hors sitemap** (pages créateur) |
| `catalogue` | fiches JSON-LD des pages skill |
| `source` | code source réel des `SKILL.md` depuis GitHub (6 workers) |
| `site` | reste du site : pages, docs, métiers, créateurs, dépôts |
| `fr` | mots-clés **français** via le cluster local (0 token) |
| `boucle` | injection toutes les 10 min + classification + sync final |

| Intention | Commande |
|---|---|
| état + volumes | `skillmp-pipeline.py status` |
| démarrer | `skillmp-pipeline.py start [étage...]` |
| arrêter | `skillmp-pipeline.py stop [étage...]` |
| injecter maintenant | `skillmp-pipeline.py inject` |
| journal | `skillmp-pipeline.py logs <étage>` |

Sans argument → `stats` puis `status`, et proposer une recherche.

## Cibles d'éc

[assistant] État `/skillmp` :

**Catalogue** — **193 277 skills** (+10k depuis hier), 25 533 dépôts, 17 581 auteurs. Mais seulement **20 099 avec code source** (10,4 % installables) et **6 008 avec mots-clés FR** (3,1 % routables via `bloc.sh`).

**Pipeline** — un seul étage tourne :

| Étage | État | Volume |
|---|---|---|
| catalogue | **actif** (PID 28337) | 33 101 fiches |
| expansion | arrêté | 65 946 découverts |
| source | arrêté | 837 186 fichiers |
| site / fr / boucle | arrêtés | — |

Le goulot est clair : la moisson de fiches avance mais **`source` et `fr` sont arrêtés**, donc le stock installable et routable ne progresse plus. La `boucle` (injection SQLite/Postgres toutes les 10 min) est aussi coupée — le catalogue s'accumule sans se déverser dans la bibliothèque vivante.

Options :
- `skillmp-pipeline.py start source fr boucle` — relancer la collecte de code + mots-clés FR + injection (0 token, mais charge réseau/GitHub) ; attention au **disque à 88 %**, la collecte source est volumineuse.
- `skillmp.py search <mots>` — chercher un skill précis.
- `skillmp.py sync-jarvis --seuil 2` — installer le lot écosystème JARVIS noté.

Je te recommande la relance `source fr boucle` mais avec le disque à 88 % je préfère ton feu vert — ou dis-moi quoi chercher.

[user] Base directory for this skill: /home/turbo/jarvis/.claude/skills/run-jarvis-autochain

# run-jarvis-autochain — fermer la boucle détection → action

Les 9 hooks `UserPromptSubmit` injectent **4 139 octets ≈ 1 034 tokens par
message** (mesuré le 2026-08-06) : familles détectées, blocs routés, commande
`skillmp cascade` toute prête. Puis ils s'arrêtent. **Aucun n'exécute quoi que
ce soit.** Sans terminus, chaque message paie le diagnostic sans jamais
l'encaisser — c'est ça, brûler du token pour rien.

`bin/jarvis-autochain.sh` est ce terminus. Une intention entre, cinq étapes
s'enchaînent sans re-délibérer, zéro appel LLM : SQL, grep, arithmétique.

**Tous les chemins sont relatifs à `/home/turbo/jarvis/`.**

## Run — commencer TOUJOURS par le smoke

```bash
bash .claude/skills/run-jarvis-autochain/driver.sh smoke
```

9 contrôles, ~90 s, aucun token. Sortie obtenue le 2026-08-06 (verbatim) :

```
3. le mode par défaut n'écrit RIEN
  ✓ tasks inchangé (2144628) — la simulation ne mute pas la base
5. VERROU RÉEL — deux chaînes simultanées
  ✓ seconde chaîne refusée — flock -n tient réellement
  ✓ verrou libéré à la fin de la chaîne de fond
6. RÉGRESSION — classification par sous-chaîne
  ✓ 4/4 commandes classées correctement (frontières de mot)
verdict
  tout vert — aucun token dépensé
```

| Commande | Coût | Effet |
|---|---|---|
| `driver.sh smoke` | ~90 s, 0 token | syntaxe, quoting, non-mutation, propreté, **verrou réel**, non-régression sous-chaîne, journal |
| `driver.sh d

[assistant] Skill autochain invoqué sans intention : je commence par le smoke (règle du skill), puis l'état de la file.

[assistant] Autochain **tout vert** — les 9 contrôles passent (verrou réel tenu, non-mutation vérifiée, classification par frontières de mot OK, 0 token dépensé).

État de la file dynamique :

| Statut | Tâches |
|---|---|
| pending | 186 |
| to_validate | 386 |
| in_progress / running | 9 |
| done | 2 148 442 |

Le journal montre les dernières chaînes : projections biblio+simul hier 23h, trois passes `cascade-massive` cette nuit (hub+lms+ollama), micro-actions skills-seo/blog-cluster.

Le terminus est opérationnel et prêt à encaisser une intention. Deux candidates héritées de la session, si tu veux les enchaîner :
- `driver.sh run "ré-ingérer corpus GPU topologie board cluster-m1"` — corrige les fiches périmées que la Sondeuse a citées (elle croit la 3080 en index 3) ;
- `driver.sh dry "libérer espace disque 88%"` — projection d'abord (le nettoyage est classé destructif, la lentille `chronologique` l'exclura du dispatch auto).

Donne-moi l'intention (ou `dry` pour simuler sans écrire) et je lance.

[user] Base directory for this skill: /tmp/claude-1000/bundled-skills/2.1.220/dd6eda29e61eb4524b1717c6d38132f6/run

**Running means launching the actual app and interacting with it** —
not the test suite, not an `import` of an internal function and a
`console.log`. The app as a user (human or programmatic) would meet
it: the CLI at its command, the server at its socket, the GUI at its
window.

## First: does a project skill already cover this?

A project skill that launches this app is the repo's verified path —
its author already cold-started from a Linux container and committed
what worked: the exact `apt-get` line, the env vars, the patches, the
driver. Use it instead of rediscovering.

```bash
d=$PWD; while :; do
  grep -Hm1 '^description:' "$d"/.claude/skills/*/SKILL.md 2>/dev/null
  [ -e "$d/.git" ] || [ "$d" = / ] && break
  d=$(dirname "$d")
done
```

- **One describes launching/driving this app** → read that SKILL.md
  and follow it verbatim. Don't paraphrase; don't skip the patches.
- **Mega-repo, several plausible, no clear match** → ask the user
  which unit to run.
- **Stale** (fails on mechanics unrelated to your task) → tell the
  user; offer to refresh it via `/run-skill-generator`.
- **Nothing about running** → fall back to the patterns below.

## Otherwise: match the shape, use the pattern

Pick the row closest to your project. Each example walks through
launch + first interaction; ignore any trailing "write the skill"
section — you're using the recipe, not authori

[user] Base directory for this skill: /home/turbo/.claude/skills/run-jarvis-planning-widget

# run-jarvis-planning-widget

Widget bureau JARVIS **« Ce que le système fait »** — app hybride :

- **Backend** `bin/jarvis-planning-widget.py` : serveur HTTP stdlib (port 8899),
  sert `/` (dashboard HTML auto-refresh) et `/data` (JSON). 5 panneaux, tout en
  **lecture seule 0-token** : file de tâches (`jarvis_master.db`), routage LLM
  (`llm_cascade_log.jsonl`, canaux de sortie), workflows **n8n** auto-déclenchés
  (`~/.n8n/database.sqlite`), GPU thermique (`nvidia-smi`), timers systemd `--user`.
  Un endpoint `POST /trigger` (liste blanche de services, durci CSRF/DNS-rebind).
- **Fenêtre** `bin/jarvis-widget-desktop.py` : affiche ce dashboard dans une
  fenêtre WebKitGTK sans bordure, `keep_below` (widget de bureau). Le rafraîchissement
  est **piloté depuis Python** (GLib) car WebKit gèle `setInterval` en arrière-plan.

## Run (agent path) — `driver.sh` (chemin PRINCIPAL)

En prod, le backend `:8899` et la fenêtre bureau tournent **déjà** (deux services
`--user`, plus bas). Le harnais **`driver.sh`** pilote cette instance vivante : il
s'assure du backend, hit `/data` (valide les 6 panneaux), puis screenshotte la
**vraie** fenêtre X11 par son ID → `assets/widget_live.png`. **Zéro charge GPU**
(`nvidia-smi` est lu par le backend, le screenshot est une capture de pixmap X11).

```bash
cd /home/turbo/jarvis
DISPLAY=:0 bash .claude/skills/run-jarvis-planning-widget/driver.sh all
DISPLAY=:0 b

[assistant] Fait — les deux fronts sont verts.

**Widget planning :8899** (piloté, pas juste lancé) :
- Backend déjà actif, `/data` sert les **6 panneaux** ✅.
- Screenshot frais de la vraie fenêtre X11 (01:00:56, capture par ID) : horloge vivante, compte à rebours à 00:02, prochain auto-déclencheur `widget-s9-reverse.service`, KPI (2 148 443 tâches faites, 190 en file, 741/h), panneau agents (1423 indexés).
- Signaux à noter : **GPU 2 et 3 à 87 °C** (proche du seuil 89 °C où la vectorisation s'auto-suspend ; conforme à ta règle « tous en ligne » mais à surveiller pendant la moisson) ; routing fallback 57 % sur fenêtre courte — artefact attendu des redémarrages LM Studio de ce soir, pas un bug de routage.

**Moisson massive multi-pôle relancée** — les 6 étages tournent désormais en parallèle :

| Étage | État |
|---|---|
| expansion | démarré (découverte hors sitemap) |
| catalogue | déjà actif |
| source | démarré (code SKILL.md, 6 workers GitHub) |
| site | démarré |
| fr | démarré (mots-clés FR, cluster local 0-token) |
| boucle | démarré (injection SQLite/Postgres toutes les 10 min) |

Point de vigilance : disque à **88 %** — l'étage `source` est le plus gourmand. Un `skillmp-pipeline.py status` dans une heure dira si le stock installable (20 099 avec code) et routable FR (6 008) décolle ; si le disque approche 92 %, je couperai `source` en priorité.

[user] lis le ploannihngf widget application traite toute les tache en attente et booste le massivement avbec traitementy massifd

[assistant] Je lis d'abord la file réelle du widget (190 pending + 386 to_validate), puis je regarde l'outil de drainage massif existant avant de le booster.

[assistant] Le traitement massif est lancé et il consomme réellement la file :

**Lecture du planning widget** — file réelle : 177 pending, 394 to_validate, 9 actives. Le drainer amont (`jarvis-backlog-drainer.py`) s'auto-régule déjà (consigne pending≈100), le goulot était **l'exécuteur** : `scripts/jarvis-prod-runner.py`, bridé à `MAX_PARALLEL = 3` — un réglage daté de l'époque où LM Studio servait en série.

**Boost appliqué :**
- `MAX_PARALLEL` **3 → 8** (borne = la file du hub :18800, 5 slots + 3 en attente ; qwen sert désormais 12 prédictions parallèles derrière, il n'est plus le facteur limitant). Le commentaire garde l'historique du diag qui interdisait 12.
- **Boucle massive en fond** (`--limit 200` par passe, mode LOOP, tâche bpjsm1485) en plus de la passe `--once --limit 50` déjà en cours.

**Preuve que ça draine** (2 min après lancement) : passe de 173 tâches engagée, 8 dispatchs simultanés vers les exécuteurs par famille (`prod-exec`, `executor-mail`, `executor-github`, `executor-openclaw`, `executor-research`…), premier ✅ en 1 s (T2190982, pipeline 5/5), file **177 → 164 pending, 12 running**.

Garde-fous actifs pendant le rush : CPU < 90 %, RAM min, timeout 300 s/tâche — et la moisson skillmp continue en parallèle. Deux points que je surveille : GPU 2/3 à 87 °C sous cette double charge, et la boucle notifiera à la fin ; si le hub commence à rejeter en « surcharge », je redescendrai à 6.

[user] # /skillmp — skills de l'écosystème JARVIS

Argument reçu : ``

Deux CLI, une seule racine durable : `~/labo/bibliotheque/skillsmp`.

## 1. Catalogue — `~/jarvis/bin/skillmp.py`

| Intention | Commande |
|---|---|
| chercher | `skillmp.py search <mots> -n 20` |
| détail + code source | `skillmp.py show <slug>` |
| installer | `skillmp.py install <slug> --cible both` |
| lot écosystème JARVIS | `skillmp.py sync-jarvis --seuil 2` |
| lister l'installé | `skillmp.py installed` |
| retirer | `skillmp.py uninstall <slug>` ou `--tout` |
| état du catalogue | `skillmp.py stats` |

## 2. Pipeline d'ingestion — `~/jarvis/bin/skillmp-pipeline.py`

Compacte 6 étages derrière une façade unique :

| Étage | Rôle |
|---|---|
| `expansion` | découvre les skills **hors sitemap** (pages créateur) |
| `catalogue` | fiches JSON-LD des pages skill |
| `source` | code source réel des `SKILL.md` depuis GitHub (6 workers) |
| `site` | reste du site : pages, docs, métiers, créateurs, dépôts |
| `fr` | mots-clés **français** via le cluster local (0 token) |
| `boucle` | injection toutes les 10 min + classification + sync final |

| Intention | Commande |
|---|---|
| état + volumes | `skillmp-pipeline.py status` |
| démarrer | `skillmp-pipeline.py start [étage...]` |
| arrêter | `skillmp-pipeline.py stop [étage...]` |
| injecter maintenant | `skillmp-pipeline.py inject` |
| journal | `skillmp-pipeline.py logs <étage>` |

Sans argument → `stats` puis `status`, et proposer une recherche.

## Cibles d'éc

[assistant] État `/skillmp` complet :

**Catalogue** — 193 277 skills · 20 099 avec code source · **6 072 avec mots-clés FR** (+64 depuis la relance de l'étage `fr` il y a une heure — il tourne).

**Pipeline** :

| Étage | État | Note |
|---|---|---|
| expansion | actif | 65 946 découverts hors sitemap |
| catalogue | **relancé cadence 2,5 s** | le site renvoyait des **429 en masse** (9 298 échecs sur la passe de 13 200) — le crawl trop agressif ne récoltait plus rien |
| source | terminé | pas mort : **travail épuisé** — 4 212 dépôts faits, 105 555 fichiers récoltés ; il repartira quand expansion/catalogue apporteront de nouvelles cibles |
| site | terminé | 7 525 pages, plus rien à traiter |
| fr | actif | mots-clés FR au fil de l'eau (cluster local) |
| boucle | actif | injection SQLite/Postgres toutes les 10 min |

**Disque** : 88 % stable (105 Go libres) — la moisson n'a pas fait bouger l'aiguille pour l'instant.

L'action utile du tour : l'étage catalogue insistait à cadence pleine contre un serveur qui refusait (throttling 429) — je l'ai redémarré avec `ASPIRE_DELAY=2.5`, le levier prévu par le moissonneur pour ce cas précis. Moins de requêtes/s, mais un taux d'échec qui devrait s'effondrer.

En parallèle, le traitement massif de la file continue (prod-runner ×8). Si tu veux exploiter le catalogue : `skillmp.py search <mots>` ou `sync-jarvis --seuil 2` pour le lot écosystème.

[user] Base directory for this skill: /home/turbo/.claude/skills/cli_skill_audit

# cli_skill_audit

Moteur d'audit local M1 (AXE 1/3). Pur bash/sqlite3/systemctl, 0 API.

## Trigger keywords
audit,analyse,rapport

## Run (agent path)
```bash
bash .claude/skills/cli_skill_audit/driver.sh
```
Sortie réelle de la dernière exécution :
```
[driver] report : /home/turbo/jarvis/audit/audit-local-20260605-1654.md
[driver] secrets: CLEAN (rc=0)
[driver] logged : skill_invocations row id 17
```

## Ce que le driver produit
1. **Services systemd — DEUX scopes** : `systemctl` (system) ET `systemctl --user`. Leçon clé : `jarvis-autoheal` / `jarvis-share` / `jarvis-cluster-mount` sont en scope user → faux négatifs si on n'interroge pas `--user`. Compte actifs/inactifs/failed par scope.
2. **Skills** : `~/.claude/skills/*/SKILL.md` + skills `run-*` du repo `/home/turbo/jarvis/.claude/skills`.
3. **Triggers** : parse `run-jarvis-autoheal/skill-triggers.json`, compte les skills couverts, liste les `run-*` sans trigger.
4. **Secrets** : exécute `/home/turbo/jarvis/bin/scan-secrets.sh`, reporte verdict + rc.

## Inspecter le dernier rapport
```bash
ls -t /home/turbo/jarvis/audit/audit-local-*.md | head -1 | xargs head -45
```

## Vérifier le log d'invocation
```bash
sqlite3 -header -column /home/turbo/jarvis/db/cli_history.db \
  "SELECT id, skill_name, invoked_at, outcome, trigger_phrase FROM skill_invocations WHERE skill_name='cli_skill_audit' ORDER BY id DESC LIMIT 1;"
```

## Notes d'implémentati

[assistant] En attendant le retour du chargement hermes (passé en fond), voici le bilan de l'audit :

**Audit local M1** (`audit-local-20260807-0106.md`) :

| Volet | Résultat |
|---|---|
| Services system | 23 actifs · **1 failed** : `gpu-boost` — cas connu, bloqué volontairement par le verrou GPU (demande un code de déverrouillage), pas une panne |
| Services user | 28 actifs · **1 failed** : `jarvis-lms-qwen-warm` — voir ci-dessous |
| Skills | 463 installés + 53 `run-*` repo |
| Triggers | 57 couverts, **tous les `run-*` ont un trigger** |
| Secrets | **CLEAN** (rc=0, motifs connus sur HEAD) |

**Le vrai incident : `jarvis-lms-qwen-warm`.** Le keep-warm garantit un plancher de modèles chargés dans LM Studio. Le journal montre : qwen OK (il ne touche pas à mon tuning 32k/12 — il ne recharge que si le modèle est *absent*, garde `exit 0` si déjà bon), mais **hermes-2-pro-mistral-7b a échoué à recharger** — c'est le modèle qui avait déjà « disparu 4 fois » le 2026-08-06 (évincé sous famine VRAM). Nos redémarrages LM Studio de ce soir l'ont déchargé, et sa relève échoue.

Le chargement manuel de hermes tourne en fond (bnruhh3qh) — son verdict dira si c'est un problème de VRAM (peu probable, ~19 Go libres), d'identifiant de modèle, ou un timeout. Disque à noter : **89 %** (+1 point depuis le début de session, la moisson et les résultats de tâches écrivent). Je reviens dessus dès que le fond répond.

[assistant] Le keep-warm est reparti proprement (« Finished », plus de failed) et le patch a tenu sa promesse :

**Réglé :**
- **hermes rechargé et stable** : 4,14 Go, ctx 4096, TTL 24 h — le plancher bi-modèle est rétabli. Cause racine du SIGABRT : depuis qwen 32k/12, les 1660S n'ont plus ~1 Go libre et un split tensor plein abort à 74 % du chargement. Le keep-warm recharge désormais les modèles plancher avec `--gpu 0.5 --ctx 4096` (surchargeable par `AUTRES_GPU`/`AUTRES_CTX`) — la prochaine éviction ne boucle plus sur un échec.
- **Conflit de consigne désamorcé** : le script visait `16384/2` en dur (époque mono-GPU/GNOME) et aurait **déchargé qwen en pleine génération** pour l'y ramener. Consigne alignée : `WANT_CTX=32768 / WANT_PAR=12`, surchargeable, avec commentaire d'avertissement.

**Découverte au passage :** qwen tourne actuellement en **8192/4/TTL 1 h** — un rechargement JIT à la config par défaut (probablement quand le crash d'hermes a fait tomber le moteur, puis une requête du prod-runner l'a relancé). Le keep-warm a correctement **reporté** son rechargement (« qwen en cours de generation → reload REPORTÉ ») pour ne pas couper le traitement massif en vol. Le tick de 2 min le remontera à 32k/12 à la première fenêtre d'inactivité — comportement voulu, rien à forcer.

État final : `gpu-boost` reste le seul failed (verrou GPU, volontaire), secrets CLEAN, 463 skills, triggers complets. Le prod-runner ×8 et la moisson continuent de tourner pendant ce temps.

[user] # /skillmp — skills de l'écosystème JARVIS

Argument reçu : ``

Deux CLI, une seule racine durable : `~/labo/bibliotheque/skillsmp`.

## 1. Catalogue — `~/jarvis/bin/skillmp.py`

| Intention | Commande |
|---|---|
| chercher | `skillmp.py search <mots> -n 20` |
| détail + code source | `skillmp.py show <slug>` |
| installer | `skillmp.py install <slug> --cible both` |
| lot écosystème JARVIS | `skillmp.py sync-jarvis --seuil 2` |
| lister l'installé | `skillmp.py installed` |
| retirer | `skillmp.py uninstall <slug>` ou `--tout` |
| état du catalogue | `skillmp.py stats` |

## 2. Pipeline d'ingestion — `~/jarvis/bin/skillmp-pipeline.py`

Compacte 6 étages derrière une façade unique :

| Étage | Rôle |
|---|---|
| `expansion` | découvre les skills **hors sitemap** (pages créateur) |
| `catalogue` | fiches JSON-LD des pages skill |
| `source` | code source réel des `SKILL.md` depuis GitHub (6 workers) |
| `site` | reste du site : pages, docs, métiers, créateurs, dépôts |
| `fr` | mots-clés **français** via le cluster local (0 token) |
| `boucle` | injection toutes les 10 min + classification + sync final |

| Intention | Commande |
|---|---|
| état + volumes | `skillmp-pipeline.py status` |
| démarrer | `skillmp-pipeline.py start [étage...]` |
| arrêter | `skillmp-pipeline.py stop [étage...]` |
| injecter maintenant | `skillmp-pipeline.py inject` |
| journal | `skillmp-pipeline.py logs <étage>` |

Sans argument → `stats` puis `status`, et proposer une recherche.

## Cibles d'éc

[assistant] La moisson respire mieux depuis le passage à cadence 2,5 s :

| Étage | Progression | Note |
|---|---|---|
| catalogue | 1 600/31 553 fiches, **ok=1 322 · ko=278** | taux d'échec effondré : **70 % → 17 %** depuis l'anti-429 — le ralentissement rapporte plus que l'insistance |
| expansion | **TERMINÉ** — 5 000 créateurs parcourus, 65 857 skills découverts | le plafond sitemap est atteint ; il repartira quand de nouvelles pages créateur apparaîtront |
| fr | +350 enrichis ce run (Gemini 173 · OL1 177) | le duo web/local se partage la charge à ~50/50 |
| boucle | injection toutes les 10 min | déversement continu vers SQLite/Postgres/BLOCS-INDEX |

Les erreurs résiduelles sont des `urlopen` ponctuels sur des pages créateur, plus le tapis de 429 d'avant.

Trajectoire : ~31 500 fiches restantes dans la passe catalogue à ~1 fiche/2,5 s ≈ 22 h de moisson continue — c'est le rythme que le site tolère. Le stock FR (6 072 → en hausse) et le code source suivront au fil des injections. Disque toujours à 88 %, je surveille.

[assistant] Chiffres consolidés de la moisson (l'injection tourne bien) :

| Grandeur | Début de session | Maintenant | Δ |
|---|---|---|---|
| Skills au catalogue | 193 277 | **198 169** | +4 892 |
| Avec code source | 20 099 | **20 834** | +735 |
| Avec mots-clés FR | 6 072 | **6 374** | +302 |

Et la preuve que l'anti-429 tient : le compteur d'échecs est **figé à 278** pendant que les ok progressent (1 422/1 700) — plus aucune nouvelle erreur de throttling depuis la relance à 2,5 s.

Étages : catalogue/fr/boucle actifs ; expansion et source terminés (repartiront quand la boucle leur apportera de nouvelles cibles). La moisson est en régime de croisière — rien d'autre à toucher, elle s'accumule toute seule.

[user] Base directory for this skill: /home/turbo/.claude/plugins/cache/claude-plugins-official/superpowers/5.1.0/skills/subagent-driven-development

# Subagent-Driven Development

Execute plan by dispatching fresh subagent per task, with two-stage review after each: spec compliance review first, then code quality review.

**Why subagents:** You delegate tasks to specialized agents with isolated context. By precisely crafting their instructions and context, you ensure they stay focused and succeed at their task. They should never inherit your session's context or history — you construct exactly what they need. This also preserves your own context for coordination work.

**Core principle:** Fresh subagent per task + two-stage review (spec then quality) = high quality, fast iteration

**Continuous execution:** Do not pause to check in with your human partner between tasks. Execute all tasks from the plan without stopping. The only reasons to stop are: BLOCKED status you cannot resolve, ambiguity that genuinely prevents progress, or all tasks complete. "Should I continue?" prompts and progress summaries waste their time — they asked you to execute the plan, so execute it.

## When to Use

```dot
digraph when_to_use {
    "Have implementation plan?" [shape=diamond];
    "Tasks mostly independent?" [shape=diamond];
    "Stay in this session?" [shape=diamond];
    "subagent-driven-development" [shape=box];
    "executing-plans" [shape=box];
    "Manual execution or brainstorm first" [shap

[assistant] Ce skill exécute un **plan d'implémentation** existant — je n'en ai pas de désigné dans cette session. Je regarde s'il y a des plans récents avant de te demander lequel exécuter.

[assistant] **Point d'étape subagent-driven development** (exécution continue, pas de pause) :

| Tâche | État |
|---|---|
| 1 — JARVIS-OMEGA README | ✅ **terminée** : chiffres honnêtes (129/180, 5 GPU vérifiés), incohérence 99≠129 corrigée après review, double review passée |
| 2 — Présentation + PDF | Implémentation DONE (HTML:227 + LinkedIn:22 corrigés, PDF régénéré 5 p./398 Ko, vérifié par pdftotext) — **review spec en cours** |
| 3 — PACK-PRODUCTION | Implémenteur en cours (réconciliation qa_bench, AI-Act preuve par preuve) |
| 4 — workflow-gestion | Implémenteur en cours (unification :8140, workers 1, kill-switch) |

Détail notable de la tâche 2 : l'implémenteur a écarté à raison deux mentions « 4 GPU » qui décrivent le stack d'un **concurrent** (pas d'inflation JARVIS) — le reviewer spec va contre-vérifier ces lignes. Je poursuis au fil des notifications : review qualité tâche 2, puis double review des tâches 3 et 4, puis review finale d'ensemble.

[assistant] Spec tâche 2 ✅ (le zip est à côté du dossier, pas dedans — non-problème). Review qualité :

[assistant] Review qualité tâche 2 lancée. Trois agents tournent en fond (qualité T2, implémenteurs T3 et T4) — je traite chaque notification à l'arrivée : double review T3/T4, puis review finale d'ensemble des 4 packages.

[assistant] Tâche 2 **✅ terminée** — double review passée : HTML valide et fluide (« 129 agents réels (180 en périmètre entreprise) »), profil LinkedIn cohérent, zéro chiffre contradictoire résiduel, PDF régénéré conforme.

État : 2/4 tâches closes. Les implémenteurs des tâches 3 (PACK-PRODUCTION — réconciliation qa_bench + AI-Act preuves à l'appui) et 4 (workflow-gestion — instance unique :8140, workers 1, kill-switch `OMEGA_SEND_ENABLED`) travaillent encore ; leurs doubles reviews puis la review finale d'ensemble suivront à réception.

[assistant] Review spec T4 en cours. Point charge : la RAM est montée à 84 % (subagents + prod-runner ×8 + moisson + 2 modèles LMS) — les garde-fous du prod-runner (RAM min, CPU < 90 %) et la zram encaissent, mais je limite le nombre d'agents simultanés à deux le temps que ça redescende. Reste en vol : implémenteur T3 (PACK-PRODUCTION) et reviewer spec T4.

[user] Base directory for this skill: /home/turbo/.claude/plugins/cache/claude-plugins-official/superpowers/5.1.0/skills/subagent-driven-development

# Subagent-Driven Development

Execute plan by dispatching fresh subagent per task, with two-stage review after each: spec compliance review first, then code quality review.

**Why subagents:** You delegate tasks to specialized agents with isolated context. By precisely crafting their instructions and context, you ensure they stay focused and succeed at their task. They should never inherit your session's context or history — you construct exactly what they need. This also preserves your own context for coordination work.

**Core principle:** Fresh subagent per task + two-stage review (spec then quality) = high quality, fast iteration

**Continuous execution:** Do not pause to check in with your human partner between tasks. Execute all tasks from the plan without stopping. The only reasons to stop are: BLOCKED status you cannot resolve, ambiguity that genuinely prevents progress, or all tasks complete. "Should I continue?" prompts and progress summaries waste their time — they asked you to execute the plan, so execute it.

## When to Use

```dot
digraph when_to_use {
    "Have implementation plan?" [shape=diamond];
    "Tasks mostly independent?" [shape=diamond];
    "Stay in this session?" [shape=diamond];
    "subagent-driven-development" [shape=box];
    "executing-plans" [shape=box];
    "Manual execution or brainstorm first" [shap

[assistant] L'exécution du plan est déjà en cours — je fais le point et je surveille la charge (RAM 86 % signalée par le hook).

[assistant] Point d'avancement du plan :

| Tâche | État |
|---|---|
| 1 — JARVIS-OMEGA | ✅ close (double review) |
| 2 — Présentation + PDF | ✅ close (double review) |
| 3 — PACK-PRODUCTION | implémenteur toujours au travail (le plus gros lot : preuves AI-Act item par item) |
| 4 — workflow-gestion | spec ✅ · **review qualité en cours** (contrat de retour du no-op, parsing env, style) |

Côté machine : RAM 40,6/47 Go mais 14 Go de cache récupérable et load en décrue (13,6 → 8,7) — les garde-fous tiennent, pas d'intervention nécessaire. Je poursuis à réception des deux reviews restantes, puis review finale d'ensemble.

[assistant] Le reviewer qualité pointe une dette réelle mais mineure : le no-op renvoie `True` comme un envoi réussi. Aucun appelant ne lit ce retour aujourd'hui — le fix est donc sûr. Je renvoie l'implémenteur d'origine :

[assistant] Fix T4 en cours chez l'implémenteur d'origine (retour `False` sur no-op + docstrings explicites, puis rebuild et re-preuve :8140). Restent en vol : ce fix, l'implémenteur T3 (PACK-PRODUCTION, le plus long), puis re-review T4 et review finale d'ensemble. J'enchaîne à chaque notification.

[assistant] Tâche 3 DONE — avec une découverte importante : le vrai harnais qa_bench (20/20 tests) n'existe que sur une **branche non fusionnée**, master exécute encore le factice ; gold set réel = 18/200. Review spec :

[assistant] Review spec T3 lancée (contre-vérification des preuves citées, y compris une preuve au hasard dans le code source réel et l'existence de la branche non fusionnée). En parallèle, le fix T4 (contrat de retour) est toujours chez l'implémenteur. À suivre : re-review T4, qualité T3, puis review finale des 4 packages.

[assistant] Fix T4 appliqué (no-op → `False`, docstrings, container rebuild + preuves). Re-review qualité :

[assistant] Délibération lancée en fond (N experts + arbitre sur le corpus `souverainete`, avec citations obligatoires). Son verdict alimentera la review finale des 4 packages. En vol également : review spec T3 et re-review qualité T4. Je consolide dès que ces trois retours arrivent.

[assistant] Dernier point mineur : le chemin `except ImportError` (httpx absent) renvoie encore `True` en contradiction avec la doc. Boucle de fix :

[assistant] Micro-fix T4 en cours. Trois retours attendus : ce fix (puis re-review finale T4), la review spec T3, et la délibération du board `souverainete` — ensuite review qualité T3 et synthèse finale des 4 packages.

[assistant] La délibération du board tourne déjà (question `souverainete` sur les prérequis de mise en prod). Je regarde où elle en est :

[assistant] La délibération est en cours de génération — les experts passent chacun leur tour sur qwen (partagé avec le traitement massif de la file, donc quelques minutes). La sortie n'arrive qu'à la synthèse de l'arbitre ; je te livre le verdict complet (accords, divergences, citations) dès la notification.

Pour ne pas empiler deux délibérations sur le même backend pendant le rush du prod-runner, je garde la 2e question éventuelle (par ex. sur le routage cluster) pour après celle-ci. En attendant, les boucles de review T3/T4 continuent en parallèle.

[user] Base directory for this skill: /home/turbo/.claude/skills/run-jarvis-cascade-ingest

# run-jarvis-cascade-ingest

`scripts/cascade-log-ingest.py` est un **ingesteur idempotent** (Python stdlib seul) qui lit le log de routage du hub LLM (`data/llm_cascade_log.jsonl`, écrit par `chat_proxy.js:18800`) et le **persiste en SQLite** dans `data/jarvis_master.db` (table `llm_cascade_log`) pour des requêtes SQL arbitraires + l'alimentation du pipeline cascade domino. Mode `--stats` pour les métriques. On le pilote en CLI ; le driver `smoke.sh` l'exécute sur des chemins **jetables** (`CASCADE_LOG`/`CASCADE_DB`) sans toucher la prod.

> À ne pas confondre avec `monitoring/llm_stats.py` (skill `run-jarvis-llm-stats`) qui lit le **même JSONL à la volée** (text/JSON/Prometheus) **sans** le persister. Celui-ci **écrit en SQLite** (requêtable, durable).

Chemins relatifs à **`/home/turbo/jarvis/`**. Driver : `.claude/skills/run-jarvis-cascade-ingest/smoke.sh`.

## Prérequis

```bash
# présents dans ce container ; sinon :
sudo apt-get install -y python3 sqlite3
```
stdlib uniquement (`sqlite3`, `json`, `os`, `sys`) — aucun pip install.

## Run (agent path) — driver smoke.sh

Crée un JSONL synthétique (incluant 1 ligne malformée + 1 fallback) + une DB temp, vérifie l'ingestion, l'idempotence (2e run = 0 inséré), l'incrément, `--stats` et une requête SQL de contrôle, puis nettoie. Sortie 0 = ingesteur sain.

```bash
cd /home/turbo/jarvis
bash .claude/skills/run-jarvis-cascade-ingest/smoke.sh
``

[assistant] `/run-jarvis-cascade-ingest` : **smoke PASS** et **ingestion prod faite** — 28 nouvelles lignes persistées, table à **147 485 routages**.

Les stats globales méritent un œil : taux OK 51,1 %, fallback 63,1 %, p95 à 75 s — mais c'est l'**historique cumulé** depuis l'origine, qui inclut les pannes du 2026-08-06 (LMS tombé sans relève) et les warmups au boot. Pour juger le routage *courant*, la fenêtre courte du widget (n=60) reste la bonne jauge. Le timer systemd continue l'ingestion toutes les 15 min.

Reviews en vol : verdict final T4 demandé (fix `ImportError` appliqué tel que suggéré), spec T3 et board `souverainete` toujours en cours.

[assistant] T4 approuvée en final, spec T3 conforme (le reviewer a même rejoué les 20 tests). Je clos T4 et lance la review qualité T3 :

[assistant] **Tâche 4 ✅ close** — double review passée après deux boucles de fix (kill-switch cohérent de bout en bout : no-op et ImportError renvoient `False`, docstrings explicites, container up sur :8140 seul, 1 worker).

Il ne reste que la review qualité T3 (en cours) et la délibération board `souverainete` (toujours en génération). Dès ces deux retours : review finale d'ensemble des 4 packages et synthèse.

[assistant] **4/4 tâches closes** — chacune avec double review (spec puis qualité), trois boucles de fix au total, toutes re-validées. La review finale transverse est lancée : balayage inter-packages des chiffres résiduels, cohérence 129/180/5 GPU entre les 4 packages, et chasse aux supports client oubliés par le plan (autres PDF/HTML). Restent attendus : ce verdict final + la délibération board `souverainete` — je livre la synthèse complète à leur retour.

[assistant] Il existe déjà un avaleur dédié à l'API de recherche (`avale_search_api.py` avec son état et son log). Je regarde où il en est avant de le relancer :

[assistant] Avaleur `/fr/search` relancé en fond (bywvt90ax) — il reprend son état persistant (248 requêtes déjà faites : lettres, bigrammes, mots-clés) et va générer les requêtes suivantes en sautant l'acquis. Les nouvelles fiches découvertes alimentent l'étage `catalogue` qui moissonne derrière à cadence 2,5 s anti-429.

État de la moisson à cet instant :
- **198 169 skills** au catalogue (+4 900 cette session), 20 834 avec code, 6 374 avec mots-clés FR ;
- avale-search : 23 800 URL uniques déjà vues, 20 031 fiches issues de l'API — la reprise vise le reliquat des ~200 000 annoncés par le site ;
- étages `catalogue`, `fr`, `boucle` actifs ; `expansion`/`source`/`site` terminés en attente de nouvelles cibles.

Toujours en vol par ailleurs : review finale des 4 packages et délibération board. Je synthétise à leur retour.

[assistant] La review finale trouve 3 trous réels hors périmètre initial mais en plein dans le fil rouge (un PDF client avec « 1 435 » prêt à partir !). Je dispatche un subagent de correction :

[assistant] Verdict du board `souverainete` (délibération complète, règle de citation appliquée — 2 réponses sans citation rejetées) :

**« Le produit n'est PAS prêt pour la production client. »** L'ordre impératif tranché par l'arbitre, cohérent avec notre audit :
1. **Fusionner le harnais réel** (20/20) dans `master` — qui exécute aujourd'hui le banc factice ;
2. **Compléter le gold set** à 200 (18 actuellement) ;
3. **Valider la checklist AI-Act** (2/9 prouvés).

Sans cela, « le risque de vanité des métriques est trop élevé » — exactement le piège que la tâche 3 a documenté. À noter honnêtement : un expert (L'Exploitante) a mal lu les faits en prenant 18/200 et 2/9 pour des objectifs atteints — c'est la synthèse de l'arbitre, croisée avec l'avis « corpus insuffisant » de La Sécurité, qui remet d'aplomb. La délibération multi-lentilles a fait son travail.

Dernière pièce en vol : le subagent qui corrige les 3 trous de la review finale (PDF client « 1 435 » en quarantaine, headline contradictoire, re-zip des archives périmées). Synthèse d'ensemble à son retour.

[assistant] Cascade cycle 1000 lancée en fond (bn4n3nwiv) : mode `validated`, toutes familles, quota 1000 — elle construit la todolist dynamique avec contexte biblio préchargé par tâche et l'écrit dans `jarvis_master.db`, sans dispatch direct. Le drainage est déjà assuré par la boucle massive du prod-runner (parallèle 8, 200/passe) qui tourne depuis 1h.

Le cycle complet est donc branché : **moisson** (catalogue 8 400/31 553, 0 échec nouveau) → **injection** (boucle 10 min) → **cascade** (1 000 tâches préchargées) → **exécution massive** (prod-runner ×8) → **journal SQL**. Je rends compte du résultat de la cascade et du fix des 3 trous packages dès leurs notifications.

[assistant] **Go donné — dispatch réel en cours** (bmocry87g). Synthèse de l'état complet :

**Plan 4 packages : terminé et durci.** Les 3 trous de la review finale sont corrigés avec preuves :
- PDF client « jusqu'à 1 435 » **mis en quarantaine** (`PDFs-clients/_QUARANTAINE-chiffres-gonfles/` + POURQUOI.md) — plus aucun 1435/961 dans les PDF prêts à envoyer (pdftotext vérifié) ;
- `REPORT_PRESENTATION.md` : headline corrigé en « 129 agents réels (180 entreprise) », le décompte gonflé requalifié en contre-exemple daté ;
- 2 notes brutes archivées hors livraison ; **les 3 .zip re-générés** depuis les sources corrigées (les anciens du 6 août embarquaient les vieux chiffres), quarantaine et archives exclues des zips.

**Verdict board intégré** : produit non prêt pour la prod client — ordre : fusionner le harnais réel dans master → gold set 200 → AI-Act. C'est documenté honnêtement dans le pack.

**Cycle massif branché de bout en bout** :
| Maillon | État |
|---|---|
| Moisson catalogue | 8 400+/31 553, zéro nouveau 429 |
| Mots-clés FR | +1 000 ce run |
| Cascade validated | 175 tâches préchargées, 13 familles |
| Cascade **auto** | dispatch réel lancé, quota 1000, garde-fous actifs |
| Prod-runner ×8 | boucle massive continue |

Je rendrai compte du bilan de dispatch à la notification.

[assistant] **Cascade auto terminée : 215 tâches dispatchées réellement**, réparties sur les 15 familles d'agents (cowork 20, run 20, monitoring 19, openclaw 19, ops 16, misc 16, comms 15, chef 14, ai/trading 13, automation/business/data/dev/omega 12) — toutes en `done`, garde-fous charge/GPU respectés malgré la RAM à 87 %. Journal : `logs/skillmp-cascade.log`, run tracé dans `protocole_runs`.

**Bilan de la session complète :**

| Chantier | Résultat |
|---|---|
| Plan 4 packages (SDD) | **4/4 closes** avec double review + 3 boucles de fix ; 3 trous transverses corrigés (PDF client 1435 en quarantaine, headline REPORT, 3 zips re-générés propres) |
| Board | Verdict sourcé : prod client NON prête — fusionner harnais → gold set 200 → AI-Act |
| Moisson skillmp | 198k skills (+~5k), catalogue 8 400/31 553 sans plus aucun 429, +1 000 mots-clés FR, avale-search relancé |
| Cycle cascade | validated 175 + auto 215 dispatchées, drainées par le prod-runner ×8 |
| Infra | 3080 réactivée en CUDA et verrouillée (5 sources), qwen 32k/12, hermes stable, keep-warm durci, M6 synchronisé |

Point de vigilance pour la suite : la machine est **à pleine charge nominale** (RAM 87 %, disque 88 %) — tout tourne dans les garde-fous, mais je ne superposerais pas un nouveau lancement massif avant que la file se vide. Prochaine action à décider côté humain : fusionner la branche `fix/qa-bench-real-harness` dans master (prérequis n°1 du board).

[user] Base directory for this skill: /home/turbo/.claude/plugins/cache/claude-plugins-official/superpowers/5.1.0/skills/executing-plans

# Executing Plans

## Overview

Load plan, review critically, execute all tasks, report when complete.

**Announce at start:** "I'm using the executing-plans skill to implement this plan."

**Note:** Tell your human partner that Superpowers works much better with access to subagents. The quality of its work will be significantly higher if run on a platform with subagent support (such as Claude Code or Codex). If subagents are available, use superpowers:subagent-driven-development instead of this skill.

## The Process

### Step 1: Load and Review Plan
1. Read plan file
2. Review critically - identify any questions or concerns about the plan
3. If concerns: Raise them with your human partner before starting
4. If no concerns: Create TodoWrite and proceed

### Step 2: Execute Tasks

For each task:
1. Mark as in_progress
2. Follow each step exactly (plan has bite-sized steps)
3. Run verifications as specified
4. Mark as completed

### Step 3: Complete Development

After all tasks complete and verified:
- Announce: "I'm using the finishing-a-development-branch skill to complete this work."
- **REQUIRED SUB-SKILL:** Use superpowers:finishing-a-development-branch
- Follow that skill to verify tests, present options, execute choice

## When to Stop and Ask for Help

**STOP executing immediately when:**
- Hit a blocker (missing dependency, test fails, ins

[assistant] Le plan des 4 packages est terminé. Pour exécuter un nouveau plan, il me faut savoir lequel — la suite logique dictée par le board serait la mise en conformité prod du produit assistant :

[assistant] Deux implémenteurs lancés en parallèle (zones disjointes) :

- **Tâche 5 — prescription board** : fusion de `fix/qa-bench-real-harness` dans master, pytest 20/20 post-merge, docs du pack mises à jour, chemin gold set 18→200 documenté honnêtement. Fusion locale seulement, pas de push.
- **Tâche 6 — anti-tarissement** : sentinelle qui mesure le delta de cibles par étage, relance `source`/`expansion` quand de nouvelles fiches apparaissent (avec garde-fous charge/RAM, verrou, timer systemd 15 min) — c'est le chaînon manquant constaté ce soir (90 % des skills sans code parce que `source` ne repart jamais seul).

La tâche 7 (matrice cartographie) partira dès qu'un des deux se libère — la RAM à 88 % impose de plafonner à deux implémenteurs simultanés. Doubles reviews à suivre pour chacune.

[assistant] Reprise de l'avaleur `/fr/search` terminée : **+2 014 fiches nouvelles** en 399 appels API (13 904 URL parcourues, 11 890 déjà connues — la dédup fonctionne). Ces fiches partent dans la file de l'étage `catalogue`, et dès que la sentinelle anti-tarissement (tâche 6, en cours) sera en place, l'étage `source` se relancera automatiquement pour récupérer leur code — exactement le trou qu'elle vient boucher.

Implémenteurs toujours au travail : fusion du harnais (T5) et sentinelle (T6). Doubles reviews et matrice cartographie (T7) à la suite.

[user] Base directory for this skill: /home/turbo/.claude/plugins/cache/claude-plugins-official/superpowers/5.1.0/skills/systematic-debugging

# Systematic Debugging

## Overview

Random fixes waste time and create new bugs. Quick patches mask underlying issues.

**Core principle:** ALWAYS find root cause before attempting fixes. Symptom fixes are failure.

**Violating the letter of this process is violating the spirit of debugging.**

## The Iron Law

```
NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST
```

If you haven't completed Phase 1, you cannot propose fixes.

## When to Use

Use for ANY technical issue:
- Test failures
- Bugs in production
- Unexpected behavior
- Performance problems
- Build failures
- Integration issues

**Use this ESPECIALLY when:**
- Under time pressure (emergencies make guessing tempting)
- "Just one quick fix" seems obvious
- You've already tried multiple fixes
- Previous fix didn't work
- You don't fully understand the issue

**Don't skip when:**
- Issue seems simple (simple bugs have root causes too)
- You're in a hurry (rushing guarantees rework)
- Manager wants it fixed NOW (systematic is faster than thrashing)

## The Four Phases

You MUST complete each phase before proceeding to the next.

### Phase 1: Root Cause Investigation

**BEFORE attempting ANY fix:**

1. **Read Error Messages Carefully**
   - Don't skip past errors or warnings
   - They often contain the exact solution
   - Read stack traces completely
   - Note line numbers, file paths, 

[assistant] J'applique le débogage systématique au bug le plus persistant de la session : **`gpu-boost.service` failed à chaque boot** — il pollue chaque alerte hook (`FAILED_SVC:1`) et a déjà masqué une vraie panne (le keep-warm qwen). Interdiction de corriger avant d'avoir la cause racine complète.

**Phase 1 — Investigation.** Ce qu'on sait du journal : le service appelle `nvidia-smi -pm 1`, le **verrou GPU** (wrapper `/usr/local/bin/nvidia-smi`) refuse en non-interactif sans `JARVIS_GPU_UNLOCK` → exit 77. Je rassemble les preuves aux 3 couches : unit, wrapper, état GPU réel.

[assistant] **Débogage systématique clos** — bilan des 4 phases :

| Phase | Résultat |
|---|---|
| 1. Cause racine | `gpu-boost.service` = unit **obsolète de l'ère 6-GPU** (`-i 5` inexistant), ses valeurs (140-150 W sur les 1660S) contredisent la bride 70 W des cartes sans ventilateur ; 3 services récents font déjà le travail, persistence déjà active |
| 2. Pattern | Les 3 services `gpu-power*` actifs/verts sont la référence fonctionnelle |
| 3. Hypothèse | Le verrou bloquait **à raison** (il empêchait un débridage dangereux) → le fix n'est pas de contourner le verrou mais de retirer l'unit |
| 4. Fix + vérif | `disable --now` + reset-failed → **zéro unit failed**, brides 70 W et persistence intactes, réversible |

Le renversement compte : le réflexe « donner le code de déverrouillage au service » aurait fait sauter la protection thermique des cartes qui tournent déjà à 87 °C. Leçon gravée en mémoire (`gpu-boost-obsolete-verrou-protege`).

L'alerte `FAILED_SVC:1` qui accompagnait chaque message depuis le début de session va s'éteindre. Toujours en cours : fusion du harnais (T5) et sentinelle anti-tarissement (T6) ; la matrice cartographie (T7) part dès qu'un slot se libère.

[assistant] Fusion faite proprement (merge `6f513e7d`, 20/20 verts sur master, PDF re-régénéré depuis le HTML fusionné, rien poussé). Je lance la review spec T5 et, le slot étant libéré, l'implémenteur de la matrice T7 :

[assistant] Trois chantiers en vol : review spec de la fusion (T5 — dont contre-vérification du PDF régénéré et du qa_bench réel sur master), implémenteur matrice cartographie (T7 — SQLite+FTS5 avec dépliage d'accents comme le board, branchée sur `bloc.sh`), et la sentinelle anti-tarissement (T6) toujours au travail. Doubles reviews et clôtures au fil des notifications.

[assistant] Spec T5 ✅ (toutes preuves rejouées, y compris pytest et pdftotext). Review qualité — légère, en haiku vu la RAM à 90 % :

[assistant] Review qualité T5 lancée (marqueurs de conflit, propreté du working tree, honnêteté du commit préalable). En parallèle : sentinelle anti-tarissement (T6) et matrice cartographie (T7) toujours en implémentation. RAM à 90 % — je n'empile rien de plus tant qu'un chantier n'est pas clos.

[user] Base directory for this skill: /home/turbo/.claude/plugins/local/jarvis-turbo/skills/mao-workflow

# Protocole MAO — Multi-Agent Orchestrator (Linux)

## Quand utiliser

- Decisions architecturales ou techniques complexes
- Code review necesitant plusieurs perspectives
- Consensus sur une question technique
- Debug multi-composants

## Flux

1. **Decomposer** la tache en sous-questions independantes
2. **Dispatcher** en parallele vers les agents adaptes (voir matrice)
3. **Collecter** les reponses JSON, extraire le contenu
4. **Synthetiser** en comparant, ponderer par poids
5. **Presenter** avec attribution claire

## Matrice de routage (M1 PRIORITAIRE, benchmark 2026-02-26)

| Tache | Principal | Secondaire | Poids |
|-------|-----------|------------|-------|
| Code nouveau | **M1/qwen3-8b** | M2 review | **M1:1.8**, M2:1.4 |
| Bug fix | **M1** | M2 patch | **M1:1.8**, M2:1.4 |
| Architecture | GEMINI | **M1** validation | GEM:1.2, **M1:1.8** |
| Raisonnement | **M1** (100%) | M2 + M3 analyse | **M1:1.8**, M3:1.3 (deepseek-r1 capable) |
| Math/Calcul | **M1** | OL1 rapide | **M1:1.8**, OL1:1.3 |
| Question simple | OL1/qwen3 | M3 fallback | OL1:1.3, M3:1.3 |
| Consensus | **M1**+M2+OL1+M3 | +GEMINI+CLAUDE | Vote pondere 5 niveaux |

## Appels paralleles

Lancer TOUJOURS les appels independants en parallele (plusieurs Bash tool calls).

**M1** (PRIORITAIRE, reasoning model, 2-15s):
```bash
curl -s --max-time 45 http://127.0.0.1:1234/v1/chat/completions \
  -H "Content-Type: a

[assistant] Protocole MAO invoqué. Décision technique réelle à trancher en consensus : **stratégie de priorisation de la collecte de code** pour les ~177 000 skills du catalogue encore sans source (10,5 % couverts seulement). Je dispatche la même question en parallèle sur 3 backends locaux (M1 pondéré 1.8, M3 1.3, OL1 1.3) :

[assistant] État des enregistrements en cours :

- **Backup SQL** (b476j889g) et **backup n8n** (bnn8f3akg) tournent en fond — pipelines dédiés : dump atomique → gzip → manifest sha256 → push repo privé LFS → miroir M5.
- **Commit jarvis** (bvqh3bf1m) en cours sur `feat/content-perf-engine` — je pousse vers GitHub dès qu'il aboutit.
- **Audit local** relancé (bd3llmnys).

Côté MAO : 1 avis sur 3 reçu pour l'instant (M3/deepseek-r1 : prioriser dépôts récents+trending sur domaines critiques, référents académiques ensuite, ignorer >2 ans sans activité et sans stars). M1 a renvoyé une réponse sans `choices` (file pleine probable sous le rush) et OL1 un corps vide — je les retenterai après la vague ; pas de consensus pondéré tant que je n'ai pas ≥2 avis réels.

La matrice cartographie (T7) est livrée : **1 910 ressources** unifiées (694 prompts, 669 registre, 547 skills) dans `matrice_ressources.db` avec FTS accent-insensible, 2 blocs routables ajoutés à la bibliothèque — recherches de contrôle pertinentes et mixtes. Sa double review suivra la vague d'enregistrement.

[assistant] Audit 02:00 : **zéro service failed dans les deux scopes** — première fois de la session (le retrait de `gpu-boost` et la réparation du keep-warm tiennent), secrets CLEAN, rapport `audit-local-20260807-0200.md`, invocation journalisée.

Tâche 5 (fusion harnais) marquée close dans le suivi. En attente : le commit du repo jarvis (je pousse dès qu'il aboutit), les deux backups (SQL, n8n), et la sentinelle anti-tarissement (T6) toujours en implémentation. Disque monté à 89 % — les backups vont écrire leurs snapshots, la rotation 24 devrait contenir la croissance ; je vérifie après leur passage.

[user] dans bibliotrheque vivant(e commande rapide et dahns claude code openclow et toute les ia agent créee les équipe ou améliore

[assistant] La demande matche le skill dédié `run-planning-context-capture` (« crée les équipes ») — je l'invoque pour suivre le chemin outillé :

[user] Base directory for this skill: /home/turbo/jarvis/.claude/skills/run-planning-context-capture

# run-planning-context-capture

Le planning savait déjà **quoi** faire. Il ignorait **avec quoi**. Cette brique
comble ce trou : pour chaque tâche de création, elle assemble un *pack de contexte*
que l'exécutant applique sans re-délibérer.

Deux modules, un harnais :

| Fichier | Rôle |
|---|---|
| `bin/planning-context-capture.py` | capture le pack, alimente `plan` (source `creation`) |
| `bin/jarvis-teams-build.py` | relie les 261 agents réels à 16 équipes et 9 départements |
| `.claude/skills/run-planning-context-capture/driver.sh` | **tout se pilote par là** |

**Tous les chemins sont relatifs à `/home/turbo/jarvis/`.**

## Ce que le pack contient

Quatre gisements existaient déjà en base et n'étaient **jamais lus par le planning** :

| Gisement | Table / fichier | Volume |
|---|---|---|
| leaderboard (séries au score prouvé) | `serie_weights` | 86 séries |
| équipes | `teams` ← `agent_index` + `org_chart` | 16 équipes · 261 agents · 9 depts |
| écosystème (outils réels) | `tool_map` + `agentic_shell_tools` | 18 514 |
| cible (repo, port, run_cmd) | `unit_registry` + `repos` | 26 + 28 |

…plus les blocs prêts (`BLOCS-INDEX`, 37 373 sûrs sur 39 917) et le backend le mieux
classé (`system_llm_routes`). Le tout est **trié** (rang = pertinence + score prouvé),
**prérempli** (`plan.preloaded`, JSON) et **orchestré** (séquence ordonnée d'étapes).

## Run — commencer TOUJOURS par le sm

[assistant] **Équipes créées/améliorées** — la table `teams` est reconstruite sur le recensement actuel : **319 agents** (Claude Code + OpenClaw + skill-logique + skillmp-squads) répartis en **16 équipes / 9 départements**, chacune avec chef et sources croisées, seulement 8 non classés (2 %). Le widget :8899 affiche la nouvelle carte. Extrait : jarvis/jv-infra 65 · chef 37 · cowork 27 · business 26 · ops 25 · run 23 · monitoring 21 · dev 20…

**Rouleau compresseur moisson armé** :
- **Superposition de patterns** : avaleur API relancé avec un dictionnaire élargi à **2 000 requêtes** (bigrammes + mots-clés), checkpoint persistant — il saute l'acquis et n'avale que le neuf ;
- **Parallélisme pondéré** : la pression est mise sur le canal API (haut rendement, tolérant), les pages HTML restent à 2,5 s (le mur 429 est physique) ;
- **Sentinelle** : les 6 étages tournent, les listes de cibles s'étendent dynamiquement toutes les 15 min (+23 k dépôts injectés au premier tick) ;
- **Checkpoints partout** : `etat.json` (avaleur), curseurs par étage, rotation des backups.

Encore en vol : commit/push GitHub du repo jarvis, backup SQL, et les reviews T6/T7. La machine encaisse (RAM 82 %) — je rends compte aux notifications.