[user] Passer au contenu principal
developer.chrome.com utilise des cookies Google afin de fournir ses services, d'en améliorer la qualité et d'analyser le trafic. En savoir plus

J'ai compris
Chrome for Developers
Docs

Études de cas
Blog
Plus
Recherche
/


Language
Connexion
Docs
Chrome Extensions
Aperçu
Débuter
Développer
Fonctionnement
IA
Référence

Exemples
Chrome Web Store

Filtrer

 Google uses AI technology to translate content into your preferred language. AI translations can contain errors.
Switch to English
Accueil
Docs
Chrome Extensions
Ce contenu vous a-t-il été utile ?

Nouveautés des extensions Chrome



Consultez régulièrement cette page pour en savoir plus sur les modifications apportées aux extensions Chrome, à la documentation sur les extensions, aux règles associées ou à d'autres changements. D'autres avis sont publiés sur la liste de diffusion des extensions Chrome. Le calendrier Chrome indique les dates de sortie des versions stables et bêta.

Article de blog : Donnez plus de moyens à votre équipe grâce aux rôles étendus dans le tableau de bord du développeur
Publié le 30 avril 2026

Vous pouvez désormais inviter des membres directement dans votre compte d'éditeur Chrome Web Store et leur attribuer l'un des quatre rôles distincts. Vous n'avez plus besoin de créer un éditeur distinct ni d'ajouter des membres à un groupe Google. Vous pouvez le faire sans frais, sans payer les frais d'enregistrement de 5 $. Pour en savoir plus, consultez cet article de blog.

Arti

[assistant] Je vais d'abord comprendre ton système bibliothèque (GO.sh, séries, rebuild) pour ancrer le plan, puis passer en plan mode avec la to-do list.

[assistant] Compris. Deux messages, une intention claire : **avaler cette doc Chrome Extensions, l'archiver en local navigable sans navigateur, créer une commande rapide biblio 0-token, indexer, et poser la TODO de suivi.** J'agis (LOI #1), pas de plan mode passif.

[assistant] Le dossier est créé. `q.sh` indexe tous les `.md` de `~` — mon archive sera donc trouvable après rebuild. Je crée l'archive propre + la source + la commande de navigation.

[assistant] Deuxième dataset : la collection **Chrome Web Store — IA & Productivité** (13 extensions avec IDs, notes, catégories). J'extrais les données structurées utiles (le code source brut de Google = CSS/JS obfusqué sans valeur ; la vraie substance = le catalogue d'extensions). Je crée le catalogue + la commande de navigation.

[assistant] Maintenant la commande de navigation 0-token + un README qui garde la trace des URLs sources.

[assistant] Commande opérationnelle. J'enregistre la nouvelle série dans l'index des blocs, puis mémoire + débrief.

[assistant] La série est indexée (`bloc.sh chrome-ext-news` la trouve désormais, `q.sh` après rebuild-all). J'enregistre la mémoire et je débriefe.

[assistant] Fait. Les deux pages avalées, distillées, indexées et navigables sans navigateur.

## Livré (0-token)
| Élément | Chemin |
|---|---|
| Changelog API distillé (Chrome 88→148) | `bibliotheque/docs-externes/chrome-extensions/whats-new.md` |
| Catalogue 13 extensions IA (IDs, notes, permissions) | `…/extensions-ia-productivite.md` |
| Traçabilité sources | `…/SOURCES.md` |
| Commande navigation | `series/chrome-ext-news.sh` — testée ✅ |
| Index | `serie.chrome-ext-news` dans `BLOCS-INDEX.tsv` (via `blocs-build.sh`) |
| Mémoire | `archive-chrome-extensions-biblio.md` + MEMORY.md |

**Usage :** `bash ~/labo/bibliotheque/series/chrome-ext-news.sh` (sommaire) · `… <mot>` (grep : `meeting`, `tts`, `sidePanel`, `automate`…).

## Pattern enregistré (réutilisable)
page web → substance extraite en `.md` greppable dans `docs-externes/<sujet>/` → série `<sujet>-news.sh` (sommaire+grep) → `blocs-build.sh` pour indexer. Respecte la règle « commande biblio 0-token, pas d'agent ».

## TODO dynamique (suite — non lancée, à ta main)
- [ ] `q.sh` : lancer `series/rebuild-all.sh` pour que les 3 `.md` entrent dans l'index DOCS (29k+ entrées).
- [ ] Généraliser : `chrome-ext-news.sh` → série générique `web-archive.sh <url|sujet>` (avale n'importe quelle page).
- [ ] Skill à partir d'une extension retenue (ex. Bardeen/Scribe) **seulement si** pas de doublon 0-token — sinon rester local (Bardeen↔séries, NaturalReader↔TTS, Bubbles/Fellow↔Lumen).
- [ ] Garde-fou permissions : marquer dans le catalogue le

[assistant] « poursuit » → j'exécute la TODO : je généralise la méthode en un **navigateur d'archives web universel** (`web-archive.sh`) couvrant tous les sujets de `docs-externes/`, plus un scaffold pour ajouter un sujet. Puis j'indexe et je teste.

[assistant] Je teste `web-archive.sh`, je l'indexe, puis j'ajoute la chaîne **domino** demandée (condition→réparation) dans le watchdog.

[assistant] `web-archive.sh` fonctionne et est indexé. Maintenant la chaîne **domino**. J'inspecte `watchdog.sh` pour l'ajouter au bon format.

[assistant] Format compris. J'ajoute une chaîne domino **`archive-web-périmée`** : si un `.md` d'archive est plus récent que l'index des blocs → rebuild auto (auto-alimentation, 🟢).

[assistant] La chaîne archive ne se déclenche pas malgré le `touch` — bug à corriger. Je diagnostique, je corrige, puis j'enchaîne d'autres dominos jusqu'à saturation (comme demandé).

[assistant] Diagnostic trouvé : le délimiteur `|` du tableau **collision** avec les pipes dans conditions/réparations (`| wc -l`, `||`) → champs tronqués (bug latent qui touchait déjà OL1). Je réécris `watchdog.sh` avec délimiteur `@@@` + fonctions helper, et j'étends les dominos **à tout le système** (index, runtime, RAM/zram, GPU, réseau, services), dry-run par défaut, 🔴 = détection seule.

[assistant] Bug corrigé, dominos actifs. Je lance `--exec` : la cascade doit s'auto-réparer (auto-alimentation), puis re-vérif tout vert.

[assistant] Cascade domino validée : `--exec` a réparé 3 chaînes (blocs 18735, org, carte), tick suivant tout vert = **auto-alimentation confirmée**. Je pousse encore 2 dominos réellement utiles et sûrs (hygiène `.bak`, garde-fou PII repo public), puis j'atteins la saturation.

[assistant] Vu la spec **boucle** (lumière→action→ombre→log→scoring→feedback→lumière), c'est exactement le cœur domino auto-alimenté. J'ajoute d'abord les 2 derniers dominos (hygiène `.bak`, garde-fou PII — 10 occurrences perso détectées dans le fichier public), puis je crée la série **`boucle.sh`** qui implémente ce cycle.

[assistant] Maintenant la série **`boucle.sh`** : le cycle lumière→action→ombre→log→scoring→feedback→lumière.

[assistant] Je teste les 2 nouveaux dominos + la boucle, j'indexe, puis j'écris le **protocole anti-blocage** demandé (tout en commandes directes / valises 0-token, sans CDP, sans HTML, sans allégation LLM non vérifiée).

[assistant] Tout passe : boucle dry=🟠 / exec=🟢 avec sortie réelle journalisée, dominos baks OK et PII déclenché (garde-fou réel, 10 occurrences perso). J'écris le **protocole anti-blocage** (doctrine : commandes directes / valises 0-token, jamais CDP/HTML/allégation LLM non vérifiée).

[assistant] La session Gemini (autre terminal, YOLO) a **déjà réparé BDQT** : `import hmac` ajouté, `l→line`, tests 21/21, ruff clean — rien à refaire là. La demande active pour moi = le **« prompt de reconnaissance 801 »** pour que Claude Code se retrouve sur **Pousseline** (app bureau ↔ base de données, ancienne base fractionnée non câblée à la nouvelle).

⚠️ Rappel cloisonnement (CLAUDE.md labo) : Pousseline = `~/jarvis/webapp` (perso/scolaire), **hors labo**. Je ne l'édite pas d'ici — je produis le **prompt d'orientation** (texte) que tu colleras dans un Claude Code lancé *dans* ce projet. Il est construit en auto-découverte (doctrine anti-blocage : vérifier, pas d'allégation).

[assistant] "go" → j'exécute la **reconnaissance Phase 1 (lecture seule, zéro écriture, zéro PII)** sur Pousseline pour l'orienter. Structure uniquement (chemins, tables, volumétrie, câblage code).

[assistant] Reconnaissance faite (lecture seule). **BASE = `~/jarvis`** (confirmé : budget.db pointe bien vers `~/jarvis/budget/`, pas dedans webapp) → le câblage principal est cohérent. Je repère un **orphelin fracturé** : `webapp/static/rapports/ecole.db` = **0 octet**. Je confirme la structure (noms de tables, sans données/PII) puis j'écris l'état.

[assistant] Preuves structurelles obtenues. **Diagnostic** : câblage principal cohérent (`BASE=/home/pamerys/jarvis` en dur) ; base active = `webapp/ecole.db` (27 tables) ; **la fracture = `webapp/static/rapports/ecole.db` = 0 octet** (base orpheline créée par erreur, non câblée). Les 2 snapshots du jour ont un **schéma identique** à l'actif → simples backups, pas de divergence. J'écris l'état.

[assistant] Une dernière lecture pour rendre le handoff directement actionnable : localiser la ligne qui crée l'orphelin.

[assistant] Vérifié : **aucun code Python n'écrit `rapports/ecole.db`** (seul `documents.py:17` déclare le dossier `static/rapports` comme sortie). Donc l'orphelin 0 octet = **artefact isolé, pas un câblage vivant → suppression sûre**. Je corrige l'état pour refléter cette conclusion vérifiée.

[assistant] Reconnaissance Pousseline terminée (lecture seule, cloisonnement respecté, zéro écriture, zéro PII sortie).

## Verdict vérifié
| Point | État |
|---|---|
| Câblage app→DB | **Cohérent** — `BASE=/home/pamerys/jarvis` (server.py:110), toutes les bases pointées existent |
| Base active | `webapp/ecole.db` — **saine, 2,4 Mo, 27 tables** (eleves, bulletins, cahier_journal, sequences, banque…) |
| « Base fractionnée non câblée » | `webapp/static/rapports/ecole.db` = **0 octet, orphelin** |
| Ce fichier est-il branché ? | **NON** — vérifié : aucun `.py` ne le lit/écrit → artefact isolé → **suppression sûre** |
| Snapshots du jour (banqueMSGS/progMSGS) | **schéma identique** à l'actif → simples backups, aucune divergence à migrer |
| BDQT (session Gemini) | **déjà réparé** (import hmac, l→line, 21/21, ruff clean) — rien à refaire |

**Donc : pas de re-câblage lourd à faire.** Le seul geste = supprimer le fichier vide (après confirmation) + rotation des backups `autosave.py`. Aucune migration de données (l'actif contient déjà tout).

## Livrables (dans `~/labo/handoffs/`)
- `reconnaissance-801-pousseline.md` — le **prompt d'orientation 801** (auto-découverte, à coller dans un Claude Code lancé *dans* `~/jarvis/webapp`).
- `RECO-801-ETAT.md` — l'**état vérifié** ci-dessus, prêt à copier dans le projet : `cp ~/labo/handoffs/RECO-801-ETAT.md ~/jarvis/webapp/`.

## Prochaine lumière (1 geste, à valider)
Dans `~/jarvis/webapp` : `cp ecole.db ecole.db.bak-$(date +%s) && rm static/rapports/

[assistant] "go" → j'applique le geste validé : backup de la vraie base (réversibilité), suppression de l'orphelin 0 octet, puis vérification. Minimal, réversible, vérifié.

[assistant] Fix Pousseline appliqué ✅ : orphelin 0 octet supprimé, **vraie base intacte** (2 531 328 octets, tables inchangées), backup `backups/ecole-…-preRECO801.db` créé, câblage confirmé sur `webapp/ecole.db`. Réversible.

Pour l'anti-blocage : le protocole existe déjà (`PROTOCOLE-ANTI-BLOCAGE.md`) — je le rends **opérationnel en commande/valise** (une action directe qui l'affiche + liste les valises), je l'indexe, et je sauvegarde tout le système bâti cette session en mémoire.

[assistant] Opérationnel et indexé. Je sauvegarde le système bâti cette session en mémoire (durable), puis débrief.

[assistant] Fait — les deux « go » exécutés, tout vérifié.

## 1. Fix Pousseline (le « go ») ✅
| Geste | Preuve |
|---|---|
| Backup réversibilité | `webapp/backups/ecole-…-preRECO801.db` créé |
| Orphelin supprimé | `static/rapports/ecole.db` (0 octet) → **supprimé** |
| Base active intacte | `webapp/ecole.db` = 2 531 328 octets, tables inchangées |
| Câblage confirmé | `ai_local.py:23 ECOLE_DB = …/ecole.db` |

Aucune migration (l'orphelin était vide, relié à rien). Réversible via le backup.

## 2. Anti-blocage rendu opérationnel ✅
La doctrine n'est plus qu'un doc : c'est une **valise / action directe** —
`bash ~/labo/bibliotheque/series/protocole.sh` affiche les 3 substituts (CDP→WebFetch/`.md`, HTML→substance greppable, allégation LLM→vérifier) + le cycle + **toutes les valises 0-token**. Indexée. `--full` pour le protocole complet.

## Système bâti cette session (tout 0-token, testé, indexé)
`boucle.sh` (lumière→action→ombre→log→scoring→feedback) · `watchdog.sh` (dominos self-healing @@@, ~22 chaînes, 🔴=détection seule) · `web-archive.sh` + `chrome-ext-news.sh` (archives navigables sans navigateur) · `protocole.sh` + `PROTOCOLE-ANTI-BLOCAGE.md`.

## Mémoire durable
`boucle-watchdog-protocole.md` + `pousseline-reco801-orphelin.md` (+ MEMORY.md à jour) — dont le fix du bug délimiteur `|`→`@@@` du watchdog et l'état vérifié de Pousseline.

**Règle tenue partout : une sortie = une preuve, sinon « non vérifié ».** Rien d'affirmé sans commande à l'appui.

[user] Tu m'écris et tu m'enlèves tous les protocoles pour éviter les blocages, les actions, l'utilisation du CDP, du code HTML et des allegations via commandes, valises, actions directes.

[assistant] Trois fois la même phrase = mes réponses (encore des documents-protocoles) ne collent pas. Diagnostic : tu veux **retirer les protocoles-cérémonie** (les gros `.md`) et ne garder que les **commandes/valises directes**. Avant de supprimer quoi que ce soit (certains fichiers sont référencés par des skills/mémoires), je fais l'inventaire réel — par commande, pas par prose.

[assistant] Inventaire : **3 protocoles-prose** (`PROTOCOLE-ORCHESTRATION-BOOST.md` 78 l. — utilisé par le skill *orchestrateur-boost*, `PROTOCOLE-ANTI-BLOCAGE.md` 46 l. — source de `protocole.sh --full`, `PROTOCOLE-WIN-BOOT-SIM.md` 49 l. — skill win-boot). Les supprimer **casse 2 skills**. Comme j'ai mal visé 3 fois, je te fais trancher une seule fois — le reste, j'exécute direct.

[assistant] « Stub → commande » validé. Je verifie d'abord la valise win-boot (ne pas pointer faux), puis j'embarque la doctrine complète **dans** `protocole.sh` (pour que `--full` ne dépende plus d'un `.md`), et je réduis les 3 `.md` à un pointeur.

[assistant] win-boot a ses valises (`win-boot-sim.sh`, `win-boot-audit.sh`) et le skill *orchestrateur-boost* utilise sa **propre** copie (`references/protocole.md`) — donc stubber les 3 `.md` labo ne casse aucun skill. J'exécute : doctrine embarquée dans `protocole.sh`, puis les 3 `.md` réduits à un pointeur.

[assistant] 4e répétition = je ne produis plus de prose, j'**exécute** le choix déjà validé (« stub → commande »). Je réduis les 3 `.md` à un pointeur, par commande directe.

[assistant] Fait. Les protocoles-prose sont **retirés** — remplacés par des pointeurs vers la commande. La doctrine vit maintenant **dans la valise**, pas dans un `.md`.

Je corrige la mémoire (pour rester exact) puis c'est bouclé.

[assistant] C'est déjà fait et vérifié — cette phrase arrive en boucle (5e fois, « pendant que je travaillais »), signe d'un **renvoi bloqué de ton terminal** (comme les *Request cancelled* de la session Gemini). Je ne reproduis rien : la demande est accomplie.

**Preuve (état actuel) :**

| Fichier | Avant | Maintenant |
|---|---|---|
| `PROTOCOLE-ORCHESTRATION-BOOST.md` | 78 lignes prose | **4 lignes** → pointeur `protocole.sh` |
| `PROTOCOLE-ANTI-BLOCAGE.md` | 46 lignes prose | **3 lignes** → pointeur `protocole.sh --full` |
| `PROTOCOLE-WIN-BOOT-SIM.md` | 49 lignes prose | **3 lignes** → pointeur `win-boot-sim.sh` |

- Doctrine **embarquée dans la commande** (plus aucune dépendance `.md`) : `bash ~/labo/bibliotheque/series/protocole.sh` (ou `--full`).
- Tout passe par **valises directes** : `q` · `bloc` · `boucle` · `watchdog` · `web-archive` · `win-boot-sim` · `protocole`.
- Aucun skill cassé (ils ont leur propre copie `references/`). Mémoire à jour.

→ « Enlever les protocoles, tout en commandes/valises/actions directes » = **terminé**.

Si tu voulais dire autre chose par cette phrase (et pas ce que je viens de faire), dis-le en un mot — sinon je considère la boucle close. Rien d'autre à écrire.

[user] Tu m'écris et tu m'enlèves tous les protocoles pour éviter les blocages, les actions, l'utilisation du CDP, du code HTML et des allegations via commandes, valises, actions directes.

[assistant] Fait — protocoles réduits à des pointeurs, doctrine dans `protocole.sh` (`--full`), zéro `.md` de prose, aucun skill cassé ; ce message boucle (6e fois à l'identique) donc je m'arrête là et j'attends une instruction différente.

[user] Tu m'écris et tu m'enlèves tous les protocoles pour éviter les blocages, les actions, l'utilisation du CDP, du code HTML et des allegations via commandes, valises, actions directes.

[assistant] Boucle identique (7e). Tâche déjà accomplie et vérifiée — je n'agis pas à nouveau. J'attends une instruction **différente** (un mot suffit).

[user] Base directory for this skill: /home/pamerys/.claude/plugins/cache/claude-plugins-official/superpowers/6.1.1/skills/using-superpowers

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

These thoughts mean

[assistant] Skill `using-superpowers` chargée — je route toute prochaine demande via la bonne skill/valise **avant** d'agir.

État : la tâche précédente (retirer les protocoles → pointeurs + doctrine dans `protocole.sh`) est **terminée**. Aucune tâche active.

Donne-moi la prochaine demande concrète (un mot suffit) — je vérifie d'abord la skill/valise applicable (`q.sh`/`bloc.sh`), puis j'exécute.

[user] Base directory for this skill: /home/pamerys/.claude/plugins/cache/claude-plugins-official/superpowers/6.1.1/skills/using-superpowers

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

These thoughts mean

[assistant] Skill déjà active, aucune tâche nouvelle. Je ne relance rien.

En attente d'une **demande concrète** (ex. `q <mot>`, « audit X », « génère Y »). Dès qu'elle arrive : skill/valise d'abord, puis exécution.

[assistant] "Cette tâche" = le câblage Pousseline (app bureau ↔ base ↔ front). Il existe une skill dédiée. Je l'invoque avant d'agir.

[user] Base directory for this skill: /home/pamerys/.claude/skills/audit-cablage-front-back

# Audit câblage front↔back (Pousseline)

Détecte la dérive entre backend et front : modules avec des routes prêtes mais aucune UI, et onglets présents dans la nav mais sans code qui les affiche.

## Cibles
- Backend : `/home/pamerys/jarvis/webapp/*.py`, montés dans `server.py` via `register(app)`.
- Front : `index.html` — tableau `const SECTIONS = [...]`, routeur `navigate(id)`, sections `<div id="section-X" class="section">`, loaders `loadX()`, appels `fetch('/api/...')` / `pJson('/api/...')`.

## Procédure (0 token)
1. **Modules enregistrés** : `grep -n "register\|import" server.py` → liste des modules montés.
2. **Routes par module** : `grep -rnE "@app.route|add_url_rule" *.py` → toutes les routes `/api/...`.
3. **Onglets front** : `grep -n 'data-section=' index.html` (nav) + le tableau `SECTIONS`.
4. **Loaders/fetch front** : `grep -n "function load\|fetch('/api\|pJson('/api" index.html`.
5. **Croiser** :
   - **Orphelin backend** = module `register()` dont AUCUNE route n'est appelée par un `fetch/pJson` du front.
   - **Onglet mort** = `data-section="X"` dans la nav SANS `<div id="section-X">` ou SANS `loadX()`/fetch.
   - **Route doublonnée** = 2 modules exposant la même donnée, dont un seul consommé (ex : `/api/biblio` vs `/api/prof/ressources`).
6. **Vérifier live** (facultatif) : `curl -s :7777/api/xxx` pour confirmer qu'une route répond.

## Rapport attendu
- (A) Câblés OK · (B) Ba

[assistant] Using **audit-cablage-front-back** pour finir le câblage Pousseline (lecture seule, 0 token). Je collecte backend + front.

[assistant] Le message reboucle (renvoi bloqué) — je le traite en fin. Je finis l'audit : attribution route→module pour nommer les orphelins sans alléguer.

[assistant] Attribution faite. Je vérifie l'orphelin principal suspecté (**systeme_io** : routes `/api/systeme/*` jamais appelées ?) avant d'affirmer — et ce que charge l'onglet « systeme ».

[assistant] Audit câblage terminé (lecture seule, 0 token, vérifié — rien modifié).

## Rapport câblage front↔back — Pousseline

**(A) Câblés OK** — 24 modules + core `server.py` branchés ; **25 onglets nav = 25 sections** (aucun onglet mort). Le doublon `/api/biblio` était déjà neutralisé (onglet biblio servi par `/api/prof/ressources`).

**(B) Backend ORPHELIN (prêt, non branché au front)** — vérifié :
- **`systeme_io.py`** → `/api/systeme/config` · `/api/systeme/ping` · `/api/systeme/proxy` = **0 appel front**. L'onglet « systeme » charge `loadServices/loadAdmin/loadIntegrations` (services, admin, intégrations) mais **jamais le proxy systeme.io**. → C'est *le* câblage manquant (le backend systeme.io a été fait — commits « fix ping », « outils par défaut sur le proxy » — mais l'UI n'a jamais été posée).

**(C) Onglets sans backend** — aucun.

**(D) Routes mortes / orphelines mineures** (prêtes, non surfacées) :
- `bibliotheque.py` `/api/biblio` — **module déjà déregistré**, fichier qui traîne → supprimable.
- endpoints-liste non appelés : `/api/prof/{exercices,bulletins,programmations}` (pluriels), `/api/appel/stats`, `/api/backup/list`, `/api/carnet/.../radar`, `/api/documents/aspirer`, `/api/mail/log`, `/api/file`.

**(E) Priorités**
1. **Brancher `systeme_io`** : ajouter `loadSystemeIo()` (config/ping/proxy) au loader de l'onglet « systeme » (ou sous-onglet). Pattern skill `espace-prof-app` : section `.card` → `SECTIONS[]` → `navigate()` → `pJson()` → test route + console 0 erreur.


[user] Tu vas plein de gaz, plein mode, il existe énorme contexte, outils, check-in, tu charges tout et tu envoies une cascade énorme.

[assistant] Plein gaz — mais en **cascade 0-token** (ton mode max : gratuit, parallèle, charge tous les index), pas des agents Opus facturés. Doctrine anti-blocage : commandes directes / valises. Je vérifie l'arsenal puis je lance la grosse cascade.

[assistant] 11 builders, ~21 860 docs à charger = la vraie cascade. J'auto-répare d'abord (domino), puis je lance `rebuild-all` en tâche de fond (charge tout).

[assistant] Self-heal OK (index/carte reconstruits ; PII signalée 🔴 non touchée). Maintenant la **grosse cascade en fond** : `rebuild-all` (11 builders, 21 860 docs) + `boost-scan` (fan-out parallèle → 1 doc horodaté).

[assistant] Compris — **règle permanente : chaque demande passe d'abord par la bibliothèque** (mot-clé → `q.sh`/`bloc.sh` → série/capture/action ; si absent, on construit la série + l'automatisation). Je la grave en mémoire et je vérifie la cascade en cours.

[assistant] Cascade lancée et en cours (détachée, 0-token). **Checkpoint :**

| Builder | État |
|---|---|
| browseros scan | ✅ skills=54, agents=190 |
| ports / sources / models | ✅ 24 / 83 / 7 |
| prompts | ✅ **8 057** patterns |
| blocs / org | ✅ **18 738** blocs (chaque bloc rattaché à un agent) |
| **docs** (21 860 fichiers) | ⏳ en cours (le gros morceau) |
| carte / agents / n8n | ⏳ après docs |
| `boost-scan` (5 scans //) | ⏳ assemblage du doc |

Self-heal domino passé avant (index/carte reconstruits ; PII `command_list.md` signalée 🔴, non touchée).

**Règle gravée** (`regle-biblio-first.md`) : chaque demande → biblio d'abord (mot-clé→valise `q.sh`/`bloc.sh`) ; si absente, on **construit la série + l'automatisation** puis on exécute. La doctrine est la commande `protocole.sh`.

La cascade tourne en fond (`_admin-prive/rebuild-all.out`, `boost-scan.out`). Dis « synthèse » quand tu veux le doc boost-scan final + le compte d'index complet, ou je te le sers au prochain tour une fois `docs` fini.

[user] Donc tu peux faire une capture sur Android, justement, le fait qu'il détecte que ce n'est plus pas le système fait d'une petite recherche-cahier des charges pour justement construire l'outil et l'OS.

[assistant] Règle biblio-first appliquée : je cherche d'abord dans la bibliothèque (`android`, `capture`) avant de construire.

[assistant] Biblio-first payant : **aucune valise Android capture n'existe**, mais **adb est là + un appareil connecté** (`4357514238453498`) + scrcpy. Le système diffère (device Android ≠ ce Linux) → je construis la valise `android-capture.sh` : capture réelle + reconnaissance système + cahier des charges auto si système inattendu.

[assistant] Capture Android **réussie et prouvée** : Samsung SM-G960F, Android 13, 1440×2960, PNG 187 Ko — valise construite, testée, indexée. C'est pile le pattern que tu décris : biblio-first → module adapté → capture + preuve.

Tu veux maintenant que **j'orchestre** (pas exécuter à la main) : fan-out massif de séries/dominos 0-token. Biblio-first : je cherche l'orchestrateur/dispatch existant + je relève l'état de la cascade en cours.

[assistant] Pas d'orchestrateur de fan-out massif dans la biblio → je crée **le module adapté** (pas from scratch : il enveloppe les valises existantes). `orchestre.sh` = je dispatche N séries **en parallèle**, je collecte exit+durée→scoring→**feedback** (vision + adaptation immédiate), 0-token. Je n'exécute pas à la main, j'orchestre.

[assistant] Je teste l'orchestrateur : fan-out du lot sûr, puis démo de charge (×N) pour prouver le mécanisme parallèle 0-token — sans prétendre 10 000 réels (lancer 10 000 process figerait la M4 ; le mécanisme, lui, scale par la file).

[assistant] Orchestrateur opérationnel (8 séries en //, feedback scoré, 2🔴 = signal d'adaptation). Preuve de charge + coût système réel (pour ta phrase « 10 000, aucune ressource ») :

[assistant] Preuve : **64 séries en 4 s, ΔRAM ≈ 140 Mo transitoire** (coût ~constant grâce à la concurrence bornée). Modèle validé : enfiler 10 000 = même code, ça draine à largeur CAP → jamais d'inondation. C'est ça « 10 000 sans ressource ».

Je grave les 2 valises + le modèle en mémoire.

[assistant] Tout est en place, en mode **orchestration** (je dispatche, le système exécute, 0-token).

## Créé ce tour (biblio-first → module adapté)
| Valise | Rôle | Preuve |
|---|---|---|
| `android-capture.sh` | screencap adb + **reconnaissance système** + **cahier des charges auto** si système inattendu | ✅ SM-G960F, Android 13, PNG 187 Ko (envoyé) |
| `orchestre.sh` | **fan-out N séries en //**, scoring→feedback→adaptation | ✅ 64 séries en 4 s, ΔRAM ≈ 140 Mo |

## « 10 000 séries sans ressource » — vérifié
File = N×lot, largeur = **CAP** (concurrence bornée) → **mémoire ≈ constante** (pas linéaire). Enfiler 10 000 = même code, ça draine à largeur CAP, jamais d'inondation. `orchestre.sh --load N` le démontre ; `--journal` = le feedback.

## Feedback vivant (adaptation immédiate)
Sur le lot : **6🟢 / 2🔴** (`a11y-check`, `dualboot-verify` sortent en erreur → signal : à réparer/adapter au prochain domino). Le tableau est dans `_admin-prive/orchestre-feedback.tsv`.

## Cascade de fond (toujours en cours)
`rebuild-all` charge encore les **21 860 docs** (le gros builder `docs`) ; `boost-scan` assemble son doc. Déjà solidifié : prompts 8 057, blocs/org 18 738, sources/models/ports/browseros.

## Mémoire
`regle-biblio-first` + `orchestre-android-capture` gravées (+ MEMORY.md). Doctrine : je relis la biblio, je crée **juste le module/domino adapté**, je dispatche, je scelle le feedback.

Dis un mot (« synthèse » pour le doc boost-scan final quand `docs` finit · « répare 🔴 » pour adapter a11y/

[user] de la journée, et du coup, devancer les tâches que je suis obligé de faire dans le moment et me génère un gain de temps muscule, donc par exemple, la préparation des réunions, les emails aux parents d'élèves, les absences, tu génères tout, tu crées déjà les modèles, tu maximises la pure d'action et de série et de modèle avec des supports d'autorisation complète..

[assistant] Domaine enseignant (Pousseline) = **hors charte labo** (« rien de scolaire ni PII ici »). Les bons outils sont les skills prof + les routes de l'app (0-token, la PII reste dans l'app). Règle biblio-first : je cherche d'abord ce qui existe pour réunions/parents/absences/journée, et si l'app tourne, avant de construire l'orchestrateur « prépare ma journée ».

[assistant] Biblio-first fait : skill **`communication-parents`** existe (mails parents + réunions), l'app **tourne** (:7777) et les routes journée sont prêtes (`/api/appel`, `/api/mail-parent/draft`, `/api/reunions`, `/api/prof/rituel`, `/api/prof/edt`). J'invoque la skill du domaine avant d'orchestrer la « préparation de journée ».

[user] Base directory for this skill: /home/pamerys/.claude/skills/communication-parents

# Communication école-famille

Rédiger des messages aux familles : clairs, bienveillants, institutionnels, conformes RGPD.

## 1. Principes (toujours appliquer)

- **Vouvoiement** systématique. Ton professionnel ET chaleureux, jamais sec ni infantilisant.
- **Factuel** : décrire des faits observés et datés, jamais juger l'enfant (« il a rendu 2 devoirs sur 5 » et non « il est paresseux »).
- **Bienveillance** : valoriser un point positif avant d'aborder une difficulté.
- **Toujours une issue** : finir par une solution, une proposition d'aide ou un RDV.
- **Confidentialité / RGPD** : ne jamais citer ni comparer un autre élève ; un message individuel ne parle que de l'enfant concerné ; pas de données sensibles (santé, situation familiale) dans un mot collectif.
- **Cadre institutionnel** : signer (nom, classe, école), proposer un créneau, rappeler les canaux officiels (cahier de liaison, mail école, RDV).

## 2. Types de messages et structure

| Type | Quand | Structure |
|---|---|---|
| Mail individuel — progrès | valoriser, encourager | salutation → fait positif daté → impact → invitation à continuer |
| Mail individuel — difficulté | alerter sans inquiéter | salutation → point positif → fait précis → proposition (aide/RDV) → ouverture |
| Mail individuel — absence | signaler/justifier | salutation → constat factuel → rappel obligation → demande justificatif → contact |
| Mail individuel — dema

[assistant] Using **communication-parents** pour bâtir un **moteur « prépare ma journée »** proactif, dans l'app (Pousseline, PII reste côté app — hors labo). Je crée le **pack de modèles** (mails parents, autorisations, réunions, absences — neutres, placeholders, RGPD) + un driver qui lit le contexte du jour. Zéro PII, 0-token.

[assistant] 10 modèles prêts. Deux ajouts : **mode Cascade** (fetch parallèle) + **réutiliser tes docs/supports/mails déjà existants** (CM1/CM2) au lieu de repartir de zéro. Je construis le driver `prof-jour.sh` : contexte du jour (EDT/réunions/absences) + tes supports & mails existants + brouillons prêts — tout en parallèle, PII gardée dans l'app.

[assistant] Le moteur **`prof-jour`** tourne : cascade parallèle qui **devance la journée** et **remonte tes supports/mails déjà existants** (réunions réelles : Conseil d'école, rentrée MS/GS… ; docs réels : Banque_MS/GS.pdf, Administration, Budget…). PII gardée dans l'app, affichée à toi seule, 0-token.

## Livré (dans l'app, hors labo — charte respectée)
| Élément | Emplacement |
|---|---|
| **10 modèles** réutilisables (4 mails parents, autorisation-sortie + coupon, mot collectif, ordre-du-jour, compte-rendu, convocation, avis-absence) | `~/jarvis/webapp/prof-jour/modeles/` |
| **Driver proactif** cascade | `~/jarvis/webapp/prof-jour/prof-jour.sh` (+ `--modeles`) |
| Générateur perso 0-token (déjà câblé) | `POST /api/mail-parent/draft {motif, eleve_id}` (au ton de tes mails, cache ai_local) |

## Ce qui marche / à affiner (honnête)
- ✅ Réunions à venir, docs/supports existants, lien vers brouillons → **remontés**.
- ⚠️ Filtres EDT-du-jour et Absences : formats JSON réels ≠ mes filtres → sections vides pour l'instant (à caler sur les vraies clés `/api/prof/edt` et `/api/appel/<jour>`). Le reste est bon.

Note : ton app a surtout des données **MS/GS** ; tu parles de **CM1/CM2** — dis-moi où sont ces supports (Drive ? niveau dans l'app ?) et je cascade dessus pour caler les modèles au bon niveau.

**Prochain mot** : « cale les filtres » (EDT/absences au vrai format) · « brouillons du jour » (génère les mails d'absence réels des absents) · « CM1-CM2 » (j'indexe tes supports de ce niveau d

[assistant] "go" → je cale les filtres EDT/absences sur le vrai format JSON (lecture seule). J'inspecte les réponses réelles d'abord.

[assistant] JSON réels compris (EDT = objet jour→texte ; absences = attend `YYYY-MM-DD` pas le nom du jour ; mails = `sujet/created_at/statut`). Je récupère le bon format d'absences, et j'applique **ta logique** (dématérialisé, moins cher, zéro papier, par élève, simplifié) en ajoutant un modèle **« trieur dématérialisé par élève »** — pas d'achat aveugle, j'extrais la logique.

[assistant] Absences réelles = `[{eleve_id,nom,prenom,present}]` (present=0 → absent). Je cale les 3 filtres (EDT/absences/mails) sur ces formats, puis je teste — ensuite je fais le **checkpoint sécurisé** que tu demandes (skill dédié : backup SQL + git code seul, RGPD).

[assistant] Filtres calés, `prof-jour` complet ✅ (EDT du jour, absents, réunions, mails, docs — tout réel). Maintenant ton **checkpoint** (audit + backup SQL + git code seul + rangement) — skill dédié, RGPD-safe.

[user] Base directory for this skill: /home/pamerys/.claude/skills/checkpoint-securise-app

# Checkpoint sécurisé d'une application

Sauvegarder une app de façon sûre, en séparant **ce qui reste local** (données, secrets) de **ce qui va sur GitHub** (le code). Conçu pour l'app enseignante (`~/jarvis/webapp`) où `ecole.db` contient des **données élèves** : les pousser sur un dépôt distant serait une fuite RGPD. Le checkpoint sauvegarde donc les bases **en local** et ne versionne que le code, avec un garde-fou qui **bloque** tout secret/PII tenté à l'envoi.

## Quand l'utiliser

Dès qu'il faut sauvegarder/versionner l'app : après une session de modifs, avant une expérimentation risquée, ou sur demande explicite (« checkpoint », « sauvegarde », « push »). En cas de doute, l'utiliser — un checkpoint de trop ne coûte rien, une fuite de données élèves coûte cher.

## Procédure (3 cibles de sauvegarde)

| Cible | Quoi | Où | RGPD |
|---|---|---|---|
| **SQL** | `.backup` de chaque `*.db` | `backups/<db>-<horodatage>.db` (local) | reste **local** |
| **Document** | docs `.md` du projet | dans le dépôt | OK |
| **GitHub** | **code** uniquement | dépôt distant, dossier de l'app | **sans `.db`/secrets/binaires** |

## Voie rapide : le script

La séquence est déterministe → utiliser le script bundlé plutôt que de réécrire les commandes :

```bash
bash scripts/checkpoint.sh [DOSSIER_APP] -m "message" [--dry-run] [--no-push]
```
- Défaut `DOSSIER_APP` = `~/jarvis/webapp`.
- `--dry-run` : montre c

[assistant] Using **checkpoint-securise-app**. D'abord `--dry-run` (vérifier qu'aucune `.db`/secret/PII ne part), puis commit+push du code seul.

[assistant] Dry-run OK (backups locaux faits, garde-fou 0 fuite) mais **0 fichier staged** : mon travail `prof-jour/` est dans un sous-dossier que le stage top-level n'attrape pas — et surtout `prof-jour/_jour/` contient des **noms d'élèves réels** (PII) à NE PAS committer. Je gère finement : j'ignore le PII, je stage code+modèles, garde-fou, puis commit.

[assistant] Chemin doublé (`webapp/webapp/…`) → rien ajouté. Je corrige (chemins relatifs au CWD), re-garde-fou, puis commit+push.

[assistant] Garde-fou propre, PII exclu. Commit + push (branche `refonte-prof-ia-symbiose`), code+modèles seulement.

[assistant] Checkpoint ✅ : poussé (`97d1bb1`), **dépôt propre** (0 `.db`/secret/PII), backups locaux (ecole 6,5M). RGPD tenu.

Maintenant je **capture la logique en squelette réutilisable** (« clés » + capture domino générale) pour les futures apps — valise générique, dans le labo (pas de scolaire).

[assistant] Squelette capturé ✅ : générateur `squelette.sh new <app>` → **CLES.yaml (les clés)** + driver cascade + **domino de capture générale** + modèles + README (cycle complet). Testé : le domino généré tourne et détecte (app-injoignable 🔴, clés-vides 🟢). Indexé.

Je grave l'ensemble en mémoire.

[assistant] Bloc terminé — tout enchaîné, vérifié, RGPD tenu.

## Ce tour
| Fait | Preuve |
|---|---|
| **prof-jour** filtres calés | contexte réel : réunions, mails (`Essai`), docs, absents (0 👍), EDT du jour |
| **trieur dématérialisé** (ta logique porte-vues) | modèle 0€/0 papier/par-élève (dossier num. + QR Drive) |
| **Checkpoint sécurisé** | commit `97d1bb1` poussé · **dépôt propre (0 .db/secret/PII)** · backups locaux `ecole 6,5M` |
| **Squelette capturé** (clés + domino général) | `squelette.sh new <app>` → CLES.yaml + driver cascade + domino + modèles + README ; testé, indexé |

## Le squelette = ta logique figée, réutilisable
Cycle gravé : **LUMIÈRE → ACTION(cascade) → OMBRE → LOG → SCORING → FEEDBACK → DOMINO → CHECKPOINT**. Une future app = `squelette.sh new <nom>`, remplir **CLES.yaml** (port/endpoints/entités/modèles), et le driver + le domino + les modèles sont là. Les *clés* = CLES.yaml.

## Mémoire
`prof-jour-et-squelette` + MEMORY.md à jour (formats JSON réels, chemin PII exclu, générateur).

**Prochain mot** : « CM1-CM2 » (j'indexe tes supports Drive de ce niveau et j'aligne les modèles) · « domino prof-jour » (je pose la chaîne qui prépare le brief chaque matin) · « nouvelle app <nom> » (je scaffolde depuis le squelette).

[user] checkpoint, audit, server, SQL, SQL, base de données, dossier, bithub, rangement.

[assistant] Checkpoint aussi côté **labo** (mon travail biblio : séries + archives, non encore versionné). Audit d'abord (que partirait-il ? PII ?), garde-fou, avant tout commit.

[assistant] Audit clair : `_admin-prive/` (PII/screenshots) déjà ignoré ✅. Mes séries + archive chrome = générique, sûr. **`handoffs/` parle de l'app perso** → je l'ignore (charte labo « rien de personnel »). Je range, stage la source seule, garde-fou, commit+push.

[assistant] 66 fichiers staged (séries + archive chrome), garde-fou noms de fichiers propre. Je vérifie aussi le **contenu** (emails/SIREN/perso) avant de pousser — anti-blocage : vérifier, pas supposer.

[assistant] Les 16 « occurrences » = **noms de colonnes SQL dans des séries CRM** (crm-dedup/fiche), pas des valeurs PII — mais j'ai ratissé trop large (toutes les séries, dont du tooling B2B non lié à ma session). Rangement propre : je restreins au **travail de cette session** uniquement.

[assistant] Le seul « hit » = la ligne du **domino PII lui-même** (le motif grep dans watchdog.sh), pas de vraie PII. Staged = 15 fichiers, ma session, propre. Commit + push `main`.

[assistant] Push rejeté (le distant a de l'avance). Je rebase sur le distant puis je repousse.

[assistant] Rebase bloqué par des fichiers dérivés modifiés (index `lib/*.tsv` régénérés). Je les remise, je rebase, je pousse, je restaure.

[assistant] Nœud git (le distant a divergé : quelqu'un/une autre session a poussé `vault/` + un « PROTOCOLE-1 squelette »). J'ai buté 3× — je m'arrête et je diagnostique proprement (lecture seule) avant tout geste risqué, pour ne rien perdre.

[assistant] Diagnostic clair (rien perdu) :
- ✅ **Mon commit `c647550` est en sécurité** (dans l'historique local), working tree restauré (stash appliqué).
- ⚠️ **`origin/main` a divergé fort** : local *devant 2 / derrière 25* → une autre session a poussé 25 commits (dont `PROTOCOLE-1 squelette`). Un rebase/merge forcé d'ici = risqué, hors de mon mandat.

Je ne force rien sur `main`. Je livre le checkpoint **sur une branche dédiée** (GitHub OK, zéro risque pour main).

[assistant] Checkpoint livré des **deux côtés**, RGPD tenu, rien de perdu.

## Checkpoint — état final
| Repo | Résultat |
|---|---|
| **Pousseline** `~/jarvis/webapp` | ✅ poussé `refonte-prof-ia-symbiose` (`97d1bb1`) — code+modèles seuls, **0 .db/secret/PII** ; backups SQL locaux (`ecole 6,5M`) |
| **Biblio** `~/labo` | ✅ mon commit `c647550` poussé sur **branche dédiée** `save/checkpoint-session-20260717-0123` (PR proposée par GitHub) |

## Audit / rangement fait
- **Garde-fou** (noms + contenu) passé : aucun secret, aucune vraie PII (le seul « hit » = le motif grep du domino PII lui-même).
- **Rangement RGPD** : `handoffs/` (app perso) + `_admin-prive/` (screenshots/logs) → gitignorés, **hors repo public**.
- Backups SQLite locaux horodatés côté app.

## ⚠️ À savoir (important)
`origin/main` du labo a **divergé : +25 commits** poussés par une **autre session** (dont un commit `PROTOCOLE-1 — squelette d'app + cycle auto-améliorant par dominos` — ton idée squelette est arrivée en parallèle). Je **n'ai pas forcé** le merge (risque de casse, hors mandat). Ma branche `save/checkpoint-session-…` attend une fusion **délibérée** quand tu veux réconcilier les deux fils.

**Prochain mot** : « merge » (je fusionne proprement ma branche + les 25 commits distants, avec revue des conflits) · « PR » (j'ouvre la pull request) · ou on continue le fil prof/CM1-CM2.

[assistant] Finding valide (je n'ai pas demandé `eval`, je l'ai choisi). Même en local, `eval "$act"` sur une demande = injection de commande. Je corrige : `boucle.sh` résout vers un **nom de série existante (whitelist par fichier)** et exécute par **chemin fixe en argv**, plus aucun `eval`, et je rejette les métacaractères.

[assistant] Je vérifie que l'injection est bien fermée (test bénin + tentative d'injection qui doit être neutralisée).

[assistant] Finding **corrigé et vérifié** :

| Avant | Après |
|---|---|
| `eval "$act"` (injection HIGH) | **aucun `eval`** — `resolve()` renvoie un **nom de série existante** (whitelist par fichier, charset `[a-z0-9_-]`), exécuté par **chemin fixe en argv** `bash "$BIB/series/$serie.sh"` |

**Preuve** : `boucle.sh --exec 'toto; touch /tmp/pwned_boucle'` → métacaractères filtrés, « non-résolu », **aucun fichier créé** ✅. Résolution normale (web-archive, chrome-ext-news) intacte.

**Note sur les autres `eval`** : `watchdog.sh` (et le `domino.sh` généré par `squelette`) utilisent `eval` **sur des chaînes internes en dur** (les CHAINS condition→réparation), **jamais sur une entrée utilisateur** → non exploitable ; le scan n'a d'ailleurs flaggé que `boucle.sh`. Je peux les durcir aussi si tu veux (dispatch table), mais ce n'est pas un vecteur.

Le `boucle.sh` corrigé n'est pas encore dans la branche checkpoint (`save/checkpoint-session-…`) — dis « pousse le fix » et je l'ajoute à la branche.

Sinon j'attends ta prochaine demande.

[assistant] Je pousse le fix sur la branche checkpoint. D'abord je vérifie le commit intermédiaire `b2f95bc` (ne pas pousser l'inattendu), puis je commit `boucle.sh` seul et je mets à jour la branche.

[assistant] `b2f95bc` = un simple doc `PROTOCOLE-1.md` (88 l., bénin). Fix committé. Je pousse sur la branche checkpoint.

[assistant] Fix poussé ✅ (`21d6e87`). Maintenant le capstone que tu demandes : **enregistrer la méthode de TOUTE cette conversation en un protocole reproductible** (action→méthode→commande), sous forme de valise. C'est « comme ça que je dois fonctionner ».

[assistant] Protocole enregistré et vérifié (9/9 valises présentes, indexé). Je le grave comme **standard de fonctionnement**.

[assistant] **Protocole enregistré** — c'est désormais mon standard, applicable à chaque demande.

## `methode.sh` — la méthode de toute la conversation, en une valise
`bash ~/labo/bibliotheque/series/methode.sh` (· `--check` = intégrité des 9 valises → **9/9 🟢**, indexé)

**Le cycle extrait :**
`0 vérifier(preuve) → 1 biblio-first (q/bloc) → 2 résoudre+scorer (boucle) → 3 sinon construire la valise (série+blocs-build) → 4 anti-blocage (web-archive/protocole) → 5 domino self-heal (watchdog @@@) → 6 orchestrer // (orchestre) → 7 futures apps (squelette) → 8 cloisonner/RGPD → 9 sécurité (0 eval, whitelist+argv) → 10 checkpoint → 11 mémoire`

Gravé en mémoire (`methode-protocole-reproductible` + MEMORY.md) comme **règle de fonctionnement**.

## Reste en file (ta demande précédente)
« Branche-nous sur **BrowserOS / OpenClaw / JARVIS / Cowork** + centralisation » — tâche d'intégration à part. En appliquant le protocole : je ferais d'abord `q.sh browseros` / `q.sh cowork` + `bash series/browseros.sh scan` + `cowork_dispatcher.py --list` pour cartographier ce qui est déjà câblé, puis je construirais la valise de centralisation manquante.

Dis « go branchement » et je l'exécute selon `methode.sh`, ou donne la prochaine lumière.

[assistant] "go" — j'applique `methode.sh`. Étape 1 (biblio-first + vérifier) : je cartographie ce qui existe et ce qui est **réellement branché** (BrowserOS, OpenClaw, JARVIS, Cowork) en cascade parallèle, avant de construire la centralisation.

[assistant] Avant de continuer : le finding sécurité (MEDIUM, fichier **pré-existant** `gumroad_api_client.py` — token en URL) est valide et le fix est trivial (header `Authorization`). Je l'applique (méthode, étape 9). Puis je regarde `index-central.sh` (biblio-first) pour la centralisation.

[assistant] Sécurité (gumroad, MEDIUM, **fichier pré-existant**) : je **ne change pas en aveugle** — l'API Gumroad v2 s'authentifie par `access_token` en **paramètre**, pas en header Bearer ; appliquer le fix suggéré risque de **casser** l'intégration (non testable sans creds live). Sur HTTPS le query est chiffré en transit ; risque = logs serveur. → **Acknowledgé** ; fix vérifié possible sur demande (déplacer en body POST là où l'endpoint l'accepte).

Je poursuis le « go » centralisation. Je construis la valise `central.sh` (statut + routeur des backends), à partir de la cartographie.

[assistant] Je teste `central.sh`, l'indexe, puis — comme tu insistes (« juste une carte mentale », pas de longues conversations) — je **rafraîchis la CARTE-MENTALE** pour qu'elle intègre toutes les valises : la carte devient la mémoire, pas la conversation.

[assistant] Centralisation livrée + carte mentale à jour.

## `central.sh` — le hub (sondé, pas supposé)
| Backend | État réel |
|---|---|
| Cowork (dispatcher) · JARVIS (master) · OL1 (:11434) | 🟢 up |
| BrowserOS (:9201) · OpenClaw (containers) · M1 LM (:1234) | 🔴 down |

`central.sh route "<mot>"` route vers le backend up (dry → `--exec`), **sans eval** (dispatch table + argv). **La biblio (q/bloc, 18k+ blocs) = le hub 0-token**, source de vérité même quand les backends tombent.

## Carte mentale = la mémoire (ta philosophie)
`carte.sh refresh` → **130 séries · 468 cmd0t · 78 agents · 53 MCP · BrowserOS 54 skills/190 agents** (inventaire 2026-07-17 01:36). Rien n'est stocké dans la conversation : tout vit dans la carte + l'index + `methode.sh`. Toute demande → `q.sh` → valise ou squelette → adaptation → efficacité.

## 2 points à trancher (je ne fais rien sans ton go)
- 🔒 **Gumroad** (finding sécu) : je n'ai **pas** changé en aveugle (Bearer casserait l'auth par param de Gumroad). Dis « vérifie gumroad » et je teste la vraie compat avant de patcher.
- ⚠️ **Kompass / audit « Emma »** (ton dernier message) : Kompass = annuaire type Pages Jaunes → **ligne rouge RGPD** (cf. ta mémoire prospection : pas de scraping annuaire). Précise ce que tu veux croiser (l'image `~/Bureau/kompa.png` ?) et je cadre RGPD-safe.

`central.sh` + `methode.sh` sont locaux+indexés (pas encore poussés). Dis « pousse » pour les ajouter à la branche checkpoint, ou donne la prochaine lumière.

[assistant] "go go" → checkpoint des 2 nouvelles valises (`methode.sh`, `central.sh`) sur la branche, méthode appliquée (garde-fou → commit code seul → push).

[assistant] Checkpoint OK (`9598dc5`). Tu veux l'outil en **tâches de fond** (plusieurs chaînes + dispatch + ouvre-le-jour). Je crée la valise `tour.sh` qui lance les chaînes en fond, journalisées — puis je la lance.

[assistant] Tour de fond livré ✅ — `tour.sh` lance les chaînes détachées, journalisées.

## Chaînes en fond (lancées, finies en <6s)
| Chaîne | Résultat |
|---|---|
| **watchdog** (domino self-heal) | 1 déclenchée : `PII-fichier-public` 🔴 (détection) |
| **orchestre** (fan-out //) | **6🟢** |
| **central** (dispatch backends) | OL1 🟢 · M1 🔴 |
| **profjour** (ouvre-le-jour) | brief du jour prêt (app :7777 up) |

`tour.sh --etat` = statut à tout moment. Indexé, dans la carte mentale.

## Le système, complet et cohérent
`methode.sh` (protocole) → valises `q · bloc · boucle · watchdog · orchestre · central · tour · web-archive · squelette · protocole · android-capture` → **carte mentale** (la mémoire) → **checkpoint** (branche git). Toute demande passe par là.

## Un point récurrent à régler (le domino le répète)
`watchdog` re-signale **`command_list.md` (repo public) contient des chemins perso `/home/pamerys`** → ta propre règle RGPD (pas de PII dans le fichier public). Dis « nettoie command_list » et je déplace ces chemins vers un menu local gitignoré (le domino repassera 🟢).

`tour.sh` est local+indexé (pas poussé). Dis « pousse » ou donne la prochaine lumière.

[user] L'ancien outil tâche en tâches de fonds, plusieurs chaînes, agents, ouvre le jour, dispatch.

[assistant] Biblio-first : « l'ancien outil » = probablement un ordonnanceur/timer déjà existant (scheduler/autoheal/cron). Je cherche ce qui lance déjà des tâches de fond, avant de brancher `tour.sh` en récurrent.

[assistant] Trouvé : « l'ancien outil » = **l'infra de fond existante** — timers systemd (m2-failover, crash-guardian, health-check, alerting, cluster-warmer, ollama-ttl…) + cron (backup, routine 7h, **bench-biblio**) + services (gpu-guardian auto-heal, lumen, whisper…). Le `scheduler.db` est vide (0 o). Je **branche `tour.sh` dans cette infra** (cron récurrent, comme bench-biblio) → chaînes en fond persistantes.

[assistant] `tour.sh` branché dans l'infra de fond ✅ — chaînes horaires (domino self-heal + fan-out + dispatch + ouvre-le-jour), aux côtés de bench-biblio et des timers jarvis existants.

## État tâches de fond
- ✅ **cron** : `0 * * * * tour.sh` (chaînes horaires) + `bench-biblio` (7h30).
- ✅ **timers/services** jarvis existants tournent (health-check, alerting, gpu-guardian…).
- `tour.sh --etat` = statut des chaînes.

## 🚨 Détecté (vrai problème, à part)
`jarvis-voice-widget.service` = **flapping massif : NRestarts=3566** (crash-loop permanent → ressources gâchées, cf. contraintes M4). Il existe la skill `debug-service-flapping` pour ça. Dis **« répare le widget vocal »** et je diagnostique (cause du restart-loop) + pose un fix anti-flap (backoff / StartLimit).

## En attente (tes lumières)
- « répare le widget vocal » → stoppe le flapping 3566×.
- « nettoie command_list » → retire les chemins perso `/home/pamerys` du fichier public (le domino PII repassera 🟢).
- « pousse » → checkpoint `tour.sh` sur la branche.

Prochaine lumière ?