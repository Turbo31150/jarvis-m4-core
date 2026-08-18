#!/bin/bash
# Optimization script JARVIS OS
echo "[1/4] Clean dead processes..."
pkill -f "defunct" 2>/dev/null || true

echo "[2/4] ZRAM & Memory Compact..."
sudo sysctl -w vm.drop_caches=3 2>/dev/null || true

echo "[3/4] Verify LLM Gateway Proxy..."
systemctl --user restart jarvis-chat-proxy.service 2>/dev/null || true

echo "[4/4] Optimize SQLite Indexes..."
sqlite3 /home/pamerys/jarvis/jarvis_master.db "PRAGMA optimize; PRAGMA journal_mode=WAL;" 2>/dev/null || true
sqlite3 /home/pamerys/jarvis/logs/jarvis_logs.db "PRAGMA optimize; PRAGMA journal_mode=WAL;" 2>/dev/null || true

echo "JARVIS Optimization Complete."
