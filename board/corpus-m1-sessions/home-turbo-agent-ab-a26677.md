[user] AUDIT SÉCURITÉ EN LECTURE SEULE. Ne modifie aucun fichier. Tu produis un rapport de findings priorisés.

PÉRIMÈTRE — le toolchain du pipeline skillsmp, ces fichiers uniquement :
- `~/labo/bibliotheque/skillsmp/*.py` (aspire.py, github_source.py, injecte.py, enrichir_fr.py, expansion*.py, aspire_site.py, todo_pipeline.py)
- `~/labo/bibliotheque/skillsmp/superviseur.sh`
- `~/jarvis/bin/skillmp.py`, `~/jarvis/bin/skillmp-pipeline.py`, `~/jarvis/bin/skillmp-cascade.sh`, `~/jarvis/bin/skillmp-detect.py`

DÉJÀ CORRIGÉ (ne les re-signale pas) : `~/jarvis/bin/orchestrateur-local.py` (passage argv) et `~/jarvis/bin/cascade-massive.sh` (read -ra). Sers-t'en comme modèle du type de faille recherché.

RECHERCHE — trois classes de failles :
1. **Injection shell** : `subprocess.run(..., shell=True)` ou `os.system`/`os.popen` avec une donnée externe (slug, repo, description, mots-clés, contenu web, argv, lignes de fichier) interpolée dans la chaîne. En bash : `$(…)` non quoté, `eval`, `$VAR` non quoté passé à une commande, word-splitting.
2. **Injection SQL** : requête construite par f-string/concaténation/`%` avec une valeur externe, au lieu de paramètres liés `?`. Vérifie particulièrement les INSERT/UPDATE dans injecte.py et skillmp.py.
3. **Écriture de fichier par chemin non assaini** : un `slug`/`repo`/`chemin` externe utilisé dans un `open(path)` ou `os.path.join` sans neutraliser `../` (traversée de répertoire hors du dossier d'installation).

MÉTHODE : grep ciblé (`shell=True`, `os.s

[assistant] Let me confirm no `shell=True`/`os.system`/`eval` exist anywhere in scope, and check `skillmp.py`'s `--famille` has no `choices` guard.

[assistant] Audit terminé (lecture seule, aucun fichier modifié). J'ai lu intégralement les 13 fichiers du périmètre et vérifié chaque sink par grep + lecture du contexte réel.

## Résultat : 1 finding réel (MEDIUM) + 1 durcissement (LOW). Rien d'aussi exploitable que les 2 déjà corrigés.

---

### MEDIUM — Injection SQL par argv dans `skillmp-cascade.sh:141-142`
- **Fichier:ligne** : `/home/turbo/jarvis/bin/skillmp-cascade.sh` lignes 140-142 (et `LIMIT $QUOTA` l.142, `statut='$ETAT' WHERE id=$ID` l.151).
- **Classe** : injection SQL (variable externe interpolée dans une chaîne `sqlite3`, pas de bind `?`).
- **Donnée en cause** : `$FAMILLE` (issu de `--famille`) et `$QUOTA` (`--quota`), interpolés bruts :
  ```bash
  sqlite3 "$DB" "SELECT ... WHERE statut='pending' \
    $([ "$FAMILLE" != all ] && echo "AND famille='$FAMILLE'") ORDER BY id LIMIT $QUOTA;"
  ```
- **Scénario d'exploitation** : `skillmp cascade --mode auto --famille "x'; DROP TABLE skillmp_cascade_taches; --"`. Le CLI `skillmp.py` (`cmd_cascade`, l.517-526) passe `a.famille` tel quel au script, et **`--famille` n'a AUCUN `choices`** (l.523 : `s.add_argument("--famille", default="all")`), contrairement à `--mode` qui, lui, est restreint. La chaîne arrive dans `sqlite3` qui exécute plusieurs instructions séparées par `;` → exécution SQL arbitraire sur `jarvis_master.db`.
- **Reachability / gravité réelle** : limitée. Le chemin normal du pipeline (`skillmp-detect.py`) n'émet que des noms de famille codés en dur (`trading`, `op