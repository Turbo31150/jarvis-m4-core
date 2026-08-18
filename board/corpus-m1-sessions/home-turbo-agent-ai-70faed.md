[assistant] Le diagnostic est établi ; sqlite3 3.45.1 supporte bien `VACUUM INTO` (requiert ≥ 3.27). Je sauvegarde puis je modifie.

[assistant] Le lot est conforme. Je vérifie que le snapshot produit par `VACUUM INTO` est une base réellement exploitable.

[assistant] Le trap fonctionne, mais le run tué a produit un **lot partiel** (4 bases sur 5). Je teste le scénario réel de `TimeoutStartSec` systemd, qui envoie SIGTERM à tout le cgroup.

[assistant] Le `setsid` a détaché le PID, le kill n'a pas été envoyé — le run tourne toujours. Je le laisse finir puis je refais le test proprement.

[assistant] Le processus bash est encore vivant (bash diffère le trap jusqu'à la fin de la commande en cours). J'attends sa sortie effective.

[assistant] Deux lots partiels (4 bases sur 5) sont nés de mes runs interrompus. Je les retire — ce sont mes artefacts de test — et je vérifie que le fichier `.lock` ne perturbe pas le miroir.

[assistant] Durcissement livré et vérifié. Le run complet passe de « 15 s à 23 min en dérive » (et jusqu'à 7 h sans converger) à **38,6 s stables**.

## Diff (`/home/turbo/jarvis/scripts/backup-multi-db.sh`, sauvegarde `.bak-20260801`)

Trois ajouts, rien d'autre touché (rotation, pg_dump et chemins intacts) :

1. **Verrou**, après `mkdir -p "$DEST"` : `exec 9>"$DEST/.lock"` puis `flock -n 9 || { echo "run déjà en cours, abandon"; exit 0; }`. Placé avant l'installation du trap, pour qu'un second lancement dans la même seconde (donc même `$TS`) ne puisse pas déclencher le nettoyage du run légitime.
2. **`VACUUM INTO`** en remplacement de `.backup`, précédé de `rm -f "$out"` puisqu'il refuse d'écraser une cible existante. Le commentaire au-dessus de la boucle documente le pourquoi (divergence de `.backup` sur base écrite en continu).
3. **Trap** `cleanup` sur `EXIT INT TERM`, installé juste après la création du manifeste : `rm -f "$DEST"/*_"${TS}".db "$DEST"/*_"${TS}".db-journal` puis `[ -s "$MANIFEST" ] || rm -f "$MANIFEST"`. Le glob est borné au timestamp du run courant, donc aucun `.gz` — ni du run, ni d'un lot antérieur — n'est concerné.

`bash -n` : OK. `VACUUM INTO` n'a échoué sur aucune base (sqlite3 3.45.1, la fonctionnalité existe depuis 3.27) — aucun repli vers `.backup` n'a donc été nécessaire.

## Les trois tests

**Run réel** — 38,6 s (`real`), 5 bases dumpées, manifeste à 5 lignes, `gzip -t` OK sur les 5 `.gz`, et `sha256sum -c` du manifeste passe intégralement. J'ai poussé l