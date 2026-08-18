[user] Review this change for security vulnerabilities.

Changed files (you may Read these and any other file in the repo):
  - bin/biblio-classify.py
  - bin/biblio-doctor.py
  - bin/biblio-ingest-sql.sh
  - bin/biblio-porte-qualite.sh
  - bin/bloc.sh
  - bin/injecter-file-nuit.py
  - bin/injecter-taches-nuit.py
  - bin/jarvis-producer.py
  - cli/biblio_cycle.py
  - scripts/biblio-health-check.sh

Unified diff (only + lines are new):

=== DIFF: bin/biblio-classify.py ===
@@ -0,0 +1,349 @@
+#!/usr/bin/env python3
+"""biblio-classify.py — attribue un TYPE à chaque bloc de la bibliothèque.
+
+Pourquoi : ~80 % de BLOCS-INDEX.tsv n'est pas exécutable (chemins nus, rapports,
+commentaires, pointeurs vers un agent). Un simple malus de score dans bloc.sh ne
+suffit pas à sortir une vraie commande en tête — il faut pouvoir FILTRER.
+
+Sortie : BLOCS-KIND.tsv  (nom<TAB>source<TAB>kind).  L'index n'est pas modifié.
+
+kind :
+  exec      commande réellement exécutable telle quelle (binaire de tête installé,
+            aucun placeholder à substituer)
+  template  exige une substitution avant de tourner ([trous:], <var>, {var}…)
+  pointeur  désigne une ressource au lieu d'agir (agent …, Skill:, chaîne:,
+            xdg-open, gh api / gh repo clone, Agent tool subagent_type=…)
+  doc       chemin nu vers un fichier, ou prose sans verbe outil
+  noop      commence par #
+
+Perf : le test « ce binaire existe-t-il ? » est fait UNE fois par tête distincte
+(quelques milliers) puis réduit à une a

[assistant] Looking at this diff, I need to review 10 files that add/modify a "bibliothèque vivante" (library of ready-to-run shell blocks) infrastructure. Let me trace data flows through each file.

[assistant] I've reviewed all 10 changed files. Ignoring the task-tracker reminder — this is a one-shot review.

Analysis summary:

- **bin/biblio-classify.py / biblio-doctor.py**: Read TSV, classify, log. Use parameterized SQL, `shutil.which`, `os.scandir` — no shell exec of user data.
- **bin/biblio-ingest-sql.sh**: Interpolates `$db`, `$c`, `$user` from `docker ps/inspect` and postgres `pg_database` into TSV blocks. Sources are admin-controlled Docker/PG configs, not attacker-influenceable.
- **bin/biblio-porte-qualite.sh**: `bash -n` is parse-only (no execution of `$(...)` etc.). Path checks use quoted `[[ -e "$p" ]]`. Safe.
- **bin/bloc.sh**: Only displays blocks; awk `-v q="$q"` is variable-safe (no eval). Blocks are NOT auto-executed here — user copy-pastes.
- **bin/injecter-file-nuit.py / injecter-taches-nuit.py**: Static command payloads, parameterized SQL. `jarvis-executor.py` routes queue items to pre-approved channel/domino dispatchers (not `shell=True` on `cmd`), so stored `cmd` isn't a direct shell sink.
- **bin/jarvis-producer.py**: Only adds `PRAGMA busy_timeout=30000`. No new sink.
- **cli/biblio_cycle.py**: `bloc_for()` builds `f"bash {path}"` unquoted, but explicitly redirected to `_ECARTES/` and never merged into the routed index. No live sink.
- **scripts/biblio-health-check.sh**: Comments out a systemctl restart. Removes a code path, adds none.

None of the changed files introduce an attacker-controllable source that reaches a sink without an effective mitigation.