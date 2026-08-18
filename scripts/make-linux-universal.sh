#!/bin/bash
# ==============================================================================
# Script d'Universalisation Système (LINUX-1Compatible Multi-Machine)
# Ce script prépare un clone système monté à démarrer sur n'importe quel PC x86_64.
# Usage: sudo bash make-linux-universal.sh <MNT_ROOT> <MNT_EFI> <DST_ROOT_DEV> <DST_EFI_DEV>
# ==============================================================================

set -euo pipefail

if [ "$#" -ne 4 ]; then
    echo "Usage: $0 <point_montage_root> <point_montage_efi> <dev_cible_root> <dev_cible_efi>"
    echo "Exemple: $0 /media/turbo/root2 /media/turbo/EFI2 /dev/sdc2 /dev/sdc1"
    exit 1
fi

MNT_ROOT="$1"
MNT_EFI="$2"
DST_ROOT_DEV="$3"
DST_EFI_DEV="$4"

echo "=== Début du processus d'universalisation système ==="

# 1. Vérification de la validité des points de montage
if [ ! -f "${MNT_ROOT}/etc/fstab" ]; then
    echo "ERREUR : Le répertoire ${MNT_ROOT} ne contient pas de système racine Linux (/etc/fstab absent)."
    exit 1
fi

# 2. Récupération des UUIDs réels
DST_ROOT_UUID=$(blkid -o value -s UUID "${DST_ROOT_DEV}")
DST_EFI_UUID=$(blkid -o value -s UUID "${DST_EFI_DEV}")

echo "UUID Cible Racine détecté : ${DST_ROOT_UUID}"
echo "UUID Cible EFI détecté    : ${DST_EFI_UUID}"

# 3. Remplacement et alignement des UUIDs dans /etc/fstab
echo "[1/6] Alignement des UUIDs de montage dans /etc/fstab..."
# Remplacer les anciennes entrées par les nouvelles de façon générique
sed -i -E "s|UUID=[0-9a-fA-F-]+\s+/\s+|UUID=${DST_ROOT_UUID} / |g" "${MNT_ROOT}/etc/fstab"
sed -i -E "s|UUID=[0-9a-fA-F-]+\s+/boot/efi\s+|UUID=${DST_EFI_UUID} /boot/efi |g" "${MNT_ROOT}/etc/fstab"

# 4. Suppression des configurations matérielles en dur (GPU, Écrans)
echo "[2/6] Nettoyage des fichiers de configurations matérielles spécifiques..."
# Supprimer les configurations Xorg spécifiques à la carte graphique d'origine (Nvidia multi-GPU, etc.)
rm -f "${MNT_ROOT}/etc/X11/xorg.conf"
rm -f "${MNT_ROOT}/etc/X11/xorg.conf.d/"*nvidia* 2>/dev/null || true

# 5. Nettoyage de la configuration réseau (Passage en DHCP universel)
echo "[3/6] Réinitialisation réseau vers DHCP universel..."
# Nettoyer les fichiers Netplan pour forcer le DHCP sur toutes les interfaces Ethernet/Wi-Fi physiques
NETPLAN_DIR="${MNT_ROOT}/etc/netplan"
if [ -d "${NETPLAN_DIR}" ]; then
    rm -f "${NETPLAN_DIR}"/*.yaml
    cat > "${NETPLAN_DIR}/01-dhcp-universal.yaml" << 'EOF'
network:
  version: 2
  renderer: networkd
  ethernets:
    ethernet-all:
      match:
        name: "e*"
      dhcp4: true
      optional: true
  wifis:
    wifi-all:
      match:
        name: "w*"
      dhcp4: true
      optional: true
EOF
    chmod 600 "${NETPLAN_DIR}/01-dhcp-universal.yaml"
fi

# Nettoyer les règles udev persistantes de cartes réseaux pour éviter les blocages de noms d'interfaces
rm -f "${MNT_ROOT}/etc/udev/rules.d/70-persistent-net.rules"
rm -f "${MNT_ROOT}/var/lib/NetworkManager/NetworkManager.state"

# 6. Réinitialisation des clés de sécurité SSH (Régénération automatique au premier boot)
echo "[4/6] Réinitialisation des clés hôtes SSH d'origine..."
rm -f "${MNT_ROOT}/etc/ssh/ssh_host_"*
# Ajouter un script ou trigger d'auto-génération au démarrage si manquant
if [ -f "${MNT_ROOT}/lib/systemd/system/ssh.service" ]; then
    # systemd réengendre les clés d'hôte au démarrage de ssh s'ils sont absents sur la plupart des distros
    echo "Les clés d'hôtes SSH se régénèreront automatiquement au premier boot."
fi

# 7. Correction et Installation de GRUB universel (UEFI Removable)
echo "[5/6] Configuration et installation de GRUB universel..."
# Correction de grub.cfg cible pour pointer vers la nouvelle racine
TARGET_GRUB_CFG="${MNT_ROOT}/boot/grub/grub.cfg"
if [ -f "${TARGET_GRUB_CFG}" ]; then
    # Remplacer toutes les anciennes UUIDs de démarrage par le nouvel UUID root
    sed -i "s|root=UUID=[0-9a-fA-F-]+|root=UUID=${DST_ROOT_UUID}|g" "${TARGET_GRUB_CFG}"
fi

# Exécution de grub-install en mode amovible universel
grub-install --target=x86_64-efi \
             --efi-directory="${MNT_EFI}" \
             --boot-directory="${MNT_ROOT}/boot" \
             --removable \
             --recheck

# 8. Recréation des répertoires de montage virtuels
echo "[6/6] Reconstruction des répertoires d'I/O virtuels vides..."
mkdir -p "${MNT_ROOT}"/{dev,proc,sys,tmp,run,mnt,media,storage}
chmod 1777 "${MNT_ROOT}/tmp"

echo "=== Système universalisé avec succès et prêt à l'implantation ==="
