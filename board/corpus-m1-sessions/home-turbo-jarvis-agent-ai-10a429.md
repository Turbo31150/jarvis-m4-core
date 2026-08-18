[assistant] Échec attendu : `ModuleNotFoundError: No module named 'sonde-doctor'`. Étape 3, l'implémentation.

[assistant] Le formateur a retiré l'import ajouté avant son usage. Je le réinjecte maintenant que le code l'utilise.

[assistant] Échec attendu. Implémentation — import et usage dans la même édition, pour que le formateur ne retire pas l'import.

[assistant] 15 tests `ok`. Le fumigène réel. D'abord `lister`, et un état des lieux des unités user en échec (une unité déjà en échec rendrait le verdict INDECIDABLE).

[assistant] Restauration parfaite : rien dans `list-unit-files`, aucune unité en échec, aucun fichier résiduel. Commit de la tâche 5.

[assistant] STATUT: DONE

## Tests

15 tests écrits, **15 passent** (dernière exécution : `Ran 15 tests in 0.045s / OK`). Progression conforme au plan à chaque étape : 2 → 7 → 9 → 13 → 15, chaque test ayant d'abord échoué pour la raison exacte annoncée (`ModuleNotFoundError: No module named 'sonde-doctor'`, puis `no attribute 'sonde_dit_sain'`, `'panne_injectee'`, `'verifier'`, `'construire_parseur'`).

## Fumigène réel

`lister` affiche bien les 4 sondes. Terrain vérifié propre avant injection (aucune unité `--user` en échec, sinon le verdict aurait été `INDECIDABLE`).

    [OK] audit-local-failed-units               FIABLE
    1 sonde(s) · 0 aveugle(s)          (code de sortie 0)

Vérification de nettoyage imposée :

    $ systemctl --user list-unit-files | grep sonde-doctor
    (aucune sortie, rc=1)

Contrôles complémentaires : `systemctl --user --failed` vide, et `~/.config/systemd/user/sonde-doctor-temoin.service` absent. La restauration est complète.

Comme convenu, `verrou-gpu-refuse-ecriture` n'a jamais été exécutée — seulement écrite dans le registre. Aucun réglage GPU touché, aucune lecture ou écriture massive sur disque.

## Commits (branche `feat/content-perf-engine`, rien poussé)

| Hash | Message |
|---|---|
| `29c1bfec` | feat(sonde-doctor): registre declaratif refusant les injections non reversibles |
| `febb9fd0` | feat(sonde-doctor): lecture du verdict, sonde injoignable = malade |
| `f01eb3f7` | feat(sonde-doctor): injection reversible, defaire garanti dans le finally 