#!/bin/bash
# GNOME Minimal Setup — JARVIS Cluster
# Applique la config minimale partagée sur n'importe quelle machine
# Usage: bash setup-gnome-minimal.sh

KEEP="ubuntu-dock@ubuntu.com ubuntu-appindicators@ubuntu.com tiling-assistant@ubuntu.com"

echo "=== GNOME Minimal Setup ==="

# 1. Supprimer extensions non-essentielles
for d in ~/.local/share/gnome-shell/extensions/*/; do
    ext=$(basename "$d")
    echo "$KEEP" | grep -qF "$ext" || { rm -rf "$d"; echo "REMOVED: $ext"; }
done

# 2. Désactiver tout sauf essentiels
for ext in $(gnome-extensions list --enabled 2>/dev/null); do
    echo "$KEEP" | grep -qF "$ext" || gnome-extensions disable "$ext" 2>/dev/null
done

# 3. Décharger modèle Ollama si actif
curl -s http://127.0.0.1:11434/api/generate -d '{"model":"gemma3:4b","keep_alive":0}' 2>/dev/null | grep -q done && echo "Ollama model unloaded"

# 4. Drop page cache
sudo sh -c 'echo 1 > /proc/sys/vm/drop_caches' 2>/dev/null && echo "Page cache cleared"

echo "Extensions actives:"
gnome-extensions list --enabled 2>/dev/null
echo "RAM libre: $(free -m | awk 'NR==2{print $4}')MB"
