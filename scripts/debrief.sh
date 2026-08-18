#!/usr/bin/env bash
# Débrief vocal : génère un TTS du texte, le joue sur cet ordinateur,
# et l'envoie en message vocal sur Telegram si un token dédié est configuré.
#
# Config Telegram (optionnelle) — créer ~/.config/jarvis/debrief.env avec :
#   TELEGRAM_DEBRIEF_TOKEN=123456:ABC...
#   TELEGRAM_DEBRIEF_CHAT=123456789
#
# Usage : debrief.sh "trois mots ou trois phrases de débrief"
set -uo pipefail
TXT="${1:-}"
[ -z "$TXT" ] && { echo "usage: debrief.sh \"texte\""; exit 1; }

VOICE="${DEBRIEF_VOICE:-fr-FR-DeniseNeural}"
MP3="/tmp/debrief-$$.mp3"
EDGE="/home/pamerys/.local/bin/edge-tts"

# 1) Synthèse vocale
"$EDGE" --text "$TXT" --voice "$VOICE" --write-media "$MP3" 2>/dev/null || { echo "TTS KO"; exit 1; }

# 2) Lecture locale (best effort)
( mpg123 -q "$MP3" 2>/dev/null || ffplay -nodisp -autoexit -loglevel quiet "$MP3" 2>/dev/null ) || true

# 3) Envoi Telegram (si configuré) — token DÉDIÉ au débrief, pas celui d'un autre service
CONF="$HOME/.config/jarvis/debrief.env"
[ -f "$CONF" ] && set -a && . "$CONF" && set +a
if [ -n "${TELEGRAM_DEBRIEF_TOKEN:-}" ] && [ -n "${TELEGRAM_DEBRIEF_CHAT:-}" ]; then
  curl -s -m 20 -F "chat_id=${TELEGRAM_DEBRIEF_CHAT}" -F "voice=@${MP3}" -F "caption=${TXT}" \
    "https://api.telegram.org/bot${TELEGRAM_DEBRIEF_TOKEN}/sendVoice" >/dev/null \
    && echo "débrief envoyé sur Telegram" || echo "envoi Telegram échoué"
else
  echo "Telegram non configuré (créer ~/.config/jarvis/debrief.env) — débrief joué en local seulement"
fi

rm -f "$MP3" 2>/dev/null || true
