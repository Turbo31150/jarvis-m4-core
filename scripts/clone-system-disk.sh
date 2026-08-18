#!/bin/bash
# ==============================================================================
# JARVIS — clone-system-disk.sh v3.0
# Clonage système MULTI-MACHINE + Adaptation BIOS/GNOME/Drivers par profil
#
# CAHIER DES CHARGES :
#   - Clone local (SSD Crucial, Samsung) OU via SSH (M1, M3…)
#   - Adaptation automatique post-clonage selon profil machine cible :
#       • DESKTOP_GPU  : Machine de bureau avec GPU NVIDIA (M1, M2)
#       • LAPTOP_NONGPU: Portable HP Entreprise sans GPU (nouvelle M3)
#       • SERVER       : Serveur headless sans écran
#   - Boot immédiat sur n'importe quelle machine UEFI
#   - GNOME configuré et opérationnel au premier démarrage
#   - Suppression automatique des drivers GPU si cible sans GPU
#   - Adaptation réseau (WiFi auto-détecté sur laptop)
#   - GRUB universel (--removable) installé systématiquement
#
# Usage:
#   sudo bash clone-system-disk.sh                       # Auto SSD Crucial local
#   sudo bash clone-system-disk.sh --local sdd           # Force disque local
#   sudo bash clone-system-disk.sh --remote M1           # Clone SSH vers M1
#   sudo bash clone-system-disk.sh --remote M3           # Clone SSH vers M3
#   sudo bash clone-system-disk.sh --remote M3 --profile LAPTOP_NONGPU
#   sudo bash clone-system-disk.sh --list                # Lister disques
#
# Profils disponibles :
#   DESKTOP_GPU   : Bureau + NVIDIA + LMStudio (défaut M1)
#   LAPTOP_NONGPU : HP portable entreprise, pas GPU, GNOME, WiFi (M3 nouvelle)
#   SERVER        : Headless, pas d'écran, Ollama+services
#
# ==============================================================================

set -euo pipefail

# ──────────────────────────────────────────────────────────────────────────────
# CLUSTER JARVIS (GEMINI.md)
# ──────────────────────────────────────────────────────────────────────────────
declare -A CLUSTER_IPS=([M1]="192.168.0.10" [M6]="10.42.0.230")   # M2/M3/M4/M5 demontes le 2026-08-06
declare -A CLUSTER_USERS=([M1]="turbo" [M2]="turbo" [M3]="turbo" [M4]="turbo" [M5]="turbo")
declare -A CLUSTER_HOSTNAMES=([M1]="jarvis-m1" [M2]="jarvis-m2" [M3]="jarvis-m3" [M4]="jarvis-m4" [M5]="m5-omega")
declare -A CLUSTER_DST_DISKS=([M1]="sdb" [M2]="sdb" [M3]="sda" [M4]="nvme1n1" [M5]="sdd")
declare -A CLUSTER_PROFILES=([M1]="DESKTOP_GPU" [M2]="DESKTOP_GPU" [M3]="LAPTOP_NONGPU" [M4]="DESKTOP_GPU" [M5]="DESKTOP_GPU")

SSH_KEY="/home/pamerys/jarvis/infra/config/ssh-access/jarvis_ed25519"
LOG_FILE="/home/pamerys/jarvis/logs/system_clone.log"
ADAPT_SCRIPT="/home/pamerys/jarvis/scripts/adapt-machine-profile.sh"

exec > >(tee -a "${LOG_FILE}") 2>&1

# ──────────────────────────────────────────────────────────────────────────────
# Exclusions rsync
# ──────────────────────────────────────────────────────────────────────────────
RSYNC_EXCLUDES=(
    "--exclude=/dev/*"
    "--exclude=/proc/*"
    "--exclude=/sys/*"
    "--exclude=/tmp/*"
    "--exclude=/run/*"
    "--exclude=/mnt/*"
    "--exclude=/media/*"
    "--exclude=/storage/*"
    "--exclude=/var/lib/docker/*"
    "--exclude=/lost+found"
    "--exclude=/swap-nvme.img"
    "--exclude=/swapfile_emergency"
    "--exclude=/timeshift/*"
    "--exclude=/home/pamerys/.cache/*"
    "--exclude=/home/pamerys/.npm-new-cache/*"
    "--exclude=/home/pamerys/restore-sdb1/*"
    "--exclude=/home/pamerys/lmstudio-models/*"
    "--exclude=/home/pamerys/.lmstudio/*"
    "--exclude=/home/pamerys/models-gguf/*"
    "--exclude=/home/pamerys/.ollama/*"
    "--exclude=/home/pamerys/.browseros/*"
    "--exclude=/home/pamerys/.claude/plugins/cache/*"
    "--exclude=/home/pamerys/.gemini/tmp/*"
    "--exclude=/home/pamerys/.gemini/antigravity-cli/brain/*"
)

# ──────────────────────────────────────────────────────────────────────────────
# Parsing arguments
# ──────────────────────────────────────────────────────────────────────────────
MODE="local_auto"
REMOTE_TARGET=""
REMOTE_USER="turbo"
FORCE_DST_DISK=""
MACHINE_PROFILE=""

usage() {
    cat <<EOF
Usage: sudo bash $0 [OPTIONS]

Options:
  --local <disk>          Force le disque local cible (ex: sdd)
  --remote <M1|M2|M3|IP> Clone vers machine distante via SSH
  --user <user>           Utilisateur SSH (défaut: turbo)
  --dst-disk <disk>       Disque cible distant (défaut: auto selon profil)
  --profile <PROFIL>      Profil machine cible (DESKTOP_GPU / LAPTOP_NONGPU / SERVER)
  --list                  Lister les disques disponibles

Exemples:
  sudo bash $0                                       # Auto Crucial local
  sudo bash $0 --local sda                           # Force /dev/sda
  sudo bash $0 --remote M1                           # Clone SSH → M1 (DESKTOP_GPU)
  sudo bash $0 --remote M3 --profile LAPTOP_NONGPU  # Clone SSH → HP Laptop sans GPU
  sudo bash $0 --remote 192.168.1.90 --user turbo --dst-disk sdb --profile LAPTOP_NONGPU
EOF
    exit 0
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --local)      MODE="local_force"; FORCE_DST_DISK="$2"; shift 2 ;;
        --remote)     MODE="remote"; REMOTE_TARGET="$2"; shift 2 ;;
        --user)       REMOTE_USER="$2"; shift 2 ;;
        --dst-disk)   FORCE_DST_DISK="$2"; shift 2 ;;
        --profile)    MACHINE_PROFILE="$2"; shift 2 ;;
        --list)
            echo "=== Disques locaux ==="
            lsblk -o NAME,MODEL,SIZE,FSTYPE,MOUNTPOINT
            echo ""
            echo "=== Machines distantes JARVIS ==="
            for m in M1 M2 M3 M4 M5; do
                echo "  $m → ${CLUSTER_IPS[$m]} — Profil: ${CLUSTER_PROFILES[$m]} — DST: /dev/${CLUSTER_DST_DISKS[$m]}"
            done
            exit 0
            ;;
        --help|-h)    usage ;;
        *)            echo "Argument inconnu: $1"; usage ;;
    esac
done

echo "=== JARVIS Clone v3.0 — Démarrage : $(date) ==="
echo "Mode    : ${MODE}"
echo "Profil  : ${MACHINE_PROFILE:-auto}"

# ──────────────────────────────────────────────────────────────────────────────
# Détection disque SOURCE
# ──────────────────────────────────────────────────────────────────────────────
SRC_PARTITION=$(lsblk -o NAME,MOUNTPOINT -n | grep -w "/" | awk '{print $1}' | tr -d '└─├─')
SRC_DISK=$(echo "${SRC_PARTITION}" | sed 's/[0-9]*$//; s/p[0-9]*$//')
[ -z "${SRC_DISK}" ] && SRC_DISK="sdb"
SRC_ROOT_DEV="/dev/${SRC_PARTITION}"
SRC_EFI_PART=$(lsblk -o NAME,FSTYPE -n "/dev/${SRC_DISK}" | grep -E "vfat|msdos" | awk '{print $1}' | tr -d '└─├─' | head -n 1)
SRC_EFI_DEV="/dev/${SRC_EFI_PART}"
echo "Source  : /dev/${SRC_DISK} (root: ${SRC_ROOT_DEV}, efi: ${SRC_EFI_DEV})"

# ──────────────────────────────────────────────────────────────────────────────
# Optimisations I/O
# ──────────────────────────────────────────────────────────────────────────────
opt_io() {
    local d="$1"
    blockdev --setra 65536 "/dev/${d}" 2>/dev/null || true
    [ -f "/sys/block/${d}/queue/max_sectors_kb" ] && echo 1024 > "/sys/block/${d}/queue/max_sectors_kb" 2>/dev/null || true
}
echo 5  > /proc/sys/vm/dirty_background_ratio || true
echo 10 > /proc/sys/vm/dirty_ratio            || true
echo 1  > /proc/sys/vm/drop_caches            || true
opt_io "${SRC_DISK}"

# ──────────────────────────────────────────────────────────────────────────────
# FONCTION : Adaptation post-clonage selon profil (run sur la cible)
# ──────────────────────────────────────────────────────────────────────────────
adapt_profile() {
    local ROOT_MNT="$1"
    local PROFILE="$2"
    local HOSTNAME_TARGET="$3"
    local SRC_ROOT_UUID_P="$4"
    local DST_ROOT_UUID_P="$5"
    local SRC_EFI_UUID_P="$6"
    local DST_EFI_UUID_P="$7"

    echo "[ADAPT] Profil = ${PROFILE} — hostname = ${HOSTNAME_TARGET}"

    # --- Hostname ---
    echo "${HOSTNAME_TARGET}" > "${ROOT_MNT}/etc/hostname"
    sed -i "s/127\.0\.1\.1.*/127.0.1.1\t${HOSTNAME_TARGET}/" "${ROOT_MNT}/etc/hosts" 2>/dev/null || true

    # --- UUIDs fstab ---
    TARGET_FSTAB="${ROOT_MNT}/etc/fstab"
    if [ -f "${TARGET_FSTAB}" ]; then
        sed -i "s/UUID=${SRC_ROOT_UUID_P}/UUID=${DST_ROOT_UUID_P}/g" "${TARGET_FSTAB}"
        sed -i "s/UUID=${SRC_EFI_UUID_P}/UUID=${DST_EFI_UUID_P}/g" "${TARGET_FSTAB}"
        # Supprimer les swapfiles machine source qui n'existent pas sur la cible
        sed -i '/swap-nvme\.img/d; /swapfile_emergency/d' "${TARGET_FSTAB}"
        echo "[ADAPT] fstab corrigé."
    fi

    # --- UUIDs grub.cfg ---
    TARGET_GRUB="${ROOT_MNT}/boot/grub/grub.cfg"
    if [ -f "${TARGET_GRUB}" ]; then
        sed -i "s/${SRC_ROOT_UUID_P}/${DST_ROOT_UUID_P}/g" "${TARGET_GRUB}"
        sed -i "s/${SRC_EFI_UUID_P}/${DST_EFI_UUID_P}/g" "${TARGET_GRUB}"
        echo "[ADAPT] grub.cfg corrigé."
    fi

    # --- Répertoires virtuels ---
    mkdir -p "${ROOT_MNT}"/{dev,proc,sys,tmp,run,mnt,media,storage}
    chmod 1777 "${ROOT_MNT}/tmp"

    # ──────────────────────────────────────────────────────────────────────────
    # Profil LAPTOP_NONGPU — HP Portable Entreprise (nouvelle M3)
    # ──────────────────────────────────────────────────────────────────────────
    if [ "${PROFILE}" = "LAPTOP_NONGPU" ]; then
        echo "[ADAPT] ▶ Profil LAPTOP_NONGPU — HP Portable Entreprise sans GPU"

        # Script d'init lancé au premier boot de la machine cible
        cat > "${ROOT_MNT}/etc/jarvis/first-boot-laptop.sh" << 'FIRSTBOOT'
#!/bin/bash
# JARVIS — Premier démarrage sur HP Portable Entreprise (LAPTOP_NONGPU)
# Exécuté une seule fois automatiquement par systemd au 1er boot
set -euo pipefail
LOG="/var/log/jarvis-first-boot.log"
exec >> "${LOG}" 2>&1
echo "=== JARVIS First Boot LAPTOP_NONGPU : $(date) ==="

# 1) Supprimer les drivers NVIDIA (inutiles et bloquants sans GPU)
echo "[GPU] Suppression des drivers NVIDIA..."
apt-get remove --purge -y nvidia-* cuda-* libnvidia-* 2>/dev/null || true
apt-get autoremove -y 2>/dev/null || true

# 2) Désactiver les services GPU JARVIS (LMStudio, CUDA, whisper GPU)
for svc in lmstudio jarvis-lmstudio jarvis-cuda-monitor jarvis-vocal-whisper nvidia-persistenced; do
    systemctl disable "${svc}" 2>/dev/null || true
    systemctl stop    "${svc}" 2>/dev/null || true
done

# 3) Installer drivers vidéo Intel / AMD intégré + pilotes WiFi HP
echo "[VIDEO] Installation drivers vidéo intégrés..."
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
    2>/dev/null || true

# 4) Installer NetworkManager + WiFi tools (portables HP)
apt-get install -y network-manager network-manager-gnome wpasupplicant 2>/dev/null || true
systemctl enable NetworkManager 2>/dev/null || true

# 5) Gestion batterie / économie d'énergie (portable)
apt-get install -y tlp tlp-rdw powertop acpi acpid 2>/dev/null || true
systemctl enable tlp 2>/dev/null || true
systemctl enable acpid 2>/dev/null || true

# 6) GNOME — activer le démarrage graphique
systemctl set-default graphical.target 2>/dev/null || true
# Activer GDM3 (display manager GNOME)
apt-get install -y gdm3 gnome-session gnome-terminal 2>/dev/null || true
systemctl enable gdm3 2>/dev/null || true

# 7) Configurer GNOME pour l'utilisateur turbo (session auto si désiré)
# Auto-login désactivé par défaut (sécurité entreprise)
mkdir -p /etc/gdm3
cat > /etc/gdm3/custom.conf << 'GDM'
[daemon]
AutomaticLoginEnable=false
WaylandEnable=true
GDM

# 8) Activer les services JARVIS compatibles laptop (Ollama CPU, bridges)
for svc in ollama jarvis-whisper-bridge jarvis-chat-proxy; do
    systemctl enable "${svc}" 2>/dev/null || true
done

# 9) Nettoyage
apt-get autoremove -y 2>/dev/null || true
apt-get autoclean -y 2>/dev/null || true

# 10) Désactiver ce service (ne s'exécute qu'une seule fois)
systemctl disable jarvis-first-boot.service 2>/dev/null || true
echo "=== First Boot terminé : $(date) ==="
FIRSTBOOT
        chmod +x "${ROOT_MNT}/etc/jarvis/first-boot-laptop.sh"
        mkdir -p "${ROOT_MNT}/etc/jarvis"

        # Créer le service systemd de premier boot
        cat > "${ROOT_MNT}/etc/systemd/system/jarvis-first-boot.service" << 'SYSD'
[Unit]
Description=JARVIS First Boot Adaptation — LAPTOP_NONGPU
After=network.target
ConditionPathExists=/etc/jarvis/first-boot-laptop.sh

[Service]
Type=oneshot
ExecStart=/bin/bash /etc/jarvis/first-boot-laptop.sh
RemainAfterExit=yes
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
SYSD

        # Activer le service de premier boot
        ln -sf /etc/systemd/system/jarvis-first-boot.service \
            "${ROOT_MNT}/etc/systemd/system/multi-user.target.wants/jarvis-first-boot.service" 2>/dev/null || true

        # Pré-configurer GRUB pour boot universel (délai court + sortie console)
        GRUB_DEFAULT="${ROOT_MNT}/etc/default/grub"
        if [ -f "${GRUB_DEFAULT}" ]; then
            sed -i 's/GRUB_TIMEOUT=.*/GRUB_TIMEOUT=3/'   "${GRUB_DEFAULT}"
            sed -i 's/GRUB_TIMEOUT_STYLE=.*/GRUB_TIMEOUT_STYLE=menu/' "${GRUB_DEFAULT}"
            # Paramètres universels : pas de quiet, pas de splash (debug visible au 1er boot)
            sed -i 's/GRUB_CMDLINE_LINUX_DEFAULT=.*/GRUB_CMDLINE_LINUX_DEFAULT="nomodeset pci=noaer"/' "${GRUB_DEFAULT}"
            # Désactiver l'OS Prober (évite erreurs sur machine vide)
            grep -q "GRUB_DISABLE_OS_PROBER" "${GRUB_DEFAULT}" || \
                echo 'GRUB_DISABLE_OS_PROBER=true' >> "${GRUB_DEFAULT}"
            echo "[ADAPT] grub/default configuré pour boot universel."
        fi

        # Configurer netplan pour WiFi + Ethernet auto
        mkdir -p "${ROOT_MNT}/etc/netplan"
        cat > "${ROOT_MNT}/etc/netplan/01-jarvis-laptop.yaml" << 'NETPLAN'
network:
  version: 2
  renderer: NetworkManager
  ethernets:
    all-eth:
      match:
        name: "en*"
      dhcp4: true
      dhcp6: false
      optional: true
  wifis:
    all-wifi:
      match:
        name: "wl*"
      dhcp4: true
      optional: true
      access-points: {}
NETPLAN
        echo "[ADAPT] Netplan WiFi+Ethernet configuré."

        # Désactiver les services GPU/Desktop lourd dans le clone
        for svc in lmstudio jarvis-lmstudio jarvis-cuda-monitor \
                   jarvis-vocal-whisper nvidia-persistenced \
                   docker-swarm; do
            rm -f "${ROOT_MNT}/etc/systemd/system/multi-user.target.wants/${svc}.service" 2>/dev/null || true
        done

        echo "[ADAPT] ✅ Profil LAPTOP_NONGPU appliqué."
    fi

    # ──────────────────────────────────────────────────────────────────────────
    # Profil DESKTOP_GPU — Bureau avec GPU NVIDIA (M1, M2)
    # ──────────────────────────────────────────────────────────────────────────
    if [ "${PROFILE}" = "DESKTOP_GPU" ]; then
        echo "[ADAPT] ▶ Profil DESKTOP_GPU — Bureau GPU NVIDIA"
        # Garder tous les services GPU actifs (rien à supprimer)
        # Configurer GRUB avec les paramètres GPU
        GRUB_DEFAULT="${ROOT_MNT}/etc/default/grub"
        if [ -f "${GRUB_DEFAULT}" ]; then
            sed -i 's/GRUB_TIMEOUT=.*/GRUB_TIMEOUT=3/' "${GRUB_DEFAULT}"
            sed -i 's/GRUB_CMDLINE_LINUX_DEFAULT=.*/GRUB_CMDLINE_LINUX_DEFAULT="quiet splash"/' "${GRUB_DEFAULT}"
        fi
        echo "[ADAPT] ✅ Profil DESKTOP_GPU appliqué."
    fi

    # ──────────────────────────────────────────────────────────────────────────
    # Profil SERVER — Headless sans écran
    # ──────────────────────────────────────────────────────────────────────────
    if [ "${PROFILE}" = "SERVER" ]; then
        echo "[ADAPT] ▶ Profil SERVER — Headless"
        if [ -f "${ROOT_MNT}/etc/default/grub" ]; then
            sed -i 's/GRUB_TIMEOUT=.*/GRUB_TIMEOUT=2/' "${ROOT_MNT}/etc/default/grub"
            sed -i 's/GRUB_CMDLINE_LINUX_DEFAULT=.*/GRUB_CMDLINE_LINUX_DEFAULT="console=tty0 console=ttyS0,115200n8"/' "${ROOT_MNT}/etc/default/grub"
        fi
        # Désactiver GNOME / GDM sur server headless
        for svc in gdm gdm3 gnome-session; do
            rm -f "${ROOT_MNT}/etc/systemd/system/graphical.target.wants/${svc}.service" 2>/dev/null || true
        done
        ln -sf /lib/systemd/system/multi-user.target "${ROOT_MNT}/etc/systemd/system/default.target" 2>/dev/null || true
        echo "[ADAPT] ✅ Profil SERVER appliqué."
    fi

    echo "[ADAPT] ✅ Adaptation post-clonage terminée."
}

# ──────────────────────────────────────────────────────────────────────────────
# HELPER : Installer GRUB universel
# ──────────────────────────────────────────────────────────────────────────────
install_grub_universal() {
    local EFI_MNT="$1"
    local BOOT_DIR="$2"
    echo "[GRUB] Installation GRUB universel --removable..."
    grub-install --target=x86_64-efi \
        --efi-directory="${EFI_MNT}" \
        --boot-directory="${BOOT_DIR}" \
        --removable \
        --recheck 2>/dev/null || \
    grub-install --target=x86_64-efi \
        --efi-directory="${EFI_MNT}" \
        --boot-directory="${BOOT_DIR}" \
        --removable \
        --recheck \
        --force 2>/dev/null || true
    echo "[GRUB] ✅ GRUB installé."
}

# ──────────────────────────────────────────────────────────────────────────────
# MODE REMOTE — Clone SSH vers machine distante
# ──────────────────────────────────────────────────────────────────────────────
if [ "${MODE}" = "remote" ]; then
    REMOTE_HOST="${REMOTE_TARGET}"
    REMOTE_MACHINE_NAME="${REMOTE_TARGET}"

    # Résolution nom → IP
    if [[ -n "${CLUSTER_IPS[${REMOTE_TARGET}]+_}" ]]; then
        REMOTE_HOST="${CLUSTER_IPS[${REMOTE_TARGET}]}"
        REMOTE_USER="${CLUSTER_USERS[${REMOTE_TARGET}]}"
        [ -z "${FORCE_DST_DISK}" ] && FORCE_DST_DISK="${CLUSTER_DST_DISKS[${REMOTE_TARGET}]}"
        [ -z "${MACHINE_PROFILE}" ] && MACHINE_PROFILE="${CLUSTER_PROFILES[${REMOTE_TARGET}]}"
        TARGET_HOSTNAME="${CLUSTER_HOSTNAMES[${REMOTE_TARGET}]}"
    else
        TARGET_HOSTNAME="${REMOTE_HOST}"
        [ -z "${MACHINE_PROFILE}" ] && MACHINE_PROFILE="LAPTOP_NONGPU"
    fi
    REMOTE_DST_DISK="${FORCE_DST_DISK:-sdb}"
    REMOTE_MNT="/media/${REMOTE_USER}/jarvis-clone-dst"

    echo "Cible       : ${REMOTE_MACHINE_NAME} → ${REMOTE_USER}@${REMOTE_HOST}"
    echo "Disque      : /dev/${REMOTE_DST_DISK}"
    echo "Profil      : ${MACHINE_PROFILE}"
    echo "Hostname    : ${TARGET_HOSTNAME}"

    SSH_OPTS="-o StrictHostKeyChecking=no -o ConnectTimeout=10"
    [ -f "${SSH_KEY}" ] && SSH_OPTS="${SSH_OPTS} -i ${SSH_KEY}"

    # Vérification connectivité
    echo "Test SSH..."
    ssh ${SSH_OPTS} "${REMOTE_USER}@${REMOTE_HOST}" "echo OK" 2>/dev/null | grep -q "OK" || {
        echo "ERREUR : Impossible de joindre ${REMOTE_HOST} via SSH."
        exit 1
    }

    # Préparation montage sur la cible
    ssh ${SSH_OPTS} "${REMOTE_USER}@${REMOTE_HOST}" "sudo mkdir -p ${REMOTE_MNT}/root ${REMOTE_MNT}/efi"
    ssh ${SSH_OPTS} "${REMOTE_USER}@${REMOTE_HOST}" "sudo mount /dev/${REMOTE_DST_DISK}2 ${REMOTE_MNT}/root 2>/dev/null || true"
    ssh ${SSH_OPTS} "${REMOTE_USER}@${REMOTE_HOST}" "sudo mount /dev/${REMOTE_DST_DISK}1 ${REMOTE_MNT}/efi 2>/dev/null || true"

    # rsync SSH
    echo "Lancement rsync SSH → ${REMOTE_HOST}..."
    rsync -aAXHv --delete --numeric-ids --progress \
        "${RSYNC_EXCLUDES[@]}" \
        -e "ssh ${SSH_OPTS}" \
        / "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_MNT}/root/"

    # UUIDs
    DST_ROOT_UUID=$(ssh ${SSH_OPTS} "${REMOTE_USER}@${REMOTE_HOST}" "sudo blkid -o value -s UUID /dev/${REMOTE_DST_DISK}2")
    DST_EFI_UUID=$(ssh ${SSH_OPTS} "${REMOTE_USER}@${REMOTE_HOST}" "sudo blkid -o value -s UUID /dev/${REMOTE_DST_DISK}1")
    SRC_ROOT_UUID=$(blkid -o value -s UUID "${SRC_ROOT_DEV}")
    SRC_EFI_UUID=$(blkid -o value -s UUID "${SRC_EFI_DEV}")

    # Adaptation (on copie adapt_profile via un heredoc exécuté à distance)
    # On génère un script temporaire et on l'exécute sur la cible via SSH
    REMOTE_ADAPT=$(cat << ADAPT_SCRIPT_EOF
#!/bin/bash
set -euo pipefail
ROOT_MNT="${REMOTE_MNT}/root"
PROFILE="${MACHINE_PROFILE}"
HOSTNAME_TARGET="${TARGET_HOSTNAME}"
SRC_ROOT_UUID="${SRC_ROOT_UUID}"
DST_ROOT_UUID="${DST_ROOT_UUID}"
SRC_EFI_UUID="${SRC_EFI_UUID}"
DST_EFI_UUID="${DST_EFI_UUID}"

echo "[REMOTE ADAPT] Profil=\${PROFILE} hostname=\${HOSTNAME_TARGET}"
echo "\${HOSTNAME_TARGET}" > "\${ROOT_MNT}/etc/hostname"
sed -i "s/127\.0\.1\.1.*/127.0.1.1\t\${HOSTNAME_TARGET}/" "\${ROOT_MNT}/etc/hosts" 2>/dev/null || true
[ -f "\${ROOT_MNT}/etc/fstab" ] && \
    sed -i "s/UUID=\${SRC_ROOT_UUID}/UUID=\${DST_ROOT_UUID}/g; s/UUID=\${SRC_EFI_UUID}/UUID=\${DST_EFI_UUID}/g; /swap-nvme/d; /swapfile_emergency/d" \
    "\${ROOT_MNT}/etc/fstab"
[ -f "\${ROOT_MNT}/boot/grub/grub.cfg" ] && \
    sed -i "s/\${SRC_ROOT_UUID}/\${DST_ROOT_UUID}/g; s/\${SRC_EFI_UUID}/\${DST_EFI_UUID}/g" \
    "\${ROOT_MNT}/boot/grub/grub.cfg"
mkdir -p "\${ROOT_MNT}"/{dev,proc,sys,tmp,run,mnt,media,storage}
chmod 1777 "\${ROOT_MNT}/tmp"

if [ "\${PROFILE}" = "LAPTOP_NONGPU" ]; then
    mkdir -p "\${ROOT_MNT}/etc/jarvis"
    [ -f "\${ROOT_MNT}/etc/default/grub" ] && \
        sed -i 's/GRUB_TIMEOUT=.*/GRUB_TIMEOUT=3/; s/GRUB_CMDLINE_LINUX_DEFAULT=.*/GRUB_CMDLINE_LINUX_DEFAULT="nomodeset pci=noaer"/' "\${ROOT_MNT}/etc/default/grub"
    mkdir -p "\${ROOT_MNT}/etc/netplan"
    cat > "\${ROOT_MNT}/etc/netplan/01-jarvis-laptop.yaml" << 'NETP'
network:
  version: 2
  renderer: NetworkManager
  ethernets:
    all-eth:
      match:
        name: "en*"
      dhcp4: true
      optional: true
  wifis:
    all-wifi:
      match:
        name: "wl*"
      dhcp4: true
      optional: true
      access-points: {}
NETP
    for svc in lmstudio jarvis-lmstudio nvidia-persistenced; do
        rm -f "\${ROOT_MNT}/etc/systemd/system/multi-user.target.wants/\${svc}.service" 2>/dev/null || true
    done
    cat > "\${ROOT_MNT}/etc/systemd/system/jarvis-first-boot.service" << 'SVC'
[Unit]
Description=JARVIS First Boot — LAPTOP_NONGPU
After=network.target
[Service]
Type=oneshot
ExecStart=/bin/bash /etc/jarvis/first-boot-laptop.sh
RemainAfterExit=yes
[Install]
WantedBy=multi-user.target
SVC
    ln -sf /etc/systemd/system/jarvis-first-boot.service \
        "\${ROOT_MNT}/etc/systemd/system/multi-user.target.wants/jarvis-first-boot.service" 2>/dev/null || true
    echo "[REMOTE ADAPT] ✅ LAPTOP_NONGPU appliqué."
fi
echo "[REMOTE ADAPT] Terminé."
ADAPT_SCRIPT_EOF
)

    echo "Exécution de l'adaptation sur ${REMOTE_HOST}..."
    echo "${REMOTE_ADAPT}" | ssh ${SSH_OPTS} "${REMOTE_USER}@${REMOTE_HOST}" "sudo bash"

    # GRUB universel sur la cible
    echo "[GRUB] Installation GRUB universel sur ${REMOTE_HOST}..."
    ssh ${SSH_OPTS} "${REMOTE_USER}@${REMOTE_HOST}" \
        "sudo grub-install --target=x86_64-efi \
            --efi-directory=${REMOTE_MNT}/efi \
            --boot-directory=${REMOTE_MNT}/root/boot \
            --removable --recheck 2>/dev/null || true"

    # Démonter proprement
    ssh ${SSH_OPTS} "${REMOTE_USER}@${REMOTE_HOST}" \
        "sudo umount ${REMOTE_MNT}/efi 2>/dev/null; sudo umount ${REMOTE_MNT}/root 2>/dev/null; true"

    echo "=== Clone REMOTE [${MACHINE_PROFILE}] → ${REMOTE_MACHINE_NAME} terminé : $(date) ==="
    exit 0
fi

# ──────────────────────────────────────────────────────────────────────────────
# MODE LOCAL — Clone vers SSD local
# ──────────────────────────────────────────────────────────────────────────────

# Détection du disque cible
if [ "${MODE}" = "local_force" ] && [ -n "${FORCE_DST_DISK}" ]; then
    DST_DISK="${FORCE_DST_DISK}"
else
    # Auto : Crucial BX500 → Samsung 870 EVO → Samsung MZ7LH
    DST_DISK=$(lsblk -o NAME,MODEL -dn | grep -vE "$(lsblk -o NAME,MOUNTPOINT -n | grep -w "/" | awk '{print $1}' | tr -d '└─├─' | sed 's/[0-9]*$//')" | \
        grep -E "CT1000BX500|CT2000BX500|Crucial|Samsung 870|MZ7LH|SAMSUNG MZ7" | \
        awk '{print $1}' | head -n 1)
    if [ -z "${DST_DISK}" ]; then
        echo "ERREUR : Aucun SSD cible auto-détecté."
        lsblk -o NAME,MODEL,SIZE -dn
        echo "Utilisez --local <disk> pour forcer."
        exit 1
    fi
fi

[ -z "${MACHINE_PROFILE}" ] && MACHINE_PROFILE="DESKTOP_GPU"
TARGET_HOSTNAME="${CLUSTER_HOSTNAMES[local]:-$(hostname)}"

echo "Cible   : /dev/${DST_DISK}"
echo "Profil  : ${MACHINE_PROFILE}"

opt_io "${DST_DISK}"

DST_ROOT_PART=$(lsblk -o NAME,FSTYPE -n "/dev/${DST_DISK}" | grep "ext4" | awk '{print $1}' | tr -d '└─├─' | head -n 1)
DST_EFI_PART=$(lsblk -o NAME,FSTYPE -n "/dev/${DST_DISK}" | grep -E "vfat|msdos" | awk '{print $1}' | tr -d '└─├─' | head -n 1)
DST_ROOT_DEV="/dev/${DST_ROOT_PART}"
DST_EFI_DEV="/dev/${DST_EFI_PART}"

[ ! -b "${DST_ROOT_DEV}" ] || [ ! -b "${DST_EFI_DEV}" ] && {
    echo "ERREUR : /dev/${DST_DISK} non partitionné."
    exit 1
}

SRC_ROOT_UUID=$(blkid -o value -s UUID "${SRC_ROOT_DEV}")
SRC_EFI_UUID=$(blkid -o value -s UUID "${SRC_EFI_DEV}")
DST_ROOT_UUID=$(blkid -o value -s UUID "${DST_ROOT_DEV}")
DST_EFI_UUID=$(blkid -o value -s UUID "${DST_EFI_DEV}")

echo "UUID src root : ${SRC_ROOT_UUID}"
echo "UUID dst root : ${DST_ROOT_UUID}"

# Montage
DST_ROOT_MNT="/media/turbo/root2"
DST_EFI_MNT="/media/turbo/EFI2"
mkdir -p "${DST_ROOT_MNT}" "${DST_EFI_MNT}"

mountpoint -q "${DST_ROOT_MNT}" || mount "${DST_ROOT_DEV}" "${DST_ROOT_MNT}"
mountpoint -q "${DST_EFI_MNT}"  || mount "${DST_EFI_DEV}"  "${DST_EFI_MNT}"

# rsync local
echo "rsync local → /dev/${DST_DISK}..."
nocache rsync -aAXHv --delete --inplace --no-whole-file --numeric-ids --progress \
    "${RSYNC_EXCLUDES[@]}" \
    / "${DST_ROOT_MNT}/"

# EFI
rsync -av --delete "/boot/efi/" "${DST_EFI_MNT}/"

# Adaptation profil
TARGET_HOSTNAME="$(hostname)"
adapt_profile \
    "${DST_ROOT_MNT}" \
    "${MACHINE_PROFILE}" \
    "${TARGET_HOSTNAME}" \
    "${SRC_ROOT_UUID}" \
    "${DST_ROOT_UUID}" \
    "${SRC_EFI_UUID}" \
    "${DST_EFI_UUID}"

# GRUB universel
install_grub_universal "${DST_EFI_MNT}" "${DST_ROOT_MNT}/boot"

echo "=== Clone LOCAL [${MACHINE_PROFILE}] → /dev/${DST_DISK} terminé : $(date) ==="
