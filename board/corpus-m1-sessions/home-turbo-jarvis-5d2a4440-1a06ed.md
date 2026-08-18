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

[assistant] Looking at the diff, I need to find vulnerabilities distinct from the two already flagged (command injection in `blocs.py` and path traversal in `__main__.py`).

[assistant] Based on my analysis, I've read all changed files (`__main__.py`, `blocs.py`, `distill.py`, and their tests) and traced the platform input through the pipeline.

Data flow examined:
- `platform` (CLI arg, no validation) → `harvest()` → `distill()` → written to `outdir / f"{platform}-...md"` → `shutil.copy` to `fiche_dir / fiche.name` (`.name` strips path components, so copy destination is safe from traversal) → `make_blocs()` embeds in single-quoted shell strings for later bloc.sh execution
- `synthesis` (LLM output) → written to markdown files (not a code sink)
- `qwen_ask` uses `subprocess.run` with argv list (no shell), so `prompt` is safe from shell injection at this call site
- `merge_index` — dedup key inconsistency (existing lines use raw `parts[0], parts[1]`; new rows use `_clean()`ed) is a logic bug but not exploitable security-wise given only this code writes the file
- File locking absent on shared `BLOCS-INDEX.tsv` — concurrency issue, not a security defect

The two most exploitable paths (platform → shell bloc via single-quote breakout, and platform → filesystem paths) are exactly the two already flagged. The additional patterns I looked for (fail-open state drift, sensitive-to-observability, allowlist escape, gate/action mismatch, IaC omitted args, resource-bound placement) don't apply — this is a small self-contained pipeline with no auth/gates, no observability leakage of sensitive values (only paths logged), and no resource sinks.

I did not find distinct vul