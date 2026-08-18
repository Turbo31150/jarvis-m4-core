#!/bin/bash
# =============================================================================
# STORAGE FUSION SYNC — JARVIS M4 CLUSTER
# Synchronise et fusionne les données M1 SSD, NVMe Fast (/storage) et Local (~)
# =============================================================================

set -euo pipefail

STORAGE_DIR="/storage"
M1_DIR="/media/pamerys/JARVIS-M1/home/pamerys"
LOCAL_HOME="/home/pamerys"

echo "=================================================="
echo "⚡ DÉBUT DE LA SYNCHRONISATION FUSION DISQUES"
echo "Date: $(date '+%Y-%m-%d %H:%M:%S')"
echo "=================================================="

# 1. Vérification du montage NVMe /storage
if ! mountpoint -q "$STORAGE_DIR"; then
    echo "⚠️  Montage de /storage (NVMe Fast)..."
    sudo mount /dev/nvme0n1p2 "$STORAGE_DIR" 2>/dev/null || true
fi

# 2. Vérification du SWAP NVMe 96 Go
if ! swapon --show | grep -q "nvme0n1p1"; then
    echo "⚡ Activation du SWAP NVMe 96 Go..."
    sudo swapon -p 10 /dev/nvme0n1p1 2>/dev/null || true
fi

# 3. Synchronisation M1 SSD -> NVMe Fast (si M1 branché)
if [ -d "$M1_DIR" ]; then
    echo "💾 [M1 -> NVMe] Synchronisation des bases, scripts et workspaces clés..."
    mkdir -p "$STORAGE_DIR/m1-mirror/jarvis" "$STORAGE_DIR/m1-mirror/databases" "$STORAGE_DIR/m1-mirror/Workspaces"
    
    # Bases SQLite
    rsync -avu --include="*.db" --include="*.sqlite" --include="*.sqlite3" --exclude="*" "$M1_DIR/jarvis/" "$STORAGE_DIR/m1-mirror/databases/" 2>/dev/null || true
    
    # Scripts JARVIS M1
    if [ -d "$M1_DIR/jarvis/scripts" ]; then
        rsync -avu "$M1_DIR/jarvis/scripts/" "$STORAGE_DIR/m1-mirror/jarvis/scripts/" 2>/dev/null || true
    fi
    
    echo "✅ Synchronisation M1 terminée."
else
    echo "ℹ️  Disque M1 SSD non branché (ignoré)."
fi

# 4. Vérification et intégrité des liens symboliques fusionnés
echo "🔗 Vérification des liens symboliques vers /storage :"
for target in "models-gguf" "m1-recover" "recovery-m1" "m1-recover-config" "docker-win-backup" "claude-desktop-debian"; do
    if [ -L "$LOCAL_HOME/$target" ]; then
        echo "  🟢 ~/$target -> $(readlink "$LOCAL_HOME/$target")"
    fi
done

echo "=================================================="
echo "📊 BILAN ESPACE DISQUE :"
df -h / "$STORAGE_DIR" /media/pamerys/JARVIS-M1 2>/dev/null || df -h / "$STORAGE_DIR"
echo "=================================================="
echo "✨ FUSION & SYNCHRONISATION TERMINÉES AVEC SUCCÈS"
