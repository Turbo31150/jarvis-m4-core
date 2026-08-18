#!/usr/bin/env bash
# jarvis-watchdog-resilient.sh — Watchdog et auto-guérison temps réel des services critiques JARVIS
# Vérifie les ports vitaux toutes les 30s et relance automatiquement les composants défaillants.

LOG_FILE="/home/pamerys/jarvis/logs/watchdog-resilient.log"
mkdir -p "$(dirname "$LOG_FILE")"

log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] [WATCHDOG] $*" >> "$LOG_FILE"
}

check_port() {
  local port="$1"
  ss -tlnp 2>/dev/null | grep -q ":${port} "
}

log "Démarrage du Watchdog Résilient JARVIS..."

while true; do
  # 1. Ollama :11434
  if ! check_port 11434; then
    log "⚠️ Ollama (:11434) down — tentative de relance..."
    sudo systemctl restart ollama 2>/dev/null || systemctl --user restart ollama 2>/dev/null || true
  fi

  # 2. Whisper Bridge :9742
  if ! check_port 9742; then
    log "⚠️ Whisper Bridge (:9742) down — relance..."
    pkill -f "whisper_bridge.py" 2>/dev/null || true
    nohup /usr/bin/python3 /home/pamerys/jarvis/scripts/whisper_bridge.py >> /home/pamerys/jarvis/logs/whisper_bridge.log 2>&1 &
  fi

  # 3. Chat Proxy :18800
  if ! check_port 18800; then
    log "⚠️ Chat Proxy (:18800) down — relance..."
    pkill -f "chat_proxy.js" 2>/dev/null || true
    nohup /usr/bin/node /home/pamerys/jarvis/scripts/chat_proxy.js >> /home/pamerys/jarvis/logs/chat_proxy.log 2>&1 &
  fi

  # 4. Board Server :8766
  if ! check_port 8766; then
    log "⚠️ Board Server (:8766) down — relance..."
    pkill -f "board_server.py" 2>/dev/null || true
    cd /home/pamerys/labo/remi-board-kit && nohup python3 board_server.py >> /home/pamerys/jarvis/logs/board_server.log 2>&1 &
  fi

  # 5. MCP Server :8901
  if ! check_port 8901; then
    log "⚠️ MCP Server (:8901) down — relance..."
    pkill -f "uvicorn main:app --host 127.0.0.1 --port 8901" 2>/dev/null || true
    cd /home/pamerys/jarvis-mcp && nohup /home/pamerys/jarvis-mcp/.venv/bin/uvicorn main:app --host 127.0.0.1 --port 8901 >> /home/pamerys/jarvis/logs/mcp_server.log 2>&1 &
  fi

  # 6. Biblio Filler Daemon
  if ! pgrep -f "biblio_filler.*loop" > /dev/null 2>&1; then
    log "⚠️ Biblio Filler Daemon arrêté — relance en boucle 0-token..."
    export LMS_URL="http://127.0.0.1:11434/v1/chat/completions"
    export LMS_MODEL="qwen2.5:7b"
    nohup python3 /home/pamerys/jarvis/cli/biblio_filler.py --loop --batch 2 --pace 90 --temp-max 82 >> /home/pamerys/jarvis/data/biblio_filler.log 2>&1 &
  fi

  sleep 30
done
