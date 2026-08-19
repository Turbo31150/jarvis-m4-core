[user] Audite la qualité d'un corpus de 36 723 entrées fraîchement scrapées depuis skillsmp.com. LECTURE SEULE — ne modifie aucun fichier, ne relance pas le scraping.

CONTEXTE
Le fichier `~/.claude/bibliotheque/local/skillsmp-live.tsv` a été produit par `~/jarvis/scripts/bibliotheque/ingest-skillsmp.py`. Format TSV, en-tête `bloc_id  source  mots_cles  action  danger`, 5 colonnes séparées par des tabulations.

La colonne `action` a la forme :
    npx skills add https://github.com/<author>/<repo> --skill <name>  # <description>

Le rapport du scraping annonce : 13 292 urls venant des sitemaps, 23 486 skills décrits par l'API, 36 723 lignes écrites après dédup, 25 165 avec description. Rapport JSON dans `~/.claude/bibliotheque/local/skillsmp-live.report.json`.

TA MISSION — analyse le TSV en Python, ne le lis pas brut (il fait 16 Mo)
1. Intégrité structurelle : combien de lignes ont exactement 5 colonnes ? Signale celles qui n'en ont pas. Vérifie qu'aucune valeur ne contient de tabulation ou de retour ligne résiduel qui décalerait le parsing.
2. Doublons : compte les `bloc_id` en double. Compte aussi les doublons sur la paire (repo GitHub, nom de skill) — deux bloc_id différents qui pointent la même chose est un vrai doublon fonctionnel.
3. Validité des URLs : extrais les URLs github.com de la colonne action. Combien sont bien formées (`https://github.com/<owner>/<repo>` avec owner et repo non vides et sans caractères interdits) ? Liste les 10 pires malformées.
4. Qualité des noms de

[assistant] I'll start by loading the context-mode tools so the 16 MB TSV never enters my conversation.

[assistant] I'll analyze the TSV entirely in the sandbox so the 16 MB never enters my context. Starting with structure, duplicates, URLs, skill names, and descriptions in one pass.

[assistant] Structure is clean: 36 723 data rows, all exactly 5 columns, no CR, no encoding damage. Now the semantic checks.

[assistant] Descriptions look hard-truncated. Let me check the ingest script's cap and then run the live URL sample.

[assistant] Confirmed a hard cap: the script does `action[:400]`. Let me quantify the resulting mid-word truncation and run the live GitHub check.

[assistant] 8/8 alive. A sample of 8 is too weak to conclude, so I'll extend it and also probe whether the skill actually exists *inside* the repo (repo 200 ≠ installable skill).

[assistant] One more decisive check: whether `--skill <name>` actually resolves to a real skill inside the repo, plus case-variant repo collisions.

[assistant] Analysis complete. Everything ran in the sandbox; the 16 MB file never entered my context.

## Audit corpus `skillsmp-live.tsv` — 36 723 entrées

Fichier : `/home/rempc/.claude/bibliotheque/local/skillsmp-live.tsv` (16 487 185 o)
Script source : `/home/rempc/jarvis/scripts/bibliotheque/ingest-skillsmp.py`
Rapport : `/home/rempc/.claude/bibliotheque/local/skillsmp-live.report.json`

### Tableau des métriques

| # | Métrique | Valeur | Verdict |
|---|---|---|---|
| 1 | Lignes de données | 36 723 (= rapport JSON, exact) | OK |
| 1 | Lignes à exactement 5 colonnes | 36 723 / 36 723 (100 %) | OK |
| 1 | Tabulations/retours ligne résiduels dans une valeur | 0 | OK |
| 1 | Octets CR, caractères de remplacement UTF-8 | 0 / 0 | OK |
| 2 | `bloc_id` en double | **0** (36 723 uniques) | OK |
| 2 | Doublons fonctionnels (repo, skill) | 2 018 clés → **2 661 lignes redondantes (7,2 %)** | Réserve |
| 2 | Idem, insensible à la casse | 2 497 clés → **3 404 lignes (9,3 %)** | Réserve |
| 2 | Dépôts présents en variantes de casse | 399 dépôts, **10 233 entrées** concernées (`affaan-m/ECC` + `affaan-m/ecc`, etc.) | Réserve |
| 3 | URLs `github.com` bien formées | **36 723 / 36 723 (100 %)** | OK |
| 3 | Lignes au format canonique strict `npx skills add https://github.com/<o>/<r> --skill ` | 36 723 (100 %) | OK |
| 3 | URLs malformées | **0** — aucune à lister | OK |
| 4 | `--skill` vide | 0 | OK |
| 4 | `--skill` générique inutile | **859** (`skill` 826, `docs` 5, `test` 9, `skills` 9, `doc` 3,