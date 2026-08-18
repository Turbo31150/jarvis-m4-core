#!/usr/bin/env bash
# m5-dispatch — CLI unifié audit/todolist/prompt M5
# Usage: m5-dispatch [audit|todo|ask|status] [args...]

set -euo pipefail
LLM_FAST="http://localhost:8083/v1"   # qwen3.5-9b
LLM_REASON="http://localhost:8082/v1"  # deepseek-r1
LLM_M2="http://127.0.0.1:18800/v1"
TODO_FILE="/home/pamerys/jarvis/data/todolist.json"
AUDIT_LOG="/home/pamerys/jarvis/data/audit_m5.json"
mkdir -p "$(dirname "$TODO_FILE")"
[[ ! -f "$TODO_FILE" ]] && echo '{"tasks":[]}' > "$TODO_FILE"

# ─── couleurs ───
R='\033[0;31m' G='\033[0;32m' Y='\033[1;33m' B='\033[0;36m' N='\033[0m'

_llm_ask() {
  local url="$1" model="$2" prompt="$3"
  curl -s --max-time 30 "$url/chat/completions" \
    -H "Content-Type: application/json" \
    -d "{\"model\":\"$model\",\"messages\":[{\"role\":\"user\",\"content\":$(echo "$prompt"|python3 -c 'import sys,json;print(json.dumps(sys.stdin.read()))')}],\"max_tokens\":512,\"stream\":false}" \
    | python3 -c "import sys,json;d=json.load(sys.stdin);print(d['choices'][0]['message']['content'])" 2>/dev/null
}

_route_llm() {
  # Choisit le bon backend selon le type de tâche
  local task_type="${1:-auto}" prompt="$2"
  case "$task_type" in
    reason|debug|code) echo "$(_llm_ask "$LLM_REASON" "deepseek-r1" "$prompt")" ;;
    fast|summary|classify) echo "$(_llm_ask "$LLM_FAST" "qwen3.5-9b" "$prompt")" ;;
    auto)
      # détection par mots-clés
      if echo "$prompt" | grep -qiE "debug|erreur|bug|pourquoi|analyse|code|fix|raison"; then
        echo "$(_llm_ask "$LLM_REASON" "deepseek-r1" "$prompt")"
      else
        echo "$(_llm_ask "$LLM_FAST" "qwen3.5-9b" "$prompt")"
      fi ;;
    m2) echo "$(_llm_ask "$LLM_M2" "auto" "$prompt")" ;;
  esac
}

cmd_audit() {
  echo -e "${B}━━━ AUDIT M5 $(date '+%H:%M:%S') ━━━${N}"
  
  # CPU/RAM
  local load; load=$(awk '{print $1}' /proc/loadavg)
  local ram_used; ram_used=$(free -h | awk '/Mem/{print $3"/"$2}')
  local swap_used; swap_used=$(free -h | awk '/Swap/{print $3"/"$2}')
  echo -e "${Y}CPU${N} Load:$load  ${Y}RAM${N} $ram_used  ${Y}SWAP${N} $swap_used"
  
  # GPU
  echo -e "${Y}GPU${N}"
  nvidia-smi --query-gpu=index,temperature.gpu,utilization.gpu,memory.used,memory.total,power.draw \
    --format=csv,noheader 2>/dev/null | while IFS=',' read -r idx temp util mem_u mem_t pwr; do
    local color="$G"
    [[ "${temp// /}" -gt 80 ]] && color="$R"
    [[ "${temp// /}" -gt 70 ]] && [[ "${temp// /}" -le 80 ]] && color="$Y"
    echo -e "  GPU${idx// /} ${color}${temp// /}°C${N} ${util// /}% VRAM:${mem_u// /}/${mem_t// /} ${pwr// /}W"
  done
  
  # Disk
  echo -e "${Y}DISK${N}"
  df -h / /mnt/ssd | grep -v tmpfs | tail -2 | while IFS=' ' read -r fs size used avail pct mnt; do
    local color="$G"
    local pn="${pct/\%/}"
    [[ $pn -gt 85 ]] && color="$R"
    [[ $pn -gt 75 ]] && [[ $pn -le 85 ]] && color="$Y"
    echo -e "  $mnt $color$pct${N} ($used/$size)"
  done
  
  # LLM
  echo -e "${Y}LLM${N}"
  for port in 8082 8083 1234; do
    local model; model=$(curl -s --max-time 2 "http://localhost:$port/v1/models" \
      | python3 -c "import sys,json;d=json.load(sys.stdin);m=d.get('data',d.get('models',[]));print(m[0]['id'] if m else 'idle')" 2>/dev/null || echo "offline")
    [[ "$model" == "offline" ]] && echo -e "  :$port ${R}offline${N}" || echo -e "  :$port ${G}$model${N}"
  done
  local m2; m2=$(curl -s --max-time 2 "http://127.0.0.1:18800/v1/models" \
    | python3 -c "import sys,json;d=json.load(sys.stdin);m=d.get('data',[]);print(m[0]['id'] if m else 'idle')" 2>/dev/null || echo "offline")
  [[ "$m2" == "offline" ]] && echo -e "  M2:1234 ${R}offline${N}" || echo -e "  M2:1234 ${G}$m2${N}"
  local m1; m1=$(ssh -o ConnectTimeout=3 m1 'echo up' 2>/dev/null || echo "offline")
  echo -e "  M1 ${m1/up/${G}up${N}}"
  
  # Services
  local failed; failed=$(systemctl --user list-units --state=failed --no-pager --no-legend 2>/dev/null | wc -l)
  local docker_n; docker_n=$(docker ps -q 2>/dev/null | wc -l)
  echo -e "${Y}SVC${N} Failed:${failed}  Docker:${docker_n} running"
  
  # Sauvegarder
  python3 -c "
import json,subprocess,datetime
data={'ts':'$(date -Iseconds)','load':'$load','ram':'$ram_used','disk_pct':86,'m1':'$m1','m2':'$m2'}
with open('$AUDIT_LOG','w') as f: json.dump(data,f,indent=2)
" 2>/dev/null
  echo ""
}

cmd_todo() {
  local action="${1:-list}"
  case "$action" in
    list|ls)
      echo -e "${B}━━━ TODOLIST ━━━${N}"
      python3 - << 'PYEOF'
import json,sys
with open("/home/pamerys/jarvis/data/todolist.json") as f:
    data = json.load(f)
tasks = data.get("tasks", [])
if not tasks:
    print("  (vide)")
    sys.exit(0)
status_icon = {"todo": "○", "doing": "◐", "done": "✓", "blocked": "✗"}
colors = {"todo": "\033[0m", "doing": "\033[1;33m", "done": "\033[0;32m", "blocked": "\033[0;31m"}
NC = "\033[0m"
for i, t in enumerate(tasks):
    s = t.get("status","todo")
    icon = status_icon.get(s,"?")
    col = colors.get(s,"")
    pri = "!" * t.get("priority",1)
    print(f"  {col}{icon} [{i}] {pri} {t['title']}{NC}  [{t.get('node','M5')}]")
PYEOF
      ;;
    add)
      local title="${2:-tâche sans titre}"
      local node="${3:-M5}"
      python3 -c "
import json
with open('$TODO_FILE') as f: d=json.load(f)
d['tasks'].append({'title':'$title','status':'todo','node':'$node','priority':1})
with open('$TODO_FILE','w') as f: json.dump(d,f,indent=2)
print('+ ajouté: $title')
"
      ;;
    done|do)
      local idx="${2:-0}"
      python3 -c "
import json
with open('$TODO_FILE') as f: d=json.load(f)
if $idx < len(d['tasks']):
    d['tasks'][$idx]['status']='done'
    with open('$TODO_FILE','w') as f: json.dump(d,f,indent=2)
    print('✓ done: '+d['tasks'][$idx]['title'])
"
      ;;
    clear)
      python3 -c "
import json
with open('$TODO_FILE') as f: d=json.load(f)
d['tasks']=[t for t in d['tasks'] if t.get('status')!='done']
with open('$TODO_FILE','w') as f: json.dump(d,f,indent=2)
print('Nettoyé (done supprimés)')
"
      ;;
  esac
}

cmd_ask() {
  local type="${1:-auto}"
  shift || true
  local prompt="$*"
  [[ -z "$prompt" ]] && { echo "Usage: m5-dispatch ask [fast|reason|auto] <prompt>"; exit 1; }
  echo -e "${B}[dispatch→$type]${N} $prompt"
  echo "---"
  _route_llm "$type" "$prompt"
  echo ""
}

cmd_status() {
  echo -e "${B}━━━ STATUS RAPIDE M5 ━━━${N}"
  echo -e "Load: $(awk '{print $1}' /proc/loadavg)  RAM: $(free -h|awk '/Mem/{print $3"/"$2}')"
  echo -e "GPU: $(nvidia-smi --query-gpu=index,temperature.gpu --format=csv,noheader 2>/dev/null | tr '\n' ' ')"
  echo -e "LLM: deepseek:8082 qwen:8083 lms:1234"
  echo -e "Todo: $(python3 -c "import json;d=json.load(open('$TODO_FILE'));t=d['tasks'];print(f\"{sum(1 for x in t if x['status']!='done')}/{len(t)} en cours\")" 2>/dev/null || echo '0/0')"
  echo -e "M1: $(ssh -o ConnectTimeout=3 m1 'echo UP' 2>/dev/null || echo 'offline')"
}

cmd_dispatch() {
  # Route une tâche vers le bon nœud/agent
  local task_desc="$*"
  echo -e "${B}[dispatch]${N} Analyse de la tâche..."
  local routing
  routing=$(_route_llm "fast" "Analyse cette tâche et réponds JSON uniquement: {\"node\":\"M5|M2|M1\",\"agent\":\"nom_agent\",\"backend\":\"deepseek-r1|qwen3.5-9b|lms\",\"priority\":1-3} pour: $task_desc")
  echo "$routing"
}

# ─── HELP ───
cmd_help() {
  echo -e "${B}m5-dispatch${N} — CLI dispatch/audit/todolist JARVIS M5"
  echo ""
  echo "  audit           — audit complet M5 (GPU/RAM/LLM/disk/services)"
  echo "  status          — status rapide 1 ligne"
  echo "  todo list       — afficher la todolist"
  echo "  todo add <titre> [node] — ajouter une tâche"
  echo "  todo done <idx> — marquer done"
  echo "  todo clear      — supprimer les done"
  echo "  ask [fast|reason|auto] <prompt> — poser une question au LLM local"
  echo "  dispatch <desc> — router une tâche vers le bon nœud"
  echo "  score <caption> [images_dir]  — score qualité contenu (grade + améliorations)"
  echo "  sync [--dry-run] [-v]                — sync M1↔M2 checksums"
  echo "  autodebug [scan|fix] [--json|--dry-run] — auto-debug KB"
  echo "  toolgen <prompt> [--name x] [--no-install] — générer + installer un outil"
  echo ""
  echo "  LLM backends:"
  echo "    fast   → qwen3.5-9b  :8083"
  echo "    reason → deepseek-r1 :8082"
  echo "    auto   → détection par mots-clés"
}

# ─── ROUTER ───
CMD="${1:-help}"
shift || true
case "$CMD" in
  audit|a)     cmd_audit ;;
  status|s)    cmd_status ;;
  todo|t)      cmd_todo "$@" ;;
  ask|q)       cmd_ask "$@" ;;
  dispatch|d)  cmd_dispatch "$@" ;;
  sync|sy)     bash ~/jarvis/scripts/cluster-sync.sh "$@" ;;
  score|sc)    python3 ~/jarvis/scripts/content-score.py score --caption "${1:-}" --images "${2:-}" ;;
  autodebug|ad) python3 ~/jarvis/scripts/auto-debug.py "${1:-scan}" "${@:2}" ;;
  toolgen|tg)  bash ~/jarvis/scripts/tool-gen.sh "$@" ;;
  help|h|--help) cmd_help ;;
  *) echo "Commande inconnue: $CMD"; cmd_help; exit 1 ;;
esac
