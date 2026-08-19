[user] Vérifie EMPIRIQUEMENT une affirmation non testée : que les extensions locales d'un index survivent bien à une resynchronisation depuis un miroir distant.

CONTEXTE
`~/.claude/bin/bloc` est un script Python qui construit un index SQLite FTS5 dans `~/.claude/bibliotheque/bibliotheque.db` à partir d'un miroir en lecture seule `~/m1-sync/bibliotheque-vivante/`.

Il vient d'être patché pour lire une 5e source : les TSV du dossier LOCAL `~/.claude/bibliotheque/local/`, qui est HORS du miroir. L'intention est que `bloc sync` (qui fait un rsync depuis la machine M1 puis reconstruit) n'efface PAS ces ajouts locaux.

Cette affirmation a été faite en lisant le code, PAS en la testant. C'est ce que tu dois trancher.

État actuel attendu : 90 354 entrées, dont ~38 433 de source `skillsmp` (dont 36 723 viennent du fichier local `skillsmp-live.tsv`).

Sauvegardes existantes : `/tmp/bibliotheque.db.bak` (index d'avant l'ajout local).

TA MISSION
1. Lis `~/.claude/bin/bloc` et comprends `cmd_build` et `cmd_sync`. Établis sur le code : est-ce que `sync` touche au dossier LOCAL ? Est-ce que le rsync a une option `--delete` qui pourrait déborder ? Quelle est la destination exacte du rsync ?
2. AVANT tout test : sauvegarde l'index actuel dans `/tmp/bibliotheque.db.pre-sync-test` et note les compteurs exacts (`bloc stats`, et un COUNT par source en SQL direct).
3. Fais une copie de sûreté du dossier local dans `/tmp/local-tsv-backup/`.
4. Lance `~/.claude/bin/bloc sync`. Il se connecte en SSH root

[assistant] All local entries survived. Let me identify the single lost key and verify integrity + search.

[assistant] The miroir diff was corrupted by a sort-by-size artifact. Let me redo it correctly and run the search test.

[assistant] Test complete. Nothing was lost — no restore needed.

## Ce que dit le CODE

**`cmd_sync` (lignes 297-309) ne touche jamais le dossier LOCAL.**

- Destination du rsync : `MIROIR + "/"` = `~/m1-sync/bibliotheque-vivante/`. Le dossier local est `~/.claude/bibliotheque/local` (ligne 33) — deux arborescences totalement disjointes.
- **Aucun `--delete`** dans la commande rsync. Flags : `-az --info=stats2` + 6 `--exclude`. Donc même à l'intérieur du miroir, rien n'est supprimé.
- Sens du transfert : `root@100.112.114.32:/home/turbo/labo/bibliotheque/` → local. **M1 est la source, jamais la destination** — le rsync est bien en lecture seule sur la machine du tiers. Aucune commande écrivant vers M1 dans le fichier.
- `cmd_build` fait bien `DROP TABLE blocs` (SCHEMA, ligne 53) mais réinjecte les 5 sources dont le LOCAL (lignes 158-166). La table est détruite puis reconstruite ; la survie dépend uniquement de la persistance des TSV locaux sur disque, qui ne sont jamais touchés.

Un seul risque théorique repéré : la dédup `vus = (bloc_id, action)` (ligne 122) est alimentée **avant** le passage LOCAL, donc si M1 finit par publier les mêmes entrées, les lignes locales sont absorbées par le miroir — pas perdues, juste ré-attribuées. C'est exactement ce qui s'est produit sur `skillsmp-blocs.tsv` (voir plus bas).

## Compteurs avant / après (sync réel, pas de repli sur `build`)

Le `bloc sync` a **réussi** : SSH `root@100.112.114.32` joignable (`turbo-MS-7C56`), rsync 57 s, `Number of delete