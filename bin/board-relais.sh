#!/usr/bin/env bash
# board-relais.sh — Le Board prend le relais, cadence 1 minute.
#
# A chaque tic : lit ce qui vient d'etre ECRIT sur la machine, demande au Board
# la suite chronologique, journalise la reponse, planifie la tache suivante,
# et l'annonce a la voix.
#
# Souverain : inference sur M6 (LM Studio), zero token facture, rien ne sort.
set -uo pipefail

BASE="$HOME/jarvis"
LOCK="/tmp/board-relais.lock"
JOURNAL="$BASE/logs/board-relais.jsonl"
ETAT="$BASE/logs/board-relais-etat.txt"
DB="$BASE/jarvis_master.db"
BOARD="$BASE/board/board.py"
PIPER="$HOME/.local/bin/piper"
VOIX="$BASE/models/piper/fr_FR-siwis-medium.onnx"
TS=$(date '+%F %T')

# --- Verrou : M6 casse a 2 requetes simultanees, la serialisation est obligatoire.
exec 9>"$LOCK"
flock -n 9 || { echo "$TS SKIP verrou tenu" >> "$ETAT"; exit 0; }

# --- Voix : annonce a chaque lancement, jamais bloquante.
dire() {
  [ -f "$HOME/.cache/tts-off" ] && return 0
  local texte="${1:0:400}" wav="/tmp/board-relais-$$.wav"
  printf '%s' "$texte" | timeout 30 "$PIPER" --model "$VOIX" --output_file "$wav" >/dev/null 2>&1 || return 0
  [ -s "$wav" ] || return 0
  export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"; unset PULSE_SERVER
  timeout 25 paplay "$wav" >/dev/null 2>&1 || timeout 25 aplay -q -D plughw:1,0 "$wav" >/dev/null 2>&1
  rm -f "$wav"
}

# --- 1. LIRE CE QUI A ETE ECRIT depuis le dernier tic (la memoire du relais).
DEPUIS=$(cat "$BASE/logs/.board-relais-derniere" 2>/dev/null || echo "3 minutes ago")
ECRITS=$(find "$HOME/jarvis" "$HOME/labo" -maxdepth 3 \
           \( -name '*.md' -o -name '*.py' -o -name '*.sh' -o -name '*.json' \) \
           -newermt "$DEPUIS" -not -path '*/.git/*' -not -path '*/node_modules/*' 2>/dev/null | head -25)
date '+%F %T' > "$BASE/logs/.board-relais-derniere"

NB=$(printf '%s\n' "$ECRITS" | grep -c . || true)
RESUME=$(printf '%s\n' "$ECRITS" | sed "s|$HOME/||" | head -12 | tr '\n' ' ')

# --- 2. Etat de la machine, pour que la suggestion soit ancree dans le reel.
TEMP=$(sensors 2>/dev/null | grep 'Package id 0' | grep -oE '\+[0-9]+' | head -1 | tr -d '+')
PERF=$(cat /sys/devices/system/cpu/intel_pstate/max_perf_pct 2>/dev/null)
M6=$(timeout 5 curl -s -o /dev/null -w '%{http_code}' http://10.42.0.230:1234/v1/models 2>/dev/null)

# --- Bascule de secours : M6 tombe (cable NO-CARRIER, tour eteinte) -> Ollama local.
# Sans cela le relais attend 240 s dans le vide a chaque minute et la cadence derive.
if [ "$M6" = "200" ]; then
  BACKEND="M6"
  export BOARD_LMS_URL="http://10.42.0.230:1234/v1"
  export BOARD_CHAT_MODEL="qwen/qwen3.5-9b"
  export BOARD_EMBED_MODEL="text-embedding-nomic-embed-text-v1.5"
  DELAI=240
else
  OL=$(timeout 4 curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:11434/v1/models 2>/dev/null)
  if [ "$OL" = "200" ]; then
    BACKEND="OLLAMA-LOCAL"
    export BOARD_LMS_URL="http://127.0.0.1:11434/v1"
    export BOARD_CHAT_MODEL="qwen2.5:7b"
    export BOARD_FORCE_MODEL=1
    export BOARD_EMBED_MODEL="nomic-embed-text:latest"
    export BOARD_MAX_TOKENS=400
    DELAI=280
  else
    BACKEND="AUCUN"
    DELAI=20
  fi
fi

# --- 3. DEMANDER LA SUITE au Board (domaine tournant, pour couvrir le terrain).
DOMAINES=(orchestration-agents fiabilite-exploitation sessions-m4 inference-locale souverainete cluster-m1)
IDX=$(( ($(date +%M) / 10) % ${#DOMAINES[@]} ))
DOM="${DOMAINES[$IDX]}"

QUESTION="Etat machine : CPU plafond ${PERF}%, ${TEMP}C, LM Studio M6 HTTP ${M6}.
Depuis la derniere minute, ${NB} fichier(s) ont ete ecrits : ${RESUME:-aucun}.
En te fondant sur le corpus, indique LA prochaine action concrete a mener maintenant.
Reponds en 3 lignes maximum : (1) ce que revele ce qui vient d etre ecrit,
(2) l action suivante, precise et executable, (3) le risque a surveiller."

if [ "$BACKEND" = "AUCUN" ]; then
  REP=""
else
  REP=$(timeout "$DELAI" python3 "$BOARD" ask "$DOM" "$QUESTION" --k 4 2>&1 | tail -40)
fi
CODE=$?

# --- 4. JOURNALISER (fichier + base : la trace survit au terminal).
python3 - "$JOURNAL" "$DB" "$TS" "$DOM" "$NB" "$TEMP" "$PERF" "$M6" "$REP" <<'PY' 2>/dev/null
import json, sqlite3, sys
journal, db, ts, dom, nb, temp, perf, m6, rep = sys.argv[1:10]
with open(journal, 'a', encoding='utf-8') as f:
    f.write(json.dumps({"ts": ts, "domaine": dom, "fichiers_ecrits": int(nb or 0),
                        "temp_c": temp, "max_perf_pct": perf, "m6_http": m6,
                        "reponse": rep}, ensure_ascii=False) + "\n")
try:
    cx = sqlite3.connect(db, timeout=20)
    cx.execute("""CREATE TABLE IF NOT EXISTS board_relais(
        id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, domaine TEXT,
        fichiers_ecrits INT, temp_c TEXT, max_perf_pct TEXT, m6_http TEXT,
        reponse TEXT, tache_suivante TEXT, statut TEXT)""")
    cx.execute("INSERT INTO board_relais(ts,domaine,fichiers_ecrits,temp_c,max_perf_pct,m6_http,reponse,statut) "
               "VALUES(?,?,?,?,?,?,?,?)", (ts, dom, int(nb or 0), temp, perf, m6, rep,
                                           'REPONDU' if rep.strip() else 'VIDE'))
    cx.commit(); cx.close()
except Exception as e:
    print("db:", e, file=sys.stderr)
PY

# --- 5. ETAT LISIBLE + ANNONCE VOCALE.
{
  echo "─── $TS · domaine $DOM ───"
  echo "machine : ${PERF}% · ${TEMP}C · backend ${BACKEND} (M6 HTTP ${M6}) · ${NB} fichier(s) ecrits"
  echo "$REP" | head -20
  echo
} >> "$ETAT"

if [ -n "${REP// /}" ] && [ "$BACKEND" != "AUCUN" ]; then
  PHRASE=$(printf '%s' "$REP" | tr '\n' ' ' | sed 's/[*#`|_]//g; s/  */ /g' | cut -c1-320)
  dire "Relais Board sur ${BACKEND}, domaine ${DOM}. ${NB} fichiers écrits. ${PHRASE}"
else
  dire "Relais Board. Aucun backend d inférence ne répond, ni M6 ni Ollama local. Aucune suggestion ce cycle."
fi
exit 0
