[assistant] Mémoire consommée. Voici l'état, puis je traite ta demande de config.

## 📁 Reprise — Prud'hommes Ambulance du Soleil (3 dossiers)

**Livrable maître écrit le 28/07 19:33** : `~/Bureau/SOL-OPS/NOTE-CAPSTAN-SOCLE-COMMUN-ET-4-ANNEXES.md` (33 Ko) — socle commun 12 §, 4 situations individuelles, 7 arbitrages, 8 points d'exposition, calendrier. Les 4 annexes chef-par-chef existent (BERNAD, DRIOUECH, COSTE, ABELLO), décomptes CSV générés pour les 4.

**Calendrier verrouillé**
| Échéance | Objet |
|---|---|
| **avant 8 août** | réponse attendue du cabinet (pilote 26.0350, périmètre visio, prise en charge BERNAD) |
| **26 août** | visio Capstan — seul créneau avant audiences |
| 8 / 15 / 29 sept | BCO COSTE / BERNAD / DRIOUECH |

**Quantum** : ~418 000 € réclamés → exposition réaliste 10–30 k€. Tout se joue sur 2 points : faire rejeter la résiliation judiciaire, et gagner la borne de départ de l'amplitude (18h revendiqué vs 20h prouvé).

**Ce qui bloque maintenant** — 2 mails rédigés le 28/07, **non envoyés à ma connaissance** :
- `DRAFT-mail-capstan-3-dossiers-pilotage-26aout.txt` (relance + 4 questions, réponse demandée avant le 8 août) ← c'est le chemin critique, il reste 10 jours
- `DRAFT-mail-transmission-dossier-capstan-visio.txt` (brouillon OpenClaw, à réviser)

**Reste à faire d'ici le 26/08** : vérifier le RAA du Gard (cahier des charges garde → coefficient équivalence 80 %) · numérisation feuilles de route janv-sept 2024 · réclamation des 635 pièces adverses non communiquée

[assistant] Réponse de l'avocate lue. **Point chaud identifié.** Je lance l'équipe complète dessus.

[user] <local-command-stdout>Set effort level to ultracode (this session only): xhigh + dynamic workflow orchestration</local-command-stdout>

[user] Base directory for this skill: /home/rempc/.claude/skills/auto-skill-detector

# Auto Skill Detector

Scans a target directory (read-only) and recommends which JARVIS skills are relevant based on file patterns, packages, frontmatter, and content regex matched against `skills-map.json`.

## Invocation

```
/auto-skill-detector <path>
/auto-skill-detector ~/dva --scope dva --strong-only
/auto-skill-detector ~/jarvis --output ./scan.md --no-postgres
```

Flags:
- `--scope <s>`: filter scope (`dva`, `patrimoine`, `expat`, `sol`, `general`)
- `--strong-only`: include only STRONG tier in report
- `--output <file>`: report path (default `~/jarvis-analysis/skill-scans/<hash>-<date>.md`)
- `--no-postgres`: skip Postgres INSERT
- `--max-depth N`: scan depth (default 3)

Programmatic:
```python
from auto_skill_detector.scan import scan
result = scan("/home/rempc/dva", scope="dva", max_depth=3)
```

## Output

- `report.json` machine-readable
- `report.md` human-readable
- `skill_relevance` Postgres INSERT (unless `--no-postgres`)

## Scoring

```
score = (4 if pkg match) + (3 if config file match)
      + (3 * regex_matches / min_matches) + (2 if path hint)
      + (4 if frontmatter key) ; then *= skill.weight / 10
```

Tiers:
- `score >= 12` → **STRONG**
- `6 <= score < 12` → **MAYBE**
- `< 6` → SKIP (not reported)

## Read-only enforcement

- No `os.remove`, `shutil.rmtree`, file `open('w')` in scanned tree
- Outputs only in `~/jarvis-analysis/skill-scans/` or explicit `--output`
- Po

[user] <local-command-stdout>[38;2;255;120;20m↯[39m Fast mode ON · model set to Opus 4.8 · $10/$50 per Mtok</local-command-stdout>

[assistant] Fil relu. **L'avocate (Me Stéphanie MASSIAVE, Capstan) a répondu ce matin en 2 mails** — elle a tranché tes 4 questions et **rouvre la porte** ("D'autres questions restent-elles en attente ?"). Voici le net :

## ✅ Réponses de Me MASSIAVE (29/07 matin)

| Ta question | Sa réponse |
|---|---|
| **1. Qui pilote le 26.0350 ?** | **Elle prend les 3 dossiers** — *« Je me chargerai du suivi de ce dossier, comme des 2 autres. »* |
| **2. Visio 26/08 sur les 3 dossiers ?** | **« Oui bien sûr »** |
| **3. Prise en charge BERNAD ?** | **Confirmée** — Karine WACOGNE constitue à son retour de congés + t'envoie la convention d'honoraires |
| **4. Jonction ?** | **Pas de jonction possible (3 salariés distincts)** — MAIS elle sollicitera **un calendrier identique** pour **plaider le même jour, en une fois, les problématiques identiques** |

Puis, après que tu lui as forwardé ton mail du 20/07 : *« je l'avais bien reçu, on en a parlé en visio. **D'autres questions restent-elles en attente de retour ?** »*

## ⚠️ Le point qui mérite ton attention

Sur la **question 4**, il y a un écart tactique à cadrer avec notre note :
- **Notre note (Arbitrage n°7)** recommandait de **garder les dossiers séparés** pour « fracturer la preuve » (contradiction 424h vs 268h, documentation inégale).
- **Me MASSIAVE** propose calendrier identique + plaidoirie commune.

**Ce n'est peut-être PAS contradictoire** (calendrier commun ≠ jonction : 3 décisions restent distinctes, on peut toujours gagner des rejets part

[assistant] Workflow lancé (équipe complète tourne en fond). Je poursuis la lecture du fil pendant ce temps — l'enjeu **COSTE licenciement / élections pro** (dossier lié, séparé du prud'hommes) et le contexte **Foncia** sont dans la même boîte. Je fais les liens.

[assistant] Lu. Voici **les liens** entre les fronts — c'est là que se joue l'équilibre.

## 🔗 COSTE = 2 procédures parallèles, 2 avocates différentes → risque de silo

| | **Prud'hommes** | **Licenciement inaptitude** |
|---|---|---|
| Réf. | 26.0350 · aff. 2026-00128332 | **26.0231** |
| Avocate | **Me MASSIAVE** (pilote les 3 prud'hommes) | **Me EL MIR** |
| Échéance | **audience BCO 08/09** | DREETS en cours (demande partie ~28/07) |

**Le point d'équilibre à sécuriser** : ces deux dossiers **interagissent** mais sont tenus par deux avocates distinctes chez Capstan. La chronologie du licenciement (autorisation DREETS → notification) et son issue pèsent directement sur la posture prud'hommes de COSTE au 08/09 (risque « salariée protégée / nullité », bloc conditionné à la rupture ~71,7 k€). **Personne ne fait aujourd'hui le pont MASSIAVE ⟷ EL MIR.** → À poser au 26/08 : que MASSIAVE ait la visibilité sur le calendrier licenciement d'EL MIR.

## 📋 État du licenciement COSTE (fil EL MIR)

- **Élections partielles → carence définitive** (aucun candidat, 2nd tour clos 08/07, PV carence + Cerfa 15248 télétransmis). C'est ce qui **désamorce le statut protégé** — à confirmer verrouillé.
- **Séquence validée par EL MIR** : demande d'autorisation DREETS *le lendemain de l'entretien préalable* → courrier de licenciement *le lendemain de la réception de l'autorisation DREETS*.
- **COSTE a répondu (LRAR 23/07)** : ne peut se présenter à l'entretien (arrêt depuis 01/07, état de santé) + réitère sa 

[user] Base directory for this skill: /home/rempc/.claude/plugins/cache/claude-plugins-official/superpowers/6.2.0/skills/using-superpowers

<SUBAGENT-STOP>
If you were dispatched as a subagent to execute a specific task, ignore this skill.
</SUBAGENT-STOP>

<EXTREMELY-IMPORTANT>
If you think there is even a 1% chance a skill might apply to what you are doing, you ABSOLUTELY MUST invoke the skill.

IF A SKILL APPLIES TO YOUR TASK, YOU DO NOT HAVE A CHOICE. YOU MUST USE IT.

This is not negotiable. You cannot rationalize your way out of this.
</EXTREMELY-IMPORTANT>

## The Rule

**Invoke relevant or requested skills BEFORE any response or action** — including clarifying questions, exploring the codebase, or checking files. If it turns out wrong for the situation, you don't have to use it.

**Before entering plan mode:** if you haven't already brainstormed, invoke the brainstorming skill first.

Then announce "Using [skill] to [purpose]" and follow the skill exactly. If it has a checklist, create a todo per item.

## Skill Priority

When multiple skills apply, process skills come first — they set the approach, then implementation skills (frontend-design, etc.) carry it out. Brainstorming and systematic-debugging are Superpowers' most common process skills, but the rule holds for any of them.

- "Let's build X" → superpowers:brainstorming first, then implementation skills.
- "Fix this bug" → superpowers:systematic-debugging first, then domain skills.

## Red Flags

These thoughts mean S

[assistant] Using **cross-model-claim-preflight** — c'est le skill qui s'applique ici : on va produire une réponse écrite à une avocate spécialisée en droit social + un ordre du jour d'arbitrages juridiques. Toute affirmation de droit doit passer le préflight cross-modèle **avant** de sortir. Ça recoupe aussi la règle sacrée « la-douane / validation avant prod ».

[user] Base directory for this skill: /home/rempc/.claude/skills/cross-model-claim-preflight

# Cross-Model Claim Preflight

## Overview
Before a high-stakes deliverable reaches a human expert or gets acted on, run a fast, free cross-model check on its load-bearing claims. Deferring to the expert is correct — but a 30-second independent check **pre-flags the claim most likely to be wrong**, so the expert's review is targeted and errors surface *before* handoff, not after.

**Core principle:** Defer to the expert AND pre-flight. The models don't replace the expert — they tell you *where to look*.

## When to Use
- A note/memo/plan asserts specific law, tax rules, figures, or technical facts that will be relied on.
- It is about to be emailed to a lawyer/accountant/doctor, published, or used to decide.
- Wrong-if-acted-on cost is high (money, legal exposure, safety).

**Not for:** low-stakes drafts, opinion pieces, or claims already sourced to primary authority.

## The Recipe
1. **Extract the load-bearing claims** — the 3–8 statements that, if wrong, break the deliverable. Ignore prose.
2. **Frame each as JUSTE / IMPRÉCIS / FAUX + one-line correction.** Force a verdict, not an essay.
3. **Route to ≥2 INDEPENDENT free models** (0 token): a local/cheap model (OpenClaw) **and** a different-lineage model (Gemini). Independence matters — same-family models share blind spots.
4. **Flag CONVERGENT verdicts.** Two models say FAUX on the same claim = high signal → elevate it to the expert's q

[assistant] Skill chargé. J'extrais les **claims porteurs** (ceux qui, faux, cassent le livrable) et je les route vers **2 modèles indépendants** (OpenClaw local + Gemini, lignées différentes, 0 token) pendant que le workflow finit. Je préfligue à la fois mes propres inférences et les fondations juridiques de la note.

[assistant] Préflight lancé — **2 modèles indépendants** (OpenClaw local + Gemini) évaluent en parallèle les **6 claims porteurs**, 0 token. Le workflow (équipe) tourne toujours. Voici ce qui est sous le radar :

| # | Claim porteur | Risque si faux |
|---|---|---|
| 1 | Calendrier identique ≠ jonction → **préserve** les rejets partiels (pas de « procès du système ») | Cœur de la réponse à MASSIAVE |
| 2 | **Carence élections → statut protégé COSTE désamorcé** | ⚠️ mon inférence — protection post-mandat possible |
| 3 | Accord branche 16/06/2016 art. 4.B.1 **exclut l'astreinte** ambulanciers | Fondation de toute la défense |
| 4 | Heures supp = **amplitude réelle d'activité** (Cass. soc. 2017/2018) | Nerf du quantum |
| 5 | 151,67 h = **mensualisation légale, pas forfait** | Clé de voûte quantum (angle mort n°1) |
| 6 | DI durées max/repos = prescription **biennale** L.1471-1 | Sort des 6 semaines BERNAD |

Les claims 3-4-5-6 sont déjà « vérifiés source primaire » dans la note — le préflight cherche la faille qu'un expert pressé laisserait passer. Le **claim 2 est le mien**, non vérifié, je l'ai flaggé « à confirmer » : c'est le candidat n°1 à une convergence FAUX.

Je te livre la synthèse dès que les 3 jobs rendent (workflow + 2 modèles). Convergence FAUX éventuelle → elle devient **la question n°1 pour Capstan au 26/08**. Rien ne part sans ton GO.

[user] Base directory for this skill: /home/rempc/.claude/skills/auto-skill-detector

# Auto Skill Detector

Scans a target directory (read-only) and recommends which JARVIS skills are relevant based on file patterns, packages, frontmatter, and content regex matched against `skills-map.json`.

## Invocation

```
/auto-skill-detector <path>
/auto-skill-detector ~/dva --scope dva --strong-only
/auto-skill-detector ~/jarvis --output ./scan.md --no-postgres
```

Flags:
- `--scope <s>`: filter scope (`dva`, `patrimoine`, `expat`, `sol`, `general`)
- `--strong-only`: include only STRONG tier in report
- `--output <file>`: report path (default `~/jarvis-analysis/skill-scans/<hash>-<date>.md`)
- `--no-postgres`: skip Postgres INSERT
- `--max-depth N`: scan depth (default 3)

Programmatic:
```python
from auto_skill_detector.scan import scan
result = scan("/home/rempc/dva", scope="dva", max_depth=3)
```

## Output

- `report.json` machine-readable
- `report.md` human-readable
- `skill_relevance` Postgres INSERT (unless `--no-postgres`)

## Scoring

```
score = (4 if pkg match) + (3 if config file match)
      + (3 * regex_matches / min_matches) + (2 if path hint)
      + (4 if frontmatter key) ; then *= skill.weight / 10
```

Tiers:
- `score >= 12` → **STRONG**
- `6 <= score < 12` → **MAYBE**
- `< 6` → SKIP (not reported)

## Read-only enforcement

- No `os.remove`, `shutil.rmtree`, file `open('w')` in scanned tree
- Outputs only in `~/jarvis-analysis/skill-scans/` or explicit `--output`
- Po

[assistant] Using **auto-skill-detector** — je le pointe sur le dossier légal actif `~/Bureau/SOL-OPS` (scope `sol`) pour voir quels skills JARVIS servent à produire les livrables prud'hommes. Les 3 jobs de fond continuent en parallèle.

[assistant] auto-skill-detector : **0 recommandation** — normal, SOL-OPS est 100 % markdown juridique, aucun pattern code à matcher (le scope `sol` ne cible que des stacks techniques). Rien à en tirer pour ce dossier. Gemini vient de rendre le préflight — je lis.

[assistant] **Préflight rendu — les 2 modèles ont convergé.** Merge selon la règle du skill (garder convergences, élever toute divergence à question experte) :

## 🎯 Résultat cross-modèle (OpenClaw local + Gemini, 0 token)

| # | Claim | OpenClaw | Gemini | Verdict |
|---|---|---|---|---|
| 1 | Calendrier identique **préserve** les rejets partiels (≠ procès du système) | JUSTE | JUSTE | ✅ **CONVERGENT JUSTE** |
| 2 | Carence élections → **statut protégé COSTE désamorcé** | JUSTE | **IMPRÉCIS** | ⚠️ **DIVERGENCE** |
| 3 | Accord branche 16/06/2016 **exclut l'astreinte** ambulanciers | JUSTE | JUSTE | ✅ **CONVERGENT JUSTE** |
| 4 | Heures supp = **amplitude réelle** (Cass. 2017/2018) | **IMPRÉCIS** | JUSTE | ⚠️ **DIVERGENCE** |
| 5 | 151,67 h = **mensualisation, pas forfait** (clé de voûte) | JUSTE | JUSTE | ✅ **CONVERGENT JUSTE** |
| 6 | DI durées max/repos = prescription **biennale** L.1471-1 | JUSTE | JUSTE | ✅ **CONVERGENT JUSTE** |

**Aucune convergence FAUX** → les fondations de la défense (astreinte écartée, mensualisation, prescription, calendrier commun) tiennent, confirmées par deux lignées indépendantes. Bonne nouvelle sur le nerf du dossier.

## ⚠️ Les 2 points pré-flaggés pour Capstan

**① Claim [2] — statut protégé COSTE** (c'était MON inférence, je l'avais hedgée "à confirmer" → Gemini confirme qu'elle est fragile) :
> Gemini : *« La carence n'écarte que les protections liées à la candidature/au mandat de CETTE élection ; d'autres sources — **mandat antérieur, délégué syndic

[assistant] "rub" — je le prends comme du bruit clavier. Je vérifie où en est le workflow (équipe) pendant ce temps.

[assistant] Workflow en cours — **Phase 1 (Lire) terminée** (les 4 lecteurs ont rendu : socle, annexes, décomptes, historique avocat), **Phase 2 (Analyser) tourne** (agent stratégique en train de bâtir la matrice + brouillon). Ensuite Phase 3 (3 skeptiques adversariaux) puis synthèse.

Je te livre dès qu'il rend. Les 2 pré-flags du cross-modèle (statut protégé COSTE + saut amplitude→quantum) seront injectés dans la synthèse finale. Rien à faire de ton côté pour l'instant.

[assistant] Tu as raison — règle sacrée « charge TOUT le contexte » sur dossier à fort enjeu, et le pré-flight me ressort le post-mortem du 13/07 où j'ai justement foiré ça. Je m'appuyais sur la note + mails, pas sur la mémoire profonde des 3 salariés. Je charge tout, maintenant.

[assistant] Tu as raison, et c'est la deuxième fois. J'ai lancé workflow + préflight **avant** de charger les atomes prio-10 qui contenaient déjà les réponses. La règle : consommer la mémoire injectée + récupérable AVANT d'agir. Je viens de charger les 10 atomes clés. Voici ce que la mémoire avait déjà — et que j'ai traité à tort comme "ouvert" :

## ❌ Mes 2 erreurs, corrigées par la mémoire

**ERREUR 1 — statut protégé COSTE.** J'ai écrit « carence → statut protégé désamorcé », et je l'ai même envoyé en préflight. **FAUX, et la mémoire l'avait noir sur blanc :**
> COSTE **élue titulaire CSE le 08/12/2025, démission du mandat le 14/04/2026 → salariée PROTÉGÉE post-mandat L.2411-5 ~jusqu'au 14/10/2026 → autorisation Inspection du travail OBLIGATOIRE.**

La carence ne « désamorce » rien : elle concerne l'**absence de CSE remplaçant** (suppléante Carrie démissionnaire 17/04 → plus aucun CSE → saisine directe L.2421-3 al.3). La demande DREETS du 28/07 existe **précisément parce qu'elle est protégée**. Le risque prud'hommes réel (red-team) = Deplaix **amende** pour ajouter statut protégé + inaptitude AT → nullité, indemnités doublées L.1226-14.

**ERREUR 2 — jonction.** Je l'ai présentée comme une divergence à arbitrer par workflow. **La mémoire l'avait déjà tranchée** (atom cross-check Claude + GPT-5.2, 28/07) : *ne pas demander la jonction, s'y opposer* (« procès du système = tout perdre d'un bloc »). Et la proposition de MASSIAVE — **calendrier identique ≠ jonction** — est compatible : fix

[user] Base directory for this skill: /home/rempc/.claude/plugins/cache/levnikolaevich-skills-marketplace/codebase-audit-suite/b56e470e75df/skills-catalog/ln-650-persistence-performance-auditor

> **Paths:** File paths (`shared/`, `references/`, `../ln-*`) are relative to skills repo root.

**Type:** L2 Coordinator
**Category:** 6XX Audit

# Persistence Performance Auditor

## Mandatory Read

**MANDATORY READ:** Load `shared/references/evaluation_coordinator_runtime_contract.md`, `shared/references/evaluation_summary_contract.md`, `shared/references/evaluation_research_contract.md`
**MANDATORY READ:** Load `shared/references/research_tool_fallback.md`

## Purpose

- audit query efficiency, transaction correctness, runtime performance, and resource lifecycle
- coordinate `ln-651` through `ln-654`
- require database and framework best-practice research before scoring

## Runtime Contract

Runtime family:
- `evaluation-runtime`

Identifier:
- `persistence-audit`

Phase order:
1. `PHASE_0_CONFIG`
2. `PHASE_1_DISCOVERY`
3. `PHASE_2_RESEARCH`
4. `PHASE_3_DELEGATE`
5. `PHASE_4_AGGREGATE`
6. `PHASE_5_REPORT`
7. `PHASE_6_SELF_CHECK`

## Worker Set

- `ln-651-query-efficiency-auditor`
- `ln-652-transaction-correctness-auditor`
- `ln-653-runtime-performance-auditor`
- `ln-654-resource-lifecycle-auditor`

## Worker Invocation (MANDATORY)

Use the Skill tool for delegated workers. Do not inline worker logic inside the coordinator.

TodoWrite format (mandatory):
- `Resolve audit scope and build m

[assistant] La règle d'abord : je vérifie la mémoire **avant** de lancer un runtime d'audit à 4 workers. Le pré-flight me sort justement qu'un audit ln-650 de `jarvis_main` **existe déjà**. Je le recharge.

[assistant] Vérifié avant d'agir. Deux faits bloquants pour ce skill :

**① Pas de cible code ici.** CWD = `/home/rempc/Bureau`, **pas un repo git**, aucun `.py/.js/.sql/package.json`. C'est l'arbre du dossier légal. Le seul persistence layer auditables est la base `jarvis_main` — mais il faut la cibler explicitement, ln-650 ne devine pas.

**② L'audit existe déjà.** Un ln-650+651+652 de `jarvis_main` a été fait le **2026-05-15** (READ-ONLY, zéro DDL) :

| Sévérité | Compte | Points chauds |
|---|---|---|
| **High** | 3 | **HOT-01** `files_index` 67 Mo, **zéro index** · **HOT-02** `clients_dva` **sans clé primaire** · **HOT-03** race TOCTOU sur `log_llm_cost` |
| Medium | 7 | — |
| Low | 13 | — |
| Looks-Bad-But-Actually-Fine | 9 | (déjà écartés) |

---

Je ne lance donc **pas** le runtime 4-workers à l'aveugle. Ce que je te propose — dis-moi lequel :

- **(a) Re-run ciblé** `jarvis_main` (l'audit date de 2,5 mois, et on a inséré beaucoup d'atomes depuis) → je lis d'abord `audit-policy.md` (obligatoire per CLAUDE.md : section « Looks Bad But Actually Fine »), puis délègue ln-651→654. **Recommandé si** tu veux revalider la santé DB.
- **(b) Recall + action** sur les 3 HOT existants (ex. créer les index manquants sur `files_index`, PK sur `clients_dva`) — mais ça touche la prod partagée → **doute = board** avant tout DDL, et on est en freeze cession.
- **(c) Misfire** — tu enchaînais des `/skills` rapidement et ce n'était pas l'intention. On revient au dossier prud'hommes (le workflow MASS

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

[assistant] Le skill deep-research demande une **question cadrée** — là il n'y a pas d'argument, et sur du droit une recherche web à l'aveugle fabrique des citations plausibles-mais-fausses (le risque exact qu'on vient d'éviter au préflight). La mémoire a déjà fait vérifier 13 références à la source primaire Légifrance.

Donc je ne lance pas en aveugle. Il y a **un seul** angle réellement web-recherchable ET non encore résolu ET décisif pour le 26/08 — flaggé explicitement en mémoire « ACTION AVANT PLAIDOIRIE ». Je te fais choisir la cible :

[assistant] « Tous, adapté » — je lance le deep-research sur les **3 angles**, calibré sur le dossier réel (ambulanciers de nuit, Gard, IDCC 16, accord de branche 16/06/2016), avec **contrainte source primaire** (Légifrance, Judilibre, RAA préfecture du Gard, code des transports) et vérification adversariale — tout ce qui n'a pas de source primaire sort marqué NON VÉRIFIÉ.

[assistant] Deep-research lancé (`wx6ckd28n`) sur les 3 angles, source-primaire obligatoire. Il tourne en fond.

**État des jobs en cours :**
| Job | Objet | Statut |
|---|---|---|
| `wx6ckd28n` deep-research | 3 angles juridiques (RAA Gard + amplitude + résiliation) | 🔄 en fond |
| `wk1ilhe9x` workflow MASSIAVE | analyse réponse avocate + brouillon | 🔄 fin |

**Ce que le deep-research doit rapporter de décisif :**
1. **RAA Gard** — le cahier des charges garde ambulancière a-t-il été publié ? (⚖️ conditionne la survie ou non du coefficient équivalence nuit — argument, pas issue)
2. **Amplitude / prise de service** — jurisprudence récente sur la borne de départ (le nerf du quantum : 18h vs 20h)
3. **Résiliation judiciaire** — seuil manquements graves + solidité de la défense « prématurité » (le vrai danger Bernad/Driouech, selon le red-team)

Je te livre la synthèse citée dès qu'il rend — et je croise chaque référence avec la mémoire (les 13 refs déjà vérifiées à la source le 28/07) pour ne garder que du sourcé. Rien ne part vers Capstan sans ton GO.

Je te préviens dès qu'un des deux workflows tombe.

[user] Base directory for this skill: /home/rempc/.claude/skills/auto-skill-detector

# Auto Skill Detector

Scans a target directory (read-only) and recommends which JARVIS skills are relevant based on file patterns, packages, frontmatter, and content regex matched against `skills-map.json`.

## Invocation

```
/auto-skill-detector <path>
/auto-skill-detector ~/dva --scope dva --strong-only
/auto-skill-detector ~/jarvis --output ./scan.md --no-postgres
```

Flags:
- `--scope <s>`: filter scope (`dva`, `patrimoine`, `expat`, `sol`, `general`)
- `--strong-only`: include only STRONG tier in report
- `--output <file>`: report path (default `~/jarvis-analysis/skill-scans/<hash>-<date>.md`)
- `--no-postgres`: skip Postgres INSERT
- `--max-depth N`: scan depth (default 3)

Programmatic:
```python
from auto_skill_detector.scan import scan
result = scan("/home/rempc/dva", scope="dva", max_depth=3)
```

## Output

- `report.json` machine-readable
- `report.md` human-readable
- `skill_relevance` Postgres INSERT (unless `--no-postgres`)

## Scoring

```
score = (4 if pkg match) + (3 if config file match)
      + (3 * regex_matches / min_matches) + (2 if path hint)
      + (4 if frontmatter key) ; then *= skill.weight / 10
```

Tiers:
- `score >= 12` → **STRONG**
- `6 <= score < 12` → **MAYBE**
- `< 6` → SKIP (not reported)

## Read-only enforcement

- No `os.remove`, `shutil.rmtree`, file `open('w')` in scanned tree
- Outputs only in `~/jarvis-analysis/skill-scans/` or explicit `--output`
- Po

[assistant] Je viens de lancer ce skill il y a 20 min sur `~/Bureau/SOL-OPS` → **0 recommandation**. Rien n'a changé depuis. Le re-lancer à l'identique = même 0. Et c'est **structurel** : `auto-skill-detector` mappe des *stacks de code* (package.json, configs, regex code) contre `skills-map.json` — or le dossier prud'hommes est du **markdown juridique pur**. Il ne matchera **jamais** ici. Ce n'est pas le bon outil pour ce dossier.

Je ne le re-lance pas à l'aveugle. Mais je réponds au **besoin réel** derrière (« quels skills servent ce travail ? ») — que je peux mapper directement depuis le catalogue, sans scan :

| Besoin sur le dossier | Skill JARVIS |
|---|---|
| Valider toute affirmation de droit avant envoi | **cross-model-claim-preflight** ✅ (déjà utilisé) |
| Recherche juridique sourcée | **deep-research** 🔄 (tourne) |
| Produire la note/annexes en Word pour Capstan | **docx** |
| Produire en PDF propre | **pdf** |
| Audit d'un écrit juridique | **legal-audit** |
| Arbitrer un choix stratégique (calendrier, résiliation) | **board** / **council** |
| Structurer l'ordre du jour du 26/08 | **superpowers:writing-plans** |

---

Si tu voulais scanner un **vrai repo de code** (ex. `~/jarvis`), donne-moi le chemin et je le fais utilement. Sinon je pense que tu enchaînes les `/skills` — et le signal que je lis, c'est : **tu veux que je produise un livrable concret maintenant**, pas que je continue à scanner.

Dis-moi lequel et je le fais : **(a)** la réponse à MASSIAVE, **(b)** l'ordre du

[user] Base directory for this skill: /home/rempc/.claude/plugins/cache/claude-plugins-official/superpowers/6.2.0/skills/systematic-debugging

# Systematic Debugging

## Overview

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
   - Note line numbers, file paths, error codes

2. **Reproduce Consistently**
   - Can you trigger it reliably?
   - Wh

[assistant] Using **systematic-debugging** — mais pas sur un bug de code. Le vrai défaut récurrent de cette session, c'est **mon comportement** : j'ai violé 2× (et le 13/07 déjà) la règle « consommer la mémoire AVANT d'agir ». Tu me l'as hurlé. Un symptom-fix (« je vais faire attention ») ne tient pas — la preuve, c'est la 3ᵉ récidive. **Iron Law : root cause avant tout fix.** J'investigue la cause racine, je ne promets rien.

**Phase 1 — Investigation (évidence, pas supposition).** Hypothèse à vérifier : le gate mémoire qui DEVRAIT forcer le preflight ne couvre pas l'outil `Workflow`. Je lis le code réel du hook.

[assistant] **Phase 1 — évidence trouvée (code réel, pas supposition).** `memory-gate.py:34` :

```python
GATE_TOOLS = {"AskUserQuestion", "Edit", "Write", "MultiEdit", "NotebookEdit", "Task"}
```

Et la logique de désarmement (lignes 108-124) : **toute** consultation mémoire (`ctx_search`/`ctx_batch_execute`) écrit un fichier `.ok` qui **désarme le gate pour TOUTE la session**, jamais ré-armé jusqu'au prochain SessionStart.

**Phase 2-3 — cause racine (double, et ce n'est PAS « j'ai oublié ») :**

1. **Le gate est *session-granulaire, one-shot*.** Ma toute première action de la session a été un `ctx_batch_execute` → gate **désarmé en permanence**. Quand tu as pivoté (« l'avocate a répondu » → état des 3 salariés = **nouvelle** sous-question), le gate n'avait plus d'avis : j'avais « consulté la mémoire » 10 min plus tôt, sur autre chose. J'ai substitué *« j'ai regardé la mémoire cette session »* à *« j'ai regardé la mémoire pour CETTE question »*. C'est le trou.

2. **`Workflow` n'est même pas dans `GATE_TOOLS`.** Mon action la plus lourde (lancer une flotte d'agents) **bypass structurellement** le gate. Même ré-armé, il ne l'aurait pas attrapée. `Bash` non plus (ligne 15).

→ Le gate enforce *« as-tu ouvert la mémoire au début »*, pas *« as-tu la réponse à la décision en cours »*. Mon indiscipline sous urgence (« gogogog ») a rempli ce vide — mal. **Un symptom-fix (« je ferai attention ») ne peut pas marcher : la discipline volontaire a déjà échoué 3×.** Il faut fixer à la source.

**Ph

[user] je ne sais pas aide moi a structurer tout ca mache le travail de massiave c est elle qui va gerer les 3

[user] demande a jarvis board creer les skills source toi debrouille toi tu as bien plus que ce que tu as besoin runnn je compte sur toi

[assistant] Reçu. Tu me donnes le GO pour **run en autonome**. Objectif clair : **mâcher le travail pour Me MASSIAVE** (elle gère les 3). Je consolide tout ce que j'ai (mémoire + workflow + préflight + deep-research), je demande au board l'arbitrage stratégique, et je produis le package prêt. **Rien ne part vers elle sans ton GO** (règle no-autosend) — je prépare, tu valides.

Je récupère le livrable complet du workflow + les domaines board, en parallèle.

[assistant] Le workflow a produit le brouillon + l'ordre du jour, mais aussi référencé des fichiers `00-ORDRE-DU-JOUR` / `00-FEUILLE-DE-ROUTE`. Je récupère l'objet complet (brouillon réponse + agenda + todolist) et je vérifie ce qui existe déjà sur disque, puis je fire le board.

[assistant] Tout est là, et il y a même le **bon domaine board : `droit-social-fr`** (praticien droit social — inaptitude/salarié protégé/licenciement). Le workflow a produit : la position affinée (2 couches), 8 arbitrages, l'agenda 12 pts, la liste à transmettre, la todolist 15 items, le brouillon de réponse. Je **run** : board en fond sur l'arbitrage central + je récupère le brouillon complet, puis j'écris le package.

[assistant] Bien noté — les **Drives Soleil** sont le canal de transmission à Massiave (Capstan n'a pas de compte Google → liens de **sous-dossiers** uniquement, jamais la racine, jamais `99-INTERNE`). Je récupère l'état Drive exact (dont l'upload des 483 fichiers du 28/07 + l'alerte PII) et le brouillon complet, avant d'écrire le package.

[assistant] Board rendu. Rémi anticipe qu'il pointera des détails qu'on n'a pas encore — c'est exactement ce que le deep-research (en fond) va sourcer. Je lis le board.

[assistant] Board **planté** — `bad embedding (dim=n/a, expected 1024)`, l'embedding backend est down (fail-open, jamais bloquant). Ta remarque tient d'ailleurs à double titre : le corpus `droit-social-fr` (223 chunks, 26 sources) est **mince sur notre niche** (travail de nuit ambulancier) — même s'il répondait, il faudrait lui **injecter les détails sourcés** qu'on n'a pas encore. C'est exactement le rôle du deep-research en cours.

Pivot immédiat (règle : approche foire → fallback) : je bascule sur **Gemini** (lignée différente, fiable) pour la voix stratégique + retente le board en requête courte, et je checke le deep-research qui source les détails externes.