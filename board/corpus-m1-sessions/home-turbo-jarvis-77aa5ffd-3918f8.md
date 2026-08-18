[user] Review this change for security vulnerabilities.

Changed files (you may Read these and any other file in the repo):
  - bin/nvidia-smi-guard.sh
  - tests/test-gpu-verrou.sh

Unified diff (only + lines are new):

=== DIFF: bin/nvidia-smi-guard.sh ===
@@ -0,0 +1,105 @@
+#!/usr/bin/env bash
+# JARVIS — garde-fou GPU. Shim place devant /usr/bin/nvidia-smi.
+# Lecture : transparent. Ecriture : code de deverrouillage exige.
+# Verrou pose le 2026-08-06 — topologie 5 GPU figee (/etc/jarvis/gpu-lock.json).
+set -uo pipefail
+
+REAL=/usr/bin/nvidia-smi
+HASHFILE=/etc/jarvis/gpu-guard.hash
+LOG=/var/log/jarvis-gpu-guard.log
+
+# --- Le vrai binaire doit exister, sinon on ne bloque rien (fail-open en lecture) ---
+[ -x "$REAL" ] || { echo "nvidia-smi introuvable" >&2; exit 127; }
+
+# --- Flags qui MODIFIENT l'etat du GPU ---
+is_write_flag() {
+  case "$1" in
+    -c|--compute-mode|--compute-mode=*) return 0 ;;
+    -pl|--power-limit|--power-limit=*) return 0 ;;
+    -e|--ecc-config|--ecc-config=*) return 0 ;;
+    -r|--gpu-reset) return 0 ;;
+    --gom|--gom=*|--gpu-operation-mode|--gpu-operation-mode=*) return 0 ;;
+    -ac|--applications-clocks|--applications-clocks=*) return 0 ;;
+    -rac|--reset-applications-clocks) return 0 ;;
+    -lgc|--lock-gpu-clocks|--lock-gpu-clocks=*) return 0 ;;
+    -rgc|--reset-gpu-clocks) return 0 ;;
+    -lmc|--lock-memory-clocks|--lock-memory-clocks=*) return 0 ;;
+    -rmc|--reset-memory-clocks) return 0 ;;
+    -pm|--persistence-mode|--persistenc

[assistant] Looking at the diff carefully. The shim's key security assumption is the secrecy of a PIN verified against a salted SHA-256 hash stored in `$HASHFILE`. Let me examine the hash-file properties and check code lengths.

[assistant] Confirmed: `tests/test-gpu-verrou.sh` line 43 hardcodes `CODE=1202` (a 4-digit PIN, and per `AUDIT_LMS_FULL.md:247` / `audit/SECURITY_HARDENING_2026-06-24.md:5` this same value is reused as the sudo password). Line 297 asserts `/etc/jarvis/gpu-guard.hash` must be **root:root 644** — world-readable.

Combined with the shim design at `bin/nvidia-smi-guard.sh`:
- Any local user can `cat /etc/jarvis/gpu-guard.hash` → obtain `SALT` + `SHA-256(SALT‖PIN)`.
- Since the PIN is a 4-digit code, offline brute-force is 10⁴ ≈ instantaneous with `sha256sum` (billions/sec on GPU).
- No PBKDF, no bcrypt/scrypt/argon2, no iteration count — a single SHA-256 pass.
- No rate-limit or lockout on wrong tries either (`journal "refus-code-invalide"` just logs), so online brute-force also feasible: 10,000 executions of the shim.

Effect: the "verrou" advertised as protecting GPU write operations is bypassable by any non-root local user (e.g. the `turbo` account) — they simply recover the PIN offline in seconds, then set `JARVIS_GPU_UNLOCK=<pin>` and issue any state-changing `nvidia-smi` command (compute-mode PROHIBITED, `-pl` outside 70–135 W, `-r` GPU reset, MIG, drain, etc.).

Also noteworthy but included above (same root cause): the fact that `check_code` uses non-constant-time `[ "$computed" = "$STORED" ]` is moot because the attacker doesn't need the shim at all once the hash file is readable.