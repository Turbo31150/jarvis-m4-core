[assistant] Je commence par lire le code du widget pour identifier la table et les colonnes réelles.

[assistant] Excellent qualité de routage. J'enregistre maintenant le script dans la bibliothèque.

[assistant] Terminé. Voici le bilan.

## Table et colonne

Le widget `:8899` lit **`tasks`** dans `/home/turbo/jarvis/jarvis_master.db` (`jarvis-planning-widget.py:1183` — `SELECT id,title,agent,context,status FROM tasks WHERE status IN ('pending','running')`). Aucun `SELECT *` sur `tasks` nulle part, donc une colonne additionnelle est inoffensive.

Il n'existait **aucune colonne de préchargement** : `planning-mega.py` concaténait le bloc dans le texte de `context` (`ctx += f" · biblio: {b}"`), ce qui le rendait invisible en SQL et surtout inapplicable aux tâches produites par les autres générateurs. J'ai ajouté **`tasks.biblio_preload TEXT`** (`ALTER TABLE`, colonne 12), et le script reflète aussi le bloc dans `context` pour qu'il reste visible à l'écran — **en préservant le type** : contexte JSON (tâches `[DYNAMIC-…]`) → nouvelles clés `"biblio"` et `"preloaded"` dans l'objet ; contexte texte (scans git) → suffixe ` · biblio: …`. C'était le vrai piège : appendre du texte à un contexte JSON aurait fait échouer le `json.loads` du widget et cassé le regroupement par domaine.

## Comptage avant / après

| Statut | Total | Préchargées avant | Après |
|---|---|---|---|
| pending | 136 | 0 | 136 |
| to_validate | 60 | 0 | 60 |
| running | 3 | 0 | 3 |

199 tâches traitées en 35 s, **199 préchargées, 1 seule sans bloc**. Le « avant = 0 » est littéral pour la nouvelle colonne ; 152 des 199 portaient déjà un ancien préchargement noyé dans `context` (format brut de `planning-mega`), les 47 restant

[assistant] Rapport renvoyé à `main` via SendMessage. Résumé de ce qu'il contient :

**Table + colonne** — `tasks` dans `/home/turbo/jarvis/jarvis_master.db`. Aucune colonne de préchargement n'existait : `planning-mega.py` noyait le bloc dans le texte de `context`, ce qui le rendait invisible en SQL et inapplicable aux tâches des autres générateurs. J'ai ajouté `tasks.biblio_preload TEXT`, avec reflet dans `context` en préservant le type (clé JSON pour les contextes JSON, suffixe texte sinon) — sans quoi le `json.loads` du widget aurait cassé.

**Comptage** — 199 tâches actives (136 pending, 60 to_validate, 3 running), 0 préchargée dans la nouvelle colonne avant, **199 après**, en 35 s. Rejeu immédiat : 0 à traiter, idempotence vérifiée.

**Intentions sans bloc** — une seule sur 199 (`bureau contenus marketing juin 2026-20260624t114939z-3-001`, un nom de dossier Takeout devenu titre de tâche), donc pas de top 10 : l'index à 41 k blocs couvre 198/199.

**Widget :8899** — OK, HTTP 200, file de 15 tâches, contextes JSON modifiés reparsés correctement.

**Script** — `/home/turbo/jarvis/bin/planning-preload-biblio.py`, enregistré dans `cli-live-blocs.tsv` et fusionné dans `BLOCS-INDEX.tsv` (41 108 lignes, sauvegarde `.bak-preload`).

J'ai aussi signalé une anomalie non liée : les tâches en `error` sont passées de 2 à 46 pendant la session, mais toutes ont `biblio_preload IS NULL` et un `updated_at` de 21:16:09 antérieur à mes écritures — un autre producteur en est la cause.