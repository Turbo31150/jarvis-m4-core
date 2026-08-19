[user] Contexte : la base /home/pamerys/m1-recover/neurones/bases/jarvis/jarvis_master.db (4,4 Go, 81 tables) a été récupérée du disque d'une machine "M1" désormais hors ligne. C'est la base principale d'un système personnel nommé JARVIS. Son contenu est inconnu de l'utilisateur, qui a besoin de savoir ce qu'elle contient réellement pour décider quoi en faire.

Ta tâche — EXPLORATION EN LECTURE SEULE :

1. Ouvre-la IMPÉRATIVEMENT en lecture seule :
   sqlite3 "file:/home/pamerys/m1-recover/neurones/bases/jarvis/jarvis_master.db?mode=ro"
   (l'ouvrir en écriture créerait des fichiers -wal/-shm et modifierait la copie récupérée)

2. Dresse la carte des 81 tables : nom, nombre de colonnes, nombre de lignes, poids approximatif. Classe-les par volume décroissant.

3. Regroupe-les par domaine fonctionnel d'après leur schéma et leur nom (par exemple : mémoire/conversations, logs/télémétrie, agents/tâches, trading, contacts/CRM, cache, embeddings/vecteurs, configuration…). Déduis le domaine du schéma réel, pas seulement du nom de table.

4. Pour les 10 tables les plus volumineuses, inspecte 2 ou 3 lignes d'exemple afin de comprendre la nature des données. **Ne recopie AUCUNE donnée personnelle dans ton rapport** : pas de noms de personnes, pas d'adresses e-mail, pas de numéros de téléphone, pas de jetons ni de clés d'API, pas de contenu de messages. Décris la NATURE du contenu ("horodatage + identifiant d'agent + texte libre de 200 à 2000 caractères"), jamais les valeurs elles-mêmes.

5. Si

[assistant] The integrity check is too slow on a 4.4 GB file. Let me kill it and use lighter queries.

[assistant] The `-shm`/`-wal` files came with the recovered copy (all DBs have them). I'll use `immutable=1` to guarantee zero writes.

[assistant] Reading key material was correctly blocked. I'll only count, never read secret values.

[assistant] Exploration terminée. La base n'a pas été modifiée (mtime du `.db` inchangé : 8 août 08:12).

## Méthode

Ouverture via `file:…?immutable=1` (plus strict que `mode=ro` : aucun accès WAL/SHM en écriture). Aucun VACUUM, aucun `PRAGMA quick_check` (trop lent sur 4,4 Go, abandonné). Tailles obtenues via `dbstat` (index rattachés à leur table).

**Réserve** : mon tout premier essai en `mode=ro` (avant bascule en `immutable`) a touché le mtime du fichier `jarvis_master.db-shm`. Le `.db` lui-même est intact — mais ce fichier `-shm` (et son `-wal` de 0 octet) existait déjà dans la copie récupérée, comme pour toutes les autres bases du dossier.

**Chiffres globaux** : 83 tables (dont 4 tables-ombres FTS5 + 2 internes SQLite), 83 index, 2 triggers, 1 135 709 pages de 4 Ko, freelist à 0. Fenêtre d'activité : **30 avril → 8 août 2026** (~100 jours). Machine d'origine : utilisateur `turbo`, nœuds M1 / M2 / OL1 / M6.

## (a) Les 20 tables les plus volumineuses

| # | Table | Lignes | Col. | Taille | Domaine |
|---|---|---:|---:|---:|---|
| 1 | `tasks` | 2 167 185 | 12 | 661 Mo | Orchestration |
| 2 | `skill_logique` | 268 895 | 13 | 542 Mo | Corpus skills |
| 3 | `full_disk_m6_index` | 1 533 439 | 5 | 469 Mo | Inventaire disque |
| 4 | `skillsmp_skills` | 218 372 | 20 | 452 Mo | Corpus skills |
| 5 | `home_full_scan` | 1 292 545 | 6 | 386 Mo | Inventaire disque |
| 6 | `disk_index` | 676 906 | 11 | 251 Mo | Inventaire disque |
| 7 | `biblio_harvest_sessions` | 413 593 | 8 | 237 Mo | Mémoir