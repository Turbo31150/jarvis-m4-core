#!/usr/bin/env bash
# Pont USB Lumenflow : maintient `adb reverse` pour que le tél joigne le backend
# (8788 traduction/STT/TTS, 9742/9743 whisper) via le câble. Idempotent, re-établit
# automatiquement à chaque reconnexion du téléphone.
PORTS="8788 9742 9743"
export ADB_SERVER_SOCKET=tcp:127.0.0.1:5037

pick_device() {
  adb devices 2>/dev/null | awk -F'\t' '$2=="device"{print $1}' | grep -v '^emulator-' | head -1
}

adb start-server >/dev/null 2>&1
while true; do
  D=$(pick_device)
  if [ -n "$D" ]; then
    for p in $PORTS; do
      adb -s "$D" reverse tcp:$p tcp:$p >/dev/null 2>&1
    done
  fi
  sleep 5
done
