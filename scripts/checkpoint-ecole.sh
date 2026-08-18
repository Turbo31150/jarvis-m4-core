#!/bin/bash
# Checkpoint « au fur et à mesure » de l'app Espace Prof.
# Sauvegarde les bases SQLite (copie cohérente via .backup) dans ~/Documents
# (synchronisé Drive → tous les appareils), avec rotation 7 jours, + 1 ligne
# d'horodatage dans jarvis-checkpoints.db. Léger, on-demand, 0 token.
set -u
DAY=$(date +%F)
TS=$(date '+%Y-%m-%d %H:%M:%S')
DEST="$HOME/Documents/jarvis-backups/$DAY"
mkdir -p "$DEST"

DBS=(
  "$HOME/jarvis/webapp/ecole.db"
  "$HOME/jarvis/webapp/notes.db"
  "$HOME/jarvis/planning.db"
  "$HOME/jarvis/rdv.db"
  "$HOME/jarvis/todo.db"
  "$HOME/jarvis/budget/budget.db"
)
n=0
for db in "${DBS[@]}"; do
  [ -f "$db" ] || continue
  base=$(basename "$db")
  # copie cohérente (ne bloque pas les écritures Flask)
  if sqlite3 "$db" ".backup '$DEST/$base'" 2>/dev/null; then n=$((n+1)); else cp -f "$db" "$DEST/$base" 2>/dev/null && n=$((n+1)); fi
done

# Trace dans le journal de checkpoints
CK="$HOME/Documents/jarvis-checkpoints.db"
sqlite3 "$CK" "CREATE TABLE IF NOT EXISTS checkpoints(id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, phase TEXT, etat_md TEXT, todos_json TEXT); INSERT INTO checkpoints(ts,phase,etat_md) VALUES('$TS','backup-auto','$n bases sauvegardées dans $DEST');" 2>/dev/null

# Snapshot du CODE/vision (léger : skills + source app + plan) — 1×/jour suffit
SNAP="$DEST/code-snapshot.tgz"
if [ ! -f "$SNAP" ]; then
  tar czf "$SNAP" 2>/dev/null \
    -C "$HOME" \
    .claude/skills \
    jarvis/webapp/PLANNING-CASCADE-PARFAITE.md \
    --exclude='*.exe' --exclude='*.db' --exclude='__pycache__' \
    jarvis/webapp 2>/dev/null || true
fi

# Rotation : ne garder que les 7 derniers jours
ls -1dt "$HOME/Documents/jarvis-backups"/*/ 2>/dev/null | tail -n +8 | xargs -r rm -rf

echo "[checkpoint] $TS — $n bases + snapshot code → $DEST (rotation 7j)"
