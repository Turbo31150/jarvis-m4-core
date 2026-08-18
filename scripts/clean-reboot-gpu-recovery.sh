#!/usr/bin/env bash
# clean-reboot-gpu-recovery.sh — reboot propre pour récupérer un GPU display hung
# Contexte : nvidia-modeset GPU:3 "Error while waiting for GPU progress" → 34+ Xvfb
# en D-state → load fantôme. Seul un reboot récupère un GPU figé matériellement.
# NE supprime AUCUN container/image (no-delete). À lancer manuellement : bash ce-script.sh
set -euo pipefail
LOG=/home/pamerys/jarvis/content_buffer/reboot-recovery.log
log(){ echo "[$(date -Iseconds)] $*" | tee -a "$LOG"; }

log "=== pré-reboot : snapshot ==="
log "load: $(uptime | grep -oE 'average.*')"
log "Xvfb D-state: $(ps -eo stat,comm | awk '$1~/^D/&&$2==\"Xvfb\"' | wc -l)"

log "=== 1. backup SQL rapide (sécurité avant reboot) ==="
sqlite3 ~/jarvis/data/jarvis.db ".backup /home/pamerys/jarvis/content_buffer/jarvis.db.prereboot" 2>/dev/null && log "jarvis.db sauvegardé" || log "backup sqlite skip"

log "=== 2. watchdog xvfb reste DISABLED (ne pas réactiver) ==="
systemctl --user is-enabled lmstudio-watchdog.service 2>/dev/null | grep -q disabled && log "watchdog disabled OK" || { systemctl --user disable lmstudio-watchdog.service 2>/dev/null; log "watchdog re-disabled"; }

log "=== 3. arrêt gracieux des services GPU (laisse Docker tranquille) ==="
# Les containers redémarrent seuls (restart=unless-stopped). On ne les supprime pas.
log "containers (restart auto au boot) : $(docker ps -q 2>/dev/null | wc -l)"

log "=== 4. REBOOT ==="
log "Après reboot, valider : bash ~/jarvis/scripts/post-reboot-check.sh"
sudo systemctl reboot
