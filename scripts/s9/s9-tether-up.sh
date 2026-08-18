#!/usr/bin/env bash
# s9-tether-up.sh — active le partage de connexion USB du Galaxy S9 depuis M1.
# Le tethering Android ne survit pas au débranchement : ce script le réarme.
# Idempotent, silencieux, exit 0 si le S9 est absent (ne casse jamais le boot).
set -uo pipefail

S9_SERIAL="${S9_SERIAL:-4357514238453498}"
ADB="${ADB:-/usr/bin/adb}"
LOG_TAG="s9-tether"

log() { logger -t "$LOG_TAG" -- "$*"; echo "[$(date '+%F %T')] $*"; }

[ -x "$ADB" ] || { log "adb absent ($ADB)"; exit 0; }

# Le serveur adb tourne sous l'utilisateur propriétaire des clés (~/.android/adbkey).
# En service systemd root, on pointe explicitement le HOME de turbo.
export HOME="${ADB_HOME:-/home/pamerys}"

# Attendre que le téléphone soit visible (branchement à chaud : jusqu'à 20 s).
for _ in $(seq 1 20); do
  state=$("$ADB" -s "$S9_SERIAL" get-state 2>/dev/null)
  [ "$state" = "device" ] && break
  sleep 1
done
[ "${state:-}" = "device" ] || { log "S9 $S9_SERIAL non disponible en adb (state=${state:-none})"; exit 0; }

# Idempotence stricte : si rndis0 porte déjà une IP, le partage tourne. Le relancer
# ferait renuméroter le sous-réseau (Android 13 le randomise) et casserait le bail
# DHCP de M1 — exactement au moment où on a besoin du secours. On sort.
if "$ADB" -s "$S9_SERIAL" shell ip -br addr show rndis0 2>/dev/null | grep -qE 'inet |[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+'; then
  exit 0
fi

# La fonction USB doit exposer rndis ET garder adb (sinon on se coupe la branche).
usbcfg=$("$ADB" -s "$S9_SERIAL" shell getprop sys.usb.state 2>/dev/null | tr -d '\r')
if [[ "$usbcfg" != *rndis* ]]; then
  log "fonction USB=$usbcfg → passage à rndis,adb"
  "$ADB" -s "$S9_SERIAL" shell svc usb setFunctions rndis,adb >/dev/null 2>&1
  sleep 4
fi

# ITetheringConnector.setUsbTethering(enable=true, callerPkg, attributionTag, listener)
# Android 13 n'expose pas `cmd tethering` : l'appel binder direct est la voie fiable.
"$ADB" -s "$S9_SERIAL" shell service call tethering 3 i32 1 s16 com.android.shell s16 com.android.shell >/dev/null 2>&1

# Vérifier que l'interface rndis0 du téléphone a bien pris une IP (= DHCP servi).
for _ in $(seq 1 10); do
  if "$ADB" -s "$S9_SERIAL" shell ip -br addr show rndis0 2>/dev/null | grep -q 'inet\? [0-9]'; then
    log "tethering USB actif"
    exit 0
  fi
  sleep 1
done

log "tethering demandé mais rndis0 sans IP côté S9"
exit 0
