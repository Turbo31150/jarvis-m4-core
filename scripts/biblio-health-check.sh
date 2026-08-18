#!/usr/bin/env bash
# Biblio Health SELF-HEALING — surveille ET répare la bibliothèque commune sans intervention.
#  - index régresse (>30% perdu) -> RESTAURE depuis le dernier snapshot bon-connu
#  - daemon biblio-filler mort   -> le RELANCE
#  - toujours: met à jour baseline + snapshot bon-connu, log, notifie (informational)
# Secret-safe : token Telegram lu depuis secrets.env, jamais en dur.
set -uo pipefail

IDX="$HOME/labo/bibliotheque/lib/BLOCS-INDEX.tsv"
BASE="$HOME/jarvis/data/.biblio_health_baseline"
GOOD="$HOME/jarvis/data/.biblio_index_lastgood.tsv"
LOG="$HOME/jarvis/data/logs/biblio-health.log"
mkdir -p "$(dirname "$LOG")" 2>/dev/null
ts(){ date '+%Y-%m-%d %H:%M:%S'; }

notify(){
  source "$HOME/.config/jarvis/secrets.env" 2>/dev/null || true
  local tok="${TELEGRAM_TOKEN:-${TELEGRAM_BOT_TOKEN:-}}" cid="${TELEGRAM_CHAT_ID:-}"
  [ -n "$tok" ] && [ -n "$cid" ] && curl -s -m10 "https://api.telegram.org/bot${tok}/sendMessage" \
    --data-urlencode "chat_id=${cid}" --data-urlencode "text=🧠 Biblio Health: $1" >/dev/null 2>&1
  echo "[$(ts)] $1" >> "$LOG"
}

count(){ [ -f "$1" ] && echo $(( $(wc -l < "$1") - 1 )) || echo 0; }

[ -f "$IDX" ] || { cp "$GOOD" "$IDX" 2>/dev/null && notify "🔧 SELF-HEAL: BLOCS-INDEX absent -> restauré depuis snapshot" || notify "⚠️ index ET snapshot absents"; }

cur=$(count "$IDX")
base=$(cat "$BASE" 2>/dev/null || echo "$cur"); [[ "$base" =~ ^[0-9]+$ ]] || base=$cur
seuil=$(( base * 70 / 100 ))

# 1) RÉGRESSION -> self-heal (restaure snapshot bon-connu si + gros)
if [ "$cur" -lt "$seuil" ] && [ -f "$GOOD" ] && [ "$(count "$GOOD")" -gt "$cur" ]; then
  cp "$GOOD" "$IDX"
  new=$(count "$IDX")
  notify "🔧 SELF-HEAL: régression détectée ($cur < $seuil) -> index restauré $cur→$new depuis snapshot. Vérifier bloc-rebuild.py (filtre 5-col)."
  cur=$new
else
  echo "[$(ts)] OK index=$cur (record=$base)" >> "$LOG"
fi

# 2) baseline + snapshot bon-connu = suit la croissance (seulement quand sain)
if [ "$cur" -ge "$seuil" ]; then
  [ "$cur" -gt "$base" ] && echo "$cur" > "$BASE"
  cp "$IDX" "$GOOD" 2>/dev/null   # snapshot bon-connu
fi

# 3) daemon biblio-filler mort -> on SIGNALE, on ne relance plus
# [neutralisé 2026-08-04] la relance réinjectait l'alimenteur non filtré : +47k blocs cycle-fichier.
# [corrigé 2026-08-06] la commande avait été commentée mais les « && / || » suivants étaient
# restés actifs : bash refusait le fichier entier (« erreur de syntaxe près de && », exit 2),
# donc AUCUNE des 3 gardes ci-dessus ne s'exécutait depuis le 04/08.
if ! systemctl --user is-active --quiet biblio-filler.service 2>/dev/null; then
  notify "⚠️ daemon biblio-filler mort (relance auto désactivée le 2026-08-04)"
fi

exit 0
