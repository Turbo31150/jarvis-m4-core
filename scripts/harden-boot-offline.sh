#!/usr/bin/env bash
# harden-boot-offline.sh — Met une machine JARVIS en état "production / boot sans câble".
# Idempotent. DRY par défaut ; --apply pour exécuter. Réutilise la préparation existante.
# Réf : CDC_LOADBALANCER.md §7 (ENF1/ENF2/ENF3) — FEEDBACK 2026-06-07.
set -uo pipefail

APPLY=0; [[ "${1:-}" == "--apply" ]] && APPLY=1
NODE="$(hostname)"
say(){ printf '  %s\n' "$*"; }
hdr(){ printf '\n\033[1m== %s ==\033[0m\n' "$*"; }
run(){ if (( APPLY )); then eval "$@"; else echo "    [DRY] $*"; fi; }

echo "### HARDEN BOOT-OFFLINE — node=$NODE — mode=$([[ $APPLY == 1 ]] && echo APPLY || echo DRY)"

# --- ENF1 : désactiver l'attente réseau bloquante au boot ---
hdr "ENF1 wait-online"
for u in systemd-networkd-wait-online.service NetworkManager-wait-online.service; do
  state=$(systemctl is-enabled "$u" 2>/dev/null || echo absent)
  if [[ "$state" == "enabled" ]]; then
    say "$u = enabled → disable"; run "sudo systemctl disable $u"
  else say "$u = $state (OK)"; fi
done

# --- ENF1 : fstab — tout montage réseau doit avoir nofail ---
hdr "ENF1 fstab montages réseau"
bad=$(grep -nE 'nfs|cifs|sshfs|fuse|//|:/' /etc/fstab 2>/dev/null | grep -vE '^\s*#' | grep -v nofail || true)
if [[ -n "$bad" ]]; then
  say "Montage réseau SANS nofail détecté (risque hang boot) :"; echo "$bad" | sed 's/^/      /'
  say "→ ajouter ',nofail,_netdev' manuellement (édition fstab non automatisée par sécurité)"
else say "Aucun montage réseau bloquant (OK)"; fi

# --- ENF1 : services LAN en Requires=network-online (devrait être Wants=) ---
hdr "ENF1 services Requires=network-online"
mapfile -t reqs < <(grep -rlE 'Requires=network-online' /etc/systemd/system/ "$HOME/.config/systemd/user/" 2>/dev/null)
if (( ${#reqs[@]} )); then
  for f in "${reqs[@]}"; do
    say "Requires= → Wants= : $f"
    run "sed -i 's/Requires=network-online.target/Wants=network-online.target/' '$f'"
  done
  run "systemctl daemon-reload || true; systemctl --user daemon-reload || true"
else say "Aucun service en Requires= dur (OK)"; fi

# --- ENF2 : route LAN prioritaire sur tethering USB ---
hdr "ENF2 route default (LAN > tethering)"
defroute=$(ip route show default | head -1)
say "default actuel : ${defroute:-<aucune>}"
if echo "$defroute" | grep -q '192.168.42'; then
  say "⚠️ default via USB tethering → bascule LAN requise"
  lan_if=$(ip -br addr show | awk '/192\.168\.1\./{print $1; exit}')
  [[ -n "$lan_if" ]] && run "sudo ip route replace default via 192.168.1.1 dev $lan_if metric 50"
else say "default sur LAN (OK)"; fi

# --- ENF3 : sonde offline (lan_ok/wan_ok) pour le report ---
hdr "ENF3 sonde réseau (pour /jarvis/report)"
lan_ok=$(ping -c1 -W1 192.168.1.1 >/dev/null 2>&1 && echo true || echo false)
wan_ok=$(ping -c1 -W1 8.8.8.8   >/dev/null 2>&1 && echo true || echo false)
say "lan_ok=$lan_ok  wan_ok=$wan_ok"

echo; echo "### FIN — node=$NODE — $([[ $APPLY == 1 ]] && echo 'APPLIQUÉ' || echo 'DRY (relancer avec --apply)')"
