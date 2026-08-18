#!/usr/bin/env bash
# cluster-acces.sh — Point d'accès unique au parc JARVIS.
# Injecté le 2026-08-14 sur M6 et M4. Relevé sur machines vivantes, pas déduit.
#
#   cluster-acces.sh            → carte du parc
#   cluster-acces.sh ssh m4     → console sur une machine
#   cluster-acces.sh anydesk m4 → bureau distant
#   cluster-acces.sh chrome     → profils Chrome disponibles
#   cluster-acces.sh test       → qui répond, maintenant

set -uo pipefail

# nom | ssh | anydesk | tailscale | cable | role
NOEUDS=(
  "m6|m6|1549231391|100.112.114.32|10.42.0.230|CALCUL — LM Studio permanent, board, bibliothèque vivante, RTX 2060+3080"
  "m4|m4|1787682419|-|10.42.0.1|PRODUCTION — interface, binôme de M6, RTX 3050 4 Go"
  "rem|rem|1978445906|100.113.121.61|-|Portable de Rémi"
  "remjarvis-server|remjarvis-server|-|100.124.69.1|-|Serveur tour de Rémi"
  "rem-s25|-|-|100.121.27.80|-|Android de Rémi"
)

c()  { printf '\033[1;36m%s\033[0m\n' "$*"; }
ok() { printf '  \033[32m●\033[0m %s\n' "$*"; }
ko() { printf '  \033[31m○\033[0m %s\n' "$*"; }

carte() {
  c "── PARC JARVIS ──"
  for n in "${NOEUDS[@]}"; do
    IFS='|' read -r nom sshn ad ts cable role <<< "$n"
    printf '\n\033[1m%s\033[0m — %s\n' "$nom" "$role"
    [ "$sshn"  != "-" ] && echo "   ssh       ssh $sshn"
    [ "$ad"    != "-" ] && echo "   anydesk   $ad"
    [ "$ts"    != "-" ] && echo "   tailscale $ts"
    [ "$cable" != "-" ] && echo "   câble     $cable"
  done
  echo
  c "── LLM ──"
  echo "   M6 sert tout le parc : http://10.42.0.230:1234/v1"
  echo "   Appel sans reasoning runaway : bash ~/jarvis/scripts/qwen-nothink.sh 'prompt'"
}

test_parc() {
  c "── QUI RÉPOND ──"
  for n in "${NOEUDS[@]}"; do
    IFS='|' read -r nom sshn ad ts cable role <<< "$n"
    cible="$cable"; [ "$cible" = "-" ] && cible="$ts"
    [ "$cible" = "-" ] && continue
    if ping -c1 -W2 "$cible" >/dev/null 2>&1; then ok "$nom ($cible)"; else ko "$nom ($cible) injoignable"; fi
  done
  echo
  c "── LM STUDIO M6 ──"
  if curl -s -m 5 http://10.42.0.230:1234/v1/models >/dev/null 2>&1; then
    ok "en ligne — $(curl -s -m 5 http://10.42.0.230:1234/v1/models | grep -c '"id"') modèles"
  else ko "injoignable"; fi
}

chrome() {
  c "── PROFILS CHROME (local) ──"
  for d in "$HOME/.config/google-chrome/Default" "$HOME/.config/google-chrome/Profile "*; do
    [ -d "$d" ] || continue
    nom=$(python3 -c "import json;print(json.load(open('$d/Preferences')).get('profile',{}).get('name','?'))" 2>/dev/null)
    printf '   %-12s %s\n' "$(basename "$d")" "${nom:-?}"
    printf '                google-chrome --profile-directory="%s"\n' "$(basename "$d")"
  done
}

resoudre() {
  for n in "${NOEUDS[@]}"; do
    IFS='|' read -r nom sshn ad ts cable role <<< "$n"
    [ "$nom" = "$1" ] && { echo "$sshn|$ad"; return 0; }
  done
  echo "|"; return 1
}

case "${1:-carte}" in
  carte|"")  carte ;;
  test)      test_parc ;;
  chrome)    chrome ;;
  ssh)       IFS='|' read -r s a <<< "$(resoudre "${2:-}")"
             [ -z "$s" ] || [ "$s" = "-" ] && { echo "Pas de SSH pour '${2:-}'"; exit 1; }
             exec ssh "$s" ;;
  anydesk)   IFS='|' read -r s a <<< "$(resoudre "${2:-}")"
             [ -z "$a" ] || [ "$a" = "-" ] && { echo "Pas d'AnyDesk pour '${2:-}'"; exit 1; }
             exec anydesk "$a" ;;
  *)         echo "Usage: $(basename "$0") [carte|test|chrome|ssh <noeud>|anydesk <noeud>]"; exit 1 ;;
esac
