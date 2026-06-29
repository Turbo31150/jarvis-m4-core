#!/usr/bin/env bash
# Pousseline — préparation nocturne (0 token, ON-DEMAND, anti-surchauffe).
# Lancé UNE seule fois par nuit par le timer systemd. Aucune boucle de rétroaction.
# 1) prépare les mails dus (absences/bilans/sorties) sans les envoyer sauf auto_send.
# 2) pré-génère le cahier-journal du lendemain SI l'emploi du temps est renseigné.
set -u
BASE="http://127.0.0.1:7777"
LOG="$HOME/jarvis/webapp/nuit.log"
ts(){ date '+%Y-%m-%d %H:%M'; }

# Garde thermique : si la machine est déjà chaude, on reporte (zéro inférence).
T=0
for f in /sys/class/thermal/thermal_zone*/temp; do
  v=$(cat "$f" 2>/dev/null || echo 0); [ "$v" -gt "$T" ] && T="$v"
done
T=$((T/1000))
if [ "$T" -ge 86 ]; then
  echo "$(ts) reporté — surchauffe ${T}°C" >> "$LOG"; exit 0
fi

# Le serveur doit répondre (sinon rien à faire).
if ! curl -s -m5 -o /dev/null "$BASE/api/status"; then
  echo "$(ts) serveur injoignable — abandon" >> "$LOG"; exit 0
fi

# 1) Automatisations dues (mails préparés ; envoi réel seulement si auto_send activé)
curl -s -m180 -X POST "$BASE/api/automations/run" \
  -H 'Content-Type: application/json' -d '{"max_actions":5}' \
  -w "$(ts) automations [%{http_code}]\n" >> "$LOG" 2>&1

# 2) Cahier-journal du lendemain — seulement si l'EDT contient quelque chose
EDT=$(curl -s -m5 "$BASE/api/prof/edt")
if echo "$EDT" | grep -qE '[a-zA-Z]{3,}'; then
  TOM=$(date -d 'tomorrow' '+%Y-%m-%d' 2>/dev/null || date '+%Y-%m-%d')
  curl -s -m240 -X POST "$BASE/api/cahier-journal/generer" \
    -H 'Content-Type: application/json' -d "{\"date\":\"$TOM\"}" -o /dev/null \
    -w "$(ts) cahier $TOM [%{http_code}]\n" >> "$LOG" 2>&1
else
  echo "$(ts) EDT vide — cahier non généré" >> "$LOG"
fi

echo "$(ts) nuit terminée (${T}°C)" >> "$LOG"
