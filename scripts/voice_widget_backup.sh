#!/bin/bash
# Sauvegarde widget vocal — idempotent, dédupé sur sha256
# Usage: voice_widget_backup.sh [--push]
set -e
DB=/home/pamerys/jarvis/data/jarvis.db
NODE="${JARVIS_NODE:-M5}"
PUSH=0
[ "$1" = "--push" ] && PUSH=1

# Backup pré-modif (rotation 7j)
mkdir -p /home/pamerys/jarvis/backups
find /home/pamerys/jarvis/backups -name "jarvis.db.before_widget_*.bak" -mtime +7 -delete 2>/dev/null
cp "$DB" "/home/turbo/jarvis/backups/jarvis.db.before_widget_$(date +%Y%m%d_%H%M%S).bak"

# Schéma (idempotent)
sqlite3 "$DB" <<'SCHEMA'
CREATE TABLE IF NOT EXISTS widget_meta (key TEXT PRIMARY KEY, value TEXT, updated_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS widget_scripts (
  path TEXT, node TEXT, bytes INTEGER, mode TEXT, mtime TEXT, sha256 TEXT, content BLOB,
  backup_at TEXT DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY(path, node));
CREATE TABLE IF NOT EXISTS widget_services (
  name TEXT, node TEXT, scope TEXT, unit_path TEXT, state TEXT, active TEXT, content TEXT,
  backup_at TEXT DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY(name, node, scope));
CREATE TABLE IF NOT EXISTS widget_autostart (
  name TEXT, node TEXT, path TEXT, content TEXT, backup_at TEXT DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY(name, node));
CREATE TABLE IF NOT EXISTS widget_keybindings (
  slot TEXT, node TEXT, name TEXT, binding TEXT, command TEXT, backup_at TEXT DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY(slot, node));
CREATE TABLE IF NOT EXISTS widget_configs (
  path TEXT, node TEXT, bytes INTEGER, mtime TEXT, content TEXT, backup_at TEXT DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY(path, node));
CREATE TABLE IF NOT EXISTS widget_state (
  node TEXT, key TEXT, value TEXT, captured_at TEXT DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY(node, key));
CREATE TABLE IF NOT EXISTS widget_journal (
  service TEXT, node TEXT, captured_at TEXT DEFAULT CURRENT_TIMESTAMP, lines TEXT, PRIMARY KEY(service, node));
CREATE TABLE IF NOT EXISTS widget_history (
  id INTEGER PRIMARY KEY AUTOINCREMENT, node TEXT, kind TEXT, target TEXT,
  sha256_before TEXT, sha256_after TEXT, changed_at TEXT DEFAULT CURRENT_TIMESTAMP);
SCHEMA

python3 - <<PY
import os, sqlite3, hashlib, subprocess, datetime
db = "$DB"; NODE = "$NODE"
con = sqlite3.connect(db); cur = con.cursor()

def fmeta(p):
    st = os.stat(p)
    return st.st_size, oct(st.st_mode)[-4:], \
           subprocess.check_output(['date','-d','@%d'%int(st.st_mtime),'+%F %T']).decode().strip()

scripts = [
  '/home/pamerys/jarvis/scripts/voice_widget.py',
  '/home/pamerys/jarvis/scripts/voice-widget.py',
  '/home/pamerys/jarvis/scripts/voice_widget.sh',
  '/home/pamerys/jarvis/scripts/voice-widget.sh',
  '/home/pamerys/jarvis/scripts/voice_pilot.py',
  '/home/pamerys/jarvis/scripts/voice-dictate.sh',
  '/home/pamerys/jarvis/scripts/voice-hud.sh',
  '/home/pamerys/jarvis/scripts/jarvis_voice_hud.py',
  '/home/pamerys/jarvis/scripts/ptt-toggle.sh',
  '/home/pamerys/jarvis/scripts/ptt-mode-toggle.sh',
  '/home/pamerys/jarvis/scripts/ptt-widget.sh',
  '/home/pamerys/jarvis/scripts/whisper_bridge.py',
  '/home/pamerys/jarvis/scripts/post-reboot-gpu-whisper.sh',
  '/home/pamerys/jarvis/scripts/gemini-voice-bridge.sh',
  '/home/pamerys/jarvis/scripts/voice_widget_backup.sh',
  '/home/pamerys/jarvis/scripts/voice_widget_restore.sh',
]
changed = 0
for p in scripts:
    if not os.path.isfile(p): continue
    b = open(p,'rb').read(); sz,mode,mt = fmeta(p); h = hashlib.sha256(b).hexdigest()
    old = cur.execute("SELECT sha256 FROM widget_scripts WHERE path=? AND node=?",(p,NODE)).fetchone()
    if old and old[0] == h:
        continue  # dédupe
    cur.execute("INSERT OR REPLACE INTO widget_scripts(path,node,bytes,mode,mtime,sha256,content) VALUES(?,?,?,?,?,?,?)",
                (p,NODE,sz,mode,mt,h,b))
    cur.execute("INSERT INTO widget_history(node,kind,target,sha256_before,sha256_after) VALUES(?,?,?,?,?)",
                (NODE,'script',p,old[0] if old else None,h))
    changed += 1

services = [
  ('jarvis-voice-widget.service','user','/home/turbo/.config/systemd/user/jarvis-voice-widget.service'),
  ('jarvis-voice-pilot.service','user','/home/pamerys/.config/systemd/user/jarvis-voice-pilot.service'),
  ('jarvis-whisper.service','user','/home/pamerys/.config/systemd/user/jarvis-whisper.service'),
  ('jarvis-vocal-whisper.service','user','/home/pamerys/.config/systemd/user/jarvis-vocal-whisper.service'),
  ('jarvis-vocal-health.service','user','/home/pamerys/.config/systemd/user/jarvis-vocal-health.service'),
  ('jarvis-voice-widget-backup.service','user','/home/turbo/.config/systemd/user/jarvis-voice-widget-backup.service'),
  ('jarvis-voice-widget-backup.timer','user','/home/turbo/.config/systemd/user/jarvis-voice-widget-backup.timer'),
  ('jarvis-whisper.service','system','/etc/systemd/system/jarvis-whisper.service'),
  ('jarvis-whisper-api.service','system','/etc/systemd/system/jarvis-whisper-api.service'),
  ('jarvis-whisper-bridge.service','system','/etc/systemd/system/jarvis-whisper-bridge.service'),
  ('jarvis-voice.service','system','/etc/systemd/system/jarvis-voice.service'),
  ('jarvis-voice-learner.service','system','/etc/systemd/system/jarvis-voice-learner.service'),
]
for unit, scope, path in services:
    if not os.path.isfile(path): continue
    flag = '--user' if scope == 'user' else '--system'
    def sysctl(args):
        try: return subprocess.check_output(['systemctl',flag]+args,stderr=subprocess.DEVNULL).decode().strip()
        except: return 'unknown'
    state = sysctl(['is-enabled',unit]); active = sysctl(['is-active',unit])
    cur.execute("INSERT OR REPLACE INTO widget_services(name,node,scope,unit_path,state,active,content) VALUES(?,?,?,?,?,?,?)",
                (unit,NODE,scope,path,state,active,open(path).read()))

# Journal logs (50 lignes par service voice)
for unit in ['jarvis-voice-pilot.service','jarvis-whisper-bridge.service','jarvis-whisper-api.service']:
    scope = '--user' if 'voice-pilot' in unit else '--system'
    try:
        out = subprocess.check_output(
            ['journalctl',scope,'-u',unit,'-n','50','--no-pager','-o','short'],
            stderr=subprocess.DEVNULL, timeout=5).decode()
    except: out = ''
    cur.execute("INSERT OR REPLACE INTO widget_journal(service,node,lines) VALUES(?,?,?)",(unit,NODE,out))

autostart = [
  '/home/turbo/.config/autostart/jarvis-ptt-widget.desktop',
  '/home/turbo/.config/autostart/jarvis-voice-widget.desktop',
  '/home/turbo/.config/autostart/jarvis-hud.desktop',
  '/home/turbo/.config/autostart/jarvis-widgets.desktop',
  '/home/pamerys/.config/autostart/WhisperFlow.desktop',
]
for p in autostart:
    if not os.path.isfile(p): continue
    cur.execute("INSERT OR REPLACE INTO widget_autostart(name,node,path,content) VALUES(?,?,?,?)",
                (os.path.basename(p), NODE, p, open(p).read()))

for p in ['/home/turbo/.config/jarvis/ptt-mode','/home/turbo/.config/jarvis/voice_hud.json']:
    if not os.path.isfile(p): continue
    sz,mode,mt = fmeta(p)
    cur.execute("INSERT OR REPLACE INTO widget_configs(path,node,bytes,mtime,content) VALUES(?,?,?,?,?)",
                (p, NODE, sz, mt, open(p).read()))

for slot in ['custom0','custom1','custom2','custom3','custom4']:
    base = f"org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/{slot}/"
    def gs(k):
        try: return subprocess.check_output(['gsettings','get',base,k],stderr=subprocess.DEVNULL).decode().strip().strip("'")
        except: return ''
    name = gs('name')
    if not name: continue
    if any(t in name for t in ['JARVIS','Mic','PTT','Voice','Widget']):
        cur.execute("INSERT OR REPLACE INTO widget_keybindings(slot,node,name,binding,command) VALUES(?,?,?,?,?)",
                    (slot, NODE, name, gs('binding'), gs('command')))

for k,v in [
    ('schema_version','2'),('node',NODE),('ip','192.168.1.94'),('role','interface-relay'),
    ('description','Backup auto widget vocal — idempotent, dédupé, avec journal logs'),
    ('last_run', datetime.datetime.now().isoformat()),
    ('scripts_changed', str(changed)),
]:
    cur.execute("INSERT OR REPLACE INTO widget_meta(key,value) VALUES(?,?)",(k,v))

try: proc = subprocess.check_output(['pgrep','-af','voice_pilot|voice-widget|jarvis_voice_hud|ptt-toggle|whisper']).decode()
except: proc=''
mode = open('/home/turbo/.config/jarvis/ptt-mode').read().strip() if os.path.exists('/home/turbo/.config/jarvis/ptt-mode') else ''
hud = open('/home/turbo/.config/jarvis/voice_hud.json').read().strip() if os.path.exists('/home/turbo/.config/jarvis/voice_hud.json') else ''
for k,v in [('active_processes',proc),('ptt_current_mode',mode),('voice_hud_state',hud),
            ('whisper_endpoint_m1','http://192.168.1.85:1234'),('whisper_endpoint_m2','http://192.168.1.26:1234')]:
    cur.execute("INSERT OR REPLACE INTO widget_state(node,key,value) VALUES(?,?,?)",(NODE,k,v))

con.commit(); con.close()
print(f"OK changed={changed}")
PY

if [ "$PUSH" = "1" ]; then
  REPO=/tmp/jarvis-tasks-sync
  [ -d "$REPO/.git" ] || gh repo clone Turbo31150/jarvis-machines-private "$REPO" -- --depth 1
  cd "$REPO" && git pull -q --rebase 2>/dev/null
  mkdir -p tasks/$NODE/voice_widget_backup
  {
    for t in widget_meta widget_scripts widget_services widget_autostart widget_keybindings widget_configs widget_state widget_journal widget_history; do
      sqlite3 "$DB" ".schema $t"
    done
  } > tasks/$NODE/voice_widget_backup/voice_widget_schema.sql
  sqlite3 "$DB" <<'SQL' > tasks/$NODE/voice_widget_backup/voice_widget_data.sql
.mode insert widget_meta
SELECT * FROM widget_meta;
.mode insert widget_services
SELECT * FROM widget_services;
.mode insert widget_autostart
SELECT * FROM widget_autostart;
.mode insert widget_keybindings
SELECT * FROM widget_keybindings;
.mode insert widget_configs
SELECT * FROM widget_configs;
.mode insert widget_state
SELECT * FROM widget_state;
SQL
  git add tasks/$NODE/voice_widget_backup
  if ! git diff --cached --quiet; then
    git commit -m "backup($NODE): widget vocal auto $(date +%F\ %H:%M)" -q
    git push origin main -q 2>&1 | tail -2
  fi
fi
# ===== BACKUP MNT (mirror externe + /mnt/backup) =====
TS=$(date +%Y%m%d_%H%M%S)
for MNT in "/media/turbo/BASE DONN2 SAUV/jarvis-backup/widget-vocal" "/mnt/backup/jarvis-widget-vocal"; do
  if [ -d "$(dirname "$MNT")" ] && { [ -w "$(dirname "$MNT")" ] || sudo -n test -w "$(dirname "$MNT")" 2>/dev/null; }; then
    DEST="$MNT/$TS"
    if [ -w "$(dirname "$MNT")" ]; then
      mkdir -p "$DEST"
    else
      sudo mkdir -p "$DEST" && sudo chown turbo:turbo "$MNT" "$DEST"
    fi
    sqlite3 "$DB" ".backup '$DEST/jarvis.db'"
    {
      for t in widget_meta widget_scripts widget_services widget_autostart widget_keybindings widget_configs widget_state widget_journal widget_history; do
        sqlite3 "$DB" ".schema $t"
      done
    } > "$DEST/widget_schema.sql"
    sqlite3 "$DB" <<'SQL' > "$DEST/widget_data.sql"
.mode insert widget_meta
SELECT * FROM widget_meta;
.mode insert widget_services
SELECT * FROM widget_services;
.mode insert widget_autostart
SELECT * FROM widget_autostart;
.mode insert widget_keybindings
SELECT * FROM widget_keybindings;
.mode insert widget_configs
SELECT * FROM widget_configs;
.mode insert widget_state
SELECT * FROM widget_state;
.mode insert widget_history
SELECT * FROM widget_history;
SQL
    tar czf "$DEST/widget_scripts.tar.gz" -C /home/pamerys/jarvis/scripts \
      voice_widget.py voice-widget.py voice_widget.sh voice-widget.sh \
      voice_pilot.py voice-dictate.sh voice-hud.sh jarvis_voice_hud.py \
      ptt-toggle.sh ptt-mode-toggle.sh ptt-widget.sh whisper_bridge.py \
      voice_widget_backup.sh voice_widget_restore.sh 2>/dev/null
    tar czf "$DEST/widget_systemd.tar.gz" -C /home/pamerys/.config/systemd/user \
      jarvis-voice-widget.service jarvis-voice-pilot.service jarvis-whisper.service \
      jarvis-vocal-whisper.service jarvis-vocal-health.service \
      jarvis-voice-widget-backup.service jarvis-voice-widget-backup.timer 2>/dev/null
    tar czf "$DEST/widget_autostart.tar.gz" -C /home/pamerys/.config/autostart \
      jarvis-ptt-widget.desktop jarvis-voice-widget.desktop jarvis-hud.desktop \
      jarvis-widgets.desktop WhisperFlow.desktop 2>/dev/null
    ln -sfn "$TS" "$MNT/latest" 2>/dev/null
    # Rotation : garder 14 derniers
    ls -1dt "$MNT"/2* 2>/dev/null | tail -n +15 | xargs -r rm -rf
    echo "  → $DEST"
  fi
done

echo "Backup done — node=$NODE"
