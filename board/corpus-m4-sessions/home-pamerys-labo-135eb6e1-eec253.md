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

[assistant] Looking at this change, it's a set of local admin shell scripts (0-token tooling for a single-user personal repo). Let me trace each for real security impact.

[assistant] After reading each script:

- **android-capture.sh**: adb output ($DEV, $MODEL, etc.) is used in string echoes only; no unquoted expansion into a shell sink. `scrcpy -s "$DEV"` and `adb -s "$DEV"` are properly quoted, and $DEV comes from a controlled awk extraction of `adb devices`. No sink exposure.

- **boucle.sh**: `eval "$act"` where $act is derived by grep-matching command patterns inside the user's own `series/*.sh` files. This is intentional (a command router that runs whatever the biblio resolves). No external-input path reaches eval — the demand only steers which line is matched, and the executed line must literally exist in trusted local scripts. Single-user local tool; matches design intent.

- **orchestre.sh**: `bash "$f" $args` unquoted, but `$args` is derived from the hard-coded SAFE array in-script. No caller-supplied route. No injection.

- **watchdog.sh**: All CHAINS entries (conditions and repairs) are hard-coded strings in the script, then eval'd. No external data flows into them. `xargs -r rm --` on `ls -t` of `$BIB/lib/*.bak*` is fragile with special filenames but the directory is script-owned. No auth boundary crossed.

- **protocole.sh**, **chrome-ext-news.sh**, **web-archive.sh**: read-only listing/grep. `web-archive.sh new <sujet>` writes under `$ROOT/$suj` where `$suj` is a CLI arg from the user — path traversal possible, but the invoker IS the user (self-CLI, no privilege boundary).

- **squelette.sh**: same shape — user-provided `NOM`/`DIR` writes 