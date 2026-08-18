[user] TÂCHE D'IMPLÉMENTATION — refactor mémoire d'un seul fichier. Contexte complet ci-dessous, ne lis aucun fichier de plan.

FICHIER : `/home/turbo/labo/bibliotheque/skillsmp/injecte.py`

PROBLÈME MESURÉ : la fonction `fusionne()` appelle `charge_jsonl(SOURCES)` qui charge INTÉGRALEMENT `sources.jsonl` (5,3 Go, 683 000 lignes JSON) en une liste Python, puis construit `par_repo` (dict repo→liste de tous les fichiers, chacun avec son champ `contenu`). RAM effective >10 Go, rejoué à CHAQUE cycle du superviseur (~10 min). C'est le poste RAM dominant du pipeline.

CODE ACTUEL (lignes ~146-180, fonction fusionne) :
```python
def fusionne():
    fiches = charge_jsonl(SKILLS)          # skills.jsonl, petit — OK de le garder en RAM
    codes = charge_jsonl(SOURCES)          # <-- 5,3 Go chargés ici
    ...
    par_repo = {}
    for c in codes:
        par_repo.setdefault(c["repo"], []).append(c)   # <-- retient tout le contenu
    ...
    for <chaque fiche>:
        slug = url.rsplit("/", 1)[-1]
        repo = slug_repo(f.get("repo"))
        contenu = ""; chemin = ""
        for c in par_repo.get(repo, []):
            if not c["chemin"].lower().endswith("skill.md"):
                continue
            if slug_de_chemin(c["chemin"]) == slug:      # appariement EXACT (déjà en place)
                contenu, chemin = c["contenu"], c["chemin"]; break
        ...
```

Le helper `slug_de_chemin(ch)` existe déjà dans le fichier (reconstruit le slug depuis un chemin de SKILL.md). L'appariement

[assistant] I need to re-indent the remainder of the loop body (lines 219-245) to 12 spaces, and fix the `return` with a `finally` to close `src`.

[assistant] Now let me verify the syntax compiles and check the data structure of sources.jsonl.

[assistant] The structure matches. Now let me write the verification test script comparing old vs new logic on the first 5000 skills.

[assistant] All 5000 identical, 0 divergent. Let me measure the peak RSS of the production pass 1 (index build only) versus the old full-load.

[assistant] Let me confirm no dangling references to the removed `codes`/`par_repo` remain, and do a final compile check.

[assistant] Refactor terminé et vérifié.

## Ce qui a changé — `/home/turbo/labo/bibliotheque/skillsmp/injecte.py`

Fonction `fusionne()` (uniquement) + 2 helpers ajoutés :

- **`index_sources_par_offset()`** (nouveau) — passe 1 : streame `sources.jsonl` en **binaire** ligne par ligne (`open(SOURCES,"rb")`, offset via `offset += len(brut)`), décode chaque ligne (`decode("utf-8","replace")`). Pour toute ligne dont `chemin` finit par `skill.md` (insensible casse), mémorise l'**offset octet** sous la clé `(repo, slug_de_chemin(chemin))`. Clé dupliquée → garde la **première** (équivaut au `break`). Aucun `contenu` retenu.
- **`lit_source_offset(f, offset)`** (nouveau) — passe 2 : `f.seek(offset)` + `readline()` + `json.loads` → `(contenu, chemin)`.
- **`fusionne()`** — supprimé `charge_jsonl(SOURCES)` et la construction `par_repo`. Ouvre `sources.jsonl` en binaire une fois, et pour chaque fiche fait `idx_offset.get((repo, slug))` → seek/lecture si trouvé, sinon `contenu=""`. Handle fermé dans un `finally`. `charge_jsonl(SKILLS)` intact. Frontmatter/desc/nettoyage prose/écritures TSV·SQLite·Postgres **strictement inchangés**.

## Vérification (aucune écriture en base)

Script jetable comparant ANCIENNE logique (par_repo full-load, itération+break, réimplémentée indépendamment) vs NOUVELLE (offset+seek) sur les 5000 premières fiches, même `sources.jsonl` :

| Métrique | Valeur |
|---|---|
| comparés | 5000 |
| **identiques** | **5000** |
| **divergents** | **0** |
| passe 1 : clés indexées | 6