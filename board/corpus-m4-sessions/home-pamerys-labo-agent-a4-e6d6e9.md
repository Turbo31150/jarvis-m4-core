[user] Contexte : 94 Go ont été rapatriés d'une machine "M1" dans /home/pamerys/m1-recover. Un index vient d'être construit dans /home/pamerys/labo/_admin-prive/index/moisson-bases.db recensant 849 bases SQLite et 4553 tables. Le disque hôte est à 84 % (76 Go libres), il y a donc un enjeu d'espace.

Schéma de l'index :
  table `base`       : chemin (PK), nom, taille, mtime, nb_tables, lisible, erreur, vu_le
  table `table_base` : chemin, nom_table, nb_colonnes, nb_lignes

On sait déjà que `n8n.db` apparaît 4 fois à l'identique (113 tables, 98 Mo) et que `jarvis_master.db` (4,4 Go, 81 tables) a un jumeau de 4,2 Go.

Ta tâche — ANALYSE UNIQUEMENT, ne supprime STRICTEMENT RIEN :

1. Identifie les groupes de doublons via l'index SQL : mêmes (nom, taille) ou mêmes (taille, nb_tables). Requête l'index, ne parcours pas les 94 Go inutilement.

2. Pour les groupes les plus volumineux (concentre-toi sur ceux dépassant 100 Mo au total), confirme l'identité réelle par empreinte. Astuce d'efficacité : compare d'abord les 1 Mo initiaux (`head -c 1048576 <f> | sha256sum`) ; ne calcule le sha256 complet que si les préfixes concordent ET que le fichier fait moins de 2 Go. Au-delà de 2 Go, compare taille + préfixe + suffixe (`tail -c 1048576`) et dis clairement que c'est une présomption et non une preuve.

3. Distingue soigneusement :
   - VRAIS DOUBLONS (contenu identique, octet pour octet ou fortement présumé)
   - VERSIONS SUCCESSIVES (backups horodatés d'une même base, tailles proches mais conten

[assistant] I'll start by querying the index to find duplicate groups without traversing the filesystem.

[assistant] Index is present (849 bases, ~46 Go of DB files inside the 94 Go). Now let me find the duplicate groups via SQL.

[assistant] Now let me look at the large-file landscape (>100 Mo) and check for hardlinks, which would change the real gain.

[assistant] No hardlinks (nlink=1 everywhere), so gains are real. Now the full sha256 on the confirmed-prefix groups.

[assistant] Prefix/suffix already disproves several same-size candidates. Now full sha256 on the 73 survivors.

[assistant] All 73 candidates resolved into 13 verified-identical groups. Now let me quantify what remains below the threshold, and map the version families.

[assistant] **Aucune écriture, aucune suppression** — index interrogé en `-readonly`, fichiers ouverts en lecture seule uniquement (`head`/`tail`/`sha256sum`/`stat`).

## Méthode

1. SQL sur l'index → 78 groupes `(nom,taille)` + 61 groupes `(taille,nb_tables)`, gain **naïf** annoncé 5,78 Go — chiffre trompeur (même taille ≠ même contenu).
2. Filtre à ≥ 40 Mo par groupe → **81 fichiers candidats** (9,79 Go).
3. `stat` sur les 81 : **nlink=1 partout** → aucun lien dur, les gains sont réels.
4. Empreinte 1er Mo + dernier Mo → 8 candidats éliminés (même taille, contenu différent).
5. **sha256 complet des 73 survivants** — tous < 2 Go, donc **preuve complète, aucune présomption nécessaire**. Les seuls fichiers > 2 Go (`jarvis_master.db` 4,65 Go et son « jumeau » 4,45 Go) ont des **tailles différentes** : ce ne sont pas des doublons.

## Vrais doublons — sha256 complet, 13 groupes / 73 fichiers / 60 copies redondantes

| Base | Exemplaires | Taille unitaire | Total occupé | Gain | Preuve |
|---|---|---|---|---|---|
| `unified_plan.db` (backups 20260806 + 20260807) | 2 | 1682,6 Mo | 3365,2 Mo | **1682,6 Mo** | sha256 complet `8bbd5bff…` |
| `etoile_cowork.db` (sql_full_20260806_044925 + …044930) | 2 | 500,3 Mo | 1000,6 Mo | **500,3 Mo** | sha256 complet `159130d2…` |
| `biblio_fts.db` (backups 20260730 → 20260808) | 10 | 54,8 Mo | 547,5 Mo | **492,8 Mo** | sha256 complet `c39679f0…` |
| `jarvis.db` + `jarvis_data.db` + `._*` | 38 | 8,3 Mo | 314,2 Mo | **306,0 Mo** | sha256 complet `e234f048…` |