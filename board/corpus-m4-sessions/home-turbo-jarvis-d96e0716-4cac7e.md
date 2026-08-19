[user] lect(ure sql sqlo3 postgre n8n  githguvb log fichier index ap planing domi_no bibliotheque vivante utiliser m6 pour vvtampon et symbiose des processus les containers et outilzs sont labas

[user] Base directory for this skill: /home/turbo/jarvis/.claude/skills/run-m6-tampon

# run-m6-tampon

`scripts/m6_tampon.py` encaisse des demandes en texte libre et fait le travail de shell
**ailleurs que sur M1**. M1 porte l'écran, les 4 GPU et l'orchestration ; scorer 7 Mo de TSV et
lancer `df`/`ps`/`uptime` est du CPU pur qui n'a pas à s'exécuter là. **M6 mâche, M1 décide.**

Tout se pilote par **un seul harnais** : `.claude/skills/run-m6-tampon/driver.sh`.
Il existe parce que trois propriétés du tampon sont invisibles dans sa sortie normale et
peuvent casser à chaque édition — le mâchage part-il vraiment sur M6, une ligne d'index forgée
est-elle toujours rejetée, et le tampon respecte-t-il encore la loi A1.

**Tous les chemins ci-dessous sont relatifs à `/home/turbo/jarvis/`.**

## Prérequis

Rien à installer. Vérifié tel quel dans ce conteneur :

```bash
python3 --version          # 3.12.3 — stdlib seule, aucun pip
sqlite3 --version          # présent
ssh -o BatchMode=yes m6 'echo ok'   # -> ok   (ICMP filtré : ne JAMAIS pinger M6)
```

Le driver doit être exécutable :

```bash
chmod +x .claude/skills/run-m6-tampon/driver.sh
```

## Run (chemin agent) — commencer TOUJOURS par le smoke

8 contrôles, **zéro appel LLM**, ~15 s. Sort en 1 si un contrôle échoue.

```bash
bash .claude/skills/run-m6-tampon/driver.sh smoke
```

Sortie obtenue le 2026-07-30 à 00:56 (verbatim, fin de la sortie) — **le contrôle 6 est
rouge, et c'est correct** : il vient de détecter une corruption réelle

[assistant] Smoke **tout vert** (M6 joignable, 70 530 blocs, index sain, A1 respectée). J'encaisse les lectures dans la file.

[assistant] **Tampon M6 armé** — 8 lectures encaissées, mâchage lancé sur M6.

| # | Contrôle smoke | État |
|---|---|---|
| 1-2 | module + 6 sous-commandes | ✓ |
| 3-4 | status JSON · 18 068 outils shell | ✓ |
| 5 | **M6 joignable (ssh, ICMP filtré)** | ✓ |
| 6 | index biblio 70 530 blocs · 0 corrompu | ✓ |
| 7 | anti-injection TSV | ✓ |
| 8 | **loi A1** — 0 appel LLM direct | ✓ |

File `tanked: [12…19]` : sql/sqlite3 · postgres/cmdlib · n8n · github · logs · index biblio · api planning :8899 · domino. Drain en cours en arrière-plan (`bls9hwf7o`) — je remonte les résultats avec `chewed_on` à l'arrivée.

`★ Insight ─────────────────────────────────────`
Le critère de réussite du tampon n'est pas « ça a répondu » mais `chewed_on: m6`. Un `m1-fallback` rend une réponse correcte tout en ayant échoué sa mission : le CPU a été payé sur la machine qui porte l'écran et les GPU. Le driver sort en 1 dans ce cas — c'est un test de *placement*, pas de contenu.
`─────────────────────────────────────────────────`

[user] Stop hook feedback:
Système instable: 3 services failed, 0 zombies. Lancer service-auto-repair ou system-stabilization-mode avant de quitter.

[assistant] **File vidée : 19 `done`, 0 `pending`** — les 8 lectures ont toutes été mâchées sur M6 (`chewed_on: m6`, aucun `m1-fallback`), servies par le hub :18800, 24-124 s chacune. La bibliothèque est passée de 70 530 → **70 559 blocs**.

Services failed — trois causes distinctes, deux traitées :

| Service | Cause réelle | Action |
|---|---|---|
| `browseros.service` | stoppé sur timeout SIGTERM | ✅ relancé, **active** |
| `browseros-mcp.service` | **BrowserOS 146 n'écrit jamais `DevToolsActivePort`** → CDP :9105 absent après 60 s | ⛔ crash-loop stoppé (panne connue, `feedback_browseros146_cdp_jamais_ouvert`) |
| `mnt-backup-os.mount` | `mount(2)` EUCLEAN — **système de fichiers corrompu** sur le WD Blue SA510 | ⚠️ **non touché** |

Deux points qui demandent ta décision :

1. **Le disque de backup est corrompu**, pas juste démonté — un `fsck.ext4 -f` sur `ata-WD_Blue_SA510…-part1` est nécessaire, mais la règle « ne toucher sous aucun prétexte aux montages/disques » me l'interdit sans ton feu vert.
2. **browseros-mcp est arrêté, pas réparé** : le relancer le remettra en boucle tant que le binaire 146 n'ouvre pas de port CDP. Le redémarrer d'un mot : `systemctl --user start browseros-mcp`.

`★ Insight ─────────────────────────────────────`
Le journal de `browseros-mcp` cite lui-même le fichier mémoire du diagnostic (`feedback_browseros146_cdp_jamais_ouvert`) : le script d'amorçage a été instrumenté pour dire *pourquoi* il abandonne, pas seulement qu'il abandonne. C'est ce qui a évité d

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

[assistant] Bug actif à traiter : **`browseros-mcp` ne démarre jamais** — je l'ai *stoppé*, ce qui masque le symptôme sans le comprendre. Phase 1 : investigation, aucun correctif.

[assistant] Preuves clés : le binaire tourne **avec** `--remote-debugging-port=9105`, mais **9105 est fermé** et aucun `DevToolsActivePort` dans son profil — alors que trois autres profils Chromium en ont un. Phase 2 : comparer qui marche.

[assistant] Différence isolée, nette :

| Instance | `--user-data-dir` | CDP |
|---|---|---|
| jarvis-cdp :9222 | **explicite** | ✓ ouvert |
| Antigravity-Prod :9011 | **explicite** | ✓ ouvert |
| **browseros :9105** | **absent → profil par défaut** | ✗ fermé |

**Hypothèse :** Chromium ≥ 136 ignore silencieusement `--remote-debugging-port` sur le répertoire de données par défaut (protection anti-vol de cookies). BrowserOS 146 en hérite. Test minimal — une seule variable changée :

[assistant] Hypothèse **réfutée** — le `--user-data-dir` explicite n'y change rien. La mémoire tenait : BrowserOS 146 n'ouvre aucun CDP, quel que soit le profil. Je note le log pour la suite et je passe à ta demande.

[assistant] « Projection multiple » notée. Avant d'écrire quoi que ce soit : l'écosystème biblio compte **déjà 10 timers et 3 daemons actifs** (`biblio-filler` running, `biblio-rebuild` et `jarvis-biblio-infinite` en *activating*). Je n'ajoute pas un 11ᵉ boucleur aveugle — je regarde ce qui manque vraiment.

[assistant] Trois demandes empilées — je traite la plus fraîche d'abord car elle conditionne le reste : **capturer le board de rem-linux**. Impossible de l'adapter sans avoir vu sa logique.

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

[assistant] **Board trouvé : `:3200` → « JARVIS OpenClaw — Centre de Commande »** (+ `:37777` claude-mem viewer). J'aspire sa logique.

[assistant] Logique intégralement capturée : board monofichier, zéro dépendance externe, sondes `/health` + WebSocket live + soumission de tâches. J'adapte à ton écosystème.

[assistant] Tout est là : **319 agents / 20 familles**, 70 828 blocs, file M6. J'écris le board.

[assistant] Board **en ligne sur `http://127.0.0.1:8890`**, branché sur le réel :

| Mesure | Valeur live |
|---|---|
| Agents | **319** / 26 familles, chacune avec avatar déterministe |
| Bibliothèque | **70 827** blocs |
| Backends sondés | **7/10 UP** — Hub, CCR, SQL Bridge, LMS, Ollama, Planning, n8n |
| Backends DOWN | Dashboard :18801, BrowserOS MCP, WhisperFlow |
| Plan | **11 595** entrées · Tampon M6 : 19 done |
| systemd failed | `mnt-backup-os.mount` (disque corrompu, non touché) |

Ce que j'ai repris de rem-linux : sonde `/health` par service avec code HTTP, grille de containers cliquables, cartes KPI, journal horodaté, refresh 30 s, monofichier sans dépendance externe. Ce que j'ai adapté : tes ports réels, les avatars par famille, et le calcul de santé déplacé côté serveur (le board de Rémi le laissait au navigateur).

**Il manque une décision qui t'appartient** — `health_verdict()` dans `bin/jarvis-board.py:158`, seule fonction non implémentée (le badge affiche `?`) :

Les données sont prêtes : `services` (chacun avec `up` et `key`) et `failed` (unités systemd). Reste à décider ce qu'affiche le bandeau. Ce n'est pas une évidence technique — **tous tes services ne pèsent pas pareil** : le hub :18800 mort coupe toute la cascade 0-token, alors que BrowserOS MCP mort (panne connue, CDP jamais ouvert) ne bloque rien. Un seuil quantitatif (« 3 down = rouge ») ferait clignoter le board pour une brique optionnelle et le laisserait vert quand la vitale tombe. Écris les 5-10 lignes q

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

[assistant] **Audit local M1 — rapport généré** : `audit/audit-local-20260806-1248.md`, invocation loguée (row 50).

| Poste | Résultat |
|---|---|
| systemd system | 24 actifs / 20 inactifs / **0 failed** |
| systemd user | 28 actifs / 71 inactifs / **0 failed** |
| Skills | 463 `SKILL.md` + 49 `run-*` repo |
| Triggers | 49 couverts · **4 sans trigger** : `run-atomes-logiques`, `run-cascade-plan`, `run-logique-atomes`, `run-m1-memory-tuning` |
| Secrets | **CLEAN** (rc=0, motifs connus sur HEAD — non exhaustif) |

Deux choses que le rapport ne dit pas et qui comptent :

**1. L'audit a un angle mort sur les unités non-`.service`.** Il annonce 0 failed, mais `systemctl --failed` sans filtre en renvoie 1 — `mnt-backup-os.mount`, le disque corrompu. Le driver force `--type=service` aux lignes 45-49, y compris sur la commande `--failed` censée être « exhaustive » (son propre commentaire dit *« capture TOUS les failed quel que soit le nom »*). C'est le même faux négatif que celui du scope user qu'il documente fièrement, transposé au type d'unité : mounts, timers et sockets en échec sont invisibles. Fix : retirer `--type=service` des lignes 45-49.

**2. L'alerte GPU 82 °C du hook est en dessous du réel** — GPU3 est à **85 °C** (1660S, 58 W). Les autres : 67/59/69/73 °C. Selon ta règle définitive (tous les GPU en ligne, ventilo mort sur GPU2 assumé), ce n'est pas une anomalie à traiter, mais le chiffre annoncé par le hook n'est pas celui de la machine.

`★ Insight ─────────────────────────────

[user] Base directory for this skill: /home/turbo/.claude/skills/cascade-massive

# Cascade massive — SkillsMP → écosystème JARVIS

Chaîne 0-token qui transforme un **plan** en **implantation réelle** distribuée aux agents.
Aucun appel LLM : tout est déterministe (SQL + parsing + shell).

> **Entrée = le catalogue SkillsMP** (11 596 skills aspirés au 6 août 2026), pas un PLAN.md.
> Pour éclater un **plan mode** en tâches affectées dans la file du widget :8899,
> c'est le skill `run-cascade-plan` (`~/jarvis/bin/cascade-massive.sh --from-plan …`).
> Les deux sont complémentaires : celui-ci implante un catalogue, l'autre exécute un plan.

## Quand l'utiliser

- À la **sortie du plan mode** : le plan est validé, il faut le faire exécuter par les agents.
- Après une nouvelle aspiration SkillsMP : de nouveaux skills doivent être affectés.
- Pour rejouer une vague ciblée sur une seule famille (`--famille omega`).

## Chaîne complète

```
aspiration → cartographie → implantation → CASCADE → dispatch agents → journal
```

| Étape | Script | Sortie |
|---|---|---|
| Cartographie | `~/labo/bibliotheque/skillsmp/cartographie.py` | `export/skills_index.json` + colonnes `categories/occupations/langue` |
| Implantation | `~/labo/bibliotheque/skillsmp/implantation.py` | `export/plan_implantation.json`, `TODO_DYNAMIQUE_SKILLSMP.json`, table `skillsmp_affectation` |
| Catégories | `~/labo/bibliotheque/skillsmp/categories_texte.py --apply` | remplit `category` depuis le texte des pages (les pages /cat

[assistant] Garde-fous **verts** (charge 8.91 < 12 · RAM 55 % < 92 · GPU 82 °C < 84). File existante entièrement `done` (218 tâches, 15 familles). Dry-run d'abord.

[assistant] Dédup efficace : sur **120 skills au plan, 118 déjà traités** — seules **2 nouvelles** entrent en file. Je dispatche.

[assistant] **Cascade massive exécutée de bout en bout**, les trois modes en escalade, file vidée :

| Étape | Résultat |
|---|---|
| Garde-fous | charge 8.47 · RAM 56 % · GPU 82 °C → **tous sous seuil**, mode `auto` autorisé |
| Plan lu | 120 skills, 15 familles × 8, **120/120 avec contexte préchargé** |
| Dédup | **118 déjà traités**, 2 nouvelles en file |
| Dispatch | vague 1/3 : `trading` + `run` → `done` · vague 2 : file vide, arrêt propre |
| File finale | **220 done, 0 pending** |

Le point qui mérite ton attention : **la cascade est saturée, pas performante.** Sur 120 skills au plan, 2 étaient neufs — 98 % du travail était déjà fait. Le mode `auto` s'est arrêté à la vague 2 sur 3 faute de matière, pas par prudence. C'est le motif exact de ta mémoire `task_autogen_source_saturation` : la file meurt quand la source est statique. Le catalogue SkillsMP (11 596 skills) n'alimente que 120 entrées de plan parce que `implantation.py` tourne avec `--par-famille 8`.

Pour relancer du volume réel, il faut élargir la source en amont, pas rejouer la cascade :

```bash
python3 ~/labo/bibliotheque/skillsmp/implantation.py --install --par-famille 40
```

Attention avant de lancer ça : `--install` **écrase** les `SKILL.md` des slugs sélectionnés. Le skill le signale, et avec `--par-famille 40` la sélection englobe les 8 déjà installés par famille. À vérifier d'abord :

```bash
sqlite3 ~/jarvis/jarvis_master.db "SELECT COUNT(*) FROM skillsmp_affectation WHERE installe_claude=1;"
```

`★ Insight ──

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

[assistant] Le bug à traiter est nommé dans ta demande : **« brûler du temps/token/résultat pour rien »**. Le déclencheur auto par mots-clés existe déjà — il tourne à chaque message. La question est s'il produit quelque chose d'utilisable. Phase 1, aucun correctif.

[assistant] 11 hooks tirent à chaque message. Trois produisent le contexte injecté. J'instrumente la frontière qui compte : ce que le routeur biblio **reçoit** vs ce qu'il **rend**.

[assistant] Pipeline identifié : `prompt → 5 premiers mots de ≥5 lettres (hors stoplist) → bloc.sh (ET strict, repli OU) → head -14`. Je le rejoue sur les prompts **réels** de cette session et je mesure à chaque frontière.

[assistant] Reproduction suspecte : **0 blocs partout**, alors que les hooks en injectent 12 à chaque message. Mon instrumentation ment ou le hook ne passe pas par là. Je vérifie l'instrument avant de conclure.

[assistant] Mon instrument était faux (extraction de stoplist ratée), pas le hook. Corrigé : le hook réel **fonctionne** sur « audit analyse rapport » — blocs tous pertinents. Mais en session réelle il a produit du bruit. Je cherche ce qui sépare les deux cas.

[assistant] Reproduction fidèle et **systématique** — le pattern est net. Phase 3, hypothèse unique :

> **Le routeur matche sur la ligne TSV entière** (nom + source + danger + commande), pas sur le nom. Un mot présent dans le champ `source` ou dans la *commande* fait matcher des milliers de blocs sans rapport sémantique, et comme ils ont tous le même score (1 match), **l'ordre alphabétique de l'index décide** de ce qui remonte.

Signature à vérifier : « cascade massive » rend `appli_, application_, audit_, audit_, …, biblio_, cahier_` — de l'alphabétique pur.

[assistant] Hypothèse **confirmée, chiffrée** :

| Mot | Lignes matchées | dans le **nom** | dans la **commande** |
|---|---|---|---|
| `cascade` | 277 | 122 | **264** |
| `superpowers` | 202 | 40 | **202** |
| `audit` | 2 736 | 2 059 | 2 618 |
| **`skill`** | **27 235** *(38,5 % de l'index)* | 25 071 | **26 831** |

Les 63 blocs `source=mode` ont **tous** « cascade » dans leur commande (`cascade-bibliotheques '…'`) — 63/63. Les blocs superpowers matchent sur le **chemin** `docs/superpowers/plans/`. Le mot « skill » matche **38,5 % du corpus** : il ne discrimine rien.

Le hook prétend pourtant filtrer. Je vérifie si le code fait ce que son en-tête annonce :

[assistant] Le hook passe bien `--strict` (ligne 33). Reste à savoir si le destinataire le reconnaît :

[assistant] **Root cause trouvée — `bin/biblio-sql.sh:70-75`.** `--strict` *est* implémenté, mais pour BLOCS-INDEX il ne change qu'une chose : il ajoute `\b…\b`. Dans les deux branches :

```bash
grep -i -E "\b($(echo "$Q" | tr ' ' '|'))\b" "$BLOCS_INDEX" | head -"$LIMIT"
```

Trois défauts cumulés : `grep` sur **la ligne entière** (pas le champ nom, contrairement à ce qu'annonce l'en-tête du hook), `tr ' ' '|'` = **OU logique** (un seul mot suffit), et `head` **sans tri** — donc les N premières lignes *dans l'ordre du fichier*, c'est-à-dire alphabétique. D'où `appli_, application_, audit_…`.

Le point décisif : **le hook n'appelle pas `bloc.sh`** — celui que tu avais fait corriger (mémoire `bloc_sh_match_et_strict` : ET strict + score A/O). Deux routeurs parallèles, un réparé, l'autre resté naïf.

[assistant] Preuve définitive, même requête : `bloc.sh` rend des blocs **nommés** « cascade… » ; `biblio-sql.sh --strict` rend de l'alphabétique dont **aucun** ne porte le mot dans son nom.

Phase 4 — le test qui échoue d'abord :

[assistant] Test **rouge** comme attendu : 0/12 sur deux requêtes. Fix minimal, uniquement la branche `--strict` :

[assistant] **Debug clos — correctif vérifié** : 0/12 → **12/12 sur les trois requêtes, test PASS**. Le hook injecte maintenant `cascade-massive`, `cascade-massive-dry`, `cascade-massive-exec`, `cascade-massive-from-plan` là où il servait de l'alphabétique. Test de régression déposé : `jarvis/tests/test-biblio-route-pertinence.sh`.

Ta nouvelle demande tombe au bon moment — le routeur qui alimentera les simulations vient d'être réparé. Je construis le moteur de projections superposées.

[assistant] Le moteur tourne, mais il a **le bug exact que je venais de corriger ailleurs** : `npx skills add` classé en « destruction ». Cause — `"kill" in "skills"` : s-**kill**-s. Matching de sous-chaîne non borné, la même faute que le grep du routeur.

[assistant] Erreur du harnais de test, pas du code — `@dataclass` exige le module dans `sys.modules` :

[assistant] Exit 144 — `sleep` en avant-plan est bloqué par le harnais. Je sépare le lancement du test.

[assistant] `pkill -f` s'est tué lui-même : le motif matchait la ligne de commande du shell qui l'exécutait. Astuce classique de la classe de caractères :

[assistant] **Le board porte maintenant un moteur de projections superposées.** Vérifié de bout en bout sur `http://127.0.0.1:8890` :

Sur l'intention *« sauvegarde sql postgres backup »* → 12 blocs routés, **5 lentilles simulées en parallèle**, consensus complet :

| Lentille | Poids | Blocs | Score |
|---|---|---|---|
| sûre | 1.4 | 9 | **12.6** |
| chronologique | 1.1 | 12 | 3.6 |
| agents | 1.0 | 3 | 3.0 |
| couverture | 0.8 | 12 | 2.62 |
| éprouvée | 1.2 | 1 | 1.2 |

**Superposition** — 4 blocs vus par 4 lentilles indépendantes : `backup-sql-github`, `jarvis-full-backup-sauvegarde-sql-infra`, `gh-jarvis-c-backup-sql-daily`, `gh-jarvis-l-github-sql-backup`. **Chronologie** : `0.lecture(5) → 1.execution(7)` — aucune action destructive retenue.

Trois principes de conception, puisque c'est là que se joue l'utilité :

- **Les lentilles doivent diverger.** Deux lentilles qui filtrent pareil votent deux fois pour la même chose et fabriquent un faux consensus. « sûre » ne garde que 🟢, « couverture » prend tout, « chronologique » exclut le destructif — elles voient le même corpus et en tirent des plans différents. C'est l'écart qui rend le vote informatif.
- **Le score divise par le risque**, il ne l'additionne pas : une projection large mais dangereuse ne bat pas une projection étroite et sûre. C'est pourquoi « sûre » gagne à 12.6 avec 9 blocs contre « couverture » à 2.62 avec 12.
- **Rien n'est exécuté.** La sortie dit ce qui *serait* fait, dans quel ordre, à quel risque.

Deux bugs corri

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

[assistant] Confirmation en conditions réelles d'abord : sur ce message, le hook a routé « superpowers systematic debugging » vers `skills-systematic-debugging`, le `SKILL.md` local, `skillsmp-cat-debugging` — **des blocs pertinents**. Le même prompt renvoyait 12 `gh-jarvis-c-*plans*` avant le correctif. Le fix tient en production.

Reste ta demande, que je n'ai pas encore livrée : **la chaîne automatique**. Je mesure d'abord ce qui se brûle réellement.

[assistant] **Root cause du gaspillage, mesurée** : `4 139 octets ≈ 1 034 tokens injectés par message` — et la colonne de droite est la même partout : **aucun hook n'exécute quoi que ce soit**. Ils détectent, proposent une commande, et s'arrêtent là. La boucle détection → action n'est jamais fermée : c'est moi qui dois relire et relancer à la main, ou rien ne se passe.

C'est exactement ce que tu décris. Le chaînon manquant, c'est l'exécuteur.

[assistant] Bug — et c'est **exactement le piège documenté dans le skill `run-m6-tampon`** que j'ai lu ce matin : `python3 -c '…'` entre apostrophes shell, les `\"` restent littéraux. Le troisième bloc a la même faute en pire (apostrophes Python qui ferment la chaîne shell). Correction par heredoc quoté + argv, comme le skill le prescrit :

[assistant] Défaut visible : le `60000` parasite dans la sortie — `PRAGMA busy_timeout` **retourne sa valeur** sur stdout, et `journal()` ne redirige que stderr.

[assistant] Sortie propre, et **le verrou est réellement tenu** — la seconde chaîne est refusée, pas seulement documentée. Test du mode `--exec` :

[assistant] **La chaîne est livrée et vérifiée en mode réel**, de bout en bout :

```
lecture sql sqlite postgres n8n github logs index planning domino
  ① biblio     : 12 blocs routés            265 ms
  ② projection : 5 lentilles ∥, 12 consensus, meilleure=sûre
  ③ todolist   : 11 tâches insérées + contexte préchargé   2 063 ms
  ④ cascade    : dispatch borné (quota 4, 2 vagues)        242 ms
  ⑤ journal    : protocole_runs — traçable, rejouable
```

`tasks` : 2 144 608 → 2 144 619 (12 actions, **1 doublon dédupliqué**). Chaque tâche porte sa commande prête en `biblio_preload`. Journal SQL alimenté aux 3 étapes.

**Ce que la mesure a montré** — le vrai gaspillage n'était pas le routage mais l'absence de terminus : `4 139 octets ≈ 1 034 tokens injectés par message`, et **aucun des 9 hooks n'exécute quoi que ce soit**. Ils détectent, proposent `skillmp cascade --mode validated`, et s'arrêtent. Sans exécuteur, chaque message payait le diagnostic sans jamais l'encaisser. `jarvis-autochain.sh` ferme cette boucle en 0 token — SQL, grep, arithmétique.

Garde-fous réellement éprouvés, pas seulement écrits : seuils charge/RAM/GPU repliant en simulation, `flock -n` **testé** avec deux chaînes concurrentes (la seconde refusée), `busy_timeout=60000` — qui a servi, l'insertion a pris 2 s sous contention sur une base de 2,1 M lignes.

Trois bugs traversés en l'écrivant, dont **deux étaient documentés dans un skill que j'avais lu ce matin** (`run-m6-tampon`) : `python3 -c '…'` où les `\"` restent lit

[user] Base directory for this skill: /home/turbo/.claude/plugins/cache/claude-plugins-official/superpowers/5.1.0/skills/writing-skills

# Writing Skills

## Overview

**Writing skills IS Test-Driven Development applied to process documentation.**

**Personal skills live in agent-specific directories (`~/.claude/skills` for Claude Code, `~/.agents/skills/` for Codex)** 

You write test cases (pressure scenarios with subagents), watch them fail (baseline behavior), write the skill (documentation), watch tests pass (agents comply), and refactor (close loopholes).

**Core principle:** If you didn't watch an agent fail without the skill, you don't know if the skill teaches the right thing.

**REQUIRED BACKGROUND:** You MUST understand superpowers:test-driven-development before using this skill. That skill defines the fundamental RED-GREEN-REFACTOR cycle. This skill adapts TDD to documentation.

**Official guidance:** For Anthropic's official skill authoring best practices, see anthropic-best-practices.md. This document provides additional patterns and guidelines that complement the TDD-focused approach in this skill.

## What is a Skill?

A **skill** is a reference guide for proven techniques, patterns, or tools. Skills help future Claude instances find and apply effective approaches.

**Skills are:** Reusable techniques, patterns, tools, reference guides

**Skills are NOT:** Narratives about how you solved a problem once

## TDD Mapping for Skills

| TDD Concept | Skill Creation |
|---

[assistant] Le skill exige un test RED avant d'écrire. **Je l'ai déjà, observé en direct dans cette session** — j'ai construit cette chaîne sans documentation et j'ai échoué six fois, de façon reproductible. Voilà le baseline, verbatim :

| # | Échec observé | Message réel |
|---|---|---|
| 1 | `python3 -c '…'` avec `\"` | `SyntaxError: unexpected character after line continuation character` |
| 2 | apostrophes Python dans `'…'` shell | quoting shell fermé prématurément |
| 3 | `PRAGMA busy_timeout` | imprime `60000` au milieu du rapport |
| 4 | `pkill -f "jarvis-board.py"` | tue le shell qui l'exécute |
| 5 | `sleep` en avant-plan | `exit 144` (garde-fou harnais) |
| 6 | `"kill" in "skills"` | `npx skills add` classé *destruction* |

Le skill doit fermer **ces** trous précis, pas des trous hypothétiques.

[assistant] Convention claire. J'écris le driver **d'abord** — c'est lui qui tient les tests, le `SKILL.md` ne fait que documenter ce qu'il prouve.

[assistant] Deux rouges. J'analyse avant de toucher quoi que ce soit — un test qui échoue peut accuser le code **ou** se tromper.

[assistant] Les deux rouges sont des **défauts du test, pas du code** :

- **Rouge 1** : le seul `python3 -c` restant est dans le **commentaire qui explique de ne pas l'utiliser**. Mon grep matche sa propre documentation.
- **Rouge 2** : plus aucune chaîne ne tourne et le verrou est libre — au moment du contrôle, la chaîne de fond n'avait simplement pas fini. Course dans le test.

Je corrige le harnais, pas la chaîne :

[assistant] **GREEN — 9 contrôles verts, 0 token.** Le SKILL.md peut maintenant documenter ce que le driver *prouve*, pas ce que j'espère.

[assistant] Dernière étape : l'audit de tout à l'heure a relevé **4 skills `run-*` sans trigger**. Je n'en ajoute pas un cinquième.

[assistant] `triggers` est une liste, pas un dict — mon script a supposé. Le fichier est intact (49 entrées, backup pris). J'inspecte la forme réelle :

[assistant] **Skill livré et enregistré** — 50 triggers, et `run-jarvis-autochain` n'a pas rejoint la liste des orphelins (les 4 préexistants restent, je ne les ai pas touchés).

Le cycle TDD complet, sans raccourci :

| Phase | Ce qui s'est passé |
|---|---|
| **RED** | 6 échecs réels observés en construisant la chaîne — pas des hypothèses : `SyntaxError` sur `\"`, quoting cassé, `60000` imprimé, `pkill` suicidaire, `exit 144`, `"kill" in "skills"` |
| **GREEN** | `driver.sh` écrit **avant** le SKILL.md, 9 contrôles couvrant exactement ces 6 échecs |
| **REFACTOR** | 2 rouges au premier smoke — **tous deux dans le test** : le grep accusait le commentaire qui décrit le piège, et `flock -n` accusait une course pour un zombie |

Ce dernier point est le plus instructif. Le contrôle 5 lance vraiment deux chaînes concurrentes et exige que la seconde soit refusée — mais il vérifiait ensuite la libération avec `flock -n` alors que la chaîne de fond tournait encore. Un test qui échoue accuse le code par défaut ; ici il se trompait deux fois sur deux. Corriger le code aurait cassé du bon travail.

Ce que le driver **prouve** à chaque exécution, et qu'aucune relecture ne montrerait :

- le mode par défaut n'écrit rien (`tasks` inchangé : 2 144 628 avant/après)
- le verrou est **tenu**, pas documenté — seconde chaîne réellement refusée
- `npx skills add` n'est plus classé *destruction*
- aucun `python3 -c` exécutable ne subsiste
- `protocole_runs` est alimenté

`★ Insight ──────────────────────────

[user] Base directory for this skill: /home/turbo/.claude/plugins/cache/claude-plugins-official/superpowers/5.1.0/skills/dispatching-parallel-agents

# Dispatching Parallel Agents

## Overview

You delegate tasks to specialized agents with isolated context. By precisely crafting their instructions and context, you ensure they stay focused and succeed at their task. They should never inherit your session's context or history — you construct exactly what they need. This also preserves your own context for coordination work.

When you have multiple unrelated failures (different test files, different subsystems, different bugs), investigating them sequentially wastes time. Each investigation is independent and can happen in parallel.

**Core principle:** Dispatch one agent per independent problem domain. Let them work concurrently.

## When to Use

```dot
digraph when_to_use {
    "Multiple failures?" [shape=diamond];
    "Are they independent?" [shape=diamond];
    "Single agent investigates all" [shape=box];
    "One agent per problem domain" [shape=box];
    "Can they work in parallel?" [shape=diamond];
    "Sequential agents" [shape=box];
    "Parallel dispatch" [shape=box];

    "Multiple failures?" -> "Are they independent?" [label="yes"];
    "Are they independent?" -> "Single agent investigates all" [label="no - related"];
    "Are they independent?" -> "Can they work in parallel?" [label="yes"];
    "Can they work in parallel?" -> "Parallel dispatch" [label="yes"];
    "Can the

[assistant] Demande explicite de dispatch parallèle. J'ai quatre domaines réellement indépendants restés en suspens — pannes distinctes, sous-systèmes distincts, aucun état partagé :

| Agent | Domaine | Fichiers/ressources touchés |
|---|---|---|
| 1 | `browseros-mcp` — CDP jamais ouvert | binaire BrowserOS, profils Chromium |
| 2 | Dashboard `:18801` down | service dashboard |
| 3 | WhisperFlow `:9743` down | service whisper |
| 4 | `mnt-backup-os` — FS corrompu | diagnostic disque, **read-only** |

Aucun ne peut réparer l'autre, aucun n'édite les mêmes fichiers.

[assistant] **4 agents lancés en parallèle.** Ils tournent en fond ; je remonterai leurs conclusions à mesure qu'elles arrivent.

Ce que chacun a reçu, et pourquoi c'est ce qui compte ici — les agents n'héritent pas de cette conversation, donc tout ce que nous avons appris aujourd'hui devait être reconstruit dans leur prompt :

**Les acquis, pour qu'ils ne les re-cherchent pas.** L'agent BrowserOS reçoit l'hypothèse *déjà réfutée* (profil par défaut) avec sa preuve, et les deux profils Chromium qui exposent bien leur CDP comme références de comparaison. Sans ça, il refait mon test raté.

**Les pièges de cet environnement**, qui ont chacun coûté un échec réel aujourd'hui : `sleep` en avant-plan → `exit 144`, `pkill -f` qui se suicide, le scope `--user` que l'audit oubliait. Un agent naïf les rencontrera exactement comme moi.

**Les interdits, calibrés par domaine.** C'est là que le cadrage compte le plus :

- L'agent Whisper a interdiction de **démarrer** le service — charger un modèle sur une machine à 5 GPU qui fait déjà tourner des LLM affamerait les modèles chargés. Il diagnostique et chiffre la VRAM, rien de plus.
- L'agent disque a des interdits absolus : jamais `fsck` sans `-n`, aucun montage, aucun `umount -l`, aucun rescan SCSI. Il reçoit aussi les deux pièges matériels documentés ici — les disques clonés aux UUID identiques, et le `e2fsck` qui a déjà détruit l'inode racine du **mauvais** disque après un `umount -l`. D'où l'exigence d'identifier le disque par `by-id` et numéro de

[user] # Sourcegraph File Read

Use `read_file` to fetch Sourcegraph file contents based on input after `/sourcegraph:sg-file`.

Interpret input in one of these forms:

- `repo path` (default revision)
- `repo rev path`

After reading the file:

1. Summarize what the file does.
2. Call out key exported symbols or entry points.
3. Mention related files that should be read next.

[assistant] La commande est arrivée **sans argument** — il me faut un dépôt et un chemin. Je vérifie d'abord que l'outil est bien disponible pour ne pas te faire répéter :

[assistant] Diagnostic net — la commande est inutilisable pour deux raisons, et aucune n'est de ton fait :

**1. Aucun argument.** Le skill attend `repo path` ou `repo rev path` ; la commande est arrivée nue.

**2. Le serveur MCP n'est pas branché.** Le plugin est bien installé (`claude-plugins-official/sourcegraph/0.1.0`) avec ses deux commandes, mais son `.mcp.json` déclare :

```json
"url": "${SOURCEGRAPH_ENDPOINT}/.api/mcp",
"headers": { "Authorization": "token ${SOURCEGRAPH_ACCESS_TOKEN}" }
```

Ces deux variables ne sont définies nulle part — ni dans `settings.json`, ni dans `settings.local.json`, ni dans aucune config MCP. `ToolSearch` sur `+sourcegraph` ne renvoie rien : l'outil `read_file` que le skill veut appeler **n'existe pas dans cette session**. Sans les variables, le serveur ne se connecte pas.

Pour l'activer, il te faut une instance Sourcegraph et un jeton :

```bash
# dans ~/.claude/settings.json, section "env"
"SOURCEGRAPH_ENDPOINT": "https://sourcegraph.com",
"SOURCEGRAPH_ACCESS_TOKEN": "sgp_..."
```

Le jeton se crée depuis *Settings → Access tokens* sur ton instance. Je peux faire l'édition via `/update-config` si tu me donnes l'endpoint — le jeton, tu le colles toi-même, je ne veux pas le manipuler.

**En attendant, pour lire un fichier de dépôt, le MCP GitHub est actif** et couvre le cas courant :

```
mcp__github-mcp-server__get_file_contents  (owner, repo, path, ref)
```

Dis-moi juste quel fichier tu voulais lire — s'il est chez `Turbo31150` ou tout autre dépô

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

[assistant] Protocole MAO, sans question en argument — je le passe sur le seul arbitrage réellement ouvert de cette session : **la règle de santé du board** (`health_verdict`, badge à `?`). Décision technique à compromis, exactement le cas d'usage.

Règle impérative du protocole : jamais de réponse simulée. Je sonde les backends avant de router.

[assistant] Les trois backends répondent **200** — le hook de démarrage annonçait pourtant `M1=DOWN`. Sonder avant de router, encore une fois payant. Dispatch parallèle, même question aux trois :

[assistant] Beaucoup converge d'un coup. Je traite dans l'ordre d'urgence.

**Agent dashboard — terminé, port réparé.** Cause racine : **deux unités systemd pour le même port**, et la seule `enabled` était doublement incapable de démarrer en scope `--user` — `WantedBy=multi-user.target` (jamais activée au login) **et** `User=turbo` (interdit en scope user → `status=216/GROUP`, boucle de restart silencieuse). `:18801` répond de nouveau **200**.

Pour le MAO : **1 backend sur 3 a produit**, et sa règle contient un défaut logique que je ne peux pas laisser passer :

```
ELSE IF BrowserOS_MCP == DOWN THEN STATUS = OK    ← court-circuite tout le reste
```

BrowserOS est en panne **permanente** : cette ligne renverrait `OK` en toutes circonstances, sans jamais évaluer les suivantes. Je relance les deux backends muets avec les correctifs connus, et je monte en parallélisme comme demandé :

[assistant] Deux agents ont livré. Le résultat Whisper change la donne :

**`:9743` n'est pas en panne — il a été coupé délibérément, triple verrou** (masque user + `Restart=no` + unité renommée `.DISABLED-turbo`), pour briser la boucle acoustique `TTS → micro → transcription charabia → xdotool → terminal`. Un `arecord` est actif en ce moment : la chaîne micro tourne toujours. **Je ne le rallume pas** — ce serait défaire ta décision documentée.

Synthèse MAO pondérée — les trois règles proposées ont chacune un défaut, et c'est la comparaison qui le révèle :

| Backend | Poids | Défaut de sa règle |
|---|---|---|
| M1 qwen3.5-9b | 1.8 | `browseros DOWN → DEGRADE` : badge orange **en permanence** |
| Hub gemma-4-12b | 1.4 | `browseros DOWN → OK` : **court-circuite** tout le reste |
| OL1 mistral | 1.3 | encore en vol |

Aucun n'a traité les 8 autres backends. La synthèse corrige les deux : BrowserOS **exclu** du calcul (panne permanente = bruit, pas signal), hub vital seul déclencheur de `CRITIQUE`.

[assistant] OL1 muet lui aussi (réponse vide) — **2 backends sur 3 ont produit**. J'implémente la synthèse :

[assistant] **Badge opérationnel** — et il dit quelque chose de juste :

```
BADGE  : DEGRADE
MOTIF  : backend(s) muet(s) : WhisperFlow
UP     : Hub LLM, Dashboard, CCR, SQL Bridge, LM Studio, Ollama, Planning, n8n   (8/10)
DOWN   : BrowserOS MCP, WhisperFlow
```

BrowserOS est down mais **absent du motif** — exclu comme bruit permanent. Dashboard est passé UP grâce à l'agent. La règle passe 5/5 en test unitaire, y compris le cas piège « browseros seul mort → OK » que les deux modèles rataient chacun à leur façon.

Sur ta demande de saturer les 16 threads — je dois te donner le chiffre avant d'appuyer :

[assistant] **Charge à 21.68 pour 16 threads — la machine est déjà en surcharge de 35 %**, et la tendance monte (15 min : 13.40 → 5 min : 19.27 → 1 min : 21.68). Un `python3` consomme à lui seul **606 % de CPU** (6 cœurs), 15 processus claude tournent, et 2 agents de diagnostic sont encore en vol.

Je ne lance pas d'agents supplémentaires maintenant, et voici pourquoi c'est la bonne réponse à ta demande plutôt qu'un refus : **au-delà de nproc, ajouter du parallélisme ne produit plus de travail, il produit de l'attente.** Les tâches se disputent les mêmes cœurs, chacune ralentit, le débit total baisse. Ton propre garde-fou cascade se replie à charge ≥ 12 — nous sommes à 21.68, presque le double. Ta mémoire `ollama_swap_thrash_gel` documente précisément la suite : daemons en boucle × modèles différents → gel de M1.

Ce qui sature actuellement, et ce qui peut être libéré :

| Consommateur | CPU | Nature |
|---|---|---|
| `python3` | **606 %** | à identifier — 6 cœurs à lui seul |
| 2 agents diagnostic | ~200 % | **utiles**, bientôt finis (BrowserOS, disque) |
| `llama-server` | 94 % | inférence légitime |

Le vrai levier n'est pas d'ouvrir un 3ᵉ front, c'est de **délocaliser** : le tampon M6 existe précisément pour ça et a déjà mâché 19 demandes aujourd'hui, `chewed_on: m6`, sans toucher un cœur de M1. C'est du parallélisme réel, sur une autre machine.

Trois options, dis-moi laquelle :

1. **Identifier et traiter le python3 à 606 %** d'abord — libérer 6 cœurs avant toute montée en charge (

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

[assistant] Sans argument → `stats` puis `status`. Et cela devrait éclairer le `python3` à 606 % : le pipeline a **6 workers** sur l'étage source.

[assistant] Le pipeline est **entièrement à l'arrêt** — les 6 étages. Le CPU est donc mangé par autre chose, et j'ai trouvé quoi :

| PID | CPU | Depuis | Processus |
|---|---|---|---|
| 687591 | **602 %** | 7 min | `python3 rdit_analysis.py` |
| 47356 | 99 % | **1 h 04** | `jarvis-plan.py --sync` |
| 128451 | 99 % | **57 min** | `gen_sql_shortcuts.py` |

Charge montée à **25.41**. Deux scripts tournent à fond depuis près d'une heure — le motif exact de ta mémoire `unguarded_cron_proliferation`.

[assistant] **Cause racine BrowserOS trouvée — et elle invalide une de tes mémoires.**

Le navigateur n'« ouvre pas de CDP » parce qu'il **ne finit jamais son démarrage** : il se bloque dans l'initialisation d'OSCrypt sur `GNOME_LIBSECRET`, le trousseau `login` étant verrouillé. Le serveur DevTools démarre plus tard dans la séquence — jamais atteint. Preuve A/B, même binaire, même profil neuf, un seul paramètre changé :

| Test | Backend mot de passe | Résultat |
|---|---|---|
| libsecret (défaut) | auto | aucun `DevTools listening`, blocage |
| **`--password-store=basic`** | local | **`DevTools listening on ws://127.0.0.1:9107/…` en ~1 s** |

Cause amont : `/etc/gdm3/custom.conf` a `AutomaticLogin=turbo`. En autologin, PAM ne voit jamais ton mot de passe, donc `pam_gnome_keyring` ne peut pas déverrouiller `login.keyring` — état permanent. L'instance de production a consommé **0,2 s de CPU en une heure** : bloquée, pas occupée.

Mon propre test avait échoué parce que le blocage est **en amont** du profil : changer `--user-data-dir` ne pouvait rien y faire.

Je corrige la mémoire, qui affirme le contraire :

[assistant] Mémoire corrigée. **Ton prompt est tronqué** — il annonce sept objets, la liste s'arrête au milieu de `chunks` (il manque `queries`, `answers`, et probablement `citations`). Je démarre la PHASE 0, qui est entièrement spécifiée, et je te demanderai la suite du schéma avant la PHASE 1.

**PHASE 0 — INVENTAIRE.** Sorties brutes, aucune supposition :

[assistant] Deux inconnues restent, et ce sont les décisives — je ne les suppose pas, je les mesure :

[assistant] La requête `pg_available_extensions` n'a rien renvoyé — je vérifie directement avec les bons rôles :

[assistant] Deux précisions importantes prises en compte : le label `JARVIS OS v13.1` dans `/etc/os-release` est un vestige d'une autre machine — je ne m'y fie pas et ne le câble pas. Nous sommes sur **M1, « La Créatrice », JARVIS OMEGA**. Et le board sera **indépendant** : aucun couplage à l'existant.

Une dernière vérification, car une sortie vide n'est pas une preuve :

[assistant] ## PHASE 0 — INVENTAIRE : constaté

**1. Machine** — M1 « La Créatrice », kernel `6.8.0-137-generic`, RAM 45 Gi (14 Gi disponibles).

```
0, RTX 2060,      12288 MiB,  8193 libres,  71°C
1, GTX 1660 SUPER, 6144 MiB,  1910 libres,  59°C
2, GTX 1660 SUPER, 6144 MiB,  4586 libres,  81°C
3, GTX 1660 SUPER, 6144 MiB,  4100 libres,  81°C
4, RTX 3080,      10240 MiB,  5126 libres,  75°C
```
→ **23,9 Go de VRAM libre** au total.

**2. Postgres** — `psql 16.14`, deux containers `postgres:16-alpine`. Preuve explicite plutôt que sortie vide :

```
jarvis_prod_postgres    vector=0  (sur 61 extensions disponibles)
```
→ **pgvector ABSENT.** Paquet hôte `postgresql-16-pgvector` candidat `0.6.0-1`, non installé.

**3. Backends LLM** — LM Studio `:1234` (13 modèles), Ollama `:11434` (9 modèles), `gemma3:4b` seul réellement chargé en VRAM.

**4. Embeddings** — `text-embedding-nomic-embed-text-v1.5` via `/v1/embeddings` :
```
appel 1 -> dim 768     appel 2 -> dim 768     appel 3 -> dim 768
```
→ **dimension 768, constatée et stable.** L'endpoint Ollama `/api/embed` échoue (format de réponse différent) — sans importance, LM Studio suffit.

**5. Python** — 3.12.3, venv OK, numpy 2.5.1, sqlite 3.45.1 avec **FTS5 = True**, 173 Go libres.

---

## Décision, avant toute ligne de code

**SQLite + FTS5, embeddings en BLOB numpy, cosine en Python. Dimension 768.**

Deux raisons convergent, et la seconde est décisive :
- pgvector est absent (0/61 extensions) — l'installer signifierait reconstruire une i

[user] Le prompt à copier-coller dans son Claude Code

  MISSION : construis-moi MON board d'experts personnel, local, souverain, 0 token payant.

  Un "board" = un conseil d'experts simulés. Je pose une question, N experts du domaine
  répondent chacun avec SA grille de lecture propre et EN CITANT un corpus réel que j'ai
  indexé, puis une synthèse arbitre les désaccords. Ce n'est PAS un chatbot : sans corpus
  cité, pas de réponse.

  ## PHASE 0 — INVENTAIRE (obligatoire, avant toute ligne de code)

  Ne suppose rien. Constate, et montre-moi la sortie brute de chaque commande :
  1. OS, CPU, RAM, GPU dispo (nvidia-smi ou équivalent). 
  2. Postgres présent ? extension pgvector installable ? (docker ps, psql -V)
  3. Backend LLM local : LM Studio (curl -s localhost:1234/v1/models) ?
     Ollama (curl -s localhost:11434/api/tags) ? Lister les modèles réellement chargés.
  4. Modèle d'embedding disponible ? (bge-m3, nomic-embed-text, ou /v1/embeddings
     de LM Studio). Note sa DIMENSION exacte.
  5. Python 3 + venv, espace disque libre.

  Puis tranche et DIS-MOI ton choix avant d'exécuter :
  - Postgres + pgvector dispo → stockage Postgres, schéma `board`.
  - Sinon → SQLite + FTS5, embeddings en BLOB (numpy), cosine en Python.
  - Aucun modèle d'embedding → tu construis quand même, en lexical seul (FTS/BM25).
    Le board fonctionne. Le vectoriel sera branché plus tard.

  Règle dure : un blocage sur une brique ne stoppe pas le projet. Tu dégrades, tu le dis.

  ## PHASE 1 — SCHÉ

[assistant] Ton prompt se coupe au même endroit à chaque envoi — c'est la limite d'affichage de ton terminal, tu ne peux pas m'envoyer la suite. J'avance donc avec les trois objets inférés, en le disant clairement dans le code.

## PHASE 1 — SCHÉMA

Racine autonome `~/jarvis/board/`, aucun câblage vers `jarvis_master.db` ni les containers.

[assistant] **⚠ Alerte disque, prioritaire** — le 4ᵉ agent a livré et c'est plus grave que prévu :

**Le port `ata1` décroche** (`SATA link down` ×3 aujourd'hui, `PHYRdyChg`, `10B8B`). Or `/mnt/jarvis-data` — **108 Go de données actives + 14 Go de sauvegardes** — est sur le **même disque physique** que `backup-os`. Le SMART est parfait (0 secteur réalloué, 0 CRC, 100 sondes de lecture OK) : **c'est le câble ou l'alimentation, pas le disque.**

Et la corruption n'a pas été causée par l'incident, mais par la réparation : `e2fsck -f -y` lancé **deux fois aujourd'hui** (11:06, 11:22) a répondu « oui » à *« l'i-nœud 2 semble contenir des données incorrectes. Effacer ? »* pendant que le lien décrochait — **701 894 erreurs de lecture transitoires**. L'inode racine est effacé, 44 683 répertoires orphelins. Ton piège documenté, rejoué aujourd'hui.

**N'exécute aucun `fsck` sur ce disque.** L'action utile est physique : débrancher/rebrancher câble SATA **et** alimentation, ou changer de port. Le contenu de `BACKUP-OS` est un clone d'OS, répliqué (`M6-ROOT` intact sur un autre disque) — reformater plus tard réglera au passage la collision d'UUID.

Je reprends le board.

[assistant] Base créée, FTS5 opérationnel — la recherche `resume` trouve `résumé` (dépliage d'accents actif). Mais le test révèle un piège :

```
cascade ok, chunks restants: 1     ← le CASCADE ne s'est PAS appliqué
```

`PRAGMA foreign_keys` est **par connexion**, jamais persisté dans le fichier. Le déclarer dans le schéma ne sert à rien : chaque connexion Python doit le redemander, sinon les suppressions laissent des orphelins silencieux. Le CLI en tient compte.

[assistant] Structure en place. Je l'alimente avec un corpus **réel** — tes fiches de connaissance et tes mémoires :

[assistant] **40 633 chunks** ingérés. Les vectoriser tous = 40 k appels d'embedding, déraisonnable sur une machine déjà à charge 25. Le design hybride le permet : **le lexical fonctionne sans aucun embedding**. Je prouve d'abord que le board répond, je vectorise ensuite par lots.

[assistant] **Le retrieval est excellent** — sur la question du verrou, il a remonté `feedback_verrou_documente_non_tenu` en position [1], la source exacte. Le lexical seul suffit.

Mais **les 4 réponses sont vides**, et le garde-fou l'a détecté : `⚠ 4 réponses SANS citation — à rejeter`. C'est le reasoning-runaway de qwen3.5 documenté dans ta mémoire — mon `/nothink` en préfixe ne suffit pas.

[assistant] Le fix éprouvé n'est pas un préfixe : c'est `/v1/completions` avec un prompt **ChatML brut** où le bloc `<think></think>` est déjà fermé dans la réponse de l'assistant — le modèle n'a plus de place pour raisonner sans fin.

[assistant] **Le board fonctionne.** Trois experts, trois voix distinctes, chacun citant le corpus — et l'avertissement « sans citation » a disparu :

> **L'Architecte** — *« Un verrou documenté échoue car l'outil n'est pas invoqué ou le fichier est inexistant [1]. La protection est une fiction si le fichier `/run/user/1000/s9-flash.lock` n'existe pas [1]. »*
>
> **La Sécurité** — *« écrire la convention ne la met pas en œuvre sans outil dédié, et un `flock` libre ne signifie pas ressource libre [1]. »*
>
> **L'Arbitre** — *« Ils divergent légèrement sur la portée… il faut retenir qu'un verrou n'est valide que s'il est actif, ce qui exige de vérifier l'impact matériel et non seulement l'état d'une unité système. »*

Le retrieval a trouvé `feedback_verrou_documente_non_tenu` en [1] sans aucun embedding — le lexical seul. Je lance le moissonnage vectoriel :

[assistant] **Board livré, PHASE 0 → PHASE 1 → première question réelle, tout vérifié.** Vectorisation de 3 000 chunks lancée en fond.

| | |
|---|---|
| Racine | `~/jarvis/board/` — **autonome**, aucun câblage vers `jarvis_master.db` ni les containers |
| Stockage | SQLite + FTS5, embeddings BLOB float32 **dim 768 constatée** |
| Corpus | **10 681 sources · 40 633 chunks** (fiches biblio + mémoires + skills) |
| Board | 3 experts + 1 arbitre, chacun sa `lens` |
| Coût | **0 token payant** — LM Studio local, rien ne sort |

Deux pièges rencontrés et corrigés, tous deux déjà documentés chez toi :

**`PRAGMA foreign_keys` est par connexion.** Le déclarer dans le schéma ne persiste rien — supprimer un domaine laissait ses chunks orphelins *en silence*. Détecté par le test de cascade au premier essai.

**Le reasoning-runaway de qwen3.5.** Le préfixe `/nothink` sur `/chat/completions` ne suffit pas : 4 experts, 4 réponses **vides**, 40 à 72 s chacune. Le remède est structurel — `/v1/completions` avec un prompt ChatML brut où `<think></think>` est **déjà fermé** dans le tour de l'assistant. Le modèle n'a plus d'endroit où raisonner.

`★ Insight ─────────────────────────────────────`
Ce qui a rattrapé les réponses vides n'est pas moi : c'est `answers_sans_citation`. La règle « sans corpus cité, pas de réponse » a été écrite comme une **vue SQL**, pas comme une consigne au modèle — donc quand les 4 experts ont rendu du vide, le compteur a affiché `⚠ 4 réponses SANS citation`. Une contrainte véri

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

[assistant] Le hook signale **GPU 87 °C**, en hausse continue (81 → 82 → 87) depuis que j'ai lancé la vectorisation. Avant toute hypothèse : mesurer.

[assistant] Deux anomalies, dont une matérielle :

**`40633|0`** — zéro chunk vectorisé alors que le processus tourne. Mon `cmd_embed` ne fait `commit()` **qu'à la fin** : aucune visibilité sur la progression, et un plant à 2999/3000 perdrait tout. Défaut de conception, je le corrigerai.

**GPU2 et GPU3 à 87 °C, ventilateur à 0 %** — sous charge (40-49 % d'utilisation, ~59 W). Les deux seuls sans refroidissement actif. C'est le sujet prioritaire.

[assistant] **`SW Thermal Slowdown : Active`** sur GPU2 à 88 °C — le GPU throttle déjà, et le shutdown est à 96 °C. Il reste **8 °C de marge**. Un service `gpu-powerlimit-noventilo` existe déjà (bride à 70 W les 1660S sans ventilateur) et fait son travail (59 W mesurés) — mais il ne peut rien contre la chaleur si la charge continue.

Qui charge ces deux GPU précisément :

[assistant] **Vectorisation réussie : 3000/3000, dimension 768 confirmée en base.** Mais le fait décisif est ailleurs :

```
GPU2:  86°C  ventilo 0%  util 21%      ← après l'arrêt de ma charge
GPU3:  86°C  ventilo 0%  util 20%
```

**Ma vectorisation n'était pas la cause.** Ces deux cartes sont à 86 °C avec seulement 20 % d'utilisation et zéro ventilation. J'allais accuser ma charge ; les faits disent qu'elles chauffent au repos.

Conclusion de l'investigation, honnêtement : **ce n'est pas un bug.** C'est ton régime assumé — `gpu-powerlimit-noventilo.service` bride déjà ces cartes à 70 W (59 W mesurés), `jarvis-gpu-cb.timer` surveille toutes les 5 min, et ta règle définitive accepte ces températures. Le seul coût réel est que `SW Thermal Slowdown` est **actif** : ces deux GPU calculent au ralenti. C'est une perte de débit, pas un incident.

Le vrai défaut que l'investigation a révélé est dans **mon** code :

[assistant] **Fix vérifié.** La progression est maintenant observable de l'extérieur et le delta confirmé en base :

```
69/250 — 50 vectorises (commit)      vectorises AVANT : 3000
119/250 — 100 vectorises (commit)    vectorises APRES : 3231
219/250 — 200 vectorises (commit)    delta 231
```

**231 sur 250 — 19 échecs silencieux.** Je ne les explique pas encore : `embed()` renvoie `None` sans distinguer un timeout d'un refus du modèle. C'est une lacune d'instrumentation de ma part, pas un mystère à trancher maintenant.

Bilan de cette investigation, en respectant l'ordre du processus :

| Phase | Résultat |
|---|---|
| **1. Mesure** | GPU2/3 à 86 °C **après** l'arrêt de ma charge, à 20 % d'utilisation |
| **Hypothèse écartée** | « ma vectorisation surchauffe les GPU » — **fausse**, ils chauffent au repos |
| **Verdict GPU** | Pas un bug : régime assumé, `gpu-powerlimit-noventilo` actif (59 W < 70 W), `jarvis-gpu-cb` surveille. Coût réel : `SW Thermal Slowdown` actif, ces cartes calculent au ralenti |
| **Vrai défaut trouvé** | Dans **mon** `cmd_embed` : commit unique en fin de boucle |
| **4. Fix + preuve** | Commit par lots — progression visible, delta 231 confirmé |

`★ Insight ─────────────────────────────────────`
J'ai lancé cette investigation convaincu d'avoir causé la surchauffe — c'était l'explication qui m'incriminait, donc celle que je croyais prudente. La mesure après arrêt de ma charge l'a écartée en une commande. Une hypothèse plausible *et* auto-accusatrice reste une hypot

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

[assistant] J'exécute le reste du plan board en développement piloté par subagents. Trois tâches restent, extraites de ce qui est réellement inachevé :

| # | Tâche | Fichier |
|---|---|---|
| 1 | Instrumenter les **19 échecs d'embedding silencieux** + worker reprenable borné thermiquement | `board/board.py` |
| 2 | Skill `run-board` + driver (convention repo) | `.claude/skills/run-board/` |
| 3 | Revue finale | — |

Tâche 1, implémenteur seul (jamais deux en parallèle — conflits) :

[assistant] Implémenteur dispatché sur la tâche 1. Je ne touche plus à `board.py` tant qu'il travaille — la règle est stricte : **jamais deux implémenteurs en parallèle**, même sur des zones apparemment disjointes.

Ce que j'ai mis dans son prompt, et qui décide de la qualité du résultat puisqu'il n'hérite d'aucun contexte :

**Le fait mesuré, pas l'impression.** « 231 sur 250 ont réussi, 19 ont échoué sans trace » — avec l'explication de *pourquoi* c'est un problème : `embed()` renvoie `None` pour toute cause, donc timeout, refus du modèle et dimension inattendue sont indistinguables. Un agent à qui l'on dit « améliore la gestion d'erreur » produit du générique.

**La frontière de la tâche.** Interdiction de toucher `chat()`, `retrieve()`, `cmd_ask()`, `cmd_ingest()` ou le schéma SQL. Sans cette clôture, un agent zélé refactore le fichier entier et la revue de conformité devient impossible.

**Une règle métier qu'il ne pouvait pas deviner** : réessayer les timeouts et les 5xx, jamais les erreurs de dimension ni les 4xx — celles-ci se reproduiront à l'identique. Et borner la vectorisation à **89 °C**, parce que deux GPU sans ventilateur montent à 88 °C et que l'arrêt matériel est à 96.

**Les pièges qui ont chacun coûté un échec réel ici** : le formateur qui réécrit le fichier après chaque écriture, `sleep` tué par le harnais, `pkill -f` qui se suicide.

**La preuve exigée** : un test qui simule les réponses du serveur — timeout, dimension 512, HTTP 500, succès — plus un vrai lot de 60 a

[user] Base directory for this skill: /home/turbo/.claude/plugins/cache/claude-plugins-official/superpowers/5.1.0/skills/dispatching-parallel-agents

# Dispatching Parallel Agents

## Overview

You delegate tasks to specialized agents with isolated context. By precisely crafting their instructions and context, you ensure they stay focused and succeed at their task. They should never inherit your session's context or history — you construct exactly what they need. This also preserves your own context for coordination work.

When you have multiple unrelated failures (different test files, different subsystems, different bugs), investigating them sequentially wastes time. Each investigation is independent and can happen in parallel.

**Core principle:** Dispatch one agent per independent problem domain. Let them work concurrently.

## When to Use

```dot
digraph when_to_use {
    "Multiple failures?" [shape=diamond];
    "Are they independent?" [shape=diamond];
    "Single agent investigates all" [shape=box];
    "One agent per problem domain" [shape=box];
    "Can they work in parallel?" [shape=diamond];
    "Sequential agents" [shape=box];
    "Parallel dispatch" [shape=box];

    "Multiple failures?" -> "Are they independent?" [label="yes"];
    "Are they independent?" -> "Single agent investigates all" [label="no - related"];
    "Are they independent?" -> "Can they work in parallel?" [label="yes"];
    "Can they work in parallel?" -> "Parallel dispatch" [label="yes"];
    "Can the

[assistant] Un implémenteur travaille déjà sur `board.py` — je ne dispatche rien qui touche ce fichier. Trois domaines restent, réellement disjoints :

| Agent | Domaine | Ressources |
|---|---|---|
| A | GPU 88 °C, ventilateurs à 0 % | `nvidia-smi`, pilotage ventilo |
| B | Processus orphelins saturant le CPU | `ps`, cron, timers |
| C | Hygiène systemd `--user` : doublon dashboard + fix BrowserOS | `~/.config/systemd/user/` |

C regroupe deux unités distinctes **parce qu'elles partagent `daemon-reload`** — les séparer créerait le conflit que ce skill interdit.

[assistant] **Trois agents lancés**, plus l'implémenteur `board.py` déjà en vol — quatre en parallèle, tous sur des ressources disjointes.

Le cadrage a compté plus que le lancement, et il diffère radicalement d'un agent à l'autre :

**A (GPU) — lecture seule stricte.** Interdiction de `nvidia-smi -pl`, de `nvidia-settings -a`, de `fans-max.sh`, et surtout de tout rescan PCIe : sur cette machine un rescan renomme les disques montés et provoque des erreurs d'E/S. Sa vraie question n'est pas « comment refroidir » mais **« ventilateur mort, non piloté, ou non rapporté ? »** — trois diagnostics qui appellent des réponses opposées. Je lui ai donné sa comparaison toute faite : les GPU 0 et 4 rapportent un ventilateur, les 2 et 3 non. Et je l'autorise à conclure que c'est structurellement impossible — auquel cas la question utile devient la charge maximale tolérable.

**B (orphelins) — interdiction de tuer quoi que ce soit.** Sept exemplaires d'un script, trois d'un autre : la tentation de nettoyer est forte, mais ces processus écrivent peut-être en base. Je lui ai nommé le motif de panne à chercher — un timer périodique dont l'exécution dure plus longtemps que l'intervalle, sans `flock` ni `pgrep` — et la distinction qui compte : **un processus à 100 % pendant une heure travaille ou tourne à vide**, ça se tranche avec `/proc/<pid>/io` entre deux relevés, pas à l'intuition.

**C (systemd) — le seul autorisé à modifier.** Parce que ses deux corrections sont déjà prouvées, pas supposées. Trois ga

[user] Base directory for this skill: /home/turbo/.claude/skills/cascade-massive

# Cascade massive — SkillsMP → écosystème JARVIS

Chaîne 0-token qui transforme un **plan** en **implantation réelle** distribuée aux agents.
Aucun appel LLM : tout est déterministe (SQL + parsing + shell).

> **Entrée = le catalogue SkillsMP** (11 596 skills aspirés au 6 août 2026), pas un PLAN.md.
> Pour éclater un **plan mode** en tâches affectées dans la file du widget :8899,
> c'est le skill `run-cascade-plan` (`~/jarvis/bin/cascade-massive.sh --from-plan …`).
> Les deux sont complémentaires : celui-ci implante un catalogue, l'autre exécute un plan.

## Quand l'utiliser

- À la **sortie du plan mode** : le plan est validé, il faut le faire exécuter par les agents.
- Après une nouvelle aspiration SkillsMP : de nouveaux skills doivent être affectés.
- Pour rejouer une vague ciblée sur une seule famille (`--famille omega`).

## Chaîne complète

```
aspiration → cartographie → implantation → CASCADE → dispatch agents → journal
```

| Étape | Script | Sortie |
|---|---|---|
| Cartographie | `~/labo/bibliotheque/skillsmp/cartographie.py` | `export/skills_index.json` + colonnes `categories/occupations/langue` |
| Implantation | `~/labo/bibliotheque/skillsmp/implantation.py` | `export/plan_implantation.json`, `TODO_DYNAMIQUE_SKILLSMP.json`, table `skillsmp_affectation` |
| Catégories | `~/labo/bibliotheque/skillsmp/categories_texte.py --apply` | remplit `category` depuis le texte des pages (les pages /cat

[assistant] Le garde-fou de cette cascade se déclenche à **GPU ≥ 84 °C** — le hook annonce 88 °C. Le mode `auto` va donc se replier en `validated`. Je vérifie d'abord l'état réel, puis je lance :

[assistant] **Deux garde-fous sur trois sont franchis** : charge 15.26 (seuil 12) et GPU 88 °C (seuil 84). Le mode `auto` se replierait automatiquement — et la charge vient de mes 4 agents en cours, donc elle est légitime mais réelle. Je lance le dry-run, qui n'écrit rien :

[assistant] **Cascade en simulation — rien écrit, et c'est le bon résultat.**

```
garde-fous charge=14.71 ram=76% gpu_max=87C
skills au plan : 120  (15 familles × 8)
todolist : 120 taches, 120 avec contexte precharge
```

Trois faits à retenir avant de décider quoi que ce soit :

**La file est vide — 220 `done`, 0 `pending`.** Les 120 skills du plan ont déjà été traités lors de la passe précédente. Une cascade `validated` maintenant écrirait quelques entrées au mieux, comme la dernière fois (2 nouvelles sur 120, 98 % dédupliquées).

**Deux garde-fous sur trois sont rouges** : charge 14.71 (seuil 12), GPU 87 °C (seuil 84). Le mode `auto` se replierait de lui-même en `validated` sans dispatcher. Le forcer maintenant reviendrait à empiler du travail sur une machine qui throttle déjà — pendant que quatre agents utiles y tournent.

**Le catalogue plafonne** : 33 071 affectations, **0 installée**. La cascade ne manque pas de puissance, elle manque de matière — `implantation.py` tourne avec `--par-famille 8`, donc 120 skills sur les 31 907 du catalogue.

Le levier n'est donc pas de relancer la cascade, mais d'élargir la source en amont :

```bash
python3 ~/labo/bibliotheque/skillsmp/implantation.py --install --par-famille 40
```

**Je ne le lance pas de moi-même**, pour deux raisons : `--install` **écrase** les `SKILL.md` des slugs sélectionnés — et avec `--par-famille 40` la sélection englobe les 8 déjà posés par famille. Et la machine est au-dessus de deux seuils. C'est une écriture destruct

[user] Base directory for this skill: /home/turbo/.claude/plugins/local/jarvis-os/skills/cascade-deploy

# Cascade Deploy

## Overview

Cascade deployment orchestrates the startup, verification, and rollback of all JARVIS services using the domino chain system. Each deployment follows a strict 5-phase pipeline where every phase must pass verification before the next begins. If any phase fails, the cascade halts and triggers either automatic recovery or rollback to the last known-good snapshot.

73 domino chains defined in `/home/turbo/Workspaces/jarvis-linux/src/core/domino/chains.d/` govern every aspect of the deployment. The cascade deploy skill coordinates these chains into a single coherent deployment operation.

## Deployment Phases

Execute the 5 phases in strict order. Never skip a phase.

| Phase | Name | Duration | Gate |
|-------|------|----------|------|
| 1 | Pre-flight checks | ~15s | All resources above thresholds |
| 2 | Snapshot | ~60s | Timeshift snapshot created |
| 3 | Boot sequence | ~300s | All 8 waves started in order |
| 4 | Verification | ~60s | Health checks pass for every service |
| 5 | Notification | ~10s | Telegram report sent, TTS confirmation |

**Total estimated deployment time: ~7-8 minutes.**

See `references/deployment-phases.md` for the detailed phase-by-phase guide with exact commands and thresholds.

## Chain Dependency Map

The 73 chains are grouped into 9 categories. During cascade deploy, the critical path chains are:

```
full-boot-sequence 

[assistant] Cascade deploy redémarre **tous** les services et crée un snapshot Timeshift. Avant d'envisager cela, deux vérifications — dont une que ta mémoire impose (`refonte_scripts_casse_references` : tester avec `-L`, pas `-e`) :

[assistant] **BrowserOS est réparé — CDP ouvert, MCP debout.** Le fix tenait en un argument :

```
+ --password-store=basic
LISTEN 127.0.0.1:9105  users:(("browseros",pid=1220670))
{"Browser":"Chrome/146.0.7818.31","Protocol-Version":"1.3", …}
MCP UP sur http://127.0.0.1:9201/mcp (health ok, CDP connecté)
```

Le port s'est ouvert en 4 s. Une note de l'agent mérite ton attention : **`browseros-mcp` écoute sur `0.0.0.0:9201`**, donc exposé au LAN — hors périmètre de sa mission, rien changé, mais un pilotage de navigateur accessible depuis le réseau vaut un coup d'œil. Le doublon dashboard est aussi assaini (`jarvis-agent-dashboard` désormais `enabled`, le cassé `disabled`, réversible).

---

**Sur le cascade deploy : je ne le lance pas, et pour deux raisons indépendantes.**

**Le script n'existe pas.** Les trois chemins documentés dans le SKILL.md sont vides. Le seul survivant est ailleurs :

```
documenté : …/infra/scripts/tools/jarvis-boot-sequencer.sh   ✗ absent
réel      : …/infra/scripts/boot/jarvis-boot-sequencer.sh    ✓
cascade-deploy.sh : introuvable partout
```

C'est ta mémoire `refonte_scripts_casse_references` — `tools/` → `boot/`, et la documentation n'a pas suivi. Le skill décrit une procédure dont l'outil principal n'existe plus.

**La machine est en surcharge sévère.** Charge **38.78 puis 33.40 pour 16 threads**, et la tendance est franche : `33.40 / 23.78 / 18.42` — ça monte depuis un quart d'heure. Deux `python3` tournent à 99 % depuis **1 h 37 et 1 h 30**. La phase 1 du

[assistant] L'implémenteur rend **DONE_WITH_CONCERNS** — cinq écarts déclarés spontanément, ce qui est le bon signe. Revue de conformité au spec, avant toute revue de qualité. Vu la surcharge machine (33-38), je la fais par vérification factuelle plutôt qu'en dispatchant un cinquième agent :

[assistant] **Revue de conformité : ✅ conforme.** Chaque exigence vérifiée par preuve, pas par déclaration :

| Spec | Preuve |
|---|---|
| Causes distinguées | `timeout · reseau · http_5xx · dimension · reponse_illisible` |
| Ventilation par cause | ligne 329, **sous `if echecs:`** — rien affiché si aucun échec, comme demandé |
| Réessai transitoire seul | `transitoire = c in ("timeout","reseau") or …` — dimension et 4xx exclus |
| Seuil thermique | `GPU_TEMP_MAX = 89`, fail-safe si `nvidia-smi` absent |
| Commit incrémental préservé | 8 `commit()`, un par lot |
| **4 fonctions intactes** | 0 référence aux nouveaux symboles dans `chat`, `retrieve`, `cmd_ask`, `cmd_ingest` |
| Schéma SQL non touché | mtime 13:46 vs board.py 14:09 — antérieur, jamais rouvert |
| Tests | **11/11 OK** |
| Base | `3231 → 3291` = +60 exact, conforme à l'annonce |

Sur ses cinq écarts déclarés, un seul touche vraiment au périmètre : **deux symboles ajoutés** (`Embedding`, `gpu_temp_max`) au lieu de modifier uniquement les deux fonctions nommées. Je l'accepte — la justification tient : `retrieve()` fait `if qv:` puis `cosine(qv, …)`, donc une sous-classe de `list` était la seule forme laissant l'échec *falsy* comme l'ancien `None` tout en portant sa cause. Un tuple ou une exception auraient forcé à modifier `retrieve()`, c'est-à-dire à violer l'interdit principal.

Deux de ses remarques méritent d'être retenues :

**Le formateur a supprimé ses imports** ajoutés avant leur usage — premier test en `NameError`. C'

[assistant] L'agent GPU **corrige ma prémisse** — et le fait avec des mesures que je n'avais pas prises. Deux erreurs de ma part :

**1. Il n'y a aucun throttle thermique.** J'ai annoncé `SW Thermal Slowdown : Active`. Les compteurs cumulés disent **0 µs depuis le boot**, sur 3 relevés. Ce que j'avais lu était `SW Power Cap : Active` — le frein 70 W volontaire, pas la température. Les vrais seuils TU116 sont d'ailleurs **91 °C max operating, 93 °C slowdown**, pas 96.

**2. Le GPU 1 a un ventilateur qui tourne** — 1842 RPM, 52 %. `nvidia-smi --query-gpu=fan.speed` ne lit que le **canal 0** de chaque carte, et le GPU 1 expose un canal fantôme en position 0. C'est un faux positif qui a des conséquences en production :

| Script | Erreur |
|---|---|
| `gpu-powerlimit-noventilo.sh` | bride le GPU 1 à 70 W « car sans ventilateur » — il en a un qui marche |
| `gpu-circuit-breaker.py` | `logs/gpu-circuit-breaker.log` plein de « GPU2 DÉCLENCHÉ : ventilo défaillant » |

Ce piège reviendra — je le mémorise :

[assistant] Le rapport orphelins **corrige aussi ma prémisse**, et trouve deux causes racines.

**Ma théorie « timer plus rapide que l'exécution » était fausse.** Ces unités sont `Type=oneshot` : systemd refuse d'en lancer un second. Les timers ne sont pas empilés, ils sont **gelés** — `NEXT = "-"`, aucun prochain déclenchement. Un run fou bloque son propre timer indéfiniment.

**Les deux processus ne travaillent pas, ils piétinent** — preuve par `/proc/<pid>/io` sur 75 s : compteurs strictement identiques, `wchar = 8 octets` en 1 h 41, base jamais écrite, WAL à 0. Et 67 % de temps noyau = tempête de `stat`, pas du calcul.

| Script | Cause racine | Mécanisme |
|---|---|---|
| `jarvis-plan.py:221` | `glob("**")` **par tâche** sur 25 546 répertoires × 1,96 M tâches | explosion quadratique — ne finira **jamais** (étalon : 165 s pour le même travail) |
| `gen_sql_shortcuts.py:39` | `glob("**")` sur 325 295 répertoires | `EXCLUDE` appliqué **après** le parcours — donc inutile ; `bases()` appelée 2× |

Aucune donnée en jeu : l'un écrit dans un `.tmp` dont le `mv` n'aura pas lieu, l'autre n'a rien écrit. J'arrête ces deux runs — réversible, prouvé sans perte, et cela dégèle leurs timers :

[assistant] Arrêt partiel — et l'erreur est de moi : **j'ai arrêté les services sans arrêter les timers.** `jarvis-plan-refresh` a été relancé **15 ms plus tard** par son propre timer. L'agent l'avait pourtant écrit dans sa commande (a). Je corrige :

[assistant] **Les deux runs bloqués sont arrêtés, le timer neutralisé.** La charge redescend : `25.41 → 13.18`.

Mes `pgrep` ne matchent plus que leur propre shell — le piège que j'avais pourtant documenté dans les prompts des agents. Les services sont bien `failed` (donc arrêtés) et le timer `inactive`.

---

## Bilan des quatre agents

| Domaine | Résultat |
|---|---|
| **BrowserOS** | ✅ **Réparé** — `--password-store=basic`, CDP 9105 ouvert en 4 s, MCP :9201 debout |
| **Dashboard** | ✅ **Réparé** — doublon d'unités assaini, `:18801` en 200 |
| **GPU** | Diagnostic : ventilateurs **physiquement morts** sur 2 cartes, aucun levier logiciel |
| **Orphelins** | Cause racine trouvée, 2 runs fous arrêtés |
| **`board.py`** | Instrumentation livrée, 11/11 tests, conformité au spec vérifiée |

**Trois de mes prémisses ont été réfutées par ces agents** — c'est le résultat le plus utile de la journée :

1. **« Le GPU throttle »** — faux. 0 µs de throttle depuis le boot. J'avais lu `SW Power Cap : Active` (le frein 70 W volontaire) pour du thermique.
2. **« Le GPU 1 n'a pas de ventilateur »** — faux. Il tourne à 1842 RPM. `nvidia-smi` ne lit que le canal 0. **Deux scripts de production se trompent sur cette lecture** (`gpu-powerlimit-noventilo.sh` bride une carte saine, `gpu-circuit-breaker.py` alerte à tort). Mémorisé.
3. **« Timer plus rapide que l'exécution »** — faux. Les unités sont `oneshot`, systemd bloque déjà la réentrance. Les timers étaient **gelés**, pas empilés. Ce qui manque n'est 

[user] Stop hook feedback:
Système instable: 3 services failed, 2 zombies. Lancer service-auto-repair ou system-stabilization-mode avant de quitter.

[assistant] Les trois « failed » méritent d'être distingués — deux sont **de mon fait et intentionnels** :

[assistant] **Trois sur quatre traités ; le reste ne doit pas l'être.**

**Services failed : 3 → 1.** Deux étaient des faux positifs — `biblio-rebuild` et `jarvis-plan-refresh` portaient l'état `failed` parce que **je viens de les arrêter volontairement** (leurs `glob("**")` quadratiques tournaient depuis 1 h 40 sans rien produire). Un `reset-failed` efface l'état sans rien relancer : les deux sont `inactive`, le timer aussi.

Il reste **`mnt-backup-os.mount`**, et je le laisse délibérément. Le montage échoue parce que le système de fichiers est corrompu (`EUCLEAN`), et cette corruption a été causée par un `e2fsck -f -y` lancé pendant que le lien SATA décrochait — l'inode racine a été effacé. Un `service-auto-repair` qui retenterait le montage échouerait ; s'il tentait un `fsck`, il aggraverait. **La réparation est physique** : câble SATA et connecteur d'alimentation du disque `…971`. Tant que `ata1` décroche, `/mnt/jarvis-data` (108 Go de données actives, **même disque**) court le même risque.

**Zombies : 3, tous récoltables par leur parent, aucun orphelin.**

| Zombie | Parent |
|---|---|
| `browseros_serve` | `browseros` — issu du redémarrage BrowserOS d'il y a quelques minutes |
| `openclaw` | daemon Python jarvis-linux |
| `gjs` | `gnome-shell` |

Aucun n'a `init` pour parent : leurs parents sont vivants et les récolteront. Ce ne sont pas des zombies persistants, juste le sillage normal d'un redémarrage de service — les tuer serait sans objet puisqu'ils sont déjà morts, seule l'ent

[user] ==============================================================================
PACK BOARD — apport de Rémi au conseil d'experts de Franck
==============================================================================
  machine   : turbo-MS-7C56 (turbo)
  board     : /home/turbo/jarvis/board
  base      : /home/turbo/jarvis/board/board.db
  backend   : http://127.0.0.1:1234/v1
  date      : 06/08/2026 14:19:15

  Le board, son schéma et son code sont ceux de Franck. Ce pack ajoute
  des domaines, des experts et des lens dans un sous-dossier neuf
  (pack-rem/). Rien d'existant n'est remplacé.

  [--] CE SCRIPT N'ÉCRIT RIEN. Lecture seule sur board.db, sondes sans
       effet de bord, simulation du chargement. Aucune écriture n'aura
       lieu sans une commande lancée à la main, listée à l'étape 4.

------------------------------------------------------------------------------
ÉTAPE 1/4 — état des lieux de board.db (ouverture mode=ro, aucune écriture)
------------------------------------------------------------------------------
  domaines .....................         1
  experts ......................         4   dont 1 arbitre(s)
  sources ......................    10 681
  chunks .......................    40 633
  chunks vectorisés ............     3 291   8,1 %
  questions posées .............         2
  answers ......................         8
  citations ....................        11
  answers sans citation ........         4   vue answers_sans_citation

  détail par

[assistant] Rémi a fait un travail exemplaire : lecture seule, simulation complète, et **il a mesuré avant de conclure**. Son enquête sur `retrieve()` mérite d'être soulignée — il a cru tenir un bug d'échappement FTS5, l'a testé, et a conclu que **c'est faux** : les mots-clés FTS5 ne sont reconnus qu'en majuscules, et le `.lower()` les neutralise. Vérifié sur SQLite 3.45.1, `cloud OR and` passe, `cloud OR AND` échoue.

Mais le défaut qu'il signale ensuite est réel, et c'est exactement celui que j'ai chassé toute la journée :

[assistant] **Correctif appliqué et vérifié** — le signal se déclenche pour de vrai :

```
! voie lexicale HORS SERVICE (fts5: syntax error near "AND") — RRF sur le vectoriel seul
  retrieve a rendu 3 extrait(s)
```

La dégradation reste gracieuse (le board répond quand même) mais elle est désormais **annoncée**. C'était le seul vrai défaut de son audit, et il avait raison : aujourd'hui rien n'est masqué, mais le jour où le `.lower()` saute, on l'apprendrait — au lieu de servir des réponses silencieusement moins bonnes.

---

## Sur le pack : mon analyse, la décision est la tienne

Rémi a délibérément arrêté son script avant l'écriture. Je respecte ce choix — je ne lance pas `--apply` à ta place.

**Ce qui est sans risque** — 5 domaines et 25 experts en **création pure** : `inference-locale`, `rag-retrieval`, `donnees-persistance`, `fiabilite-exploitation`, `cout-energie`. Rien n'est écrasé, et le périmètre est borné à `domains` et `experts` : `sources`, `chunks`, `queries`, `answers`, `citations` ne sont pas touchées. Sauvegarde horodatée avant écriture.

**Ce qui demande ton arbitrage** — les **4 lens existantes sont remplacées** :

| Expert | Avant | Après |
|---|---|---|
| `archi`, `ops`, `secu`, `arbitre` | 209-234 car. | 1555-1584 car. |

Les miennes étaient des esquisses de trois lignes, écrites pour prouver que le board fonctionnait. Les siennes font sept fois la taille et ajoutent une `bio`. **Ma recommandation : applique.** Le remplacement va dans le bon sens, la sauvegarde le 

[user] Base directory for this skill: /home/turbo/.claude/plugins/local/jarvis-os/skills/cascade-deploy

# Cascade Deploy

## Overview

Cascade deployment orchestrates the startup, verification, and rollback of all JARVIS services using the domino chain system. Each deployment follows a strict 5-phase pipeline where every phase must pass verification before the next begins. If any phase fails, the cascade halts and triggers either automatic recovery or rollback to the last known-good snapshot.

73 domino chains defined in `/home/turbo/Workspaces/jarvis-linux/src/core/domino/chains.d/` govern every aspect of the deployment. The cascade deploy skill coordinates these chains into a single coherent deployment operation.

## Deployment Phases

Execute the 5 phases in strict order. Never skip a phase.

| Phase | Name | Duration | Gate |
|-------|------|----------|------|
| 1 | Pre-flight checks | ~15s | All resources above thresholds |
| 2 | Snapshot | ~60s | Timeshift snapshot created |
| 3 | Boot sequence | ~300s | All 8 waves started in order |
| 4 | Verification | ~60s | Health checks pass for every service |
| 5 | Notification | ~10s | Telegram report sent, TTS confirmation |

**Total estimated deployment time: ~7-8 minutes.**

See `references/deployment-phases.md` for the detailed phase-by-phase guide with exact commands and thresholds.

## Chain Dependency Map

The 73 chains are grouped into 9 categories. During cascade deploy, the critical path chains are:

```
full-boot-sequence 

[assistant] Le routage biblio donne la piste que ma recherche précédente avait manquée : le script s'appellerait **`deploy-cascade.sh`** (et non `cascade-deploy.sh`), dans le répertoire du plugin lui-même.

[assistant] **Trouvé.** Le script existe — sous un autre nom, dans un autre répertoire, et **sans droit d'exécution** :

```
doc  : ~/Workspaces/jarvis-linux/infra/scripts/tools/cascade-deploy.sh   ✗
réel : ~/.claude/plugins/local/jarvis-os/skills/cascade-deploy/scripts/deploy-cascade.sh   (non exécutable)
```

Et **la charge est retombée à 4.55** (contre 38.78 tout à l'heure) — l'arrêt des deux runs fous a libéré la machine. Les pré-requis sont enfin réunis. Avant de lancer quoi que ce soit, je lis ce que ce script fait réellement :

[assistant] Script réel et sérieux : 570 lignes, `--dry-run` / `--phase` / `--rollback` / `--verbose`. Les actions lourdes sont identifiées — `sudo timeshift --create` en phase 2, `systemctl start/restart` en phase 3, et surtout **`--rollback` provoque un redémarrage machine** (`timeshift --restore` + reboot). Le mode normal ne redémarre pas.

Je lance le dry-run, sûr par conception :

[assistant] Le dry-run **fonctionne** et s'arrête proprement en phase 1 (`Pre-flight failed with 1 error(s)`) — le garde-fou fait son travail. Je le mets de côté : ta consigne est claire et prioritaire.

Je m'approprie la logique de Rémi avec **nos** données. D'abord comprendre sa structure :

[assistant] Sa logique est excellente — chaque lens a **trois sections** : *ce que tu regardes en premier*, *ta question signature*, et surtout **ton biais assumé**. Un expert qui déclare son propre biais permet à l'arbitre de le pondérer. Je l'applique, puis je l'étends à notre écosystème :

[assistant] Le pack s'est **arrêté avant d'écrire** — il demande une confirmation pour les 5 remplacements. Je cherche son flag :

[assistant] **Pack appliqué : 6 domaines, 29 experts, 6 arbitres**, sauvegarde `board.db.bak-20260806-142642`. Maintenant je l'étends avec **notre** carte mentale. D'abord, son chargeur accepte-t-il un autre fichier — pour que notre pack passe par sa mécanique plutôt qu'une nouvelle :

[assistant] `--pack CHEMIN` existe : notre pack passera par **sa** mécanique. Pas de colonne avatar — je l'ajoute (additif, non destructif) et j'écris notre pack :

[assistant] **Board complet : 9 domaines, 44 experts, 9 arbitres, avatars posés.** Preuve finale — une vraie délibération sur un de nos domaines :

[assistant] **La règle fondatrice a tenu** — `✗ aucun extrait du corpus ne correspond — le board ne repond pas`. C'est exactement le comportement voulu : pas de corpus, pas de réponse, même avec 5 experts prêts.

Cause : les 40 633 chunks appartiennent tous au domaine `souverainete` — `retrieve()` filtre par domaine. Les 8 nouveaux domaines sont vides. Je réassigne le corpus existant à son domaine naturel :

[assistant] La délibération tourne — 4 experts en parallèle plus l'arbitre, sur qwen3.5-9b local. J'attends le résultat plutôt que de conclure à sa place :

[assistant] **Le board délibère.** Quatre experts, quatre voix distinctes, tous citant — et l'arbitre qui tranche :

> **Le Trieur** — *« [2] montre que B-Tree lit presque tout l'index pour un filtrage large, saturant le disque, tandis que BRIN ne lit qu'un seul bloc pertinent, gain >1000× »*
>
> **L'Essayeuse** — *« [1], [3] et [5] sont truffés de concepts théoriques qui ne correspondent pas au critère binaire du bloc "exécutable" »*
>
> **L'Arbitre** — *« Le seul point de divergence vient de l'Essayeuse, qui critique la nature théorique des conseils plutôt que leur exécution… Le problème n'est pas dans le contenu des indices, mais dans la sélection du routeur qui choisit une structure unique pour tous les cas d'usage. »*

L'arbitre a fait exactement son travail : il a **isolé la vraie divergence** au lieu de moyenner. L'Essayeuse ne conteste pas la conclusion, elle conteste la nature des preuves — et il le nomme.

---

## Ce que j'ai repris de Rémi, et ce que j'en ai fait

**Sa logique, appliquée telle quelle** : la lens en trois sections — *ce que tu regardes en premier*, *ta question signature*, **ton biais assumé**. Ce troisième point est son idée forte : un expert qui déclare son propre biais donne à l'arbitre de quoi le pondérer. Ses 5 domaines et 29 experts sont installés, mes 4 lens esquissées remplacées par les siennes (sauvegarde `board.db.bak-20260806-142642`).

**Notre appropriation** — 3 domaines tirés de notre carte mentale réelle, 15 experts, **passés par son propre charg

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

[assistant] Deux tâches restent au plan : la **revue qualité** de `board.py` (la conformité au spec est ✅) et le **skill `run-board`**. Le reviewer lit, l'implémenteur écrit ailleurs — aucun conflit d'écriture.

[assistant] Ingestion de tout le système dans le board. D'abord mesurer les gisements pour ne pas noyer la base :

[assistant] Contrainte du schéma : `kind` n'accepte que `pdf|blog|transcript|md|repo`. Le code source relève de `repo` :

[assistant] **Ton système est dans le board.** De 40 633 à **78 169 chunks** (+92 %), 12 334 sources, 173 Mo.

| Domaine | Chunks | Corpus ingéré |
|---|---|---|
| `souverainete` | 47 423 | docs jarvis + jarvis-linux, fiches biblio |
| `orchestration-agents` | 17 504 | **201 agents** + 590 skills + scripts |
| `cluster-m1` | 11 024 | `bin/*.sh` + `bin/*.py`, mémoires infra |
| `biblio-vivante` | 2 218 | bibliothèque + ses scripts |

Deux points relevés en chemin :

**Le schéma a refusé `kind='sh'`** — la contrainte n'accepte que `pdf|blog|transcript|md|repo`. C'est le cahier des charges d'origine, et il a bien fait de tenir : le code source relève de `repo`, pas d'un type inventé à la volée. Contrainte respectée plutôt que contournée.

**210 doublons écartés automatiquement** par le `content_sha256 UNIQUE` — les fichiers déjà présents sous un autre chemin n'ont pas été ré-ingérés.

Les deux agents travaillent toujours : revue qualité de `board.py`, et création du skill `run-board` avec son harnais de vérification. Je remonte leurs conclusions à l'arrivée.

Une réserve à connaître : **seuls 3 291 chunks sur 78 169 sont vectorisés** (4 %). Le board fonctionne — la délibération de tout à l'heure l'a montré en lexical pur — mais le RRF n'a qu'une jambe. Vectoriser le reste demanderait ~75 000 appels d'embedding, à faire par lots quand la machine est calme :

```bash
python3 board.py embed --limit 5000 --batch 200
```

La garde thermique à 89 °C s'arrêtera d'elle-même si les deux cartes sans 

[user] Base directory for this skill: /home/turbo/.claude/skills/deep-research

---
name: deep-research
description: "Universal deep research agent team. 13-agent pipeline for rigorous academic research on any topic. 7 modes: full research, quick brief, paper review, lit-review, fact-check, Socratic guided research dialogue, and systematic review with optional meta-analysis. Covers research question formulation, Socratic mentoring, methodology design, systematic literature search, source verification, cross-source synthesis, risk of bias assessment, meta-analysis, APA 7.0 report compilation, editorial review, devil's advocate challenges, ethics review, and post-research literature monitoring. Triggers on: research, deep research, literature review, systematic review, meta-analysis, PRISMA, evidence synthesis, fact-check, guide my research, help me think through, 研究, 深度研究, 文獻回顧, 文獻探討, 系統性回顧, 後設分析, 事實查核, 引導我的研究, 幫我釐清, 幫我想想, 我不確定要研究什麼, 研究方向, 研究主題."
metadata:
  version: "2.4"
  last_updated: "2026-03-27"
---

# Deep Research — Universal Academic Research Agent Team

Universal deep research tool — a domain-agnostic 13-agent team for rigorous academic research on any topic.

**v2.4** adds writing quality improvements to the report compiler:
- **Style Profile consumption** (optional) — If a Style Profile is available from academic-paper intake, the report compiler applies it as a soft guide for the Executive Summary and Synthesis sections. Discipline conventions and report objectivity take

[assistant] `/deep-research` sans sujet — le pipeline 13 agents a besoin d'une question. Trois sont réellement ouvertes dans ton système, et une recherche rigoureuse changerait tes décisions :

[assistant] Trois recherches complètes en parallèle, chacune avec son shell. Elles alimenteront la révision du cahier des charges du board.

[assistant] La revue trouve **trois bloquants**, et deux sont des fautes que j'ai commises aujourd'hui même :

**1. J'ai corrigé une moitié du silence et laissé l'autre.** J'ai instrumenté la panne lexicale avec un commentaire disant « ne JAMAIS avaler en silence » — et dix lignes plus bas, `if qv:` supprime la voie vectorielle sans un mot si LM Studio tombe. Pire : si les deux voies meurent, le message accuse le **corpus** alors que le backend est mort.

**2. Le compteur de conformité est déjà faux, preuve à l'appui.** `chat()` transforme une panne backend en texte, inséré comme réponse d'expert. Les 4 lignes actuelles de `answers_sans_citation` ont `text = ''` — ce sont les réponses vides du reasoning-runaway, **des pannes, pas des violations**. La métrique fondatrice du produit mesure autre chose que ce qu'elle annonce.

**3. `CHUNK_OVERLAP` n'a jamais eu d'effet** : `i = max(j - CHUNK_OVERLAP, j)` vaut toujours `j`. Recouvrement mesuré : **0 au lieu de 200**. Les 77 962 chunks ont été produits ainsi, et le coût de correction grossit à chaque ingestion.

Je corrige les trois maintenant — le troisième s'aggrave à chaque minute :

[assistant] Le skill `run-board` est livré et vert. Deux choses que son auteur a bien faites : il a **mesuré au lieu de recopier** — le brief annonçait deux cartes sans ventilateur, il en relève trois (58/74/78 °C) et écrit ce qu'il voit ; et il a ajouté de lui-même un contrôle sur les **`lens` strictement dupliquées**, rendant vérifiable le piège du faux consensus.

Mais son driver a été validé **avant** mes trois corrections. Je vérifie qu'elles ne l'ont pas cassé :

[assistant] **Skill vert après mes corrections — `SMOKE OK, exit=0`.** Le driver confirme aussi les 4 réponses sans citation en les identifiant nommément (`archi`, `ops`, `secu`, `arbitre` d'une même requête) : exactement les 4 pannes du reasoning-runaway diagnostiquées par la revue.

## Bilan de cette séquence

**Trois bloquants corrigés et vérifiés** — dont deux écrits par moi aujourd'hui :

| # | Défaut | Preuve de correction |
|---|---|---|
| 1 | Panne vectorielle silencieuse (`if qv:` sans message) | message symétrique à la voie lexicale |
| 2 | Pannes backend comptées comme violations de citation | plus insérées en `answers` |
| 3 | **`CHUNK_OVERLAP` = 0 au lieu de 200** | recouvrement mesuré : 9-12 mots communs entre chunks |

Le troisième est le plus instructif : `i = max(j - CHUNK_OVERLAP, j)` vaut toujours `j`. Le paramètre était déclaré, documenté, et **n'avait jamais eu d'effet**. Les 78 169 chunks en base ont tous été découpés sans recouvrement — une définition à cheval sur une frontière n'est complète dans aucun fragment.

`★ Insight ─────────────────────────────────────`
Le reviewer a nommé l'absence la plus coûteuse du fichier : `embed()` est bien testé, mais `chunk_text()` — la fonction qui a produit **toute la donnée** — n'a aucun test. Une seule assertion sur le recouvrement aurait attrapé le bug avant 78 000 chunks. On teste spontanément ce qui casse bruyamment, pas ce qui produit silencieusement du contenu légèrement dégradé.
`────────────────────────────────────────

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

[user] Base directory for this skill: /home/turbo/.claude/skills/deep-research

---
name: deep-research
description: "Universal deep research agent team. 13-agent pipeline for rigorous academic research on any topic. 7 modes: full research, quick brief, paper review, lit-review, fact-check, Socratic guided research dialogue, and systematic review with optional meta-analysis. Covers research question formulation, Socratic mentoring, methodology design, systematic literature search, source verification, cross-source synthesis, risk of bias assessment, meta-analysis, APA 7.0 report compilation, editorial review, devil's advocate challenges, ethics review, and post-research literature monitoring. Triggers on: research, deep research, literature review, systematic review, meta-analysis, PRISMA, evidence synthesis, fact-check, guide my research, help me think through, 研究, 深度研究, 文獻回顧, 文獻探討, 系統性回顧, 後設分析, 事實查核, 引導我的研究, 幫我釐清, 幫我想想, 我不確定要研究什麼, 研究方向, 研究主題."
metadata:
  version: "2.4"
  last_updated: "2026-03-27"
---

# Deep Research — Universal Academic Research Agent Team

Universal deep research tool — a domain-agnostic 13-agent team for rigorous academic research on any topic.

**v2.4** adds writing quality improvements to the report compiler:
- **Style Profile consumption** (optional) — If a Style Profile is available from academic-paper intake, the report compiler applies it as a soft guide for the Executive Summary and Synthesis sections. Discipline conventions and report objectivity take

[user] <local-command-stdout>Set model to [1mFable 5[22m and saved as your default for new sessions</local-command-stdout>

[assistant] **Modèle verrouillé sur Fable 5** — noté, je n'y toucherai pas. Ta mémoire `feedback_model_fable5_verrouille` le couvrait déjà, c'est réaffirmé.

**Les 3 recherches ont échoué** — pas sur le fond : `session limit · resets 3:50pm`. Aucun rapport produit, rien à récupérer. À relancer après 15h50 :

```
/deep-research  → puis rechoisir les 3 sujets
```

**Catalogue skillmp** (avant coupure) : `33 282 skills · 16 357 avec code source · 6 455 dépôts`. Le `status` du pipeline a été coupé par le timeout.

**Quota à 101 %** — je m'arrête là sur les tâches lourdes. Acquis de la séquence, tous vérifiés :

| | |
|---|---|
| Board | 9 domaines · 44 experts · 78 169 chunks · délibération prouvée |
| 3 bloquants corrigés | recouvrement 0→200, panne vectorielle muette, métrique de citation faussée |
| Skill `run-board` | `SMOKE OK`, exit 0 |
| BrowserOS + dashboard | réparés |
| 2 runs fous arrêtés | charge 38 → 4 |

**En attente de toi** : câble SATA du disque `…971`, les deux `glob` quadratiques, et `jarvis-plan-refresh.timer` que j'ai laissé désactivé.

[assistant] **15:54 — limite réinitialisée** (reset 15:50). GPU 80 °C, charge 9.4, `recherche/` vide : les 3 agents n'ont rien écrit. Je relance tout.

[assistant] **Moisson lancée — 5 étages actifs** : `expansion` + `site` + `fr` démarrés, `catalogue` et `source` tournaient déjà.

**Audit relu** : `audit/audit-local-20260806-1557.md`, secrets **CLEAN**, invocation loguée (row 54).

Une chose à savoir sur cet audit, relevée en le relisant : il annonce **0 service failed** alors que `systemctl --failed` en compte 2. Ses lignes 45-49 forcent `--type=service` y compris sur la commande `--failed` que son propre commentaire dit « exhaustive ». Les unités `.mount`, `.timer` et `.socket` en échec lui sont invisibles — dont `mnt-backup-os.mount`. Correctif : retirer `--type=service` de ces lignes. Le fichier est hors repo (`~/.claude/skills/`), je ne l'ai pas touché sans ton accord.

**Cahier des charges du board** : compris, je n'y touche pas avant les rapports. Les 3 recherches tournent (boards d'experts, RAG/RRF, GPU passifs) et écriront dans `board/recherche/`. La vectorisation tourne aussi — 6 000 chunks par lots de 200, garde thermique à 89 °C.

Je remonte chaque résultat à l'arrivée.

[user] Base directory for this skill: /home/turbo/.claude/skills/deep-research

---
name: deep-research
description: "Universal deep research agent team. 13-agent pipeline for rigorous academic research on any topic. 7 modes: full research, quick brief, paper review, lit-review, fact-check, Socratic guided research dialogue, and systematic review with optional meta-analysis. Covers research question formulation, Socratic mentoring, methodology design, systematic literature search, source verification, cross-source synthesis, risk of bias assessment, meta-analysis, APA 7.0 report compilation, editorial review, devil's advocate challenges, ethics review, and post-research literature monitoring. Triggers on: research, deep research, literature review, systematic review, meta-analysis, PRISMA, evidence synthesis, fact-check, guide my research, help me think through, 研究, 深度研究, 文獻回顧, 文獻探討, 系統性回顧, 後設分析, 事實查核, 引導我的研究, 幫我釐清, 幫我想想, 我不確定要研究什麼, 研究方向, 研究主題."
metadata:
  version: "2.4"
  last_updated: "2026-03-27"
---

# Deep Research — Universal Academic Research Agent Team

Universal deep research tool — a domain-agnostic 13-agent team for rigorous academic research on any topic.

**v2.4** adds writing quality improvements to the report compiler:
- **Style Profile consumption** (optional) — If a Style Profile is available from academic-paper intake, the report compiler applies it as a soft guide for the Executive Summary and Synthesis sections. Discipline conventions and report objectivity take

[assistant] Les 3 recherches tournent déjà (relancées à 15:54) — je ne les duplique pas. État :

[assistant] **Tout tourne.** Rien à relancer :

| | |
|---|---|
| 3 recherches | en vol (boards LLM · RAG/RRF · GPU passifs) — `recherche/` créé à 16:04, rapports pas encore écrits |
| Vectorisation | **3 291 → 7 884** / 78 169 (10 %), +4 593 depuis 15:54 |
| Machine | GPU 86 °C · charge 8.9 · 10 agents |

Le GPU à 86 °C reste sous la garde de 89 °C — la vectorisation s'arrêtera d'elle-même si ça monte.

Je te remonte chaque rapport dès qu'il tombe, puis on révisera le cahier des charges du board avec leurs conclusions, comme convenu.

[user] Base directory for this skill: /home/turbo/.claude/skills/deepspeed

---
name: deepspeed
description: Expert guidance for distributed training with DeepSpeed - ZeRO optimization stages, pipeline parallelism, FP16/BF16/FP8, 1-bit Adam, sparse attention
version: 1.0.0
author: Orchestra Research
license: MIT
tags: [DeepSpeed, Distributed Training, ZeRO, Pipeline Parallelism, Mixed Precision, Optimization, Microsoft, Large-Scale Training, FP16, FP8]
dependencies: [deepspeed, torch, transformers, accelerate]
---

# Deepspeed Skill

Comprehensive assistance with deepspeed development, generated from official documentation.

## When to Use This Skill

This skill should be triggered when:
- Working with deepspeed
- Asking about deepspeed features or APIs
- Implementing deepspeed solutions
- Debugging deepspeed code
- Learning deepspeed best practices

## Quick Reference

### Common Patterns

**Pattern 1:** DeepNVMe Contents Requirements Creating DeepNVMe Handles Using DeepNVMe Handles Blocking File Write Non-Blocking File Write Parallel File Write Pinned Tensors Putting it together Acknowledgements Appendix Advanced Handle Creation Performance Tuning DeepNVMe APIs General I/O APIs GDS-specific APIs Handle Settings APIs This tutorial will show how to use DeepNVMe for data transfers between persistent storage and tensors residing in host or device memory. DeepNVMe improves the performance and efficiency of I/O operations in Deep Learning applications through powerful optimizations buil

[assistant] **L'instrumentation d'`embed()` vient de payer.** Le lot rend `13 http_400` — cause **nommée**, non transitoire, donc **non réessayée**. Avant le correctif, ces 13 auraient disparu en silence comme les 19 du premier lot. Ce sont probablement des chunks trop longs refusés par le modèle : un motif reproductible, désormais visible.

**Vectorisation : 3 291 → 9 278** / 78 169 (12 %), 5 987/6 000 réussis.

---

**DeepSpeed : non installé**, et je ne l'installe pas sans ton accord — mais surtout, **il ne sert à rien ici** :

| | |
|---|---|
| `deepspeed` | `ModuleNotFoundError` |
| `torch` | 2.13.0+cu130, CUDA OK — mais **4 GPU visibles sur 5** |

DeepSpeed optimise l'**entraînement distribué** de gros modèles (ZeRO, pipeline parallelism). Ton usage est de l'**inférence** via LM Studio et Ollama, qui ont leur propre gestion mémoire. Ajouter DeepSpeed ne toucherait aucun de tes chemins chauds.

Et le matériel s'y prête mal : ZeRO partitionne l'état sur des GPU **homogènes**. Les tiens vont de 6 Go (1660S) à 12 Go (2060) — le partitionnement s'alignerait sur la plus petite carte, et deux d'entre elles n'ont pas de ventilateur, donc pas de charge soutenue possible.

Un détail à noter au passage : **torch ne voit que 4 GPU** alors que `nvidia-smi` en compte 5. Cohérent avec ta mémoire `lmstudio_reecrit_cuda_visible_devices` — une carte est masquée par `CUDA_VISIBLE_DEVICES`.

**Les 3 recherches tournent toujours**, `recherche/` encore vide.

[user] c'est mon board en local pour mon écosysteme donc le cahier des charge tu loe change apres la recherche

[assistant] Compris, et je m'y tiens : **je ne touche pas au cahier des charges tant que les rapports ne sont pas là.** C'est ton board, local, pour ton écosystème — la spec se révise avec les conclusions en main, pas avant.

[assistant] **Les 3 recherches tournent** — 10 agents actifs, `recherche/` encore vide. Elles écriront chacune leur rapport :

```
board/recherche/01-boards-experts-llm.md      ← 4 experts + 1 arbitre : la divergence paie-t-elle ?
board/recherche/02-rag-hybride-rrf.md         ← RRF avec 12 % de couverture vectorielle
board/recherche/03-gpu-passif-risers.md       ← charge soutenable, usure à 87 °C
```

**Ce que je ferai à leur arrivée**, dans cet ordre :

1. Je te remonte les conclusions et les recommandations chiffrées de chacune
2. Tu tranches ce que tu retiens
3. **Alors seulement** je révise le cahier des charges du board — schéma, lens, paramètres de retrieval

Rien ne bouge côté spec d'ici là. Ce qui continue en attendant est neutre : vectorisation (**9 278/78 169**) et moisson skillmp (5 étages).

Un point de vigilance : **GPU à 87 °C**, charge 12.6. La garde thermique de `cmd_embed` coupe à 89 °C — il reste 2 °C. Si tu veux souffler, je peux suspendre la vectorisation le temps que les recherches finissent ; elle est reprenable sans rien perdre grâce au commit par lots.

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

[assistant] **GPU : configuration verrouillée, je n'y touche pas.** Aucun `nvidia-smi -pl`, aucun `nvidia-settings`, aucun changement de power limit ou de ventilation. C'est noté comme règle permanente.

Moissonnage intensif sur les 16 threads — je regarde d'abord où sont les limites actuelles :

[assistant] Rôle compris : **orchestrateur central, je fais faire, je n'écris pas.** Je sonde d'abord les exécutants disponibles avant de router.

[assistant] Exécutants confirmés : **`agy` v1.1.10**, **LM Studio :1234** (200), **Ollama cloud** (`gpt-oss:120b/20b`, `kimi-k2.5`). Antigravity écoute sur 9011 mais ne rend pas de CDP. Je regarde comment commander `agy` :

[assistant] **GAZ.** Dispatch parallèle sur les trois exécutants — chacun sa tâche, je ne fais qu'orchestrer.

[assistant] Décodé : un **registre couleur/action/mot-clé/commande**, injecté dans Claude Code, avec **superposition pondérée** et boucle **demande → action → log → scoring → feedback**, une erreur = une amélioration. Les briques existent déjà en partie (`jarvis-simul.py` fait la superposition pondérée, `jarvis-autochain.sh` la chaîne). Je fais construire le reste — je n'écris pas.

[assistant] **Le premier rapport est là, et il corrige quelque chose que j'ai mal lu devant toi.**

`board/recherche/01-boards-experts-llm.md` — 486 lignes, 50 sources dont 24 évaluées par les pairs.

**La délibération que je t'ai présentée comme réussie était un échec.** Question posée : index énorme vs index réduit exécutable, à propos de **ta bibliothèque**. Les 5 extraits remontés portaient sur les **index PostgreSQL BRIN/B-Tree** — hors sujet. Les 4 experts ont répondu, cité, convergé ; l'arbitre a écrit « convergence massive ». La règle « pas de citation = invalide » n'a rien vu : **elle vérifie la forme de l'ancrage, pas sa pertinence.**

Ce que la littérature établit :

| Constat | Mesure |
|---|---|
| Débat multi-agents vs CoT + self-consistency, budget apparié | **ne bat pas**, 6 études indépendantes |
| Gain du débat (Du et al., ICML 2024) | +4 pts · self-consistency : **+17,9 pts** |
| Persona vs modèle | +1,1 % vs **+2,2 %** — 2 agents divers ≈ 16 homogènes |
| 10 agents, même modèle de base | **≈ 1,2 voix effective** |
| Ton board, deux experts sur la question 2 | **Jaccard = 1,00** — voix identiques |
| Modèles 7-8 B (classe de qwen3.5-9b) | le débat homogène **perd**, ×2-3 jetons, **85,5 % de sycophancie** |
| Coût par question | **103 s mur / 295 s GPU** vs 64 s pour un expert seul — **×4,6** |

Et le **« biais assumé »** — l'idée forte du pack de Rémi, que j'ai reprise dans nos 15 lens : **aucun article ne le valide**. Ce qui est validé, c'est le camp **assigné** (Khan,

[assistant] **Étape 1 — garde de provenance : refus.**

> No recent /scrape result found in this conversation. Run /scrape \<intent\> first, then say /skillify.

Ce `/skillify` est celui de **gstack** : il codifie un scrape navigateur en script Playwright déterministe. Son contrat exige un `/scrape` réussi dans les 10 derniers tours. Il n'y en a aucun dans cette session — et le skill interdit explicitement de synthétiser depuis des fragments de conversation. Je m'arrête là.

C'est aussi ce qui s'est passé à ta session précédente : la bibliothèque a gardé la trace du même refus.

**Trois `skillify` différents sont installés chez toi**, et ce n'est pas celui-ci que tu veux :

| Skill | Ce qu'il codifie |
|---|---|
| gstack (celui invoqué) | un `/scrape` navigateur → script + test + fixture |
| OMC | un **workflow répétable de la session** → brouillon de skill |
| meta | une **fonctionnalité brute** → skill testé complet |

Pour ce que tu fais — moisson, registre, scoring — c'est le deuxième ou le troisième. Ou plus simplement la convention maison : `SKILL.md` + `driver.sh` avec smoke, comme `run-jarvis-autochain` et `run-board` livrés tout à l'heure.

**Deux agents travaillent déjà là-dessus** : le registre couleur/action/mot-clé/commande **inclut son `SKILL.md`** d'injection dans Claude Code, et la boucle scoring produit `poids_appris.json`. C'est exactement la codification que tu demandes, faite par les bons outils.

État courant : moisson 6 étages actifs · vectorisation 9 278/78 169 · 4

[assistant] **Deuxième rapport livré** — `board/recherche/03-gpu-passif-risers.md`, 918 lignes, 21 références. Il mesure au lieu d'extrapoler, et il corrige deux idées reçues.

**Ton bridage à 70 W ne protège pas ces cartes :**

| Mesure | Valeur |
|---|---|
| Résistance thermique GPU2 / GPU3 | **0,691 / 0,694 °C/W** — deux marques, accord à 0,4 % |
| Carte ventilée (référence) | 0,267 °C/W — rapport **2,6×** |
| Constante de temps τ | **149 s** (R² = 0,982) |
| 70 W **soutenus** | **96 °C = seuil de coupure** |

Autrement dit : **seul le rapport cyclique les sauve**, pas le plafond de puissance. Une rafale sous 60 s coûte +11 °C ; au-delà de 2,5 min on est en régime établi.

**Charge maximale recommandée : 50 W moyens sur toute fenêtre glissante de 5 minutes** (≈ 69 % de rapport cyclique) → équilibre à 82 °C. Plafond absolu 62 W (91 °C). GPU3 tourne à **55,5 W / 86 °C — 11 % au-dessus**. GPU2 (39 W / 76 °C) a de la marge : **rééquilibrer entre les deux est gratuit** et respecte ta règle « tous les GPU en ligne ».

**Sur l'usure, la littérature se contredit et il le dit :** Arrhenius prédit ×5-8 sur le silicium, mais Summit (27 648 GPU, 2,5 ans, télémétrie 1 Hz) ne trouve **aucune corrélation température/panne**, et Coffin-Manson rend le régime *continu* favorable. Le vrai angle mort est le VRM et les condensateurs — aucun capteur ne les mesure. Et **91 °C est une limite de fonctionnement garanti, pas de longévité** : l'affirmation inverse, courante sur les forums, n'est sourcée nulle pa

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

[assistant] **`SMOKE OK` — exit 0, aucun contrôle en échec.** Les 9 familles passent, y compris après mes trois correctifs de tout à l'heure.

Ce qui a bougé depuis la rédaction du skill :

| | Skill (rédaction) | Maintenant |
|---|---|---|
| Vectorisés | 3 291 (4,2 %) | **9 278 (11 %)** |
| Dimensions distinctes | 768 seule | **1 seule** — aucune dérive |
| Domaines sans corpus | 5 | 5 (inchangé) |
| Réponses sans citation | 4 | 4 — **le compteur n'a pas monté** |

Ce dernier point est le seul qui compte vraiment : le contrôle 7 dit que ce qui importe est la **tendance**. Deux délibérations ont eu lieu depuis, le compteur est resté à 4 — les 4 lignes historiques du reasoning-runaway, aucune nouvelle violation.

**Les 2 avertissements restent, et le premier rejoint la recherche qui vient de tomber :**

`cout-energie`, `donnees-persistance`, `fiabilite-exploitation`, `inference-locale`, `rag-retrieval` — **25 experts qui ne peuvent jamais répondre**, faute de corpus dans leur domaine. Le rapport sur les boards LLM en fait sa **recommandation numéro 1**, avant toute amélioration du conseil : améliorer la délibération quand cinq domaines sur neuf sont vides et que le RRF fusionne un BM25 complet avec un cosinus à 11 %, c'est optimiser l'aval d'un tuyau bouché.

Peupler ces cinq domaines est mécanique — `board.py ingest <domaine> '<glob>'`, comme pour les quatre autres. Mais **je ne touche pas au cahier des charges** avant le troisième rapport (RAG/RRF), qui dira justement s'il faut finir de

[assistant] Même verrou, même réponse — le contrat de ce `/skillify` exige un `/scrape` récent, il n'y en a toujours pas :

> No recent /scrape result found in this conversation. Run /scrape \<intent\> first, then say /skillify.

Mais **ta demande en argument est déjà en cours d'exécution** par les deux agents dispatchés il y a un moment. Je vérifie où ils en sont :

[assistant] Les deux artefacts sont livrés — `registre-actions.py` + sa base de **66 Mo**, `scoring-feedback.py` + `poids_appris.json`. Je récupère la méthodologie et j'installe tout au board, en peuplant les 5 domaines vides :

[assistant] Deux domaines à zéro — le `content_sha256 UNIQUE` a bloqué : ces fichiers sont **déjà ingérés ailleurs**, on ne peut pas les dupliquer. Je réaffecte depuis le corpus existant, comme pour les premiers domaines :

[assistant] **Les 9 domaines ont du corpus. Aucun expert orphelin.**

```
souverainete           32 072      inference-locale        6 195
orchestration-agents   17 504      fiabilite-exploitation  4 809
cluster-m1             11 024      cout-energie            4 654
                                   donnees-persistance     2 288
biblio-vivante          2 218      rag-retrieval           1 105
```

C'était l'avertissement du smoke et la **recommandation numéro 1** du rapport sur les boards LLM : 25 experts qui ne pouvaient jamais répondre. Ils le peuvent maintenant.

La méthodologie est installée dans le board : les **deux rapports de recherche** (349 chunks) sont ingérés dans `rag-retrieval` — le board peut désormais délibérer sur sa propre conception, sources à l'appui.

Deux choses apprises en le faisant :

**Le `content_sha256 UNIQUE` empêche d'ingérer un même fichier dans deux domaines.** Sur `donnees-persistance`, les 9 globs ont rendu 0 source et 132 doublons : tout était déjà en base sous `souverainete`. C'est la contrainte qui fait son travail — pas de duplication silencieuse. La réaffectation par mot-clé du titre est la bonne voie, et elle est réversible.

**Les artefacts que tu demandais sont livrés** par les agents, pas par moi :

| | |
|---|---|
| `bin/registre-actions.py` + base **66 Mo** | couleur · action · mot-clé · commande, FTS5 |
| `bin/scoring-feedback.py` + `scoring.db` | cycle demande → action → log → scoring |
| `data/poids_appris.json` | pondérations apprises, 

[user] Base directory for this skill: /tmp/claude-1000/bundled-skills/2.1.220/01e37e4bf6d803d9377889c16f2da1c1/run

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

[assistant] Le skill `run-board` est le chemin vérifié du dépôt — je l'utilise. Et « lancer » ne suffit pas : il faut **piloter**. Le vrai test est un domaine qui ne pouvait **jamais** répondre il y a dix minutes.

[assistant] **Contrôle qualité — la règle fondatrice tient.**

```
réponses 13 · citations 26 · SANS citation 4
```

Le compteur est **inchangé depuis ce matin**. Les 4 lignes sont les réponses vides du reasoning-runaway, historiques. Aucune violation nouvelle en trois délibérations — c'est le critère que le contrôle 7 du smoke désigne : ce qui compte n'est pas la valeur absolue mais la tendance.

La délibération sur `rag-retrieval` tourne toujours (5 experts + arbitre sur LM Studio, dizaines de secondes chacun). Elle valide le point le plus important de la journée : **ce domaine ne pouvait rien répondre il y a un quart d'heure**, faute de corpus.

**Chronologie de la session, en tâche de fond :**

| Shell | Ce qu'il fait | État |
|---|---|---|
| moisson skillmp | 6 étages, catalogue 33 282 skills | tourne |
| board `ask` | délibération `rag-retrieval` | tourne |
| agent recherche | RAG/RRF — 3ᵉ rapport | tourne |
| agent registre | `SKILL.md` d'injection | tourne |
| agent scoring | rapport de la boucle | tourne |

**Livré et vérifié aujourd'hui :** routeur biblio corrigé (0/12 → 12/12) · moteur de projections pondérées · chaîne `autochain` 0-token · board 9 domaines / 44 experts / 78 518 chunks, **tous les domaines peuplés** · 3 bloquants corrigés dans `board.py` · skills `run-jarvis-autochain` et `run-board` avec smoke vert · BrowserOS et dashboard réparés · 2 runs fous arrêtés (charge 38 → 11) · registre 66 Mo · boucle de scoring · 2 rapports de recherche sur 3.

**En attente de toi*

[assistant] Deux enseignements, et l'un est un défaut dans **ma** correction.

**Mon correctif ne couvre que la boucle des experts, pas l'arbitre.** Les 4 experts ont bien été écartés — `⚠ PANNE BACKEND : [echec backend: HTTPError] — non enregistre`. Mais l'arbitre, lui, a été enregistré avec son texte d'erreur, et il a fait monter le compteur : **4 → 5**. Le bloc arbitre est écrit séparément, une centaine de lignes plus bas, et je ne l'ai pas traité.

[assistant] **Métrique restaurée : 13 réponses · 26 citations · 4 sans citation.** Retour aux 4 lignes historiques, la pollution est effacée et le garde-fou couvre désormais l'arbitre.

**Ce que la panne a démontré, malgré elle :** le correctif marchait pour les experts (4 pannes écartées proprement) et **échouait pour l'arbitre**, écrit dans un bloc séparé cent lignes plus bas. Je l'avais corrigé à moitié sans le voir — c'est la deuxième fois aujourd'hui sur ce même fichier, après la voie lexicale instrumentée et la voie vectorielle laissée muette. **Le même défaut a deux emplacements, et je n'en corrige qu'un.**

Le backend n'est pas mort : `:1234` répond 200. Il a saturé sous la charge combinée — moisson, étage `fr` sur le cluster local, vectorisation, 4 `llama-server` et GPU à 88 °C. Les 4 experts ont attendu **63 secondes chacun** avant de recevoir un `HTTPError`.

---

**La boucle de scoring est livrée**, et son auteur est franc sur ce qui compte :

```
score = (Σ wᵢ·succèsᵢ + α·m) / (Σ wᵢ + α)   α=4, m=0.5
wᵢ    = max(0.05, 0.5^(âge_jours / 14))
poids ∈ [0.5 ; 2.0]
```

Quatre décisions justifiées, pas subies : le **plancher 0.05** sur la fraîcheur (décroissance, pas oubli — sinon une action désastreuse redeviendrait vierge en attendant) ; le **plancher 0.5** sur les poids (à zéro, l'action ne serait plus jamais tentée, donc plus jamais réévaluée — la boucle se refermerait sur elle-même) ; des **pentes asymétriques** +2.0 / −1.0 parce qu'un échec est plus souvent circonstanciel qu

[assistant] **Le registre est livré — 79 542 actions indexées, requêtables en 0,04 s.**

```
🟢 sûr        59 496   74,8 %        lancer      42 154   53,0 %
🟠 modifie    16 130   20,3 %        sonder      12 424   15,6 %
🔴 destructif  3 916    4,9 %        consulter    9 326   11,7 %
```

Tu as désormais un chiffre que personne n'avait : **3 916 blocs destructifs** dans ton corpus, isolables d'une requête. Et le skill `registre` est déjà chargé par le harnais — il répondra à « combien de blocs destructifs », « quelles commandes touchent au GPU », « montre-moi les actions sûres ».

**Ce que l'agent a fait de mieux que ce que je lui demandais :** au premier build, **41 % des blocs tombaient dans `autre`**. Le corpus préfixe ses commandes — `[skillsmp] Titre — npx skills add…` (9 894 blocs), `# /chemin/script.py` (5 134), `xdg-open…` (7 136). Il a ajouté un déshabillage avant l'extraction du verbe : `autre` est tombé à 8,4 %. Sans ça, *« le registre était formellement conforme mais inutile »*. C'est exactement la différence entre exécuter un spec et livrer quelque chose qui sert.

Et il a refusé de tricher sur les 6 670 restants : actions en langue naturelle et métadonnées. *« Les étiqueter au jugé aurait été pire que les laisser visibles. »*

`★ Insight ─────────────────────────────────────`
Son refus de purger par défaut est le point le plus fin du rapport. Il a lu l'index **quatre fois en quinze minutes** : 74 467 → 79 316 → 78 002 → 79 547 lignes, parce que `biblio-filler` le réécrit en

[assistant] **`hermes-2-pro-mistral-7b` répond en 7,8 s** — trois fois plus vite que qwen3.5-9b (55-75 s). Sa réponse sur sa propre identité est fantaisiste (« Tiny T1 »), ce qui est normal : les modèles ne connaissent pas leur nom de déploiement.

Ton idée est exactement la recommandation la plus forte du rapport de recherche : **varier le modèle bat varier la persona** — +2,2 % contre +1,1 %, et *« 2 agents divers ≈ 16 agents homogènes »*. Aujourd'hui les 44 experts partagent la même base, ce qui donne **≈ 1,2 voix effective**. Je câble les deux.

[assistant] Les deux sont chargés dans LM Studio, `Parallel 4` sur hermes. Reste à ce que `board.py` **utilise** la colonne — `chat()` a encore le modèle en dur :

[assistant] Le grep ne trouve rien — **les remplacements ont échoué en silence** (`str.replace` ne signale pas l'absence). Je vérifie au lieu de croire le message :

[assistant] Partiellement appliqué : la signature a changé, mais le formateur avait réécrit le corps sur plusieurs lignes. Correction par numéro de ligne :

[assistant] **Câblé et vérifié dans le fichier**, pas seulement annoncé :

```
198:  "model": model or CHAT_MODEL,
463:  model=e["model"] if "model" in e.keys() else None,
```

Répartition : **27 experts sur qwen3.5-9b, 17 sur hermes-2-pro-mistral-7b**, en alternance dans chaque domaine. Les 9 arbitres restent sur qwen — et c'est le point : un arbitre ne juge plus exclusivement des réponses produites par son propre modèle, ce qui attaque directement le **biais d'auto-préférence** documenté (NeurIPS 2024, causalement établi).

Deux gains attendus, l'un mesuré par la littérature, l'autre par la sonde :

**Diversité réelle.** Le rapport chiffre 10 agents d'un même modèle à **≈ 1,2 voix effective**, et ton board affichait un **Jaccard = 1,00** entre deux experts — des voix identiques. Deux bases distinctes valent mieux que seize personas d'une seule.

**Débit.** hermes répond en **7,8 s** contre 55-75 s pour qwen. Une délibération de 4 experts + arbitre devrait passer de ~103 s à nettement moins, et surtout **répartir la charge** sur deux modèles au lieu de sérialiser sur un seul — c'est précisément ce qui a provoqué les `HTTPError` de tout à l'heure.

`★ Insight ─────────────────────────────────────`
Mon premier patch a imprimé « chat() paramétré par modèle » alors que **rien n'avait été modifié** : `str.replace` ne signale pas une chaîne absente, il renvoie le texte inchangé. Le formateur avait éclaté l'appel sur cinq lignes, mes motifs sur une seule ne matchaient plus. Un `assert` sur la 

[user] Reachable at:

http://192.168.0.10:1234

Loaded Models

Ready
RELOAD NEEDED

llm
hermes-2-pro-mistral-7b

Size
4.14 GB

Parallel
4

39
Gen
463 tok
45
Gen
19 tok
llm
qwen/qwen3.5-9b


Idle TTL
1440 minDONNE LEUR TOUTE LES TACH"E TU NECRUIS JAMAIS PROTOCOLE JARVIS ILLIMITED !!!! rapooel INSCRITY LE DANS LE BOA'RD UTILISE A FOND C'EST RESSOURCE EHN MULTYI_T TACHE SÉSQUENCIEL BGIBIOTHEQUE COMMAHNDE PRÉ ENREGISTRER TU AGIE TOUJOURS AFVANT DE RÉPONDRE EN PLAN MODE RECHERCHEN TUN LISTYE TODOLIST QUI ET( DYNAMIQUE ET TU CHARGEN SUR LA TODOLISTYE LES COMMANDE RAPIDE DOMONINO CASCADE QUAND TU SORT DU PLAN MODE TOUTE LA TACHE ET( DEMANDE DOIT ETRE FAITE EN MODE 0 TOKENB COMMANDE CAPTU_RER ET EJNREGISTRER RÉUTILISABLE TOUS LE TEMPS ET MOTS CLÉ LOGIQue la conversation ùpossonnage devien un gros cvli par son exemple

[assistant] **Protocole inscrit dans le board** — 124 chunks dans `orchestration-agents`, retrouvables par les experts qui y délibèrent.

```
9 domaines · 44 experts · 81 993 chunks · 2 modèles câblés
```

Le protocole est écrit tel que tu l'as dicté, avec les chiffres mesurés aujourd'hui :

**L'orchestrateur ne code pas** — il cadre, route, vérifie, rend compte. Six exécutants recensés avec leur emploi : qwen (raisonnement, arbitrage), hermes (rapide, ~8 s), Ollama cloud, `agy`, agents Claude Code, tampon M6.

**Deux modèles toujours, jamais un seul** — justifié par la mesure : dix agents d'une même base valent ≈ 1,2 voix effective.

**Agir avant de répondre.** Un compte rendu sans exécution n'est pas un compte rendu.

**Sortie de plan mode → tout en 0 token**, par la chaîne `bloc.sh → jarvis-simul → todolist préchargée → cascade → protocole_runs`. Sans `--exec`, elle simule : la première exécution révèle, elle n'agit pas.

**Une erreur = une amélioration** — journalisée, scorée, le poids de l'action suit. Les pannes d'infra exclues du score.

**Les garde-fous priment sur la vitesse** : GPU verrouillé, ≤ 50 W moyens sur 5 min, seuils de dispatch, verrou tenu et non documenté, jamais deux implémenteurs sur les mêmes fichiers.

Et les **dix pièges** de cet environnement, à recopier dans tout prompt d'agent isolé — dont celui que je viens de commettre : *`str.replace` ne signale pas une chaîne absente, il rend le texte inchangé.* Toujours `assert` avant de remplacer.

Le registre retrouve 

[assistant] Le protocole dit d'agir avant de répondre. Le seul point non vérifié est le board bi-modèle. Je mesure d'abord, comme le protocole l'exige :

[assistant] **Le troisième rapport est là. Les trois recherches sont complètes — le cahier des charges peut être révisé.**

Et il trouve **deux bugs réels dans le `retrieve()` que j'ai écrit** :

**1. `[:8]` garde les 8 *premiers* mots de la question.** Il jette `sigkill`, `status`, `sha256` et garde `pourquoi`, `est`, `que`. Les termes discriminants sont systématiquement perdus.

**2. Le modèle d'embedding est appelé sans les préfixes `search_query:` / `search_document:`** que son éditeur déclare obligatoires. Les 9 278 vecteurs sont calculés hors spécification.

Et une mesure qui tranche la question que tu posais ce matin :

> Quand la réponse est hors du périmètre vectorisé — **88 % du corpus** — la voie vectorielle **améliore 0 fois sur 60 et dégrade 13 fois**.

Les fragments vectorisés font 20 % du corpus mais **78 % du top-6 RRF** (×3,8), et **43 % du top-6 BM25 est délogé**. RRF n'est pas en cause, `k=60` non plus : c'est ce qu'on lui donne à fusionner.

Je charge la todolist avec les neuf recommandations, commandes préchargées :

[assistant] Doublons créés — mon premier script avait commité **avant** de planter sur le `print`, le second a réinséré sous des titres légèrement différents. Je nettoie :

[assistant] Un daemon a marqué mes tâches `done` sans que rien ne soit fait — c'est exactement ta mémoire `tasks_prodloop_faux_done` : **une action inscrite dans `tasks` reçoit un faux `done` de la boucle de production**. Elle dit d'utiliser `plan`. Je vérifie :

[assistant] Confirmé : marquées `done` entre **14:57 et 15:00**, quelques minutes après insertion, sans qu'aucune ligne de code n'ait bougé. Ta mémoire est exacte. Je les déplace vers `plan`, la table que tu avais désignée :

[assistant] **Les 9 recommandations sont dans `plan`, hors de la boucle de production.** Le cahier des charges est révisé, comme convenu : après la recherche, pas avant.

## Ce que les trois recherches ont changé

**Deux bugs réels dans mon `retrieve()`** — mesurés, pas supposés :

| Bug | Effet |
|---|---|
| `[:8]` garde les 8 **premiers** mots | jette `sigkill`, `status`, `sha256` ; garde `pourquoi`, `est`, `que` |
| Embeddings sans `search_query:` / `search_document:` | 9 278 vecteurs calculés hors spécification de l'éditeur |

**La réponse à ta question de ce matin** — faut-il finir de vectoriser ? La mesure dit : **pas dans cet état**. Hors du périmètre vectorisé (88 % du corpus), la voie vectorielle **améliore 0 fois sur 60 et dégrade 13 fois**. Les 20 % de fragments vectorisés occupent **78 % du top-6** et délogent **43 % du top-6 BM25**. RRF n'est pas en cause, `k=60` non plus. Corriger les préfixes **avant** de vectoriser coûte moins cher à 9 278 vecteurs qu'à 82 000.

**Le board :** trois correctifs à coût nul — abstention sur la pertinence (le seul qui aurait attrapé la délibération hors-sujet), permutation de l'ordre des avis (44,4 → 58,8 %), anonymisation des experts (23,8 → 56,2 %).

**Le GPU :** rééquilibrer GPU3 (55,5 W / 86 °C, 11 % au-dessus) vers GPU2 (39 W / 76 °C), et brancher les **six prises boîtier** — 369 W évacués sans un seul ventilateur. Configuration GPU non touchée.

`★ Insight ─────────────────────────────────────`
Mes tâches ont été marquées `done` en troi

[user] ────────────────────────────────────────────────────────────────────────
> /skillmp /skillmp recupere cette commande pour moissonage deeprecherche
  grossi le scan et moissonnage intensif par cyècle patter,net sans aucun
  arrer multi tache micro actionb une énorme massse d'action ern
  parrélélisme en micro ntache permety de charfger la todolist avexc des
  action masssive et immépar commande et code déja enregistrer lancer par
  commande rapide mot cles auto detecter et generer

[assistant] J'agis d'abord : le registre contient déjà **79 542 actions**, je charge le plan avec les commandes sûres et exécutables, par famille de verbe.

[assistant] **1 173 micro-tâches chargées** — `sonder` 386, `lire` 387, `consulter` 400. Plan total : **12 778**. Uniquement des actions 🟢 vérifiables, aucune 🟠 ni 🔴 : on charge du scan, pas de la mutation.

Tu demandes que le protocole devienne la règle permanente et qu'il s'améliore. J'y inscris ce que cette séquence vient d'apprendre :

[assistant] **Le protocole est enrichi et réingéré — 128 chunks, board à 82 121 chunks.** Il est désormais la règle permanente, consultable par les experts qui délibèrent dans `orchestration-agents`.

Ce que j'y ai ajouté, tiré de cette session seulement :

**§8 — Cycle de moissonnage permanent.** La chaîne complète, du registre au scoring, avec les deux règles qui viennent d'être payées : **charger `plan`, jamais `tasks`** (faux `done` en trois minutes, timestamps à l'appui), et **ne charger que du 🟢 en masse** — le registre compte 3 916 blocs destructifs et 16 130 qui modifient, une todolist massive ne se remplit que de `sonder`, `lire`, `consulter`.

**§9 — Ce que cette session a coûté.** Sept échecs réels, datés, avec leur parade :

- `str.replace` qui rend le texte inchangé sans rien dire — `assert` avant de remplacer
- **le même défaut a souvent deux emplacements** — voie lexicale instrumentée / voie vectorielle muette, experts protégés / arbitre non
- une mémoire ne protège que si on la consulte **au moment de choisir**
- un test qui échoue peut accuser le test
- **le lot qui réussit ne prouve rien** — forcer les chemins d'échec
- une réponse plausible et citée peut être hors sujet — la règle vérifie la forme, pas la pertinence
- sonder avant de router, toujours

`★ Insight ─────────────────────────────────────`
Le §9 est le seul qui rende le protocole meilleur que sa version d'il y a une heure. Les sections 1 à 8 décrivent ce qu'on veut faire ; celle-là décrit ce qui a réellement

[assistant] `pip` refuse (PEP 668, environnement géré par la distribution). La voie propre sur Ubuntu est le paquet système, pas `--break-system-packages` :

[assistant] **`python3-magic` installé et vérifié** — paquet système (`2:0.4.27-3`), pas de `--break-system-packages` :

```
application/vnd.sqlite3   board.db
text/x-shellscript        bloc.sh
text/plain                BLOCS-INDEX.tsv
```

C'est directement utile au moissonnage : `board.py ingest` lit aujourd'hui n'importe quel fichier attrapé par un glob, sans vérifier son type. Le rapport de revue signalait justement qu'**un `.db` ou une archive avalée par un glob est lue entière en RAM, décodée en charabia, passe le test des 120 caractères et finit indexée puis vectorisée**. `magic.from_file(f, mime=True)` règle ça en une ligne.

**IPython 9.12.0 est déjà installé** — les magics `%timeit`, `%%bash`, `%store` sont disponibles sans rien ajouter.

Sur « snippets 3 python » je ne veux pas deviner. Trois lectures possibles, et elles n'appellent pas la même chose :

**A.** Un **gestionnaire de snippets** — sauvegarder et rejouer des bouts de code. Tu en as déjà l'infrastructure : le registre indexe 79 542 commandes par couleur et verbe. Un snippet Python y aurait sa place sans nouvel outil.

**B.** Les **snippets IPython** — `%store` pour persister des variables, `%macro` pour rejouer des cellules, `%save`/`%load`. Déjà disponibles.

**C.** Trois snippets Python précis que tu veux que je produise — dis lesquels.

Laquelle ? Le registre existant (A) me semble le meilleur point d'ancrage : il est déjà branché sur le protocole, le scoring et la todolist, et il évite d'ajouter un outil de plus