[user] Tu construis une BOUCLE D'APPRENTISSAGE pour un orchestrateur d'actions. Tu ne connais rien de la conversation qui précède. Stdlib Python uniquement, aucune dépendance externe.

## Le principe à implémenter

**Une erreur = une amélioration.** Chaque exécution d'action est journalisée, scorée, et le score modifie la pondération de l'action pour les fois suivantes. Une action qui échoue est déclassée ; une action qui réussit remonte. Le système apprend de son propre journal, sans intervention.

## Ce qui existe déjà (lis-le avant d'écrire)

- `~/jarvis/logs/jarvis_logs.db` — table `protocole_runs(id, ts, demande, etape, backend, resultat, duree_ms)`. C'est le journal brut des exécutions.
- `~/jarvis/bin/jarvis-simul.py` — moteur de projections. Il applique **5 lentilles pondérées** dont les poids sont **codés en dur** dans une liste `LENTILLES` : `sure 1.4 · couverture 0.8 · eprouvee 1.2 · agents 1.0 · chronologique 1.1`. Il superpose leurs votes et rend un consensus. Lis-le pour comprendre la structure — **mais ne le modifie pas**.
- `~/jarvis/bin/jarvis-autochain.sh` — la chaîne qui appelle le moteur et journalise dans `protocole_runs`.
- `~/labo/bibliotheque/lib/BLOCS-INDEX.tsv` — ~70 000 blocs, entête `nom<TAB>source<TAB>danger<TAB>bloc`.

**Ne modifie aucune de ces briques.** Tu construis à côté.

## Ce que tu construis : `~/jarvis/bin/scoring-feedback.py`

Une base `~/jarvis/data/scoring.db` et un CLI. Sous-commandes minimales :

```
scoring-feedback.py ingest            

[assistant] Only 53 rows in the journal — that will matter for the conclusion. Let me look at the data and the existing bricks.

[assistant] Now I have the shape of the data. Let me check the Python version and the autochain briefly.

[assistant] 15 distinct actions over 53 runs — thin, but enough to exercise the loop. Writing the engine now.

[assistant] Two failures — and they're my assertions, not the engine. The lissage means 500 failures give score 2/504 ≈ 0.004, not 0, so the weight lands at 0.504, just above the floor. That's correct behavior: the prior bounds the result before the clamp ever binds. Fixing the assertions to test the real property.

[assistant] Both are the same class of bug: a **mention** of failure read as a **verdict**. `0 failed` in a health report and `motif rejet` referring to a past rejection are success/context, not failures. This is precisely the failure mode the brief warns about — a mis-parse declassing a good action. Let me add a neutralization pass.

[assistant] The classification rules changed, so stored verdicts must be replayable. Let me make ingest refresh derived fields via upsert — still idempotent for rows, but rule changes take effect.

[assistant] 28/28 green. Now re-ingest so the corrected rules take effect on the stored runs.

[assistant] Exactly the two false positives, reclassified without re-inserting a single row.

[assistant] The M2 outage is marked `×` and excluded — `0-sonde` keeps a weight of 1.19 instead of being punished for a network cut. That's the whole point of the exercise.

[assistant] Final verification: confirm I touched nothing I shouldn't have, and that the read-only + FK guards actually hold.

[assistant] The source DB mtime moved (15:33 → 16:33). I must confirm that's an external writer and not me.

[assistant] Confirmed clean: `protocole_runs` still 53 rows / max id 53 (my process wrote nothing), the 16:33 write went to another table in that DB from the running harvester, and both existing bricks keep their pre-session mtimes (12:58 / 13:08).

[assistant] Terminé. Voici le rendu.

## 1. Fichiers créés

| Chemin | Rôle |
|---|---|
| `/home/turbo/jarvis/bin/scoring-feedback.py` | moteur + CLI (`ingest` · `poids` · `top` · `explique`) |
| `/home/turbo/jarvis/bin/test_scoring.py` | 28 tests autonomes sur données simulées |
| `/home/turbo/jarvis/data/scoring.db` | base propre (`actions`, `runs_vus`, `ingests`) |
| `/home/turbo/jarvis/data/poids_appris.json` | poids consommables, écriture atomique |

`jarvis-simul.py` (mtime 12:58) et `jarvis-autochain.sh` (13:08) sont **intacts** — vérifié après coup. `jarvis_logs.db` est resté à 53 lignes / max id 53 ; sa mtime a bougé à cause du moissonnage qui écrit dans une *autre* table de la même base, pas moi. Garde-fous vérifiés à l'exécution : `attempt to write a readonly database`, `foreign_keys = 1`, `busy_timeout = 60000`, `FOREIGN KEY constraint failed`.

## 2. La formule

```
score = (Σ wᵢ·succèsᵢ + α·m) / (Σ wᵢ + α)     α=4, m=0.5
wᵢ    = max(0.05, 0.5^(âge_jours / 14))
poids = 1.0 + (score − 0.5) × 2.0   si score ≥ 0.5      → borné [0.5 ; 2.0]
        1.0 − (0.5 − score) × 1.0   sinon
```

- **Lissage** — α=4 pseudo-observations tirées vers 0.5. Un 1/1 pèse 1 observation contre 4 d'a priori → 0.60 ; un 45/50 en pèse 50 → 0.87. Le petit échantillon ne peut pas gagner.
- **Fraîcheur** — demi-vie 14 j, **plancher 0.05** : décroissance, pas oubli. Sans plancher, une action désastreuse redeviendrait vierge en attendant assez longtemps ; l'historique doit rester une dette.
- **Exclusion d