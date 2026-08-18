#!/bin/bash
# Restore complet widget vocal depuis SQL
# Usage: voice_widget_restore.sh [--dry-run] [--node M5]
set -e
DB=/home/pamerys/jarvis/data/jarvis.db
NODE="${JARVIS_NODE:-M5}"
DRY=0
while [ $# -gt 0 ]; do
  case "$1" in
    --dry-run) DRY=1;;
    --node) NODE="$2"; shift;;
  esac
  shift
done

[ -f "$DB" ] || { echo "DB introuvable: $DB"; exit 1; }

cnt=$(sqlite3 "$DB" "SELECT COUNT(*) FROM widget_scripts WHERE node='$NODE'" 2>/dev/null || echo 0)
[ "$cnt" -gt 0 ] || { echo "Aucun script en DB pour node=$NODE"; exit 2; }

echo "Restauration depuis $DB (node=$NODE) — dry-run=$DRY"

python3 - <<PY
import sqlite3, os, hashlib
DB="$DB"; NODE="$NODE"; DRY=$DRY
con = sqlite3.connect(DB)

# Scripts
for path, mode, content, sha in con.execute(
    "SELECT path, mode, content, sha256 FROM widget_scripts WHERE node=?", (NODE,)):
    cur_sha = None
    if os.path.exists(path):
        cur_sha = hashlib.sha256(open(path,'rb').read()).hexdigest()
    if cur_sha == sha:
        print(f"= {path}")
        continue
    print(f"{'~' if cur_sha else '+'} {path} (mode={mode})")
    if not DRY:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path,'wb') as f: f.write(content)
        os.chmod(path, int(mode,8))

# Services (jamais auto-overwrite sans backup)
for name, scope, unit_path, content in con.execute(
    "SELECT name, scope, unit_path, content FROM widget_services WHERE node=?", (NODE,)):
    if scope == 'system':
        print(f"⚠️  {name} (system) — restore manuel: sudo tee {unit_path}")
        continue
    if os.path.exists(unit_path) and open(unit_path).read() == content:
        print(f"= {unit_path}")
        continue
    print(f"~ {unit_path}")
    if not DRY:
        os.makedirs(os.path.dirname(unit_path), exist_ok=True)
        if os.path.exists(unit_path):
            os.rename(unit_path, unit_path+'.bak')
        with open(unit_path,'w') as f: f.write(content)

# Autostart
for name, path, content in con.execute("SELECT name, path, content FROM widget_autostart WHERE node=?", (NODE,)):
    if os.path.exists(path) and open(path).read() == content:
        print(f"= {path}")
        continue
    print(f"~ {path}")
    if not DRY:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path,'w') as f: f.write(content)

# Configs
for path, content in con.execute("SELECT path, content FROM widget_configs WHERE node=?", (NODE,)):
    if os.path.exists(path) and open(path).read() == content:
        print(f"= {path}")
        continue
    print(f"~ {path}")
    if not DRY:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path,'w') as f: f.write(content)

# Keybindings
import subprocess
for slot, name, binding, command in con.execute(
    "SELECT slot, name, binding, command FROM widget_keybindings WHERE node=?", (NODE,)):
    base=f"org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/{slot}/"
    print(f"~ keybinding {slot} = '{binding}' → {command}")
    if not DRY:
        subprocess.run(['gsettings','set',base,'name', name])
        subprocess.run(['gsettings','set',base,'binding', binding])
        subprocess.run(['gsettings','set',base,'command', command])

con.close()
PY

if [ "$DRY" = "0" ]; then
  echo "Reload systemd user…"
  systemctl --user daemon-reload 2>/dev/null || true
  echo "Restauration terminée. Reboot ou relogin GNOME pour appliquer raccourcis."
fi
