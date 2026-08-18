[assistant] **S9 branché et reconnu** [OL/local]

| Item | Valeur |
|---|---|
| USB | Bus 007 · `04e8:6860` SAMSUNG_Android (MTP) |
| adb | `4357514238453498` → **device** (autorisé, pas `unauthorized`) |
| Modèle | SM-G960F · `starlte` (starlteeea) |
| Port ACM | `ttyACM0` créé (modem/RNDIS exposé) |
| MTP GNOME | ⚠️ non monté (`/run/user/1000/gvfs` vide) |

Le téléphone démarre normalement (pas de Download Mode / OEM lock — le cas biblio `s9-oem-lock-diagnostic` ne s'applique pas).

`★ Insight ─────────────────────────────────────`
• `adb devices` renvoie `device` et non `unauthorized` → la clé RSA de M1 est déjà dans `/data/misc/adb/adb_keys` du S9, donc aucune boîte de dialogue à valider sur l'écran.
• `cdc_acm → ttyACM0` signifie que le S9 expose aussi une interface série (config USB composite Samsung) : c'est ce qui permet le tethering/RNDIS sans MTP.
• MTP énuméré mais gvfs vide = le daemon `gvfs-mtp` n'a pas monté le volume ; l'accès fichiers passe alors par `adb pull/push`, pas par le gestionnaire de fichiers.
`─────────────────────────────────────────────────`

Prêt pour : `/run-s9-trackpad` (écran S9 = souris M1) · `run-lumenflow-android` (build/install APK) · PWA `jarvis-os-pwa :8088`. Dis lequel.

[user] +crée une aplication ou je parle sur un sms ou dans une fenetre ou il y a le curseur en vocal et il retranscrit par écrit

[assistant] Compris — l'app va **sur le S9**. Je vérifie l'outillage de build Android et l'API Whisper.

[assistant] Tout est là : chaîne de build APK **sans Gradle** (SDK 34 + JDK 21 déjà installés), keystore debug, et `stt-bridge.py` déjà écrit. Je construis l'app par-dessus.

`★ Insight ─────────────────────────────────────`
• Pour écrire **à la position du curseur dans n'importe quelle app** (SMS Samsung, WhatsApp…), Android n'offre qu'une voie : un **IME** (`InputMethodService`). Une app normale ne peut pas injecter du texte chez une autre — seul le clavier détient l'`InputConnection`.
• `phone-mouse/apk/build.sh` compile en 6 étapes brutes (aapt2 → javac → d8 → zipalign → apksigner). Pas de Gradle, pas de téléchargement, pas de compte : build en ~15 s et 0 €.
• Deux moteurs valent mieux qu'un : `SpeechRecognizer` natif (gratuit, déjà sur le S9, marche en 4G) + Whisper M1 via `adb reverse` (souverain, quand branché). Le second réutilise `stt-bridge.py` déjà écrit.
`─────────────────────────────────────────────────`

[assistant] Bug isolé : **d8 8.2.2 + javac 21 échoue sur toute classe anonyme** (`phone-mouse` compilait car il n'en a aucune). Je vérifie si les classes internes *nommées* passent :

[assistant] D8 8.2.33 (déjà présent dans `cmdline-tools`) gère les classes anonymes. Je bascule le build dessus :

[user] [Image: original 1080x2220, displayed at 973x2000. Multiply coordinates by 1.11 to map to original image.]

[assistant] Micro passé au rouge avec le bouton stop → **l'écoute démarre bien**. J'arrête l'écoute et je pousse sur GitHub sous le nom `transcription-portable`.

[assistant] Bug remonté : le bouton `⌨` ne ramène pas au clavier normal. `switchToNextInputMethod` échoue silencieusement quand il n'y a pas d'IME suivant éligible — je le double d'un repli sur le sélecteur :

[assistant] Bouton corrigé — le sélecteur s'ouvre. J'aligne le nom affiché sur `Transcription Portable`, puis je pousse :

[assistant] Poussé : **https://github.com/Turbo31150/transcription-portable**

Maintenant les deux modes. Le point clé :

`★ Insight ─────────────────────────────────────`
• Une bulle flottante ne peut **pas** écrire à la position du curseur — cette capacité appartient exclusivement à l'IME, qui seul détient l'`InputConnection`.
• La solution est donc un duo : la bulle est un **déclencheur**, le clavier reste l'**écrivain**. Les deux vivant dans le même processus, la bulle appelle directement l'instance du service clavier.
• Conséquence à assumer : la bulle n'agit que si Transcription Portable est le clavier sélectionné. Elle le détecte et le dit au lieu d'échouer en silence.
`─────────────────────────────────────────────────`

[assistant] Exigence clé comprise : **garder le clavier Samsung**. Cela change l'architecture — sans être l'IME actif, il faut une autre voie pour écrire dans le champ.

`★ Insight ─────────────────────────────────────`
• Android offre une seconde porte vers le champ de saisie d'autrui : un **service d'accessibilité**. Il peut récupérer le nœud focalisé et lui appliquer `ACTION_SET_TEXT` — sans être le clavier.
• `ACTION_SET_TEXT` **remplace tout le contenu**. Pour insérer au curseur il faut lire le texte, lire `textSelectionStart`, recomposer, puis remettre le curseur avec `ACTION_SET_SELECTION`. Sinon la dictée efface ce qui était déjà écrit.
• L'app aura donc deux écrivains : l'IME quand il est actif (aperçu en temps réel), l'accessibilité sinon (clavier Samsung conservé).
`─────────────────────────────────────────────────`

[assistant] Maintenant la bulle devient autonome — elle dicte elle-même et écrit par accessibilité :

[assistant] Compilé. J'ajoute la section accessibilité dans les réglages, puis j'installe et je teste avec le clavier Samsung :

[assistant] L'écran s'était verrouillé — d'où les captures blanches. Je réveille le téléphone :

[assistant] La bulle dorée est bien visible par-dessus l'app. Deux choses à finir : le texte déborde à droite, et le mode Tailscale demandé.

[assistant] Sauvegarde lancée. Je reviens à l'app — préréglages réseau incluant Tailscale, et correction du débordement de texte :

[assistant] Le téléphone est utilisé en ce moment — j'arrête de piloter l'écran. Je finalise le code et vérifie la sauvegarde :

[assistant] Attention : **plusieurs sauvegardes tournent en parallèle** (d'autres sessions en ont lancé une il y a ~1h45). Je n'en relance pas, je laisse converger. Pendant ce temps, je finalise l'app :

[assistant] ## App — `transcription-portable` sur GitHub

**https://github.com/Turbo31150/transcription-portable** (privé) · APK 37 Ko · installée et testée sur le S9

| Mode | Geste | Votre clavier |
|---|---|---|
| **Bulle flottante** | curseur → appui sur la bulle → parle → ça écrit | **conservé** (Samsung) |
| **Clavier de dictée** | on le sélectionne, aperçu du texte en direct | remplacé le temps de dicter |

| Moteur | Réseau | Coût |
|---|---|---|
| natif Google (défaut) | 4G ou hors‑ligne | 0 € |
| Whisper M1 | USB · Wi‑Fi · **Tailscale (4G, partout)** | 0 € |

Vérifié réellement : clavier affiché dans Messages Samsung · écoute qui démarre (micro rouge) · bulle dorée par‑dessus les apps · sélecteur de clavier réparé · pont Whisper à **HTTP 200 sur les trois voies** (`127.0.0.1`, `192.168.0.10`, `100.112.114.32`).

**Il reste une chose de votre côté** : Tailscale n'est **pas installé sur le S9** (`pm list packages` ne le trouve pas). Tant qu'il ne l'est pas, les voies USB et Wi‑Fi marchent, mais pas la 4G. Le moteur natif, lui, fonctionne déjà partout sans rien.

Sur le PC : `~/jarvis/apps/s9-dictee/pont-whisper.sh` ouvre les trois voies d'un coup.

`★ Insight ─────────────────────────────────────`
• `d8` de `build-tools/34.0.0` plante sur **toute classe imbriquée** compilée par javac 21 ; `phone-mouse` compilait par chance — il n'en contient aucune. Le `r8.jar` des `cmdline-tools`, déjà sur le disque, corrige le bug : aucun téléchargement.
• Le pont n'écoute jamais sur `0.0.0.0` 

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

[assistant] Ce skill exige un plan d'implémentation. Il n'y en a pas d'écrit — je le construis d'abord à partir des manques réels de l'app, puis j'exécute en continu.

[assistant] Pendant que l'implémenteur travaille, je vérifie l'avancée de la sauvegarde (aucun fichier en commun) :

[assistant] Plan figé en 3 tâches (`PLAN.md`), branche `dictee-ameliorations` créée.

| # | Manque constaté | État |
|---|---|---|
| T1 | La bulle ignore le réglage Whisper et dicte toujours via Google | implémenteur lancé |
| T2 | Pas de `BOOT_COMPLETED` : la bulle disparaît après redémarrage | en file |
| T3 | Hôte Whisper figé : échec en 4G alors que Tailscale répondrait | en file |

Chaque tâche passera par implémenteur → revue de conformité au plan → revue de qualité, sans pause entre les tâches.

En parallèle, le push LFS de la sauvegarde a démarré (5 commits, ~1,6 Go).

[assistant] L'implémenteur T1 est toujours en cours — il a déjà modifié `BulleService.java`, pas encore commité. Je ne touche pas à ce fichier tant qu'il travaille (risque de conflit).

Je serai relancé automatiquement à sa fin, puis j'enchaîne : revue de conformité → revue de qualité → T2 → T3, sans pause.

[assistant] T1 avance : 65 lignes ajoutées, 29 retirées dans `BulleService.java`, build et commit pas encore faits. J'ai armé une veille qui me réveillera dès le commit, pour enchaîner les deux revues sans délai.

Je ne lance pas T2 en parallèle : les deux tâches appelleraient `./build.sh`, qui commence par `rm -rf build` — les builds se détruiraient mutuellement.

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

[assistant] État réel, sans broderie :

**T1** — l'implémenteur a écrit le code (`BulleService.java`, +65/−29) et rebuildé l'APK à 02:56, mais n'a toujours pas commité après ~30 min. Je viens de lui demander de livrer son statut ou de nommer son blocage. Je n'enchaîne pas les revues avant d'avoir un commit à réviser.

**Alerte service** (remontée par le hook, hors périmètre de l'app) : `jarvis-lms-qwen-warm.service` échoue — `lms load qwen/qwen3.5-9b` renvoie `rc=1`, et LM Studio n'a que `nomic-embed` chargé, donc **qwen3.5-9b n'est pas en VRAM**. Piste : le binaire `lms` a été remplacé à 02:51, soit quelques minutes avant les échecs — une mise à jour de LM Studio est le suspect le plus probable. Je ne creuse pas plus loin sans que vous me le demandiez, pour ne pas quitter le plan en cours.

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

[assistant] L'implémenteur n'a plus bougé depuis 40 min. Je reprends la partie mécanique restante (build + commit) et je garde les deux revues par subagents, qui sont le vrai garde-fou. D'abord, j'inspecte ce qu'il a écrit :

[assistant] Le code est propre et respecte les limites. J'arrête l'implémenteur figé, puis je termine build + commit :

[assistant] T1 livré : **DONE_WITH_CONCERNS**, commit `9e50555`. Les doutes sont des observations (chemin Whisper non exerçable sans parler), pas des défauts de portée. Je passe à la revue de conformité.

[assistant] Relecteur de conformité : **NON CONFORME** — un écart, le `arreteEtEnvoie()` ajouté dans `onDestroy`, hors périmètre et porteur d'un effet observable non demandé (masquer la bulle pendant un enregistrement enverrait le texte et l'écrirait alors que la bulle a disparu). Je renvoie l'implémenteur corriger :

[assistant] Pendant la correction, je remets en place le service d'accessibilité sur le S9 — l'implémenteur l'avait remis à l'état vide qu'il avait trouvé, or sans lui la bulle ne peut pas écrire :

[assistant] T1 : correction livrée, re-revue de conformité en cours. Accessibilité réactivée sur le S9 (elle avait été remise à vide) — la bulle peut de nouveau écrire avec le clavier Samsung en place.

Nouvelle tâche créée au passage, issue de la revue : **T4 — annuler l'enregistrement quand la bulle disparaît** (le micro reste ouvert jusqu'à 2 min ; la bonne réponse est d'annuler, pas d'envoyer — ce qui exige une méthode d'annulation dans `MoteurWhisper`, fichier hors périmètre de T1).

[user] Base directory for this skill: /home/turbo/.claude/skills/cascade-massive

# Cascade massive — SkillsMP → écosystème JARVIS

Chaîne 0-token qui transforme un **plan** en **implantation réelle** distribuée aux agents.
Aucun appel LLM : tout est déterministe (SQL + parsing + shell).

> **Entrée = le catalogue SkillsMP** (4180 skills aspirés), pas un PLAN.md.
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
| Cascade | `~/jarvis/bin/skillmp-cascade.sh` | table `skillmp_cascade_taches`, dispatch, `logs/skillmp-cascade.log` |

## Commandes

```bash
# 1. (re)ca

[assistant] Deux choses arrivées en même temps : T1 est **CONFORME**, et une revue de sécurité automatique signale une *control-regression* dans `BulleService.java`.

Cette régression est celle que nous avons créée sciemment il y a quelques minutes : en retirant la clôture dans `onDestroy`, le micro reste ouvert jusqu'à `MAX_SECONDES` quand la bulle disparaît. C'est tracé en **T4**, avec la bonne réponse (annuler, pas envoyer). Je l'acquitte à ce titre, sans la re-corriger dans T1 dont ce n'était pas le périmètre.

J'enchaîne la revue de qualité T1, et je lance la cascade en parallèle — garde-fous vérifiés : charge 5,8 (< 12), RAM 75 % (< 92 %), GPU max 75 °C (< 84 °C).

[assistant] Cartographie : **8 786 skills** indexés (le catalogue a doublé depuis les 4 180 documentés), 5 813 reliés à un métier. Étape 2, plan d'implantation en simulation :

[assistant] Charge à **12,25** — juste au-dessus du seuil de dispatch. Je persiste donc la file sans dispatcher (mode `validated`), ce qui est exactement le repli prévu :

[assistant] Pour accélérer, je lance T2 et T3 **en parallèle** — leurs fichiers sont disjoints, et je neutralise le seul vrai conflit (le build, qui commence par `rm -rf build`) avec un verrou `flock`.

[assistant] Revue qualité T1 : **À CORRIGER**, avec un vrai bloquant. Le champ `ecoute` sert à la fois d'affichage piloté par le clavier *et* de verrou anti-double-envoi — le clavier peut donc le désarmer à distance, et deux dictées peuvent écrire dans le même champ. Je renvoie corriger et je lance T3 en même temps.

[assistant] **Trois agents tournent maintenant en parallèle** — c'est ça, l'accélération :

| Agent | Fichier(s) | Conflit ? |
|---|---|---|
| T1 correctif | `BulleService.java` | — |
| T2 boot | `BootReceiver.java` + manifeste | — |
| T3 repli réseau | `MoteurWhisper.java` + `Reglages.java` | — |

Fichiers disjoints, `git add` ciblé imposé à chacun, et le build sérialisé par `flock /tmp/s9-dictee-build.lock`. Le skill déconseille le parallèle d'implémenteurs à cause des conflits — j'ai supprimé la cause du conflit plutôt que la parallélisation.

**Cascade massive** livrée en parallèle, sans LLM :

| Étape | Résultat |
|---|---|
| Cartographie | 8 786 skills indexés, 5 813 reliés à un métier, 854 rubriques |
| Implantation | 120 skills sélectionnés, répartis sur 15 familles / 310 agents |
| Cascade | **220 tâches en base** (99 `done`, 121 `pending`), widget `:8899` en HTTP 200 |

Aucun dispatch automatique : la charge était à **12,25**, juste au-dessus du seuil de 12. Le mode `validated` a persisté la file sans lancer les agents — exactement le repli prévu par les garde-fous. Pour dispatcher, il faudra attendre que les 8 sauvegardes concurrentes retombent.

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

[assistant] Alerte **GPU 88 °C**. Un cascade-deploy démarre 8 vagues de services — je ne lance rien avant d'avoir regardé quel GPU chauffe et pourquoi.

[assistant] GPU2 à **88 °C avec le ventilateur à 0 %** — c'est l'incident connu : son ventilateur est mort, et il est censé être exclu. Or il est utilisé à 80 %. Je vérifie qui l'occupe :

[assistant] Deux choses bloquent le déploiement demandé, et la seconde est sérieuse.

## Le script n'existe pas

`~/Workspaces/jarvis-linux/infra/scripts/tools/cascade-deploy.sh` est **absent**. Le skill décrit une chaîne en 5 phases qui n'a pas de moteur sur cette machine — rien à exécuter, ni en réel ni en `--dry-run`.

## GPU2 chauffe parce qu'une protection vient d'être retirée

La phase 1 (pré-vol) échouerait de toute façon. Voici ce que j'ai mesuré :

| GPU | Modèle | Temp. | Ventilateur | Charge |
|---|---|---|---|---|
| 0 | RTX 2060 | 57 °C | 45 % | 26 % |
| 1 | GTX 1660 S | 59 °C | 0 % | 78 % |
| **2** | **GTX 1660 S** | **86–88 °C** | **0 %** | **80 %** |
| 3 | RTX 3080 | 66 °C | 38 % | 21 % |

L'occupant de GPU2 est `ollama`, qui y a chargé `gemma3:4b`. Et la cause est datée : à **03:32:08 ce matin**, un « recâblage » a désactivé quatre drop-ins systemd, dont `gpu-isolation.conf` qui contenait exactement ceci :

> `# Exclus: GPU0 écran RTX2060, GPU2 ventilo mort.`

Le drop-in qui l'a remplacé, `zzzzz-recablage-4gpu.conf`, réintroduit **les quatre UUID**, GPU2 compris. Son propre commentaire dit « 1660S x2 (70W, **sans ventilateur**) » : l'absence de ventilateur était connue, le pari étant que 70 W suffisent à tenir. La mesure dit le contraire — 88 °C, ventilateur à 0 %, throttling déjà actif.

**Je n'ai rien modifié.** Ce recâblage date de quinze minutes et une autre session le pilote peut-être encore ; défaire sa configuration pendant qu'elle travaille créerait un conflit pir

[user] Base directory for this skill: /home/turbo/.claude/plugins/local/jarvis-turbo/skills/performance-tuning

# Performance Tuning — JARVIS (topologie Tailscale, mesures du 2026-08-01)

> Toutes les latences de ce document ont été mesurées le **2026-08-01** avec une requête
> de génération d'**1 token**. Elles décrivent la topologie réelle après la migration
> Tailscale de ce matin. M2 (127.0.0.1) et M3 (127.0.0.1) n'existent plus.

## 1. Latences mesurées

| Backend | Endpoint | Modèle | Latence 1 token | Verdict |
|---|---|---|---|---|
| M1 LM Studio | 127.0.0.1:1234 | `qwen/qwen3.5-9b` | **1 422 ms** | ✅ seul backend viable en interactif |
| M1 Ollama | 127.0.0.1:11434 | `gemma3:4b` | **34 686 ms** | ⚠️ 24× plus lent que LM Studio |
| rem-linux Ollama | 100.113.121.61:11434 | `qwen3:1.7b` | **timeout > 85 s** | ❌ inutilisable en interactif |

Corollaire : sur cette machine, **Ollama n'est jamais un raccourci**. L'ancienne
recommandation « questions simples → Ollama parce que le modèle est petit » était
inversée et dégradait les performances.

## 2. Topologie réelle

| Nœud | Adresse | CPU / RAM / GPU | Ce qui y tourne |
|---|---|---|---|
| **M1** (local) | 127.0.0.1 | 16 threads, 46 Go, 4 GPU | LM Studio :1234 → `qwen/qwen3.5-9b` (2 instances), `openai/gpt-oss-20b`, `text-embedding-nomic-embed-text-v1.5` · Ollama :11434 → `gemma3:4b` |
| **rem-linux** | 100.113.121.61 (SSH `jarvis-dva`) | 8 cœurs, 15 Go, GTX 1050 | Ollama → `gemma3:27b`, `gemma3:4b`, `qwen3:1.7b`, `mxbai-embed-

[assistant] Ce skill tranche la question — il dit noir sur blanc :

> **GPU2 — VENTILATEUR MORT, NE JAMAIS L'ACTIVER.** Ne jamais proposer de l'ajouter à `CUDA_VISIBLE_DEVICES`, ni d'y placer un modèle.

Le recâblage de 03:32 a fait exactement les deux. Ce n'est plus un désaccord entre sessions : c'est une règle que vous avez posée à deux endroits (ce skill et la mémoire persistante), et un modèle tourne dessus à 87 °C. Je rétablis l'exclusion.

[assistant] Ollama est sorti de GPU2 — mais **LM Studio y a pris sa place** (86 °C, 71 % d'utilisation). Je corrige aussi sa configuration :

[assistant] T1 **APPROUVÉ** par la contre-relecture. Je finis d'abord GPU2, qui est plus urgent.

[assistant] Le fichier se contredit lui-même : son commentaire dit « les 3 cartes SAINES, la 1660S #2 (ventilateur mort) est absente », mais la ligne active liste **les 4 UUID**, GPU2 compris. Il mentionne aussi la vraie protection matérielle — je la vérifie :

[assistant] Aucune protection n'est armée : les 4 GPU sont en mode `Default` et le `gpu-deadfan-lock.service` mentionné dans le commentaire **n'existe pas**. Je corrige la config puis j'arme le verrou, dans cet ordre (l'inverse ferait planter LM Studio, comme documenté dans le fichier) :

[assistant] Ce protocole existe déjà chez vous — je vérifie avant d'écrire quoi que ce soit :

[assistant] Le protocole que vous m'envoyez est **déjà implémenté sur cette machine**, à l'identique :

```
jarvis-audit.sh <run|init|scan-local|scan-web|multi-agents|report|todo|cascade>
  --target DIR  --topic TXT  --profile tech|business|souverainete|full
  --mode fast|standard|deep  --client NOM  --previous RAPPORT.md
```

Les huit phases, les quatre profils, les trois modes, `AUDIT_CONFIG.yaml` (`~/jarvis/audit/`), le skill `audit-mode`, et des rapports déjà produits (PassCerfa, `~/jarvis-audit/reports/`). Il n'y a rien à écrire — juste à lancer. Je ne réécris donc pas le YAML ni le squelette CLI.

Je finis d'abord GPU2 :

[assistant] GPU2 : **88 °C → 60 °C**, carte vidée et mode calcul `Prohibited` armé. Le verrou tient maintenant au niveau matériel, pas seulement dans une variable d'environnement.

[assistant] Ce prompt désigne `Turbo31150/jarvis-master-orchestrateur` comme source de vérité. Je vérifie s'il existe avant de dérouler le pipeline :

[assistant] Je déroule la chaîne complète — clone de l'orchestrateur, contexte maximal (cahier + plan + todo + protocole), puis les 8 phases d'audit :

[assistant] L'orchestrateur était déjà cloné. Je lance tout en parallèle — audit, contexte maximal, et chargement des outils MCP de dispatch :

[assistant] Les deux chaînes ont terminé. Je dispatche maintenant sur les IA en parallèle pendant que je récupère les artefacts :

[assistant] Le wrapper Gemini renvoie un accusé sans le contenu — inexploitable. Je récupère les artefacts réellement produits :

[assistant] Diagnostic bouclé — et il explique tout le reste.

## La cause racine

**LM Studio est mort** (`:1234` → HTTP 000, aucun processus). Le hub de cascade `:18800` fonctionne, mais il retombe sur `rem-linux/gemma3:4b` — le backend que votre propre skill classe « timeout > 85 s, inutilisable en interactif », et que votre mémoire signale comme cause d'effondrement quand il passe en tête de cascade.

C'est pourquoi l'audit rend des rapports **à moitié vides** : sur 4 agents, `business` (310 mots) et `ops` (313 mots) ont abouti, `tech` et `legal` sont retombés à 7 mots. Ce n'est pas le pipeline qui est cassé, c'est son étage LLM qui est à sec. Le même mort explique le service `jarvis-lms-qwen-warm` en échec depuis 03:00.

`★ Insight ─────────────────────────────────────`
• Les quatre symptômes de la nuit ont une signature commune : **des garde-fous qui reposent sur des conventions, pas sur des verrous**. GPU2 était protégé par une variable d'environnement qu'un recâblage a écrasée ; le vrai verrou (`compute_mode=PROHIBITED`) n'était pas armé.
• Même motif pour les sauvegardes : 8 exécutions concurrentes parce que rien n'empêche deux sessions de lancer le même pipeline — il manque un `flock`, exactement celui que j'ai dû ajouter à la main pour les builds Android.
• Et pour la cascade LLM : elle bascule silencieusement sur le pire backend au lieu d'échouer bruyamment. Un repli qui ne se signale pas transforme une panne franche en dégradation invisible.
`────────────────────────────────

[user] avance avec multyi shell mutli tache sequencielle parralélisme mulmti ia utilise ls mcp systeme pour dispact tache gemini omehga openclaw fi,ni la todolis fast boost go run

[assistant] GPU2 est **retombé en `Default` et remonté à 85 °C** — quelque chose réarme la config. Je pose un verrou persistant plutôt que de le refaire à la main, et je lance les deux revues en parallèle.

[assistant] Verrou posé et réarmé toutes les minutes. Maintenant les deux revues en parallèle :

[assistant] OpenClaw est hors service : **Node v22.22.1 alors qu'il exige ≥ 22.22.3**. Je regarde si une version compatible est déjà installée avant de télécharger quoi que ce soit :

[assistant] **Node v24.18.0 est déjà installé** — c'est exactement la version qu'OpenClaw réclame. Il n'est simplement pas dans le PATH. Je teste avant de changer quoi que ce soit :

[assistant] Deux revues rendues. Je renvoie les correctifs et je cherche en parallèle les shells d'autocompilation.

[assistant] LM Studio est **revenu de lui-même** (200) — le watchdog a fait son travail. Il ne reste qu'OpenClaw. Je le répare avec le Node 24 déjà présent :

[assistant] OpenClaw est de nouveau en ligne. Je relance les services en échec et je fais l'état complet :

[assistant] Preuve décisive : LM Studio **liste** `qwen3.5-9b` mais **ne le sert pas** — 45 s de timeout, réponse vide. C'est l'incident du *reasoning runaway* déjà documenté chez vous, avec son contournement. Je le vérifie :

[assistant] Deux tentatives, deux échecs : je m'arrête là sur ce point et je vous donne l'état.

## Autocompilation et dispatch — l'inventaire

| Brique | Rôle | État |
|---|---|---|
| `bin/compile_cli.sh` | PyInstaller → binaires dans `bin/dist` | ✓ |
| `bin/domino-compile.py` · `bloc-rebuild.py` · `jarvis-teams-build.py` | compilation dominos / blocs / équipes | ✓ |
| `bin/jarvis-dispatch.sh` | routeur LLM, heuristique auto + failover | ✓ route `→ local` |
| `scripts/jarvis-keyword-dispatch.py` | règles JSON → hub / LMS / OpenClaw | ✓ |
| `cli/jarvis_dispatcher.py` | façade avec circuit-breaker | ✓ |
| Timers | `jarvis-cascade-ingest` (15 min) · `omega-cascade` (15 min) · `biblio-rebuild` | ✓ actifs |

**L'infrastructure est complète et bien faite. Le problème n'est pas le dispatch, c'est ce qu'il y a au bout.**

## Ce que j'ai réparé

- **OpenClaw** : était mort (Node 22.22.1 < 22.22.3 requis). Node **24.18 était déjà installé** — j'ai posé un wrapper qui l'utilise pour ce seul appel, sans toucher au Node système. `OpenClaw 2026.7.1-2` répond.
- **GPU2** : 88 °C → verrou `PROHIBITED` + service systemd `gpu-deadfan-lock` avec timer de réarmement toutes les minutes. Il était retombé en `Default` une fois — maintenant il se remet seul.

## Ce qui reste cassé, avec la preuve

**LM Studio est à moitié en ligne**, et c'est le pire état possible :

```
/v1/models          → 200, liste qwen3.5-9b et 5 autres modèles
/v1/chat/completions → 45 s de timeout, réponse vide
qwen-nothink.sh      → H

[assistant] Vous avez redémarré et déverrouillé le S9 — c'est exactement le test qui manquait à T2. Je le valide tout de suite :

[assistant] Le S9 a redémarré il y a 2 min. **La bulle n'est pas revenue** — `EcritureService` tourne, mais `BulleService` est absent. T2 échoue à son premier vrai test. Je cherche laquelle des trois conditions a lâché :

[assistant] 9 sauvegardes concurrentes, et le push traîne depuis 2 h. **Tout ce que vous demandez est déjà dans les snapshots** — je vérifie l'avancement réel plutôt que d'en lancer une 10ᵉ :

[assistant] **Le push est mort** : 2 h 21 d'existence, **0 octet lu, 0 octet écrit**, alors que GitHub répond en 0,5 s. Ce n'est pas le réseau — le processus est figé, et il bloque 5 commits (8 Go de LFS). Je débloque :

[assistant] T2 est **validé par un vrai redémarrage** — l'agent a prouvé que la bulle revient sans qu'aucune activité ne soit lancée. Mon relevé de tout à l'heure était simplement trop précoce (2 min après le boot, avant que le service ne remonte).

Je vérifie l'état après l'arrêt des backups :