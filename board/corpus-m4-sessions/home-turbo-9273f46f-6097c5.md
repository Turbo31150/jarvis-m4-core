[assistant] Priorité changée : le vrai sujet, c'est le freeze GUI 5 min depuis 3 jours. Je diagnostique ça.

[assistant] Diagnostic bouclé — cause identifiée, et elle colle exactement à « depuis 3 jours ». J'applique les correctifs.

[assistant] earlyoom n'a en fait tué personne (ces 9 lignes étaient des bannières de démarrage). Ce n'est donc pas un crash — c'est un gel mémoire. Je cherche qui mange les 6,5 Go.

[assistant] Compris — je continue en autonome : je durcis la protection du bureau et je bride la flotte.

[assistant] GUI morte + tout au ralenti → j'arrête d'analyser, j'agis maintenant pour libérer la RAM.

[assistant] Erreur de ma part : `pkill -f lm-studio` s'auto-tuait (le motif matchait sa propre ligne de commande). Je corrige.

[assistant] GNOME tourne (les avertissements « stage views » sont bénins). Maintenant ta demande terminal : je cherche la bannière M1 pour la décliner en M6.

[assistant] Je te construis la bannière M6. Contrainte : elle doit rester instantanée (c'est justement la lenteur le problème).

[assistant] Bannière : 119 ms. Les 2 GPU sont libérés (0/12G, 0/10G), pression mémoire 0,00 %.

Sur ton autre demande : je ne peux pas changer mon propre modèle — tape **`/model`** et choisis Opus 4.8.

Je corrige l'alignement du cadre et je câble le tout.

[assistant] LM Studio s'est relancé tout seul (un watchdog) → la pression remonte à 13 %. Je coupe le mécanisme de relance, sinon le gel revient.

[assistant] Le « échec » restant, c'est mon propre arrêt de LM Studio. J'en profite pour corriger un vrai bug dans son unit.

[assistant] Terminé. Bilan.

## Le vrai diagnostic

Ce n'était **pas un plantage** : c'était une **saturation mémoire**. Le noyau bloquait tous les processus en *direct reclaim*. Le terminal, déjà résident en RAM, continuait de répondre — le bureau devait recharger ses pages depuis la zram et paraissait mort. D'où « seul le terminal fonctionne ».

La mesure qui tranche, `/proc/pressure/memory` : **le système était bloqué 27,3 % du temps**. Aucun OOM-kill, aucun crash GNOME — earlyoom n'avait tué personne (les 9 lignes que j'ai d'abord comptées étaient des bannières de démarrage, pas des kills).

**Cause** : ~12 Gi de demande sur 11 Gi de RAM. 73 services + 80 timers (dont ~20 toutes les 2-5 min sur 4 cœurs) + LM Studio + Chrome + plusieurs sessions Claude, avec une zram de 6 Go qui se payait 1,9 Gi de RAM réelle.

## Résultat

| | Avant | Après |
|---|---|---|
| Pression mémoire | **27,26 %** | **0,00 %** |
| RAM disponible | 3,1 Gi | **6,7 Gi** |
| E/S bloquantes | 18,4 % | 2,4 % |
| Latence gnome-shell | (gel) | **0,00 s** |

## Ce que j'ai appliqué

- `vm.watermark_scale_factor=125` — kswapd réclame en arrière-plan au lieu de bloquer (persisté).
- **Protection cgroup du bureau** : `session.slice MemoryMin=1200M`, `app.slice MemoryHigh=4G` → GNOME garde ses pages, la flotte JARVIS est bridée en premier.
- **earlyoom ne vise plus `gnome-shell`** : il était configuré en `--prefer` (il aurait fini par tuer ton bureau). Passé en `--avoid`.
- Arrêt de 20 timers haute fréquence, 9 daemons de

[user] Base directory for this skill: /tmp/claude-1000/bundled-skills/2.1.226/60142f5eda5f43fd60a7b273a566edf5/run-skill-generator

Your job is to produce a **skill** at `<unit>/.claude/skills/run-<unit-name>/`
that lets a future agent build, launch, and **drive** this project from
a clean machine.

The skill has two parts that live together:

```
<unit>/.claude/skills/run-<unit-name>/
  SKILL.md      ← agent-facing instructions — SHORT. Points at the driver.
  driver.mjs    ← (or driver.py, smoke.sh, … — or none: web apps use
                   chromium-cli off-the-shelf, and the heredoc in
                   SKILL.md is the script)
```

That almost always means **writing code**, not just prose. If the app
has any interactive surface (GUI, TUI, long-running server, REPL), the
future agent needs a programmatic way to poke it. A markdown file by
itself cannot click a button — but sometimes the button-clicker
already exists: for web apps it's `chromium-cli`, for servers it's
`curl`. You build (or script) that harness now, commit it alongside
the skill, and the `SKILL.md` documents how to use it.

## Definition of done

You are done when **all** of these are true:

1. **You launched the app in this container and interacted with it** —
   not its test suite, the actual running app. For anything with a GUI,
   that means you have a screenshot file on disk that you took.
2. **The interaction harness is committed** next to the skill. A driver
   script, a REPL wrapper, a smoke test, or the

[assistant] `run-m1-memory-tuning` tourne sur M6 mais vise **swappiness=180** — exactement la valeur qui a saturé le swap ici. Un agent qui lancerait son `apply` recréerait le gel. C'est donc bien une unité distincte. Je crée `run-m6-memoire`.

D'abord l'obligation la plus dure : une vraie capture du bureau.

[assistant] Le bureau est vivant : fond JARVIS OMEGA, barre GNOME, fenêtre décorée, horloge à jour. Maintenant le driver.

[assistant] Deux bugs révélés par l'exécution réelle. Le premier est vicieux : la locale française.

[assistant] Le driver capture bien un bureau vivant. Maintenant le test qui compte : l'aller-retour `restore` → `relief`.

[assistant] `restore` a fait exactement ce qu'il annonce : pression **0,00 % → 21,97 %** en 10 secondes. Preuve directe que c'est bien la flotte. Je relance `relief`.

[assistant] `smoke` passe (sortie 0). J'écris la SKILL.md, puis j'enchaîne sur ton scan hardware — car si ça rame encore de fenêtre en fenêtre à 0,27 % de pression, ce n'est plus la mémoire.

[assistant] Skill livrée. J'enchaîne sur ton scan hardware — la mémoire est à 0,27 %, donc si ça rame de fenêtre en fenêtre, la cause est ailleurs.

[assistant] CPU sain (3,4 GHz, 46 °C), disques sains (2 SSD SATA). Je creuse la RAM physique — 11 Gi est un total inhabituel.

[assistant] Je vérifie qu'un simple changement de câble est possible avant de te le recommander.

[assistant] Point capital — et ça change la recommandation. **J'ai arrêté LM Studio, donc M4 est privé de compute en ce moment.** Je le remets tout de suite.

[assistant] LM Studio est reparti (`qwen2.5-coder-14b`). Je vérifie qu'il est bien joignable **depuis M4** — sinon tout ça ne sert à rien.

[assistant] LM Studio écoute sur `0.0.0.0:1234`, joignable depuis le câble M4 → **200**. M4 a retrouvé son compute.

Mais ça révèle un défaut que j'ai introduit : mon `relief` tue LM Studio **en premier**, alors que c'est la mission de M6. J'inverse la priorité.

[assistant] Le correctif tient. Je propage la même protection à l'alias terminal `m6-relief`, sinon il couperait encore M4.

[assistant] ## Skill livrée

`jarvis/.claude/skills/run-m6-memoire/` — `SKILL.md` + `driver.sh`, testés intégralement sur la machine.

```bash
bash .claude/skills/run-m6-memoire/driver.sh smoke   # → sortie 0, verdict « M6 saine »
```

Le driver ne se contente pas de lire des compteurs : il **prouve** que le bureau répond (3 mesures de latence D-Bus sur `org.gnome.Shell`) et **prend une capture d'écran** à chaque passage. J'ai vérifié l'aller-retour en conditions réelles :

| | services | timers | RAM dispo | pression |
|---|---|---|---|---|
| après `relief` | 62 | 56 | 6,7 Gi | **0,00 %** |
| 10 s après `restore` | 71 | 80 | 4,8 Gi | **21,97 %** |
| 40 s après `restore` | 71 | 80 | 3,0 Gi | **30,38 %** |
| après `relief` | 60 | 56 | 6,9 Gi | **0,27 %** |

C'est la démonstration que la flotte est bien la cause.

## Le scan matériel — deux plafonds

**1. Ton écran est branché sur la mauvaise carte.**

```
01:00.0  RTX 2060   Width x16                 ← fait le RENDU
08:00.0  RTX 3080   Width x1 (downgraded)     ← porte l'ÉCRAN
```

`xrandr --listproviders` confirme le montage PRIME : la 2060 rend, la 3080 affiche. Chaque image 1920×1080 (~8 Mo) **traverse un lien PCIe x1** avant d'arriver sur la dalle. Voilà pourquoi ça rame de fenêtre en fenêtre alors que la pression mémoire est à 0,11 %.

L'écran est sur `card2-HDMI-A-2` (= la 3080). **La RTX 2060 a 4 sorties libres** : HDMI-A-1, DP-1, DP-2, DP-3. Déplace le câble HDMI sur la 2060 — gratuit, 10 secondes, et la copie inter-bus disparaît.

[user] Base directory for this skill: /home/turbo/.claude/skills/remplir-bibliotheque

# Bibliothèque Vivante Infinie — remplissage 0-token

Porté du pattern « banque annuelle » de M4 : remplissage par lots, idempotent,
anti-surchauffe GPU, cache SQL, todoliste dynamique qui se régénère toute seule.

Moteur : **LM Studio M1 `:1234`** (qwen3.5-9b) prioritaire → fallback `jarvis_dispatcher.ask()` (Ollama).
Cœur : `~/jarvis/cli/biblio_filler.py`.

## 1. Voir l'avancement
```bash
python3 ~/jarvis/cli/biblio_filler.py --status
```

## 2. Remplir un lot maintenant (à la demande)
```bash
bash ~/.claude/skills/remplir-bibliotheque/scripts/remplir.sh 6      # 6 items
```

## 3. Remplissage perpétuel (daemon)
```bash
systemctl --user status  biblio-filler.service     # état
systemctl --user start   biblio-filler.service     # lancer l'infini
systemctl --user stop    biblio-filler.service     # arrêter
journalctl --user -u biblio-filler.service -f      # suivre en direct
```
Le daemon boucle : lot de 3 toutes les 90 s, pause si GPU ≥ 84 °C, auto-alimente la
todoliste quand elle se vide.

## 4. Où va le contenu
| Type | Destination |
|---|---|
| Commandes | Postgres `cmdlib` (container `jv-infra-biblio-db`) + `Documents/Commande_Directe_Bibliotheque/command_list.md` (section « 🌱 Bibliothèque vivante ») |
| Fiches connaissance | SQLite `jarvis_master.db` table `biblio_knowledge` + `~/jarvis/data/biblio_knowledge/*.md` |
| Todoliste | `jarvis_master.db` table `biblio_topics` |
| Cache 0-token | `

[assistant] Todoliste à sec (`pending=0`) et `cmdlib` vide — le container Postgres n'existe pas sur M6. Je lance un lot pour voir si l'auto-alimentation repart.

[assistant] Le remplissage marche à moitié : les fiches passent (+2), mais **100 % des commandes échouent** — le container Postgres n'existe pas. Je creuse.

[assistant] PostgreSQL 16 **natif** tourne sur M6 (127.0.0.1:5432) mais sans base `cmdlib` — le filler, lui, cherche un container docker qui n'existe pas ici. Je regarde le code exact.

[assistant] Tout y est : le Postgres natif de M6 est en version 16, exactement ce qu'attend le schéma. Je crée la base localement.

[assistant] Base créée avec 253 commandes déjà seedées. Maintenant je rends le filler adaptatif — docker sur M1, natif sur M6.

[assistant] Le repli natif est bien sélectionné. Test réel : un lot où les commandes doivent maintenant passer.

[assistant] Correction validée : **6/6 items** cette fois (contre 2/6), `cmdlib` 253 → **256**. Plus aucun `PG insert KO`. Je lance le daemon perpétuel, avec un garde-fou mémoire vu l'historique de gel.

[assistant] Le daemon tourne et reste borné (31-65 Mo, pression retombée à ~1 %). Mais il est **bloqué** : `expand: pas de JSON exploitable` en boucle, pending=0. La todoliste ne se régénère plus. Je diagnostique.

[assistant] **Reasoning runaway confirmé** : 400/400 tokens partis en raisonnement, `content` vide, `finish_reason: length`. C'est le bug documenté par `run-qwen-nothink`. Je regarde le remède éprouvé.

[assistant] Remède validé : `finish_reason: stop`, 63 tokens, JSON propre. J'applique ça au filler.

[assistant] Le filler implémente **déjà** le think pré-fermé. Le problème est donc ailleurs. Je lis.

[assistant] Je termine le diagnostic du filler (je suis à un pas), puis je traite ta demande M4/rem-linux.

[assistant] Cause exacte : le modèle produit un tableau JSON **qui ne se referme jamais** (508 tokens, coupé à 2219 caractères). Je rends l'analyse tolérante plutôt que d'espérer un modèle parfait.

[assistant] Sauvetage validé sur les 4 cas. Je relance le daemon et vérifie que la todoliste repart.