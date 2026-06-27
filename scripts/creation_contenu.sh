#!/bin/bash
# JARVIS Création de Contenu - Assistance multimédia pour enseignants
# Usage: creation_contenu.sh [video|podcast|presentation|resume <fichier>|dictee]

set -e

CONTENU_DIR="$HOME/Documents/Contenu"
mkdir -p "$CONTENU_DIR/{Videos,Podcasts,Presentations,Resumes}"

log() { echo "📌 $*"; }
err() { echo "❌ $*" >&2; }

case "$1" in
  video)
    log "Lancement OBS Studio..."
    if command -v obs &>/dev/null; then
      obs &
      PID=$!
      log "OBS lancé (PID: $PID)"
      log "💡 Conseil: Exporte en MP4 720p pour les cours en ligne"
    else
      err "OBS non installé. Installe: sudo apt install obs-studio"
      exit 1
    fi
    ;;

  podcast)
    log "Mode: Enregistrement podcast"
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    PODCAST_FILE="$CONTENU_DIR/Podcasts/${TIMESTAMP}_podcast.wav"

    if ! command -v arecord &>/dev/null; then
      err "arecord non installé. Installe: sudo apt install alsa-utils"
      exit 1
    fi

    log "Configuration: 44.1kHz stéréo, 16-bit"
    log "Appuie sur CTRL+C pour terminer"
    sleep 1

    arecord -f S16_LE -r 44100 -c 2 "$PODCAST_FILE" &
    PID=$!
    log "Enregistrement lancé (PID: $PID)"
    log "Fichier: $PODCAST_FILE"
    wait $PID 2>/dev/null || true
    log "✅ Podcast sauvegardé"
    ;;

  presentation)
    log "Mode: Création présentation LibreOffice Impress"
    TEMPLATE="$CONTENU_DIR/Presentations/TEMPLATE.odp"

    if [ -f "$TEMPLATE" ]; then
      log "Utilisation du template: $TEMPLATE"
      libreoffice --impress "$TEMPLATE" 2>/dev/null &
    else
      log "Création nouvelle présentation..."
      touch "$CONTENU_DIR/Presentations/$(date +%Y%m%d)_presentation.odp"
      libreoffice --impress 2>/dev/null &
    fi

    PID=$!
    log "LibreOffice ouvert (PID: $PID)"
    ;;

  resume)
    if [ -z "$2" ]; then
      err "Usage: creation_contenu.sh resume <fichier>"
      exit 1
    fi

    if [ ! -f "$2" ]; then
      err "Fichier non trouvé: $2"
      exit 1
    fi

    log "Génération du résumé..."
    CONTENU=$(cat "$2")
    PROMPT="Résume ce cours en 5 points clés, format markdown structuré:\n\n$CONTENU"

    # Utilise lm-ask.sh local (M2 qwen3.5-9b)
    RESUME=$(/bin/bash ~/jarvis/scripts/lm-ask.sh "$PROMPT" 2>/dev/null)

    OUTPUT="$CONTENU_DIR/Resumes/$(date +%Y%m%d_%H%M%S)_resume.md"
    echo "# Résumé du cours" > "$OUTPUT"
    echo "**Généré:** $(date)" >> "$OUTPUT"
    echo "" >> "$OUTPUT"
    echo "$RESUME" >> "$OUTPUT"

    log "✅ Résumé généré: $OUTPUT"
    cat "$OUTPUT"
    ;;

  dictee)
    log "Mode: Dictée vocale → texte"
    if ! command -v whisper &>/dev/null; then
      err "Whisper non installé. Installe: pip install openai-whisper"
      exit 1
    fi

    AUDIO_FILE="/tmp/dictee_$(date +%s).wav"
    TEXT_FILE="$CONTENU_DIR/Resumes/$(date +%Y%m%d_%H%M%S)_dictee.txt"

    log "Enregistrement de la dictée (CTRL+C pour terminer)..."
    arecord -f S16_LE -r 16000 -c 1 "$AUDIO_FILE" &
    REC_PID=$!

    trap "kill $REC_PID 2>/dev/null; log 'Transcription...'" SIGINT
    wait $REC_PID 2>/dev/null || true

    log "Transcription via Whisper..."
    whisper "$AUDIO_FILE" --output_format txt --output_dir "$CONTENU_DIR/Resumes" \
            --language fr --device cpu 2>/dev/null

    log "✅ Dictée transcrite: $CONTENU_DIR/Resumes/"
    rm -f "$AUDIO_FILE"
    ;;

  *)
    cat <<EOF
📚 JARVIS Création de Contenu

Usage: creation_contenu.sh <mode> [options]

Modes:
  video              Ouvre OBS Studio pour enregistrer une vidéo
  podcast            Enregistre un podcast audio (WAV stéréo)
  presentation       Ouvre LibreOffice Impress
  resume <fichier>   Résume automatique d'un cours (IA local)
  dictee             Enregistre et transcrit une dictée vocale

Exemples:
  creation_contenu.sh video
  creation_contenu.sh podcast
  creation_contenu.sh resume mon_cours.txt
  creation_contenu.sh dictee

📁 Dossier de destination: $CONTENU_DIR
EOF
    exit 1
    ;;
esac
