#!/usr/bin/env bash
# [Bluetooth/ADB] Trackpad S9 -> curseur PC via ADB-over-Bluetooth-PAN (sans wifi).
#
# DEUX topologies possibles (les deux echouent sur CE S9 LineageOS 20, cf. plus bas) :
#
#   A) S9=NAP / PC=PANU  (defaut, --s9-nap) :
#      le S9 partage un reseau via Bluetooth (NAP), le PC s'y connecte en client
#      PANU -> interface bnep0 cote PC -> adb connect <ip S9>:5555.
#      -> ECHEC : la ROM n'a pas de BT tethering (mTetherOn=false, pas de
#         config_tether_bluetooth_regexs). Le S9 refuse d'agir en serveur NAP.
#
#   B) PC=NAP / S9=PANU  (--pc-nap, teste 2026-07-15, chemin de code inverse) :
#      le PC monte un serveur NAP (pont pan0 + dnsmasq), le S9 doit se connecter
#      en client PANU en cochant "Acces a Internet" dans les reglages BT du device.
#      -> ECHEC AUSSI : la page detail du device (turbo-MS-7C56, type "Ordinateur")
#         de cette build LineageOS 20 NE REND PAS la case "Acces a Internet" /
#         "Internet access" (profils affiches : Appels / Multimedia / Contacts /
#         Son spatial uniquement). Le PanService cote S9 connait pourtant le PC
#         (objet BluetoothPanDevice cree, mPanIfName=bt-pan) mais la politique PAN
#         est FORBIDDEN (=-1) et aucun appel user-space (cmd bluetooth_manager
#         n'expose que enable/disable/wait-for-state) ne permet d'invoquer
#         PanService.connect() sans root. Meme NAP PC decouvert + reconnexion BT
#         forcee ne declenche AUCUN PANU automatique (0 bnep, 0 bail DHCP).
#
#   => CONCLUSION : sans root ni autre ROM, aucun L3 Bluetooth n'est possible dans
#      un sens comme dans l'autre sur ce telephone. Utiliser USB (deja OK) ou
#      USB-tethering RNDIS. Le mode B ci-dessous est fonctionnel cote PC (serveur
#      NAP OK, verifie) et echoue proprement en signalant la case manquante.
#
# PREREQUIS (une seule fois, EN USB, pour le chemin adb-over-PAN si un jour L3 up) :
#   adb -s <serial-usb> tcpip 5555      # ouvre le port adb TCP sur le S9
#   (le S9 doit rester appaire+trusted avec ce PC : deja fait ici)
#
# ATTENTION — limite connue sur CE S9 :
#   La ROM LineageOS 20 (SM-G960F, starlte) N'EXPOSE PAS le partage de connexion
#   Bluetooth (ecran Tethering = USB + hotspot Wi-Fi uniquement, aucun
#   config_tether_bluetooth_regexs). Le NAP accepte le lien BNEP puis le coupe
#   aussitot ("Network service is connected" -> "disconnected") et aucune
#   interface bnep0 n'est creee. Sans root (SELinux bloque, pas de su) on ne peut
#   pas forcer le service PAN d'Android.
#   => Ce script est FONCTIONNEL et pret, mais il echouera proprement sur ce
#      telephone tant que le BT tethering n'est pas disponible (autre ROM /
#      module PAN). Il detecte le cas et le signale.
#
# Usage :
#   ./s9-trackpad-bt.sh [MAC_BT] [--serial-usb SER] [--ip IP_S9] [args-trackpad...]
#     -> topologie A : S9=NAP / PC=PANU (defaut)
#   ./s9-trackpad-bt.sh --pc-nap
#     -> topologie B : PC=NAP / S9=PANU (chemin inverse, teste 2026-07-15)
#        monte le serveur NAP cote PC (pont pan0 192.168.44.1/24 + dnsmasq
#        192.168.44.10-50), pilote le S9 en adb pour cocher "Acces a Internet",
#        detecte l'absence de la case (echec propre) et nettoie tout.
# Ex : ./s9-trackpad-bt.sh E0:D0:83:BC:4E:E6 --gain 0.9

set -uo pipefail

MAC="${1:-E0:D0:83:BC:4E:E6}"           # MAC Bluetooth du S9 (bluetoothctl devices)
[ "${1:-}" ] && [ "${1:0:2}" != "--" ] && shift

SERIAL_USB="4357514238453498"           # serial adb USB du S9 (pour le tcpip initial)
IP_S9=""                                 # laisser vide = auto-detection depuis bnep0
ADB_PORT=5555
PC_NAP=0                                  # --pc-nap => topologie B (PC serveur NAP)
PAN_BR="pan0"                             # pont reseau Bluetooth cote PC
PAN_IP="192.168.44.1"                    # IP du PC sur le PAN (passerelle S9)
PAN_CIDR="24"
DRIVER="$(dirname "$(readlink -f "$0")")/s9-trackpad.py"

# --- parse options simples, le reste est passe tel quel au driver python ---
PASS=()
while [ $# -gt 0 ]; do
  case "$1" in
    --serial-usb) SERIAL_USB="$2"; shift 2;;
    --ip)         IP_S9="$2"; shift 2;;
    --port)       ADB_PORT="$2"; shift 2;;
    --pc-nap)     PC_NAP=1; shift;;
    *)            PASS+=("$1"); shift;;
  esac
done

log(){ echo "[Bluetooth/ADB] $*" >&2; }
die(){ log "ERREUR: $*"; exit 1; }
# Privilège : sudo sans mot de passe si NOPASSWD configuré (recommandé), sinon
# prompt interactif. JAMAIS de mot de passe en dur dans le script.
# NOPASSWD (une fois) : sudo tee /etc/sudoers.d/s9-trackpad <<'EOF'
#   turbo ALL=(root) NOPASSWD: /usr/sbin/ip, /usr/bin/dnsmasq, /usr/bin/bt-network, /usr/sbin/sysctl, /usr/bin/kill, /bin/kill
# EOF
S(){ sudo -n "$@" 2>/dev/null || sudo -p 'sudo (%u@%h) mot de passe : ' "$@"; }

# =====================================================================
# Topologie B : PC=NAP serveur / S9=PANU client  (--pc-nap)
# =====================================================================
NAP_PID=""; DNSMASQ_PID=""; DNSMASQ_CONF="/tmp/s9-pan-dnsmasq.conf"
pc_nap_cleanup(){
  log "nettoyage serveur NAP PC..."
  [ -n "$NAP_PID" ] && S kill "$NAP_PID" 2>/dev/null
  pkill -f "bt-network -s nap $PAN_BR" 2>/dev/null
  [ -n "$DNSMASQ_PID" ] && S kill "$DNSMASQ_PID" 2>/dev/null
  [ -f /tmp/s9-pan-dnsmasq.pid ] && S kill "$(cat /tmp/s9-pan-dnsmasq.pid 2>/dev/null)" 2>/dev/null
  S ip link set "$PAN_BR" down 2>/dev/null
  S ip link del "$PAN_BR" 2>/dev/null
  rm -f "$DNSMASQ_CONF" /tmp/s9-pan-dnsmasq.pid 2>/dev/null
}

run_pc_nap(){
  trap pc_nap_cleanup EXIT INT TERM
  command -v dnsmasq >/dev/null || die "dnsmasq manquant (apt install dnsmasq-base)"

  # 1) pont pan0 + IP (non destructif : interface dediee, ne touche pas au reseau PC)
  S ip link del "$PAN_BR" 2>/dev/null
  S ip link add name "$PAN_BR" type bridge   || die "creation pont $PAN_BR"
  S ip addr add "$PAN_IP/$PAN_CIDR" dev "$PAN_BR"
  S ip link set "$PAN_BR" up
  log "pont $PAN_BR up sur $PAN_IP/$PAN_CIDR"

  # 2) DHCP leger scope UNIQUEMENT a pan0 (bind-interfaces => ne touche rien d'autre)
  cat > "$DNSMASQ_CONF" <<EOF
interface=$PAN_BR
bind-interfaces
except-interface=lo
dhcp-range=192.168.44.10,192.168.44.50,255.255.255.0,1h
dhcp-option=3,$PAN_IP
dhcp-option=6,$PAN_IP
port=0
EOF
  S dnsmasq --conf-file="$DNSMASQ_CONF" --pid-file=/tmp/s9-pan-dnsmasq.pid
  sleep 1
  DNSMASQ_PID="$(cat /tmp/s9-pan-dnsmasq.pid 2>/dev/null)"
  log "dnsmasq DHCP 192.168.44.10-50 sur $PAN_BR (pid $DNSMASQ_PID)"

  # 3) serveur NAP bluez ponte sur pan0
  S bash -c "bt-network -s nap $PAN_BR >/tmp/s9-pan-server.log 2>&1 &"
  sleep 2
  grep -qi "registered" /tmp/s9-pan-server.log \
    && log "serveur NAP enregistre (org.bluez.NetworkServer1)" \
    || die "echec enregistrement NAP : $(cat /tmp/s9-pan-server.log)"
  NAP_PID="$(pgrep -f "bt-network -s nap $PAN_BR" | head -1)"
  S sysctl -w net.ipv4.ip_forward=1 >/dev/null 2>&1

  # 4) cote S9 : ouvrir les reglages BT du device PC pour cocher "Acces a Internet"
  local PC_BT; PC_BT=$(bluetoothctl show 2>/dev/null | grep -oE '([0-9A-F]{2}:){5}[0-9A-F]{2}' | head -1)
  log "PC BT=$PC_BT — le S9 doit maintenant cocher 'Acces a Internet' (PANU)."
  if adb -s "$SERIAL_USB" get-state >/dev/null 2>&1; then
    adb -s "$SERIAL_USB" shell am start -a android.settings.BLUETOOTH_SETTINGS >/dev/null 2>&1
    sleep 2
    # detecter si la case Internet-access existe sur la page detail du device
    adb -s "$SERIAL_USB" shell uiautomator dump /sdcard/_pan.xml >/dev/null 2>&1
    adb -s "$SERIAL_USB" pull /sdcard/_pan.xml /tmp/s9-pan-ui.xml >/dev/null 2>&1
    if grep -qiE 'Acc[eè]s [aà] Internet|Internet access' /tmp/s9-pan-ui.xml 2>/dev/null; then
      log "case 'Acces a Internet' presente -> la cocher manuellement sur le S9."
    else
      log "case 'Acces a Internet' ABSENTE de la build LineageOS 20 (profils: Appels/Media/Contacts/Son)."
    fi
  fi

  # 5) attendre qu'un bnep s'attache a pan0 (S9 devenu PANU) — max 15 s
  local m="" i
  for i in $(seq 1 8); do
    m=$(ip -o link show master "$PAN_BR" 2>/dev/null | grep -oE 'bnep[0-9]+' | head -1)
    [ -n "$m" ] && break
    sleep 2
  done
  if [ -z "$m" ]; then
    log "ECHEC topologie B : aucun bnep sur $PAN_BR, aucun bail DHCP -> le S9 n'a pas"
    log "  initie PANU (case absente, politique PAN=FORBIDDEN, pas de root). L3 BT impossible."
    return 1
  fi

  # 6) L3 etabli : le S9 a une IP dans 192.168.44.x, le PC est 192.168.44.1
  log "SUCCES : $m attache a $PAN_BR. Le S9 est en PANU."
  local S9IP
  S9IP=$(awk '/192.168.44/{print $3}' /var/lib/misc/dnsmasq.leases 2>/dev/null | head -1)
  log "IP S9 sur le PAN : ${S9IP:-<voir bail>}  ·  IP PC (a mettre dans l'app) : $PAN_IP:8770"
  log "Le serveur Phone Mouse tourne deja (systemd phone-mouse-server.service, port 8770)."
  log "Dans l'app : champ IP -> $PAN_IP  (port 8770). Ne PAS fermer ce script (garde le NAP up)."
  # garder le serveur NAP vivant tant que l'utilisateur s'en sert
  wait "$NAP_PID" 2>/dev/null
  return 0
}

if [ "$PC_NAP" = "1" ]; then
  run_pc_nap
  exit $?
fi

command -v bt-network >/dev/null || die "bt-network manquant (apt install bluez-tools)"
command -v adb        >/dev/null || die "adb manquant"

# 1) s'assurer que adb tcpip 5555 est actif sur le S9 (necessite USB une fois)
ensure_tcpip(){
  # si un S9 est branche en USB, (re)active le mode TCP
  if adb -s "$SERIAL_USB" get-state >/dev/null 2>&1; then
    local p; p=$(adb -s "$SERIAL_USB" shell getprop service.adb.tcp.port 2>/dev/null | tr -d '\r')
    if [ "$p" != "$ADB_PORT" ]; then
      log "activation adb tcpip $ADB_PORT via USB..."
      adb -s "$SERIAL_USB" tcpip "$ADB_PORT" >/dev/null 2>&1
      sleep 2
    else
      log "adb tcpip $ADB_PORT deja actif."
    fi
  else
    log "S9 non branche en USB -> on suppose adb tcpip $ADB_PORT deja active precedemment."
  fi
}

# 2) appairage/connexion BT + montee du PAN (PC client PANU -> NAP du S9)
BTNET_PID=""
bring_up_pan(){
  log "appairage/connexion BT $MAC..."
  bluetoothctl connect "$MAC" >/dev/null 2>&1 || true

  log "connexion PANU vers le NAP du S9..."
  # bt-network reste au premier plan tant que le PAN est monte -> lance en fond
  bt-network -c "$MAC" nap >/tmp/s9-trackpad-btnet.log 2>&1 &
  BTNET_PID=$!

  # attendre l'apparition de bnep0 (max 12 s)
  local iface="" i
  for i in $(seq 1 12); do
    iface=$(ip -o link show 2>/dev/null | grep -oE 'bnep[0-9]+' | head -1)
    [ -n "$iface" ] && break
    # si bt-network est deja mort, la ROM refuse le PAN
    kill -0 "$BTNET_PID" 2>/dev/null || break
    sleep 1
  done

  if [ -z "$iface" ]; then
    log "echec: aucune interface bnep0. Le S9 a coupe le PAN (BT tethering indispo sur la ROM)."
    log "log bt-network: $(tr '\n' ' ' </tmp/s9-trackpad-btnet.log)"
    kill "$BTNET_PID" 2>/dev/null
    return 1
  fi
  log "interface PAN active: $iface"

  # obtenir une IP L3 (le S9 en NAP fait DHCP, typiquement 192.168.44.x)
  if ! ip -4 addr show "$iface" 2>/dev/null | grep -q 'inet '; then
    log "DHCP sur $iface..."
    sudo -n dhclient -1 -timeout 8 "$iface" 2>/dev/null \
      || sudo -n dhcpcd -t 8 "$iface" 2>/dev/null \
      || log "avert: pas de bail DHCP auto (sudo requis ?)."
  fi
  BNEP_IFACE="$iface"
  return 0
}

# 3) determiner l'IP du S9 sur le PAN
resolve_ip(){
  [ -n "$IP_S9" ] && { echo "$IP_S9"; return; }
  # passerelle sur bnep0 = IP du S9 (il est routeur NAP)
  local gw
  gw=$(ip route show dev "${BNEP_IFACE:-bnep0}" 2>/dev/null | awk '/default|via/{print $3; exit}')
  [ -z "$gw" ] && gw=$(ip -4 addr show "${BNEP_IFACE:-bnep0}" 2>/dev/null \
        | awk '/inet /{split($2,a,"/"); n=a[1]; sub(/[0-9]+$/,"1",n); print n; exit}')
  echo "$gw"
}

cleanup(){ [ -n "$BTNET_PID" ] && kill "$BTNET_PID" 2>/dev/null; }
trap cleanup EXIT INT TERM

# ---- deroulement ----
ensure_tcpip
if ! bring_up_pan; then
  cat >&2 <<'EOF'
[Bluetooth/ADB] BT-PAN indisponible sur ce S9 (ROM sans BT tethering).
  Alternatives fonctionnelles sans wifi :
   - USB (deja OK)      : python3 s9-trackpad.py
   - USB tethering RNDIS: adb connect 192.168.67.24:5555 puis
                          python3 s9-trackpad.py 192.168.67.24:5555
EOF
  exit 1
fi

IP=$(resolve_ip)
[ -z "$IP" ] && die "IP du S9 introuvable sur le PAN."
log "S9 sur le PAN: $IP -> adb connect $IP:$ADB_PORT"

adb connect "$IP:$ADB_PORT" >/dev/null 2>&1
sleep 1
adb -s "$IP:$ADB_PORT" get-state >/dev/null 2>&1 \
  || die "adb connect $IP:$ADB_PORT a echoue (adb tcpip pas fait en USB ?)."

log "trackpad Bluetooth actif sur $IP:$ADB_PORT."
exec python3 "$DRIVER" "$IP:$ADB_PORT" "${PASS[@]}"
