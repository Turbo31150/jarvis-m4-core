#!/usr/bin/env bash
# JARVIS OS — PACKAGER POUR INSTALLATION CHEZ L'UTILISATEUR (HOME INSTALLER)
set -e

SRC_TAR="/home/pamerys/Workspaces/jarvis-linux/skills-library/dist/board_os_living_library_2026.tar.gz"
DEST_DIR="$HOME/Desktop/JARVIS_BOARD_OS_EXPORT"

echo "=== [PREPARATION DU PAQUET D'INSTALLATION PERSONNELLE] ==="
mkdir -p "$DEST_DIR"
cp "$SRC_TAR" "$DEST_DIR/board_os_living_library_2026.tar.gz"

cat << 'EOF' > "$DEST_DIR/README_INSTALLATION.txt"
===================================================================
      JARVIS BOARD OS & BIBLIOTHÈQUE VIVANTE — PACK PERSONNEL
===================================================================

Pour installer Board OS et la Bibliothèque Vivante sur votre ordinateur personnel (Linux / macOS / WSL2) :

1. Décompressez l'archive :
   tar -xvf board_os_living_library_2026.tar.gz

2. Lancez l'installeur automatique :
   cd board_os_bundle
   bash install_board_os.sh

3. Testez l'installation :
   jarvis-board ask biblio-vivante "Comment utiliser la bibliothèque ?"

===================================================================
EOF

echo "[OK] Paquet d'installation personnelle généré dans : $DEST_DIR"
