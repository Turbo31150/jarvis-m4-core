#!/usr/bin/env bash
# AbuseIPDB Blacklist Sync — JARVIS Security
# Télécharge blacklist confiance ≥75%, charge dans ipset, bloque via iptables
set -euo pipefail

KEY_FILE="$HOME/jarvis/.secrets/abuseipdb.key"
IPSET_NAME="abuseipdb-blacklist"
LIMIT=10000
CONFIDENCE=75

if [[ ! -f "$KEY_FILE" ]]; then echo "ERREUR: clé manquante"; exit 1; fi
API_KEY=$(cat "$KEY_FILE" | tr -d '\n')

echo "[$(date)] Téléchargement blacklist AbuseIPDB (confiance>=$CONFIDENCE%)..."

# Télécharger blacklist
BLACKLIST=$(curl -sS --fail -G "https://api.abuseipdb.com/api/v2/blacklist" \
  -H "Key: $API_KEY" \
  -H "Accept: text/plain" \
  --data-urlencode "confidenceMinimum=$CONFIDENCE" \
  --data-urlencode "limit=$LIMIT" 2>/dev/null)

COUNT=$(echo "$BLACKLIST" | wc -l)
echo "[$(date)] $COUNT IPs reçues"

# Créer/vider ipset
sudo ipset create "$IPSET_NAME" hash:ip 2>/dev/null || sudo ipset flush "$IPSET_NAME"

# Charger IPs
while IFS= read -r IP; do
  [[ -z "$IP" || "$IP" =~ ^# ]] && continue
  sudo ipset add "$IPSET_NAME" "$IP" 2>/dev/null || true
done <<< "$BLACKLIST"

# Brancher sur iptables INPUT si pas déjà fait
if ! sudo iptables -L INPUT -n | grep -q "$IPSET_NAME"; then
  sudo iptables -I INPUT 1 -m set --match-set "$IPSET_NAME" src -j DROP
  sudo iptables -I DOCKER-USER 1 -m set --match-set "$IPSET_NAME" src -j DROP
  echo "[$(date)] Règles iptables ajoutées"
fi

LOADED=$(sudo ipset list "$IPSET_NAME" | grep -c "^[0-9]" || true)
echo "[$(date)] ✅ $LOADED IPs dans $IPSET_NAME"

# Sauvegarder stats en DB
python3 -c "
import sqlite3
from datetime import datetime, timezone
db = sqlite3.connect('$HOME/jarvis/data/jarvis.db')
db.execute('''CREATE TABLE IF NOT EXISTS jarvis_security_metrics
  (metric TEXT, value INTEGER, recorded_at TEXT)''')
db.execute('INSERT INTO jarvis_security_metrics VALUES (?,?,?)',
  ('abuseipdb_blacklist_count', $LOADED, datetime.now(timezone.utc).isoformat()))
db.commit(); db.close()
" 2>/dev/null || true
