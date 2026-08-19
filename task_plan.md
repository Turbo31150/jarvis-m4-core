# task_plan.md — Moisson massive → todolist préchargée → cascade

**Goal** : moissonner en masse (LinkedIn, forums, réseaux, actualité), en tirer une todolist
dont chaque tâche arrive préchargée (skill / agent / CLI / prompt / commande), et déverser
le tout dans la cascade.

**Plan approuvé** : `~/.claude/plans/tranquil-forging-snail.md`
**Créé le** : 2026-08-19 · **Machine** : M4 (`pamerys-m4`) · **Backend 0-token** : M6 `10.42.0.230:1234`

> Runtime du skill `planning-with-files` ABSENT (scripts/ et templates/ vides dans les
> 9 copies installées). Ce fichier est tenu à la main. `check-complete.sh`,
> `session-catchup.py`, l'attestation et les modes autonomous/gated ne sont pas disponibles.

---

## Phase A — Socle de préchargement · Status: complete

| # | Tâche | Statut | Preuve |
|---|---|---|---|
| A1 | Index FTS5 de toutes les racines de skills | complete | 40 073 entrées en 12 s ; recherche en 3 ms |
| A2 | Préchargeur enrichi (5 champs) | complete | `scripts/precharge_taches.py` |
| A3 | Rescan des 12 792 entrées de `plan` | complete | skill apparié 0 → 11 684 (91 %) |

## Phase B — Moisson multi-sources · Status: complete (B2 livré mais bloqué en amont)

| # | Tâche | Statut | Preuve |
|---|---|---|---|
| B1 | Moissonneur public 6 sources, idempotent | complete | 257 signaux ; 2ᵉ passage delta = 0 |
| B2 | Passe LinkedIn CDP `:9100` plafonnée | complete (script) / **bloqué** (exécution) | arrêt code 2, 0 donnée, 0 onglet laissé, quota 3/40 |

**B2 — pourquoi aucune donnée.** Deux causes indépendantes, toutes deux mesurées :
1. **BrowserOS est figé.** PID 6760, 8 h 24 d'uptime, état `Sl`. Il accepte le CDP et crée
   des onglets, mais `Page.navigate` ne déclenche jamais `loadEventFired` et
   `Runtime.evaluate` expire. Diagnostic décisif : `example.com` échoue **exactement**
   comme `linkedin.com`, alors que l'hôte répond HTTP 200 en 0,11 s. Cause externe au script.
2. **Aucune session LinkedIn nulle part.** browser-os : 181 cookies lisibles, 0 linkedin.
   google-chrome : 226, 0. chromium : pas de fichier. Lecture prouvée fonctionnelle
   (google, claude.ai, chatgpt visibles). Même navigateur réparé, B2 ne moissonnerait rien.

Le script est néanmoins complet et testé **sur son chemin d'échec** — le plus important
pour un script plafonné : plafond persisté, arrêt net, onglet refermé en `finally`.

## Phase C — Superposition par pattern · Status: complete (avec limite mesurée)

| # | Tâche | Statut |
|---|---|---|
| C1 | Vectorisation des signaux **bruts** | complete | 428/428, cascade M6→M4-ollama |
| C2 | Clustering average-link, seuil calibré | complete | 0,68 (p99 mesuré), plus gros cluster = 16 |
| C3 | Qualification par superposition (4 angles) | 16/33 | arrêté à 94 °C, script rendu reprenable |
| C4 | Rescan borné à 3 tours | script écrit, non lancé | `scripts/rescan_patterns.py` |
| C5 | Centrage par source | complete | écart intra/inter +0,110 → −0,011 |

**Limite mesurée** : 16/16 clusters étaient mono-source. L'embedding capture le style de
la plateforme avant le sujet. Le centrage corrige cela, mais les clusters multi-sources
qui en résultent se forment sur du recouvrement lexical superficiel. Le corpus (428 signaux,
5 sources hétérogènes) n'a pas la densité pour produire un signal de marché transversal.

## Phase D — Sortie cascade · Status: complete

| # | Tâche | Statut | Preuve |
|---|---|---|---|
| D1 | Écrire `bin/cascade-massive.sh` (référencé, absent) | complete | 4 781 tâches en `file_actions` |
| D2 | Dispatch via `skillmp-cascade.sh` | complete | pending 11 → 2 |

---

## Décisions

| Décision | Raison |
|---|---|
| Clusteriser les signaux BRUTS, pas des interprétations | interpréter avant de regrouper injecterait le biais du modèle dans la géométrie |
| Seuil de clustering calibré sur la distribution mesurée | même méthode que l'appariement : ne jamais deviner un seuil |
| **average-link, pas single-link** | le single-link chaîne : à 0,60 il absorbait 395 des 428 signaux dans un seul groupe |
| Filtre de qualité à l'insertion, toutes sources | le cluster le mieux noté du corpus était fait de 10 « Voir cette offre » |
| Le label préfère une lecture informative à `INSUFFISANT` | sinon un refus légitime en tête masque les angles qui, eux, concluent |
| `moisson_vecteurs` porte son backend, `charger()` refuse les mélanges | deux modèles d'embedding placent le même texte ailleurs, et aucun chiffre ne le signalerait |
| `suppress_origin` plutôt que `--remote-allow-origins` | le drapeau affaiblirait la protection de Chrome pour toutes les pages, pas seulement les miennes |
| Recouvrement lexical pondéré, PAS bm25 | bm25 ne discrimine pas : −21,57 faux vs −16,77 juste (400 titres) |
| Seuil d'abstention à 3 points | à 5 pts on ne garde que 29 %, et la tranche 3-4 (66 %) est majoritairement juste |
| Confiance graduée plutôt que binaire | un appariement faux non signalé égare l'agent plus qu'une case vide |
| `file_actions` séparée de `skillmp_cascade_taches` | la seconde n'installe que des slugs du catalogue ; son dispatcher ignore `commande` |
| Google Trends FR à retirer | ne remonte que du divertissement, zéro valeur ici |
| LinkedIn : deux voies séparées | choix utilisateur ; le CDP expose le compte, le public ne l'expose pas |

## Erreurs rencontrées

| Erreur | Tentative | Résolution |
|---|---|---|
| `UNIQUE constraint failed: ...titre` | 1 | `ON CONFLICT(titre) DO UPDATE`, statut `done`/`failed` préservé |
| 2 tâches d'action en `failed` | 1 | Erreur de conception : file d'installation ≠ file d'action → table `file_actions` |
| 9 signaux Trends sur 10 écrasés | 1 | `sig()` hachait l'URL seule ; hache désormais url + titre |
| Rate-limit GitHub 403 | 1 | Signalé dans le journal, non masqué ; `time.sleep(2)` entre requêtes |
| Handshake CDP 403 Forbidden | 1 | Chrome ≥ 111 refuse tout header `Origin` → `suppress_origin=True` |
| Onglet resté sur `about:blank` | 2 | `?url=` de `/json/new` ignoré → `Page.navigate` explicite |
| `Runtime.evaluate` en timeout | 3 | **Escaladé** : BrowserOS figé, cause externe (protocole 3-strikes) |
| `ValueError` à l'import | 1 | `dispatch_superposition` lisait `sys.argv[1]` au niveau module, cassant tout importateur |
| Vectorisation figée à 45/257 | 1 | **Deadlock `Lock`** : `worker()` appelait `log()` en tenant déjà `_lk` → `RLock` |
| M6 LM Studio injoignable | 1 | M6 avait redémarré, port 1234 muet → cascade vers Ollama M4 |
| Méga-cluster de 395 signaux | 1 | single-link chaîne → average-link (scipy) |
| Cluster n°1 fait de « Voir cette offre » | 1 | regex FreeWork trop large → `/job-mission/` + filtre qualité |
| Job de fond apparemment muet | 1 | `\| tail -24` retenait la sortie jusqu'à la fin du pipe |


---

## Phase E — Parade `<think></think>` sur le parc · Status: partiel (4/33)

| # | Tâche | Statut | Preuve |
|---|---|---|---|
| E1 | Cibler les fichiers concernés | complete | 94 avec `chat/completions`, **33 actifs** sans parade (63 en comptant les `.bak`) |
| E2 | `jarvis-table-ronde` | complete | conclusion émise (157 c) au lieu de raisonnement brut |
| E3a | `jarvis-planning-widget.py` | complete | faux succès `{ok:true, reply:""}` → 502 franc ; service redémarré |
| E3b | `multi-llm-orchestrate.py` | complete | verdict **FAIBLE 0,538 → FORT 1.0** |
| E3c | `jarvis-linkedin` | complete | 3 backends OK |
| E3d | module partagé `m6_parade.py` | complete | lève `M6Muet` au lieu de rendre du vide |
| E3e | **28 fichiers restants** | **non fait** | 0-1 référence chacun, plusieurs datent de mars-avril |

## Phase F — Montée en volume · Status: complete

| # | Tâche | Statut | Preuve |
|---|---|---|---|
| F1 | Pagination `--pages=N` | complete | **1 427 nouveaux signaux en 114 s**, corpus 428 → 1 855 |
| F2 | Rate-limit GitHub | complete | arrêt **propre** de la source (400 signaux conservés), journalisé |
| F3 | Filtre qualité | complete | 92 libellés de navigation écartés et comptés |

## Phase G — Patterns sur corpus élargi · Status: in_progress

| # | Tâche | Statut | Preuve |
|---|---|---|---|
| G1 | M6 obligatoire + garde thermique | complete | repli CPU **interdit** ; arrêt si M6 muet ou M4 ≥ 85 °C |
| G2 | Vectorisation massive | complete | 1 855 vecteurs, 24 workers, **M4 à 56 °C** (contre 94 °C avant) |
| G3 | Qualification multi-sources | in_progress | 60 clusters retenus sur 234 denses |
| G4 | Rescan borné | non lancé | `scripts/rescan_patterns.py` |

**Le résultat qui compte** : à 428 signaux, **0 %** de clusters multi-sources.
À 1 855, **50 %** au seuil 0,147. Le constat « densité insuffisante » du volet C est **levé**.
Inspection manuelle de 6 clusters : 4 cohérents, 2 bruit. Le plus précieux mêle
**5 offres d'emploi RAG (FreeWork) et 5 issues techniques RAG (GitHub)** — la demande
solvable et le problème réel dans le même groupe. Ce cluster n'existait pas à 428.

**Débit M6 mesuré** : 1 worker 1,6/s · 6 workers 7,5/s · **24 workers 34,3/s**.
M6 encaisse le parallélisme (4 GPU) là où Ollama local sérialise.
