#!/usr/bin/env bash
# Applique la propriete des services JARVIS declaree dans
# infra/config/cluster/service-ownership.json.
#
# Pourquoi : le 2026-08-03, 18 services tournaient en double sur M1 et M6 avec
# des unites identiques bindant les memes ports sur 0.0.0.0. Ce script fige
# l'etat de demarrage pour que la situation ne revienne pas a chaque boot.
#
# Idempotent. Ne fait rien par defaut : il faut --apply pour ecrire.
#
#   apply-service-ownership.sh              # dry-run : montre les ecarts
#   apply-service-ownership.sh --apply      # enable/disable au boot selon le manifeste
#   apply-service-ownership.sh --apply --stop-now   # + arrete les services non proprietaires
#
set -uo pipefail

MANIFEST="${JARVIS_OWNERSHIP_MANIFEST:-$HOME/jarvis/infra/config/cluster/service-ownership.json}"
NODE="${JARVIS_NODE_ID:-$(hostname | tr '[:lower:]' '[:upper:]')}"
APPLY=0
STOP_NOW=0
for a in "$@"; do
  case "$a" in
    --apply)    APPLY=1 ;;
    --stop-now) STOP_NOW=1 ;;
    -h|--help)  sed -n '2,16p' "$0"; exit 0 ;;
    *) echo "option inconnue : $a" >&2; exit 2 ;;
  esac
done

[[ -r "$MANIFEST" ]] || { echo "manifeste introuvable : $MANIFEST" >&2; exit 1; }

echo "noeud      : $NODE"
echo "manifeste  : $MANIFEST"
echo "mode       : $( ((APPLY)) && echo "APPLY$( ((STOP_NOW)) && echo ' +stop-now')" || echo 'dry-run (aucune ecriture)' )"
echo

# Le manifeste est la seule source de verite : on en sort des lignes "service<TAB>owner".
mapfile -t ROWS < <(python3 - "$MANIFEST" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
for name, spec in d["services"].items():
    print(f"{name}\t{spec['owner']}\t{spec.get('boot','auto')}")
PY
) || { echo "manifeste illisible (JSON invalide ?)" >&2; exit 1; }

changed=0 skipped=0 absent=0
printf '%-28s %-7s %-10s %s\n' SERVICE PROPR. ACTUEL ACTION
printf '%-28s %-7s %-10s %s\n' ---------------------------- ------- ---------- ------
for row in "${ROWS[@]}"; do
  IFS=$'\t' read -r svc owner boot <<<"$row"
  unit="$svc.service"

  # Un service absent du noeud n'est pas une anomalie : chaque machine n'a pas tout.
  if ! systemctl --user cat "$unit" >/dev/null 2>&1; then
    absent=$((absent+1)); continue
  fi

  # is-enabled sort en code 1 quand l'unite est 'disabled' : on lit la sortie,
  # jamais le code de retour, sinon tout service desactive passerait pour 'unknown'.
  cur=$(systemctl --user is-enabled "$unit" 2>/dev/null | head -1)
  [[ -z "$cur" ]] && cur=unknown

  # 'local' = legitime partout : on n'y touche pas, quel que soit l'etat.
  if [[ "$owner" == "local" ]]; then
    printf '%-28s %-7s %-10s %s\n' "$svc" local "$cur" "laisse tel quel"
    skipped=$((skipped+1)); continue
  fi

  if [[ "$owner" == "$NODE" ]]; then
    # boot=manuel : le service etait deliberement disabled au boot partout.
    # On ne le reveille pas — on se contente de garantir l'unicite ailleurs.
    if [[ "$boot" == "manuel" ]]; then
      printf '%-28s %-7s %-10s %s\n' "$svc" "$owner" "$cur" "proprietaire, demarrage manuel (non force)"
      skipped=$((skipped+1)); continue
    fi
    want=enable
  else
    want=disable
  fi

  # 'indirect' et 'static' ne se pilotent pas par enable/disable : on ne force pas.
  if [[ "$cur" == "indirect" || "$cur" == "static" ]]; then
    printf '%-28s %-7s %-10s %s\n' "$svc" "$owner" "$cur" "non pilotable (ignore)"
    skipped=$((skipped+1)); continue
  fi

  if { [[ "$want" == enable ]] && [[ "$cur" == enabled ]]; } ||
     { [[ "$want" == disable ]] && [[ "$cur" == disabled ]]; }; then
    printf '%-28s %-7s %-10s %s\n' "$svc" "$owner" "$cur" "conforme"
    continue
  fi

  act="$want au boot"
  ((STOP_NOW)) && [[ "$want" == disable ]] && act="$act + arret immediat"
  printf '%-28s %-7s %-10s %s\n' "$svc" "$owner" "$cur" ">>> $act"
  changed=$((changed+1))

  if ((APPLY)); then
    if [[ "$want" == enable ]]; then
      systemctl --user enable "$unit" >/dev/null 2>&1 || echo "    echec enable $unit" >&2
    else
      systemctl --user disable "$unit" >/dev/null 2>&1 || echo "    echec disable $unit" >&2
      ((STOP_NOW)) && { systemctl --user stop "$unit" >/dev/null 2>&1 || echo "    echec stop $unit" >&2; }
    fi
  fi
done

echo
echo "ecarts : $changed | laisses tels quels : $skipped | absents de ce noeud : $absent"

# --- Doublons entre scopes systemd ------------------------------------------
# Decouvert le 2026-08-03 : jarvis-chat-proxy existait en unite utilisateur ET
# en unite systeme. L'utilisateur detenait 0.0.0.0:18800, la systeme bouclait en
# crash sur EADDRINUSE en declenchant un failure-handler a chaque tentative.
# Convention du cluster : le scope UTILISATEUR est canonique ; toute unite
# systeme homonyme est un reliquat et doit rester eteinte.
echo
echo "--- jumeaux en scope systeme (doivent rester inactive/disabled)"
scope_bad=0
for row in "${ROWS[@]}"; do
  IFS=$'\t' read -r svc owner boot <<<"$row"
  unit="$svc.service"
  systemctl --user cat "$unit" >/dev/null 2>&1 || continue
  systemctl        cat "$unit" >/dev/null 2>&1 || continue

  sa=$(systemctl is-active  "$unit" 2>/dev/null | head -1)
  se=$(systemctl is-enabled "$unit" 2>/dev/null | head -1)
  if [[ "$sa" == "inactive" || "$sa" == "failed" ]] && [[ "$se" == "disabled" ]]; then
    [[ "$sa" == "failed" ]] && printf '    %-26s systeme=failed (residu) — reset conseille\n' "$svc" \
                            || printf '    %-26s systeme dormant, conforme\n' "$svc"
    continue
  fi

  printf '    %-26s >>> systeme=%s/%s ALORS QUE utilisateur existe : conflit de port possible\n' "$svc" "$sa" "$se"
  scope_bad=$((scope_bad+1))
  if ((APPLY)); then
    if sudo -n true 2>/dev/null; then
      sudo -n systemctl disable --now "$unit" >/dev/null 2>&1 && echo "        -> unite systeme desactivee et arretee"
      sudo -n systemctl reset-failed "$unit" >/dev/null 2>&1
    else
      echo "        -> sudo non disponible sans mot de passe ; a faire a la main :"
      echo "           sudo systemctl disable --now $unit"
    fi
  fi
done
((scope_bad)) || echo "    aucun conflit de scope"
if ((changed)) && ! ((APPLY)); then
  echo
  echo "Rien n'a ete modifie. Pour appliquer :"
  echo "  $0 --apply             # etat de boot seulement (les services en cours continuent)"
  echo "  $0 --apply --stop-now  # + arrete tout de suite les services non proprietaires"
fi
exit 0
