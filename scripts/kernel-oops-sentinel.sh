#!/usr/bin/env bash
# Sentinelle Oops noyau — détecte corruption mémoire, journalise SQL, alerte.
# 0-token. Posé le 2026-08-03 suite au crash RAM mixte 3400 MT/s.
set -uo pipefail
DB="$HOME/jarvis/logs/jarvis_logs.db"
LOG="$HOME/jarvis/logs/kernel-oops.log"
TS=$(date -Iseconds)

# 1. Oops du boot PRECEDENT (le crash qui a tué la machine)
PREV=$(journalctl -b -1 -k --no-pager 2>/dev/null | grep -cE "Oops:|kernel BUG|general protection")
PREV_RIP=$(journalctl -b -1 -k --no-pager 2>/dev/null | grep -m1 "RIP: 0010:" | sed 's/.*RIP: 0010://')
# 2. Oops du boot COURANT (corruption en cours = danger immédiat)
CUR=$(journalctl -b 0 -k --no-pager 2>/dev/null | grep -cE "Oops:|kernel BUG|general protection")
# 3. Machine Check Exceptions
MCE=$(journalctl -b 0 -k --no-pager 2>/dev/null | grep -c "Hardware Error")
# 4. Profil mémoire (détection kits mixtes)
MIX=$(sudo -n dmidecode -t memory 2>/dev/null | grep "Part Number" | sort -u | wc -l)

VERDICT="OK"
(( PREV > 0 )) && VERDICT="CRASH_PRECEDENT"
(( CUR  > 0 )) && VERDICT="CORRUPTION_ACTIVE"
(( MCE  > 0 )) && VERDICT="${VERDICT}+MCE"
(( MIX  > 1 )) && VERDICT="${VERDICT}+RAM_MIXTE"

echo "$TS verdict=$VERDICT oops_prev=$PREV oops_cur=$CUR mce=$MCE kits_ram=$MIX rip=${PREV_RIP:-none}" >> "$LOG"

sqlite3 "$DB" "CREATE TABLE IF NOT EXISTS kernel_oops(ts TEXT, verdict TEXT, oops_prev INT, oops_cur INT, mce INT, kits_ram INT, rip TEXT);
INSERT INTO kernel_oops VALUES('$TS','$VERDICT',$PREV,$CUR,$MCE,$MIX,'${PREV_RIP//\'/}');" 2>/dev/null

if [[ "$VERDICT" != "OK" ]]; then
  MSG="⚠️ M1 noyau: $VERDICT | oops(boot-1)=$PREV oops(now)=$CUR mce=$MCE kits=$MIX | RIP:${PREV_RIP:-n/a}"
  command -v notify-send >/dev/null && DISPLAY=:0 notify-send -u normal -t 10000 "JARVIS — corruption mémoire" "$MSG" 2>/dev/null
  echo "$MSG"
  exit 1
fi
echo "OK — aucun Oops, aucune MCE."
