#!/usr/bin/env bash
# weekly_report.sh — Génère le rapport hebdomadaire et l'envoie sur Telegram
set -uo pipefail

# 1. Charger les variables Telegram
ENV_FILE="/home/pamerys/jarvis-linux/.env"
TELEGRAM_TOKEN=""
TELEGRAM_CHAT=""

if [ -f "$ENV_FILE" ]; then
    TELEGRAM_TOKEN=$(grep -E "^TELEGRAM_TOKEN=" "$ENV_FILE" | cut -d= -f2- | tr -d '"' | tr -d "'")
    TELEGRAM_CHAT=$(grep -E "^TELEGRAM_CHAT=" "$ENV_FILE" | cut -d= -f2- | tr -d '"' | tr -d "'")
fi

if [ -z "$TELEGRAM_TOKEN" ] || [ -z "$TELEGRAM_CHAT" ]; then
    echo "Erreur: TELEGRAM_TOKEN ou TELEGRAM_CHAT non configuré dans $ENV_FILE" >&2
    exit 1
fi

REPORT="<b>📊 RAPPORT HEBDOMADAIRE JARVIS</b>\n"
REPORT+="Généré le: $(date '+%Y-%m-%d %H:%M:%S')\n\n"

# 2. Taille du disque
DISK_INFO=$(df -h / | tail -1 | awk '{print $3 " / " $2 " (" $5 ")"}')
REPORT+="<b>💾 Stockage principal:</b>\n- Utilisation: $DISK_INFO\n\n"

# 3. Services critiques (UP/DOWN)
REPORT+="<b>🛠️ Services Critiques:</b>\n"
for svc in "jarvis-whisper-api.service:9743" "jarvis-chat-proxy.service:18800" "jarvis-whisper-bridge.service:9742"; do
    name="${svc%%:*}"
    port="${svc#*:}"
    if nc -z 127.0.0.1 "$port" >/dev/null 2>&1; then
        REPORT+="  🟢 $name (Port $port)\n"
    else
        REPORT+="  🔴 $name (Port $port)\n"
    fi
done

# Docker containers
ACTIVE_CONTAINERS=$(docker ps --format '{{.Names}}' | wc -l)
TOTAL_CONTAINERS=$(docker ps -a --format '{{.Names}}' | wc -l)
REPORT+="  🐳 Docker: $ACTIVE_CONTAINERS / $TOTAL_CONTAINERS actifs\n\n"

# 4. Commits de la semaine dans les repos principaux
REPORT+="<b>💻 Activité Git (derniers 7 jours):</b>\n"
REPO_COUNT=0
for repo in /home/pamerys/Workspaces/*/; do
    [ -d "$repo/.git" ] || continue
    repo_name=$(basename "$repo")
    commits=$(git -C "$repo" log --oneline --since='1 week ago' 2>/dev/null | wc -l)
    if [ "$commits" -gt 0 ]; then
        REPORT+="  - <code>$repo_name</code>: $commits commit(s)\n"
        REPO_COUNT=$((REPO_COUNT + 1))
    fi
done

if [ "$REPO_COUNT" -eq 0 ]; then
    REPORT+="  Aucun commit cette semaine.\n"
fi

# 5. Envoyer sur Telegram
echo -e "$REPORT"
curl -s -X POST "https://api.telegram.org/bot$TELEGRAM_TOKEN/sendMessage" \
    -d "chat_id=$TELEGRAM_CHAT" \
    -d "text=$(echo -e "$REPORT")" \
    -d "parse_mode=HTML" > /dev/null

echo "Rapport hebdomadaire envoyé."
