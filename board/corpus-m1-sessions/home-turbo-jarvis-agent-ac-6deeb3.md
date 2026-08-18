[assistant] Les deux PID n'existent plus. Je vérifie s'ils ont été relancés sous d'autres PID, et l'état des sorties.

[assistant] Les deux processus sont **morts**. Le fichier `.tmp` est figé à 0 octet depuis 12h41. J'établis pourquoi.

[assistant] Le service `jarvis-plan-refresh` a été tué (SIGTERM) à 14h17:50 après **1h42 de CPU** consommées, et son timer arrêté à 14h18:11. Je lis maintenant le code.

[assistant] Le code de `gen_sql_shortcuts.py` révèle déjà le mécanisme. Je vérifie l'hypothèse décisive : ce que `glob` traverse réellement.

[assistant] Pas de montage SSHFS — donc pas de traversée réseau. Je mesure le volume réel que `glob` doit parcourir, et je lis le `cmd_sync`.

[assistant] 325 302 répertoires, parcourus par `find` en moins de 100 s. Le volume seul n'explique donc pas 1h47. Je reproduis le `glob` exact, chronométré, et je lis les lecteurs de sources du plan.

[assistant] `glob` **n'a pas fini en 150 s** là où `find` couvre les mêmes 325 302 répertoires en moins de 100 s. Je lis les globs de `jarvis-plan.py`.

[assistant] Voilà le coupable de `jarvis-plan.py` : ligne 220. Je mesure son coût réel et sa fréquence d'appel.

[assistant] Un **seul** de ces globs ne finit pas en 120 s. Reste à compter combien de fois il est appelé par sync.

[assistant] **2 145 554 lignes** dans `tasks`. Je dimensionne le correctif et vérifie le garde-fou du timer.

[assistant] 58 570 répertoires visibles seulement — `find` les couvre en secondes. Il manque donc une pièce : je vérifie si `glob` suit les symlinks de répertoires.

[assistant] Pièce maîtresse : **`glob` suit les symlinks de répertoires** (Python 3.12, `_rlistdir` sans `follow_symlinks=False`). Le scan sort donc de `/home/turbo` via `labo`, `models-gguf`, `lmstudio-models` — vers `/mnt/jarvis-data`.

[assistant] Le volume via symlinks reste modeste. Je mesure le débit réel du parcours en Python pur pour identifier où il se perd.

[assistant] Une vérification de cohérence : `sql-blocs.tsv` a bien été produit le 6 août à 01h03, après la date affichée du lien Wine. Je date précisément l'apparition de la boucle.

[assistant] Le `ctime` confirme : la boucle existe depuis le 5 août 21h57. Un run a pourtant abouti à 01h03. Je vérifie qui lance le rebuild et à quelle heure, pour dater la durée réelle.