#!/bin/bash
# jarvis-watchdog.sh — surveillance matérielle M1
#   sondes : MCE · GPU fantôme · température GPU · CORRUPTION KERNEL (nouveau 2026-07-30)
#
# Déployer : sudo install -m755 ~/jarvis/scripts/jarvis-watchdog.sh /usr/local/bin/
#            sudo systemctl restart jarvis-watchdog
LOG=/var/log/jarvis-watchdog.log
CRASHDIR=/home/pamerys/jarvis/logs
STAMP=/run/jarvis-watchdog-kernel-alerted

MCE_PREV=$(journalctl -k -b --no-pager 2>/dev/null | grep -c "Machine check events"); MCE_PREV=${MCE_PREV:-0}

echo "$(date): JARVIS Watchdog démarré (MCE baseline=$MCE_PREV)" >> $LOG

# ── SONDE CORRUPTION KERNEL ───────────────────────────────────────────────
# Pourquoi /proc/sys/kernel/tainted et pas `grep dmesg` : un seul read, aucun
# parsing, et le bit reste posé même si le ring buffer a débordé. Bits guettés :
#   128   (7)  D  — le kernel a déjà oopsé ce boot
#   512   (9)  W  — WARNING déclenché
#   16384 (14) L  — soft lockup
# Ne JAMAIS utiliser ps/pgrep/top comme sonde : quand la task-list est corrompue,
# chaque itération de /proc ajoute un oops (RIP next_tgid). Cette sonde ne lit
# qu'un scalaire, elle n'aggrave rien.
kernel_died(){ [ $(( $(cat /proc/sys/kernel/tainted 2>/dev/null || echo 0) & 128 )) -ne 0 ]; }

# Alerte Telegram autonome. Deux pièges connus, évités ici :
#  · `source autoheal.env` ne suffit pas : le fichier peut contenir un doublon
#    TELEGRAM_TOKEN vide qui écrase la bonne valeur → on prend la 1ʳᵉ NON vide
#    (le `.+` de la regex saute les lignes vides tout seul).
#  · on n'hérite JAMAIS de $TELEGRAM_TOKEN de l'environnement : un export mort
#    traîne dans .bashrc et renvoie 401.
alert(){
  local msg="$1" env=/home/pamerys/.config/jarvis/autoheal.env tok cid
  [ -r "$env" ] || return 1
  tok=$(grep -m1 -oP '^TELEGRAM_TOKEN=\K.+' "$env" 2>/dev/null)
  cid=$(grep -m1 -oP '^(TELEGRAM_)?CHAT_ID=\K.+' "$env" 2>/dev/null)
  [ -n "$tok" ] && [ -n "$cid" ] || return 1
  timeout 15 curl -sS -o /dev/null -X POST \
    "https://api.telegram.org/bot${tok}/sendMessage" \
    --data-urlencode "chat_id=${cid}" --data-urlencode "text=${msg}"
}

capture_crash(){
  local dump="$CRASHDIR/kernel-crash-$(date +%Y%m%d-%H%M%S).log"
  mkdir -p "$CRASHDIR"
  {
    echo "### CRASH KERNEL détecté par jarvis-watchdog ###"
    echo "date: $(date -Is)"
    echo "uname: $(uname -r)"
    echo "tainted: $(cat /proc/sys/kernel/tainted)"
    echo "uptime_s: $(cut -d' ' -f1 /proc/uptime)"
    echo "loadavg: $(cat /proc/loadavg)"
    echo
    dmesg
  } > "$dump" 2>&1
  # sync ciblé : un `sync` global peut bloquer indéfiniment quand l'I/O est saturé
  # par la cascade d'oops — or c'est précisément le moment où on capture.
  timeout 10 sync -f "$dump" 2>/dev/null
  echo "$dump"
}

# Réaction à une corruption kernel confirmée.
# Contexte du 2026-07-30 : 153 oops en 9 min, load 126 → 244 → 315, freeze dur.
# Personne n'a réagi → les bases SQLite ont failli partir avec (WAL non flushé).
# Le bit D seul ne suffit pas à condamner la machine (un oops isolé peut être
# bénin) : le discriminant est la TRAJECTOIRE du load, pas la présence du bit.
KERNEL_LOAD_SHED=100     # au-delà : délestage (stop des producteurs de charge)
KERNEL_LOAD_REBOOT=250   # au-delà : reboot propre (0 = désactivé)

handle_kernel_corruption(){
  local load; load=$(cut -d' ' -f1 /proc/loadavg | cut -d. -f1)

  if [ "$load" -ge "$KERNEL_LOAD_SHED" ]; then
    echo "$(date): load $load ≥ $KERNEL_LOAD_SHED → délestage + protection des bases" >> $LOG
    # Producteurs de charge d'abord : chaque fork sur un kernel corrompu ajoute
    # un oops. Docker est le pire (churn de veth + fork en rafale).
    systemctl stop docker.socket docker.service 2>/dev/null
    # Le service tourne en root : joindre le bus utilisateur exige XDG_RUNTIME_DIR
    # explicitement (`su - turbo -c 'systemctl --user'` échoue sans lui).
    sudo -u turbo XDG_RUNTIME_DIR=/run/user/1000 \
      systemctl --user stop jarvis-task-auto.timer biblio-filler.service 2>/dev/null
    # Puis les bases : checkpoint PASSIVE (n'attend aucun verrou) et sync CIBLÉ —
    # un `sync` global bloque indéfiniment quand l'I/O est déjà saturé.
    for db in /home/pamerys/jarvis/jarvis_master.db /home/pamerys/jarvis/cowork_engine.db \
              /home/pamerys/jarvis/data/etoile.db /home/pamerys/jarvis/logs/jarvis_logs.db; do
      [ -f "$db" ] || continue
      timeout 20 sqlite3 "$db" "PRAGMA wal_checkpoint(PASSIVE);" >/dev/null 2>&1
      timeout 10 sync -f "$db" 2>/dev/null
    done
    echo "$(date): délestage terminé, bases checkpointées" >> $LOG
  fi

  if [ "$KERNEL_LOAD_REBOOT" -gt 0 ] && [ "$load" -ge "$KERNEL_LOAD_REBOOT" ]; then
    echo "$(date): load $load ≥ $KERNEL_LOAD_REBOOT → reboot propre" >> $LOG
    alert "🔄 M1 : reboot automatique (kernel corrompu, load $load)"
    timeout 10 sync 2>/dev/null
    systemctl reboot
  fi
}

while true; do
  # ── Corruption kernel (priorité absolue : la fenêtre pour capturer est courte)
  if kernel_died && [ ! -f "$STAMP" ]; then
    DUMP=$(capture_crash)
    OOPS=$(grep -c 'Oops:' "$DUMP" 2>/dev/null || echo '?')
    RIP=$(grep -oE 'RIP: 0010:[a-z_0-9+/x]+' "$DUMP" 2>/dev/null | tail -1)
    MSG="🔴 CORRUPTION KERNEL M1 — $OOPS oops, $RIP, load $(cut -d' ' -f1 /proc/loadavg). Reboot requis. Trace: $DUMP"
    echo "$(date): $MSG" >> $LOG
    touch "$STAMP"   # /run → remis à zéro au reboot, pas de spam
    alert "$MSG" || echo "$(date): (alerte Telegram indisponible)" >> $LOG
    handle_kernel_corruption "$DUMP"
  fi

  # ── MCE
  MCE_NOW=$(journalctl -k -b --no-pager 2>/dev/null | grep -c "Machine check events"); MCE_NOW=${MCE_NOW:-0}
  if [ "$MCE_NOW" -gt "$MCE_PREV" ]; then
    echo "$(date): ALERTE MCE $MCE_NOW (+$((MCE_NOW-MCE_PREV))) → throttle LM Studio 30s" >> $LOG
# DISABLED-MCE-STOP     pkill -STOP -f "LM Studio" 2>/dev/null; pkill -STOP -f lms 2>/dev/null
    sleep 30
# DISABLED-MCE-STOP     pkill -CONT -f "LM Studio" 2>/dev/null; pkill -CONT -f lms 2>/dev/null
    MCE_PREV=$MCE_NOW
  fi

  # ── GPU fantôme re-remove si réapparu
  if [ -e /sys/bus/pci/devices/0000:07:00.0 ]; then
    echo "$(date): GPU fantôme 07:00.0 réapparu → remove" >> $LOG
    echo 1 | tee /sys/bus/pci/devices/0000:07:00.0/remove 2>/dev/null
  fi

  # ── Température GPU
  nvidia-smi --query-gpu=index,temperature.gpu,name --format=csv,noheader 2>/dev/null | while IFS=, read idx temp name; do
    temp=$(echo $temp | tr -d ' ')
    if [ -n "$temp" ] && [ "$temp" -gt 82 ] 2>/dev/null; then
      echo "$(date): GPU$idx (${name}) ${temp}°C > 82°C → kill LM Studio" >> $LOG
      pkill -9 -f "LM Studio" 2>/dev/null; pkill -9 -f lms 2>/dev/null
    fi
  done

  sleep 55
done
