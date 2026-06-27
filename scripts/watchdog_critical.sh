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
            echo "[$DATE_CMD] Attempting to restart '$service_name'..." | tee -a $LOG_FILE
            eval $restart_cmd >> $LOG_FILE 2>&1
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

# Define services: Port, Name, Health Check URL (optional), Restart Command (optional)
# Using default Docker container names based on context where possible.
# Note: Precise container/service names might differ. This is an educated guess.
# T001/T002 mention specific scripts, T005 mentions jarvis_prod_jarvis-telegram.
# Assuming generic names or service update for docker services where applicable.
# Lumen service assumed to be started via npm run dev.
SERVICES=(
    "9743 whisper http://127.0.0.1:9743/health 'docker restart whisper-bridge-container'" 
    "18800 chat_proxy http://127.0.0.1:18800/health 'docker service update --force jarvis_prod_jarvis-telegram'"
    "9742 bridge http://127.0.0.1:9742/health 'docker restart bridge-container'"
    "4173 lumen http://127.0.0.1:4173/health 'cd /home/pamerys/lumen/ && npm run dev --silent'" # Assuming lumen runs via npm run dev
    "8788 token http://127.0.0.1:8788/health 'docker restart token-service-container'"
)

for service_info in "${SERVICES[@]}"; do
    read -r port service_name health_url restart_cmd <<< "$service_info"
    
    # Use curl for health check if URL is provided and available, otherwise use netcat
    if [ -n "$health_url" ]; then
        # Check if curl is available
        if command -v curl &> /dev/null; then
            if ! curl --fail --connect-timeout 2 "$health_url" > /dev/null 2>&1; then
                echo "[$DATE_CMD] Service '$service_name' on port $port (URL: $health_url) is DOWN." | tee -a $LOG_FILE
                if [ -n "$restart_cmd" ]; then
                    echo "[$DATE_CMD] Attempting to restart '$service_name'..." | tee -a $LOG_FILE
                    eval $restart_cmd >> $LOG_FILE 2>&1
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

echo "[$DATE_CMD] Watchdog finished." | tee -a $LOG_FILE

exit 0
