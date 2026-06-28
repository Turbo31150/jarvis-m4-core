Je vais produire le cahier des charges directement. La cartographie est déjà fournie dans le contexte, et les skills existantes sont listées. Voici le markdown.

# CDC-TEETSH-ESPACE-PROF
## Cahier des charges — Intégrer le meilleur de Teetsh dans l'app Espace Prof

> Cible : PWA Flask `~/jarvis/webapp` · IA locale 0-token (cache SQL → Ollama) · base `ecole.db` · pattern modulaire `register(app)`
> Principe RGPD : **aucune donnée élève dans le cloud** — tout reste local.
> Périmètre : strictement les fonctionnalités présentes dans la cartographie Teetsh.

---

## 1) Tableau récapitulatif

Légende couverture : **OUI** = déjà dans l'Espace Prof / skill · **PARTIEL** = amorcé, à étendre · **NON** = à créer.

| # | Fonctionnalité Teetsh | Valeur prof | Déjà couvert (skill) | À créer / étendre |
|---|---|---|---|---|
| **Domaine cahier-journal / EDT** |
| 1 | Emploi du temps drag-and-drop (grille créneaux, volumes horaires temps réel, multi-niveaux, modèles, export PDF) | Trame de semaine en quelques clics, respect volumes officiels | NON | **À créer** — module EDT |
| 2 | Génération auto du cahier-journal depuis l'EDT | Cahier-journal pré-rempli, pas de re-saisie | PARTIEL — `cahier-journal-preparations` | Étendre (lien EDT→CJ) |
| 3 | Éditeur de séance avec B.O. préintégrés (cycles 1/2/3) | Rattachement compétences officielles | OUI — `cahier-journal-preparations` | Vérifier B.O. à jour |
| 4 | Copier-coller / duplication de séances entre jours/semaines | Gain de temps activités récurrentes | PARTIEL — `cahier-journal-preparations` | Étendre (duplication) |
| 5 | Import séance depuis fiche de prép / programmation | Cohérence prép↔CJ sans re-saisie | PARTIEL — `cahier-journal-preparations` | Étendre (liaison) |
| 6 | Séances Atelier maternelle (groupes + rotations auto) | Couvre besoin maternelle ateliers tournants | NON | **À créer** — module Ateliers |
| 7 | Rituels comme événement EDT (temps réparti multi-domaines) | Comptabilise temps rituels dans volumes | NON | **À créer** (dans EDT) |
| 8 | Programmations (période) & progressions (semaine), modèles, glisser-déposer | Vue année, couverture programmes | PARTIEL — `cahier-journal-preparations` | Étendre (module prog.) |
| 9 | Suivi d'avancement programmations (à faire / en cours / complété) | Traçabilité prévu vs réalisé | NON | **À créer** (statuts) |
| 10 | Bilans / rappels / statut des séances (terminé/en cours) | Mémoire du déroulé réel | PARTIEL — `cahier-journal-preparations` | Étendre (statuts CJ) |
| 11 | Partage / collaboration (remplaçant, décharge, collègues) | Continuité pédagogique | NON | **À créer** (export/lien) |
| 12 | Export PDF + personnalisation mise en page (polices, vues) | Documents inspection présentables | PARTIEL | Étendre (mise en page) |
| **Domaine préparations / séances** |
| 13 | Séquences hiérarchisées (dossiers > séquences > séances) | Rangement, capitalisation annuelle | PARTIEL — `cahier-journal-preparations` | Étendre (arbo) |
| 14 | Fiches de prép structurées (champs standards + déroulé minuté) | Fiche normée inspection | OUI — `cahier-journal-preparations` | — |
| 15 | Champs personnalisés sur les fiches | Fiche sur-mesure | PARTIEL — `cahier-journal-preparations` / `differenciation-pedagogique` | Étendre (champs custom) |
| 16 | Éditeur de texte enrichi (encadrés colorés, tableaux, images) | Fiches lisibles, consignes en avant | NON | **À créer** (éditeur front) |
| 17 | Export PDF personnalisable fiches/séquences (2 vues) | Prép imprimable propre | PARTIEL | Étendre |
| 18 | Partage / copie collaborative de séquences | Travail équipe de cycle | NON | **À créer** (export/lien) |
| 19 | Banque de ressources prêtes à l'emploi (~37 ressources, PS→CM2) | Activités clé en main différenciées | PARTIEL — `differenciation-pedagogique` | Étendre (banque) |
| 20 | Modèles de progressions/programmations prêts à l'emploi | Démarrage rapide | NON | **À créer** (templates) |
| **Domaine suivi / évaluation** |
| 21 | Carnet de notes multi-systèmes (LSU, NA/PA/A, /10 /20 /100, %, niveaux nommés, custom) | Flexibilité, pas de double saisie | PARTIEL — `evaluation-lsu-bulletins` | Étendre (systèmes notation) |
| 22 | Référentiels B.O. cycles 1/2/3 dans les évals | Alignement attendus officiels | PARTIEL — `evaluation-lsu-bulletins` | Étendre (sélecteur B.O.) |
| 23 | Calcul auto des moyennes (élève / domaine / compétence / période) | Zéro calcul manuel | PARTIEL — `evaluation-lsu-bulletins` | Étendre (calculs SQL) |
| 24 | Bilan individuel + diagramme araignée (vs moyenne classe) | Support visuel entretiens parents | NON | **À créer** (radar) |
| 25 | Visualisation des progrès dans le temps | Mesure progrès réels (PPRE) | PARTIEL — `evaluation-lsu-bulletins` | Étendre (séries temporelles) |
| 26 | Génération bulletins/livrets depuis le carnet | Supprime double saisie note→bulletin | OUI — `evaluation-lsu-bulletins` | — |
| 27 | Saisie d'appréciations avec aide IA | Gain de temps rédaction | OUI — `evaluation-lsu-bulletins` (IA locale) | — |
| 28 | Export XML LSU (habilitation officielle) | LSU rempli sans re-saisie | PARTIEL — `evaluation-lsu-bulletins` | Étendre (export XML LSU) |
| 29 | Export multiple de livrets + verrouillage | Toute la classe en une opération | NON | **À créer** (batch + lock) |
| 30 | Synchronisation livret ↔ carnet de notes | Livret reste à jour | NON | **À créer** (sync) |
| 31 | Gestion des périodes (trimestres / semestres / custom) | S'adapte à l'organisation école | PARTIEL — `evaluation-lsu-bulletins` | Étendre (config périodes) |
| 32 | Module Élèves — fiches + champs personnalisables (import CSV ONDE/LSU) | Centralise infos élève | NON | **À créer** — module Élèves |
| 33 | Listes personnalisées dynamiques + groupes (filtres, tri) | Groupes de besoin réutilisables | PARTIEL — `differenciation-pedagogique` | Étendre (listes filtrées) |
| 34 | Trombinoscope automatique (PDF photos + prénoms) | Début d'année, remplaçants | NON | **À créer** (PDF) |
| 35 | Pyramide des âges (répartition âge/sexe) | Vue démographique classe | NON | **À créer** (graphe) |
| 36 | Registre d'appel + suivi présences + stats PDF | Suivi réglementaire assiduité | NON | **À créer** — module Appel |
| 37 | Partage sécurisé carnets/livrets (liens expiration) | Continuité remplacement | NON | **À créer** (liens locaux) |
| 38 | Module Carnets/Livrets gratuit + hébergement RGPD FR | Conformité RGPD données élèves | PARTIEL | Atout natif local (déjà 0 cloud) |
| **Domaine différenciation / besoins** |
| 39 | Champs perso de différenciation dans fiches | Différenciation dans la prép officielle | PARTIEL — `differenciation-pedagogique` | Étendre |
| 40 | Encadré / zone adaptation élèves à besoins (dys, PAP, PPRE) | Adaptations repérables d'un coup d'œil | PARTIEL — `differenciation-pedagogique` | Étendre (encadré front) |
| 41 | Champ perso fiche élève (profil de besoins, étiquettes couleur) | Centralise PAI/PAP/dys, filtrable | PARTIEL — `differenciation-pedagogique` | Étendre (lié module Élèves) |
| 42 | Listes filtrées dynamiques par critère (niveau, groupe) | Groupes de besoin à la volée | NON | **À créer** (= #33) |
| 43 | Gestion des groupes d'élèves (groupes de besoin, couleurs) | Groupes réutilisables séances/ateliers | PARTIEL — `differenciation-pedagogique` | Étendre |
| 44 | Ateliers tournants avec permutation des groupes | Automatise organisation ateliers | NON | **À créer** (= #6) |
| 45 | Duplication de séance avec adaptation du dispositif | Décline une notion en versions différenciées | PARTIEL — `differenciation-pedagogique` | Étendre |
| 46 | EDT individualisés par élève (ULIS/UEMA/SEGPA, vue multi-élèves) | Parcours individualisés dispositifs | NON | **À créer** (extension EDT) |
| 47 | Colonnes Inclusions & Infos Pros (AESH, éducateurs) | Coordonne accompagnement + inclusion | NON | **À créer** (extension EDT) |
| 48 | Progressions individuelles + micro-objectifs par élève | Suivi objectif-par-objectif (PPRE/PAP) | PARTIEL — `differenciation-pedagogique` / `evaluation-lsu-bulletins` | Étendre |
| 49 | Partage multi-professionnels (AESH, équipe) + QR codes | Aligne AESH/famille autour de l'élève | NON | **À créer** (lien local + QR) |
| **Domaine communication / vie de classe** |
| 50 | Communication aux familles (mails, mots liaison, CR réunion, convocations, infos sortie) — *absent chez Teetsh* | Différenciation forte vs Teetsh | OUI — `communication-parents` | — (avantage acquis) |
| 51 | Modèles réunion de rentrée parents-profs (diaporama) | Gain de temps réunion rentrée | PARTIEL — `communication-parents` | Étendre (bibliothèque modèles) |
| **Domaine organisation / technique** |
| 52 | Plateforme tout-en-un, modules connectés | Tout au même endroit | OUI (Flask modulaire) | — |
| 53 | Accès multi-appareils + synchro | Prépare maison, consulte classe | PARTIEL — PWA | Étendre (sync) |
| 54 | Mode hors-ligne *(absent chez Teetsh)* | Utilisable sans réseau en classe | OUI — PWA installable + IA locale | — (avantage différenciant) |
| 55 | Crédits IA mensuels (quota, payant à l'usage) | — | OUI — IA locale **illimitée 0-token** | — (avantage différenciant) |
| 56 | Conformité RGPD / hébergement données | Données élèves sensibles protégées | PARTIEL — local | Atout natif (0 cloud) |

---

## 2) Modules à créer / étendre dans Espace Prof (par priorité)

Chaque module suit le pattern `register(app)` : table(s) `ecole.db`, routes `/api/...`, onglet front `index.html`, IA locale `ai_local.generate` quand pertinent.

### Priorité P0 — Socle données (prérequis des autres modules)

| Module | Routes /api | Onglet | Table ecole.db | IA locale |
|---|---|---|---|---|
| **Élèves** (#32, #41) | `/api/eleves` CRUD, `/api/eleves/import` (CSV ONDE/LSU), `/api/eleves/<id>/champs` | « Élèves » | `eleves`, `eleve_champs` (clé/valeur + couleur) | — (saisie/import pur) |
| **Groupes & listes** (#33, #42, #43) | `/api/groupes` CRUD, `/api/listes` (filtres dynamiques) | sous « Élèves » | `groupes`, `eleve_groupe`, `listes` | — |
| **Périodes** (#31) | `/api/periodes` (trimestre/semestre/custom) | Réglages | `periodes` | — |

### Priorité P1 — Cœur planification (forte valeur, manques nets)

| Module | Routes /api | Onglet | Table | IA locale |
|---|---|---|---|---|
| **Emploi du temps** (#1, #7) | `/api/edt` CRUD créneaux, `/api/edt/volumes` (calcul horaire), `/api/edt/pdf` | « EDT » | `edt_creneaux`, `edt_modeles` | — |
| **EDT → Cahier-journal** (#2) | `/api/cj/generer-depuis-edt` | « Cahier-journal » | `cj_seances` (lien `edt_creneau_id`) | optionnel (pré-remplissage) |
| **Programmations / progressions** (#8, #9, #12, #20) | `/api/programmations` CRUD, `/api/programmations/<id>/statut`, `/api/programmations/pdf` | « Programmations » | `programmations`, `prog_items` (statut: à faire/en cours/complété) | suggestion répartition |
| **Statuts & bilans CJ** (#4, #5, #10) | `/api/cj/<id>/dupliquer`, `/api/cj/<id>/statut`, `/api/cj/import-prep` | « Cahier-journal » | colonnes `statut`, `bilan` sur `cj_seances` | — |

### Priorité P2 — Évaluation avancée

| Module | Routes /api | Onglet | Table | IA locale |
|---|---|---|---|---|
| **Carnet multi-systèmes** (#21, #22, #23) | `/api/evals` CRUD, `/api/evals/moyennes`, `/api/evals/dupliquer` | « Évaluation » | `evals`, `eval_notes`, `systemes_notation` | — (calcul SQL) |
| **Bilan élève + radar** (#24, #25) | `/api/eleves/<id>/bilan`, `/api/eleves/<id>/radar` | « Évaluation » | vues sur `eval_notes` | — (agrégation) |
| **Livrets / LSU** (#28, #29, #30) | `/api/livrets/generer`, `/api/livrets/sync-carnet`, `/api/livrets/export-xml`, `/api/livrets/export-batch` | « Livrets » | `livrets`, `livret_lock` | appréciations (`ai_local.generate`, déjà OUI) |

### Priorité P3 — Maternelle & dispositifs spécialisés

| Module | Routes /api | Onglet | Table | IA locale |
|---|---|---|---|---|
| **Ateliers maternelle** (#6, #44) | `/api/ateliers`, `/api/ateliers/rotation` (génère tableau rotation), `/api/ateliers/permuter` | « Ateliers » | `ateliers`, `atelier_groupes`, `rotations` | — |
| **EDT individualisés + Inclusions/Infos Pros** (#46, #47) | `/api/edt/eleve/<id>`, `/api/edt/multi`, colonnes inclusions/infos-pros | « EDT » (vue dispositif) | extension `edt_creneaux` | — |
| **Progressions individuelles micro-objectifs** (#48) | `/api/progressions/eleve/<id>` | « Programmations » | `prog_eleve_items` | suggestion micro-objectifs |

### Priorité P4 — Confort, présentation, partage

| Module | Routes /api | Onglet | Table | IA locale |
|---|---|---|---|---|
| **Éditeur enrichi + encadrés** (#16, #40) | (front uniquement) | partout (séances/fiches) | — | — |
| **Banque de ressources** (#19) | `/api/ressources`, `/api/ressources/<id>/pdf` | « Ressources » | `ressources` | génération fiches (`differenciation`) |
| **Trombinoscope** (#34) | `/api/eleves/trombinoscope/pdf` | « Élèves » | sur `eleves` | — |
| **Pyramide des âges** (#35) | `/api/eleves/pyramide` | « Élèves » | sur `eleves` | — |
| **Registre d'appel** (#36) | `/api/appel`, `/api/appel/stats`, `/api/appel/pdf` | « Appel » | `appels` | — |
| **Partage local + QR** (#11, #18, #37, #49) | `/api/partage/lien` (lien local expirant), `/api/partage/qr` | bouton contextuel | `partages` | — |
| **Modèles communication rentrée** (#51) | `/api/modeles/reunion` | « Communication » | `modeles_comm` | rédaction (`communication-parents`) |
| **Export PDF / mise en page** (#12, #17) | `/api/pdf/options` (polices, vues) | global | — | — |

---

## 3) Mapping avec les skills existantes

| Skill existante | Fonctionnalités Teetsh couvertes / à router vers elle | Action |
|---|---|---|
| **`cahier-journal-preparations`** | #2, #3, #4, #5, #10, #13, #14, #15 (séances B.O., duplication, séquences, déroulé minuté, lien prép↔CJ) | Étendre : duplication inter-semaines, statuts/bilans, arbo dossiers, génération depuis EDT |
| **`differenciation-pedagogique`** | #15, #19, #33, #39, #40, #41, #43, #45, #48 (champs différenciation, encadrés besoins, groupes, exercices par niveau, ressources) | Étendre : groupes réutilisables, listes filtrées, profil de besoins élève |
| **`evaluation-lsu-bulletins`** | #21, #22, #23, #25, #26, #27, #28, #31, #48 (carnet, moyennes, B.O., bulletins, appréciations IA, LSU, micro-objectifs) | Étendre : multi-systèmes notation, radar, sync livret↔carnet, export XML batch + lock |
| **`communication-parents`** | #50 (mails, mots liaison, CR réunion, convocations, infos sortie), #51 (réunion rentrée) | Avantage déjà acquis ; étendre : bibliothèque de modèles téléchargeables |
| **`espace-prof-app`** | Tous les nouveaux modules (route Flask, `register(app)`, branchement front) | Pilote la création de chaque module ci-dessus |
| **`creer-outil-cascade-locale`** | Branchement IA locale 0-token de chaque module IA (#27, #51, ressources, suggestions prog.) | Garantit cascade cache→Ollama, on-demand, anti-surchauffe |

**Non couvert par aucune skill (modules purement data/UI, sans IA)** : EDT (#1, #7, #46, #47), Élèves/import (#32), trombinoscope (#34), pyramide (#35), appel (#36), périodes (#31), partage local + QR (#11/#18/#37/#49), ateliers (#6/#44). → relèvent de `espace-prof-app` seule.

---

## 4) Réutilisation cascade IA locale 0-token + RGPD

### Cascade obligatoire (toute fonction IA des modules)
```
1. CACHE SQL (ecole.db)   → réponse déjà générée pour ce contexte ? → renvoyer (0 compute)
2. OLLAMA local (OL1)     → ai_local.generate (appréciations, suggestions prog., micro-objectifs, ressources)
3. Cluster LM (M1/M2)     → fallback si besoin qualité (distill Claude-opus, 0 token facturé)
4. Gemini (gemini-ask)    → dernier recours, 0 token (OAuth Google One)
```
- **Lecture SQL/cache AVANT toute inférence** (protocole `protocole-sql-avant-compute`).
- **On-demand uniquement** : pas de boucle d'inférence en tâche de fond (anti-surchauffe M4, cf. mémoire).
- Fonctions concernées : appréciations bulletin (#27), suggestion répartition horaire (#8), micro-objectifs (#48), rédaction modèles communication (#51), génération ressources différenciées (#19).
- Fonctions **sans IA** (calcul pur SQL) : moyennes (#23), radar (#24), volumes horaires EDT (#1), stats appel (#36), pyramide (#35), rotations ateliers (#6). → jamais d'inférence, SQL/Python seul.

### RGPD — aucune donnée élève dans le cloud
| Règle | Application |
|---|---|
| Données élèves (#32, #41, notes, appel, livrets) restent dans `ecole.db` local | Stockage 100 % local, jamais d'upload |
| IA sur données élèves → **Ollama local OL1 uniquement** | Appréciations, bilans : pas de Gemini/cloud si nom/données élève dans le prompt |
| Anonymisation avant tout fallback cluster/cloud | Remplacer prénoms par jetons (`[ELEVE]`) si escalade nécessaire |
| Partage (#11/#37/#49) = **liens locaux** (réseau LAN / export PDF / QR vers ressource locale) | Pas de service cloud tiers ; HTTPS local pour PWA offline |
| Sauvegarde | locale (`ecole.db`), pas de cloud — atout vs Teetsh cloud |

---

## 5) TODOLISTE dynamique priorisée

### V1 — Socle données (P0)
- [ ] Module **Élèves** : table `eleves` + `/api/eleves` CRUD + onglet
- [ ] Import CSV ONDE/LSU (`/api/eleves/import`)
- [ ] Champs personnalisés élève + étiquettes couleur (`eleve_champs`)
- [ ] Module **Groupes & listes filtrées** (`groupes`, `eleve_groupe`, `listes`)
- [ ] Module **Périodes** (trimestre/semestre/custom)

### V2 — Emploi du temps + Cahier-journal (P1)
- [ ] Module **EDT** drag-and-drop + calcul volumes horaires temps réel
- [ ] Rituels comme événement EDT (temps réparti multi-domaines)
- [ ] Export PDF EDT
- [ ] **Génération CJ depuis EDT** (`/api/cj/generer-depuis-edt`)
- [ ] Duplication séances inter-jours/semaines + import depuis prép
- [ ] Statuts (terminé/en cours) + bilans/rappels sur séances

### V3 — Programmations / progressions (P1)
- [ ] Module **Programmations** (période) + **progressions** (semaine)
- [ ] Sélecteur B.O. cycles 1/2/3 dans les items
- [ ] Statuts d'avancement (à faire / en cours / complété)
- [ ] Modèles prêts à l'emploi + glisser-déposer
- [ ] Visualisation répartition horaire / équilibre matières
- [ ] Export PDF (vues période×semaine, polices)

### V4 — Évaluation avancée (P2)
- [ ] Carnet **multi-systèmes de notation** (LSU, NA/PA/A, /10/20/100, %, niveaux nommés, custom)
- [ ] Calcul auto moyennes (élève / domaine / compétence / période) — SQL pur
- [ ] **Bilan élève + diagramme araignée** (vs moyenne classe)
- [ ] Visualisation des progrès dans le temps
- [ ] Export **XML LSU** + export batch + verrouillage livrets
- [ ] **Synchronisation livret ↔ carnet** (`/api/livrets/sync-carnet`)

### V5 — Maternelle & dispositifs spécialisés (P3)
- [ ] Module **Ateliers** maternelle (groupes + rotation auto + permutation)
- [ ] Encadrés consignes/différenciation/notes ATSEM-AESH
- [ ] **EDT individualisés par élève** (ULIS/UEMA/SEGPA) + vue multi-élèves
- [ ] Colonnes **Inclusions** & **Infos Pros** (AESH/éducateurs)
- [ ] **Progressions individuelles** micro-objectifs par élève

### V6 — Confort, présentation, vie de classe (P4)
- [ ] **Éditeur de texte enrichi** (encadrés colorés, tableaux, images) front
- [ ] **Registre d'appel** + stats par période + export PDF
- [ ] **Trombinoscope** automatique (PDF photos + prénoms)
- [ ] **Pyramide des âges** (répartition âge/sexe)
- [ ] **Banque de ressources** prêtes à l'emploi (PDF, différenciées)
- [ ] **Séquences hiérarchisées** (dossiers > séquences > séances)
- [ ] Champs personnalisés sur fiches de prép
- [ ] Export PDF personnalisable (2 vues, 10 polices)

### V7 — Partage & collaboration locale (P4)
- [ ] **Partage local** (liens LAN expirants) cahier-journal / EDT / programmations
- [ ] Copie collaborative de séquences (export/import lien)
- [ ] Partage multi-professionnels (AESH/équipe) + **QR codes** vers ressource locale
- [ ] **Bibliothèque de modèles** communication rentrée (diaporama)

### Transverse (à respecter sur chaque V)
- [ ] Toute fonction IA branchée sur cascade **cache SQL → Ollama → cluster → Gemini**
- [ ] **Lecture SQL/cache avant toute inférence** (on-demand, anti-surchauffe)
- [ ] **Aucune donnée élève hors `ecole.db`** ; anonymisation avant tout fallback cluster/cloud
- [ ] Chaque module = pattern `register(app)` + onglet `index.html` + table `ecole.db`
- [ ] PWA offline (HTTPS local) préservé sur tous les nouveaux onglets