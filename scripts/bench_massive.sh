#!/bin/bash
# JARVIS Benchmark Massif — OL1 Local + M1/M2 remote
# Génère rapport JSON + SQLite
set -euo pipefail

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_DIR="/home/pamerys/jarvis/logs"
REPORT_FILE="${LOG_DIR}/bench_massif_${TIMESTAMP}.json"
mkdir -p "$LOG_DIR"

# Endpoints disponibles
declare -A NODES
NODES["OL1_ollama"]="http://127.0.0.1:11434"
NODES["M1_lmstudio"]="http://127.0.0.1:1234"
NODES["M2_lmstudio"]="http://127.0.0.1:18800"

# Modèles OL1
OLLAMA_MODELS=("qwen3:1.7b" "gemma3:4b" "deepseek-r1:7b")
ITERATIONS=10

PROMPTS=(
  "Explique le concept de transformers en ML en 2 phrases"
  "Écris une fonction Python de tri rapide"
  "Analyse les risques d un portefeuille crypto en 3 points"
)

# SQLite db
DB="/home/pamerys/jarvis/logs/bench_results.db"
python3 -c "
import sqlite3
conn = sqlite3.connect('$DB')
conn.execute('''CREATE TABLE IF NOT EXISTS bench_runs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts TEXT, node TEXT, model TEXT, prompt_idx INTEGER,
  iteration INTEGER, latency_ms REAL, tokens_out INTEGER,
  success INTEGER, error TEXT
)''')
conn.commit(); conn.close()
print('DB OK')
"

echo "=== JARVIS Benchmark Massif ${TIMESTAMP} ==="
echo "Nodes: ${!NODES[@]}"

declare -A RESULTS
TOTAL=0; ERRORS=0

bench_ollama() {
  local node="OL1_ollama"
  local url="http://127.0.0.1:11434/api/generate"
  
  for model in "${OLLAMA_MODELS[@]}"; do
    echo "  → Testing $model on $node"
    latencies=()
    tokens=()
    errs=0
    
    for ((i=1; i<=ITERATIONS; i++)); do
      for pidx in "${!PROMPTS[@]}"; do
        prompt="${PROMPTS[$pidx]}"
        start_ms=$(python3 -c "import time; print(int(time.time()*1000))")
        
        response=$(curl -s --max-time 30 -X POST "$url" \
          -H "Content-Type: application/json" \
          -d "{\"model\":\"$model\",\"prompt\":\"$prompt\",\"stream\":false,\"options\":{\"num_predict\":80}}" \
          2>/dev/null)
        
        end_ms=$(python3 -c "import time; print(int(time.time()*1000))")
        lat=$((end_ms - start_ms))
        
        success=$(echo "$response" | python3 -c "import sys,json; d=json.load(sys.stdin); print(1 if d.get('done') else 0)" 2>/dev/null || echo "0")
        tok=$(echo "$response" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('eval_count',0))" 2>/dev/null || echo "0")
        
        if [[ "$success" == "1" ]]; then
          latencies+=("$lat")
          tokens+=("$tok")
        else
          errs=$((errs+1))
          ERRORS=$((ERRORS+1))
        fi
        TOTAL=$((TOTAL+1))
      done
    done
    
    # Calcul stats
    if [[ ${#latencies[@]} -gt 0 ]]; then
      # Écrire les latences dans un fichier temporaire
      printf '%s\n' "${latencies[@]}" > /tmp/lats_$$.txt
      printf '%s\n' "${tokens[@]}" > /tmp/toks_$$.txt
      stats=$(python3 - <<PYEOF
import json, statistics
lats = [int(x) for x in open('/tmp/lats_$$.txt').read().split() if x]
toks = [int(x) for x in open('/tmp/toks_$$.txt').read().split() if x]
lats_sorted = sorted(lats) if lats else [0]
n = len(lats_sorted)
p50 = lats_sorted[int(n*0.50)] if n > 1 else lats_sorted[0]
p95 = lats_sorted[int(n*0.95)] if n > 1 else lats_sorted[-1]
p99 = lats_sorted[int(n*0.99)] if n > 1 else lats_sorted[-1]
print(json.dumps({'p50':p50,'p95':p95,'p99':p99,'mean':int(statistics.mean(lats)) if lats else 0,'min':min(lats) if lats else 0,'max':max(lats) if lats else 0,'avg_tokens':int(statistics.mean(toks)) if toks else 0}))
PYEOF
)
      rm -f /tmp/lats_$$.txt /tmp/toks_$$.txt
      echo "    Stats $model: $stats"
      python3 -c "
import sqlite3, json
conn = sqlite3.connect('$DB')
stats = json.loads('$stats')
conn.execute('INSERT INTO bench_runs (ts,node,model,prompt_idx,iteration,latency_ms,tokens_out,success,error) VALUES (?,?,?,?,?,?,?,?,?)',
  ('$TIMESTAMP','$node','$model',0,$ITERATIONS,stats['mean'],stats['avg_tokens'],1,''))
conn.commit(); conn.close()
"
    fi
    echo "    Errors: $errs/$((ITERATIONS * ${#PROMPTS[@]}))"
  done
}

bench_lmstudio() {
  local node="$1"
  local url="${NODES[$node]}"
  
  # Check disponibilité
  if ! curl -s --max-time 3 "${url}/v1/models" &>/dev/null; then
    echo "  ⚠ $node OFFLINE - skip"
    return
  fi
  
  echo "  → $node ONLINE"
  models=$(curl -s --max-time 5 "${url}/v1/models" | python3 -c "import json,sys; [print(m['id']) for m in json.load(sys.stdin).get('data',[])]" 2>/dev/null | head -2)
  
  for model in $models; do
    latencies=()
    for ((i=1; i<=5; i++)); do
      prompt="${PROMPTS[0]}"
      start_ms=$(python3 -c "import time; print(int(time.time()*1000))")
      response=$(curl -s --max-time 30 -X POST "${url}/v1/completions" \
        -H "Content-Type: application/json" \
        -d "{\"model\":\"$model\",\"prompt\":\"$prompt\",\"max_tokens\":80}" 2>/dev/null)
      end_ms=$(python3 -c "import time; print(int(time.time()*1000))")
      latencies+=($((end_ms - start_ms)))
    done
    echo "    $node $model: ${latencies[*]}"
  done
}

# SNAPSHOT SYSTÈME AVANT
SYS_BEFORE=$(python3 -c "
import psutil, json
print(json.dumps({
  'cpu_percent': psutil.cpu_percent(interval=1),
  'ram_used_gb': round(psutil.virtual_memory().used/1e9,2),
  'ram_total_gb': round(psutil.virtual_memory().total/1e9,2),
  'disk_free_gb': round(psutil.disk_usage('/').free/1e9,2)
}))
" 2>/dev/null || echo '{"cpu_percent":0,"ram_used_gb":0}')

echo "System BEFORE: $SYS_BEFORE"
echo ""

# EXÉCUTION
bench_ollama
bench_lmstudio "M1_lmstudio"
bench_lmstudio "M2_lmstudio"

# SNAPSHOT SYSTÈME APRÈS
SYS_AFTER=$(python3 -c "
import psutil, json
print(json.dumps({
  'cpu_percent': psutil.cpu_percent(interval=1),
  'ram_used_gb': round(psutil.virtual_memory().used/1e9,2),
  'ram_total_gb': round(psutil.virtual_memory().total/1e9,2),
}))
" 2>/dev/null || echo '{"cpu_percent":0}')

# RAPPORT FINAL JSON
ERROR_RATE=$(python3 -c "print(round($ERRORS/$TOTAL*100,1) if $TOTAL>0 else 0)")
STABILITY_SCORE=$(python3 -c "print(round(100-$ERROR_RATE,1))")

python3 -c "
import json, sqlite3
conn = sqlite3.connect('$DB')
rows = conn.execute('SELECT node,model,AVG(latency_ms),MAX(latency_ms),SUM(success),COUNT(*) FROM bench_runs WHERE ts=\"$TIMESTAMP\" GROUP BY node,model').fetchall()
summary = [{'node':r[0],'model':r[1],'avg_lat_ms':round(r[2],0),'max_lat_ms':round(r[3],0),'success_rate':round(r[4]/r[5]*100,1)} for r in rows]
report = {
  'timestamp': '$TIMESTAMP',
  'total_requests': $TOTAL,
  'errors': $ERRORS,
  'error_rate_pct': $ERROR_RATE,
  'stability_score': $STABILITY_SCORE,
  'system_before': $SYS_BEFORE,
  'system_after': $SYS_AFTER,
  'results': summary
}
with open('$REPORT_FILE','w') as f: json.dump(report, f, indent=2)
print(json.dumps(report, indent=2))
conn.close()
"

echo ""
echo "✅ Rapport: $REPORT_FILE"
echo "✅ DB: $DB"
echo "📊 Stability score: ${STABILITY_SCORE}/100"
