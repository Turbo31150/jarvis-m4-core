#!/usr/bin/env bash
# precompute_jour.sh — Domino matinal : pré-calcule les suggestions du jour (SQL pur,
# 0 inférence, 0 chauffe) et stocke un instantané dans ecole.db (kv: suggestions_jour).
# L'app ouvre alors la journée déjà préparée. Lancé par jarvis-precompute.timer.
set -euo pipefail
DB="$HOME/jarvis/webapp/ecole.db"
JSON="$(curl -s -m 15 http://127.0.0.1:7777/api/automations/suggestions || echo '{}')"
python3 - "$DB" "$JSON" <<'PY'
import sys, sqlite3, json
from datetime import date
db, js = sys.argv[1], sys.argv[2]
try:
    data = json.loads(js)
except Exception:
    data = {}
payload = json.dumps({"date": date.today().isoformat(),
                      "total": data.get("total", 0),
                      "suggestions": data.get("suggestions", [])}, ensure_ascii=False)
with sqlite3.connect(db) as c:
    c.execute("CREATE TABLE IF NOT EXISTS kv (k TEXT PRIMARY KEY, v TEXT, "
              "ts TEXT DEFAULT (datetime('now')))")
    c.execute("INSERT OR REPLACE INTO kv(k,v,ts) VALUES('suggestions_jour', ?, "
              "datetime('now','localtime'))", (payload,))
print(f"[precompute] {data.get('total', 0)} suggestions du jour en cache")
PY
