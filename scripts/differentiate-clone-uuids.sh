#!/bin/bash
# ==============================================================================
# Script de Différenciation de Clone Système JARVIS
# Change les UUIDs de la cible après clonage physique pour éviter les collisions
# et met à jour la configuration de boot sur la cible.
# ==============================================================================

set -euo pipefail

LOG_FILE="/home/pamerys/jarvis/logs/differentiate_clone.log"
exec > >(tee -a "${LOG_FILE}") 2>&1

echo "=== Début de la différenciation des UUIDs de la cible : $(date) ==="

# Détection automatique des disques
SRC_PARTITION=$(lsblk -o NAME,MOUNTPOINT -n | grep -w "/" | awk '{print $1}' | tr -d '└─├─')
SRC_DISK=$(echo "${SRC_PARTITION}" | sed 's/[0-9]*$//')
if [ -z "${SRC_DISK}" ]; then
    SRC_DISK="sdb"
fi

DST_DISK=$(lsblk -o NAME,MODEL -dn | grep -E "CT1000BX500|Crucial" | awk '{print $1}' | head -n 1)
if [ -z "${DST_DISK}" ]; then
    echo "ERREUR : Impossible de détecter le SSD Crucial cible."
    exit 1
fi

SRC_ROOT_DEV="/dev/${SRC_DISK}2"
SRC_EFI_DEV="/dev/${SRC_DISK}1"
DST_ROOT_DEV="/dev/${DST_DISK}2"
DST_EFI_DEV="/dev/${DST_DISK}1"

DST_ROOT_MNT="/media/turbo/root2"
DST_EFI_MNT="/media/turbo/EFI2"

# 1. Vérification que les volumes cibles ne sont pas montés
echo "Démontage des volumes cibles..."
sudo umount -f "${DST_ROOT_DEV}" 2>/dev/null || true
sudo umount -f "${DST_EFI_DEV}" 2>/dev/null || true

# 2. Récupération des UUIDs source actuels
SRC_ROOT_UUID=$(blkid -o value -s UUID "${SRC_ROOT_DEV}")
SRC_EFI_UUID=$(blkid -o value -s UUID "${SRC_EFI_DEV}")

echo "UUID Source Racine actuel : ${SRC_ROOT_UUID}"
echo "UUID Source EFI actuel : ${SRC_EFI_UUID}"

# 3. Génération des nouveaux UUIDs pour la cible
NEW_ROOT_UUID=$(uuidgen)
# UUID FAT32 est un ID de volume de 8 caractères hexa (ex: A5DD-8FE3 -> A5DD8FE3)
NEW_EFI_ID=$(openssl rand -hex 4 | tr 'a-f' 'A-F')
# Formater l'UUID FAT32 avec le tiret standard pour blkid
NEW_EFI_UUID="${NEW_EFI_ID:0:4}-${NEW_EFI_ID:4:4}"

echo "Nouveau UUID Racine généré pour la cible : ${NEW_ROOT_UUID}"
echo "Nouveau UUID EFI généré pour la cible : ${NEW_EFI_UUID} (Volume ID: ${NEW_EFI_ID})"

# 4. Application du nouvel UUID ext4 sur la partition Racine cible
echo "Application du nouvel UUID sur la partition racine cible (${DST_ROOT_DEV})..."
sudo tune2fs -U "${NEW_ROOT_UUID}" "${DST_ROOT_DEV}"

# 5. Application du nouvel UUID FAT32 sur la partition EFI cible
# Pour FAT32, le formatage avec l'option -i est le moyen le plus sûr de changer l'ID du volume.
# Nous sauvegardons temporairement le contenu de l'EFI source (ou de la cible clonée)
echo "Sauvegarde des fichiers de boot EFI..."
EFI_TEMP_DIR=$(mktemp -d)
mkdir -p "${DST_EFI_MNT}"
sudo mount "${DST_EFI_DEV}" "${DST_EFI_MNT}"
rsync -av "${DST_EFI_MNT}/" "${EFI_TEMP_DIR}/"
sudo umount "${DST_EFI_MNT}"

echo "Formatage de la partition EFI cible avec le nouvel ID de volume..."
sudo mkfs.vfat -F 32 -i "${NEW_EFI_ID}" -n "EFI2" "${DST_EFI_DEV}"

echo "Restauration des fichiers de boot EFI..."
sudo mount "${DST_EFI_DEV}" "${DST_EFI_MNT}"
rsync -av "${EFI_TEMP_DIR}/" "${DST_EFI_MNT}/"
rm -rf "${EFI_TEMP_DIR}"

# 6. Montage de la partition racine cible pour modification
echo "Montage de la partition racine cible (${DST_ROOT_DEV})..."
mkdir -p "${DST_ROOT_MNT}"
sudo mount "${DST_ROOT_DEV}" "${DST_ROOT_MNT}"

# 7. Correction du fstab sur la cible
TARGET_FSTAB="${DST_ROOT_MNT}/etc/fstab"
if [ -f "${TARGET_FSTAB}" ]; then
    echo "Mise à jour des UUIDs dans ${TARGET_FSTAB}..."
    # Remplacement des UUIDs sources par les nouveaux UUIDs cibles
    # Note : Le clonage physique a écrasé le fstab de la cible avec celui de la source.
    # Donc le fstab de la cible contient actuellement les UUIDs sources.
    sudo sed -i "s/UUID=${SRC_ROOT_UUID}/UUID=${NEW_ROOT_UUID}/g" "${TARGET_FSTAB}"
    sudo sed -i "s/UUID=${SRC_EFI_UUID}/UUID=${NEW_EFI_UUID}/g" "${TARGET_FSTAB}"
    echo "fstab mis à jour avec succès."
else
    echo "ERREUR : fstab introuvable sur la cible !"
fi

# 8. Correction de la configuration GRUB sur la cible
TARGET_GRUB_CFG="${DST_ROOT_MNT}/boot/grub/grub.cfg"
if [ -f "${TARGET_GRUB_CFG}" ]; then
    echo "Mise à jour des UUIDs dans ${TARGET_GRUB_CFG}..."
    # Remplacer toutes les occurrences de l'UUID racine source par le nouvel UUID racine cible
    sudo sed -i "s/${SRC_ROOT_UUID}/${NEW_ROOT_UUID}/g" "${TARGET_GRUB_CFG}"
    # Remplacer toutes les occurrences de l'UUID EFI source par le nouvel UUID EFI cible
    sudo sed -i "s/${SRC_EFI_UUID}/${NEW_EFI_UUID}/g" "${TARGET_GRUB_CFG}"
    echo "grub.cfg mis à jour avec succès."
else
    echo "AVERTISSEMENT : grub.cfg introuvable sur la cible."
fi

# 9. Installation de GRUB universel de secours sur la cible
echo "Installation de GRUB universel amovible avec les nouveaux UUIDs..."
sudo grub-install --target=x86_64-efi \
                  --efi-directory="${DST_EFI_MNT}" \
                  --boot-directory="${DST_ROOT_MNT}/boot" \
                  --removable \
                  --recheck

# 10. Recréation des répertoires système virtuels vides sur la cible
echo "Recréation des répertoires système virtuels vides sur la cible..."
sudo mkdir -p "${DST_ROOT_MNT}"/{dev,proc,sys,tmp,run,mnt,media,storage}
sudo chmod 1777 "${DST_ROOT_MNT}/tmp"

# Nettoyage des montages
sudo umount "${DST_EFI_MNT}"
sudo umount "${DST_ROOT_MNT}"

echo "=== Différenciation des UUIDs de la cible terminée avec succès : $(date) ==="
