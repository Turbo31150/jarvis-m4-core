#!/bin/bash
exec 8>/tmp/gsl.lock; flock -n 8 || exit 0
# gemini-session-logger.sh — Log chaque appel Gemini CLI dans SQLite
# Usage: source depuis gemini-smart.sh ou appel direct
# DB: ~/.gemini/stats.db

DB="$HOME/.gemini/stats.db"

_gemini_db_init() {
  sqlite3 "$DB" "CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts_start INTEGER NOT NULL,
    ts_end   INTEGER,
    hour     INTEGER,
    model    TEXT,
    prompt_len INTEGER,
    output_len INTEGER,
    duration_ms INTEGER,
    status   TEXT,  -- ok | timeout | quota | error | hung
    error_msg TEXT,
    via      TEXT   -- direct | lumen | whisperflow | telegram | cli
  );
  CREATE INDEX IF NOT EXISTS idx_hour ON sessions(hour);
  CREATE INDEX IF NOT EXISTS idx_status ON sessions(status);"
}

gemini_log_start() {
  # $1=model $2=prompt_len $3=via
  local model="${1:-gemini-3.7-flash}" plen="${2:-0}" via="${3:-direct}"
  local ts=$(date +%s%3N) hr=$(date +%H)
  _gemini_db_init
  echo $(sqlite3 "$DB" "INSERT INTO sessions(ts_start,hour,model,prompt_len,via) VALUES($ts,$hr,'$model',$plen,'$via'); SELECT last_insert_rowid();")
}

gemini_log_end() {
  # $1=id $2=status $3=output_len $4=error_msg
  local id="$1" status="${2:-ok}" olen="${3:-0}" err="${4:-}"
  local ts_end=$(date +%s%3N)
  sqlite3 "$DB" "UPDATE sessions SET
    ts_end=$ts_end,
    duration_ms=($ts_end - ts_start),
    output_len=$olen,
    status='$status',
    error_msg='${err//\'/\'\'}'
  WHERE id=$id;" 2>/dev/null
}

gemini_analyze() {
  # Affiche les meilleures périodes + taux blocage
  _gemini_db_init
  echo "=== Gemini CLI — Session Scoring ==="
  echo ""
  echo "Meilleures heures (taux succès ≥ 70%) :"
  sqlite3 -column -header "$DB" "
    SELECT
      printf('%02d:00', hour) AS heure,
      COUNT(*) AS total,
      SUM(CASE WHEN status='ok' THEN 1 ELSE 0 END) AS ok,
      ROUND(100.0*SUM(CASE WHEN status='ok' THEN 1 ELSE 0 END)/COUNT(*),1) AS pct_ok,
      ROUND(AVG(CASE WHEN status='ok' THEN duration_ms END)/1000.0,1) AS avg_dur_s
    FROM sessions
    WHERE total > 0
    GROUP BY hour
    HAVING total >= 2
    ORDER BY pct_ok DESC, avg_dur_s ASC
    LIMIT 8;
  " 2>/dev/null

  echo ""
  echo "Top erreurs (7 derniers jours) :"
  sqlite3 -column "$DB" "
    SELECT status, COUNT(*) as n FROM sessions
    WHERE ts_start > (strftime('%s','now')-604800)*1000
    GROUP BY status ORDER BY n DESC;
  " 2>/dev/null

  echo ""
  echo "Sessions récentes (10 dernières) :"
  sqlite3 -column -header "$DB" "
    SELECT
      datetime(ts_start/1000,'unixepoch','localtime') as debut,
      model,
      via,
      status,
      ROUND(duration_ms/1000.0,1) as dur_s,
      output_len
    FROM sessions ORDER BY id DESC LIMIT 10;
  " 2>/dev/null
}

gemini_ingest_telemetry() {
  # Parse ~/.gemini/telemetry.jsonl → injecte dans sessions SQLite
  # Format telemetry: {"eventName":"...","timestamp":..., "model":"...", "latencyMs":...}
  local tfile="$HOME/.gemini/telemetry.jsonl"
  [[ ! -f "$tfile" ]] && return 0
  _gemini_db_init

  local count=0
  while IFS= read -r line; do
    [[ -z "$line" ]] && continue
    local event ts model latency status
    event=$(echo "$line" | python3 -c "import json,sys; d=json.loads(sys.stdin.read()); print(d.get('eventName',''))" 2>/dev/null)
    ts=$(echo "$line" | python3 -c "import json,sys; d=json.loads(sys.stdin.read()); print(int(d.get('timestamp',0)))" 2>/dev/null)
    model=$(echo "$line" | python3 -c "import json,sys; d=json.loads(sys.stdin.read()); print(d.get('model','unknown'))" 2>/dev/null)
    latency=$(echo "$line" | python3 -c "import json,sys; d=json.loads(sys.stdin.read()); print(int(d.get('latencyMs',0)))" 2>/dev/null)
    status=$(echo "$line" | python3 -c "import json,sys; d=json.loads(sys.stdin.read()); print('ok' if d.get('success',True) else 'error')" 2>/dev/null)
    [[ -z "$ts" || "$ts" == "0" ]] && continue
    local hr=$(date -d "@$((ts/1000))" +%H 2>/dev/null || echo "0")
    sqlite3 "$DB" "INSERT OR IGNORE INTO sessions(ts_start,ts_end,hour,model,duration_ms,status,via)
      VALUES($ts,$((ts+latency)),$hr,'$model',$latency,'$status','telemetry');" 2>/dev/null
    ((count++)) || true
  done < "$tfile"
  echo "[telemetry] $count entrées ingérées"
}

gemini_best_hours() {
  # Retourne la meilleure heure courante pour décider du modèle
  _gemini_db_init
  local now_hr=$(date +%H | sed 's/^0//')
  sqlite3 "$DB" "
    SELECT CASE
      WHEN COUNT(*) < 3 THEN 'unknown'
      WHEN ROUND(100.0*SUM(CASE WHEN status='ok' THEN 1 ELSE 0 END)/COUNT(*),0) >= 70 THEN 'good'
      ELSE 'bad'
    END
    FROM sessions WHERE hour=$now_hr;" 2>/dev/null
}

# Appel direct : gemini-session-logger.sh analyze
[[ "$1" == "analyze" || "$1" == "stats" ]] && { gemini_analyze; exit 0; }
[[ "$1" == "init" ]] && { _gemini_db_init; echo "DB init: $DB"; exit 0; }
[[ "$1" == "ingest" ]] && { gemini_ingest_telemetry; exit 0; }
[[ "$1" == "best-hour" ]] && { gemini_best_hours; exit 0; }
