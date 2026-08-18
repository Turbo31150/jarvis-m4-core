#!/usr/bin/env bash
# lumen-cli — Interface CLI headless complète pour Lumen
# Usage sans avoir la page web ouverte
# Requiert: curl, xdotool, xclip, python3

API="http://127.0.0.1:8788/api"
WHISPER_API="http://127.0.0.1:9742/api/voice"
CLUSTER_M1="http://127.0.0.1:1234/v1"
CLUSTER_M2="http://127.0.0.1:18800/v1"

# ── Couleurs ─────────────────────────────────────────────────────
C_CYAN='\033[0;36m'; C_GREEN='\033[0;32m'; C_YELLOW='\033[1;33m'
C_RED='\033[0;31m'; C_PURPLE='\033[0;35m'; C_RESET='\033[0m'; C_BOLD='\033[1m'

usage() {
cat << EOF
${C_BOLD}lumen-cli${C_RESET} — Lumen headless (sans UI web)

${C_CYAN}TRANSCRIPTION${C_RESET}
  record [sec]           Enregistre micro ${C_YELLOW}[5s]${C_RESET} et transcrit
  record-file <file>     Transcrit un fichier audio (wav/mp3/ogg)
  stream                 Mode streaming continu (Ctrl+C pour stop)
  inject                 Injecte dernier transcript au curseur
  last                   Affiche dernier transcript

${C_CYAN}TRAITEMENT TEXTE/CODE${C_RESET}
  chat <msg>             Chat direct cluster (auto-route M1→M2→OL1)
  code <msg>             Traitement code (route vers deepseek-r1)
  translate <lang> <tx>  Traduit en [fr|en|es|de|zh|ja|ar]
  decode <text>          Analyse/déchiffre texte chiffré ou encodé
  summarize              Résume le presse-papiers

${C_CYAN}CONTRÔLE${C_RESET}
  status                 État Lumen (mode, STT, profil)
  mode <name>            Changer mode [auto|research|translation|document|meeting|classroom]
  stt <engine>           Changer STT [whisper|gemini|browser]
  profile <p>            Profil cluster [speed|balanced|deep|consensus]

${C_CYAN}EXEMPLES${C_RESET}
  lumen-cli record 10                    → 10s audio → transcript
  lumen-cli record-file audio.wav        → transcrit le fichier
  lumen-cli code "explique ce code"      → analyse code deepseek
  lumen-cli translate en "Bonjour"       → traduit en anglais
  lumen-cli decode "SGVsbG8="            → détecte base64, décode
  lumen-cli chat "résume la réunion"     → chat cluster
  lumen-cli inject                       → colle transcript au curseur
EOF
}

# ── Helpers ──────────────────────────────────────────────────────
cluster_chat() {
  local msg="$1" model="${2:-}" route="${3:-auto}"
  local body
  if [ -n "$model" ]; then
    body="{\"messages\":[{\"role\":\"user\",\"content\":$(echo -n "$msg" | python3 -c "import sys,json; print(json.dumps(sys.stdin.read()))")}],\"model\":\"$model\",\"max_tokens\":2048,\"stream\":false}"
    local base="$CLUSTER_M1"
    [[ "$model" == *"deepseek"* ]] && base="$CLUSTER_M2"
    curl -sf -X POST "${base}/chat/completions" \
      -H "Content-Type: application/json" \
      -d "$body" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['choices'][0]['message']['content'])" 2>/dev/null
  else
    # Route via token-server cluster bridge
    local payload
    payload="{\"message\":$(echo -n "$msg" | python3 -c "import sys,json; print(json.dumps(sys.stdin.read()))")}"
    curl -sf -X POST "${API}/cluster/chat-send" \
      -H "Content-Type: application/json" \
      -d "$payload" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('agent_message',{}).get('content') or d.get('content') or d.get('response',''))" 2>/dev/null
  fi
}

record_and_transcribe() {
  local sec="${1:-5}"
  local tmpfile="/tmp/lumen-record-$$.wav"
  echo -e "${C_PURPLE}⏺ Enregistrement ${sec}s...${C_RESET}"
  arecord -D default -f S16_LE -r 16000 -c 1 -d "$sec" "$tmpfile" 2>/dev/null
  if [ ! -f "$tmpfile" ]; then
    echo -e "${C_RED}Erreur: arecord indisponible${C_RESET}"
    return 1
  fi
  echo -e "${C_CYAN}⟳ Transcription...${C_RESET}"
  transcribe_file "$tmpfile"
  rm -f "$tmpfile"
}

transcribe_file() {
  local file="$1"
  local b64 result text
  b64=$(base64 -w 0 "$file" 2>/dev/null)
  local ext="${file##*.}"

  # Essai Whisper JARVIS
  result=$(curl -sf --max-time 30 -X POST "${WHISPER_API}/transcribe_blob" \
    -H "Content-Type: application/json" \
    -d "{\"audio\":\"$b64\",\"format\":\"$ext\",\"language\":\"fr\"}" 2>/dev/null)
  text=$(echo "$result" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('text',''))" 2>/dev/null)

  # Fallback: token-server whisper
  if [ -z "$text" ]; then
    result=$(curl -sf --max-time 30 -X POST "${API}/cluster/transcribe" \
      -H "Content-Type: application/json" \
      -d "{\"audio\":\"$b64\",\"format\":\"$ext\",\"language\":\"fr\"}" 2>/dev/null)
    text=$(echo "$result" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('text','') or d.get('transcribedText',''))" 2>/dev/null)
  fi

  if [ -z "$text" ]; then
    echo -e "${C_RED}Transcription échouée (whisper indisponible?)${C_RESET}"; return 1
  fi

  echo -e "${C_GREEN}✓ Transcript:${C_RESET}"
  echo "$text"

  # Stocker pour inject
  curl -sf -X POST "${API}/control/transcript" \
    -H "Content-Type: application/json" \
    -d "{\"text\":$(echo -n "$text" | python3 -c "import sys,json; print(json.dumps(sys.stdin.read()))")}" > /dev/null 2>&1

  # Copier dans presse-papiers
  echo -n "$text" | xclip -selection clipboard 2>/dev/null
  echo -e "${C_YELLOW}→ Copié dans presse-papiers${C_RESET}"
}

decode_text() {
  local input="$1"
  local result
  # Détecter le type d'encodage
  if echo "$input" | python3 -c "import sys,base64; base64.b64decode(sys.stdin.read().strip()); print('ok')" 2>/dev/null | grep -q ok; then
    local decoded
    decoded=$(echo "$input" | python3 -c "import sys,base64; print(base64.b64decode(sys.stdin.read().strip()).decode('utf-8','replace'))")
    echo -e "${C_CYAN}Base64 détecté:${C_RESET} $decoded"
    result="$decoded"
  elif echo "$input" | grep -qE '^[0-9a-fA-F ]+$'; then
    local decoded
    decoded=$(echo "$input" | python3 -c "import sys; h=sys.stdin.read().replace(' ','').strip(); print(bytes.fromhex(h).decode('utf-8','replace'))")
    echo -e "${C_CYAN}Hex détecté:${C_RESET} $decoded"
    result="$decoded"
  elif echo "$input" | grep -qE '^[01 ]+$'; then
    local decoded
    decoded=$(echo "$input" | python3 -c "import sys; b=sys.stdin.read().replace(' ','').strip(); print(''.join(chr(int(b[i:i+8],2)) for i in range(0,len(b),8)))")
    echo -e "${C_CYAN}Binaire détecté:${C_RESET} $decoded"
    result="$decoded"
  else
    echo -e "${C_YELLOW}Analyse sémantique via cluster...${C_RESET}"
    result=$(cluster_chat "Analyse et déchiffre ce texte, explique son encodage: $input")
    echo "$result"
  fi
}

# ── Main ─────────────────────────────────────────────────────────
CMD="${1:-}"
shift 2>/dev/null || true

case "$CMD" in
  record)
    record_and_transcribe "${1:-5}"
    ;;
  record-file|transcribe)
    [ -z "$1" ] && echo "Usage: lumen-cli record-file <fichier>" && exit 1
    transcribe_file "$1"
    ;;
  stream)
    echo -e "${C_PURPLE}Mode stream (Ctrl+C pour stop). Segments de 8s...${C_RESET}"
    while true; do
      record_and_transcribe 8
      echo "---"
    done
    ;;
  inject)
    RESULT=$(curl -sf -X POST "${API}/control/inject" \
      -H "Content-Type: application/json" -d '{"useLast":true}' 2>/dev/null)
    TEXT=$(echo "$RESULT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('injected',''))" 2>/dev/null)
    [ -n "$TEXT" ] && echo -e "${C_GREEN}Injecté:${C_RESET} $TEXT" || echo -e "${C_YELLOW}Rien à injecter${C_RESET}"
    ;;
  last)
    curl -sf "${API}/control/status" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('lastTranscript','(vide)'))" 2>/dev/null
    ;;
  chat)
    [ -z "$1" ] && echo "Usage: lumen-cli chat <message>" && exit 1
    cluster_chat "$*"
    ;;
  code)
    [ -z "$1" ] && echo "Usage: lumen-cli code <message>" && exit 1
    cluster_chat "[CODE_ANALYSIS]\n$*" "deepseek-r1-0528-qwen3-8b"
    ;;
  translate)
    [ -z "$1" ] || [ -z "$2" ] && echo "Usage: lumen-cli translate <lang> <texte>" && exit 1
    LANG="$1"; shift
    TEXT="$*"
    RESULT=$(curl -sf -X POST "${API}/cluster/translate" \
      -H "Content-Type: application/json" \
      -d "{\"text\":$(echo -n "$TEXT" | python3 -c "import sys,json; print(json.dumps(sys.stdin.read()))"),\"sourceLanguage\":\"auto\",\"targetLanguage\":\"$LANG\"}" 2>/dev/null)
    echo "$RESULT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('translatedText') or d.get('content',''))" 2>/dev/null
    ;;
  decode)
    [ -z "$1" ] && echo "Usage: lumen-cli decode <texte>" && exit 1
    decode_text "$*"
    ;;
  summarize)
    TEXT=$(xclip -o -selection clipboard 2>/dev/null)
    [ -z "$TEXT" ] && echo "Presse-papiers vide" && exit 1
    cluster_chat "Résume en 3 points clés: $TEXT"
    ;;
  status)
    curl -sf "${API}/control/status" | python3 -c "
import sys,json
d=json.load(sys.stdin)
print(f\"Micro:   {'ON 🔴' if d.get('micActive') else 'OFF'}\")
print(f\"STT:     {d.get('transcriptionMode','?')}\")
print(f\"Mode:    {d.get('taskMode','?')}\")
print(f\"Profil:  {d.get('orchestrationProfile','?')}\")
print(f\"Endpoint: {d.get('endpoint','?')}\")
t=d.get('lastTranscript','')
print(f\"Dernier: {t[:80]}{'...' if len(t)>80 else ''}\")
" 2>/dev/null
    ;;
  mode)
    [ -z "$1" ] && echo "Usage: lumen-cli mode <auto|research|translation|document|meeting|classroom>" && exit 1
    bash /home/pamerys/jarvis/scripts/lumen/lumen-mode.sh "$1"
    ;;
  stt)
    [ -z "$1" ] && echo "Usage: lumen-cli stt <whisper|gemini|browser>" && exit 1
    bash /home/pamerys/jarvis/scripts/lumen/lumen-mode.sh "$1"
    ;;
  profile)
    [ -z "$1" ] && echo "Usage: lumen-cli profile <speed|balanced|deep|consensus>" && exit 1
    bash /home/pamerys/jarvis/scripts/lumen/lumen-mode.sh "$1"
    ;;
  ""|help|--help|-h)
    usage
    ;;
  *)
    echo -e "${C_RED}Commande inconnue: $CMD${C_RESET}"
    usage
    exit 1
    ;;
esac
