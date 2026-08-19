[user] Explore le dossier /home/pamerys/jarvis/webapp/ (app Flask enseignante "Pousseline", ecole.db SQLite, backend modules *.py, front prof.html).

Objectif : cartographier tout ce qui existe pour la DIFFÉRENCIATION PAR ÉLÈVE et les PROFILS D'ÉLÈVES, car je vais planifier une feature : préparer des profils d'élèves en difficulté (dys, handicap, avancement) et adapter automatiquement chaque exercice de plusieurs façons selon le profil.

Cherche et rapporte précisément (avec chemins fichier:ligne) :
1. La route /api/exercice/differencier (dans prof_routes.py ou adaptatif.py) : quel prompt, quels paramètres (profil élève ?), comment elle adapte.
2. La route /api/exercice/generer : paramètres, notamment un éventuel paramètre "élève" (ex-el dans le front).
3. Le module adaptatif.py : que fait-il (moteur adaptatif par élève ?), quelles routes, quelles tables.
4. Les tables élèves : schéma de `eleves`, `eleve_champs`, `groupes`, `eleve_groupe`, `comportement` — quels champs de profil/besoin existent (PAP, PPRE, dys, points forts/faibles ?).
5. Le front prof.html : onglet "diff" (Différencier) et "eleves" — comment on sélectionne un élève et son profil, quelles fonctions JS (genDiff, etc.).
6. La skill differenciation-pedagogique si un fichier SKILL.md existe dans ~/.claude/skills/differenciation-pedagogique/ : quels principes/prompts de différenciation elle contient.

Contrainte RGPD importante : rapporte si des VRAIES données élèves (noms) sont présentes — je ne dois PAS en fabriquer ni

[assistant] I'll explore the webapp directory to map out everything related to student differentiation and profiles.

[assistant] Let me read the front-end panels and JS functions in detail, plus verify module registration.

[assistant] I have enough to compile the report. Let me quickly confirm the auxiliary routes (eleve_champs, groupes) for reusability.

[assistant] Voici le rapport de cartographie complet.

# Cartographie : Différenciation par élève & Profils d'élèves — webapp Pousseline

## RGPD — ALERTE : de VRAIES données élèves sont présentes
`ecole.db` contient **11 vrais élèves** avec `prenom`/`nom` remplis et des profils réels (`besoins`, `points_forts`). Exemples de besoins déjà saisis (à NE PAS reproduire/exposer) : `dyslexie`, `PPRE lecture`, `TDA`, `allophone (arrivée récente)`, `dyspraxie/graphisme`, etc. Il y a aussi une table `eleve_champs` avec une clé `allergie` (donnée de santé sensible).
- Pour ta feature : travaille avec des **profils-types anonymes** (dys, TDAH, allophone, avance/HPI) découplés des lignes `eleves` réelles. Ne jamais injecter `prenom`/`nom` réels dans les prompts mis en cache.
- Point de vigilance existant déjà bien géré : les routes forcent `cache=False` dès qu'un élève nommé est impliqué (voir plus bas).

---

## 1. Route `/api/exercice/differencier`
`/home/pamerys/jarvis/webapp/prof_routes.py:365-422`
- Body : `{matiere, niveau, notion, nb, eleve_ids:[...]}`. `nb` clampé 1–10 (défaut 3), `eleve_ids` **plafonné à 6** (`ids[:6]`, ligne 376 — raison thermique/lenteur IA locale).
- Boucle sur chaque `eleve_id` → `SELECT * FROM eleves WHERE id=?` → construit un profil à partir de **`points_forts`** et **`besoins`** uniquement (lignes 383-386).
- Prompt (lignes 387-392) : `"Crée {nb} exercices de {matiere} niveau {niveau} sur « {notion} » pour {prenom}, élève de primaire. Adapte précisément à son profil 