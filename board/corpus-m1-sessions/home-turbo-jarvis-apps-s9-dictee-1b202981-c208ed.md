[user] Review this change for security vulnerabilities.

Changed files (you may Read these and any other file in the repo):
  - pont-whisper.sh
  - src/com/jarvis/dictee/BulleService.java
  - src/com/jarvis/dictee/DicteeIME.java
  - src/com/jarvis/dictee/EcritureService.java
  - src/com/jarvis/dictee/MoteurNatif.java
  - src/com/jarvis/dictee/Reglages.java
  - src/com/jarvis/dictee/SetupActivity.java

Unified diff (only + lines are new):

=== DIFF: pont-whisper.sh ===
@@ -0,0 +1,79 @@
+#!/usr/bin/env bash
+# Expose le serveur Whisper du PC au téléphone, par les trois voies possibles.
+#
+#   ./pont-whisper.sh            # écoute loopback + Tailscale, et branche l'USB
+#   ./pont-whisper.sh --usb      # loopback seulement (téléphone branché)
+#   ./pont-whisper.sh --arret
+#
+# Pourquoi trois voies : l'USB est le chemin le plus court et n'expose rien ;
+# le Wi-Fi sert à la maison sans câble ; Tailscale rend Whisper joignable en
+# 4G, depuis n'importe où, sans ouvrir un seul port sur la box — le lien est
+# chiffré de bout en bout entre les deux machines du tailnet.
+set -uo pipefail
+
+PORT="${STT_PORT:-9744}"
+BACKEND="${STT_BACKEND:-http://127.0.0.1:8789}"   # serveur Whisper local
+PONT="$(dirname "$0")/stt-bridge.py"
+PID_FILE="/tmp/pont-whisper.pid"
+
+arret() {
+  if [ -f "$PID_FILE" ]; then
+    while read -r pid; do kill "$pid" 2>/dev/null; done < "$PID_FILE"
+    rm -f "$PID_FILE"
+  fi
+  pkill -f "stt-bridge.py" 2>/dev/null
+  adb reverse --remove "tcp:$PORT" 2>/dev/null

[assistant] Looking at this diff, I need to trace new sinks and entry points across the changed files.

[assistant] After reading all changed files, the manifest, and the accessibility service config, and tracing the new sinks:

- `BulleService`: overlay + foreground service, exported=false; the ACTION_STOP PendingIntent uses FLAG_IMMUTABLE on 23+; declencheDepuisBulle is in-process only.
- `EcritureService`: accessibility service properly gated by BIND_ACCESSIBILITY_SERVICE, restricted to typeViewFocused events; `ecrit()` is only reachable in-process via the static `instance`.
- `DicteeIME`: static `instance`/`observateur` fields are only readable in-process; no cross-process exposure.
- `MoteurNatif`: standard Google SpeechRecognizer wrapper with no attacker-controlled sinks.
- `SetupActivity.detecte()`: only iterates hardcoded `Reglages.CANDIDATS` — no user input reaches `repond()`.
- `Reglages`: only SharedPreferences accessors; no sinks.
- `pont-whisper.sh`: the LAN/Tailscale binding and plaintext transport concerns are covered by the two excluded findings; the remaining shell operations use values from `tailscale ip` / `hostname -I` which are not attacker-controllable in the threat model.

The `EcritureService.autorise()` substring check is a common Android anti-pattern but here it only feeds a status label in Setup — `actif()` uses the trusted `instance != null`, so no auth decision hangs on it. `insere()` doesn't skip password fields, but the write is user-initiated per dictation. None of these rise to a reportable defect distinct from what's already excluded.