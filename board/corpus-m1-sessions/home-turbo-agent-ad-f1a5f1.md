[user] INVESTIGATION EN LECTURE SEULE. Ne modifie AUCUN fichier, aucune base — un pipeline écrit en direct dessus. Tu produis un rapport de constats, rien d'autre.

CONTEXTE VÉRIFIÉ (n'utilise QUE ces chemins ; ignore tout `skillsmp.db`, `avale_pages.py`, `extraire_dom.py`, `/home/pamerys` — ils n'existent pas) :
- Base : `~/jarvis/jarvis_master.db` → table `skillsmp_skills` (colonnes utiles : slug, repo, chemin, corps, a_source).
- Code source aspiré : `~/labo/bibliotheque/skillsmp/sources.jsonl` (une ligne JSON par fichier : champs `repo`, `chemin`, `contenu`).
- Injecteur : `~/labo/bibliotheque/skillsmp/injecte.py`.
- Installeur : `~/jarvis/bin/skillmp.py` (fonction `nom_conforme`, `rapatrie_annexes`).

PROBLÈME À QUANTIFIER : ~50 % des skills dont le dépôt a été collecté ne s'apparient pas à leur fichier SKILL.md — leur `corps` reste vide alors que `sources.jsonl` contient bien le fichier. On veut la cause racine.

TÂCHE :
1. Compte dans `skillsmp_skills` : total, `a_source=1`, `corps<>''`, et les cas `repo` présent dans sources.jsonl MAIS `corps=''`.
2. Prends 10 slugs concrets dans ce cas (repo collecté, corps vide). Pour chacun, cherche dans sources.jsonl les `chemin` disponibles pour ce `repo` et compare au `chemin` attendu en base. Où est la rupture d'appariement ? (casse, préfixe de dossier, slug ≠ basename, SKILL.md vs skill.md, sous-dossier profond…)
3. Lis la logique d'appariement dans `injecte.py` (comment il relie une ligne sources.jsonl à une fiche skillsmp_skills) e

[assistant] I'll investigate this appariement bug. Let me start by examining the database schema, counts, and the key files in parallel.

[assistant] Now let me run the deeper analysis. The matching logic is at lines 157-164. I can already see a strong candidate (root-level `SKILL.md` where `dossier=""`). Let me quantify with a Python analysis over sources.jsonl and the DB.

[assistant] Clear signal emerging. Let me compute the "repo collected" denominator (the ~50% framing) and inspect how the *matched* rows relate slug↔chemin, to nail the exact rule and the correct fix.

[assistant] Now the intended slug↔chemin relation is obvious: **slug = full SKILL.md directory path, `/`→`-`, leading dot stripped** (e.g. `.claude/skills/entry-signals/SKILL.md` → `claude-skills-entry-signals`). The current rule only inspects the *immediate parent folder* and does a fragile substring test. Let me validate a corrected deterministic-inverse rule and measure the exact recovery gain.

[assistant] Let me characterize the 313 currently-full rows the inverse rule does NOT reproduce (potential mis-attribution vs. benign normalization差异) before writing up.

[assistant] I have a complete, rigorous picture. Cleaning up scratch files and delivering the report.

[assistant] # Rapport — appariement `skillsmp_skills` ↔ `sources.jsonl`

## 1. Chiffres exacts (base en lecture seule)

| Mesure | Valeur |
|---|---|
| `skillsmp_skills` total | **8 119** |
| `a_source = 1` | **3 094** |
| `corps <> ''` | **3 094** (identique à a_source) |
| `corps` vide | **5 025** |
| corps vide **ET** repo présent dans sources.jsonl | **402** |

Contexte : sources.jsonl = 683 033 fichiers sur **1 304 repos**. Fiches dont le repo a été collecté = **3 496** → 3 094 pleines (**88,5 %**), 402 vides (**11,5 %**). Les 4 623 autres corps vides pointent vers des repos jamais collectés (hors sujet). Le taux réel de non-appariement sur repo collecté est **~11,5 %**, pas 50 %.

## 2. Décomposition des 402 corps-vides+repo-collecté

- **104** = vrai bug d'appariement : le `SKILL.md` est bien dans sources.jsonl et le slug reconstruit **colle exactement**, mais la règle échoue. Quasi tous sont des **`SKILL.md` à la racine** du repo (slug `"skill"`).
- **284** = **lacune de collecte**, pas d'appariement : le repo est dans sources.jsonl mais le `SKILL.md` précis de cette fiche **n'a jamais été aspiré** (monorepos partiellement collectés, ex. `agentskillexchange/skills`). Aucun correctif de code ne peut inventer un fichier absent → il faut recollecter.
- **14** = repo collecté sans aucun `SKILL.md`.

## 3. Cause racine (règle qui échoue — `injecte.py` lignes 157-164)

```python
for c in par_repo.get(repo, []):
    dossier = c["chemin"].rsplit("/", 2)[-2] if "/" in c["chemin"] else ""
