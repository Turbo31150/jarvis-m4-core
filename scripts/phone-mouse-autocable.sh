#!/usr/bin/env bash
# phone-mouse-autocable.sh — AUTO-CÂBLAGE : branchement USB du S9 => tout se connecte seul.
# Déclenché par règle udev (add) OU boucle. Idempotent.
#   1. attend l'autorisation adb, 2. adb reverse tcp:8770, 3. lance l'app phonemouse,
#   4. garantit le service serveur uinput actif.
set -uo pipefail
PKG="com.jarvis.phonemouse"
ACT="$PKG/.MainActivity"
LOG="/tmp/phone-mouse-autocable.log"
log(){ echo "[$(date '+%F %T')] $*" >> "$LOG"; }

export ANDROID_ADB_SERVER_PORT="${ANDROID_ADB_SERVER_PORT:-5037}"

# 1. serveur uinput up
systemctl --user start phone-mouse.service 2>/dev/null

# 2. attendre un device adb autorisé (max 20s)
for i in $(seq 1 20); do
  state=$(adb get-state 2>/dev/null)
  [ "$state" = "device" ] && break
  sleep 1
done
[ "$(adb get-state 2>/dev/null)" != "device" ] && { log "aucun device adb autorisé"; exit 0; }

SER=$(adb get-serialno 2>/dev/null)
log "S9 détecté ($SER) — câblage auto"

# 3. reverse du port (USB => l'app vise 127.0.0.1:8770)
adb reverse tcp:8770 tcp:8770 2>>"$LOG" && log "adb reverse 8770 OK"

# 4. lancer l'app (si installée)
if adb shell pm list packages 2>/dev/null | grep -q "$PKG"; then
  adb shell am start -n "$ACT" >/dev/null 2>&1 && log "app lancée ($ACT)"
else
  log "APK $PKG non installée sur le S9 (à installer une fois: adb install phonemouse.apk)"
fi
log "câblage terminé"
