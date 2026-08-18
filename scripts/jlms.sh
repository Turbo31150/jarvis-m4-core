#!/usr/bin/env bash
# jlms — JARVIS LM Studio cluster control CLI
# Audit & control LM Studio cluster M1 (127.0.0.1:1234) + M2 (127.0.0.1:18800)
#                                    + M5 Ollama (127.0.0.1:18800)
# Author: JARVIS / cowork-system
set -euo pipefail

# -------------------------------------------------------------- config
M1_HOST="127.0.0.1"; M1_PORT="1234"
M2_HOST="127.0.0.1"; M2_PORT="1234"
M5_HOST="127.0.0.1"; M5_PORT="11434"

SSH_M2="ssh -i ${HOME}/jarvis/infra/config/ssh-access/jarvis_ed25519 -o IdentitiesOnly=yes -o ConnectTimeout=4 -o StrictHostKeyChecking=accept-new turbo@${M2_HOST}"
SSH_M5="ssh -i ${HOME}/.ssh/jarvis_cluster -o ConnectTimeout=4 -o StrictHostKeyChecking=accept-new turbo@${M5_HOST}"

SNAP_DIR="${HOME}/jarvis/logs/lms-snapshots"
LMS_LOG_CANDIDATES=(
  "${HOME}/.lmstudio/server-logs.json"
  "${HOME}/.cache/lm-studio/server-logs.json"
  "/tmp/lmstudio-server.log"
  "${HOME}/.lmstudio/logs/server.log"
)

mkdir -p "${SNAP_DIR}"

# colors
if [[ -t 1 ]]; then
  C_RED=$'\033[31m'; C_GRN=$'\033[32m'; C_YEL=$'\033[33m'
  C_BLU=$'\033[34m'; C_DIM=$'\033[2m'; C_BLD=$'\033[1m'; C_RST=$'\033[0m'
else
  C_RED=""; C_GRN=""; C_YEL=""; C_BLU=""; C_DIM=""; C_BLD=""; C_RST=""
fi

# ----------------------------------------------------------- helpers
_die()   { echo "${C_RED}error:${C_RST} $*" >&2; exit 1; }
_info()  { echo "${C_BLU}::${C_RST} $*"; }
_ok()    { echo "${C_GRN}ok${C_RST} $*"; }
_warn()  { echo "${C_YEL}!!${C_RST} $*"; }

_have() { command -v "$1" >/dev/null 2>&1; }

# parse JSON: jq if available, else python3
_json() {
  if _have jq; then jq -r "$@"
  else python3 -c "
import sys,json
try: d=json.load(sys.stdin)
except Exception as e: print(''); sys.exit(0)
# tiny query lang: supports .data[].id  or  .[].id  or  .data|length
q=sys.argv[1] if len(sys.argv)>1 else '.'
def walk(o,path):
  for p in path:
    if p=='': continue
    if p.endswith(']'):
      key=p[:-3]
      if key: o=o.get(key,[])
    elif p in ('length','count'):
      return len(o) if hasattr(o,'__len__') else 0
    else:
      if isinstance(o,list): o=[x.get(p) for x in o if isinstance(x,dict)]
      elif isinstance(o,dict): o=o.get(p)
def emit(o):
  if isinstance(o,list):
    for x in o: print(x if not isinstance(x,(dict,list)) else json.dumps(x))
  elif o is None: pass
  else: print(o)
parts=[p for p in q.replace('|',' ').split() ]
# fallback minimal eval via dot-path
import re
m=re.match(r'^\.(data\[\]\.)?([A-Za-z0-9_]+)$',q)
if m and m.group(1):
  obj=d.get('data',d) if isinstance(d,dict) else d
  for x in obj:
    if isinstance(x,dict): print(x.get(m.group(2),''))
  sys.exit(0)
m=re.match(r'^\.data\|length$',q)
if m:
  obj=d.get('data',[]) if isinstance(d,dict) else d
  print(len(obj) if hasattr(obj,'__len__') else 0); sys.exit(0)
m=re.match(r'^\.models\[\]\.([A-Za-z0-9_]+)$',q)
if m:
  obj=d.get('models',[]) if isinstance(d,dict) else d
  for x in obj:
    if isinstance(x,dict): print(x.get(m.group(1),''))
  sys.exit(0)
print(json.dumps(d))
" "$1"
  fi
}

# curl wrapper: gives http_code:body, timeout-safe
_curl() {
  local url="$1" tout="${2:-5}"
  curl -fsS --max-time "${tout}" "$url" 2>/dev/null || return 1
}

_curl_code() {
  local url="$1" tout="${2:-5}"
  curl -s -o /dev/null -w "%{http_code}" --max-time "${tout}" "$url" 2>/dev/null
}

_latency_ms() {
  local url="$1"
  local t
  t=$(curl -s -o /dev/null -w "%{time_total}" --max-time 6 "$url" 2>/dev/null || echo "0")
  python3 -c "import sys;print(int(float('${t:-0}')*1000))" 2>/dev/null || echo "0"
}

# ------------------------------------------------------------- usage
usage() {
cat <<'EOF'
jlms — JARVIS LM Studio cluster control CLI

USAGE
  jlms <command> [args]

COMMANDS
  status              Résumé M1/M2/M5: ping, port, #modèles, latence
  models [node]       Liste modèles (node = m1|m2|m5|all, defaut: all)
  clients             Connexions actives :1234 M1 groupées par IP
  requests [n]        N dernières requêtes des logs LMStudio (defaut: 20)
  gpu                 nvidia-smi + per-process VRAM (fallback si NVML KO)
  top                 Vue continue (refresh 5s): clients + requests + gpu
  watch               Alias de top
  snapshot            Dump horodaté dans ~/jarvis/logs/lms-snapshots/
  history [n]         Liste les N derniers snapshots (defaut: 10)
  latency [model]     Bench 3 chat completions p50/p95 (defaut: qwen/qwen3.5-9b)
  kill-runaway        Kill lm-ask.sh zombies + curl chat/completions >60s
  restart [m1|m2]     Restart LM Studio M1 (kill+launch) ou ssh M2
  report              Rapport markdown complet stdout
  help                Affiche cette aide

EXAMPLES
  jlms status
  jlms models m1
  jlms latency qwen3.5-coder-14b
  jlms snapshot && jlms report > /tmp/lms-now.md
  jlms top
  jlms kill-runaway

ENDPOINTS
  M1 = 127.0.0.1:1234   (LMStudio leader, 6 GPU)
  M2 = 127.0.0.1:18800 (LMStudio reasoning)
  M5 = 127.0.0.1:18800 (Ollama backup)
EOF
}

# ----------------------------------------------------------- status
cmd_status() {
  printf "%-4s %-22s %-7s %-7s %-9s %-9s\n" "NODE" "ENDPOINT" "PING" "PORT" "MODELS" "LAT(ms)"
  printf "%-4s %-22s %-7s %-7s %-9s %-9s\n" "----" "--------" "----" "----" "------" "-------"
  _row M1 "${M1_HOST}:${M1_PORT}" "http://${M1_HOST}:${M1_PORT}/v1/models"
  _row M2 "${M2_HOST}:${M2_PORT}" "http://${M2_HOST}:${M2_PORT}/v1/models"
  _row M5 "${M5_HOST}:${M5_PORT}" "http://${M5_HOST}:${M5_PORT}/api/tags"
}

_row() {
  local node="$1" addr="$2" url="$3"
  local host="${addr%%:*}" port="${addr##*:}"
  local ping_s="DOWN" port_s="-" cnt="-" lat="-"
  if ping -c1 -W1 "$host" >/dev/null 2>&1; then ping_s="UP"; fi
  if timeout 2 bash -c ">/dev/tcp/${host}/${port}" 2>/dev/null; then port_s="OPEN"; fi
  local body
  body=$(_curl "$url" 4 || true)
  if [[ -n "$body" ]]; then
    if [[ "$url" == *"/v1/models"* ]]; then
      cnt=$(echo "$body" | python3 -c "import sys,json;d=json.load(sys.stdin);print(len(d.get('data',[])))" 2>/dev/null || echo "?")
    else
      cnt=$(echo "$body" | python3 -c "import sys,json;d=json.load(sys.stdin);print(len(d.get('models',[])))" 2>/dev/null || echo "?")
    fi
    lat=$(_latency_ms "$url")
  fi
  local color="$C_GRN"
  [[ "$ping_s" = "DOWN" || "$port_s" = "-" ]] && color="$C_RED"
  [[ "$cnt" = "-" && "$port_s" = "OPEN" ]]   && color="$C_YEL"
  printf "${color}%-4s${C_RST} %-22s %-7s %-7s %-9s %-9s\n" "$node" "$addr" "$ping_s" "$port_s" "$cnt" "$lat"
}

# ----------------------------------------------------------- models
cmd_models() {
  local target="${1:-all}"
  case "$target" in
    m1|M1)  _list_models M1 "http://${M1_HOST}:${M1_PORT}/v1/models" lms ;;
    m2|M2)  _list_models M2 "http://${M2_HOST}:${M2_PORT}/v1/models" lms ;;
    m5|M5)  _list_models M5 "http://${M5_HOST}:${M5_PORT}/api/tags" ollama ;;
    all)
      _list_models M1 "http://${M1_HOST}:${M1_PORT}/v1/models" lms
      echo
      _list_models M2 "http://${M2_HOST}:${M2_PORT}/v1/models" lms
      echo
      _list_models M5 "http://${M5_HOST}:${M5_PORT}/api/tags" ollama
      ;;
    *) _die "node inconnu: $target (m1|m2|m5|all)" ;;
  esac
}

_list_models() {
  local node="$1" url="$2" kind="$3"
  echo "${C_BLD}[$node]${C_RST} $url"
  local body
  body=$(_curl "$url" 4 || true)
  if [[ -z "$body" ]]; then _warn "  pas de réponse"; return 0; fi
  if [[ "$kind" = "lms" ]]; then
    echo "$body" | python3 -c "
import sys,json
try: d=json.load(sys.stdin)
except: print('  parse error'); sys.exit(0)
for m in d.get('data',[]):
  print(f\"  - {m.get('id','?')}\")
" 2>/dev/null || _warn "  parse error"
  else
    echo "$body" | python3 -c "
import sys,json
try: d=json.load(sys.stdin)
except: print('  parse error'); sys.exit(0)
for m in d.get('models',[]):
  sz=m.get('size',0)
  print(f\"  - {m.get('name','?')}  ({sz//1024//1024} MB)\" if sz else f\"  - {m.get('name','?')}\")
" 2>/dev/null || _warn "  parse error"
  fi
}

# ----------------------------------------------------------- clients
cmd_clients() {
  echo "${C_BLD}Active connexions sur :${M1_PORT} (M1)${C_RST}"
  if ! _have ss; then _warn "ss manquant"; return 0; fi
  local raw
  raw=$(ss -tn 2>/dev/null | awk -v p=":${M1_PORT}" '$4 ~ p || $5 ~ p {print}')
  if [[ -z "$raw" ]]; then
    _info "aucune connexion active"
    return 0
  fi
  echo "$raw" | awk '{
    split($5,a,":"); ip=a[1]
    if(ip=="" || ip=="0.0.0.0") next
    cnt[ip]++
  } END {
    for(i in cnt) printf "  %-18s  %d conn\n", i, cnt[i]
  }' | sort -k3 -nr
  echo
  echo "${C_DIM}Total raw lignes ss: $(echo "$raw" | wc -l)${C_RST}"
}

# ----------------------------------------------------------- requests
cmd_requests() {
  local n="${1:-20}"
  local logf=""
  for c in "${LMS_LOG_CANDIDATES[@]}"; do
    [[ -f "$c" ]] && { logf="$c"; break; }
  done
  if [[ -z "$logf" ]]; then
    _warn "aucun log LMStudio trouvé. Cherché:"
    for c in "${LMS_LOG_CANDIDATES[@]}"; do echo "    $c"; done
    return 0
  fi
  echo "${C_BLD}Dernières $n requêtes — $logf${C_RST}"
  if [[ "$logf" = *.json ]]; then
    tail -n "$n" "$logf" | python3 -c "
import sys,json
for line in sys.stdin:
  line=line.strip()
  if not line: continue
  try: e=json.loads(line)
  except: print('  raw:',line[:120]); continue
  t=e.get('timestamp',e.get('time',''))
  m=e.get('model',e.get('modelId',''))
  ip=e.get('clientIp',e.get('ip',''))
  ev=e.get('event',e.get('type',''))
  print(f\"  {t}  {ev:12} {ip:16} {m}\")
" 2>/dev/null || tail -n "$n" "$logf"
  else
    tail -n "$n" "$logf"
  fi
}

# --------------------------------------------------------------- gpu
cmd_gpu() {
  if ! _have nvidia-smi; then _warn "nvidia-smi indisponible"; return 0; fi
  echo "${C_BLD}GPU global${C_RST}"
  if ! nvidia-smi --query-gpu=index,name,utilization.gpu,memory.used,memory.total,temperature.gpu \
        --format=csv,noheader,nounits 2>/dev/null \
        | awk -F',' '{printf "  GPU%-2s %-22s util=%s%%  mem=%s/%s MB  T=%s°C\n",$1,$2,$3,$4,$5,$6}'; then
    _warn "NVML lecture KO"
  fi
  echo
  echo "${C_BLD}Per-process VRAM${C_RST}"
  if ! nvidia-smi --query-compute-apps=pid,process_name,used_memory \
        --format=csv,noheader,nounits 2>/dev/null \
        | awk -F',' '{printf "  pid=%-7s %-30s vram=%s MB\n",$1,$2,$3}'; then
    _warn "  process listing KO (NVML)"
  fi
}

# --------------------------------------------------------------- top
cmd_top() {
  if ! _have watch; then _die "watch manquant"; fi
  exec watch -c -n5 -t "bash '$0' _top_inline"
}

cmd__top_inline() {
  date
  echo "=========================================="
  cmd_status
  echo
  cmd_clients
  echo
  cmd_gpu
  echo
  cmd_requests 8
}

# ---------------------------------------------------------- snapshot
cmd_snapshot() {
  local ts; ts=$(date +%Y%m%d-%H%M%S)
  local out="${SNAP_DIR}/${ts}.md"
  {
    echo "# LMS snapshot — ${ts}"
    echo ""
    echo "## status"; echo '```'; cmd_status 2>&1; echo '```'
    echo "## models"; echo '```'; cmd_models all 2>&1; echo '```'
    echo "## clients"; echo '```'; cmd_clients 2>&1; echo '```'
    echo "## gpu"; echo '```'; cmd_gpu 2>&1; echo '```'
    echo "## requests (50)"; echo '```'; cmd_requests 50 2>&1; echo '```'
  } > "$out"
  _ok "snapshot écrit: $out"
  echo "$out"
}

# ----------------------------------------------------------- history
cmd_history() {
  local n="${1:-10}"
  ls -1t "${SNAP_DIR}"/*.md 2>/dev/null | head -n "$n" \
    | awk '{printf "  %s\n",$0}' \
    || _info "aucun snapshot"
}

# ----------------------------------------------------------- latency
cmd_latency() {
  local model="${1:-qwen/qwen3.5-9b}"
  local url="http://${M1_HOST}:${M1_PORT}/v1/chat/completions"
  echo "${C_BLD}Bench latency model=$model x3 → $url${C_RST}"
  local times=()
  for i in 1 2 3; do
    local t
    t=$(curl -s -o /dev/null -w "%{time_total}" --max-time 30 \
        -H "Content-Type: application/json" \
        -d "{\"model\":\"$model\",\"messages\":[{\"role\":\"user\",\"content\":\"ping\"}],\"max_tokens\":4,\"stream\":false}" \
        "$url" 2>/dev/null || echo "0")
    times+=("$t")
    printf "  call %d: %ss\n" "$i" "$t"
  done
  python3 -c "
import sys
xs=sorted(float(x) for x in '${times[*]}'.split())
def pct(p): return xs[min(len(xs)-1,int(round((len(xs)-1)*p/100)))]
print(f'  p50={pct(50)*1000:.0f}ms  p95={pct(95)*1000:.0f}ms  min={xs[0]*1000:.0f}ms  max={xs[-1]*1000:.0f}ms')
"
}

# ------------------------------------------------------- kill-runaway
cmd_kill_runaway() {
  echo "${C_BLD}Recherche processus runaway...${C_RST}"
  # lm-ask.sh zombies
  local zpids
  zpids=$(pgrep -f "lm-ask.sh" 2>/dev/null || true)
  if [[ -n "$zpids" ]]; then
    for p in $zpids; do
      local et; et=$(ps -o etimes= -p "$p" 2>/dev/null | tr -d ' ' || echo 0)
      if [[ "${et:-0}" -gt 60 ]]; then
        _warn "kill lm-ask.sh pid=$p (etime=${et}s)"
        kill "$p" 2>/dev/null || true
      fi
    done
  fi
  # curl chat/completions long
  local cpids
  cpids=$(pgrep -f "curl.*chat/completions" 2>/dev/null || true)
  if [[ -n "$cpids" ]]; then
    for p in $cpids; do
      local et; et=$(ps -o etimes= -p "$p" 2>/dev/null | tr -d ' ' || echo 0)
      if [[ "${et:-0}" -gt 60 ]]; then
        _warn "kill curl pid=$p (etime=${et}s)"
        kill "$p" 2>/dev/null || true
      fi
    done
  fi
  _ok "fini."
}

# ----------------------------------------------------------- restart
cmd_restart() {
  local node="${1:-}"
  [[ -z "$node" ]] && _die "usage: jlms restart [m1|m2]"
  case "$node" in
    m1|M1)
      _info "kill processus LM Studio M1 local..."
      # NB: le nom du binaire varie selon la version : LM_Studio.AppImage (underscore),
      # LM-Studio-0.4.20-1-x64.AppImage (TIRET), et le lanceur monté /tmp/.mount_LM-Stu*/lm-studio
      # (minuscules). Les trois motifs sont nécessaires — vérifié 2026-08-01 : avec le seul
      # motif underscore/espace, l'AppImage à tiret survivait et le restart était silencieusement vide.
      pkill -f "LM[-_ ]Studio" 2>/dev/null || true
      pkill -f "mount_LM-Stu" 2>/dev/null || true
      pkill -f "lms-server" 2>/dev/null || true
      sleep 2
      # verrous Electron orphelins → toute relance sortirait en silence
      rm -f "$HOME/.config/LM Studio/SingletonLock" "$HOME/.config/LM Studio/SingletonCookie" "$HOME/.config/LM Studio/SingletonSocket" 2>/dev/null || true
      export PATH="$HOME/.lmstudio/bin:$PATH"
      # Protection matérielle : GPU2 (GTX 1660S, index PCI 2) a le VENTILATEUR MORT.
      # L'ordre PCI_BUS_ID garantit que les index CUDA == index nvidia-smi ;
      # sans lui, CUDA trie par perf et les index ne désignent pas les mêmes cartes.
      export CUDA_DEVICE_ORDER=PCI_BUS_ID
      export CUDA_VISIBLE_DEVICES=0,1,3
      if _have lms; then
        _info "relance via 'lms server start'"
        lms server start || _warn "lms server start KO"
      else
        _warn "binaire 'lms' introuvable — relance GUI manuellement"
      fi
      ;;
    m2|M2)
      _info "restart M2 via ssh..."
      $SSH_M2 'pkill -f "LM Studio" 2>/dev/null; sleep 2; (lms server start || true)' \
        || _warn "ssh M2 KO"
      ;;
    *) _die "node inconnu: $node" ;;
  esac
}

# ------------------------------------------------------------ report
cmd_report() {
  local ts; ts=$(date -Iseconds)
  cat <<EOF
# LMS cluster report — ${ts}

## 1. Status
\`\`\`
$(cmd_status 2>&1)
\`\`\`

## 2. Modèles disponibles
\`\`\`
$(cmd_models all 2>&1)
\`\`\`

## 3. Clients actifs M1
\`\`\`
$(cmd_clients 2>&1)
\`\`\`

## 4. GPU
\`\`\`
$(cmd_gpu 2>&1)
\`\`\`

## 5. Dernières requêtes
\`\`\`
$(cmd_requests 20 2>&1)
\`\`\`

## 6. Recommandations
- Vérifier que p95 latency < 2000 ms sur modèles 9b (sinon: GPU saturée)
- Si M2 :1234 ne répond pas mais ping OK → relancer GUI (\`jlms restart m2\`)
- Si > 5 clients actifs depuis même IP → enquêter (boucle bug ?)
- Avant tout kill: \`jlms snapshot\` puis \`jlms report\`
EOF
}

# ------------------------------------------------------------- main
case "${1:-help}" in
  status)       shift; cmd_status "$@" ;;
  models)       shift; cmd_models "$@" ;;
  clients)      shift; cmd_clients "$@" ;;
  requests)     shift; cmd_requests "$@" ;;
  gpu)          shift; cmd_gpu "$@" ;;
  top|watch)    shift; cmd_top "$@" ;;
  _top_inline)  shift; cmd__top_inline "$@" ;;
  snapshot)     shift; cmd_snapshot "$@" ;;
  history)      shift; cmd_history "$@" ;;
  latency)      shift; cmd_latency "$@" ;;
  kill-runaway) shift; cmd_kill_runaway "$@" ;;
  restart)      shift; cmd_restart "$@" ;;
  report)       shift; cmd_report "$@" ;;
  help|-h|--help) usage ;;
  *) usage; exit 1 ;;
esac
