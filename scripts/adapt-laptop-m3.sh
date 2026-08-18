#!/bin/bash
# ==============================================================================
# Script d'Adaptation Multi-Machine Cible M3 (HP Portable Entreprise sans GPU)
# A exécuter sur le point de montage du clone (/media/turbo/root2)
# ==============================================================================

set -euo pipefail

MNT_ROOT="/media/turbo/root2"
MNT_EFI="/media/turbo/EFI2"
TARGET_HOSTNAME="jarvis-m3"

echo "=== Démarrage de l'adaptation HP Portable M3 (sans GPU) ==="

if [ ! -f "${MNT_ROOT}/etc/fstab" ]; then
    echo "ERREUR : Le point de montage ${MNT_ROOT} ne contient pas de racine système."
    exit 1
fi

# 1. Montage des systèmes de fichiers virtuels pour chroot
echo "[1/8] Montage des systèmes de fichiers virtuels..."
mkdir -p "${MNT_ROOT}"/{dev,proc,sys,run}
mount --bind /dev "${MNT_ROOT}/dev"
mount --bind /dev/pts "${MNT_ROOT}/dev/pts"
mount --bind /proc "${MNT_ROOT}/proc"
mount --bind /sys "${MNT_ROOT}/sys"
mount --bind /run "${MNT_ROOT}/run"

# Sauvegarde / copie temporaire de la config DNS pour apt dans chroot
cp /etc/resolv.conf "${MNT_ROOT}/etc/resolv.conf"

# 2. Nettoyage spécifique GPU NVIDIA et CUDA (inutile et ralentit le boot sur laptop HP)
echo "[2/8] Suppression des packages NVIDIA/CUDA dans le clone..."
chroot "${MNT_ROOT}" bash -c "
    export DEBIAN_FRONTEND=noninteractive
    apt-get purge -y '*nvidia*' '*cuda*' 'cuda-*' 'nvidia-*' || true
    apt-get autoremove -y || true
"

# 3. Installation des firmwares et drivers pour CPU Intel/AMD et WiFi HP
echo "[3/8] Installation des pilotes vidéo intégrés et WiFi (Intel/AMD/Realtek)..."
chroot "${MNT_ROOT}" bash -c "
    export DEBIAN_FRONTEND=noninteractive
    apt-get update -qq
    apt-get install -y --no-install-recommends \
        xserver-xorg-video-intel \
        xserver-xorg-video-amdgpu \
        mesa-vulkan-drivers \
        va-driver-all \
        i965-va-driver \
        intel-media-va-driver \
        firmware-linux-nonfree \
        firmware-iwlwifi \
        firmware-realtek \
        firmware-amd-graphics \
        network-manager \
        network-manager-gnome \
        tlp \
        tlp-rdw \
        acpid \
        acpi \
        gnome-core \
        gdm3 || true
"

# 4. Désactivation des services GPU d'origine dans systemd
echo "[4/8] Désactivation des services JARVIS GPU d'origine..."
chroot "${MNT_ROOT}" bash -c "
    systemctl disable lmstudio jarvis-lmstudio jarvis-cuda-monitor jarvis-vocal-whisper nvidia-persistenced docker-swarm || true
    systemctl enable NetworkManager || true
    systemctl enable tlp || true
    systemctl enable acpid || true
    systemctl set-default graphical.target || true
    systemctl enable gdm3 || true
"

# 5. Configuration réseau universelle via NetworkManager (essentiel pour WiFi portable)
echo "[5/8] Configuration de Netplan pour NetworkManager..."
NETPLAN_FILE="${MNT_ROOT}/etc/netplan/01-network-manager-all.yaml"
rm -f "${MNT_ROOT}/etc/netplan"/*.yaml
cat > "${NETPLAN_FILE}" << 'EOF'
network:
  version: 2
  renderer: NetworkManager
EOF
chmod 600 "${NETPLAN_FILE}"

# Nettoyage udev et NM states
rm -f "${MNT_ROOT}/etc/udev/rules.d/70-persistent-net.rules"
rm -f "${MNT_ROOT}/var/lib/NetworkManager/NetworkManager.state"

# 6. Adaptation Hostname et hosts
echo "[6/8] Adaptation du Hostname (${TARGET_HOSTNAME})..."
echo "${TARGET_HOSTNAME}" > "${MNT_ROOT}/etc/hostname"
sed -i "s/127\.0\.1\.1.*/127.0.1.1\t${TARGET_HOSTNAME}/" "${MNT_ROOT}/etc/hosts" 2>/dev/null || true

# 7. Configuration de GRUB pour démarrage immédiat et propre (sans blocage nvidia)
echo "[7/8] Configuration de GRUB sur la cible..."
GRUB_DEFAULT="${MNT_ROOT}/etc/default/grub"
if [ -f "${GRUB_DEFAULT}" ]; then
    sed -i 's/GRUB_TIMEOUT=.*/GRUB_TIMEOUT=2/' "${GRUB_DEFAULT}"
    sed -i 's/GRUB_TIMEOUT_STYLE=.*/GRUB_TIMEOUT_STYLE=menu/' "${GRUB_DEFAULT}"
    sed -i 's/GRUB_CMDLINE_LINUX_DEFAULT=.*/GRUB_CMDLINE_LINUX_DEFAULT="quiet splash pci=noaer"/' "${GRUB_DEFAULT}"
    grep -q "GRUB_DISABLE_OS_PROBER" "${GRUB_DEFAULT}" || echo 'GRUB_DISABLE_OS_PROBER=true' >> "${GRUB_DEFAULT}"
fi

# Mettre à jour grub.cfg dans le chroot
chroot "${MNT_ROOT}" update-grub || true

# 8. Réinstallation du bootloader GRUB universel (UEFI removable)
echo "[8/8] Réinstallation de GRUB universel..."
grub-install --target=x86_64-efi \
             --efi-directory="${MNT_EFI}" \
             --boot-directory="${MNT_ROOT}/boot" \
             --removable \
             --recheck

# Démonter les dossiers système virtuels
echo "Démontage des dossiers virtuels..."
umount "${MNT_ROOT}/dev/pts" 2>/dev/null || true
umount "${MNT_ROOT}/dev" 2>/dev/null || true
umount "${MNT_ROOT}/proc" 2>/dev/null || true
umount "${MNT_ROOT}/sys" 2>/dev/null || true
umount "${MNT_ROOT}/run" 2>/dev/null || true

echo "=== Adaptation terminée avec succès ! ==="
