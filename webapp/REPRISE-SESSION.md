# Reprise session Pousseline — 2026-07-16 (22h)

## ✅ Fait cette session (score 9/10 — 0 token, autonome)
- **Audit complet du câblage** : 25 modules backend tous enregistrés ; 5 backends orphelins côté front (outils_classe, commandes, banque, systeme_io, bibliotheque) ; 1 onglet mort (« Outils Classe »).
- **Banque annuelle → 100 %** : 114 → 247 fiches (cible 240), tous niveaux PS→CM2, 3 différenciations + corrigé/fiche. Via `scripts/dispatch_banque.py` (6 workers parallèles → Ollama cloud, déporté, 0 token, 0 chaleur, 16 min). Réutilisable : `python3 scripts/dispatch_banque.py [workers] [--only NIVEAU]`. Log : `backups/dispatch_banque.log`.
- **Amélioration système** : `ai_local.py` def `_gemini` morte (legacy gemini-ask.sh) supprimée — compile OK.
- App vivante `:7777` (HTTP 200), UI rendue OK (screenshot `~/pousseline_accueil.png`).

## ✅ FAIT — Onglet « Outils Classe » câblé (TOUR 2, 22h32)
Section `#section-outils` + `'outils'` dans SECTIONS + hook `navigate()` + 5 fn JS (`loadOutils/genProbleme/genRituel/renderComportement/cptDelta/loadCeintures/setCeinture`). Testé bout-en-bout : 4/4 routes vertes, 0 erreur console, génération live rendue à l'écran. Non commité.

## ✅ FAIT — Module « Plan B » câblé (TOUR 4, 23h12)
Onglet 🆘 Plan B : pioche dans les 247 fiches pré-générées (filtres niveau/matière, chips, « Version courte » = extraction Soutien 100% locale 0-IA, Surprends-moi, Imprimer). Câble l'orphelin `banque_annuelle`. Testé 4/4 + 0 erreur console. **C'est la réponse usage au « ça ne génère rien » : sert le pré-généré local, marche hors-ligne.** Défaut mineur : gap blanc avant le contenu (cosmétique). Non commité.

## 🔄 3 tâches de fond — LIVRÉES (2026-07-16 23h12)
1. **Moteur templates de repli hors-IA** (anti-503) : créer `templates_repli.py` (portage dict de `/mnt/windows/Users/clair/generateur_commentaires_v3.py` : `MODELES[matiere][niveau_scolaire][niveau_eleve]=[phrases]`, 5 styles, `_accorder`/`_pronom`). Brancher via un param `fallback=` dans `ai_local.generate()` : aux 2 `raise AIUnavailable` (ai_local.py ~L428/434) → `if fallback: return {"text":fallback(),"backend":"templates-local","cached":False}`. Prioriser `/api/prof/bulletin`. Front : bandeau « Mode hors-ligne (sans IA) » si backend=templates-local.
2. **Orphelins** : `systeme_io` → CÂBLER dans l'onglet Système existant (carte clé+toggle+test, 3 fn `loadSystemeIo/saveSystemeIo/pingSystemeIo`, hook L1215). `bibliotheque` → **FAIT** : retiré du register `server.py` (route morte).
3. **Programme maternelle 2026** : dict `PROGRAMME_MATERNELLE_2026` complet (PS/MS/GS × 5 domaines BO n°19 × 5 périodes × 4-6 notions ≈ 375 cellules) produit par l'agent (dans son transcript). Intégration : coller sous `DOMAINES_2026` (~L409) + `cells_2026(niveau)` ; dans `_cells()` si niveau∈PS/MS/GS → `cells_2026()`. Puis dispatch masse (idempotent) pour générer les fiches. Explorer le monde scindé `[T/E]`+`[V/M/O]`.

## ✅ Rubriques remplies (2026-07-16 23h19)
- **groupes** : 3 groupes de besoin (Soutien/Standard/Approfondissement) + 11 élèves répartis.
- **ateliers** : 30 (25 maternelle thématiques par domaine 2026 ajoutés par l'agent de fond + 5 élémentaire) — 0 doublon.
- ⚠️ Observation : l'agent general-purpose maternelle a écrit en base via l'API (25 ateliers) — utile mais imprévu ; surveiller les agents "lecture seule" qui peuvent POST.

## ✅ FAIT — Onglet « Commandes & budget matériel » câblé (TOUR 3, 22h44)
Nav item 🛒 + section `#section-commandes` (budget classe, générateur IA depuis besoins, lignes CRUD) + hook `navigate` + 7 fn JS. Testé : 5/5 routes, 0 erreur console, budget réel (800/100, reste 212,50 €) + 14 lignes rendus. ⚠️ **Note du budget classe à réécrire** (vidée par un test, valeur d'origine perdue). Non commité.

## ▶️ PROCHAIN PAQUET — Dédoublonner `/api/biblio`
**Ombre** : `bibliotheque.py` expose `/api/biblio` mais l'onglet « Biblio » consomme `/api/prof/ressources` (route morte). Décider : soit brancher l'onglet sur `/api/biblio`, soit supprimer `bibliotheque.py` du `register`. Vérifier d'abord ce que chaque route renvoie (`curl`), puis trancher. Ensuite : aligner ordre cascade doc↔code (`ai_local.py` vs PROTOCOLE).

## ✅ FAIT — Programme maternelle 2026 intégré + dispatch (TOUR 5, 23h32)
Module `programme_maternelle_2026.py` (375 notions, 5 domaines BO n°19 × 5 périodes) + `_cells()` de `banque_annuelle.py` branché : PS/MS/GS → 125 cellules 2026 chacun. Dispatch lancé → banque 247 → ~622 fiches (0 token, ~15 min). **Piège ruff** : mettre l'usage avant l'import (autofix F401 supprime les imports non encore utilisés).
**Reste** : (a) nettoyer les ~90 anciennes fiches maternelle (matières « Langage oral »/« Nombres »… hors plan 2026) ; (b) câbler `/api/banque/plan` + onglet « Année » sur les domaines 2026 (actuellement affiche encore les anciennes matières via PROGRAMME).

## 🔴 AUDIT GÉNÉRATION (2026-07-16) — voir `AUDIT-GENERATION-2026-07-16.md`
L'app **génère** (via ollama-cloud) mais SPOF : M1 down + local bridé thermique (≥82 °C) + pas de repli hors-IA → 503 si le cloud/net tombe = « ne génère rien ».
**Priorité #0 (robustesse)** : réintégrer un **moteur templates local sans IA** (l'ancienne app Windows l'avait) pour ne jamais renvoyer 503. Puis delta produit : styles de formulation (5), appréciation structurée 3 blocs, accord genre F/M, génération par lot, exports Word/Excel, TTS bulletin. Sources : `/mnt/windows/Users/clair/{generateur_commentaires_v3,generateur_commentaires_scolaires,module_vocal,export_bulletins}.py`. Cf. mémoire `ancienne-app-prof-windows`.

## ⚠️ Vigilance
- **GPU 89 °C `HOT`** (fan 3200) NON causé par le dispatch (compute déporté cloud). Charge locale résiduelle → vérifier `nvidia-smi`, LM Studio, boucles systemd-USER (cf. mémoire m4-surchauffe-overclocking). NE PAS lancer de génération LOCALE tant que >82 °C.
- **Git non commité** sur `refonte-prof-ia-symbiose` : `ai_local.py`, `scripts/dispatch_banque.py`. → checkpoint conseillé (`/checkpoint-securise-app` : backup SQLite + push code seul, 0 PII/secret).

## 🔁 Trous restants (paquets suivants)
1. Câbler onglet Outils Classe (ci-dessus). 2. Brancher `commandes` (budget matériel) au front. 3. Dédoublonner `/api/biblio` vs `/api/prof/ressources`. 4. Aligner ordre cascade doc↔code. 5. (option) mode « variantes » banque (relecture 8× titres différents) — APRÈS complétude.
