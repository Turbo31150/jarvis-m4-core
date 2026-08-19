[user] Contexte : un disque de la machine "M1" a été rapatrié par rsync dans /home/pamerys/m1-recover (94 Go). Un inventaire vient d'indexer 856 fichiers SQLite dans la base d'index /home/pamerys/labo/_admin-prive/index/moisson-bases.db. Sur ces 856, **19 se sont révélés illisibles** (colonne `lisible=0`, avec le message d'erreur dans la colonne `erreur`).

Schéma de l'index :
  table `base`       : chemin (PK), nom, taille, mtime, nb_tables, lisible, erreur, vu_le
  table `table_base` : chemin, nom_table, nb_colonnes, nb_lignes

Ta tâche — DIAGNOSTIC UNIQUEMENT, ne répare rien, ne supprime rien :

1. Liste les 19 bases illisibles :
   sqlite3 /home/pamerys/labo/_admin-prive/index/moisson-bases.db "SELECT chemin, nom, taille, erreur FROM base WHERE lisible=0"

2. Pour chacune, détermine la cause réelle en inspectant le fichier sur disque :
   - `file <chemin>` et les 16 premiers octets (un vrai fichier SQLite commence par "SQLite format 3\0")
   - taille nulle ou quasi nulle ?
   - est-ce en réalité un fichier -wal / -shm / -journal orphelin (compagnon d'une base absente) ?
   - est-ce une base chiffrée, un fichier tronqué par la copie, ou un format différent (LevelDB, Chrome, etc.) ?
   - le fichier existe-t-il encore sur le disque source /media/pamerys/JARVIS-M1 ? compare les tailles pour détecter une copie incomplète

3. Classe chaque cas dans exactement une catégorie :
   FICHIER_VIDE / COMPAGNON_WAL_SHM_ORPHELIN / COPIE_TRONQUEE / PAS_UNE_BASE_SQLITE / CHIFFREE / CORROMPUE / AU

[assistant] The index actually contains 849 files with 11 unreadable, not 856/19. Let me verify and diagnose each.

[assistant] Now let me analyze the zero-filled files, the etoile.db header, and compare against the source disk.

[assistant] The 6 large files contain real data but zeroed headers. Let me measure the leading zero run and locate the source-disk counterparts.

[assistant] The 6 large files have exactly their first 4096-byte page zeroed, with intact data after. Now let me locate the source-disk counterparts.

[assistant] Source counterparts found with identical sizes. Let me compare content byte-for-byte.

[assistant] All 9 distinct files match their source byte-for-byte in size and header state. Let me verify content equality and check the backup siblings.

[assistant] The pattern is clear: interrupted backups. Let me verify good copies exist and check the index discrepancy.

[assistant] Diagnostic terminé (lecture seule — aucun fichier modifié, supprimé ni réparé, aucun `-wal`/`-shm` créé).

## Correction préalable sur les chiffres

L'index `/home/pamerys/labo/_admin-prive/index/moisson-bases.db` (écrit le 2026-08-13 22:01) contient **849 bases indexées, dont 11 illisibles** — pas 856/19. Répartition `erreur` : 10 × « file is not a database », 1 × « database disk image is malformed ». Il n'existe pas d'autre index dans le répertoire. Les chiffres 856/19 de la consigne ne correspondent à aucun état présent de la base.

## Tableau des 11 fichiers illisibles

| # | nom (chemin sous `/home/pamerys/m1-recover/`) | taille | catégorie | cause précise | récupérable depuis la source ? |
|---|---|---|---|---|---|
| 1 | `openclaw/.openclaw/skills/siemens-awl-stl-programmer/assets/templates/DataBlock.db` | 226 o | PAS_UNE_BASE_SQLITE | Texte ASCII : template Siemens STEP7 (`DATA_BLOCK "Data_block_1" … END_DATA_BLOCK`). L'extension `.db` signifie « Data Block » automate, pas SQLite | Sans objet — identique à la source, fichier intact |
| 2 | `openclaw/.openclaw/…/templates/FunctionBlockInstanceDB.db` | 129 o | PAS_UNE_BASE_SQLITE | Idem, template `DATA_BLOCK "Motor…"` | Sans objet — identique, intact |
| 3 | `claude/dot-claude/plugins/local/skillsmp/skills/siemens-awl-stl-programmer/assets/templates/DataBlock.db` | 226 o | PAS_UNE_BASE_SQLITE | Copie du n°1 (même skill dupliquée dans `.claude/plugins`) | Sans objet — identique, intact |
| 4 | `claude/dot-claude/…/templat