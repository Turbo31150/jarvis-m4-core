#!/bin/bash

# Script to monitor critical services and attempt restarts.
# Services to monitor:
# 9743 (whisper)
# 18800 (chat proxy)
# 9742 (bridge)
# 4173 (lumen)
# 8788 (token)

LOG_FILE="/home/pamerys/jarvis/logs/watchdog_critical.log"
DATE_CMD=$(date '+%Y-%m-%d %H:%M:%S')

echo "[$DATE_CMD] Running critical services watchdog..." | tee -a $LOG_FILE

# Function to check port and restart if down
check_and_restart() {
    local port=$1
    local service_name=$2
    local health_check_url=$3 # Optional: URL for health check
    local restart_cmd=$4 # Command to restart the service

    if ! nc -z 127.0.0.1 $port > /dev/null 2>&1; then
        echo "[$DATE_CMD] Service '$service_name' on port $port is DOWN." | tee -a $LOG_FILE
        if [ -n "$restart_cmd" ]; then
            echo "[$DATE_CMD] Attempting to restart '$service_name' -> $restart_cmd" | tee -a $LOG_FILE
            # Exécute la commande de restart via un sous-shell propre (pas d'eval,
            # pas de quotes littérales) : $restart_cmd peut contenir un préfixe
            # d'env (XDG_RUNTIME_DIR=...), un pipeline ou un '&' -> bash -c les
            # interprète correctement. Cf. correctif du bug eval/quotes.
            bash -c "$restart_cmd" >> $LOG_FILE 2>&1
            sleep 5 # Give it a moment to restart
            if ! nc -z 127.0.0.1 $port > /dev/null 2>&1; then
                echo "[$DATE_CMD] Restart failed for '$service_name' on port $port." | tee -a $LOG_FILE
            else
                echo "[$DATE_CMD] Restart successful for '$service_name' on port $port." | tee -a $LOG_FILE
            fi
        else
            echo "[$DATE_CMD] No automatic restart command defined for '$service_name'. Manual intervention may be required." | tee -a $LOG_FILE
        fi
    else
        echo "[$DATE_CMD] Service '$service_name' on port $port is UP." | tee -a $LOG_FILE
    fi
}

# Define services : Port|Name|HealthURL|RestartCmd  (séparateur = '|').
# IMPORTANT (correctif bug eval/quotes) :
#   - le séparateur est '|' et NON l'espace, car RestartCmd contient des espaces ;
#   - PAS de quotes littérales autour de RestartCmd : elles étaient reprises
#     telles quelles par read puis eval traitait la chaîne entière comme un seul
#     nom de commande -> "commande introuvable" (RC 127), aucun service redémarré ;
#   - chat_proxy = service --user : XDG_RUNTIME_DIR=/run/user/1000 EN DUR
#     (pas $(id -u), qui casse en cron si 'id' hors PATH ; Linger actif -> DBUS
#     déduit de $XDG_RUNTIME_DIR/bus) ;
#   - whisper/bridge = services system-level -> 'sudo systemctl' conservé.
SERVICES=(
    "9742|whisper_bridge|http://127.0.0.1:9742/|XDG_RUNTIME_DIR=/run/user/1000 systemctl --user restart jarvis-whisper-bridge.service"
    "18800|chat_proxy|http://127.0.0.1:18800/health|XDG_RUNTIME_DIR=/run/user/1000 systemctl --user restart jarvis-chat-proxy.service"
    "9742|gateway|http://127.0.0.1:9742/health|XDG_RUNTIME_DIR=/run/user/1000 systemctl --user restart jv-dg-orchestrator.service"
    "4173|lumen|http://127.0.0.1:4173/|nohup python3 -m http.server 4173 --directory /home/pamerys/IA/Research/lumen-transcription-multilangue/dist > /tmp/lumen-web.log 2>&1 &"
    "8788|token|http://127.0.0.1:8788/health|XDG_RUNTIME_DIR=/run/user/1000 systemctl --user restart jarvis-lumen.service"
)

for service_info in "${SERVICES[@]}"; do
    IFS='|' read -r port service_name health_url restart_cmd <<< "$service_info"
    
    # Use curl for health check if URL is provided and available, otherwise use netcat
    if [ -n "$health_url" ]; then
        # Check if curl is available
        if command -v curl &> /dev/null; then
            if ! curl --fail --connect-timeout 2 "$health_url" > /dev/null 2>&1; then
                echo "[$DATE_CMD] Service '$service_name' on port $port (URL: $health_url) is DOWN." | tee -a $LOG_FILE
                if [ -n "$restart_cmd" ]; then
                    echo "[$DATE_CMD] Attempting to restart '$service_name' -> $restart_cmd" | tee -a $LOG_FILE
                    # Idem check_and_restart : bash -c au lieu d'eval (pas de quotes
                    # littérales, gère env-prefix / pipeline / '&').
                    bash -c "$restart_cmd" >> $LOG_FILE 2>&1
                    sleep 5 # Give it a moment to restart
                    # Re-check after restart
                    if ! curl --fail --connect-timeout 2 "$health_url" > /dev/null 2>&1; then
                        echo "[$DATE_CMD] Restart failed for '$service_name' on port $port." | tee -a $LOG_FILE
                    else
                        echo "[$DATE_CMD] Restart successful for '$service_name' on port $port." | tee -a $LOG_FILE
                    fi
                else
                    echo "[$DATE_CMD] No automatic restart command defined for '$service_name'. Manual intervention may be required." | tee -a $LOG_FILE
                fi
            else
                echo "[$DATE_CMD] Service '$service_name' on port $port (URL: $health_url) is UP." | tee -a $LOG_FILE
            fi
        else
            echo "[$DATE_CMD] 'curl' command not found. Falling back to netcat for '$service_name' on port $port." | tee -a $LOG_FILE
            check_and_restart "$port" "$service_name" "" "$restart_cmd" # Use netcat check without health URL
        fi
    else # Fallback to netcat if no health URL specified
        check_and_restart "$port" "$service_name" "" "$restart_cmd"
    fi
done

# ─────────────────────────────────────────────────────────────────────────────
# NOYAU M4+M6 — surveillance du nœud de compute distant.
# Ajouté le 2026-08-17 : les 5 sondes ci-dessus ne testent QUE des ports locaux.
# M6 (10.42.0.230, LM Studio au bout du câble USB-C) est tombé le 17/08 sans
# qu'aucun des 225 cycles du réveil ne le signale — tout était "vert" pendant
# que le board ne pouvait plus délibérer.
# Aucun redémarrage possible d'ici : on constate et on trace, c'est tout.
# ─────────────────────────────────────────────────────────────────────────────
M6_HOST="10.42.0.230"
M6_PORT="1234"
M6_LOG="$HOME/jarvis/logs/noyau-m4m6.log"
mkdir -p "$(dirname "$M6_LOG")"

# Parsing en python : grep+cut sur du JSON casse des que le format bouge
# (le delimiteur cut a echoue en shell, d'ou les 'chat=?' dans le journal).
# Les modeles charges sur M6 CHANGENT en cours de route (qwen3.5-9b puis
# qwen2.5-coder-14b puis qwen3.5-9b en quelques minutes) : on lit ce qui est
# la maintenant, on ne suppose rien.
m6=$(curl -s --max-time 8 "http://$M6_HOST:$M6_PORT/v1/models" 2>/dev/null | python3 -c "
import sys, json
try:
    ids = [m['id'] for m in json.load(sys.stdin).get('data', [])]
except Exception:
    print('INJOIGNABLE|'); raise SystemExit
chat  = [i for i in ids if 'embed' not in i.lower()]
embed = [i for i in ids if 'embed' in i.lower()]
print((chat[0] if chat else 'AUCUN') + '|' + (embed[0] if embed else ''))
" 2>/dev/null)
m6_chat="${m6%%|*}"; m6_embed="${m6##*|}"

if [ -z "$m6" ] || [ "$m6_chat" = "INJOIGNABLE" ]; then
    echo "[$(date '+%F %T')] 🔴 M6 INJOIGNABLE ($M6_HOST:$M6_PORT) — board sans backend, cascade sur Ollama local" | tee -a "$M6_LOG"
elif [ -z "$m6_embed" ]; then
    echo "[$(date '+%F %T')] 🟠 M6 OK (chat=$m6_chat) mais AUCUN modele d'embedding — vectorisation impossible, 'lms load text-embedding-nomic-embed-text-v1.5' requis sur M6" | tee -a "$M6_LOG"
else
    echo "[$(date '+%F %T')] 🟢 NOYAU M4+M6 OK — chat=$m6_chat embed=$m6_embed" >> "$M6_LOG"
fi

# Façade unifiée : le hub doit répondre, c'est par lui que le board passe désormais.
hub=$(curl -s -o /dev/null -w '%{http_code}' --max-time 6 "http://127.0.0.1:18800/v1/models" 2>/dev/null)
[ "${hub:-000}" = "200" ] || echo "[$(date '+%F %T')] 🔴 HUB 18800 ne liste plus les modèles (code=$hub) — noyau désunifié" | tee -a "$M6_LOG"

# ─────────────────────────────────────────────────────────────────────────────
# UNITE SYSTEMD — un port qui repond ne prouve pas que le service a un filet.
# Le 17/08 a 20h04, jarvis-chat-proxy est mort (SIGTERM apres 2j16h). Les sondes
# ci-dessus testent l'URL de sante : port muet => elles auraient du relancer,
# mais le watchdog lui-meme ne tournait plus (reveil bloque depuis 16h01).
# Inversement, un service 'failed' dont un processus orphelin tient le port
# passait pour UP alors qu'il n'aurait jamais redemarre tout seul.
# On verifie donc l'ETAT DE L'UNITE, independamment du port.
# ─────────────────────────────────────────────────────────────────────────────
# jarvis-chat-proxy existe en DOUBLE : une unite --system (celle qui tient
# reellement :18800, Restart=always) et une unite --user qui echouait en boucle
# sur EADDRINUSE. Surveiller la --user faisait croire a des morts du hub alors
# que le serveur n'a jamais cesse de servir. La --user est desormais desactivee ;
# on interroge chaque unite dans SA portee.
for spec in "system:jarvis-chat-proxy.service" "user:jarvis-lumen.service"; do
    portee="${spec%%:*}"; unit="${spec#*:}"
    if [ "$portee" = "system" ]; then
        etat=$(systemctl is-active "$unit" 2>/dev/null)
    else
        etat=$(systemctl --user is-active "$unit" 2>/dev/null)
    fi
    if [ "$etat" != "active" ]; then
        echo "[$(date '+%F %T')] 🔴 UNITE $unit = $etat — relance" | tee -a "$M6_LOG"
        if [ "$portee" = "user" ]; then
            XDG_RUNTIME_DIR=/run/user/1000 systemctl --user reset-failed "$unit" 2>/dev/null
            XDG_RUNTIME_DIR=/run/user/1000 systemctl --user start "$unit" 2>/dev/null
            sleep 3; nouv=$(systemctl --user is-active "$unit" 2>/dev/null)
        else
            # unite system : pas de relance possible sans sudo, on constate.
            nouv="$etat (relance impossible sans privileges — Restart=always doit suffire)"
        fi
        echo "[$(date '+%F %T')]    -> $nouv" | tee -a "$M6_LOG"
    fi
done

# HEARTBEAT — trace datee a chaque passage. Un PID vivant ne prouve rien ;
# seule une ecriture horodatee distingue 'tourne' de 'bloque'.
echo "[$(date '+%F %T')] heartbeat watchdog" >> "$M6_LOG"

echo "[$DATE_CMD] Watchdog finished." | tee -a $LOG_FILE

exit 0

