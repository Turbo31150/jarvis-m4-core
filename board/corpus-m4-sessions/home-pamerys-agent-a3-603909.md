[user] Tu es l'agent MOISSON-SQL. Objectif : inventorier TOUTES les bases SQLite/SQL du système (M4 + /storage + disque M1) — SCHÉMAS et rôles uniquement — et les cataloguer dans Notion comme actifs de données. AUCUN fichier local.

SÉCURITÉ CRITIQUE : lecture seule STRICTE en mode immuable : sqlite3 'file:CHEMIN?mode=ro&immutable=1' (jamais de verrou à chaud). Tu ne dois JAMAIS lire/exporter le CONTENU des lignes — SEULEMENT : nom du fichier, taille, liste des tables, schéma (colonnes), nombre de lignes par table (COUNT). Bases à données personnelles (ecole.db = élèves, commercial.db = clients, secrets.db, *creancier*, *demarche*) : SCHÉMA + COUNT seulement, JAMAIS une seule ligne de données. Aucun secret. Aucune publication.

SOURCES (lecture seule) :
- ~/jarvis (**/*.db, y compris logs, master), /storage (m1-mirror/databases : jarvis_master.db, jarvis_logs.db, board.db, unified_plan.db…), ~/.n8n/database.sqlite (ne pas ouvrir si verrou — juste taille), ~/jarvis/webapp (ecole.db → schéma seul).
- M1 disque : /media/pamerys/JARVIS-M1/home/turbo (bases .db) — schéma/count seulement.
Liste d'abord tous les .db (find, tailles), puis pour les principaux : tables + schéma + counts.

MOISSON : tableau par base → chemin · taille · nb tables · tables clés · rôle (à quoi sert la base) · sensibilité (PII oui/non) · valorisable ? (ex : base de connaissances, catalogue produits, données de démo anonymisées). Marque clairement les bases PII « NE PAS vendre / anonymiser avant ».

ÉCRIS la page N

[assistant] The find hit the massive backups tree. Let me target live databases only, excluding backups.

[assistant] Good inventory. Now let me pull schemas and counts from the principal live databases.

[assistant] The page title isn't indexed. Let me check the hub's children directly for a possible duplicate before retrying.

[assistant] Page wasn't created. Let me create it in two fast steps: empty page first, then append blocks.

[assistant] Done. The Notion page is created and populated.

## Rapport — MOISSON-SQL

**Page Notion créée** : "🗄️ Moisson — Bases SQL/SQLite (schémas & rôles)"
URL : https://app.notion.com/p/Moisson-Bases-SQL-SQLite-sch-mas-r-les-3bc7800a81d681c8825be809f4e7c4c8
Sous le hub « 🧠 JARVIS OS — Hub », avec lien de rattachement vers l'index maître.

**Contenu** : callout d'intro « schémas & compteurs uniquement — aucune donnée personnelle lue », tableau de 25 bases (7 colonnes : Base · Chemin · Taille · Tables · Rôle · PII · Valorisable), callout final « NE PAS vendre / anonymiser avant ».

**Bases inventoriées : 25** (schéma + COUNT uniquement), réparties en 3 zones :
- Miroir M1 `/storage/m1-mirror/databases` (11) : jarvis_master.db (4,6 Go, 83 tables), board.db (2,8 Go, chunks FTS5 264 616), unified_plan.db (1,7 Go), cowork_engine, jarvis_logs, crm, web_archive, jarvis, browseros, scheduler, secrets
- M4 `~/jarvis` (7) : ecole.db (Pousseline, ~33 tables), data/jarvis.db, etoile.db, jarvis-index.db, code_library.db, budget.db, todo/notes/planning/rdv
- Disque M1 archive + n8n (7) : skillsmp.db (263 Mo, 218 k skills), biblio_fts, gabarits, matrice_ressources, jv_memory, domino_runs, n8n database.sqlite (101 Mo, credentials)

**Marquées PII / SECRETS (6 « NE PAS vendre »)** : ecole.db (élèves), crm.db (prospects), budget.db (finances), secrets.db (credentials), n8n database.sqlite (credentials), data/jarvis.db (security_keys).

**Valorisables** : jarvis_master.db, board.db, skillsmp.db, code_