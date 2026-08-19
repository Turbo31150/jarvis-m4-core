[user] Review this change for security vulnerabilities.

Changed files (you may Read these and any other file in the repo):
  - webapp/modeles-communication/generer.sh
  - webapp/scripts/build_modeles.py
  - webapp/scripts/modeles_annee.py
  - webapp/static/modeles/index.html

Unified diff (only + lines are new):

=== DIFF: webapp/modeles-communication/generer.sh ===
@@ -0,0 +1,50 @@
+#!/usr/bin/env bash
+# Générateur cascade 0-token : remplit un modèle de communication via l'IA locale OL1.
+# Usage :
+#   ./generer.sh                         → liste les modèles
+#   ./generer.sh mail-difficulte "Léo, oublie souvent son matériel, propose un RDV"
+#   ./generer.sh mot-sortie "musée du Louvre, 12 mai, car, pique-nique"
+# Sortie : brouillon prêt à relire, affiché + sauvegardé dans brouillons/
+set -uo pipefail
+DIR="$(cd "$(dirname "$0")" && pwd)"
+OL1="http://127.0.0.1:11434/api/generate"
+MODEL="${MODEL:-qwen2.5:7b}"
+mkdir -p "$DIR/brouillons"
+
+# Retrouve un modèle par nom (sans extension), quel que soit le sous-dossier
+type="${1:-}"
+if [ -z "$type" ]; then
+  echo "📋 Modèles disponibles :"
+  find "$DIR" -name '*.md' ! -name 'README.md' | sed "s|$DIR/||; s|\.md$||" | sort | sed 's/^/  • /'
+  echo; echo "Usage : ./generer.sh <type> \"faits datés + issue (RDV/aide)\""
+  exit 0
+fi
+tpl="$(find "$DIR" -name "$(basename "$type").md" | head -1)"
+[ -f "$tpl" ] || { echo "❌ modèle inconnu : $type (lance sans argument pour la liste)"; exit 1; }
+faits="${*:2}"; faits="${faits:-à co

[assistant] Looking at this diff, I need to evaluate:
1. `generer.sh` — bash script calling local Ollama with user-supplied args
2. `build_modeles.py` — writes static templates to SQLite + generates HTML
3. `modeles_annee.py` — extends templates, imports build_modeles dynamically
4. `index.html` — generated static HTML output

[assistant] Analysis:

**generer.sh** — Takes CLI args `$1` (type) and `${*:2}` (faits).
- `$type` → `basename "$type"` before use in `find -name` pattern and output filename → path traversal is stripped
- `$faits` → interpolated into a heredoc → passed via `jq -n --arg p "$prompt"` → jq safely JSON-encodes; no command injection into curl body
- Output file uses `basename` + timestamp; no traversal
- Talks only to `127.0.0.1:11434` (local Ollama); no SSRF surface (URL is static)
- No `eval`/`exec` of model output; it's just written to disk and stdout via `tee`
- The `find -name "$(basename $type).md"` glob could match unintended templates if user passes `*`, but no security impact — it just picks a different `.md` under the same directory

**build_modeles.py / modeles_annee.py** — All template strings are static hardcoded literals. SQLite uses parameterized queries (`?` placeholders). HTML output uses `html.escape()` on category, title, and corps. The dynamic `importlib.util.spec_from_file_location` targets a fixed path adjacent to `__file__` (not user-controlled). `open(...).write(doc)` writes to a fixed OUT path.

**index.html** — Static generated file with hardcoded template content; the inline `onclick="cp(this)"` handler reads from `<pre>` via `innerText` and calls `clipboard.writeText` — content is trusted static text, not attacker-controlled.

No source→sink path with attacker influence and no missing/broken gate. Templates are all hardcoded strings; the shell script uses safe jq 