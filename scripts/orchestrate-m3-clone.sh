#!/bin/bash
# ==============================================================================
# Script d'Orchestration Post-Clonage et Adaptation pour M3 (HP Portable)
# ==============================================================================
set -euo pipefail

LOG_FILE="/home/pamerys/jarvis/logs/orchestrate_m3_clone.log"
exec > >(tee -a "${LOG_FILE}") 2>&1

echo "=== Début de l'orchestration post-clonage pour M3 : $(date) ==="

# 1. Attente de la fin du clonage ddrescue dans tmux
echo "Attente de la fin du clonage ddrescue (session tmux 'clonage-crucial')..."
while sudo tmux has-session -t clonage-crucial 2>/dev/null; do
    sleep 60
done
echo "La session tmux 'clonage-crucial' est terminée."

# 2. Audit de l'état du clonage via le mapfile
MAPFILE="/home/pamerys/jarvis/logs/clonage_root.map"
if [ ! -f "${MAPFILE}" ]; then
    echo "ERREUR : Mapfile de clonage racine introuvable à ${MAPFILE} !"
    exit 1
fi

NON_COPIE=$(grep -v '^#' "${MAPFILE}" | grep -E '\s+(\?|-)$' || true)

if [ -n "${NON_COPIE}" ]; then
    echo "ERREUR : Le clonage ddrescue ne s'est pas terminé complètement ou a échoué."
    echo "Blocs restants non copiés :"
    echo "${NON_COPIE}"
    exit 1
fi

echo "Le clonage physique par secteur est terminé à 100% avec succès."
python3 /home/pamerys/jarvis/scripts/util_logging.py --service jarvis.antigravity-cloning --message "Clonage physique par secteurs terminé à 100% avec succès." || true

# 3. Différenciation des UUIDs du disque Crucial cible
echo "Exécution de differentiate-clone-uuids.sh..."
sudo bash /home/pamerys/jarvis/scripts/differentiate-clone-uuids.sh

# 4. Adaptation de l'image pour le portable M3 (HP sans GPU)
DST_DISK=$(lsblk -o NAME,MODEL -dn | grep -E "CT1000BX500|Crucial" | awk '{print $1}' | head -n 1)
if [ -z "${DST_DISK}" ]; then
    echo "ERREUR : Impossible de détecter le SSD Crucial cible."
    exit 1
fi

DST_ROOT_DEV="/dev/${DST_DISK}2"
DST_EFI_DEV="/dev/${DST_DISK}1"
DST_ROOT_MNT="/media/turbo/root2"
DST_EFI_MNT="/media/turbo/EFI2"

echo "Montage des partitions cibles pour adaptation..."
sudo mkdir -p "${DST_ROOT_MNT}" "${DST_EFI_MNT}"
sudo mount "${DST_ROOT_DEV}" "${DST_ROOT_MNT}"
sudo mount "${DST_EFI_DEV}" "${DST_EFI_MNT}"

echo "Exécution de adapt-laptop-m3.sh..."
sudo bash /home/pamerys/jarvis/scripts/adapt-laptop-m3.sh

# 5. Sécurité : Installation de GRUB pour BIOS Legacy (i386-pc)
# Remonter les partitions si adapt-laptop-m3.sh les a démontées
if ! mountpoint -q "${DST_ROOT_MNT}"; then
    sudo mount "${DST_ROOT_DEV}" "${DST_ROOT_MNT}"
fi

echo "Installation de GRUB en mode BIOS Legacy de secours sur /dev/${DST_DISK}..."
sudo grub-install --target=i386-pc --boot-directory="${DST_ROOT_MNT}/boot" --force "/dev/${DST_DISK}"

# 6. Démontage propre
echo "Démontage des partitions cibles..."
sudo umount "${DST_EFI_MNT}" 2>/dev/null || true
sudo umount "${DST_ROOT_MNT}" 2>/dev/null || true

echo "=== Fin de l'orchestration et adaptation pour M3 : $(date) ==="
python3 /home/pamerys/jarvis/scripts/util_logging.py --service jarvis.antigravity-cloning --message "Adaptation M3 (HP Portable) et installation double boot BIOS/UEFI terminées avec succès !" || true
echo '{"ts": "'$(date -Iseconds)'", "lvl": "INFO", "svc": "jarvis.antigravity-cloning", "msg": "Clonage et adaptation terminés à 100%. Prêt pour M3 (HP Portable) !"}' >> /home/pamerys/jarvis/logs/antigravity-cloning/2026-06-07.jsonl
