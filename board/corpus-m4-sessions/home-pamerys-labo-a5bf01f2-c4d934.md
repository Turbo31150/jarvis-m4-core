[user] Review this change for security vulnerabilities.

Changed files (you may Read these and any other file in the repo):
  - bibliotheque/series/android-capture.sh
  - bibliotheque/series/boucle.sh
  - bibliotheque/series/chrome-ext-news.sh
  - bibliotheque/series/orchestre.sh
  - bibliotheque/series/protocole.sh
  - bibliotheque/series/squelette.sh
  - bibliotheque/series/watchdog.sh
  - bibliotheque/series/web-archive.sh

Unified diff (only + lines are new):

=== DIFF: bibliotheque/series/android-capture.sh ===
@@ -0,0 +1,85 @@
+#!/usr/bin/env bash
+# SERIE: android-capture — capture écran d'un appareil Android (adb) + RECONNAISSANCE système ; si le système n'est pas celui attendu → CAHIER DES CHARGES auto pour construire l'outil/OS
+# 0-token, sans navigateur. Une sortie = une preuve (doctrine anti-blocage).
+# Usage:
+#   android-capture.sh            → détecte l'appareil, capture l'écran (PNG horodaté)
+#   android-capture.sh --info     → reconnaissance seule (modèle, version, résolution), pas de capture
+#   android-capture.sh --mirror   → miroir live (scrcpy) si présent
+set -uo pipefail
+BIB="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
+OUT="$BIB/_admin-prive/android"; mkdir -p "$OUT"
+STATE="$OUT/.expected_serial"; CDC="$OUT/CDC-android-capture.md"
+
+# --- CAHIER DES CHARGES auto : émis quand « ce n'est plus le système » (pas d'adb / pas d'appareil / device inattendu) ---
+emit_cdc(){
+  local motif="$1"
+  cat > "$CDC" <<EOF
+# Cahier des charges — outil de captu

[assistant] Looking at this diff — all changes are local bash administration scripts in `bibliotheque/series/` for a single-user operator's tooling library. Let me trace source→sink for the potentially-dangerous constructs.

[assistant] **Analysis summary:**

All eight files are local single-operator bash utilities under `bibliotheque/series/`. Tracing the potentially-dangerous sinks:

- **`boucle.sh` — `eval "$act"`**: `$act` is resolved from either (a) `bloc.sh` output filtered by grep, or (b) grep of `$BIB/series/*.sh` with the operator's demand interpolated as regex. Source is the operator's stdin/argv (interactive `--loop` or CLI arg). Executing operator-provided commands is the tool's *stated purpose* ("résolution demande→commande"). No cross-trust-boundary flow.
- **`watchdog.sh` — `eval "$cond"` / `eval "$repair"`**: every string in `CHAINS` is a hardcoded literal in-script. No external data reaches these evals. `$BIB` derives from `BASH_SOURCE` (script location), not input.
- **`orchestre.sh` — `bash "$f" $args`**: `$args` is drawn from the hardcoded `SAFE` array (`"android-capture --info"`, etc.). No user input.
- **`android-capture.sh` — `adb -s "$DEV"`**: `$DEV` comes from `adb devices` output; attacker would need physical USB/ADB access. `emit_cdc` heredoc expands `$(cat "$STATE")` which inserts file *contents as text*, not code.
- **`web-archive.sh new <sujet>`**, **`squelette.sh new <nom>`**: operator-supplied names used in `mkdir -p "$ROOT/$suj"` and `sed -i "s/<NOM>/$NOM/g"`. Path-traversal / sed-metachar breakage are usability bugs when the operator types weird names on their own machine — no attacker-crossable boundary.
- **`chrome-ext-news.sh`**: `grep -rin "$q" "$DIR"/*.md` — properly qu