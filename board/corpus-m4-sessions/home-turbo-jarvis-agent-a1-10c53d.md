[user] Tu construis un REGISTRE d'actions exécutables et son injection dans Claude Code. Tu ne connais rien de la conversation qui précède. Stdlib Python + bash uniquement, aucune dépendance externe.

## Ce qui existe déjà (lis-le avant d'écrire quoi que ce soit)

- `~/labo/bibliotheque/lib/BLOCS-INDEX.tsv` — index TSV de **~70 000 blocs**, entête `nom<TAB>source<TAB>danger<TAB>bloc`. Le champ `danger` est un emoji : 🟢 sûr · 🟠 modifie · 🔴 destructif. Le champ `bloc` est une commande shell prête, un chemin, ou une action en une ligne.
- `~/jarvis/bin/bloc.sh` — routeur : une intention en argument → des blocs prêts, triés par danger.
- `~/jarvis/bin/jarvis-simul.py` — moteur de projections : route une intention, applique **5 lentilles pondérées en parallèle** (sûre 1.4 · couverture 0.8 · éprouvée 1.2 · agents 1.0 · chronologique 1.1), superpose les votes, et rend une chronologie en phases (lecture → exécution → écriture → destruction). Sortie JSON avec `--json`.
- `~/jarvis/bin/jarvis-autochain.sh` — chaîne : intention → biblio → projections → todolist SQLite → cascade → journal `protocole_runs` dans `~/jarvis/logs/jarvis_logs.db`.
- `~/jarvis/logs/jarvis_logs.db` — table `protocole_runs(id, ts, demande, etape, backend, resultat, duree_ms)`.

**Ne réécris aucune de ces briques.** Tu t'appuies dessus.

## Ce que tu construis

### 1. `~/jarvis/bin/registre-actions.py`

Un registre qui indexe les blocs sur **quatre axes** et les rend interrogeables instantanément :

- **couleur** — le da

[assistant] Two large families are misclassified because of decorative prefixes. Let me fix the extraction and make `build` self-healing.

[assistant] Now make `build` self-healing so re-running re-applies improved extraction without duplicating.

[assistant] The SKILL.md has one abbreviated line in a block I labelled verbatim. Fixing it.

[assistant] Terminé.

## 1. Fichiers créés (deux, aucun existant modifié)

- `/home/turbo/jarvis/bin/registre-actions.py`
- `/home/turbo/jarvis/.claude/skills/registre/SKILL.md`

Base créée : `/home/turbo/jarvis/data/registre_actions.db` (71 Mo). `git status` ne montre que ces deux chemins en `??` — `BLOCS-INDEX.tsv`, `bloc.sh`, `jarvis-simul.py`, `jarvis-autochain.sh` et `jarvis_logs.db` sont intacts. Le skill est déjà chargé par le harnais sous le nom `registre`.

## 2. `build` (verbatim, progression élidée)

```
registre-actions build — source /home/turbo/labo/bibliotheque/lib/BLOCS-INDEX.tsv
  lignes retenues : 79547
  rejets : champs=0 cr=0 vide=120
  base : /home/turbo/jarvis/data/registre_actions.db
  avant 77997 → après 79542 : +1661 nouveaux, 5 reclassés, 77876 inchangés, 5 doublons, 116 purgés
=== 2e passage : idempotence ===
  avant 79542 → après 79542 : +0 nouveaux, 5 reclassés, 79537 inchangés, 5 doublons, 0 purgés
```

~14 s, commits par lots de 2 000 avec compteur. Idempotence tenue : `+0 nouveaux, 0 purgés`.

## 3. `stats` (verbatim)

```
 registre-actions — 79542 actions · 154 sources · /home/turbo/jarvis/data/registre_actions.db

 PAR COULEUR
   🟢 sur           59496   74.8 %
   🟠 modifie       16130   20.3 %
   🔴 destructif     3916    4.9 %

 PAR ACTION
   lancer        42154   53.0 %      ecrire         2147    2.7 %
   sonder        12424   15.6 %      supprimer       594    0.7 %
   consulter      9326   11.7 %      installer       463    0.6 %
   autre          66