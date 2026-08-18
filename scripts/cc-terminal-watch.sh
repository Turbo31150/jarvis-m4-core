#!/usr/bin/env bash
# Surveillance NON-STOP des terminaux Claude Code (uid turbo) — 0-token.
# Pour chaque terminal surveillé : lit l'activité → route via la bibliothèque
# commande/action (bloc.sh) → teste/valide → PLANIFIE une tâche en todolist.
# Exclut la session courante (EXCLUDE_PID). Ne touche pas aux sessions surveillées.
set -uo pipefail

UID_T=$(id -u turbo)
PROJDIR="/home/pamerys/.claude/projects/-home-turbo"
OUT="/home/pamerys/.claude/cc-terminals-todolist.md"
LOG="/home/pamerys/.claude/cc-terminal-watch.log"
BLOC="/home/pamerys/jarvis/bin/bloc.sh"
QWEN="/home/pamerys/jarvis/bin/qwen-nothink.sh"
EXCLUDE_PID="${EXCLUDE_PID:-0}"     # PID claude à ne pas surveiller (session courante)
MY_TRANSCRIPT="${MY_TRANSCRIPT:-$(basename "$(ls -t "$PROJDIR"/*.jsonl 2>/dev/null | head -1)")}"  # mon jsonl (le + récent au lancement)
INTERVAL="${1:-90}"                 # secondes entre scans

log(){ echo "[$(date '+%F %T')] $*" >> "$LOG" 2>/dev/null; }

# Dernière activité utile d'un transcript : derniers outils réellement appelés
last_activity(){
  local f="$1"; [ -f "$f" ] || { echo "n/a"; return; }
  local tools; tools=$(tail -n 40 "$f" 2>/dev/null \
    | grep -oE '"type":"tool_use","name":"[^"]+"' | grep -oE '"name":"[^"]+"' \
    | sed 's/"name":"//;s/"//' | tail -4 | tr '\n' ',' | sed 's/,$//')
  echo "${tools:-idle}"
}

# Les 2 transcripts les plus récemment modifiés, hors le mien (session courante)
target_transcripts(){
  ls -t "$PROJDIR"/*.jsonl 2>/dev/null | grep -v "$MY_TRANSCRIPT" | head -2
}

# Route une intention via la bibliothèque (bloc.sh) → 1re commande prête
plan_via_biblio(){
  local intent="$1"
  [ -x "$BLOC" ] || { echo "biblio indispo"; return; }
  "$BLOC" "$intent" 2>/dev/null | grep -vE '^\s*$' | head -1
}

DB="/home/pamerys/jarvis/jarvis_master.db"
BACKENDS=(LMStudio-M1 OpenClaw-agent Ollama-cloud)   # mix backends gratuits

# Match une série domino (action_series) par mot-clé
match_serie(){
  local intent="$1" first
  first=$(awk '{print $1}' <<<"$intent" | tr -cd 'a-z')
  [ -z "$first" ] && first="watchdog"
  sqlite3 "file:$DB?mode=ro" \
    "SELECT name FROM action_series WHERE keywords LIKE '%$first%' OR name LIKE '%$first%' ORDER BY usage_count ASC LIMIT 1;" 2>/dev/null
}

# Enregistre une tâche planifiée en domino_triggers (rotation backend = mix)
record_domino(){
  local tty="$1" serie="$2" backend="$3" state="$4"
  [ -z "$serie" ] && serie="watchdog"
  sqlite3 "$DB" "INSERT INTO domino_triggers(trigger_event,chain_name,threshold,status,payload_json) \
    VALUES('cc-term $tty','$serie',1,'planned','{\"tty\":\"$tty\",\"backend\":\"$backend\",\"state\":\"$state\"}');" 2>/dev/null
  sqlite3 "$DB" "UPDATE action_series SET usage_count=usage_count+1 WHERE name='$serie';" 2>/dev/null
}

# SCORING + FEEDBACK + AUTO-CORRECTION : 1 action biblio = 1 boucle qualité
# Retourne la série (éventuellement corrigée) via variable globale CORRECTED
CORRECTED=""
score_feedback(){
  local tty="$1" serie="$2" backend="$3" state="$4" intent="$5"
  local score fb corrected="$serie"
  # scoring : match réel vs fallback + fraîcheur d'activité
  if [ "$serie" = "watchdog" ] || [ -z "$serie" ]; then
    score=0.30; fb="intent-vague-fallback"
  elif [ "$state" = "active" ]; then
    score=0.95; fb="match-actif-ok"
  else
    score=0.70; fb="match-ok-inactif"
  fi
  # AUTO-CORRECTION : score bas → réélargir l'intention via contexte système
  if awk "BEGIN{exit !($score < 0.5)}"; then
    local sys_intent; sys_intent=$(top -bn1 2>/dev/null | awk 'NR>7{print $12}' | sort | uniq -c | sort -rn | awk 'NR==1{print $2}')
    corrected=$(match_serie "${sys_intent:-audit}")
    [ -z "$corrected" ] && corrected="cli-skill-audit"
    fb="$fb→corrige:${sys_intent:-audit}"
    # réenregistre le trigger corrigé
    record_domino "$tty" "$corrected" "$backend" "corrected"
  fi
  # log scoring + feedback en base
  sqlite3 "$DB" "INSERT INTO action_feedback(tty,serie,backend,state,score,feedback,corrected_serie) \
    VALUES('$tty','$serie','$backend','$state',$score,'$fb','$corrected');" 2>/dev/null
  # màj poids série (apprentissage : bon score → poids monte)
  sqlite3 "$DB" "INSERT INTO serie_weights(serie,weight,hits,ts) VALUES('$corrected',$score,1,datetime('now')) \
    ON CONFLICT(serie) DO UPDATE SET weight=(weight+$score)/2, hits=hits+1, ts=datetime('now');" 2>/dev/null
  echo "[$(date '+%F %T')] tty=$tty serie=$serie score=$score fb=$fb corr=$corrected" >> /home/pamerys/.claude/cc-terminal-scoring.log 2>/dev/null
  CORRECTED="$corrected"
}

scan_once(){
  local ts now; ts=$(date '+%F %T'); now=$(date +%s)
  # Terminaux CC interactifs (pts) hors session courante
  mapfile -t TERMS < <(ps -u "$UID_T" -o pid,tty,etime,comm --no-headers \
    | awk '$4=="claude" && $2 ~ /pts/' | awk -v ex="$EXCLUDE_PID" '$1!=ex')

  {
    echo "# 🖥️ Todolist planifiée — surveillance terminaux Claude Code (uid $UID_T)"
    echo "_MàJ $ts • scan ${INTERVAL}s • daemon PID $$ • exclu=$EXCLUDE_PID • backends: LMStudio/OpenClaw/Ollama-cloud_"
    echo ""
    [ "${#TERMS[@]}" -eq 0 ] && echo "⚠️ Aucun terminal CC à surveiller."
    mapfile -t TFS < <(target_transcripts)
    local i=0
    for line in "${TERMS[@]}"; do
      i=$((i+1))
      local pid tty etime; pid=$(awk '{print $1}'<<<"$line"); tty=$(awk '{print $2}'<<<"$line"); etime=$(awk '{print $3}'<<<"$line")
      # transcript actif le plus récent (hors le mien), mappé par ordre de récence
      local tf="${TFS[$((i-1))]:-}"
      local act age; act=$(last_activity "$tf")
      if [ -f "$tf" ]; then age=$(( now - $(stat -c %Y "$tf") )); else age=-1; fi
      echo "## Terminal $i — \`$tty\` (PID $pid, up $etime)"
      echo "- 🔎 activité : ${act:-inconnue}"
      echo "- ⏱️ transcript inactif : ${age}s"
      # PLANIFICATION : route l'activité via la bibliothèque + série domino
      local intent="${act:-status}"; local bloc serie backend state
      bloc=$(plan_via_biblio "$intent")
      serie=$(match_serie "$intent")
      backend="${BACKENDS[$(( (i-1) % ${#BACKENDS[@]} ))]}"   # mix par rotation
      if [ "$age" -ge 0 ] && [ "$age" -gt 300 ]; then state="idle5"
      elif [ "$age" -ge 0 ] && [ "$age" -gt 120 ]; then state="idle2"
      else state="active"; fi
      # enregistre la tâche planifiée en base (domino_triggers)
      record_domino "$tty" "$serie" "$backend" "$state"
      # scoring + feedback + auto-correction (1 action biblio = 1 boucle qualité)
      score_feedback "$tty" "${serie:-watchdog}" "$backend" "$state" "$intent"
      local disp_serie="${CORRECTED:-$serie}"
      echo "- 🎯 série domino : \`${disp_serie:-watchdog}\` • backend : **$backend** • état : $state"
      echo "- 📊 scoring/feedback : voir table \`action_feedback\` (auto-correction active)"
      if [ "$state" = "idle5" ]; then
        echo "- [ ] ⏰ **PLANIFIÉ** \`$tty\` inactif >5min → série \`${serie:-watchdog}\` via $backend : \`${bloc:-verifier session}\`"
      elif [ "$state" = "idle2" ]; then
        echo "- [ ] 🔍 **PLANIFIÉ** \`$tty\` pause >2min → série \`${serie:-watchdog}\` via $backend"
      else
        echo "- [x] ✅ \`$tty\` actif — série \`${serie:-watchdog}\` prête via $backend"
      fi
      echo ""
    done
    echo "---"
    echo "_Historique : $ts → ${#TERMS[@]} terminal(aux) planifié(s)_"
  } > "$OUT.tmp" && mv "$OUT.tmp" "$OUT"
  log "scan: ${#TERMS[@]} terminaux planifiés → $OUT"
}

log "=== démarrage daemon interval=${INTERVAL}s exclude=$EXCLUDE_PID ==="
while true; do scan_once; sleep "$INTERVAL"; done
