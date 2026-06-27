#!/usr/bin/env bash
# AbuseIPDB Check/Report — JARVIS Security
# Usage: abuseipdb-check.sh <IP> [report] [category]
set -euo pipefail

KEY_FILE="$HOME/jarvis/.secrets/abuseipdb.key"
CACHE_TTL=3600
REDIS_CLI=$(which redis-cli 2>/dev/null || echo "")
ACTION="${2:-check}"
CATEGORY="${3:-18}"  # 18=Brute-Force, 22=SSH

if [[ ! -f "$KEY_FILE" ]]; then
  echo "ERREUR: Clé AbuseIPDB manquante → $KEY_FILE" >&2
  exit 1
fi

API_KEY=$(cat "$KEY_FILE" | tr -d '\n')
IP="${1:-}"

if [[ -z "$IP" ]]; then
  echo "Usage: $0 <IP> [check|report] [category]" >&2
  exit 1
fi

# Cache Redis pour éviter de dépasser 1000 req/24h
CACHE_KEY="abuseipdb:$IP"
if [[ -n "$REDIS_CLI" && "$ACTION" == "check" ]]; then
  CACHED=$($REDIS_CLI -p 6379 GET "$CACHE_KEY" 2>/dev/null || true)
  if [[ -n "$CACHED" ]]; then
    echo "$CACHED"
    exit 0
  fi
fi

if [[ "$ACTION" == "check" ]]; then
  RESPONSE=$(curl -sS --fail \
    -G "https://api.abuseipdb.com/api/v2/check" \
    -H "Key: $API_KEY" \
    -H "Accept: application/json" \
    --data-urlencode "ipAddress=$IP" \
    --data-urlencode "maxAgeInDays=30" \
    --data-urlencode "verbose" 2>/dev/null)
  
  # Mettre en cache Redis (TTL 1h)
  if [[ -n "$REDIS_CLI" ]]; then
    $REDIS_CLI -p 6379 SETEX "$CACHE_KEY" "$CACHE_TTL" "$RESPONSE" >/dev/null 2>&1 || true
  fi
  
  # Extraire score + log si > 50
  SCORE=$(echo "$RESPONSE" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['data']['abuseConfidenceScore'])" 2>/dev/null || echo "0")
  echo "$RESPONSE"
  
  if [[ "$SCORE" -gt 50 ]]; then
    logger -t abuseipdb "HIGH RISK IP: $IP score=$SCORE"
    # Enregistrer en DB
    python3 -c "
import sqlite3, json
db = sqlite3.connect('$HOME/jarvis/data/jarvis.db')
db.execute('''CREATE TABLE IF NOT EXISTS jarvis_ip_threats (
  ip TEXT, score INTEGER, country TEXT, detected_at TEXT, action TEXT)''')
data = json.loads('$(echo "$RESPONSE" | tr "'" '"')')
d = data['data']
from datetime import datetime, timezone
db.execute('INSERT INTO jarvis_ip_threats VALUES (?,?,?,?,?)',
  (d['ipAddress'], d['abuseConfidenceScore'], d.get('countryCode',''), 
   datetime.now(timezone.utc).isoformat(), 'flagged'))
db.commit(); db.close()
" 2>/dev/null || true
  fi

elif [[ "$ACTION" == "report" ]]; then
  COMMENT="${4:-Brute-force detected by JARVIS cluster firewall}"
  curl -sS --fail \
    -X POST "https://api.abuseipdb.com/api/v2/report" \
    -H "Key: $API_KEY" \
    -H "Accept: application/json" \
    --data-urlencode "ip=$IP" \
    --data-urlencode "categories=$CATEGORY" \
    --data-urlencode "comment=$COMMENT" 2>/dev/null
  logger -t abuseipdb "REPORTED: $IP cat=$CATEGORY"
fi
