#!/bin/bash
# Ultra Optimizer JARVIS OS — Boost CPU, RAM, Disk I/O & Parallel Engine

echo "[1/5] Optimization Process Priorities (Nice / Ionice)..."
renice -n -5 -p $(pgrep -f "jarvis-planning-widget.py" 2>/dev/null) 2>/dev/null || true
renice -n -5 -p $(pgrep -f "openclaw-master.py" 2>/dev/null) 2>/dev/null || true

echo "[2/5] SQLite Performance Boost (WAL + Synchronous Normal + Cache Size)..."
for db in /home/pamerys/jarvis/jarvis_master.db /home/pamerys/jarvis/logs/jarvis_logs.db /home/pamerys/jarvis-cowork/etoile.db; do
  if [ -f "$db" ]; then
    sqlite3 "$db" "PRAGMA journal_mode=WAL; PRAGMA synchronous=NORMAL; PRAGMA cache_size=-64000; PRAGMA temp_store=MEMORY; PRAGMA optimize;" 2>/dev/null || true
  fi
done

echo "[3/5] Memory Compaction & Cache Release..."
sudo sysctl -w vm.dirty_background_ratio=5 2>/dev/null || true
sudo sysctl -w vm.dirty_ratio=10 2>/dev/null || true
sudo sysctl -w vm.vfs_cache_pressure=50 2>/dev/null || true

echo "[4/5] Widget Performance Sync..."
killall conky 2>/dev/null || true
DISPLAY=:0 nohup conky -c /home/pamerys/.config/conky/jarvis-system-left.conf >/dev/null 2>&1 &

echo "[5/5] Ultra Optimization Complete."
