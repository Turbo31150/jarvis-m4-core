#!/usr/bin/env bash
# =============================================================================
# generalize-image-m3.sh — Rend l'image clonée (Crucial) PORTABLE sur toute machine
# Cible : disque Crucial CT1000BX500SSD1 (serial 2234E658B756) → futur M3 (HP sans GPU)
#
# À lancer UNIQUEMENT après la fin du clone ddrescue (sdb2 -> sdc2).
# N'écrit JAMAIS sur le système vif M1 (sdb) : cible identifiée par SERIAL.
#
# Idempotent. Chaque étape est ré-exécutable. Garde-fous stricts.
# Établi 2026-06-07.
# =============================================================================
set -euo pipefail

# ---- Identification stricte de la cible (par serial, pas par /dev/sdX) -------
TARGET_SERIAL="2234E658B756"          # Crucial CT1000BX500SSD1
TARGET_DISK="$(lsblk -ndo NAME,SERIAL | awk -v s="$TARGET_SERIAL" '$2==s{print "/dev/"$1}')"
[ -n "${TARGET_DISK:-}" ] || { echo "FATAL: Crucial serial $TARGET_SERIAL introuvable"; exit 1; }
DST_EFI="${TARGET_DISK}1"
DST_ROOT="${TARGET_DISK}2"
MNT=/mnt/m3img
HOSTNAME_NEW="jarvis-m3"

# ---- Garde-fou: ne jamais cibler le disque root vif ------------------------
ROOT_SRC="$(findmnt -no SOURCE / | sed 's/[0-9]*$//')"
[ "$TARGET_DISK" != "$ROOT_SRC" ] || { echo "FATAL: cible == disque root vif ($ROOT_SRC). ABORT"; exit 1; }
echo "== Cible: $TARGET_DISK (root=$DST_ROOT, efi=$DST_EFI) | système vif: $ROOT_SRC =="

# ---- Garde-fou: clone terminé ? --------------------------------------------
if pgrep -x ddrescue >/dev/null; then echo "FATAL: ddrescue tourne encore. Attendre la fin."; exit 1; fi

log(){ echo -e "\n\033[1;36m[*] $*\033[0m"; }

# =============================================================================
log "1/13 — fsck du root cloné (réparation post-clone)"
sudo e2fsck -f -y "$DST_ROOT" || true   # -y: le journal cloné sera réparé/recréé

log "2/13 — Nouvel UUID root (éviter collision avec M1 — clone bloc = UUID identique)"
NEW_UUID_ROOT="$(uuidgen)"
sudo tune2fs -U "$NEW_UUID_ROOT" "$DST_ROOT"
echo "    nouveau UUID root: $NEW_UUID_ROOT"
UUID_EFI="$(sudo blkid -s UUID -o value "$DST_EFI")"

log "3/13 — Montage cible + binds"
sudo umount -R "$MNT" 2>/dev/null || true
sudo mkdir -p "$MNT"
sudo mount "$DST_ROOT" "$MNT"
sudo mkdir -p "$MNT/boot/efi"
sudo mount "$DST_EFI" "$MNT/boot/efi" 2>/dev/null || true
for d in dev dev/pts proc sys run; do sudo mount --bind "/$d" "$MNT/$d"; done
sudo cp -a /etc/resolv.conf "$MNT/etc/resolv.conf" 2>/dev/null || true

# Helper chroot
chr(){ sudo chroot "$MNT" /bin/bash -c "$1"; }

log "4/13 — /etc/fstab portable (UUID Crucial, purge des montages spécifiques M1)"
sudo tee "$MNT/etc/fstab" >/dev/null <<EOF
# fstab portable — généré $(date +%F) pour image universelle JARVIS
UUID=$NEW_UUID_ROOT  /          ext4  errors=remount-ro,noatime  0 1
UUID=$UUID_EFI       /boot/efi  vfat  umask=0077                 0 1
# Pas de swap matériel-spécifique : zram géré par service si présent
tmpfs                /tmp       tmpfs  defaults,noatime,nosuid    0 0
EOF
echo "    fstab réécrit (cryptswap/swap-nvme/sshfs cluster/storage retirés)"

log "5/13 — Reset identité machine (regénérée au 1er boot)"
sudo truncate -s 0 "$MNT/etc/machine-id" 2>/dev/null || true
sudo rm -f "$MNT/var/lib/dbus/machine-id" 2>/dev/null || true
sudo rm -f "$MNT"/etc/ssh/ssh_host_* 2>/dev/null || true   # regénérées par ssh-keygen au boot

log "6/13 — initramfs universel (MODULES=most : boot sur tout hardware)"
sudo sed -i 's/^MODULES=.*/MODULES=most/' "$MNT/etc/initramfs-tools/initramfs.conf" 2>/dev/null || \
  echo "MODULES=most" | sudo tee -a "$MNT/etc/initramfs-tools/initramfs.conf" >/dev/null

log "7/13 — Firmware + microcode génériques (boot HP/Intel/AMD)"
chr "apt-get update -qq && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
     linux-firmware intel-microcode amd64-microcode grub-efi-amd64 grub-pc-bin os-prober network-manager" \
   || echo '    [!] apt en chroot a échoué (réseau?) — à relancer manuellement'

log "8/13 — Service auto-détection hardware (GPU conditionnel)"
sudo tee "$MNT/usr/local/sbin/jarvis-hw-autodetect.sh" >/dev/null <<'HW'
#!/usr/bin/env bash
# Détecte le hardware au boot et active/désactive les services GPU en conséquence.
set -e
GPU_SERVICES="nvidia-persistenced lmstudio jarvis-vocal-whisper jarvis-gpu-watchdog ollama"
if lspci 2>/dev/null | grep -qiE 'VGA.*(NVIDIA|AMD/ATI)|3D controller.*NVIDIA'; then
  echo "[hw-autodetect] GPU détecté → activation services GPU"
  for s in $GPU_SERVICES; do systemctl enable --now "$s" 2>/dev/null || true; done
else
  echo "[hw-autodetect] PAS de GPU (mode bureautique/M3) → désactivation services GPU"
  for s in $GPU_SERVICES; do systemctl disable --now "$s" 2>/dev/null || true; done
  # CPU-only: forcer Ollama/llama en CPU si présent, sinon rien
fi
HW
sudo chmod +x "$MNT/usr/local/sbin/jarvis-hw-autodetect.sh"
sudo tee "$MNT/etc/systemd/system/jarvis-hw-autodetect.service" >/dev/null <<'SVC'
[Unit]
Description=JARVIS hardware auto-detect (GPU conditional services)
After=multi-user.target
[Service]
Type=oneshot
ExecStart=/usr/local/sbin/jarvis-hw-autodetect.sh
RemainAfterExit=yes
[Install]
WantedBy=multi-user.target
SVC
chr "systemctl enable jarvis-hw-autodetect.service" || true
# Désactiver par défaut les services GPU (réactivés par autodetect si GPU)
chr "systemctl disable nvidia-persistenced lmstudio 2>/dev/null || true"

log "9/13 — Réseau portable (NetworkManager + DHCP, purge bindings M1)"
sudo rm -f "$MNT"/etc/netplan/*static* 2>/dev/null || true
sudo tee "$MNT/etc/netplan/01-portable.yaml" >/dev/null <<'NET'
network:
  version: 2
  renderer: NetworkManager
NET
sudo find "$MNT/etc/NetworkManager/system-connections/" -type f -delete 2>/dev/null || true

log "10/13 — Hostname neutre"
echo "$HOSTNAME_NEW" | sudo tee "$MNT/etc/hostname" >/dev/null
sudo sed -i "s/127.0.1.1.*/127.0.1.1\t$HOSTNAME_NEW/" "$MNT/etc/hosts" 2>/dev/null || true

log "11/13 — GRUB dual BIOS(legacy)+UEFI (vieux HP + machines modernes)"
# UEFI
chr "grub-install --target=x86_64-efi --efi-directory=/boot/efi --bootloader-id=JARVIS --recheck --no-nvram" || echo "    [!] grub UEFI échec"
# BIOS legacy (GPT nécessite partition bios_grub ; si absente, install best-effort sur le disque)
chr "grub-install --target=i386-pc --recheck $TARGET_DISK" 2>/dev/null || echo "    [!] grub BIOS legacy: partition bios_grub manquante (UEFI seul OK)"
chr "update-grub" || true
chr "update-initramfs -u -k all" || echo "    [!] initramfs à régénérer manuellement"

log "12/13 — Allègement optionnel (modèles IA inutiles sur bureautique M3)"
echo "    (laissé manuel) modèles lourds clonés présents dans : ~/lmstudio-models ~/.ollama ~/models-gguf"
echo "    → libérer ~XXGo: sudo rm -rf $MNT/home/pamerys/{lmstudio-models,.ollama,models-gguf,.lmstudio} si voulu"

log "13/13 — Démontage propre"
sync
for d in run sys proc dev/pts dev; do sudo umount -l "$MNT/$d" 2>/dev/null || true; done
sudo umount -R "$MNT" 2>/dev/null || true

echo -e "\n\033[1;32m✅ IMAGE GÉNÉRALISÉE — $TARGET_DISK bootable portable (UEFI+BIOS), GPU conditionnel.\033[0m"
echo "   UUID root: $NEW_UUID_ROOT | hostname: $HOSTNAME_NEW"
echo "   → Débrancher le Crucial, l'installer dans le HP (M3), booter. Les services GPU resteront OFF (pas de GPU)."
