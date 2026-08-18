#!/bin/bash
# sata-rattrapage.sh — JARVIS M1, 2026-08-06
#
# Contexte : la carte mere (MSI B550-A PRO, BIOS A.L1) expose 6 ports SATA mais
# n'etablit pas toujours le lien sur tous au demarrage a froid. Constate le
# 2026-08-06 : ata1 et ata2 « SATA link down (SStatus 0) » au boot, alors qu'un
# rescan a chaud fait apparaitre le disque de ata1 (WD Blue SN 24375P800237,
# SMART PASSED, 103 h, 0 erreur CRC). Le disque est sain : c'est le lien qui ne
# monte pas au POST.
#
# Ce script redemande un scan UNIQUEMENT sur les hotes dont le lien est absent,
# puis monte ce que fstab declare encore absent.
#
# REGLE DURE — ne jamais rescanner un hote qui a deja un lien.
# Un rescan sur un port actif reinitialise le lien : le noyau detache puis
# reattache le disque sous une NOUVELLE lettre (sdc -> sdg le 2026-08-06), ce qui
# transforme instantanement tout montage existant en montage mort (« Erreur
# d'entree/sortie » sur /mnt/jarvis-data, e2fsck en cours coupe de son
# peripherique). C'est la raison d'etre du filtre ci-dessous.

set -u
LOG=/var/log/jarvis-sata-rattrapage.log
ts() { date '+%Y-%m-%d %H:%M:%S'; }
log() { echo "[$(ts)] $*" >> "$LOG"; }

log "--- rattrapage SATA ---"
rescan=0

for host in /sys/class/scsi_host/host*; do
    n=$(basename "$host")
    # Ports AHCI uniquement : ne jamais toucher aux hotes usb-storage.
    [ "$(cat "$host/proc_name" 2>/dev/null)" = "ahci" ] || continue

    idx=${n#host}
    link="/sys/class/ata_link/link$((idx + 1))/sata_spd"

    # Un lien negocie = port occupe et fonctionnel -> on passe, sans exception.
    spd=$(cat "$link" 2>/dev/null)
    if [ -n "$spd" ] && [ "$spd" != "<unknown>" ]; then
        log "$n : lien actif ($spd) -> ignore"
        continue
    fi

    log "$n : aucun lien -> scan"
    echo "0 0 0" > "$host/scan" 2>/dev/null && rescan=$((rescan + 1))
done

if [ "$rescan" -gt 0 ]; then
    sleep 5
    # nofail + UUID dans fstab : mount -a ne monte que ce qui manque et
    # n'echoue pas sur un peripherique toujours absent.
    mount -a 2>>"$LOG"
    log "$rescan port(s) rescanne(s), mount -a applique"
else
    log "tous les ports ont un lien, rien a faire"
fi

log "disques vus : $(lsblk -dn -o NAME,SERIAL 2>/dev/null | grep -vE 'loop|zram' | tr '\n' ' ')"
exit 0
