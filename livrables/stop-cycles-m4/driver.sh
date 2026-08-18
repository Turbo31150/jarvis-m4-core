#!/usr/bin/env bash
# stop-cycles-m4 — coupe et désactive les boucles d'inférence autonomes qui
# saturent le M4 (RAM + thermique). 0-token, fail-safe, idempotent.
# Interdit sur M4 seul : cf. mémoire m4-dispatch-flux-ondemand / surchauffe 95-100°C.
# Usage :  bash driver.sh            (coupe + désactive, montre RAM avant/après)
#          bash driver.sh --dry      (montre ce qui tourne, ne tue rien)
set -uo pipefail

DRY=0; [ "${1:-}" = "--dry" ] && DRY=1

# Boucles connues + motifs génériques de boucles autonomes (jamais les apps user).
PATTERNS=(
  'board_continuous_loop'
  'swarm-auto-connect'
  'cowork-loop'
  'cowork-dispatcher'
  'domino-loop'
  'task-exec-loop'
  'continuous_loop'
  'autonomous_loop'
)
# Garde-fous : on ne touche JAMAIS à ces process (apps/services légitimes).
PROTECT='jarvis-webapp|chat_proxy|jarvis-mcp|guardian-urls|dispatch_embed|chrome|claude|code|Xorg|gnome|pipewire|wireplumber|whisper|lumen'

say(){ printf '%s\n' "$*"; }
ram(){ free -h 2>/dev/null | awk '/Mem:/{print "  RAM dispo: "$7"   swap: "$3"/"$2}'; }

say "== stop-cycles-m4 $([ $DRY -eq 1 ] && echo '(DRY-RUN)') =="
say "-- avant --"; ram

# 1) Process : lister puis (hors dry) tuer par motif, en respectant la garde.
for pat in "${PATTERNS[@]}"; do
  # pids correspondant au motif, hors process protégés
  pids=$(pgrep -f "$pat" 2>/dev/null | while read -r p; do
    a=$(ps -o args= -p "$p" 2>/dev/null)
    printf '%s' "$a" | grep -qiE "$PROTECT" && continue
    echo "$p"
  done)
  [ -z "$pids" ] && continue
  if [ $DRY -eq 1 ]; then
    say "  [dry] tournerait tuer '$pat' : $(echo $pids | tr '\n' ' ')"
  else
    echo "$pids" | xargs -r kill 2>/dev/null
    sleep 1
    echo "$pids" | xargs -r kill -9 2>/dev/null   # récalcitrants
    say "  coupé: $pat ($(echo $pids | tr '\n' ' '))"
  fi
done

# 2) Lanceurs systemd --user : stopper + désactiver toute unité qui référence un motif.
if command -v systemctl >/dev/null 2>&1; then
  for pat in "${PATTERNS[@]}"; do
    units=$(systemctl --user list-unit-files --no-legend 2>/dev/null | awk '{print $1}' \
      | while read -r u; do
          systemctl --user cat "$u" 2>/dev/null | grep -qiE "$pat" && echo "$u"
        done | sort -u)
    for u in $units; do
      if [ $DRY -eq 1 ]; then say "  [dry] désactiverait unité: $u"; else
        systemctl --user stop "$u" 2>/dev/null
        systemctl --user disable "$u" 2>/dev/null
        say "  désactivé (systemd --user): $u"
      fi
    done
  done
fi

# 3) Autostart XDG : neutraliser les .desktop qui lancent un motif (renommer .disabled).
for d in "$HOME/.config/autostart"/*.desktop; do
  [ -e "$d" ] || continue
  for pat in "${PATTERNS[@]}"; do
    if grep -qiE "$pat" "$d" 2>/dev/null; then
      if [ $DRY -eq 1 ]; then say "  [dry] neutraliserait autostart: $d"; else
        mv -f "$d" "$d.disabled" 2>/dev/null && say "  autostart neutralisé: $(basename "$d")"
      fi
      break
    fi
  done
done

# 4) crontab : commenter les lignes qui lancent un motif (sauvegarde .bak).
if command -v crontab >/dev/null 2>&1; then
  cur=$(crontab -l 2>/dev/null)
  if [ -n "$cur" ]; then
    new="$cur"
    for pat in "${PATTERNS[@]}"; do
      new=$(printf '%s\n' "$new" | sed -E "/^[^#].*$pat/ s/^/# [stop-cycles-m4] /")
    done
    if [ "$new" != "$cur" ]; then
      if [ $DRY -eq 1 ]; then say "  [dry] commenterait des lignes crontab"; else
        printf '%s\n' "$cur" | crontab - 2>/dev/null && crontab -l 2>/dev/null >"$HOME/.crontab.stop-cycles.bak"
        printf '%s\n' "$new" | crontab - 2>/dev/null && say "  crontab: lignes de boucle commentées (backup ~/.crontab.stop-cycles.bak)"
      fi
    fi
  fi
fi

# 5) Décharger les modèles Ollama que les boucles rechargeaient.
if [ $DRY -eq 0 ] && command -v ollama >/dev/null 2>&1; then
  ollama ps 2>/dev/null | awk 'NR>1{print $1}' | while read -r m; do
    [ -n "$m" ] && ollama stop "$m" 2>/dev/null && say "  modèle déchargé: $m"
  done
  sync
fi

say "-- après --"; ram
say "== terminé =="
exit 0
