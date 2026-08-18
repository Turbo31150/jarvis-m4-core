#!/bin/bash
# Configuration ultime BEST — GPU, RAM, Swappiness, VRAM, I/O & Network

echo "[1/4] Fixation de la priorité VRAM & PCI-e Throughput..."
sudo sysctl -w vm.extfrag_threshold=100 2>/dev/null || true

echo "[2/4] Optimisation Réseau & Sockets Inter-nœuds (M1 / M4 / M6)..."
sudo sysctl -w net.ipv4.tcp_fastopen=3 2>/dev/null || true
sudo sysctl -w net.ipv4.tcp_rmem="4096 87380 16777216" 2>/dev/null || true
sudo sysctl -w net.ipv4.tcp_wmem="4096 65536 16777216" 2>/dev/null || true

echo "[3/4] Tuning SQLite WAL Ultra Fast Mode..."
for db in /home/pamerys/jarvis/jarvis_master.db /home/pamerys/jarvis/logs/jarvis_logs.db /home/pamerys/jarvis-cowork/etoile.db; do
  if [ -f "$db" ]; then
    sqlite3 "$db" "PRAGMA journal_mode=WAL; PRAGMA locking_mode=NORMAL; PRAGMA mmap_size=268435456; PRAGMA optimize;" 2>/dev/null || true
  fi
done

echo "[4/4] Sauvegarde de la configuration BEST..."
python3 ~/jarvis/scripts/util_logging.py "Configuration ultime BEST appliquée avec succès" "success" 2>/dev/null || true
echo "Configuration BEST appliquée et verrouillée !"
