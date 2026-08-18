[user] Review this change for security vulnerabilities.

Changed files (you may Read these and any other file in the repo):
  - cli/content_perf/__main__.py
  - tests/content_perf/test_cli.py
  - cli/content_perf/blocs.py
  - tests/content_perf/test_blocs.py
  - cli/content_perf/distill.py
  - tests/content_perf/test_distill.py

Unified diff (only + lines are new):

=== DIFF: cli/content_perf/__main__.py ===
@@ -0,0 +1,47 @@
+"""content_perf — capture des meilleures perfs d'une plateforme de contenu.
+Usage: python3 -m cli.content_perf <plateforme> [--limit 12]
+Prod: fiche -> ~/jarvis/data/biblio_knowledge/, prompt -> ~/prompts/prompts/claude-code/,
+blocs -> ~/labo/bibliotheque/lib/BLOCS-INDEX.tsv. `base` surchargeable pour les tests."""
+
+import argparse
+import json
+import shutil
+from pathlib import Path
+from . import harvest as hv, distill as dt, blocs as bl
+
+
+def run(platform, base=None, ask=dt.qwen_ask, limit=12):
+    home = Path.home()
+    if base:  # arborescence de test auto-contenue
+        base = Path(base)
+        fiche_dir, prompt_dir = base / "biblio_knowledge", base / "prompts"
+        index, work = base / "lib/BLOCS-INDEX.tsv", base / "content_perf" / platform
+    else:  # chemins de prod réels
+        fiche_dir = home / "jarvis/data/biblio_knowledge"
+        prompt_dir = home / "prompts/prompts/claude-code"
+        index = home / "labo/bibliotheque/lib/BLOCS-INDEX.tsv"
+        work = home / "jarvis/data/content_perf" / platform
+    src = hv.harves

[assistant] Looking at this diff, I'll focus on the security-relevant flows:

1. `platform` is a CLI arg that flows into file paths and into shell-command strings inside a TSV that's likely executed by a "bloc" runner
2. `_clean` strips whitespace but NOT single quotes
3. `make_blocs` wraps paths in single quotes only

Let me verify the bloc-execution context and check for any other sink.

[assistant] I'll ignore the task-tool reminder (not relevant to a security review) and finish verifying whether the `bloc` column is executed.

[assistant] I have enough context now. Key findings:

1. `_clean` strips tab/CR/LF but not single quotes — and the bloc column wraps paths in single quotes, then the user later runs those bloc strings in their shell (per `content-perf-harvester.md` and `bloc.sh` displaying blocs meant to be executed).

2. `platform` flows unvalidated into filesystem paths — path traversal risk.

3. The README content flows into the qwen bash script as argv[2] — but that's argv-safe unless qwen-nothink.sh mishandles it (out of scope of this diff).